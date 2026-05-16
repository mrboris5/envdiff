"""Tests for envdiff.normalizer."""

import pytest
from envdiff.normalizer import normalize_env_lines, NormalizeResult


def _lines(*lines):
    return list(lines)


def test_uppercase_key_normalized():
    result = normalize_env_lines(_lines("db_host=localhost"))
    assert result.entries[0].normalized_line == "DB_HOST=localhost"


def test_already_uppercase_not_flagged_as_changed():
    result = normalize_env_lines(_lines("DB_HOST=localhost"))
    assert not result.entries[0].was_changed


def test_value_with_spaces_gets_quoted():
    result = normalize_env_lines(_lines("GREETING=hello world"))
    assert result.entries[0].normalized_line == 'GREETING="hello world"'


def test_value_with_hash_gets_quoted():
    result = normalize_env_lines(_lines("COLOR=blue#1"))
    assert result.entries[0].normalized_line == 'COLOR="blue#1"'


def test_empty_value_gets_quoted():
    result = normalize_env_lines(_lines("EMPTY="))
    assert result.entries[0].normalized_line == 'EMPTY=""'


def test_existing_double_quotes_stripped_then_reapplied():
    result = normalize_env_lines(_lines('KEY="value"'))
    # simple value — no spaces/hash, so quotes not reapplied
    assert result.entries[0].normalized_line == "KEY=value"


def test_existing_single_quotes_stripped():
    result = normalize_env_lines(_lines("KEY='value'"))
    assert result.entries[0].normalized_line == "KEY=value"


def test_comment_lines_preserved_unchanged():
    result = normalize_env_lines(_lines("# This is a comment"))
    assert result.entries[0].normalized_line == "# This is a comment"
    assert not result.entries[0].was_changed


def test_blank_lines_preserved():
    result = normalize_env_lines(_lines(""))
    assert result.entries[0].normalized_line == ""


def test_has_changes_true_when_key_uppercased():
    result = normalize_env_lines(_lines("foo=bar"))
    assert result.has_changes


def test_has_changes_false_when_already_normalized():
    result = normalize_env_lines(_lines("FOO=bar"))
    assert not result.has_changes


def test_changed_entries_only_returns_modified():
    result = normalize_env_lines(_lines("FOO=bar", "baz=qux"))
    changed = result.changed_entries
    assert len(changed) == 1
    assert changed[0].key == "BAZ"


def test_to_env_string_joins_lines():
    result = normalize_env_lines(_lines("FOO=bar", "BAZ=qux"))
    env_str = result.to_env_string()
    assert "FOO=bar" in env_str
    assert "BAZ=qux" in env_str


def test_no_uppercase_option_preserves_case():
    result = normalize_env_lines(_lines("db_host=localhost"), uppercase_keys=False)
    assert result.entries[0].normalized_line == "db_host=localhost"


def test_no_quote_option_leaves_spaced_value_unquoted():
    result = normalize_env_lines(_lines("GREETING=hello world"), quote_values=False)
    assert result.entries[0].normalized_line == "GREETING=hello world"


def test_export_prefix_key_normalized():
    result = normalize_env_lines(_lines("export app_name=myapp"))
    assert result.entries[0].normalized_line == "APP_NAME=myapp"
