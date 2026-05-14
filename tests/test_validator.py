"""Tests for envdiff.validator module."""

import pytest
from envdiff.validator import (
    ValidationIssue,
    ValidationResult,
    validate_env_dict,
)


def test_valid_env_passes():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "true"}
    result = validate_env_dict(env)
    assert result.valid


def test_invalid_key_format_flagged():
    env = {"123BAD": "value", "GOOD_KEY": "val"}
    result = validate_env_dict(env)
    assert not result.valid
    keys_with_issues = [i.key for i in result.issues]
    assert "123BAD" in keys_with_issues
    assert "GOOD_KEY" not in keys_with_issues


def test_empty_value_flagged():
    env = {"EMPTY_VAR": "", "PRESENT": "yes"}
    result = validate_env_dict(env)
    assert not result.valid
    assert any(i.key == "EMPTY_VAR" for i in result.issues)


def test_zero_value_not_flagged_as_empty():
    env = {"RETRIES": "0"}
    result = validate_env_dict(env)
    assert result.valid


def test_required_keys_missing():
    env = {"PRESENT": "yes"}
    result = validate_env_dict(env, required_keys=["PRESENT", "MISSING_KEY"])
    assert not result.valid
    assert any(i.key == "MISSING_KEY" for i in result.issues)


def test_required_keys_all_present():
    env = {"A": "1", "B": "2"}
    result = validate_env_dict(env, required_keys=["A", "B"])
    assert result.valid


def test_forbidden_keys_present():
    env = {"SECRET": "abc123", "SAFE": "ok"}
    result = validate_env_dict(env, forbidden_keys=["SECRET"])
    assert not result.valid
    assert any(i.key == "SECRET" for i in result.issues)


def test_forbidden_keys_absent():
    env = {"SAFE": "ok"}
    result = validate_env_dict(env, forbidden_keys=["SECRET"])
    assert result.valid


def test_validation_result_str_no_issues():
    result = ValidationResult()
    assert "No validation issues found" in str(result)


def test_validation_result_str_with_issues():
    result = ValidationResult()
    result.add("BAD_KEY", "Something is wrong", line=3)
    text = str(result)
    assert "1 issue(s)" in text
    assert "BAD_KEY" in text
    assert "line 3" in text


def test_validation_issue_str_no_line():
    issue = ValidationIssue(key="MY_KEY", message="oops")
    assert "MY_KEY" in str(issue)
    assert "line" not in str(issue)
