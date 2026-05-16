"""Tests for envdiff.cli_renamer."""
import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_renamer import cmd_rename, register_rename_commands


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("OLD_KEY=hello\nOTHER=world\n")
    return p


def _ns(env_file, old_key, new_key, **kwargs):
    defaults = {
        "note": "",
        "dry_run": False,
        "out_file": None,
        "output": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(
        env_file=str(env_file),
        old_key=old_key,
        new_key=new_key,
        **defaults,
    )


def test_rename_writes_new_key(env_file: Path):
    rc = cmd_rename(_ns(env_file, "OLD_KEY", "NEW_KEY"))
    assert rc == 0
    content = env_file.read_text()
    assert "NEW_KEY=hello" in content
    assert "OLD_KEY" not in content


def test_rename_missing_key_still_succeeds(env_file: Path, capsys):
    rc = cmd_rename(_ns(env_file, "DOES_NOT_EXIST", "WHATEVER"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "skipped" in out


def test_rename_dry_run_does_not_write(env_file: Path):
    original = env_file.read_text()
    rc = cmd_rename(_ns(env_file, "OLD_KEY", "NEW_KEY", dry_run=True))
    assert rc == 0
    assert env_file.read_text() == original


def test_rename_json_output(env_file: Path, capsys):
    rc = cmd_rename(_ns(env_file, "OLD_KEY", "NEW_KEY", output="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "applied" in data
    assert data["applied"][0]["old_key"] == "OLD_KEY"
    assert data["applied"][0]["new_key"] == "NEW_KEY"


def test_rename_missing_file_returns_error(tmp_path: Path):
    ns = _ns(tmp_path / "nonexistent.env", "A", "B")
    rc = cmd_rename(ns)
    assert rc == 1


def test_rename_writes_to_out_file(env_file: Path, tmp_path: Path):
    out = tmp_path / "result.env"
    rc = cmd_rename(_ns(env_file, "OLD_KEY", "RENAMED", out_file=str(out)))
    assert rc == 0
    assert out.exists()
    assert "RENAMED=hello" in out.read_text()


def test_register_rename_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_rename_commands(sub)
    args = parser.parse_args(["rename", "file.env", "OLD", "NEW"])
    assert args.old_key == "OLD"
    assert args.new_key == "NEW"
