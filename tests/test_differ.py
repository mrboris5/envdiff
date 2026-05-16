"""Tests for envdiff.differ multi-file diffing."""
from __future__ import annotations

import textwrap
import pytest

from envdiff.differ import multi_diff, MultiDiffReport, PairDiff
from envdiff.core import diff_envs
from envdiff.parser import parse_env_string


def _write_env(tmp_path, name: str, content: str):
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return str(p)


@pytest.fixture()
def env_files(tmp_path):
    base = _write_env(tmp_path, "base.env", """
        APP_NAME=myapp
        DEBUG=false
        SECRET_KEY=abc123
    """)
    target_a = _write_env(tmp_path, "target_a.env", """
        APP_NAME=myapp
        DEBUG=true
        SECRET_KEY=abc123
    """)
    target_b = _write_env(tmp_path, "target_b.env", """
        APP_NAME=myapp
        DEBUG=true
        NEW_KEY=hello
    """)
    return base, target_a, target_b


def test_multi_diff_returns_report(env_files):
    base, target_a, target_b = env_files
    report = multi_diff(base, [target_a, target_b])
    assert isinstance(report, MultiDiffReport)
    assert len(report.pairs) == 2


def test_multi_diff_base_name_set(env_files):
    base, target_a, _ = env_files
    report = multi_diff(base, [target_a])
    assert report.base == base


def test_has_any_diff_true_when_differences(env_files):
    base, target_a, target_b = env_files
    report = multi_diff(base, [target_a, target_b])
    assert report.has_any_diff is True


def test_has_any_diff_false_when_identical(tmp_path):
    base = _write_env(tmp_path, "base.env", "KEY=val\n")
    same = _write_env(tmp_path, "same.env", "KEY=val\n")
    report = multi_diff(base, [same])
    assert report.has_any_diff is False


def test_keys_always_differing_finds_common_diff_keys(env_files):
    base, target_a, target_b = env_files
    report = multi_diff(base, [target_a, target_b])
    always = report.keys_always_differing()
    # DEBUG differs in both targets
    assert "DEBUG" in always


def test_keys_always_differing_excludes_partial_diff(env_files):
    base, target_a, target_b = env_files
    report = multi_diff(base, [target_a, target_b])
    always = report.keys_always_differing()
    # SECRET_KEY only differs in target_b (missing), not target_a
    # NEW_KEY only in target_b
    assert "NEW_KEY" not in always


def test_pair_summary_format(env_files):
    base, target_a, _ = env_files
    report = multi_diff(base, [target_a])
    summary = report.pairs[0].summary()
    assert "vs" in summary
    assert "added" in summary


def test_to_dict_structure(env_files):
    base, target_a, target_b = env_files
    report = multi_diff(base, [target_a, target_b])
    d = report.to_dict()
    assert "base" in d
    assert "pairs" in d
    assert "has_any_diff" in d
    assert "keys_always_differing" in d
    assert len(d["pairs"]) == 2


def test_missing_file_raises(tmp_path):
    base = _write_env(tmp_path, "base.env", "KEY=val\n")
    with pytest.raises(FileNotFoundError):
        multi_diff(base, [str(tmp_path / "ghost.env")])
