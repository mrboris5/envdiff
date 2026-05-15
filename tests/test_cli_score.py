"""Tests for envdiff.cli_score."""

import json
import argparse
import pytest

from envdiff.cli_score import cmd_score, register_score_commands


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=supersecret\nDEBUG=false\n")
    return str(p)


@pytest.fixture
def bad_env_file(tmp_path):
    p = tmp_path / ".env.bad"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=changeme\nBAD LINE\n")
    return str(p)


def _ns(**kwargs):
    defaults = {"format": "text", "require": "", "min_score": 0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_score_text_output(env_file, capsys):
    rc = cmd_score(_ns(env_file=env_file))
    out = capsys.readouterr().out
    assert "Score:" in out
    assert rc == 0


def test_score_json_output(env_file, capsys):
    rc = cmd_score(_ns(env_file=env_file, format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "score" in data
    assert "grade" in data
    assert "deductions" in data
    assert rc == 0


def test_score_missing_file_returns_1(tmp_path):
    rc = cmd_score(_ns(env_file=str(tmp_path / "no.env")))
    assert rc == 1


def test_min_score_fails_when_below(bad_env_file, capsys):
    rc = cmd_score(_ns(env_file=bad_env_file, min_score=99))
    assert rc == 1


def test_min_score_passes_when_above(env_file):
    rc = cmd_score(_ns(env_file=env_file, min_score=0))
    assert rc == 0


def test_register_score_commands_adds_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_score_commands(sub)
    args = parser.parse_args(["score", "somefile.env"])
    assert args.env_file == "somefile.env"
