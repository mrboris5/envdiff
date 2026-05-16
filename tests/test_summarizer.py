"""Tests for envdiff.summarizer and envdiff.cli_summarizer."""
from __future__ import annotations

import json
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.summarizer import summarize_env
from envdiff.cli_summarizer import cmd_summarize


SAMPLE_ENV = textwrap.dedent("""\
    DB_HOST=localhost
    DB_PASSWORD=secret123
    API_KEY=abc
    CACHE_URL=redis://localhost
    EMPTY_VAR=
    lowercase_key=bad
""").splitlines(keepends=True)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("".join(SAMPLE_ENV))
    return p


def _make_dict():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret123",
        "API_KEY": "abc",
        "CACHE_URL": "redis://localhost",
        "EMPTY_VAR": "",
        "lowercase_key": "bad",
    }


def test_total_keys_count():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    assert report.total_keys == 6


def test_sensitive_keys_counted():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    # DB_PASSWORD and API_KEY are sensitive
    assert report.sensitive_count >= 2


def test_empty_value_counted():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    assert report.empty_value_count == 1


def test_category_counts_present():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    assert isinstance(report.category_counts, dict)
    assert len(report.category_counts) > 0


def test_lint_errors_detected():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    # lowercase_key should trigger a lint warning
    assert report.lint_warn_count >= 1


def test_to_dict_has_expected_keys():
    report = summarize_env("test.env", _make_dict(), SAMPLE_ENV)
    d = report.to_dict()
    assert "source" in d
    assert "total_keys" in d
    assert "sensitive_count" in d
    assert "empty_value_count" in d
    assert "category_counts" in d
    assert "lint_error_count" in d
    assert "lint_warn_count" in d


def test_cmd_summarize_text_output(env_file, capsys):
    args = Namespace(env_file=str(env_file), format="text")
    rc = cmd_summarize(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Summary for" in captured.out
    assert "Total keys" in captured.out


def test_cmd_summarize_json_output(env_file, capsys):
    args = Namespace(env_file=str(env_file), format="json")
    rc = cmd_summarize(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_keys"] == 6


def test_cmd_summarize_missing_file(tmp_path, capsys):
    args = Namespace(env_file=str(tmp_path / "missing.env"), format="text")
    rc = cmd_summarize(args)
    assert rc == 2
