"""Summarizer: produce a human-readable summary report of a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.classifier import classify_key, ClassifyResult
from envdiff.redactor import is_sensitive_key
from envdiff.linter import lint_lines


@dataclass
class SummaryReport:
    source: str
    total_keys: int
    sensitive_count: int
    empty_value_count: int
    category_counts: Dict[str, int] = field(default_factory=dict)
    lint_error_count: int = 0
    lint_warn_count: int = 0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "sensitive_count": self.sensitive_count,
            "empty_value_count": self.empty_value_count,
            "category_counts": self.category_counts,
            "lint_error_count": self.lint_error_count,
            "lint_warn_count": self.lint_warn_count,
        }

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"Summary for: {self.source}",
            f"  Total keys       : {self.total_keys}",
            f"  Sensitive keys   : {self.sensitive_count}",
            f"  Empty values     : {self.empty_value_count}",
            f"  Lint errors      : {self.lint_error_count}",
            f"  Lint warnings    : {self.lint_warn_count}",
            "  Categories:",
        ]
        for cat, count in sorted(self.category_counts.items()):
            lines.append(f"    {cat:<20} {count}")
        return "\n".join(lines)


def summarize_env(source: str, env_dict: Dict[str, str], raw_lines: List[str]) -> SummaryReport:
    """Build a SummaryReport from a parsed env dict and its raw source lines."""
    classify_result: ClassifyResult = ClassifyResult()
    for key in env_dict:
        classify_result.add(key)

    category_counts: Dict[str, int] = {}
    for key in env_dict:
        cat = classify_result.category_for(key)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    sensitive_count = sum(1 for k in env_dict if is_sensitive_key(k))
    empty_value_count = sum(1 for v in env_dict.values() if v == "")

    lint_result = lint_lines(raw_lines)
    lint_error_count = len(lint_result.errors())
    lint_warn_count = len(lint_result.warnings())

    return SummaryReport(
        source=source,
        total_keys=len(env_dict),
        sensitive_count=sensitive_count,
        empty_value_count=empty_value_count,
        category_counts=category_counts,
        lint_error_count=lint_error_count,
        lint_warn_count=lint_warn_count,
    )
