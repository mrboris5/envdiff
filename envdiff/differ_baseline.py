"""Baseline comparator: compare a current .env against a saved baseline snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.snapshotter import Snapshot, take_snapshot


@dataclass
class BaselineDiffEntry:
    key: str
    baseline_value: Optional[str]
    current_value: Optional[str]

    @property
    def status(self) -> str:
        if self.baseline_value is None:
            return "added"
        if self.current_value is None:
            return "removed"
        if self.baseline_value != self.current_value:
            return "changed"
        return "unchanged"

    def __str__(self) -> str:
        return f"{self.status.upper():10s} {self.key}"


@dataclass
class BaselineDiffResult:
    source: str
    baseline_label: str
    entries: List[BaselineDiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.status != "unchanged" for e in self.entries)

    def added(self) -> List[BaselineDiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    def removed(self) -> List[BaselineDiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    def changed(self) -> List[BaselineDiffEntry]:
        return [e for e in self.entries if e.status == "changed"]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "baseline": self.baseline_label,
            "has_changes": self.has_changes,
            "added": [e.key for e in self.added()],
            "removed": [e.key for e in self.removed()],
            "changed": [e.key for e in self.changed()],
        }

    def __str__(self) -> str:
        lines = [f"Baseline diff: {self.source} vs {self.baseline_label}"]
        for e in self.entries:
            if e.status != "unchanged":
                lines.append(f"  {e}")
        if not self.has_changes:
            lines.append("  (no changes)")
        return "\n".join(lines)


def diff_against_baseline(
    current: Dict[str, str],
    baseline: Snapshot,
    source: str = "current",
) -> BaselineDiffResult:
    """Compare *current* env dict against a *baseline* Snapshot."""
    all_keys = set(current) | set(baseline.data)
    entries: List[BaselineDiffEntry] = []
    for key in sorted(all_keys):
        entries.append(
            BaselineDiffEntry(
                key=key,
                baseline_value=baseline.data.get(key),
                current_value=current.get(key),
            )
        )
    return BaselineDiffResult(
        source=source,
        baseline_label=baseline.source,
        entries=entries,
    )
