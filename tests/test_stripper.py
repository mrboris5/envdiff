"""Tests for envdiff.stripper."""
from __future__ import annotations

import pytest
from envdiff.stripper import strip_env, StripResult


def _lines(*items: str):
    return [line + "\n" for line in items]


def test_removes_comment_lines():
    lines = _lines("# comment", "KEY=value")
    result = strip_env(lines)
    assert result.removed_count == 1
    assert "KEY=value" in result.kept_lines
    assert all("# comment" not in l for l in result.kept_lines)


def test_removes_blank_lines():
    lines = _lines("KEY=value", "", "OTHER=yes")
    result = strip_env(lines)
    assert result.removed_count == 1
    assert "" not in result.kept_lines


def test_keeps_comments_when_flag_set():
    lines = _lines("# comment", "KEY=value")
    result = strip_env(lines, remove_comments=False)
    assert result.removed_count == 0
    assert result.was_changed is False


def test_keeps_blanks_when_flag_set():
    lines = _lines("KEY=value", "", "OTHER=yes")
    result = strip_env(lines, remove_blanks=False)
    assert result.removed_count == 0


def test_removed_lines_include_line_numbers():
    lines = _lines("# first comment", "KEY=value", "# second comment")
    result = strip_env(lines)
    linenos = [ln for ln, _ in result.removed_lines]
    assert 1 in linenos
    assert 3 in linenos


def test_was_changed_false_for_clean_file():
    lines = _lines("KEY=value", "OTHER=123")
    result = strip_env(lines)
    assert result.was_changed is False


def test_to_env_string_joins_kept_lines():
    lines = _lines("# comment", "KEY=value", "", "OTHER=123")
    result = strip_env(lines)
    env_str = result.to_env_string()
    assert "KEY=value" in env_str
    assert "OTHER=123" in env_str
    assert "# comment" not in env_str


def test_dry_run_does_not_modify_kept_lines():
    lines = _lines("# comment", "KEY=value")
    result = strip_env(lines, dry_run=True)
    # dry_run: kept_lines reflects original, but removed_count still counted
    assert result.removed_count == 1
    assert len(result.kept_lines) == len(lines)


def test_str_representation():
    lines = _lines("# comment", "KEY=value")
    result = strip_env(lines)
    s = str(result)
    assert "removed=1" in s
    assert "changed=True" in s


def test_empty_file_no_changes():
    result = strip_env([])
    assert result.removed_count == 0
    assert result.was_changed is False
    assert result.to_env_string() == "\n"
