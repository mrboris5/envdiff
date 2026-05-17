"""Tests for envdiff.differ_baseline."""
from __future__ import annotations

import pytest

from envdiff.differ_baseline import (
    BaselineDiffEntry,
    BaselineDiffResult,
    diff_against_baseline,
)
from envdiff.snapshotter import Snapshot


def _snapshot(data: dict, source: str = "baseline.env") -> Snapshot:
    return Snapshot(source=source, data=data, timestamp="2024-01-01T00:00:00")


# ---------------------------------------------------------------------------
# BaselineDiffEntry status
# ---------------------------------------------------------------------------

def test_entry_status_added():
    e = BaselineDiffEntry(key="NEW_KEY", baseline_value=None, current_value="hello")
    assert e.status == "added"


def test_entry_status_removed():
    e = BaselineDiffEntry(key="OLD_KEY", baseline_value="bye", current_value=None)
    assert e.status == "removed"


def test_entry_status_changed():
    e = BaselineDiffEntry(key="KEY", baseline_value="old", current_value="new")
    assert e.status == "changed"


def test_entry_status_unchanged():
    e = BaselineDiffEntry(key="KEY", baseline_value="same", current_value="same")
    assert e.status == "unchanged"


def test_entry_str_includes_status_and_key():
    e = BaselineDiffEntry(key="TOKEN", baseline_value=None, current_value="abc")
    s = str(e)
    assert "ADDED" in s
    assert "TOKEN" in s


# ---------------------------------------------------------------------------
# diff_against_baseline
# ---------------------------------------------------------------------------

def test_no_changes_when_identical():
    data = {"A": "1", "B": "2"}
    result = diff_against_baseline(data, _snapshot(data))
    assert not result.has_changes


def test_detects_added_key():
    baseline = _snapshot({"A": "1"})
    current = {"A": "1", "B": "new"}
    result = diff_against_baseline(current, baseline)
    assert result.has_changes
    assert any(e.key == "B" for e in result.added())


def test_detects_removed_key():
    baseline = _snapshot({"A": "1", "B": "gone"})
    current = {"A": "1"}
    result = diff_against_baseline(current, baseline)
    assert any(e.key == "B" for e in result.removed())


def test_detects_changed_value():
    baseline = _snapshot({"PORT": "8000"})
    current = {"PORT": "9000"}
    result = diff_against_baseline(current, baseline)
    assert any(e.key == "PORT" for e in result.changed())


def test_source_and_baseline_label_set():
    baseline = _snapshot({}, source="prod.env")
    result = diff_against_baseline({}, baseline, source="local.env")
    assert result.source == "local.env"
    assert result.baseline_label == "prod.env"


def test_to_dict_structure():
    baseline = _snapshot({"A": "1", "B": "old"})
    current = {"B": "new", "C": "extra"}
    result = diff_against_baseline(current, baseline)
    d = result.to_dict()
    assert "added" in d
    assert "removed" in d
    assert "changed" in d
    assert d["has_changes"] is True
    assert "C" in d["added"]
    assert "A" in d["removed"]
    assert "B" in d["changed"]


def test_str_output_no_changes():
    data = {"X": "1"}
    result = diff_against_baseline(data, _snapshot(data))
    assert "no changes" in str(result)


def test_str_output_lists_changed_keys():
    baseline = _snapshot({"HOST": "localhost"})
    current = {"HOST": "remotehost"}
    result = diff_against_baseline(current, baseline)
    s = str(result)
    assert "HOST" in s
    assert "CHANGED" in s
