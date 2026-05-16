"""Multi-file environment differ: compare N env files pairwise against a base."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.core import diff_envs, DiffResult


@dataclass
class PairDiff:
    """Diff result between a base file and one target file."""
    base: str
    target: str
    result: DiffResult

    def summary(self) -> str:
        r = self.result
        return (
            f"{self.base} vs {self.target}: "
            f"+{r.added_count} added, "
            f"-{r.removed_count} removed, "
            f"~{r.changed_count} changed"
        )


@dataclass
class MultiDiffReport:
    """Aggregated diffs of multiple targets against a single base."""
    base: str
    pairs: List[PairDiff] = field(default_factory=list)

    def add(self, pair: PairDiff) -> None:
        self.pairs.append(pair)

    @property
    def has_any_diff(self) -> bool:
        return any(p.result.has_diff for p in self.pairs)

    def keys_always_differing(self) -> List[str]:
        """Keys that differ in every pair comparison."""
        if not self.pairs:
            return []
        sets = [
            {e.key for e in p.result.entries if e.status.name != "SAME"}
            for p in self.pairs
        ]
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return sorted(result)

    def to_dict(self) -> dict:
        return {
            "base": self.base,
            "has_any_diff": self.has_any_diff,
            "pairs": [
                {
                    "target": p.target,
                    "summary": p.summary(),
                    "added": p.result.added_count,
                    "removed": p.result.removed_count,
                    "changed": p.result.changed_count,
                }
                for p in self.pairs
            ],
            "keys_always_differing": self.keys_always_differing(),
        }


def multi_diff(base_path: str, target_paths: List[str]) -> MultiDiffReport:
    """Diff each target against the base, returning a MultiDiffReport."""
    base_env = parse_env_file(base_path)
    report = MultiDiffReport(base=base_path)
    for target_path in target_paths:
        target_env = parse_env_file(target_path)
        result = diff_envs(base_env, target_env)
        report.add(PairDiff(base=base_path, target=target_path, result=result))
    return report
