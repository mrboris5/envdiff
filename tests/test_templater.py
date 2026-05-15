"""Tests for envdiff.templater module."""

import pytest

from envdiff.templater import (
    TemplateEntry,
    TemplateResult,
    generate_template,
)


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DATABASE_URL": "postgres://localhost/db",
    "SECRET_KEY": "s3cr3t",
    "API_TOKEN": "tok_abc123",
    "DEBUG": "true",
    "EMPTY_VAR": "",
}


def test_generate_template_returns_all_keys():
    result = generate_template(SAMPLE_ENV)
    keys = [e.key for e in result.entries]
    assert set(keys) == set(SAMPLE_ENV.keys())


def test_sensitive_keys_get_placeholder():
    result = generate_template(SAMPLE_ENV)
    entry_map = {e.key: e for e in result.entries}
    assert entry_map["SECRET_KEY"].placeholder == "<your_secret_key>"
    assert entry_map["API_TOKEN"].placeholder == "<your_api_token>"


def test_non_sensitive_values_replaced_by_default():
    result = generate_template(SAMPLE_ENV)
    entry_map = {e.key: e for e in result.entries}
    # Without keep_values, non-sensitive values are preserved as-is
    assert entry_map["APP_NAME"].placeholder == "myapp"
    assert entry_map["DEBUG"].placeholder == "true"


def test_keep_values_preserves_non_sensitive():
    result = generate_template(SAMPLE_ENV, keep_values=True)
    entry_map = {e.key: e for e in result.entries}
    assert entry_map["APP_NAME"].placeholder == "myapp"
    assert entry_map["DATABASE_URL"].placeholder == "postgres://localhost/db"


def test_keep_values_still_redacts_sensitive():
    result = generate_template(SAMPLE_ENV, keep_values=True)
    entry_map = {e.key: e for e in result.entries}
    assert entry_map["SECRET_KEY"].placeholder == "<your_secret_key>"


def test_skip_keys_excluded_from_entries():
    result = generate_template(SAMPLE_ENV, skip_keys=["DEBUG", "EMPTY_VAR"])
    keys = [e.key for e in result.entries]
    assert "DEBUG" not in keys
    assert "EMPTY_VAR" not in keys
    assert set(result.skipped_keys) == {"DEBUG", "EMPTY_VAR"}


def test_empty_value_produces_empty_placeholder():
    result = generate_template({"EMPTY_VAR": ""})
    assert result.entries[0].placeholder == ""


def test_comments_attached_to_entries():
    comments = {"APP_NAME": "Name of the application"}
    result = generate_template({"APP_NAME": "myapp"}, comments=comments)
    assert result.entries[0].comment == "Name of the application"


def test_template_entry_to_line_with_comment():
    entry = TemplateEntry(key="FOO", placeholder="bar", comment="A foo value")
    line = entry.to_line()
    assert line == "# A foo value\nFOO=bar"


def test_template_entry_to_line_without_comment():
    entry = TemplateEntry(key="FOO", placeholder="bar")
    assert entry.to_line() == "FOO=bar"


def test_to_env_string_includes_all_keys():
    result = generate_template({"A": "1", "B": "2"})
    output = result.to_env_string()
    assert "A=1" in output
    assert "B=2" in output


def test_to_env_string_with_header():
    result = generate_template({"A": "1"})
    output = result.to_env_string(header="Auto-generated template")
    assert "# Auto-generated template" in output
    assert "A=1" in output
