"""Tests for envdiff.exporter module."""

import json
from pathlib import Path

import pytest

from envdiff.exporter import (
    export_env_dict_to_dotenv,
    export_env_dict_to_json,
    export_env_dict_to_shell,
)


@pytest.fixture()
def tmp_file(tmp_path: Path):
    return str(tmp_path / "output")


SAMPLE = {"DB_HOST": "localhost", "DB_PASSWORD": "s3cr3t", "PORT": "5432"}


# --- dotenv export ---

def test_dotenv_export_writes_key_value_pairs(tmp_file):
    export_env_dict_to_dotenv(SAMPLE, tmp_file)
    content = Path(tmp_file).read_text()
    assert "DB_HOST=localhost" in content
    assert "PORT=5432" in content


def test_dotenv_export_quotes_values_with_spaces(tmp_file):
    export_env_dict_to_dotenv({"GREETING": "hello world"}, tmp_file)
    content = Path(tmp_file).read_text()
    assert 'GREETING="hello world"' in content


def test_dotenv_export_header_comment(tmp_file):
    export_env_dict_to_dotenv(SAMPLE, tmp_file, header_comment="Auto-generated")
    content = Path(tmp_file).read_text()
    assert content.startswith("# Auto-generated")


def test_dotenv_export_redacts_sensitive_keys(tmp_file):
    export_env_dict_to_dotenv(SAMPLE, tmp_file, redact=True)
    content = Path(tmp_file).read_text()
    assert "s3cr3t" not in content
    assert "DB_PASSWORD" in content


def test_dotenv_export_keys_sorted(tmp_file):
    export_env_dict_to_dotenv(SAMPLE, tmp_file)
    lines = [l for l in Path(tmp_file).read_text().splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


# --- JSON export ---

def test_json_export_valid_json(tmp_file):
    export_env_dict_to_json(SAMPLE, tmp_file)
    data = json.loads(Path(tmp_file).read_text())
    assert data["DB_HOST"] == "localhost"
    assert data["PORT"] == "5432"


def test_json_export_redacts_sensitive_keys(tmp_file):
    export_env_dict_to_json(SAMPLE, tmp_file, redact=True)
    data = json.loads(Path(tmp_file).read_text())
    assert data["DB_PASSWORD"] != "s3cr3t"


def test_json_export_keys_sorted(tmp_file):
    export_env_dict_to_json(SAMPLE, tmp_file)
    raw = Path(tmp_file).read_text()
    data = json.loads(raw)
    assert list(data.keys()) == sorted(data.keys())


# --- shell export ---

def test_shell_export_contains_export_statements(tmp_file):
    export_env_dict_to_shell(SAMPLE, tmp_file)
    content = Path(tmp_file).read_text()
    assert "export DB_HOST='localhost'" in content
    assert "export PORT='5432'" in content


def test_shell_export_starts_with_shebang(tmp_file):
    export_env_dict_to_shell(SAMPLE, tmp_file)
    content = Path(tmp_file).read_text()
    assert content.startswith("#!/usr/bin/env sh")


def test_shell_export_redacts_sensitive_keys(tmp_file):
    export_env_dict_to_shell(SAMPLE, tmp_file, redact=True)
    content = Path(tmp_file).read_text()
    assert "s3cr3t" not in content


def test_shell_export_escapes_single_quotes(tmp_file):
    export_env_dict_to_shell({"MSG": "it's alive"}, tmp_file)
    content = Path(tmp_file).read_text()
    # single quote inside value must be escaped for POSIX sh
    assert "it'\"'\"'s alive" in content
