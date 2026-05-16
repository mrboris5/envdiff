"""Tests for envdiff.cli_sorter."""

import argparse
import json
import pytest

from envdiff.cli_sorter import cmd_sort, register_sort_commands


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("ZEBRA=1\nAPPLE=2\nMANGO=3\n")
    return f


@pytest.fixture
def sorted_env_file(tmp_path):
    f = tmp_path / ".env.sorted"
    f.write_text("ALPHA=1\nBETA=2\nGAMMA=3\n")
    return f


def _ns(env_file, **kwargs):
    defaults = dict(env_file=str(env_file), write=False, order=None, format="text")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_sort_text_output(env_file, capsys):
    rc = cmd_sort(_ns(env_file))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Sorted" in out or "sorted" in out.lower()


def test_sort_already_sorted_says_so(sorted_env_file, capsys):
    rc = cmd_sort(_ns(sorted_env_file))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Already sorted" in out


def test_sort_json_output(env_file, capsys):
    rc = cmd_sort(_ns(env_file, format="json"))
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert "was_changed" in data
    assert "sorted_content" in data
    assert "moved_keys" in data


def test_sort_write_flag_updates_file(env_file):
    rc = cmd_sort(_ns(env_file, write=True))
    assert rc == 0
    content = env_file.read_text()
    keys = [l.split("=")[0] for l in content.splitlines() if "=" in l]
    assert keys == sorted(keys)


def test_sort_missing_file_returns_error(tmp_path, capsys):
    rc = cmd_sort(_ns(tmp_path / "missing.env"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_sort_custom_order(env_file, capsys):
    rc = cmd_sort(_ns(env_file, format="json", order="MANGO"))
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    first_key = data["sorted_content"].splitlines()[0].split("=")[0]
    assert first_key == "MANGO"


def test_register_sort_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_sort_commands(sub)
    args = parser.parse_args(["sort", "some.env"])
    assert args.env_file == "some.env"
    assert args.write is False
