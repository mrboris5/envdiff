"""Tests for envdiff.caster."""

import pytest
from envdiff.caster import cast_env_dict, _cast_value, CastResult


# --- _cast_value unit tests ---

@pytest.mark.parametrize("raw", ["true", "True", "TRUE", "yes", "1", "on"])
def test_cast_true_variants(raw):
    value, typ = _cast_value(raw)
    assert value is True
    assert typ == "bool"


@pytest.mark.parametrize("raw", ["false", "False", "FALSE", "no", "0", "off"])
def test_cast_false_variants(raw):
    value, typ = _cast_value(raw)
    assert value is False
    assert typ == "bool"


def test_cast_integer():
    value, typ = _cast_value("42")
    assert value == 42
    assert typ == "int"


def test_cast_negative_integer():
    value, typ = _cast_value("-7")
    assert value == -7
    assert typ == "int"


def test_cast_float():
    value, typ = _cast_value("3.14")
    assert abs(value - 3.14) < 1e-9
    assert typ == "float"


def test_cast_empty_string_is_null():
    value, typ = _cast_value("")
    assert value is None
    assert typ == "null"


def test_cast_plain_string():
    value, typ = _cast_value("hello")
    assert value == "hello"
    assert typ == "str"


# --- cast_env_dict integration tests ---

def test_cast_env_dict_returns_cast_result():
    result = cast_env_dict({"PORT": "8080", "DEBUG": "true", "NAME": "app"})
    assert isinstance(result, CastResult)
    assert len(result.entries) == 3


def test_cast_env_dict_typed_dict():
    result = cast_env_dict({"PORT": "8080", "DEBUG": "false", "RATIO": "0.5"})
    typed = result.typed_dict()
    assert typed["PORT"] == 8080
    assert typed["DEBUG"] is False
    assert abs(typed["RATIO"] - 0.5) < 1e-9


def test_cast_env_dict_by_key():
    result = cast_env_dict({"WORKERS": "4"})
    by_key = result.by_key()
    assert "WORKERS" in by_key
    assert by_key["WORKERS"].inferred_type == "int"


def test_cast_entry_str():
    result = cast_env_dict({"ENABLED": "yes"})
    entry = result.by_key()["ENABLED"]
    s = str(entry)
    assert "ENABLED" in s
    assert "bool" in s


def test_empty_env_dict():
    result = cast_env_dict({})
    assert result.entries == []
    assert result.typed_dict() == {}


def test_null_value_in_typed_dict():
    result = cast_env_dict({"EMPTY": ""})
    assert result.typed_dict()["EMPTY"] is None
