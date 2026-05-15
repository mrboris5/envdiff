"""Tests for envdiff.auditor."""

import json
import os

import pytest

from envdiff.auditor import AuditEvent, AuditLog, build_diff_event
from envdiff.core import DiffResult, DiffStatus, EnvEntry


def _make_event(**kwargs) -> AuditEvent:
    defaults = dict(operation="diff", source=".env", target=".env.prod", keys_affected=[], details="")
    defaults.update(kwargs)
    return AuditEvent(**defaults)


def test_audit_event_str_includes_operation_and_source():
    event = _make_event(operation="sync", source=".env", target=".env.prod")
    text = str(event)
    assert "SYNC" in text
    assert ".env" in text
    assert ".env.prod" in text


def test_audit_event_str_includes_keys_when_present():
    event = _make_event(keys_affected=["DB_HOST", "SECRET_KEY"])
    text = str(event)
    assert "DB_HOST" in text
    assert "SECRET_KEY" in text


def test_audit_event_str_no_target():
    event = _make_event(operation="validate", target=None)
    text = str(event)
    assert "->" not in text


def test_audit_event_to_dict_has_all_fields():
    event = _make_event(details="2 added")
    d = event.to_dict()
    assert set(d.keys()) == {"operation", "source", "target", "timestamp", "keys_affected", "details"}
    assert d["details"] == "2 added"


def test_audit_log_records_and_retrieves_events():
    log = AuditLog()
    log.record(_make_event(operation="diff"))
    log.record(_make_event(operation="sync"))
    assert len(log.events) == 2
    assert log.events[0].operation == "diff"


def test_audit_log_to_json_is_valid_json():
    log = AuditLog()
    log.record(_make_event(keys_affected=["FOO"]))
    data = json.loads(log.to_json())
    assert isinstance(data, list)
    assert data[0]["keys_affected"] == ["FOO"]


def test_audit_log_to_text_empty():
    log = AuditLog()
    assert "No audit events" in log.to_text()


def test_audit_log_to_text_contains_events():
    log = AuditLog()
    log.record(_make_event(operation="diff", source="a.env"))
    text = log.to_text()
    assert "DIFF" in text
    assert "a.env" in text


def test_audit_log_save_appends_to_file(tmp_path):
    log = AuditLog()
    log.record(_make_event(operation="sync", source=".env"))
    out = str(tmp_path / "audit.log")
    log.save(out)
    content = open(out).read()
    assert "SYNC" in content


def test_build_diff_event_captures_non_same_keys():
    entries = [
        EnvEntry(key="FOO", source_value="1", target_value="1", status=DiffStatus.SAME),
        EnvEntry(key="BAR", source_value="x", target_value=None, status=DiffStatus.MISSING),
        EnvEntry(key="BAZ", source_value="a", target_value="b", status=DiffStatus.DIFFERING),
    ]
    result = DiffResult(entries=entries)
    event = build_diff_event("src.env", "tgt.env", result)
    assert event.operation == "diff"
    assert "BAR" in event.keys_affected
    assert "BAZ" in event.keys_affected
    assert "FOO" not in event.keys_affected
    assert "missing" in event.details
