"""Audit log for tracking env diff and sync operations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEvent:
    operation: str  # e.g. 'diff', 'sync', 'validate'
    source: str
    target: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    keys_affected: List[str] = field(default_factory=list)
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp,
            "keys_affected": self.keys_affected,
            "details": self.details,
        }

    def __str__(self) -> str:
        target_part = f" -> {self.target}" if self.target else ""
        keys_part = f" [{', '.join(self.keys_affected)}]" if self.keys_affected else ""
        return f"[{self.timestamp}] {self.operation.upper()}: {self.source}{target_part}{keys_part} {self.details}".strip()


class AuditLog:
    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> List[AuditEvent]:
        return list(self._events)

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._events], indent=2)

    def to_text(self) -> str:
        if not self._events:
            return "No audit events recorded."
        return "\n".join(str(e) for e in self._events)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            for event in self._events:
                fh.write(str(event) + "\n")


def build_diff_event(source: str, target: str, diff_result) -> AuditEvent:
    """Create an AuditEvent from a DiffResult."""
    from envdiff.core import DiffStatus

    affected = [
        entry.key
        for entry in diff_result.entries
        if entry.status != DiffStatus.SAME
    ]
    summary = (
        f"{diff_result.added} added, {diff_result.missing} missing, "
        f"{diff_result.differing} differing"
    )
    return AuditEvent(
        operation="diff",
        source=source,
        target=target,
        keys_affected=affected,
        details=summary,
    )
