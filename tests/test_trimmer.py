"""Tests for envdiff.trimmer."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.trimmer import trim_env, TrimResult


SOURCE = textwrap.dedent("""\
    # database config
    DB_HOST=localhost
    DB_PORT=5432
    DB_PASSWORD=secret
    UNUSED_KEY=value
    ANOTHER_UNUSED=123
""")

REFERENCE_KEYS = {"DB_HOST", "DB_PORT", "DB_PASSWORD"}


def test_trim_identifies_unused_keys():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    assert result.has_removals
    assert "UNUSED_KEY" in result.removed_keys
    assert "ANOTHER_UNUSED" in result.removed_keys


def test_trim_does_not_remove_referenced_keys():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    assert "DB_HOST" not in result.removed_keys
    assert "DB_PORT" not in result.removed_keys
    assert "DB_PASSWORD" not in result.removed_keys


def test_trim_kept_lines_exclude_removed_keys():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    env_out = result.to_env_string()
    assert "UNUSED_KEY" not in env_out
    assert "ANOTHER_UNUSED" not in env_out
    assert "DB_HOST" in env_out


def test_trim_preserves_comments_and_blanks():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    env_out = result.to_env_string()
    assert "# database config" in env_out


def test_trim_dry_run_does_not_modify_kept_lines():
    result = trim_env(SOURCE, REFERENCE_KEYS, dry_run=True)
    assert result.has_removals
    # kept_lines should be the original lines unchanged
    assert "UNUSED_KEY" in result.to_env_string()
    assert "ANOTHER_UNUSED" in result.to_env_string()


def test_trim_entry_line_number_is_set():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    unused = {e.key: e for e in result.removed}
    # UNUSED_KEY is line 5 in SOURCE (1-based)
    assert unused["UNUSED_KEY"].line_number == 5


def test_trim_clean_env_has_no_removals():
    clean = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = trim_env(clean, {"DB_HOST", "DB_PORT"})
    assert not result.has_removals
    assert result.removed == []


def test_trim_empty_reference_removes_all():
    result = trim_env(SOURCE, set())
    assert result.removed_keys == {"DB_HOST", "DB_PORT", "DB_PASSWORD", "UNUSED_KEY", "ANOTHER_UNUSED"}


def test_trim_export_prefix_handled():
    src = "export FOO=bar\nexport BAR=baz\n"
    result = trim_env(src, {"FOO"})
    assert "BAR" in result.removed_keys
    assert "FOO" not in result.removed_keys


def test_trim_to_env_string_is_valid_env():
    result = trim_env(SOURCE, REFERENCE_KEYS)
    from envdiff.parser import parse_env_string
    parsed = parse_env_string(result.to_env_string())
    assert set(parsed.keys()) == REFERENCE_KEYS
