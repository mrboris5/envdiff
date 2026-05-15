"""Generate .env.example templates from existing .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive_key


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    comment: Optional[str] = None

    def to_line(self) -> str:
        parts = []
        if self.comment:
            parts.append(f"# {self.comment}")
        parts.append(f"{self.key}={self.placeholder}")
        return "\n".join(parts)


@dataclass
class TemplateResult:
    entries: List[TemplateEntry] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def to_env_string(self, header: Optional[str] = None) -> str:
        lines: List[str] = []
        if header:
            for h_line in header.splitlines():
                lines.append(f"# {h_line}")
            lines.append("")
        for entry in self.entries:
            lines.append(entry.to_line())
        lines.append("")
        return "\n".join(lines)


def _make_placeholder(key: str, value: str, sensitive: bool) -> str:
    """Return a placeholder string for the given key/value pair."""
    if sensitive:
        return f"<your_{key.lower()}>"
    if not value:
        return ""
    return value


def generate_template(
    env_dict: Dict[str, str],
    *,
    keep_values: bool = False,
    skip_keys: Optional[List[str]] = None,
    comments: Optional[Dict[str, str]] = None,
) -> TemplateResult:
    """Build a TemplateResult from an env dictionary.

    Args:
        env_dict: Parsed environment variables.
        keep_values: If True, non-sensitive values are preserved as-is.
        skip_keys: Keys to exclude from the template entirely.
        comments: Optional mapping of key -> inline comment string.
    """
    skip_set = set(skip_keys or [])
    comments = comments or {}
    result = TemplateResult()

    for key, value in env_dict.items():
        if key in skip_set:
            result.skipped_keys.append(key)
            continue

        sensitive = is_sensitive_key(key)
        if keep_values and not sensitive:
            placeholder = value
        else:
            placeholder = _make_placeholder(key, value, sensitive)

        entry = TemplateEntry(
            key=key,
            placeholder=placeholder,
            comment=comments.get(key),
        )
        result.entries.append(entry)

    return result
