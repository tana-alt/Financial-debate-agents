from __future__ import annotations

import pytest

from src.llm import LLMProviderError, OpenAIProvider
from src.workflow_errors import WorkflowErrorCategory


class _FakeUsage:
    prompt_tokens = 3
    completion_tokens = 5


class _FakeMessage:
    content = "{}"


class _FakeChoice:
    message = _FakeMessage()


class _FakeCompletions:
    def __init__(self, error: Exception | None = None) -> None:
        self.params = None
        self.error = error

    def create(self, **params):
        self.params = params
        if self.error is not None:
            raise self.error
        return type(
            "FakeResponse",
            (),
            {"choices": [_FakeChoice()], "usage": _FakeUsage()},
        )()


class _FakeChat:
    def __init__(self, error: Exception | None = None) -> None:
        self.completions = _FakeCompletions(error)


class _FakeClient:
    def __init__(self, error: Exception | None = None) -> None:
        self.chat = _FakeChat(error)


class _FakeSDKError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _provider(
    model: str,
    error: Exception | None = None,
) -> tuple[OpenAIProvider, _FakeClient]:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    client = _FakeClient(error)
    provider.client = client  # type: ignore[assignment]
    provider.model = model
    return provider, client


def test_openai_provider_uses_minimum_max_completion_tokens_for_gpt5_models():
    provider, client = _provider("gpt-5.4-mini")

    provider.complete("system", "user", max_tokens=123, temperature=0.2)

    params = client.chat.completions.params
    assert params["max_completion_tokens"] == 4096
    assert "max_tokens" not in params
    assert "temperature" not in params


def test_openai_provider_keeps_max_tokens_for_legacy_chat_models():
    provider, client = _provider("gpt-4o")

    provider.complete("system", "user", max_tokens=123, temperature=0.2)

    params = client.chat.completions.params
    assert params["max_tokens"] == 123
    assert params["temperature"] == 0.2
    assert "max_completion_tokens" not in params


def test_openai_provider_uses_env_defaults_when_call_tokens_are_omitted(monkeypatch):
    monkeypatch.setenv("EARNINGS_DEBATE_LLM_DEFAULT_MAX_TOKENS", "777")
    monkeypatch.setenv("EARNINGS_DEBATE_LLM_DEFAULT_TEMPERATURE", "0.33")
    provider, client = _provider("gpt-4o")

    provider.complete("system", "user")

    params = client.chat.completions.params
    assert params["max_tokens"] == 777
    assert params["temperature"] == 0.33


def test_openai_provider_uses_env_minimum_completion_tokens(monkeypatch):
    monkeypatch.setenv("EARNINGS_DEBATE_OPENAI_MIN_COMPLETION_TOKENS", "2048")
    provider, client = _provider("gpt-5.4-mini")

    provider.complete("system", "user", max_tokens=123, temperature=0.2)

    params = client.chat.completions.params
    assert params["max_completion_tokens"] == 2048


def test_openai_provider_maps_auth_failure_to_provider_config():
    provider, _client = _provider(
        "gpt-4o",
        _FakeSDKError("Incorrect API key provided", status_code=401),
    )

    with pytest.raises(LLMProviderError) as excinfo:
        provider.complete("system", "user")

    assert excinfo.value.category is WorkflowErrorCategory.PROVIDER_CONFIG
    assert excinfo.value.provider == "openai"
    assert excinfo.value.retryable is False


def test_openai_provider_maps_rate_limit_to_provider_transient():
    provider, _client = _provider(
        "gpt-4o",
        _FakeSDKError("Rate limit reached", status_code=429),
    )

    with pytest.raises(LLMProviderError) as excinfo:
        provider.complete("system", "user")

    assert excinfo.value.category is WorkflowErrorCategory.PROVIDER_TRANSIENT
    assert excinfo.value.provider == "openai"
    assert excinfo.value.retryable is True


def test_openai_structured_completion_passes_json_schema_response_format():
    provider, client = _provider("gpt-4o")

    provider.complete_structured(
        "system",
        "user",
        output_schema={"type": "object", "properties": {"answer": {"type": "string"}}},
        schema_name="Answer",
        max_tokens=123,
        temperature=0.2,
    )

    params = client.chat.completions.params
    assert params["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "Answer",
            "schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
            "strict": True,
        },
    }
