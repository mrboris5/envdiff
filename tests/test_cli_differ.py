"""Tests for envdiff.cli_differ CLI commands."""
from __future__ import annotations

import json
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.cli_differ import cmd_multi_diff


@pytest.fixture()
def env_files(tmp_path):
    base = tmp_path / "base.env"
    base.write_text("APP=myapp\nDEBUG=false\n")
    target = tmp_path / "prod.env"
    target.write_text("APP=myapp\nDEBUG=true\nEXTRA=yes\n")
    return str(base), str(target)


def _ns(base, targets, fmt="text"):
    return Namespace(base=base, targets=targets, format=fmt)


def test_multi_diff_text_output(env_files, capsys):
    base, target = env_files
    rc = cmd_multi_diff(_ns(base, [target]))
    out = capsys.readouterr().out
    assert "Base:" in out
    assert "Targets:" in out
    assert rc == 1  # has diff


def test_multi_diff_json_output(env_files, capsys):
    base, target = env_files
    rc = cmd_multi_diff(_ns(base, [target], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "pairs" in data
    assert data["has_any_diff"] is True


def test_multi_diff_no_diff_returns_zero(tmp_path, capsys):
    base = tmp_path / "base.env"
    base.write_text("KEY=val\n")
    same = tmp_path / "same.env"
    same.write_text("KEY=val\n")
    rc = cmd_multi_diff(_ns(str(base), [str(same)]))
    assert rc == 0


def test_multi_diff_missing_file_returns_2(env_files, capsys):
    base, _ = env_files
    rc = cmd_multi_diff(_ns(base, ["/nonexistent/ghost.env"]))
    err = capsys.readouterr().err
    assert rc == 2
    assert "Error" in err


def test_multi_diff_json_keys_always_differing(tmp_path, capsys):
    base = tmp_path / "base.env"
    base.write_text("A=1\nB=2\n")
    t1 = tmp_path / "t1.env"
    t1.write_text("A=9\nB=2\n")
    t2 = tmp_path / "t2.env"
    t2.write_text("A=9\nB=2\n")
    cmd_multi_diff(_ns(str(base), [str(t1), str(t2)], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "A" in data["keys_always_differing"]
