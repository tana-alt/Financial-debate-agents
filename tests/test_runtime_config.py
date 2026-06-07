from pathlib import Path

import pytest

import src.runtime_config as runtime_config
from src.runtime_config import env_bool, env_float, env_int, env_path, env_str


def test_env_helpers_return_defaults_for_unset_or_empty(monkeypatch):
    monkeypatch.delenv("TEST_RUNTIME_CONFIG_VALUE", raising=False)
    assert env_str("TEST_RUNTIME_CONFIG_VALUE", "default") == "default"
    assert env_int("TEST_RUNTIME_CONFIG_VALUE", 12) == 12
    assert env_float("TEST_RUNTIME_CONFIG_VALUE", 1.5) == 1.5
    assert env_bool("TEST_RUNTIME_CONFIG_VALUE", True) is True
    assert env_path("TEST_RUNTIME_CONFIG_VALUE", "outputs") == Path("outputs")

    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "")
    assert env_str("TEST_RUNTIME_CONFIG_VALUE", "default") == "default"
    assert env_int("TEST_RUNTIME_CONFIG_VALUE", 12) == 12
    assert env_float("TEST_RUNTIME_CONFIG_VALUE", 1.5) == 1.5
    assert env_bool("TEST_RUNTIME_CONFIG_VALUE", False) is False
    assert env_path("TEST_RUNTIME_CONFIG_VALUE", "outputs") == Path("outputs")


def test_env_helpers_parse_valid_values(monkeypatch):
    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "42")
    assert env_int("TEST_RUNTIME_CONFIG_VALUE", 12) == 42

    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "0.25")
    assert env_float("TEST_RUNTIME_CONFIG_VALUE", 1.5) == 0.25

    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "yes")
    assert env_bool("TEST_RUNTIME_CONFIG_VALUE", False) is True

    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "tmp/cache")
    assert env_path("TEST_RUNTIME_CONFIG_VALUE", "outputs") == Path("tmp/cache")


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "not-a-number"])
def test_env_float_rejects_invalid_values(monkeypatch, value):
    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", value)

    with pytest.raises(ValueError):
        env_float("TEST_RUNTIME_CONFIG_VALUE", 1.5)


def test_env_int_rejects_invalid_or_out_of_range_values(monkeypatch):
    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "not-an-int")
    with pytest.raises(ValueError):
        env_int("TEST_RUNTIME_CONFIG_VALUE", 12)

    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "0")
    with pytest.raises(ValueError):
        env_int("TEST_RUNTIME_CONFIG_VALUE", 12, min_value=1)


def test_env_bool_and_path_reject_invalid_values(monkeypatch):
    monkeypatch.setenv("TEST_RUNTIME_CONFIG_VALUE", "maybe")
    with pytest.raises(ValueError):
        env_bool("TEST_RUNTIME_CONFIG_VALUE", False)

    monkeypatch.setattr(runtime_config.os, "getenv", lambda name: "bad\x00path")
    with pytest.raises(ValueError):
        env_path("TEST_RUNTIME_CONFIG_VALUE", "outputs")
