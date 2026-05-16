"""Group env keys by prefix or custom category for organized diffing and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupEntry:
    key: str
    value: str
    group: str

    def __str__(self) -> str:
        return f"[{self.group}] {self.key}={self.value}"


@dataclass
class GroupResult:
    groups: Dict[str, List[GroupEntry]] = field(default_factory=dict)
    ungrouped: List[GroupEntry] = field(default_factory=list)

    def add(self, entry: GroupEntry) -> None:
        if entry.group == "__ungrouped__":
            self.ungrouped.append(entry)
        else:
            self.groups.setdefault(entry.group, []).append(entry)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def get_group(self, name: str) -> List[GroupEntry]:
        return self.groups.get(name, [])

    def to_dict(self) -> dict:
        return {
            "groups": {
                g: [{"key": e.key, "value": e.value} for e in entries]
                for g, entries in self.groups.items()
            },
            "ungrouped": [{"key": e.key, "value": e.value} for e in self.ungrouped],
        }


def _infer_group(key: str, custom_map: Optional[Dict[str, str]] = None) -> str:
    """Return the group name for a key.

    Priority:
    1. custom_map exact match
    2. custom_map prefix match (longest prefix wins)
    3. underscore-prefix heuristic (e.g. DB_HOST -> DB)
    4. '__ungrouped__' fallback
    """
    if custom_map:
        if key in custom_map:
            return custom_map[key]
        # longest matching prefix
        best: Optional[str] = None
        best_len = 0
        for pattern, group in custom_map.items():
            if key.startswith(pattern) and len(pattern) > best_len:
                best = group
                best_len = len(pattern)
        if best is not None:
            return best

    # heuristic: first segment before '_'
    if "_" in key:
        return key.split("_")[0]

    return "__ungrouped__"


def group_env(
    env: Dict[str, str],
    custom_map: Optional[Dict[str, str]] = None,
) -> GroupResult:
    """Group a flat env dict into a GroupResult."""
    result = GroupResult()
    for key, value in env.items():
        group = _infer_group(key, custom_map)
        result.add(GroupEntry(key=key, value=value, group=group))
    return result
