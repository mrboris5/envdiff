"""Tests for envdiff.linter module."""

import pytest
from envdiff.linter import lint_env_string, LintIssue


def test_clean_file_has_no_issues():
    content = "DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=abc123\n"
    result = lint_env_string(content)
    assert result.clean
    assert result.errors == []
    assert result.warnings == []


def test_comments_and_blank_lines_ignored():
    content = "# comment\n\nDB_HOST=localhost\n"
    result = lint_env_string(content)
    assert result.clean


def test_export_prefix_accepted():
    content = "export DB_HOST=localhost\n"
    result = lint_env_string(content)
    assert result.clean


def test_lowercase_key_warns():
    content = "db_host=localhost\n"
    result = lint_env_string(content)
    assert not result.clean
    assert any("uppercase" in i.message for i in result.warnings)


def test_missing_equals_is_error():
    content = "BADLINE\n"
    result = lint_env_string(content)
    assert len(result.errors) == 1
    assert "no '='" in result.errors[0].message


def test_empty_key_is_error():
    content = "=somevalue\n"
    result = lint_env_string(content)
    assert any(i.severity == "error" and "empty" in i.message for i in result.issues)


def test_key_with_spaces_is_error():
    content = "DB HOST=localhost\n"
    result = lint_env_string(content)
    assert any("spaces" in i.message for i in result.errors)


def test_duplicate_key_is_error():
    content = "DB_HOST=localhost\nDB_HOST=remotehost\n"
    result = lint_env_string(content)
    assert any("Duplicate" in i.message for i in result.errors)


def test_unmatched_double_quote_is_error():
    content = 'API_KEY="abc\n'
    result = lint_env_string(content)
    assert any("Unmatched quote" in i.message for i in result.errors)


def test_unmatched_single_quote_is_error():
    content = "API_KEY='abc\n"
    result = lint_env_string(content)
    assert any("Unmatched quote" in i.message for i in result.errors)


def test_matched_double_quotes_ok():
    content = 'API_KEY="abc def"\n'
    result = lint_env_string(content)
    assert result.clean


def test_summary_string():
    content = "BADLINE\ndb_host=x\n"
    result = lint_env_string(content)
    summary = result.summary()
    assert "error" in summary
    assert "warning" in summary


def test_lint_issue_str():
    issue = LintIssue(line_number=3, key="FOO", message="Something wrong", severity="error")
    s = str(issue)
    assert "ERROR" in s
    assert "FOO" in s
    assert "3" in s
