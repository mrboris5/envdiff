"""Tests for envdiff.duplicator."""

import pytest
from envdiff.duplicator import find_duplicates, DuplicateResult, DuplicateEntry


SIMPLE_ENV = """
DB_HOST=localhost
DB_PORT=5432
DB_HOST=remotehost
"""

CLEAN_ENV = """
DB_HOST=localhost
DB_PORT=5432
APP_ENV=production
"""

TRIPLE_DUP = """
SECRET=a
SECRET=b
SECRET=c
"""

EXPORT_ENV = """
export KEY=first
export KEY=second
"""


def test_detects_duplicate_key():
    result = find_duplicates("test", SIMPLE_ENV)
    assert result.has_duplicates
    assert "DB_HOST" in result.keys()


def test_clean_env_has_no_duplicates():
    result = find_duplicates("test", CLEAN_ENV)
    assert not result.has_duplicates
    assert result.keys() == []


def test_duplicate_entry_has_both_values():
    result = find_duplicates("test", SIMPLE_ENV)
    dup = next(d for d in result.duplicates if d.key == "DB_HOST")
    assert "localhost" in dup.values
    assert "remotehost" in dup.values


def test_duplicate_entry_records_line_numbers():
    result = find_duplicates("test", SIMPLE_ENV)
    dup = next(d for d in result.duplicates if d.key == "DB_HOST")
    assert len(dup.lines) == 2
    assert dup.lines[0] < dup.lines[1]


def test_triple_duplicate_all_values_captured():
    result = find_duplicates("test", TRIPLE_DUP)
    assert result.has_duplicates
    dup = result.duplicates[0]
    assert dup.values == ["a", "b", "c"]
    assert len(dup.lines) == 3


def test_export_prefix_keys_detected():
    result = find_duplicates("test", EXPORT_ENV)
    assert result.has_duplicates
    assert "KEY" in result.keys()


def test_comments_and_blank_lines_ignored():
    env = "# comment\n\nFOO=1\nFOO=2\n"
    result = find_duplicates("test", env)
    assert result.has_duplicates
    assert result.duplicates[0].key == "FOO"


def test_str_no_duplicates():
    result = find_duplicates("myfile", CLEAN_ENV)
    assert "no duplicate" in str(result)


def test_str_with_duplicates():
    result = find_duplicates("myfile", SIMPLE_ENV)
    text = str(result)
    assert "DB_HOST" in text
    assert "myfile" in text


def test_duplicate_entry_str():
    entry = DuplicateEntry(key="FOO", values=["a", "b"], lines=[1, 5])
    s = str(entry)
    assert "FOO" in s
    assert "1" in s
    assert "5" in s


def test_source_preserved_in_result():
    result = find_duplicates("env.production", CLEAN_ENV)
    assert result.source == "env.production"
