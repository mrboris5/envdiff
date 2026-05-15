"""Tests for envdiff.merger module."""

import pytest
from envdiff.merger import merge_envs, MergeResult


ENV_A = """DB_HOST=localhost
DB_PORT=5432
APP_ENV=development
"""

ENV_B = """DB_HOST=prod.db.example.com
DB_PORT=5432
APP_SECRET=supersecret
"""

ENV_C = """APP_ENV=production
APP_SECRET=anothersecret
NEW_KEY=hello
"""


def test_merge_last_wins_resolves_conflict():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, strategy="last_wins")
    assert result.merged["DB_HOST"] == "prod.db.example.com"
    assert not result.has_conflicts


def test_merge_first_wins_keeps_original():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, strategy="first_wins")
    assert result.merged["DB_HOST"] == "localhost"
    assert not result.has_conflicts


def test_merge_strict_records_conflicts():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, strategy="strict")
    assert "DB_HOST" in result.conflicts
    assert "localhost" in result.conflicts["DB_HOST"]
    assert "prod.db.example.com" in result.conflicts["DB_HOST"]


def test_merge_identical_values_not_flagged_as_conflict():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, strategy="strict")
    assert "DB_PORT" not in result.conflicts
    assert result.merged["DB_PORT"] == "5432"


def test_merge_collects_all_unique_keys():
    result = merge_envs({"a": ENV_A, "b": ENV_B, "c": ENV_C}, strategy="last_wins")
    assert "DB_HOST" in result.merged
    assert "APP_ENV" in result.merged
    assert "APP_SECRET" in result.merged
    assert "NEW_KEY" in result.merged


def test_merge_sources_order_respected():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, strategy="last_wins")
    assert result.sources == ["a", "b"]


def test_merge_base_processed_first():
    result = merge_envs(
        {"b": ENV_B, "a": ENV_A},
        strategy="first_wins",
        base="a",
    )
    # 'a' is base so processed first; first_wins keeps 'a' value
    assert result.merged["DB_HOST"] == "localhost"
    assert result.sources[0] == "a"


def test_merge_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        merge_envs({"a": ENV_A}, strategy="unknown")


def test_to_env_string_renders_sorted_keys():
    result = merge_envs({"a": ENV_A}, strategy="last_wins")
    env_str = result.to_env_string()
    lines = env_str.strip().splitlines()
    keys = [line.split("=")[0] for line in lines]
    assert keys == sorted(keys)


def test_to_env_string_quotes_values_with_spaces():
    sources = {"a": 'GREETING=hello world\n'}
    result = merge_envs(sources, strategy="last_wins")
    env_str = result.to_env_string()
    assert 'GREETING="hello world"' in env_str
