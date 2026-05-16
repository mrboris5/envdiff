"""Tests for envdiff.differ_multi (key-frequency analysis)."""
import pytest
from envdiff.differ_multi import KeyFrequency, analyse_frequency


ENV_A = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc"}
ENV_B = {"DB_HOST": "prod-db", "DB_PORT": "5432", "API_URL": "https://api"}
ENV_C = {"DB_HOST": "staging", "API_URL": "https://staging"}


def test_universal_key_detected():
    report = analyse_frequency([ENV_A, ENV_B, ENV_C], ["a", "b", "c"])
    universal = {e.key for e in report.universal_keys()}
    assert "DB_HOST" in universal


def test_non_universal_key_not_in_universal():
    report = analyse_frequency([ENV_A, ENV_B, ENV_C], ["a", "b", "c"])
    universal = {e.key for e in report.universal_keys()}
    assert "SECRET_KEY" not in universal


def test_count_is_correct():
    report = analyse_frequency([ENV_A, ENV_B, ENV_C], ["a", "b", "c"])
    by_key = {e.key: e for e in report.entries}
    assert by_key["DB_HOST"].count == 3
    assert by_key["SECRET_KEY"].count == 1
    assert by_key["API_URL"].count == 2


def test_coverage_fraction():
    report = analyse_frequency([ENV_A, ENV_B, ENV_C], ["a", "b", "c"])
    by_key = {e.key: e for e in report.entries}
    assert by_key["API_URL"].coverage == pytest.approx(2 / 3)


def test_sparse_keys_threshold():
    report = analyse_frequency([ENV_A, ENV_B, ENV_C], ["a", "b", "c"])
    sparse = report.sparse_keys(threshold=0.5)
    sparse_names = {e.key for e in sparse}
    # SECRET_KEY appears in 1/3 ≈ 0.33 which is < 0.5
    assert "SECRET_KEY" in sparse_names
    # DB_HOST appears in 3/3 = 1.0 which is NOT sparse
    assert "DB_HOST" not in sparse_names


def test_sources_list_populated():
    report = analyse_frequency([ENV_A, ENV_B], ["alpha", "beta"])
    by_key = {e.key: e for e in report.entries}
    assert "alpha" in by_key["DB_HOST"].sources
    assert "beta" in by_key["DB_HOST"].sources


def test_auto_generated_source_names():
    report = analyse_frequency([ENV_A, ENV_B])
    by_key = {e.key: e for e in report.entries}
    assert "env0" in by_key["DB_HOST"].sources
    assert "env1" in by_key["DB_HOST"].sources


def test_to_dict_has_required_fields():
    kf = KeyFrequency(key="FOO", count=2, total=3, sources=["a", "b"])
    d = kf.to_dict()
    for field in ("key", "count", "total", "coverage", "is_universal", "sources"):
        assert field in d


def test_str_representation():
    kf = KeyFrequency(key="FOO", count=1, total=4, sources=["a"])
    s = str(kf)
    assert "FOO" in s
    assert "1/4" in s
    assert "25%" in s


def test_empty_envs_returns_empty_report():
    report = analyse_frequency([], [])
    assert report.entries == []


def test_single_env_all_keys_universal():
    report = analyse_frequency([ENV_A], ["only"])
    assert all(e.is_universal for e in report.entries)
