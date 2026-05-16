"""Tests for envdiff.flattener."""
import pytest
from envdiff.flattener import flatten_dict, FlattenEntry, FlattenResult


def test_flat_dict_returns_all_keys():
    result = flatten_dict({"HOST": "localhost", "PORT": "5432"})
    keys = [e.key for e in result.entries]
    assert "HOST" in keys
    assert "PORT" in keys


def test_nested_dict_flattened_with_separator():
    result = flatten_dict({"db": {"host": "localhost", "port": 5432}})
    keys = [e.key for e in result.entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys


def test_uppercase_applied_by_default():
    result = flatten_dict({"app": {"debug": True}})
    assert result.entries[0].key == "APP_DEBUG"


def test_uppercase_disabled():
    result = flatten_dict({"app": {"debug": True}}, uppercase=False)
    assert result.entries[0].key == "app_debug"


def test_boolean_true_becomes_string_true():
    result = flatten_dict({"FEATURE": True})
    assert result.entries[0].value == "true"


def test_boolean_false_becomes_string_false():
    result = flatten_dict({"FEATURE": False})
    assert result.entries[0].value == "false"


def test_none_value_becomes_empty_string():
    result = flatten_dict({"OPTIONAL": None})
    assert result.entries[0].value == ""


def test_integer_value_stringified():
    result = flatten_dict({"WORKERS": 4})
    assert result.entries[0].value == "4"


def test_list_values_indexed():
    result = flatten_dict({"HOSTS": ["a", "b"]})
    keys = [e.key for e in result.entries]
    assert "HOSTS_0" in keys
    assert "HOSTS_1" in keys


def test_original_path_recorded():
    result = flatten_dict({"db": {"host": "localhost"}})
    entry = result.entries[0]
    assert entry.original_path == "db_host"


def test_prefix_prepended():
    result = flatten_dict({"host": "localhost"}, prefix="APP")
    assert result.entries[0].key == "APP_HOST"


def test_custom_separator():
    result = flatten_dict({"db": {"host": "h"}}, separator="__")
    assert result.entries[0].key == "DB__HOST"


def test_to_env_string_format():
    result = flatten_dict({"HOST": "localhost", "PORT": "5432"})
    env_str = result.to_env_string()
    assert "HOST=localhost" in env_str
    assert "PORT=5432" in env_str


def test_to_dict_returns_mapping():
    result = flatten_dict({"KEY": "val"})
    d = result.to_dict()
    assert d == {"KEY": "val"}


def test_no_warnings_for_clean_input():
    result = flatten_dict({"A": "1", "B": "2"})
    assert not result.has_warnings


def test_entry_str_includes_key_and_path():
    entry = FlattenEntry(key="DB_HOST", value="localhost", original_path="db_host")
    s = str(entry)
    assert "DB_HOST=localhost" in s
    assert "db_host" in s
