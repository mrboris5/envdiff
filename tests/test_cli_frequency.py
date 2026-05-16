"""Tests for envdiff.cli_frequency."""
import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_frequency import cmd_frequency, register_frequency_commands


@pytest.fixture()
def env_files(tmp_path: Path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    c = tmp_path / "c.env"
    a.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n")
    b.write_text("DB_HOST=prod\nDB_PORT=5432\nAPI_URL=https://api\n")
    c.write_text("DB_HOST=staging\nAPI_URL=https://staging\n")
    return a, b, c


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"format": "text", "sparse": False, "threshold": 0.5}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_frequency_text_output(env_files, capsys):
    a, b, c = env_files
    ns = _ns(files=[str(a), str(b), str(c)])
    rc = cmd_frequency(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "DB_HOST" in out
    assert "3/3" in out


def test_frequency_json_output(env_files, capsys):
    a, b, c = env_files
    ns = _ns(files=[str(a), str(b), str(c)], format="json")
    rc = cmd_frequency(ns)
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    keys = {e["key"] for e in data["entries"]}
    assert "DB_HOST" in keys
    assert "SECRET_KEY" in keys


def test_frequency_sparse_flag(env_files, capsys):
    a, b, c = env_files
    ns = _ns(files=[str(a), str(b), str(c)], sparse=True, threshold=0.5)
    rc = cmd_frequency(ns)
    out = capsys.readouterr().out
    assert rc == 0
    # SECRET_KEY (1/3) is sparse; DB_HOST (3/3) should not appear
    assert "SECRET_KEY" in out
    assert "DB_HOST" not in out


def test_missing_file_returns_two(tmp_path, capsys):
    ns = _ns(files=[str(tmp_path / "ghost.env")])
    rc = cmd_frequency(ns)
    assert rc == 2


def test_register_frequency_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_frequency_commands(sub)
    ns = parser.parse_args(["frequency", "a.env", "b.env"])
    assert ns.format == "text"
    assert ns.threshold == 0.5
