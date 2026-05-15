"""Merge multiple .env files into a single unified output."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from envdiff.parser import parse_env_string


@dataclass
class MergeResult:
    """Result of merging multiple env sources."""
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: Dict[str, List[str]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def to_env_string(self) -> str:
        """Render the merged dict as a .env-formatted string."""
        lines = []
        for key, value in sorted(self.merged.items()):
            if " " in value or "#" in value:
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines)


def merge_envs(
    sources: Dict[str, str],
    strategy: str = "last_wins",
    base: Optional[str] = None,
) -> MergeResult:
    """Merge multiple env strings into one.

    Args:
        sources: Mapping of label -> env file content string.
        strategy: 'last_wins' keeps the last seen value;
                  'first_wins' keeps the first seen value;
                  'strict' records conflicts instead of resolving.
        base: Optional label to process first regardless of dict order.

    Returns:
        MergeResult with merged values and any conflicts.
    """
    if strategy not in ("last_wins", "first_wins", "strict"):
        raise ValueError(f"Unknown merge strategy: {strategy!r}")

    result = MergeResult()
    ordered_labels = list(sources.keys())
    if base and base in ordered_labels:
        ordered_labels.remove(base)
        ordered_labels.insert(0, base)

    result.sources = ordered_labels
    seen: Dict[str, str] = {}  # key -> label that set it

    for label in ordered_labels:
        parsed = parse_env_string(sources[label])
        for key, value in parsed.items():
            if key not in result.merged:
                result.merged[key] = value
                seen[key] = label
            else:
                existing_value = result.merged[key]
                if existing_value == value:
                    continue  # identical — no conflict
                if strategy == "last_wins":
                    result.merged[key] = value
                    seen[key] = label
                elif strategy == "first_wins":
                    pass  # keep original
                elif strategy == "strict":
                    if key not in result.conflicts:
                        result.conflicts[key] = [existing_value]
                    result.conflicts[key].append(value)

    return result
