"""Encrypt and decrypt sensitive values in .env files using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore

from envdiff.redactor import is_sensitive_key


@dataclass
class EncryptEntry:
    key: str
    original: str
    result: str
    encrypted: bool

    def __str__(self) -> str:
        state = "encrypted" if self.encrypted else "skipped"
        return f"{self.key}: {state}"


@dataclass
class EncryptResult:
    entries: List[EncryptEntry] = field(default_factory=list)

    @property
    def encrypted_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.encrypted]

    @property
    def skipped_keys(self) -> List[str]:
        return [e.key for e in self.entries if not e.encrypted]

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.result for e in self.entries}


def generate_key() -> str:
    """Generate a new Fernet key as a URL-safe base64 string."""
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography package is required: pip install cryptography")
    return Fernet.generate_key().decode()


def encrypt_env_dict(
    env: Dict[str, str],
    key: str,
    sensitive_only: bool = True,
) -> EncryptResult:
    """Encrypt values in an env dict. If sensitive_only, only encrypt sensitive keys."""
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography package is required: pip install cryptography")
    f = Fernet(key.encode() if isinstance(key, str) else key)
    result = EncryptResult()
    for k, v in env.items():
        should_encrypt = (not sensitive_only) or is_sensitive_key(k)
        if should_encrypt:
            encrypted_value = f.encrypt(v.encode()).decode()
            result.entries.append(EncryptEntry(key=k, original=v, result=encrypted_value, encrypted=True))
        else:
            result.entries.append(EncryptEntry(key=k, original=v, result=v, encrypted=False))
    return result


def decrypt_env_dict(
    env: Dict[str, str],
    key: str,
) -> Dict[str, str]:
    """Decrypt all Fernet-encrypted values in an env dict. Non-encrypted values pass through."""
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography package is required: pip install cryptography")
    f = Fernet(key.encode() if isinstance(key, str) else key)
    out: Dict[str, str] = {}
    for k, v in env.items():
        try:
            out[k] = f.decrypt(v.encode()).decode()
        except (InvalidToken, Exception):
            out[k] = v
    return out
