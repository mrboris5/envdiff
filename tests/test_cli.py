"""Tests for envdiff.cli module."""

import json
import pytest
from pathlib import Path

from envdiff.cli import main


@pytest.fixture
def env_files(tmp_path):
    source = tmp_path / "source.env"
    target = tmp_path / "target.env"
    source.write_text("KEY_A=alpha\nKEY_B=beta\nKEY_C=gamma\n")
    target.write_text("KEY_A=alpha\nKEY_B=different\n")
    return source, target


def test_diff_command_text_output(env_files, capsys):
    source, target = env_files
    rc = main(["diff", str(source), str(target)])
    out = capsys.readouterr().out
    assert "KEY_B" in out
    assert "KEY_C" in out
    assert rc == 1  # has diff


def test_diff_command_json_output(env_files, capsys):
    source, target = env_files
    main(["diff", str(source), str(target), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data


def test_diff_command_no_diff_returns_zero(tmp_path, capsys):
    f = tmp_path / "a.env"
    f.write_text("KEY=value\n")
    rc = main(["diff", str(f), str(f)])
    assert rc == 0


def test_sync_command_adds_missing(env_files, capsys):
    source, target = env_files
    rc = main(["sync", str(source), str(target)])
    out = capsys.readouterr().out
    assert "+1 added" in out
    assert rc == 0
    assert "KEY_C" in target.read_text()


def test_sync_command_dry_run(env_files, capsys):
    source, target = env_files
    original = target.read_text()
    main(["sync", str(source), str(target), "--dry-run"])
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert target.read_text() == original


def test_sync_command_overwrite(env_files, capsys):
    source, target = env_files
    main(["sync", str(source), str(target), "--overwrite"])
    content = target.read_text()
    assert "KEY_B=beta" in content
