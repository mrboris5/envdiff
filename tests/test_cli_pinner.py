"""Tests for envdiff.cli_pinner."""
import json
import os
import pytest
from argparse import Namespace
from envdiff.cli_pinner import cmd_pin_add, cmd_pin_check, cmd_pin_list, cmd_pin_remove
from envdiff.pinner import save_pin_store, PinStore


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / "test.env"
    p.write_text("DB_HOST=localhost\nAPI_KEY=secret123\nPORT=5432\n")
    return str(p)


@pytest.fixture()
def pin_file(tmp_path):
    return str(tmp_path / "pins.json")


def _ns(**kwargs) -> Namespace:
    defaults = {"format": "text", "note": None}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_pin_add_creates_pin(env_file, pin_file):
    args = _ns(env_file=env_file, key="DB_HOST", pin_file=pin_file)
    rc = cmd_pin_add(args)
    assert rc == 0


def test_pin_add_missing_key_returns_error(env_file, pin_file):
    args = _ns(env_file=env_file, key="NONEXISTENT", pin_file=pin_file)
    rc = cmd_pin_add(args)
    assert rc == 1


def test_pin_list_empty(pin_file, capsys):
    args = _ns(pin_file=pin_file, format="text")
    rc = cmd_pin_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No keys pinned" in out


def test_pin_list_json(env_file, pin_file, capsys):
    add_args = _ns(env_file=env_file, key="PORT", pin_file=pin_file)
    cmd_pin_add(add_args)
    list_args = _ns(pin_file=pin_file, format="json")
    rc = cmd_pin_list(list_args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["key"] == "PORT"


def test_pin_check_no_drift(env_file, pin_file, capsys):
    add_args = _ns(env_file=env_file, key="DB_HOST", pin_file=pin_file)
    cmd_pin_add(add_args)
    check_args = _ns(env_file=env_file, pin_file=pin_file, format="text")
    rc = cmd_pin_check(check_args)
    assert rc == 0
    assert "match" in capsys.readouterr().out


def test_pin_check_detects_drift(tmp_path, pin_file, capsys):
    original = tmp_path / "orig.env"
    original.write_text("DB_HOST=localhost\n")
    add_args = _ns(env_file=str(original), key="DB_HOST", pin_file=pin_file)
    cmd_pin_add(add_args)

    changed = tmp_path / "changed.env"
    changed.write_text("DB_HOST=remotehost\n")
    check_args = _ns(env_file=str(changed), pin_file=pin_file, format="text")
    rc = cmd_pin_check(check_args)
    assert rc == 1


def test_pin_remove_existing(env_file, pin_file, capsys):
    add_args = _ns(env_file=env_file, key="API_KEY", pin_file=pin_file)
    cmd_pin_add(add_args)
    rm_args = _ns(key="API_KEY", pin_file=pin_file, format="text")
    rc = cmd_pin_remove(rm_args)
    assert rc == 0
    assert "Unpinned" in capsys.readouterr().out


def test_pin_remove_nonexistent(pin_file):
    args = _ns(key="GHOST", pin_file=pin_file, format="text")
    rc = cmd_pin_remove(args)
    assert rc == 1
