"""Lint .env files for common style and correctness issues."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class LintIssue:
    line_number: int
    key: str
    message: str
    severity: str = "warning"  # "warning" or "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] Line {self.line_number}: {self.key} — {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add(self, issue: LintIssue) -> None:
        self.issues.append(issue)

    def summary(self) -> str:
        return f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"


def lint_env_string(content: str) -> LintResult:
    """Lint raw .env file content line by line."""
    result = LintResult()
    seen_keys: Dict[str, int] = {}

    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        # Strip optional export prefix
        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            result.add(LintIssue(lineno, "<unknown>", "Line has no '=' separator", "error"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.add(LintIssue(lineno, "<empty>", "Key is empty", "error"))
            continue

        if key != key.upper():
            result.add(LintIssue(lineno, key, "Key is not uppercase", "warning"))

        if " " in key:
            result.add(LintIssue(lineno, key, "Key contains spaces", "error"))

        if key in seen_keys:
            result.add(LintIssue(
                lineno, key,
                f"Duplicate key (first seen on line {seen_keys[key]})",
                "error"
            ))
        else:
            seen_keys[key] = lineno

        if value.startswith(("'", '"')) and not (
            (value.startswith("'") and value.endswith("'")) or
            (value.startswith('"') and value.endswith('"'))
        ):
            result.add(LintIssue(lineno, key, "Unmatched quote in value", "error"))

    return result
