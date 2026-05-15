"""Tests for envdiff.cli_profile."""

import json
import argparse
import pytest
from envdiff.cli_profile import cmd_profile_check, cmd_profile_create, register_profile_commands
from envdiff.profiler import EnvProfile, save_profile


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DATABASE_URL=postgres://localhost\nSECRET_KEY=abc123\nDEBUG=true\n")
    return str(p)


@pytest.fixture
def profile_file(tmp_path):
    profile = EnvProfile(
        name="test",
        required_keys=["DATABASE_URL", "SECRET_KEY"],
        optional_keys=["DEBUG"],
    )
    path = str(tmp_path / "profile.json")
    save_profile(profile, path)
    return path


def _ns(**kwargs):
    return argparse.Namespace(**kwargs)


def test_profile_check_passes(env_file, profile_file, capsys):
    args = _ns(env_file=env_file, profile=profile_file)
    rc = cmd_profile_check(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_profile_check_fails_on_missing_key(tmp_path, profile_file, capsys):
    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=x\n")
    args = _ns(env_file=str(env), profile=profile_file)
    rc = cmd_profile_check(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "SECRET_KEY" in out


def test_profile_check_missing_profile(env_file, capsys):
    args = _ns(env_file=env_file, profile="/nonexistent/profile.json")
    rc = cmd_profile_check(args)
    assert rc == 2


def test_profile_check_missing_env_file(profile_file, capsys):
    args = _ns(env_file="/no/such/.env", profile=profile_file)
    rc = cmd_profile_check(args)
    assert rc == 2


def test_profile_create_writes_file(env_file, tmp_path, capsys):
    out_path = str(tmp_path / "out.json")
    args = _ns(env_file=env_file, name="myapp", output=out_path, description="test desc")
    rc = cmd_profile_create(args)
    assert rc == 0
    with open(out_path) as fh:
        data = json.load(fh)
    assert data["name"] == "myapp"
    assert "DATABASE_URL" in data["required_keys"]
    assert "SECRET_KEY" in data["required_keys"]


def test_profile_create_missing_env_file(tmp_path, capsys):
    args = _ns(env_file="/no/.env", name="x", output=str(tmp_path / "p.json"), description="")
    rc = cmd_profile_create(args)
    assert rc == 2


def test_register_profile_commands_adds_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_profile_commands(subparsers)
    args = parser.parse_args(["profile-create", ".env", "--name", "prod"])
    assert args.name == "prod"
