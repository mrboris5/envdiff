"""Tests for envdiff.tagger."""

import pytest
from envdiff.tagger import TagEntry, TagStore


def test_add_tag_creates_entry():
    store = TagStore()
    entry = store.add("DATABASE_URL", ["db", "required"])
    assert entry.key == "DATABASE_URL"
    assert "db" in entry.tags
    assert "required" in entry.tags


def test_add_tag_with_note():
    store = TagStore()
    entry = store.add("SECRET_KEY", ["secret"], note="rotate monthly")
    assert entry.note == "rotate monthly"


def test_get_returns_entry():
    store = TagStore()
    store.add("PORT", ["infra"])
    e = store.get("PORT")
    assert e is not None
    assert e.key == "PORT"


def test_get_missing_returns_none():
    store = TagStore()
    assert store.get("MISSING") is None


def test_remove_existing_key():
    store = TagStore()
    store.add("KEY", ["x"])
    result = store.remove("KEY")
    assert result is True
    assert store.get("KEY") is None


def test_remove_missing_key_returns_false():
    store = TagStore()
    assert store.remove("GHOST") is False


def test_keys_with_tag_filters_correctly():
    store = TagStore()
    store.add("A", ["infra", "required"])
    store.add("B", ["required"])
    store.add("C", ["infra"])
    assert set(store.keys_with_tag("required")) == {"A", "B"}
    assert set(store.keys_with_tag("infra")) == {"A", "C"}


def test_all_tags_returns_sorted_unique():
    store = TagStore()
    store.add("X", ["beta", "alpha"])
    store.add("Y", ["alpha", "gamma"])
    assert store.all_tags() == ["alpha", "beta", "gamma"]


def test_all_entries_returns_all():
    store = TagStore()
    store.add("A", ["x"])
    store.add("B", ["y"])
    keys = [e.key for e in store.all_entries()]
    assert "A" in keys and "B" in keys


def test_to_dict_round_trip():
    store = TagStore()
    store.add("DB", ["db"], note="main db")
    data = store.to_dict()
    store2 = TagStore.from_dict(data)
    e = store2.get("DB")
    assert e is not None
    assert "db" in e.tags
    assert e.note == "main db"


def test_save_and_load(tmp_path):
    path = str(tmp_path / "tags.json")
    store = TagStore()
    store.add("API_KEY", ["secret", "required"])
    store.save(path)
    loaded = TagStore.load(path)
    e = loaded.get("API_KEY")
    assert e is not None
    assert "secret" in e.tags


def test_tag_entry_str_no_note():
    e = TagEntry(key="PORT", tags=["infra"])
    assert "PORT" in str(e)
    assert "infra" in str(e)


def test_tag_entry_str_with_note():
    e = TagEntry(key="PORT", tags=["infra"], note="listen port")
    assert "listen port" in str(e)
