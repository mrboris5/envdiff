"""Resolve .env values by merging multiple sources with priority ordering."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ResolvedEntry:
    key: str
    value: str
    source: str  # which file/source the winning value came from
    overridden_by: Optional[str] = None  # if a higher-priority source shadowed a lower one

    def __str__(self) -> str:
        if self.overridden_by:
            return f"{self.key}={self.value!r} (from {self.source}, overrides {self.overridden_by})"
        return f"{self.key}={self.value!r} (from {self.source})"


@dataclass
class ResolveResult:
    entries: List[ResolvedEntry] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def resolved(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    @property
    def overridden_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.overridden_by]

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            lines.append(f"{e.key}={e.value}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return (
            f"ResolveResult(sources={self.sources}, "
            f"keys={len(self.entries)}, overridden={len(self.overridden_keys)})"
        )


def resolve_envs(
    sources: List[Tuple[str, Dict[str, str]]],
) -> ResolveResult:
    """Resolve multiple env dicts in priority order (first = highest priority).

    Args:
        sources: List of (name, env_dict) tuples ordered from highest to lowest priority.

    Returns:
        ResolveResult with the winning value for each key and provenance info.
    """
    if not sources:
        return ResolveResult()

    source_names = [name for name, _ in sources]
    all_keys: Dict[str, List[Tuple[str, str]]] = {}

    for name, env_dict in sources:
        for key, value in env_dict.items():
            all_keys.setdefault(key, []).append((name, value))

    entries: List[ResolvedEntry] = []
    for key in sorted(all_keys.keys()):
        candidates = all_keys[key]  # ordered by source priority
        winner_source, winner_value = candidates[0]
        overridden_by = None
        if len(candidates) > 1:
            # Check if a lower-priority source had a different value
            for src, val in candidates[1:]:
                if val != winner_value:
                    overridden_by = src
                    break
        entries.append(
            ResolvedEntry(
                key=key,
                value=winner_value,
                source=winner_source,
                overridden_by=overridden_by,
            )
        )

    return ResolveResult(entries=entries, sources=source_names)
