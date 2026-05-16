"""Tests for envdiff.classifier."""

import pytest
from envdiff.classifier import (
    classify_key,
    classify_env,
    ClassifyResult,
)


def test_database_url_classified_as_database():
    assert classify_key("DATABASE_URL") == "database"


def test_db_prefix_classified_as_database():
    assert classify_key("DB_HOST") == "database"


def test_redis_key_classified_as_cache():
    assert classify_key("REDIS_URL") == "cache"


def test_secret_key_classified_as_security():
    assert classify_key("SECRET_KEY") == "security"


def test_password_classified_as_security():
    assert classify_key("DB_PASSWORD") == "security"


def test_aws_key_classified_as_cloud():
    assert classify_key("AWS_ACCESS_KEY_ID") == "cloud"


def test_log_level_classified_as_logging():
    assert classify_key("LOG_LEVEL") == "logging"


def test_port_classified_as_network():
    assert classify_key("PORT") == "network"


def test_debug_classified_as_app():
    assert classify_key("DEBUG") == "app"


def test_unknown_key_is_uncategorized():
    assert classify_key("FOOBAR_XYZ") == "uncategorized"


def test_case_insensitive_matching():
    assert classify_key("redis_url") == "cache"
    assert classify_key("aws_region") == "cloud"


def test_classify_env_groups_all_keys():
    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "abc123",
        "PORT": "8000",
        "FOOBAR": "baz",
    }
    result = classify_env(env)
    assert "DATABASE_URL" in result.categories["database"]
    assert "SECRET_KEY" in result.categories["security"]
    assert "PORT" in result.categories["network"]
    assert "FOOBAR" in result.categories["uncategorized"]


def test_classify_result_to_dict():
    result = ClassifyResult()
    result.add("REDIS_URL")
    result.add("LOG_LEVEL")
    d = result.to_dict()
    assert "cache" in d
    assert "logging" in d


def test_classify_result_category_for():
    result = ClassifyResult()
    result.add("AWS_SECRET_ACCESS_KEY")
    # AWS_ matches cloud first in pattern order
    assert result.category_for("AWS_SECRET_ACCESS_KEY") == "cloud"


def test_classify_result_str_output():
    result = ClassifyResult()
    result.add("PORT")
    result.add("HOST")
    output = str(result)
    assert "[network]" in output
    assert "PORT" in output
    assert "HOST" in output


def test_classify_empty_env():
    result = classify_env({})
    assert result.categories == {}


def test_add_with_explicit_category():
    result = ClassifyResult()
    result.add("MY_CUSTOM_KEY", category="custom")
    assert "MY_CUSTOM_KEY" in result.categories["custom"]
