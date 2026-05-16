"""Tests for envdiff.masker."""
import pytest

from envdiff.masker import (
    DEFAULT_MASK,
    MaskEntry,
    MaskResult,
    _partial_mask,
    mask_env_dict,
)


# ---------------------------------------------------------------------------
# _partial_mask
# ---------------------------------------------------------------------------

def test_partial_mask_shows_last_chars():
    result = _partial_mask("supersecret", visible=4)
    assert result.endswith("cret")
    assert result.startswith(DEFAULT_MASK)


def test_partial_mask_short_value_fully_masked():
    result = _partial_mask("abc", visible=4)
    assert result == DEFAULT_MASK


def test_partial_mask_exact_length_fully_masked():
    result = _partial_mask("abcd", visible=4)
    assert result == DEFAULT_MASK


# ---------------------------------------------------------------------------
# mask_env_dict — sensitive keys
# ---------------------------------------------------------------------------

def test_password_key_is_masked():
    result = mask_env_dict({"DB_PASSWORD": "s3cr3t"})
    entry = result.entries[0]
    assert entry.was_masked is True
    assert entry.masked == DEFAULT_MASK


def test_token_key_is_masked():
    result = mask_env_dict({"API_TOKEN": "tok_abc123"})
    assert result.entries[0].was_masked is True


def test_non_sensitive_key_not_masked():
    result = mask_env_dict({"APP_ENV": "production"})
    entry = result.entries[0]
    assert entry.was_masked is False
    assert entry.masked == "production"


def test_partial_flag_reveals_suffix():
    result = mask_env_dict({"SECRET_KEY": "abcdefghij"}, partial=True)
    entry = result.entries[0]
    assert entry.masked.endswith("ghij")
    assert entry.masked.startswith(DEFAULT_MASK)


# ---------------------------------------------------------------------------
# mask_env_dict — extra_sensitive
# ---------------------------------------------------------------------------

def test_extra_sensitive_key_is_masked():
    result = mask_env_dict({"MY_CUSTOM_FIELD": "value"}, extra_sensitive=["MY_CUSTOM_FIELD"])
    assert result.entries[0].was_masked is True


def test_extra_sensitive_case_insensitive():
    result = mask_env_dict({"MY_FIELD": "value"}, extra_sensitive=["my_field"])
    assert result.entries[0].was_masked is True


# ---------------------------------------------------------------------------
# MaskResult helpers
# ---------------------------------------------------------------------------

def test_masked_keys_returns_only_masked():
    env = {"DB_PASSWORD": "secret", "APP_ENV": "prod"}
    result = mask_env_dict(env)
    assert "DB_PASSWORD" in result.masked_keys
    assert "APP_ENV" not in result.masked_keys


def test_to_dict_returns_masked_values():
    env = {"DB_PASSWORD": "secret", "APP_ENV": "prod"}
    result = mask_env_dict(env)
    d = result.to_dict()
    assert d["DB_PASSWORD"] == DEFAULT_MASK
    assert d["APP_ENV"] == "prod"


def test_mask_entry_str_includes_status():
    entry = MaskEntry(key="TOKEN", original="abc", masked=DEFAULT_MASK, was_masked=True)
    assert "masked" in str(entry)
    assert "TOKEN" in str(entry)


def test_empty_env_returns_empty_result():
    result = mask_env_dict({})
    assert result.entries == []
    assert result.masked_keys == []
