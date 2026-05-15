"""Snapshot module: capture and compare .env state at a point in time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.redactor import redact_env_dict


@dataclass
class Snapshot:
    source: str
    timestamp: str
    entries: Dict[str, str]
    redacted: bool = False

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "timestamp": self.timestamp,
            "redacted": self.redacted,
            "entries": self.entries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            source=data["source"],
            timestamp=data["timestamp"],
            entries=data["entries"],
            redacted=data.get("redacted", False),
        )

    def __str__(self) -> str:
        return f"Snapshot(source={self.source!r}, ts={self.timestamp}, keys={len(self.entries)})"


@dataclass
class SnapshotDiff:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def take_snapshot(env_dict: Dict[str, str], source: str, redact: bool = False) -> Snapshot:
    """Capture a snapshot of an env dict."""
    entries = redact_env_dict(env_dict) if redact else dict(env_dict)
    timestamp = datetime.now(timezone.utc).isoformat()
    return Snapshot(source=source, timestamp=timestamp, entries=entries, redacted=redact)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def diff_snapshots(old: Snapshot, new: Snapshot) -> SnapshotDiff:
    """Compare two snapshots and return what changed."""
    result = SnapshotDiff()
    old_keys = set(old.entries)
    new_keys = set(new.entries)

    for key in new_keys - old_keys:
        result.added[key] = new.entries[key]

    for key in old_keys - new_keys:
        result.removed[key] = old.entries[key]

    for key in old_keys & new_keys:
        if old.entries[key] != new.entries[key]:
            result.changed[key] = (old.entries[key], new.entries[key])

    return result
