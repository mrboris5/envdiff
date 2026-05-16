"""Flattener: collapse nested dict structures into flat KEY=value env entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FlattenEntry:
    key: str
    value: str
    original_path: str  # dot-notation path in the source dict

    def __str__(self) -> str:
        return f"{self.key}={self.value}  # from {self.original_path}"


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def to_env_string(self) -> str:
        lines = [f"{e.key}={e.value}" for e in self.entries]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}


def _to_env_value(value: Any) -> str:
    """Convert a primitive value to a string suitable for .env files."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def flatten_dict(
    data: Dict[str, Any],
    separator: str = "_",
    prefix: str = "",
    uppercase: bool = True,
) -> FlattenResult:
    """Recursively flatten a nested dict into a FlattenResult.

    Args:
        data: The nested dictionary to flatten.
        separator: Character used to join key segments (default ``_``).
        prefix: Optional prefix prepended to every key.
        uppercase: When True (default) all keys are uppercased.
    """
    result = FlattenResult()
    _recurse(data, prefix, separator, uppercase, result)
    return result


def _recurse(
    node: Any,
    path: str,
    separator: str,
    uppercase: bool,
    result: FlattenResult,
) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            child_path = f"{path}{separator}{k}" if path else k
            _recurse(v, child_path, separator, uppercase, result)
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            child_path = f"{path}{separator}{i}" if path else str(i)
            _recurse(v, child_path, separator, uppercase, result)
    else:
        key = path.upper() if uppercase else path
        if not key:
            result.warnings.append("Encountered empty key path; skipping entry.")
            return
        value = _to_env_value(node)
        result.entries.append(FlattenEntry(key=key, value=value, original_path=path))
