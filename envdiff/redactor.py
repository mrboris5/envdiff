"""Redactor module for masking sensitive values in .env diffs."""

import re
from typing import Optional

# Patterns that suggest a value is sensitive and should be redacted
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"(password|passwd|pwd)", re.IGNORECASE),
    re.compile(r"(secret|token|api[_-]?key)", re.IGNORECASE),
    re.compile(r"(private[_-]?key|auth[_-]?key)", re.IGNORECASE),
    re.compile(r"(access[_-]?key|client[_-]?secret)", re.IGNORECASE),
    re.compile(r"(credential|dsn|database[_-]?url)", re.IGNORECASE),
]

REDACTED_PLACEHOLDER = "***REDACTED***"


def is_sensitive_key(key: str) -> bool:
    """Return True if the key name suggests the value is sensitive."""
    return any(pattern.search(key) for pattern in SENSITIVE_KEY_PATTERNS)


def redact_value(key: str, value: Optional[str], redact: bool = True) -> Optional[str]:
    """Return the value, or the redacted placeholder if the key is sensitive.

    Args:
        key: The environment variable key.
        value: The original value (may be None for missing entries).
        redact: If False, bypass redaction entirely (e.g. for sync operations).

    Returns:
        The original value, the redacted placeholder, or None.
    """
    if value is None:
        return None
    if redact and is_sensitive_key(key):
        return REDACTED_PLACEHOLDER
    return value


def redact_env_dict(
    env: dict[str, str], redact: bool = True
) -> dict[str, str]:
    """Return a copy of the env dict with sensitive values redacted.

    Args:
        env: Mapping of key -> value.
        redact: If False, return the dict unchanged.

    Returns:
        A new dict with sensitive values replaced.
    """
    if not redact:
        return dict(env)
    return {k: redact_value(k, v) or v for k, v in env.items()}
