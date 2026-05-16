"""Trimmer: detect and remove unused keys from a .env file given a reference set."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envdiff.parser import parse_env_string


@dataclass
class TrimEntry:
    key: str
    value: str
    line_number: int

    def __str__(self) -> str:
        return f"{self.key} (line {self.line_number})"


@dataclass
class TrimResult:
    removed: List[TrimEntry] = field(default_factory=list)
    kept_lines: List[str] = field(default_factory=list)

    @property
    def has_removals(self) -> bool:
        return len(self.removed) > 0

    @property
    def removed_keys(self) -> Set[str]:
        return {e.key for e in self.removed}

    def to_env_string(self) -> str:
        return "\n".join(self.kept_lines)


def trim_env(
    source: str,
    reference_keys: Set[str],
    dry_run: bool = False,
) -> TrimResult:
    """Remove keys from *source* that are not present in *reference_keys*.

    Args:
        source: Raw content of the .env file to trim.
        reference_keys: Set of keys considered "in use".
        dry_run: If True, populate *removed* but leave *kept_lines* unchanged.

    Returns:
        A :class:`TrimResult` describing what was (or would be) removed.
    """
    parsed: Dict[str, str] = parse_env_string(source)
    all_lines = source.splitlines()

    # Build a quick lookup: key -> line index (1-based)
    key_to_line: Dict[str, int] = {}
    for idx, raw in enumerate(all_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        clean = stripped.removeprefix("export ").strip()
        if "=" in clean:
            k = clean.split("=", 1)[0].strip()
            if k:
                key_to_line[k] = idx

    result = TrimResult()
    removable: Set[str] = set(parsed.keys()) - reference_keys

    for key in sorted(removable):
        line_no = key_to_line.get(key, 0)
        result.removed.append(TrimEntry(key=key, value=parsed[key], line_number=line_no))

    if dry_run:
        result.kept_lines = all_lines[:]
        return result

    for raw in all_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            result.kept_lines.append(raw)
            continue
        clean = stripped.removeprefix("export ").strip()
        if "=" in clean:
            k = clean.split("=", 1)[0].strip()
            if k in removable:
                continue
        result.kept_lines.append(raw)

    return result
