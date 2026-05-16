"""Normalize .env file contents: consistent quoting, casing, and whitespace."""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class NormalizeEntry:
    key: str
    original_line: str
    normalized_line: str

    @property
    def was_changed(self) -> bool:
        return self.original_line != self.normalized_line

    def __str__(self) -> str:
        if self.was_changed:
            return f"{self.key}: {self.original_line!r} -> {self.normalized_line!r}"
        return f"{self.key}: unchanged"


@dataclass
class NormalizeResult:
    entries: List[NormalizeEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.was_changed for e in self.entries)

    @property
    def changed_entries(self) -> List[NormalizeEntry]:
        return [e for e in self.entries if e.was_changed]

    def to_env_string(self) -> str:
        return "\n".join(e.normalized_line for e in self.entries)


def _normalize_line(line: str, uppercase_keys: bool = True, quote_values: bool = True) -> Tuple[str, str]:
    """Return (key, normalized_line) or (None, line) for comments/blanks."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None, line.rstrip()

    raw = stripped
    if raw.startswith("export "):
        raw = raw[len("export "):].strip()

    if "=" not in raw:
        return None, line.rstrip()

    key, _, value = raw.partition("=")
    key = key.strip()
    value = value.strip()

    # Strip existing quotes
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]

    normalized_key = key.upper() if uppercase_keys else key

    if quote_values and (" " in value or "#" in value or not value):
        normalized_value = f'"{value}"'
    elif quote_values and value:
        normalized_value = value
    else:
        normalized_value = value

    normalized_line = f"{normalized_key}={normalized_value}"
    return normalized_key, normalized_line


def normalize_env_lines(
    lines: List[str],
    uppercase_keys: bool = True,
    quote_values: bool = True,
) -> NormalizeResult:
    result = NormalizeResult()
    for line in lines:
        original = line.rstrip()
        key, normalized = _normalize_line(original, uppercase_keys=uppercase_keys, quote_values=quote_values)
        if key is None:
            # comment or blank — preserve as-is
            result.entries.append(NormalizeEntry(key="", original_line=original, normalized_line=normalized))
        else:
            result.entries.append(NormalizeEntry(key=key, original_line=original, normalized_line=normalized))
    return result
