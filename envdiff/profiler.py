"""Environment profile management: named sets of expected keys and rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os


@dataclass
class EnvProfile:
    """A named profile describing expected keys and optional metadata."""

    name: str
    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required_keys": self.required_keys,
            "optional_keys": self.optional_keys,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvProfile":
        return cls(
            name=data["name"],
            required_keys=data.get("required_keys", []),
            optional_keys=data.get("optional_keys", []),
            description=data.get("description", ""),
        )

    def all_known_keys(self) -> List[str]:
        return list(self.required_keys) + list(self.optional_keys)


@dataclass
class ProfileCheckResult:
    """Result of checking an env dict against a profile."""

    profile_name: str
    missing_required: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.missing_required) == 0

    def summary(self) -> str:
        parts = [f"Profile '{self.profile_name}':"]
        if self.passed:
            parts.append("  OK — all required keys present.")
        else:
            for k in self.missing_required:
                parts.append(f"  MISSING  {k}")
        for k in self.unknown_keys:
            parts.append(f"  UNKNOWN  {k}")
        return "\n".join(parts)


def check_profile(env: Dict[str, str], profile: EnvProfile) -> ProfileCheckResult:
    """Check an env dict against a profile, returning a ProfileCheckResult."""
    known = set(profile.all_known_keys())
    missing = [k for k in profile.required_keys if k not in env]
    unknown = [k for k in env if k not in known]
    return ProfileCheckResult(
        profile_name=profile.name,
        missing_required=missing,
        unknown_keys=unknown,
    )


def load_profile(path: str) -> EnvProfile:
    """Load a profile from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return EnvProfile.from_dict(data)


def save_profile(profile: EnvProfile, path: str) -> None:
    """Save a profile to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(profile.to_dict(), fh, indent=2)
