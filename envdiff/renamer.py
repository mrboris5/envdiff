"""Rename keys across .env files with tracking and dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameEntry:
    old_key: str
    new_key: str
    note: str = ""

    def to_dict(self) -> dict:
        return {"old_key": self.old_key, "new_key": self.new_key, "note": self.note}

    @classmethod
    def from_dict(cls, d: dict) -> "RenameEntry":
        return cls(old_key=d["old_key"], new_key=d["new_key"], note=d.get("note", ""))

    def __str__(self) -> str:
        note_part = f" ({self.note})" if self.note else ""
        return f"{self.old_key} -> {self.new_key}{note_part}"


@dataclass
class RenameResult:
    applied: List[RenameEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.applied)

    def to_env_string(self) -> str:
        return "\n".join(self.lines)


def rename_keys(
    source_lines: List[str],
    renames: List[RenameEntry],
    *,
    dry_run: bool = False,
) -> RenameResult:
    """Apply a list of renames to env file lines.

    Returns a RenameResult with updated lines and tracking info.
    Keys not found in source are recorded as skipped.
    """
    rename_map: Dict[str, RenameEntry] = {r.old_key: r for r in renames}
    present_keys: set = set()

    new_lines: List[str] = []
    applied: List[RenameEntry] = []

    for line in source_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        key_part = stripped.lstrip("export ").split("=")[0].strip()
        if key_part in rename_map:
            present_keys.add(key_part)
            entry = rename_map[key_part]
            if not dry_run:
                new_line = line.replace(key_part, entry.new_key, 1)
            else:
                new_line = line
            new_lines.append(new_line)
            applied.append(entry)
        else:
            new_lines.append(line)

    skipped = [r.old_key for r in renames if r.old_key not in present_keys]
    return RenameResult(applied=applied, skipped=skipped, lines=new_lines)
