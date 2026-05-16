"""Tests for envdiff.pinner."""
import pytest
from envdiff.pinner import PinnedKey, PinStore


def _store_with_pins() -> PinStore:
    store = PinStore()
    store.pin("DB_HOST", "localhost", "prod.env")
    store.pin("API_KEY", "abc123", "prod.env", note="do not change")
    return store


def test_pin_adds_entry():
    store = PinStore()
    entry = store.pin("FOO", "bar", "dev.env")
    assert entry.key == "FOO"
    assert entry.value == "bar"
    assert entry.source == "dev.env"
    assert store.get("FOO") is entry


def test_pin_with_note():
    store = PinStore()
    entry = store.pin("SECRET", "x", "prod.env", note="critical")
    assert entry.note == "critical"


def test_unpin_removes_entry():
    store = _store_with_pins()
    assert store.unpin("DB_HOST") is True
    assert store.get("DB_HOST") is None


def test_unpin_missing_key_returns_false():
    store = PinStore()
    assert store.unpin("NONEXISTENT") is False


def test_all_pins_returns_list():
    store = _store_with_pins()
    pins = store.all_pins()
    assert len(pins) == 2
    keys = {p.key for p in pins}
    assert keys == {"DB_HOST", "API_KEY"}


def test_check_drift_no_drift():
    store = _store_with_pins()
    env = {"DB_HOST": "localhost", "API_KEY": "abc123"}
    drift = store.check_drift(env)
    assert drift == []


def test_check_drift_detects_changed_value():
    store = _store_with_pins()
    env = {"DB_HOST": "remotehost", "API_KEY": "abc123"}
    drift = store.check_drift(env)
    assert len(drift) == 1
    assert drift[0]["key"] == "DB_HOST"
    assert drift[0]["status"] == "changed"
    assert drift[0]["pinned"] == "localhost"
    assert drift[0]["current"] == "remotehost"


def test_check_drift_detects_missing_key():
    store = _store_with_pins()
    env = {"API_KEY": "abc123"}  # DB_HOST missing
    drift = store.check_drift(env)
    assert any(d["key"] == "DB_HOST" and d["status"] == "missing" for d in drift)


def test_to_dict_round_trip():
    store = _store_with_pins()
    data = store.to_dict()
    restored = PinStore.from_dict(data)
    assert restored.get("DB_HOST").value == "localhost"
    assert restored.get("API_KEY").note == "do not change"


def test_pinned_key_str_includes_source_and_key():
    entry = PinnedKey(key="PORT", value="5432", source="staging.env", pinned_at="2024-01-01T00:00:00+00:00")
    s = str(entry)
    assert "PORT" in s
    assert "5432" in s
    assert "staging.env" in s


def test_pinned_key_str_includes_note_when_present():
    entry = PinnedKey(key="X", value="1", source="a.env", pinned_at="2024-01-01T00:00:00+00:00", note="important")
    assert "important" in str(entry)


def test_pin_store_get_missing_returns_none():
    store = PinStore()
    assert store.get("MISSING") is None
