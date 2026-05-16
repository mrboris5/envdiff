"""Tests for envdiff.cli_duplicator."""

import json
import argparse
import pytest

from envdiff.cli_duplicator import cmd_duplicates, register_duplicator_commands


@pytest.fixture()
def clean_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return str(f)


@pytest.fixture()
def dup_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nDB_HOST=remote\n")
    return str(f)


def _ns(file, fmt="text"):
    return argparse.Namespace(file=file, format=fmt)


def test_clean_file_returns_zero(clean_env_file):
    assert cmd_duplicates(_ns(clean_env_file)) == 0


def test_duplicate_file_returns_one(dup_env_file):
    assert cmd_duplicates(_ns(dup_env_file)) == 1


def test_text_output_mentions_key(dup_env_file, capsys):
    cmd_duplicates(_ns(dup_env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "DB_HOST" in out


def test_json_output_is_valid(dup_env_file, capsys):
    cmd_duplicates(_ns(dup_env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "duplicates" in data
    assert data["has_duplicates"] is True


def test_json_output_clean_file(clean_env_file, capsys):
    cmd_duplicates(_ns(clean_env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["has_duplicates"] is False
    assert data["duplicates"] == []


def test_register_adds_duplicates_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_duplicator_commands(sub)
    args = parser.parse_args(["duplicates", "some.env"])
    assert args.file == "some.env"
    assert args.format == "text"
