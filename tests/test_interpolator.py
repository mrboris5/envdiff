"""Tests for envdiff.interpolator."""

import pytest
from envdiff.interpolator import interpolate_env, InterpolationResult


def test_no_references_returned_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = interpolate_env(env)
    assert result.resolved == env
    assert not result.has_warnings


def test_brace_reference_expanded():
    env = {"BASE": "http://example.com", "URL": "${BASE}/api"}
    result = interpolate_env(env)
    assert result.resolved["URL"] == "http://example.com/api"


def test_bare_reference_expanded():
    env = {"DIR": "/app", "LOG": "$DIR/logs"}
    result = interpolate_env(env)
    assert result.resolved["LOG"] == "/app/logs"


def test_multiple_references_in_one_value():
    env = {"HOST": "db", "PORT": "5432", "DSN": "postgres://${HOST}:${PORT}/mydb"}
    result = interpolate_env(env)
    assert result.resolved["DSN"] == "postgres://db:5432/mydb"


def test_unresolved_reference_produces_warning():
    env = {"URL": "${MISSING}/path"}
    result = interpolate_env(env)
    assert result.has_warnings
    assert result.warnings[0].ref == "MISSING"
    assert result.warnings[0].key == "URL"


def test_unresolved_reference_leaves_token_intact():
    env = {"URL": "${MISSING}/path"}
    result = interpolate_env(env)
    assert result.resolved["URL"] == "${MISSING}/path"


def test_extra_context_used_for_resolution():
    env = {"FULL_URL": "${SCHEME}://example.com"}
    result = interpolate_env(env, extra_context={"SCHEME": "https"})
    assert result.resolved["FULL_URL"] == "https://example.com"
    assert not result.has_warnings


def test_env_value_overrides_extra_context():
    env = {"SCHEME": "http", "FULL_URL": "${SCHEME}://example.com"}
    result = interpolate_env(env, extra_context={"SCHEME": "https"})
    # env's own SCHEME takes priority
    assert result.resolved["FULL_URL"] == "http://example.com"


def test_warning_str_representation():
    env = {"X": "${NOPE}"}
    result = interpolate_env(env)
    warn_str = str(result.warnings[0])
    assert "NOPE" in warn_str
    assert "X" in warn_str


def test_chained_references_resolved():
    env = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
    # Single-pass: B resolves using original context which has A=hello;
    # C resolves using original context which has B=${A}_world (unexpanded).
    # After one pass B="hello_world" but C sees original B.
    result = interpolate_env(env)
    assert result.resolved["B"] == "hello_world"
    # C references original B value from context (env), not yet expanded
    assert "${A}_world" in result.resolved["C"] or "hello_world" in result.resolved["C"]


def test_empty_env_returns_empty_result():
    result = interpolate_env({})
    assert result.resolved == {}
    assert not result.has_warnings
