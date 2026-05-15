"""Tests for envdiff.scorer."""

import pytest
from envdiff.scorer import score_env, EnvScore


CLEAN_ENV = """APP_NAME=myapp
DATABASE_URL=postgres://localhost/db
DEBUG=false
"""

LINT_ERROR_ENV = """APP_NAME=myapp
BAD LINE
DEBUG=false
"""

PLACEHOLDER_SECRET_ENV = """APP_NAME=myapp
SECRET_KEY=changeme
"""

EMPTY_VALUE_ENV = """APP_NAME=myapp
DATABASE_URL=
"""


def test_clean_env_scores_high():
    result = score_env(CLEAN_ENV)
    assert isinstance(result, EnvScore)
    assert result.total >= 90


def test_grade_a_for_high_score():
    result = score_env(CLEAN_ENV)
    assert result.grade == "A"


def test_lint_errors_reduce_score():
    clean = score_env(CLEAN_ENV)
    bad = score_env(LINT_ERROR_ENV)
    assert bad.total < clean.total


def test_placeholder_secret_reduces_score():
    result = score_env(PLACEHOLDER_SECRET_ENV)
    categories = [d.category for d in result.details]
    assert "security" in categories


def test_placeholder_secret_deduction_is_significant():
    result = score_env(PLACEHOLDER_SECRET_ENV)
    security_deductions = sum(d.deduction for d in result.details if d.category == "security")
    assert security_deductions >= 10


def test_missing_required_key_reduces_score():
    result = score_env(CLEAN_ENV, required_keys=["MISSING_KEY"])
    categories = [d.category for d in result.details]
    assert "validation" in categories


def test_score_never_negative():
    very_bad = "\n".join(["BAD LINE"] * 20)
    result = score_env(very_bad)
    assert result.total >= 0


def test_score_str_includes_grade():
    result = score_env(CLEAN_ENV)
    text = str(result)
    assert "Grade" in text
    assert str(result.total) in text


def test_details_listed_in_str():
    result = score_env(PLACEHOLDER_SECRET_ENV)
    text = str(result)
    assert "security" in text.lower()


def test_grade_f_for_very_low_score():
    score = EnvScore(total=20)
    assert score.grade == "F"


def test_grade_b_for_mid_score():
    score = EnvScore(total=80)
    assert score.grade == "B"
