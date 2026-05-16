"""Detect and report duplicate keys within a single .env file or string."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DuplicateEntry:
    key: str
    values: List[str]
    lines: List[int]

    def __str__(self) -> str:
        locs = ", ".join(str(ln) for ln in self.lines)
        return f"{self.key} (lines {locs}): {self.values}"


@dataclass
class DuplicateResult:
    source: str
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicates) > 0

    def keys(self) -> List[str]:
        return [d.key for d in self.duplicates]

    def __str__(self) -> str:
        if not self.has_duplicates:
            return f"{self.source}: no duplicate keys"
        lines = [f"{self.source}: {len(self.duplicates)} duplicate key(s)"]
        for dup in self.duplicates:
            lines.append(f"  {dup}")
        return "\n".join(lines)


def find_duplicates(source: str, text: str) -> DuplicateResult:
    """Parse raw .env text and return a DuplicateResult listing repeated keys."""
    seen: Dict[str, List] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        stripped = stripped.removeprefix("export ").strip()
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key not in seen:
            seen[key] = {"values": [], "lines": []}
        seen[key]["values"].append(value)
        seen[key]["lines"].append(lineno)

    result = DuplicateResult(source=source)
    for key, data in seen.items():
        if len(data["lines"]) > 1:
            result.duplicates.append(
                DuplicateEntry(key=key, values=data["values"], lines=data["lines"])
            )
    return result


def find_duplicates_in_file(path: str) -> DuplicateResult:
    """Read a file and return duplicate key analysis."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return find_duplicates(source=path, text=text)
