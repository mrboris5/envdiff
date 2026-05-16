"""Classify env keys into semantic categories based on naming patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Pattern-to-category mapping (checked in order)
_CATEGORY_PATTERNS: List[tuple[str, str]] = [
    ("DATABASE_URL", "database"),
    ("DB_", "database"),
    ("POSTGRES", "database"),
    ("MYSQL", "database"),
    ("REDIS", "cache"),
    ("CACHE_", "cache"),
    ("MEMCACHE", "cache"),
    ("SECRET", "security"),
    ("PASSWORD", "security"),
    ("TOKEN", "security"),
    ("API_KEY", "security"),
    ("PRIVATE_KEY", "security"),
    ("AWS_", "cloud"),
    ("GCP_", "cloud"),
    ("AZURE_", "cloud"),
    ("S3_", "cloud"),
    ("LOG_", "logging"),
    ("LOGGING_", "logging"),
    ("SENTRY_", "logging"),
    ("PORT", "network"),
    ("HOST", "network"),
    ("URL", "network"),
    ("ENDPOINT", "network"),
    ("DEBUG", "app"),
    ("ENV", "app"),
    ("ENVIRONMENT", "app"),
    ("APP_", "app"),
    ("FLASK_", "app"),
    ("DJANGO_", "app"),
]

_UNCATEGORIZED = "uncategorized"


def classify_key(key: str) -> str:
    """Return the category name for a given env key."""
    upper = key.upper()
    for pattern, category in _CATEGORY_PATTERNS:
        if pattern in upper:
            return category
    return _UNCATEGORIZED


@dataclass
class ClassifyResult:
    categories: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, key: str, category: Optional[str] = None) -> None:
        cat = category if category is not None else classify_key(key)
        self.categories.setdefault(cat, []).append(key)

    def category_for(self, key: str) -> str:
        for cat, keys in self.categories.items():
            if key in keys:
                return cat
        return _UNCATEGORIZED

    def to_dict(self) -> Dict[str, List[str]]:
        return dict(self.categories)

    def __str__(self) -> str:
        lines = []
        for cat in sorted(self.categories):
            keys = ", ".join(sorted(self.categories[cat]))
            lines.append(f"[{cat}] {keys}")
        return "\n".join(lines)


def classify_env(env: Dict[str, str]) -> ClassifyResult:
    """Classify all keys in an env dict and return a ClassifyResult."""
    result = ClassifyResult()
    for key in env:
        result.add(key)
    return result
