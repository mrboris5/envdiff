"""Tests for envdiff.formatter."""

from pathlib import Path

from envdiff.core import DiffResult, DiffStatus
from envdiff.formatter import format_diff_text, format_diff_json


def _make_result() -> DiffResult:
    """Build a minimal DiffResult fixture for testing."""
    return DiffResult(
        source_file=Path(".env.staging"),
        target_file=Path(".env.production"),
        entries=[
            # Using a simple namespace-style object to satisfy DiffResult
        ],
    )


def _make_entry(key, status, src=None, tgt=None):
    from types import SimpleNamespace
    return SimpleNamespace(key=key, status=status, source_value=src, target_value=tgt)


def test_format_diff_text_contains_header(tmp_path):
    result = DiffResult(
        source_file=Path(".env.dev"),
        target_file=Path(".env.prod"),
        entries=[],
    )
    output = format_diff_text(result)
    assert ".env.dev" in output
    assert ".env.prod" in output


def test_format_diff_text_summary_line():
    result = DiffResult(
        source_file=Path("a"),
        target_file=Path("b"),
        entries=[],
    )
    output = format_diff_text(result)
    assert "Summary:" in output
    assert "added" in output


def test_format_diff_json_structure():
    result = DiffResult(
        source_file=Path(".env.dev"),
        target_file=Path(".env.prod"),
        entries=[],
    )
    data = format_diff_json(result)
    assert data["source_file"] == ".env.dev"
    assert data["target_file"] == ".env.prod"
    assert "summary" in data
    assert "entries" in data
    assert isinstance(data["has_diff"], bool)


def test_format_diff_json_summary_keys():
    result = DiffResult(
        source_file=Path("a"),
        target_file=Path("b"),
        entries=[],
    )
    summary = format_diff_json(result)["summary"]
    for key in ("added", "missing", "changed", "same"):
        assert key in summary
