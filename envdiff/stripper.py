"""Strip comments and blank lines from .env files, with optional dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class StripResult:
    original_lines: List[str]
    kept_lines: List[str]
    removed_count: int
    removed_lines: List[Tuple[int, str]] = field(default_factory=list)  # (lineno, content)

    @property
    def was_changed(self) -> bool:
        return self.removed_count > 0

    def to_env_string(self) -> str:
        return "\n".join(self.kept_lines).rstrip("\n") + "\n"

    def __str__(self) -> str:
        return (
            f"StripResult(removed={self.removed_count}, "
            f"kept={len(self.kept_lines)}, changed={self.was_changed})"
        )


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def strip_env(
    lines: List[str],
    remove_comments: bool = True,
    remove_blanks: bool = True,
    dry_run: bool = False,
) -> StripResult:
    """Strip comments and/or blank lines from parsed .env file lines."""
    kept: List[str] = []
    removed: List[Tuple[int, str]] = []

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if remove_comments and _is_comment(line):
            removed.append((i, line))
        elif remove_blanks and _is_blank(line):
            removed.append((i, line))
        else:
            kept.append(line)

    return StripResult(
        original_lines=lines,
        kept_lines=kept if not dry_run else [l.rstrip("\n") for l in lines],
        removed_count=len(removed),
        removed_lines=removed,
    )
