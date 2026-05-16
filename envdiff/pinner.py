"""Pin and track specific env key versions across environments."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json


@dataclass
class PinnedKey:
    key: str
    value: str
    source: str
    pinned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "pinned_at": self.pinned_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PinnedKey":
        return cls(
            key=data["key"],
            value=data["value"],
            source=data["source"],
            pinned_at=data.get("pinned_at", ""),
            note=data.get("note"),
        )

    def __str__(self) -> str:
        note_part = f" ({self.note})" if self.note else ""
        return f"[{self.source}] {self.key}={self.value}{note_part} @ {self.pinned_at}"


@dataclass
class PinStore:
    pins: Dict[str, PinnedKey] = field(default_factory=dict)

    def pin(self, key: str, value: str, source: str, note: Optional[str] = None) -> PinnedKey:
        entry = PinnedKey(key=key, value=value, source=source, note=note)
        self.pins[key] = entry
        return entry

    def unpin(self, key: str) -> bool:
        if key in self.pins:
            del self.pins[key]
            return True
        return False

    def get(self, key: str) -> Optional[PinnedKey]:
        return self.pins.get(key)

    def all_pins(self) -> List[PinnedKey]:
        return list(self.pins.values())

    def check_drift(self, env: Dict[str, str]) -> List[dict]:
        """Compare pinned values against a live env dict; return drift entries."""
        drift = []
        for key, pinned in self.pins.items():
            current = env.get(key)
            if current is None:
                drift.append({"key": key, "status": "missing", "pinned": pinned.value, "current": None})
            elif current != pinned.value:
                drift.append({"key": key, "status": "changed", "pinned": pinned.value, "current": current})
        return drift

    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self.pins.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "PinStore":
        store = cls()
        for k, v in data.items():
            store.pins[k] = PinnedKey.from_dict(v)
        return store


def load_pin_store(path: str) -> PinStore:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return PinStore.from_dict(json.load(fh))
    except FileNotFoundError:
        return PinStore()


def save_pin_store(store: PinStore, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store.to_dict(), fh, indent=2)
