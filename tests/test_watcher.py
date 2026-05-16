"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envdiff.watcher import EnvWatcher, WatchEvent, _file_hash


@pytest.fixture
def env_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    return f


def test_file_hash_returns_string(env_file):
    h = _file_hash(str(env_file))
    assert isinstance(h, str)
    assert len(h) == 32  # MD5 hex


def test_file_hash_changes_on_content_change(env_file):
    h1 = _file_hash(str(env_file))
    env_file.write_text("FOO=changed\n")
    h2 = _file_hash(str(env_file))
    assert h1 != h2


def test_watch_event_str(env_file):
    from envdiff.core import diff_envs

    diff = diff_envs({"A": "1"}, {"A": "2", "B": "3"})
    event = WatchEvent(
        path=str(env_file),
        previous_hash="abc",
        current_hash="def",
        diff=diff,
    )
    s = str(event)
    assert "WatchEvent" in s
    assert "changed=1" in s
    assert "added=1" in s


def test_watcher_detects_change(env_file):
    events = []
    watcher = EnvWatcher(paths=[str(env_file)], interval=0.05)

    def on_change(event: WatchEvent):
        events.append(event)

    # Modify file after watcher initialises
    original = env_file.read_text()

    def _modify_and_watch():
        # Run 2 cycles; modify between init and first check
        import threading

        def modify():
            time.sleep(0.02)
            env_file.write_text(original + "NEW_KEY=hello\n")

        t = threading.Thread(target=modify, daemon=True)
        t.start()
        watcher.start(on_change, max_cycles=3)

    _modify_and_watch()
    assert len(events) >= 1
    assert events[0].path == str(env_file)


def test_watcher_no_event_when_unchanged(env_file):
    events = []
    watcher = EnvWatcher(paths=[str(env_file)], interval=0.05)
    watcher.start(lambda e: events.append(e), max_cycles=2)
    assert events == []


def test_watcher_diff_contains_added_key(env_file):
    events = []
    watcher = EnvWatcher(paths=[str(env_file)], interval=0.05)

    import threading

    def modify():
        time.sleep(0.02)
        env_file.write_text(env_file.read_text() + "EXTRA=1\n")

    t = threading.Thread(target=modify, daemon=True)
    t.start()
    watcher.start(lambda e: events.append(e), max_cycles=3)

    assert any("EXTRA" in e.diff.added for e in events)
