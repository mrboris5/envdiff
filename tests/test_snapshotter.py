"""Tests for envdiff.snapshotter."""

import json
import os
import pytest

from envdiff.snapshotter import (
    Snapshot,
    SnapshotDiff,
    take_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}


def test_take_snapshot_captures_all_keys():
    snap = take_snapshot(SAMPLE, source="test.env")
    assert snap.entries["DB_HOST"] == "localhost"
    assert snap.entries["DB_PORT"] == "5432"
    assert snap.source == "test.env"
    assert snap.redacted is False


def test_take_snapshot_redacts_sensitive_keys():
    snap = take_snapshot(SAMPLE, source="test.env", redact=True)
    assert snap.redacted is True
    assert snap.entries["SECRET_KEY"] == "***REDACTED***"
    assert snap.entries["DB_HOST"] == "localhost"


def test_snapshot_timestamp_is_set():
    snap = take_snapshot(SAMPLE, source="x.env")
    assert snap.timestamp  # non-empty
    assert "T" in snap.timestamp  # ISO format


def test_snapshot_to_dict_round_trip():
    snap = take_snapshot(SAMPLE, source="env.test")
    d = snap.to_dict()
    restored = Snapshot.from_dict(d)
    assert restored.source == snap.source
    assert restored.entries == snap.entries
    assert restored.timestamp == snap.timestamp


def test_snapshot_str_includes_source_and_key_count():
    snap = take_snapshot(SAMPLE, source="prod.env")
    s = str(snap)
    assert "prod.env" in s
    assert str(len(SAMPLE)) in s


def test_save_and_load_snapshot(tmp_path):
    snap = take_snapshot(SAMPLE, source="local.env")
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    assert os.path.exists(path)
    loaded = load_snapshot(path)
    assert loaded.source == snap.source
    assert loaded.entries == snap.entries
    assert loaded.timestamp == snap.timestamp


def test_save_snapshot_writes_valid_json(tmp_path):
    snap = take_snapshot(SAMPLE, source="ci.env")
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    with open(path) as fh:
        data = json.load(fh)
    assert "entries" in data
    assert "timestamp" in data


def test_diff_snapshots_detects_added_key():
    old = take_snapshot({"A": "1"}, source="old")
    new = take_snapshot({"A": "1", "B": "2"}, source="new")
    diff = diff_snapshots(old, new)
    assert "B" in diff.added
    assert diff.has_changes


def test_diff_snapshots_detects_removed_key():
    old = take_snapshot({"A": "1", "B": "2"}, source="old")
    new = take_snapshot({"A": "1"}, source="new")
    diff = diff_snapshots(old, new)
    assert "B" in diff.removed


def test_diff_snapshots_detects_changed_value():
    old = take_snapshot({"A": "old_val"}, source="old")
    new = take_snapshot({"A": "new_val"}, source="new")
    diff = diff_snapshots(old, new)
    assert "A" in diff.changed
    assert diff.changed["A"] == ("old_val", "new_val")


def test_diff_snapshots_no_changes():
    snap = take_snapshot(SAMPLE, source="env")
    diff = diff_snapshots(snap, snap)
    assert not diff.has_changes
