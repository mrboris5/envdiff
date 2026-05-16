"""Tests for envdiff.renamer."""
import pytest
from envdiff.renamer import RenameEntry, RenameResult, rename_keys


def _lines(text: str):
    return text.splitlines(keepends=True)


def test_rename_applies_simple_key():
    lines = _lines("FOO=bar\nBAZ=qux\n")
    entry = RenameEntry(old_key="FOO", new_key="FOO_NEW")
    result = rename_keys(lines, [entry])
    assert result.has_changes
    assert len(result.applied) == 1
    assert result.applied[0].new_key == "FOO_NEW"
    assert "FOO_NEW=bar" in result.to_env_string()


def test_rename_skips_missing_key():
    lines = _lines("BAZ=qux\n")
    entry = RenameEntry(old_key="MISSING", new_key="RENAMED")
    result = rename_keys(lines, [entry])
    assert not result.has_changes
    assert "MISSING" in result.skipped


def test_rename_preserves_comments_and_blanks():
    lines = _lines("# comment\n\nFOO=1\n")
    entry = RenameEntry(old_key="FOO", new_key="FOO_V2")
    result = rename_keys(lines, [entry])
    env_str = result.to_env_string()
    assert "# comment" in env_str
    assert "FOO_V2=1" in env_str


def test_rename_dry_run_does_not_change_lines():
    lines = _lines("KEY=value\n")
    entry = RenameEntry(old_key="KEY", new_key="KEY_NEW")
    result = rename_keys(lines, [entry], dry_run=True)
    assert result.has_changes
    assert "KEY=value" in result.to_env_string()
    assert "KEY_NEW" not in result.to_env_string()


def test_rename_multiple_entries():
    lines = _lines("A=1\nB=2\nC=3\n")
    renames = [
        RenameEntry(old_key="A", new_key="A_NEW"),
        RenameEntry(old_key="C", new_key="C_NEW"),
    ]
    result = rename_keys(lines, renames)
    env_str = result.to_env_string()
    assert "A_NEW=1" in env_str
    assert "B=2" in env_str
    assert "C_NEW=3" in env_str
    assert len(result.applied) == 2


def test_rename_entry_str_with_note():
    e = RenameEntry(old_key="OLD", new_key="NEW", note="deprecated")
    assert "OLD -> NEW" in str(e)
    assert "deprecated" in str(e)


def test_rename_entry_str_without_note():
    e = RenameEntry(old_key="OLD", new_key="NEW")
    assert str(e) == "OLD -> NEW"


def test_rename_entry_round_trip():
    e = RenameEntry(old_key="K", new_key="K2", note="test")
    restored = RenameEntry.from_dict(e.to_dict())
    assert restored.old_key == e.old_key
    assert restored.new_key == e.new_key
    assert restored.note == e.note


def test_rename_handles_export_prefix():
    lines = _lines("export DB_HOST=localhost\n")
    entry = RenameEntry(old_key="DB_HOST", new_key="DATABASE_HOST")
    result = rename_keys(lines, [entry])
    assert result.has_changes
    assert "DATABASE_HOST" in result.to_env_string()
