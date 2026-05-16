"""masker.py — Mask env values for safe display in logs or output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.redactor import is_sensitive_key

DEFAULT_MASK = "********"
_VISIBLE_CHARS = 4  # show last N chars for partial masking


@dataclass
class MaskEntry:
    key: str
    original: str
    masked: str
    was_masked: bool

    def __str__(self) -> str:
        status = "masked" if self.was_masked else "plain"
        return f"{self.key}={self.masked} ({status})"


@dataclass
class MaskResult:
    entries: List[MaskEntry] = field(default_factory=list)

    @property
    def masked_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.was_masked]

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.masked for e in self.entries}


def _partial_mask(value: str, visible: int = _VISIBLE_CHARS) -> str:
    """Show only the last `visible` characters; mask the rest."""
    if len(value) <= visible:
        return DEFAULT_MASK
    return DEFAULT_MASK + value[-visible:]


def mask_env_dict(
    env: Dict[str, str],
    *,
    partial: bool = False,
    extra_sensitive: List[str] | None = None,
) -> MaskResult:
    """Mask sensitive values in an env dict.

    Args:
        env: Mapping of key -> value.
        partial: If True, reveal the last few characters of masked values.
        extra_sensitive: Additional keys to treat as sensitive regardless of name.

    Returns:
        MaskResult with one MaskEntry per key.
    """
    extra = {k.upper() for k in (extra_sensitive or [])}
    result = MaskResult()
    for key, value in env.items():
        sensitive = is_sensitive_key(key) or key.upper() in extra
        if sensitive:
            masked = _partial_mask(value) if partial else DEFAULT_MASK
        else:
            masked = value
        result.entries.append(
            MaskEntry(key=key, original=value, masked=masked, was_masked=sensitive)
        )
    return result
