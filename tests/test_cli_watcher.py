"""Tests for envdiff.cli_watcher."""

from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from envdiff.cli_watcher import cmd_watch, register_watch_commands, _on_change_text, _on_change_json
from envdiff.watcher import WatchEvent
from envdiff.core import diff_envs


@pytest.fixture
def env_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    return f


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"format": "text", "interval": 0.05}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_event(path: str) -> WatchEvent:
    diff = diff_envs({"A": "1"}, {"A": "2", "B": "3"})
    return WatchEvent(path=path, previous_hash="aaa", current_hash="bbb", diff=diff)


def test_on_change_text_prints_path(env_file, capsys):
    event = _make_event(str(env_file))
    _on_change_text(event)
    out = capsys.readouterr().out
    assert str(env_file) in out


def test_on_change_json_is_valid_json(env_file, capsys):
    event = _make_event(str(env_file))
    _on_change_json(event)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["path"] == str(env_file)
    assert "diff" in data
    assert data["current_hash"] == "bbb"


def test_register_watch_commands_adds_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_watch_commands(sub)
    args = parser.parse_args(["watch", "a.env", "--interval", "2.5"])
    assert args.paths == ["a.env"]
    assert args.interval == 2.5


def test_cmd_watch_returns_zero_on_keyboard_interrupt(env_file):
    args = _ns(paths=[str(env_file)], interval=0.05)
    with patch("envdiff.cli_watcher.EnvWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        instance.start.side_effect = KeyboardInterrupt
        result = cmd_watch(args)
    assert result == 0


def test_cmd_watch_json_format_uses_json_callback(env_file):
    args = _ns(paths=[str(env_file)], format="json", interval=0.05)
    with patch("envdiff.cli_watcher.EnvWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        instance.start.side_effect = KeyboardInterrupt
        cmd_watch(args)
        call_args = instance.start.call_args
        callback = call_args[0][0]
    assert callback is not None
    # Verify json callback is used by checking it produces JSON output
    from io import StringIO
    import sys

    event = _make_event(str(env_file))
    captured = []
    with patch("builtins.print", side_effect=lambda x: captured.append(x)):
        callback(event)
    assert captured
    data = json.loads(captured[0])
    assert "path" in data
