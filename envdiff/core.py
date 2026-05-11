"""Core logic for parsing, diffing, and syncing .env files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DiffStatus(Enum):
    """Status of a key when comparing two .env files."""
    ADDED = "added"        # present in target, missing in source
    REMOVED = "removed"    # present in source, missing in target
    CHANGED = "changed"    # present in both, but values differ
    UNCHANGED = "unchanged"  # present in both with same value


@dataclass
class EnvEntry:
    """Represents a single key-value pair from a .env file."""
    key: str
    value: str
    comment: Optional[str] = None  # inline comment, if any

    def __repr__(self) -> str:
        return f"EnvEntry(key={self.key!r}, value={self.value!r})"


@dataclass
class DiffResult:
    """Result of comparing two .env files."""
    source_path: Path
    target_path: Path
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old_val, new_val)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_diff(self) -> bool:
        """Return True if there are any differences."""
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        """Return a short human-readable summary of the diff."""
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No differences found."
        return ", ".join(parts)


# Regex to match valid .env lines: KEY=VALUE or KEY="VALUE" etc.
_ENV_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)


def parse_env_file(path: Path) -> Dict[str, EnvEntry]:
    """Parse a .env file and return a dict of key -> EnvEntry.

    - Skips blank lines and comment-only lines (starting with #).
    - Strips optional surrounding quotes from values.
    - Preserves inline comments (value # comment).

    Args:
        path: Path to the .env file.

    Returns:
        Ordered dict mapping variable names to EnvEntry objects.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    entries: Dict[str, EnvEntry] = {}
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")

            # Skip blank lines and pure comment lines
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = _ENV_LINE_RE.match(stripped)
            if not match:
                # Not a valid key=value line — skip silently
                continue

            key = match.group("key")
            raw_value = match.group("value").strip()

            # Split off inline comment (unquoted # outside of quotes)
            value, inline_comment = _split_value_comment(raw_value)

            entries[key] = EnvEntry(key=key, value=value, comment=inline_comment)

    return entries


def _split_value_comment(raw: str) -> Tuple[str, Optional[str]]:
    """Separate the value from an optional inline comment.

    Handles quoted values (single or double quotes) and ignores
    # characters that appear inside quotes.
    """
    if raw and raw[0] in ('"', "'"):
        quote_char = raw[0]
        end_quote = raw.find(quote_char, 1)
        if end_quote != -1:
            value = raw[1:end_quote]
            rest = raw[end_quote + 1:].strip()
            comment = rest.lstrip("# ").strip() if rest.startswith("#") else None
            return value, comment

    # Unquoted value — split on first unescaped #
    if " #" in raw:
        idx = raw.index(" #")
        value = raw[:idx].strip()
        comment = raw[idx + 2:].strip()
        return value, comment or None

    return raw.strip(), None


def diff_env_files(source: Path, target: Path) -> DiffResult:
    """Compare two .env files and return a DiffResult.

    Args:
        source: The baseline .env file (e.g. .env.example).
        target: The file to compare against (e.g. .env).

    Returns:
        A DiffResult describing all differences.
    """
    src_entries = parse_env_file(source)
    tgt_entries = parse_env_file(target)

    result = DiffResult(source_path=Path(source), target_path=Path(target))

    all_keys = set(src_entries) | set(tgt_entries)

    for key in sorted(all_keys):
        in_src = key in src_entries
        in_tgt = key in tgt_entries

        if in_src and not in_tgt:
            result.removed.append(key)
        elif in_tgt and not in_src:
            result.added.append(key)
        elif src_entries[key].value != tgt_entries[key].value:
            result.changed.append((key, src_entries[key].value, tgt_entries[key].value))
        else:
            result.unchanged.append(key)

    return result
