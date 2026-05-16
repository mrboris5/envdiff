"""Tests for envdiff.grouper."""

import pytest
from envdiff.grouper import GroupEntry, GroupResult, group_env, _infer_group


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "REDIS_URL": "redis://localhost",
    "APP_DEBUG": "true",
    "APP_NAME": "envdiff",
    "SECRET": "s3cr3t",
}


def test_group_by_prefix_heuristic():
    result = group_env(SAMPLE_ENV)
    assert "DB" in result.group_names()
    assert "REDIS" in result.group_names()
    assert "APP" in result.group_names()


def test_key_without_underscore_goes_to_ungrouped():
    result = group_env(SAMPLE_ENV)
    keys = [e.key for e in result.ungrouped]
    assert "SECRET" in keys


def test_get_group_returns_correct_entries():
    result = group_env(SAMPLE_ENV)
    db_entries = result.get_group("DB")
    db_keys = {e.key for e in db_entries}
    assert db_keys == {"DB_HOST", "DB_PORT"}


def test_get_group_missing_returns_empty_list():
    result = group_env(SAMPLE_ENV)
    assert result.get_group("NONEXISTENT") == []


def test_custom_map_exact_key_overrides_heuristic():
    custom = {"DB_HOST": "database", "DB_PORT": "database"}
    result = group_env(SAMPLE_ENV, custom_map=custom)
    assert "database" in result.group_names()
    keys = {e.key for e in result.get_group("database")}
    assert keys == {"DB_HOST", "DB_PORT"}


def test_custom_map_prefix_match():
    custom = {"APP_": "application"}
    result = group_env(SAMPLE_ENV, custom_map=custom)
    app_keys = {e.key for e in result.get_group("application")}
    assert "APP_DEBUG" in app_keys
    assert "APP_NAME" in app_keys


def test_custom_map_longest_prefix_wins():
    custom = {"APP_": "app", "APP_D": "app_debug_group"}
    group = _infer_group("APP_DEBUG", custom_map=custom)
    assert group == "app_debug_group"


def test_group_names_are_sorted():
    result = group_env(SAMPLE_ENV)
    names = result.group_names()
    assert names == sorted(names)


def test_to_dict_structure():
    result = group_env({"DB_HOST": "localhost", "PLAIN": "value"})
    d = result.to_dict()
    assert "groups" in d
    assert "ungrouped" in d
    assert "DB" in d["groups"]
    assert any(e["key"] == "PLAIN" for e in d["ungrouped"])


def test_group_entry_str():
    entry = GroupEntry(key="DB_HOST", value="localhost", group="DB")
    assert "DB" in str(entry)
    assert "DB_HOST" in str(entry)


def test_empty_env_produces_empty_result():
    result = group_env({})
    assert result.group_names() == []
    assert result.ungrouped == []


def test_infer_group_no_underscore_ungrouped():
    assert _infer_group("PLAIN") == "__ungrouped__"


def test_infer_group_with_underscore():
    assert _infer_group("REDIS_URL") == "REDIS"
