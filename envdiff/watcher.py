"""Watch .env files for changes and report diffs."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from envdiff.parser import parse_env_file
from envdiff.core import diff_envs, DiffResult


@dataclass
class WatchEvent:
    path: str
    previous_hash: Optional[str]
    current_hash: str
    diff: DiffResult

    def __str__(self) -> str:
        return (
            f"WatchEvent(path={self.path!r}, "
            f"added={len(self.diff.added)}, "
            f"removed={len(self.diff.removed)}, "
            f"changed={len(self.diff.changed)})"
        )


def _file_hash(path: str) -> str:
    """Return MD5 hex digest of file contents."""
    content = Path(path).read_bytes()
    return hashlib.md5(content).hexdigest()


@dataclass
class EnvWatcher:
    paths: list
    interval: float = 1.0
    _hashes: Dict[str, Optional[str]] = field(default_factory=dict, init=False)
    _snapshots: Dict[str, dict] = field(default_factory=dict, init=False)

    def start(self, callback: Callable[[WatchEvent], None], max_cycles: int = 0) -> None:
        """Poll files for changes, calling callback on each detected change."""
        for p in self.paths:
            self._hashes[p] = _file_hash(p) if Path(p).exists() else None
            self._snapshots[p] = parse_env_file(p) if Path(p).exists() else {}

        cycles = 0
        while True:
            time.sleep(self.interval)
            for p in self.paths:
                self._check(p, callback)
            cycles += 1
            if max_cycles and cycles >= max_cycles:
                break

    def _check(self, path: str, callback: Callable[[WatchEvent], None]) -> None:
        if not Path(path).exists():
            return
        new_hash = _file_hash(path)
        old_hash = self._hashes.get(path)
        if new_hash == old_hash:
            return
        old_env = self._snapshots.get(path, {})
        new_env = parse_env_file(path)
        result = diff_envs(old_env, new_env)
        event = WatchEvent(
            path=path,
            previous_hash=old_hash,
            current_hash=new_hash,
            diff=result,
        )
        self._hashes[path] = new_hash
        self._snapshots[path] = new_env
        callback(event)
