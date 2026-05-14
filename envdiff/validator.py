"""Validation utilities for .env file keys and values."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Valid env key: starts with letter or underscore, followed by word chars
_KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


@dataclass
class ValidationIssue:
    key: str
    message: str
    line: Optional[int] = None

    def __str__(self) -> str:
        loc = f" (line {self.line})" if self.line is not None else ""
        return f"[{self.key}]{loc} {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.issues) == 0

    def add(self, key: str, message: str, line: Optional[int] = None) -> None:
        self.issues.append(ValidationIssue(key=key, message=message, line=line))

    def __str__(self) -> str:
        if self.valid:
            return "No validation issues found."
        lines = [f"{len(self.issues)} issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def validate_env_dict(
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
    forbidden_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate a parsed env dictionary for common issues."""
    result = ValidationResult()

    for key, value in env.items():
        if not _KEY_PATTERN.match(key):
            result.add(key, f"Invalid key format: '{key}'")

        if not value and value != "0":
            result.add(key, "Value is empty")

    if required_keys:
        for rk in required_keys:
            if rk not in env:
                result.add(rk, "Required key is missing")

    if forbidden_keys:
        for fk in forbidden_keys:
            if fk in env:
                result.add(fk, "Forbidden key is present")

    return result


def validate_env_file(path: str, **kwargs) -> ValidationResult:
    """Parse and validate an env file at the given path."""
    from envdiff.parser import parse_env_file

    env = parse_env_file(path)
    return validate_env_dict(env, **kwargs)
