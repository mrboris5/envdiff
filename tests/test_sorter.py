"""Tests for envdiff.sorter."""

import pytest
from envdiff.sorter import sort_env_lines, sort_env_file, _key_from_line


def test_key_from_line_basic():
    assert _key_from_line("FOO=bar") == "FOO"


def test_key_from_line_export():
    assert _key_from_line("export BAR=baz") == "BAR"


def test_key_from_line_comment_returns_none():
    assert _key_from_line("# comment") is None


def test_key_from_line_blank_returns_none():
    assert _key_from_line("") is None


def test_sort_alphabetically():
    lines = ["ZEBRA=1", "APPLE=2", "MANGO=3"]
    result = sort_env_lines(lines)
    keys = [l.split("=")[0] for l in result.sorted_lines]
    assert keys == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_already_sorted_no_change():
    lines = ["ALPHA=1", "BETA=2", "GAMMA=3"]
    result = sort_env_lines(lines)
    assert not result.was_changed


def test_sort_unsorted_marks_was_changed():
    lines = ["Z=1", "A=2"]
    result = sort_env_lines(lines)
    assert result.was_changed


def test_sort_preserves_comments_attached_to_key():
    lines = ["# zebra comment", "ZEBRA=1", "# apple comment", "APPLE=2"]
    result = sort_env_lines(lines)
    idx_apple_comment = result.sorted_lines.index("# apple comment")
    idx_apple_key = result.sorted_lines.index("APPLE=2")
    assert idx_apple_key == idx_apple_comment + 1


def test_sort_custom_order_pins_keys_first():
    lines = ["ZEBRA=1", "APPLE=2", "MANGO=3"]
    result = sort_env_lines(lines, custom_order=["MANGO"])
    assert result.sorted_lines[0] == "MANGO=3"


def test_sort_moved_keys_populated():
    lines = ["Z=1", "A=2", "M=3"]
    result = sort_env_lines(lines)
    assert len(result.moved_keys) > 0


def test_sort_blank_lines_handled():
    lines = ["B=2", "", "A=1"]
    result = sort_env_lines(lines)
    assert result.sorted_lines is not None
    assert any("A=1" in l for l in result.sorted_lines)


def test_to_env_string_joins_with_newline():
    lines = ["B=2", "A=1"]
    result = sort_env_lines(lines)
    content = result.to_env_string()
    assert "\n" in content


def test_sort_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("Z=1\nA=2\nM=3\n")
    result = sort_env_file(str(f))
    assert result.source == str(f)
    assert result.was_changed
    first_key = result.sorted_lines[0].split("=")[0]
    assert first_key == "A"


def test_sort_env_file_not_found():
    with pytest.raises(FileNotFoundError):
        sort_env_file("/nonexistent/.env")
