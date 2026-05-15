"""Tests for envdiff.profiler."""

import json
import pytest
from envdiff.profiler import (
    EnvProfile,
    ProfileCheckResult,
    check_profile,
    load_profile,
    save_profile,
)


@pytest.fixture
def simple_profile():
    return EnvProfile(
        name="web",
        required_keys=["DATABASE_URL", "SECRET_KEY"],
        optional_keys=["DEBUG", "LOG_LEVEL"],
        description="Web application profile",
    )


def test_profile_all_known_keys(simple_profile):
    keys = simple_profile.all_known_keys()
    assert "DATABASE_URL" in keys
    assert "DEBUG" in keys
    assert len(keys) == 4


def test_check_profile_passes_when_all_required_present(simple_profile):
    env = {"DATABASE_URL": "postgres://", "SECRET_KEY": "abc"}
    result = check_profile(env, simple_profile)
    assert result.passed is True
    assert result.missing_required == []


def test_check_profile_fails_when_required_missing(simple_profile):
    env = {"DATABASE_URL": "postgres://"}
    result = check_profile(env, simple_profile)
    assert result.passed is False
    assert "SECRET_KEY" in result.missing_required


def test_check_profile_detects_unknown_keys(simple_profile):
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "MYSTERY_VAR": "z"}
    result = check_profile(env, simple_profile)
    assert "MYSTERY_VAR" in result.unknown_keys


def test_check_profile_no_unknown_when_all_known(simple_profile):
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "DEBUG": "true"}
    result = check_profile(env, simple_profile)
    assert result.unknown_keys == []


def test_summary_includes_ok_when_passed(simple_profile):
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y"}
    result = check_profile(env, simple_profile)
    assert "OK" in result.summary()


def test_summary_includes_missing_key_name(simple_profile):
    env = {"DATABASE_URL": "x"}
    result = check_profile(env, simple_profile)
    assert "SECRET_KEY" in result.summary()
    assert "MISSING" in result.summary()


def test_profile_round_trip_via_dict(simple_profile):
    d = simple_profile.to_dict()
    restored = EnvProfile.from_dict(d)
    assert restored.name == simple_profile.name
    assert restored.required_keys == simple_profile.required_keys
    assert restored.description == simple_profile.description


def test_save_and_load_profile(tmp_path, simple_profile):
    path = str(tmp_path / "profile.json")
    save_profile(simple_profile, path)
    loaded = load_profile(path)
    assert loaded.name == simple_profile.name
    assert loaded.required_keys == simple_profile.required_keys
    assert loaded.optional_keys == simple_profile.optional_keys


def test_load_profile_file_content(tmp_path, simple_profile):
    path = str(tmp_path / "profile.json")
    save_profile(simple_profile, path)
    with open(path) as fh:
        data = json.load(fh)
    assert data["name"] == "web"
    assert "DATABASE_URL" in data["required_keys"]
