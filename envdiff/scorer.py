"""Env health scorer: produces a numeric score for a .env file based on lint, validation, and redaction signals."""

from dataclasses import dataclass, field
from typing import List

from envdiff.linter import lint_env_string, LintResult
from envdiff.validator import validate_env, ValidationResult
from envdiff.redactor import is_sensitive_key


@dataclass
class ScoreDetail:
    category: str
    deduction: int
    reason: str

    def __str__(self) -> str:
        return f"[-{self.deduction}] ({self.category}) {self.reason}"


@dataclass
class EnvScore:
    total: int
    max_score: int = 100
    details: List[ScoreDetail] = field(default_factory=list)

    @property
    def grade(self) -> str:
        pct = self.total / self.max_score
        if pct >= 0.9:
            return "A"
        if pct >= 0.75:
            return "B"
        if pct >= 0.60:
            return "C"
        if pct >= 0.40:
            return "D"
        return "F"

    def __str__(self) -> str:
        lines = [f"Score: {self.total}/{self.max_score} (Grade: {self.grade})"]
        for d in self.details:
            lines.append(f"  {d}")
        return "\n".join(lines)


def score_env(env_string: str, required_keys: List[str] = None) -> EnvScore:
    """Score an env string from 0-100 based on quality signals."""
    required_keys = required_keys or []
    deductions: List[ScoreDetail] = []

    lint_result: LintResult = lint_env_string(env_string)
    for issue in lint_result.issues:
        if issue.severity == "error":
            deductions.append(ScoreDetail("lint", 10, str(issue)))
        else:
            deductions.append(ScoreDetail("lint", 3, str(issue)))

    from envdiff.parser import parse_env_string
    env_dict = parse_env_string(env_string)

    if required_keys:
        val_result: ValidationResult = validate_env(env_dict, required_keys=required_keys)
        for issue in val_result.issues:
            deductions.append(ScoreDetail("validation", 8, str(issue)))

    for key, value in env_dict.items():
        if is_sensitive_key(key) and value and value != "":
            if any(marker in value.lower() for marker in ["changeme", "example", "test", "dummy", "placeholder"]):
                deductions.append(ScoreDetail("security", 15, f"Sensitive key '{key}' has placeholder-like value"))

    total = max(0, 100 - sum(d.deduction for d in deductions))
    return EnvScore(total=total, details=deductions)
