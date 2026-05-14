"""Parser for .env files."""

import re
from pathlib import Path
from typing import Dict, Optional

from envdiff.core import EnvEntry

_COMMENT_RE = re.compile(r"^\s*#.*$")
_BLANK_RE = re.compile(r"^\s*$")
_ENTRY_RE = re.compile(
    r"^\s*(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$"
)


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1]
    return value


def parse_env_string(content: str) -> Dict[str, EnvEntry]:
    """Parse the contents of a .env file string into a dict of EnvEntry objects."""
    entries: Dict[str, EnvEntry] = {}
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
            continue
        match = _ENTRY_RE.match(line)
        if match:
            key = match.group("key")
            raw_value = match.group("value").strip()
            value: Optional[str] = _strip_quotes(raw_value) if raw_value else ""
            entries[key] = EnvEntry(key=key, value=value, line=lineno)
    return entries


def parse_env_file(path: Path) -> Dict[str, EnvEntry]:
    """Read and parse a .env file from disk."""
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_env_string(content)
