"""Tests for envdiff.redactor module."""

import pytest
from envdiff.redactor import (
    is_sensitive_key,
    redact_value,
    redact_env_dict,
    REDACTED_PLACEHOLDER,
)


# --- is_sensitive_key ---

def test_password_key_is_sensitive():
    assert is_sensitive_key("DB_PASSWORD") is True


def test_token_key_is_sensitive():
    assert is_sensitive_key("GITHUB_TOKEN") is True


def test_api_key_is_sensitive():
    assert is_sensitive_key("STRIPE_API_KEY") is True


def test_secret_key_is_sensitive():
    assert is_sensitive_key("CLIENT_SECRET") is True


def test_private_key_is_sensitive():
    assert is_sensitive_key("PRIVATE_KEY") is True


def test_database_url_is_sensitive():
    assert is_sensitive_key("DATABASE_URL") is True


def test_plain_key_is_not_sensitive():
    assert is_sensitive_key("APP_ENV") is False


def test_port_key_is_not_sensitive():
    assert is_sensitive_key("PORT") is False


def test_log_level_is_not_sensitive():
    assert is_sensitive_key("LOG_LEVEL") is False


# --- redact_value ---

def test_redact_value_sensitive_key():
    result = redact_value("DB_PASSWORD", "supersecret")
    assert result == REDACTED_PLACEHOLDER


def test_redact_value_non_sensitive_key():
    result = redact_value("APP_ENV", "production")
    assert result == "production"


def test_redact_value_none_returns_none():
    result = redact_value("DB_PASSWORD", None)
    assert result is None


def test_redact_value_bypass_redact_flag():
    result = redact_value("DB_PASSWORD", "supersecret", redact=False)
    assert result == "supersecret"


# --- redact_env_dict ---

def test_redact_env_dict_masks_sensitive():
    env = {"APP_ENV": "production", "API_KEY": "abc123", "PORT": "8080"}
    result = redact_env_dict(env)
    assert result["APP_ENV"] == "production"
    assert result["API_KEY"] == REDACTED_PLACEHOLDER
    assert result["PORT"] == "8080"


def test_redact_env_dict_bypass():
    env = {"API_KEY": "abc123", "DB_PASSWORD": "secret"}
    result = redact_env_dict(env, redact=False)
    assert result == env


def test_redact_env_dict_does_not_mutate_original():
    env = {"DB_PASSWORD": "secret"}
    result = redact_env_dict(env)
    assert env["DB_PASSWORD"] == "secret"
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
