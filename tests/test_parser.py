"""Tests for envdiff.parser."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_string, parse_env_file


SAMPLE_ENV = """
# Database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME="myapp"
DB_PASSWORD='s3cr3t'

export API_KEY=abc123
EMPTY_VAR=
"""


def test_parse_basic_key_value():
    entries = parse_env_string("FOO=bar")
    assert "FOO" in entries
    assert entries["FOO"].value == "bar"


def test_parse_ignores_comments():
    entries = parse_env_string("# this is a comment\nFOO=bar")
    assert len(entries) == 1
    assert "FOO" in entries


def test_parse_strips_double_quotes():
    entries = parse_env_string('DB_NAME="myapp"')
    assert entries["DB_NAME"].value == "myapp"


def test_parse_strips_single_quotes():
    entries = parse_env_string("DB_PASSWORD='s3cr3t'")
    assert entries["DB_PASSWORD"].value == "s3cr3t"


def test_parse_export_prefix():
    entries = parse_env_string("export API_KEY=abc123")
    assert "API_KEY" in entries
    assert entries["API_KEY"].value == "abc123"


def test_parse_empty_value():
    entries = parse_env_string("EMPTY_VAR=")
    assert "EMPTY_VAR" in entries
    assert entries["EMPTY_VAR"].value == ""


def test_parse_line_numbers():
    content = "FOO=1\nBAR=2\nBAZ=3"
    entries = parse_env_string(content)
    assert entries["FOO"].line == 1
    assert entries["BAR"].line == 2
    assert entries["BAZ"].line == 3


def test_parse_full_sample():
    entries = parse_env_string(SAMPLE_ENV)
    assert set(entries.keys()) == {"DB_HOST", "DB_PORT", "DB_NAME", "DB_PASSWORD", "API_KEY", "EMPTY_VAR"}


def test_parse_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file(Path("/nonexistent/.env"))


def test_parse_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hello\nPORT=8080\n", encoding="utf-8")
    entries = parse_env_file(env_file)
    assert entries["SECRET"].value == "hello"
    assert entries["PORT"].value == "8080"
