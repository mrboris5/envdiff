"""Multi-environment comparator: diff one source .env against many targets."""

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.core import diff_envs, DiffResult, DiffStatus


@dataclass
class CompareReport:
    """Aggregated comparison of one source against multiple target environments."""

    source_name: str
    results: Dict[str, DiffResult] = field(default_factory=dict)

    def add(self, target_name: str, result: DiffResult) -> None:
        self.results[target_name] = result

    def environments(self) -> List[str]:
        return list(self.results.keys())

    def has_any_diff(self) -> bool:
        return any(r.has_diff() for r in self.results.values())

    def keys_missing_in(self, target_name: str) -> List[str]:
        result = self.results.get(target_name)
        if result is None:
            return []
        return [
            e.key
            for e in result.entries
            if e.status == DiffStatus.MISSING_IN_TARGET
        ]

    def keys_extra_in(self, target_name: str) -> List[str]:
        result = self.results.get(target_name)
        if result is None:
            return []
        return [
            e.key
            for e in result.entries
            if e.status == DiffStatus.MISSING_IN_SOURCE
        ]

    def summary(self) -> Dict[str, Dict[str, int]]:
        """Return per-target counts of each diff status."""
        out: Dict[str, Dict[str, int]] = {}
        for name, result in self.results.items():
            counts: Dict[str, int] = {}
            for entry in result.entries:
                label = entry.status.value
                counts[label] = counts.get(label, 0) + 1
            out[name] = counts
        return out


def compare_many(
    source_name: str,
    source: Dict[str, str],
    targets: Dict[str, Dict[str, str]],
) -> CompareReport:
    """Diff *source* against every environment in *targets*.

    Args:
        source_name: Human-readable label for the source environment.
        source: Parsed key/value mapping for the source.
        targets: Mapping of environment name -> parsed key/value mapping.

    Returns:
        A :class:`CompareReport` containing one :class:`DiffResult` per target.
    """
    report = CompareReport(source_name=source_name)
    for target_name, target_env in targets.items():
        result = diff_envs(source, target_env)
        report.add(target_name, result)
    return report
