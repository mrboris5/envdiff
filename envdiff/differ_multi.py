"""Multi-file key frequency analysis: how often each key appears across envs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class KeyFrequency:
    key: str
    count: int
    total: int
    sources: List[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        """Fraction of environments that define this key (0.0 – 1.0)."""
        return self.count / self.total if self.total else 0.0

    @property
    def is_universal(self) -> bool:
        return self.count == self.total

    def __str__(self) -> str:
        pct = f"{self.coverage * 100:.0f}%"
        return f"{self.key}: {self.count}/{self.total} ({pct})"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": self.count,
            "total": self.total,
            "coverage": round(self.coverage, 4),
            "is_universal": self.is_universal,
            "sources": self.sources,
        }


@dataclass
class FrequencyReport:
    entries: List[KeyFrequency] = field(default_factory=list)

    def universal_keys(self) -> List[KeyFrequency]:
        return [e for e in self.entries if e.is_universal]

    def sparse_keys(self, threshold: float = 0.5) -> List[KeyFrequency]:
        """Keys present in fewer than *threshold* fraction of envs."""
        return [e for e in self.entries if e.coverage < threshold]

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def analyse_frequency(
    env_dicts: Sequence[Dict[str, str]],
    source_names: Sequence[str] | None = None,
) -> FrequencyReport:
    """Count how many of the supplied env dicts define each key."""
    if source_names is None:
        source_names = [f"env{i}" for i in range(len(env_dicts))]

    total = len(env_dicts)
    counts: Dict[str, List[str]] = {}

    for name, env in zip(source_names, env_dicts):
        for key in env:
            counts.setdefault(key, []).append(name)

    entries = [
        KeyFrequency(key=k, count=len(srcs), total=total, sources=srcs)
        for k, srcs in sorted(counts.items())
    ]
    return FrequencyReport(entries=entries)
