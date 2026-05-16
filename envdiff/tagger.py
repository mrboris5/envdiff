"""Tag .env keys with metadata labels for grouping and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class TagEntry:
    key: str
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {"key": self.key, "tags": self.tags, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict) -> "TagEntry":
        return cls(
            key=data["key"],
            tags=data.get("tags", []),
            note=data.get("note"),
        )

    def __str__(self) -> str:
        parts = [self.key, "[", ", ".join(self.tags), "]"]
        if self.note:
            parts += [" #", self.note]
        return "".join(parts)


@dataclass
class TagStore:
    _entries: Dict[str, TagEntry] = field(default_factory=dict)

    def add(self, key: str, tags: List[str], note: Optional[str] = None) -> TagEntry:
        entry = TagEntry(key=key, tags=list(tags), note=note)
        self._entries[key] = entry
        return entry

    def remove(self, key: str) -> bool:
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def get(self, key: str) -> Optional[TagEntry]:
        return self._entries.get(key)

    def keys_with_tag(self, tag: str) -> List[str]:
        return [k for k, e in self._entries.items() if tag in e.tags]

    def all_tags(self) -> List[str]:
        seen: set = set()
        for e in self._entries.values():
            seen.update(e.tags)
        return sorted(seen)

    def all_entries(self) -> List[TagEntry]:
        return list(self._entries.values())

    def to_dict(self) -> dict:
        return {"tags": [e.to_dict() for e in self._entries.values()]}

    @classmethod
    def from_dict(cls, data: dict) -> "TagStore":
        store = cls()
        for item in data.get("tags", []):
            e = TagEntry.from_dict(item)
            store._entries[e.key] = e
        return store

    def save(self, path: str) -> None:
        with open(path, "w") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, path: str) -> "TagStore":
        with open(path) as fh:
            return cls.from_dict(json.load(fh))
