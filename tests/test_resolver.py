"""Tests for envdiff.resolver."""

import pytest
from envdiff.resolver import resolve_envs, ResolvedEntry, ResolveResult


def test_resolve_single_source_returns_all_keys():
    result = resolve_envs([("prod", {"FOO": "bar", "BAZ": "qux"})])
    assert set(result.resolved.keys()) == {"FOO", "BAZ"}


def test_resolve_first_source_wins():
    result = resolve_envs([
        ("prod", {"FOO": "prod_val"}),
        ("local", {"FOO": "local_val"}),
    ])
    assert result.resolved["FOO"] == "prod_val"


def test_resolve_missing_key_filled_from_lower_priority():
    result = resolve_envs([
        ("prod", {"FOO": "bar"}),
        ("local", {"FOO": "bar", "EXTRA": "only_in_local"}),
    ])
    assert result.resolved["EXTRA"] == "only_in_local"


def test_resolve_overridden_keys_detected():
    result = resolve_envs([
        ("prod", {"SECRET": "real_secret"}),
        ("local", {"SECRET": "dev_secret"}),
    ])
    assert "SECRET" in result.overridden_keys


def test_resolve_identical_values_not_flagged_as_overridden():
    result = resolve_envs([
        ("prod", {"PORT": "8080"}),
        ("local", {"PORT": "8080"}),
    ])
    assert "PORT" not in result.overridden_keys


def test_resolve_sources_list_preserved():
    result = resolve_envs([
        ("prod", {"A": "1"}),
        ("staging", {"B": "2"}),
    ])
    assert result.sources == ["prod", "staging"]


def test_resolve_empty_sources_returns_empty():
    result = resolve_envs([])
    assert result.resolved == {}
    assert result.sources == []


def test_resolved_entry_str_with_override():
    entry = ResolvedEntry(key="DB_URL", value="prod_url", source="prod", overridden_by="local")
    s = str(entry)
    assert "DB_URL" in s
    assert "prod" in s
    assert "local" in s


def test_resolved_entry_str_no_override():
    entry = ResolvedEntry(key="PORT", value="8080", source="prod")
    s = str(entry)
    assert "PORT" in s
    assert "overrides" not in s


def test_resolve_to_env_string_format():
    result = resolve_envs([("base", {"KEY": "value", "OTHER": "thing"})])
    env_str = result.to_env_string()
    assert "KEY=value" in env_str
    assert "OTHER=thing" in env_str


def test_resolve_result_str():
    result = resolve_envs([
        ("prod", {"A": "1"}),
        ("local", {"A": "2"}),
    ])
    s = str(result)
    assert "ResolveResult" in s
    assert "prod" in s


def test_resolve_three_sources_first_wins():
    result = resolve_envs([
        ("prod", {"X": "prod"}),
        ("staging", {"X": "staging"}),
        ("local", {"X": "local"}),
    ])
    assert result.resolved["X"] == "prod"
    assert "X" in result.overridden_keys
