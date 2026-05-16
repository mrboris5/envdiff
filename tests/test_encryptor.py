"""Tests for envdiff.encryptor."""

from __future__ import annotations

import pytest

pytest.importorskip("cryptography", reason="cryptography package required")

from envdiff.encryptor import (
    EncryptResult,
    decrypt_env_dict,
    encrypt_env_dict,
    generate_key,
)


@pytest.fixture()
def fernet_key() -> str:
    return generate_key()


def test_generate_key_returns_string(fernet_key):
    assert isinstance(fernet_key, str)
    assert len(fernet_key) > 0


def test_encrypt_sensitive_key_is_encrypted(fernet_key):
    env = {"DB_PASSWORD": "secret123", "APP_NAME": "myapp"}
    result = encrypt_env_dict(env, fernet_key, sensitive_only=True)
    assert result.entries[0].encrypted is True
    assert result.entries[0].result != "secret123"


def test_non_sensitive_key_skipped_by_default(fernet_key):
    env = {"APP_NAME": "myapp"}
    result = encrypt_env_dict(env, fernet_key, sensitive_only=True)
    assert result.entries[0].encrypted is False
    assert result.entries[0].result == "myapp"


def test_encrypt_all_flag_encrypts_non_sensitive(fernet_key):
    env = {"APP_NAME": "myapp"}
    result = encrypt_env_dict(env, fernet_key, sensitive_only=False)
    assert result.entries[0].encrypted is True


def test_encrypted_keys_list(fernet_key):
    env = {"API_TOKEN": "tok", "HOST": "localhost"}
    result = encrypt_env_dict(env, fernet_key)
    assert "API_TOKEN" in result.encrypted_keys
    assert "HOST" in result.skipped_keys


def test_to_dict_contains_all_keys(fernet_key):
    env = {"SECRET_KEY": "abc", "PORT": "8080"}
    result = encrypt_env_dict(env, fernet_key)
    d = result.to_dict()
    assert set(d.keys()) == {"SECRET_KEY", "PORT"}


def test_decrypt_restores_original_value(fernet_key):
    env = {"DB_PASSWORD": "hunter2"}
    encrypted = encrypt_env_dict(env, fernet_key).to_dict()
    decrypted = decrypt_env_dict(encrypted, fernet_key)
    assert decrypted["DB_PASSWORD"] == "hunter2"


def test_decrypt_passthrough_for_non_encrypted_value(fernet_key):
    env = {"APP_NAME": "myapp"}
    decrypted = decrypt_env_dict(env, fernet_key)
    assert decrypted["APP_NAME"] == "myapp"


def test_round_trip_all_keys(fernet_key):
    env = {"DB_PASSWORD": "s3cr3t", "PORT": "5432", "API_SECRET": "xyz"}
    encrypted = encrypt_env_dict(env, fernet_key, sensitive_only=False).to_dict()
    decrypted = decrypt_env_dict(encrypted, fernet_key)
    assert decrypted == env


def test_entry_str_encrypted(fernet_key):
    env = {"DB_PASSWORD": "x"}
    result = encrypt_env_dict(env, fernet_key)
    assert "encrypted" in str(result.entries[0])


def test_entry_str_skipped(fernet_key):
    env = {"HOST": "localhost"}
    result = encrypt_env_dict(env, fernet_key)
    assert "skipped" in str(result.entries[0])
