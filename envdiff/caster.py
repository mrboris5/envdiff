"""Type casting for .env values — infer and convert string values to Python types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


_TRUE_VALUES = {"true", "yes", "1", "on"}
_FALSE_VALUES = {"false", "no", "0", "off"}


@dataclass
class CastEntry:
    key: str
    raw: str
    cast_value: Any
    inferred_type: str

    def __str__(self) -> str:
        return f"{self.key}: {self.raw!r} -> {self.cast_value!r} ({self.inferred_type})"


@dataclass
class CastResult:
    entries: List[CastEntry] = field(default_factory=list)

    def by_key(self) -> Dict[str, CastEntry]:
        return {e.key: e for e in self.entries}

    def typed_dict(self) -> Dict[str, Any]:
        return {e.key: e.cast_value for e in self.entries}


def _cast_value(raw: str) -> tuple[Any, str]:
    """Return (cast_value, type_name) for a raw string."""
    if raw.lower() in _TRUE_VALUES:
        return True, "bool"
    if raw.lower() in _FALSE_VALUES:
        return False, "bool"
    # Try integer
    try:
        return int(raw), "int"
    except ValueError:
        pass
    # Try float
    try:
        return float(raw), "float"
    except ValueError:
        pass
    # Empty string
    if raw == "":
        return None, "null"
    return raw, "str"


def cast_env_dict(env: Dict[str, str]) -> CastResult:
    """Infer and cast all values in an env dict."""
    result = CastResult()
    for key, raw in env.items():
        cast_value, inferred_type = _cast_value(raw)
        result.entries.append(
            CastEntry(key=key, raw=raw, cast_value=cast_value, inferred_type=inferred_type)
        )
    return result
