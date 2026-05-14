"""Formatters for displaying DiffResult output."""

from typing import List

from envdiff.core import DiffResult, DiffStatus

_STATUS_SYMBOLS = {
    DiffStatus.ADDED: "+",
    DiffStatus.MISSING: "-",
    DiffStatus.CHANGED: "~",
    DiffStatus.SAME: " ",
}

_STATUS_LABELS = {
    DiffStatus.ADDED: "ADDED",
    DiffStatus.MISSING: "MISSING",
    DiffStatus.CHANGED: "CHANGED",
    DiffStatus.SAME: "SAME",
}


def format_diff_text(result: DiffResult, show_values: bool = False) -> str:
    """Return a human-readable text representation of a DiffResult."""
    lines: List[str] = []
    lines.append(f"Diff: {result.source_file} -> {result.target_file}")
    lines.append("-" * 60)

    for entry in sorted(result.entries, key=lambda e: e.key):
        symbol = _STATUS_SYMBOLS[entry.status]
        label = _STATUS_LABELS[entry.status]
        if show_values and entry.status == DiffStatus.CHANGED:
            lines.append(
                f"  {symbol} [{label}] {entry.key}: "
                f"{entry.source_value!r} -> {entry.target_value!r}"
            )
        else:
            lines.append(f"  {symbol} [{label}] {entry.key}")

    lines.append("-" * 60)
    summary = (
        f"Summary: {result.added} added, {result.missing} missing, "
        f"{result.changed} changed, {result.same} same"
    )
    lines.append(summary)
    return "\n".join(lines)


def format_diff_json(result: DiffResult) -> dict:
    """Return a JSON-serialisable dict representation of a DiffResult."""
    return {
        "source_file": str(result.source_file),
        "target_file": str(result.target_file),
        "has_diff": result.has_diff(),
        "summary": {
            "added": result.added,
            "missing": result.missing,
            "changed": result.changed,
            "same": result.same,
        },
        "entries": [
            {
                "key": e.key,
                "status": e.status.value,
                "source_value": e.source_value,
                "target_value": e.target_value,
            }
            for e in sorted(result.entries, key=lambda e: e.key)
        ],
    }
