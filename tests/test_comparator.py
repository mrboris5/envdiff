"""Tests for envdiff.comparator — multi-environment comparison."""

import pytest

from envdiff.comparator import compare_many, CompareReport
from envdiff.core import DiffStatus


SOURCE = {"APP_ENV": "production", "DB_URL": "postgres://prod", "SECRET_KEY": "abc"}

STAGING = {"APP_ENV": "staging", "DB_URL": "postgres://staging"}
# Missing SECRET_KEY, different values for APP_ENV and DB_URL

DEV = {"APP_ENV": "development", "DB_URL": "postgres://dev", "SECRET_KEY": "abc", "DEBUG": "true"}
# DEBUG is extra (missing in source)


@pytest.fixture
def report() -> CompareReport:
    return compare_many(
        source_name="production",
        source=SOURCE,
        targets={"staging": STAGING, "dev": DEV},
    )


def test_report_lists_environments(report):
    assert set(report.environments()) == {"staging", "dev"}


def test_report_source_name(report):
    assert report.source_name == "production"


def test_has_any_diff_when_differences_exist(report):
    assert report.has_any_diff() is True


def test_has_any_diff_false_when_identical():
    env = {"KEY": "val"}
    r = compare_many("src", env, {"copy": dict(env)})
    assert r.has_any_diff() is False


def test_keys_missing_in_staging(report):
    missing = report.keys_missing_in("staging")
    assert "SECRET_KEY" in missing


def test_keys_missing_in_unknown_target(report):
    assert report.keys_missing_in("nonexistent") == []


def test_keys_extra_in_dev(report):
    extra = report.keys_extra_in("dev")
    assert "DEBUG" in extra


def test_keys_extra_in_staging_empty(report):
    # staging has no extra keys beyond source
    extra = report.keys_extra_in("staging")
    assert extra == []


def test_summary_contains_all_targets(report):
    summary = report.summary()
    assert "staging" in summary
    assert "dev" in summary


def test_summary_staging_has_missing_in_target(report):
    summary = report.summary()
    staging = summary["staging"]
    assert staging.get(DiffStatus.MISSING_IN_TARGET.value, 0) >= 1


def test_summary_dev_has_missing_in_source(report):
    summary = report.summary()
    dev = summary["dev"]
    assert dev.get(DiffStatus.MISSING_IN_SOURCE.value, 0) >= 1


def test_compare_many_empty_targets():
    r = compare_many("src", {"A": "1"}, {})
    assert r.environments() == []
    assert r.has_any_diff() is False
