"""Tests for envdiff.cli_tagger."""

import argparse
import json
import os
import pytest

from envdiff.cli_tagger import cmd_tag_add, cmd_tag_list, cmd_tag_remove
from envdiff.tagger import TagStore


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\nPORT=8080\n")
    return str(p)


@pytest.fixture
def tag_file(tmp_path):
    return str(tmp_path / "tags.json")


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": None, "key": None, "tags": "", "note": None,
                "tag_file": None, "filter": None, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_tag_add_creates_entry(env_file, tag_file):
    ns = _ns(env_file=env_file, key="DATABASE_URL", tags="db,required", tag_file=tag_file)
    rc = cmd_tag_add(ns)
    assert rc == 0
    store = TagStore.load(tag_file)
    e = store.get("DATABASE_URL")
    assert e is not None
    assert "db" in e.tags and "required" in e.tags


def test_tag_add_missing_key_returns_error(env_file, tag_file):
    ns = _ns(env_file=env_file, key="NONEXISTENT", tags="x", tag_file=tag_file)
    rc = cmd_tag_add(ns)
    assert rc == 1


def test_tag_add_with_note(env_file, tag_file):
    ns = _ns(env_file=env_file, key="SECRET_KEY", tags="secret", note="rotate often", tag_file=tag_file)
    cmd_tag_add(ns)
    store = TagStore.load(tag_file)
    assert store.get("SECRET_KEY").note == "rotate often"


def test_tag_remove_existing(env_file, tag_file):
    store = TagStore()
    store.add("PORT", ["infra"])
    store.save(tag_file)
    ns = _ns(key="PORT", tag_file=tag_file)
    rc = cmd_tag_remove(ns)
    assert rc == 0
    store2 = TagStore.load(tag_file)
    assert store2.get("PORT") is None


def test_tag_remove_missing_key_returns_error(tag_file):
    store = TagStore()
    store.save(tag_file)
    ns = _ns(key="GHOST", tag_file=tag_file)
    rc = cmd_tag_remove(ns)
    assert rc == 1


def test_tag_list_text_output(tag_file, capsys):
    store = TagStore()
    store.add("PORT", ["infra"])
    store.save(tag_file)
    ns = _ns(tag_file=tag_file, format="text", filter=None)
    rc = cmd_tag_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "PORT" in out
    assert "infra" in out


def test_tag_list_json_output(tag_file, capsys):
    store = TagStore()
    store.add("SECRET_KEY", ["secret"])
    store.save(tag_file)
    ns = _ns(tag_file=tag_file, format="json", filter=None)
    cmd_tag_list(ns)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["key"] == "SECRET_KEY"


def test_tag_list_filter_by_tag(tag_file, capsys):
    store = TagStore()
    store.add("A", ["infra"])
    store.add("B", ["secret"])
    store.save(tag_file)
    ns = _ns(tag_file=tag_file, format="text", filter="infra")
    cmd_tag_list(ns)
    out = capsys.readouterr().out
    assert "A" in out
    assert "B" not in out
