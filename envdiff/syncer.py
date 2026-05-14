"""Sync logic for applying diff results to env files."""

from pathlib import Path
from typing import Optional

from envdiff.core import DiffResult, DiffStatus
from envdiff.parser import parse_env_file, parse_env_string


def apply_sync(
    diff: DiffResult,
    target_path: Path,
    dry_run: bool = False,
    overwrite_existing: bool = False,
) -> dict:
    """
    Apply a DiffResult to the target .env file.

    Returns a summary dict with keys added, updated, skipped.
    """
    current_entries = parse_env_file(target_path) if target_path.exists() else {}
    lines = target_path.read_text().splitlines(keepends=True) if target_path.exists() else []

    added = []
    updated = []
    skipped = []

    new_lines = list(lines)

    for entry in diff.entries:
        if entry.status == DiffStatus.MISSING_IN_TARGET:
            key = entry.key
            value = entry.source_value or ""
            added.append(key)
            if not dry_run:
                new_lines.append(f"{key}={value}\n")

        elif entry.status == DiffStatus.VALUE_DIFFERS:
            key = entry.key
            value = entry.source_value or ""
            if overwrite_existing:
                updated.append(key)
                if not dry_run:
                    new_lines = _replace_key_in_lines(new_lines, key, value)
            else:
                skipped.append(key)

        elif entry.status in (DiffStatus.MISSING_IN_SOURCE, DiffStatus.IN_SYNC):
            skipped.append(entry.key)

    if not dry_run and (added or updated):
        target_path.write_text("".join(new_lines))

    return {"added": added, "updated": updated, "skipped": skipped}


def _replace_key_in_lines(lines: list, key: str, new_value: str) -> list:
    """Replace the value of an existing key in the line list."""
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"export {key}="):
            prefix = "export " if stripped.startswith("export ") else ""
            result.append(f"{prefix}{key}={new_value}\n")
        else:
            result.append(line)
    return result
