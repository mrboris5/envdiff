"""Variable interpolation support for .env files.

Expands references like ${VAR} or $VAR within env values using
a provided context dictionary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_BRACE_RE = re.compile(r"\$\{([^}]+)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationWarning:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] unresolved reference '${{{self.ref}}}': {self.message}"


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    warnings: List[InterpolationWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def _expand_value(
    key: str,
    value: str,
    context: Dict[str, str],
    warnings: List[InterpolationWarning],
) -> str:
    """Expand ${VAR} and $VAR references in *value* using *context*."""

    def replace_brace(m: re.Match) -> str:
        ref = m.group(1)
        if ref in context:
            return context[ref]
        warnings.append(
            InterpolationWarning(key=key, ref=ref, message="key not found in context")
        )
        return m.group(0)  # leave original token intact

    def replace_bare(m: re.Match) -> str:
        ref = m.group(1)
        if ref in context:
            return context[ref]
        warnings.append(
            InterpolationWarning(key=key, ref=ref, message="key not found in context")
        )
        return m.group(0)

    value = _BRACE_RE.sub(replace_brace, value)
    value = _BARE_RE.sub(replace_bare, value)
    return value


def interpolate_env(
    env: Dict[str, str],
    extra_context: Optional[Dict[str, str]] = None,
) -> InterpolationResult:
    """Interpolate all values in *env*, resolving references against itself
    and an optional *extra_context* mapping (extra_context takes lower priority).

    Returns an :class:`InterpolationResult` with the expanded mapping and any
    warnings for unresolved references.
    """
    context: Dict[str, str] = {}
    if extra_context:
        context.update(extra_context)
    # env values override extra_context
    context.update(env)

    warnings: List[InterpolationWarning] = []
    resolved: Dict[str, str] = {}

    for key, value in env.items():
        resolved[key] = _expand_value(key, value, context, warnings)

    return InterpolationResult(resolved=resolved, warnings=warnings)
