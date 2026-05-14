"""Tests for envdiff.syncer module."""

import pytest
from pathlib import Path

from envdiff.core import DiffResult, DiffStatus, EnvEntry
from envdiff.syncer import apply_sync, _replace_key_in_lines


def _entry(key, status, source_value=None, target_value=None):
    return EnvEntry(
        key=key,
        status=status,
        source_value=source_value,
        target_value=target_value,
    )


def _make_diff(*entries):
    return DiffResult(entries=list(entries))


def test_apply_sync_adds_missing_key(tmp_path):
    target = tmp_path / ".env"
    target.write_text("EXISTING=yes\n")
    diff = _make_diff(_entry("NEW_KEY", DiffStatus.MISSING_IN_TARGET, source_value="hello"))
    summary = apply_sync(diff, target)
    assert "NEW_KEY" in summary["added"]
    content = target.read_text()
    assert "NEW_KEY=hello" in content
    assert "EXISTING=yes" in content


def test_apply_sync_skips_differing_without_overwrite(tmp_path):
    target = tmp_path / ".env"
    target.write_text("KEY=old\n")
    diff = _make_diff(_entry("KEY", DiffStatus.VALUE_DIFFERS, source_value="new", target_value="old"))
    summary = apply_sync(diff, target, overwrite_existing=False)
    assert "KEY" in summary["skipped"]
    assert target.read_text() == "KEY=old\n"


def test_apply_sync_updates_with_overwrite(tmp_path):
    target = tmp_path / ".env"
    target.write_text("KEY=old\n")
    diff = _make_diff(_entry("KEY", DiffStatus.VALUE_DIFFERS, source_value="new", target_value="old"))
    summary = apply_sync(diff, target, overwrite_existing=True)
    assert "KEY" in summary["updated"]
    assert "KEY=new" in target.read_text()


def test_apply_sync_dry_run_does_not_write(tmp_path):
    target = tmp_path / ".env"
    target.write_text("EXISTING=yes\n")
    diff = _make_diff(_entry("NEW_KEY", DiffStatus.MISSING_IN_TARGET, source_value="hello"))
    summary = apply_sync(diff, target, dry_run=True)
    assert "NEW_KEY" in summary["added"]
    assert "NEW_KEY" not in target.read_text()


def test_apply_sync_target_does_not_exist(tmp_path):
    target = tmp_path / ".env"
    diff = _make_diff(_entry("FOO", DiffStatus.MISSING_IN_TARGET, source_value="bar"))
    summary = apply_sync(diff, target)
    assert "FOO" in summary["added"]
    assert target.exists()
    assert "FOO=bar" in target.read_text()


def test_replace_key_in_lines():
    lines = ["FOO=old\n", "BAR=keep\n"]
    result = _replace_key_in_lines(lines, "FOO", "new")
    assert result == ["FOO=new\n", "BAR=keep\n"]


def test_replace_key_in_lines_export():
    lines = ["export FOO=old\n"]
    result = _replace_key_in_lines(lines, "FOO", "new")
    assert result == ["export FOO=new\n"]
