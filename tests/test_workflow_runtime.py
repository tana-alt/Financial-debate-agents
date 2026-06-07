from src.workflow_runtime import (
    AgentRuntime,
    _agent_max_workers,
    _debate_selection_attempts,
    _judge_selection_attempts,
)


class _Future:
    def __init__(self, value):
        self.value = value

    def result(self):
        return self.value


class _Executor:
    max_workers_seen = None

    def __init__(self, max_workers):
        type(self).max_workers_seen = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def submit(self, fn, *args):
        return _Future(fn(*args))


class _Agent:
    spec = type("Spec", (), {"public_role": "EarningsQualityAnalyst"})()

    def __init__(self, llm, *, trace_sink=None):
        self.llm = llm
        self.trace_sink = trace_sink

    def run(self, context):
        return context["value"]


def test_agent_runtime_uses_env_max_workers(monkeypatch):
    monkeypatch.setenv("EARNINGS_DEBATE_AGENT_MAX_WORKERS", "1")
    monkeypatch.setattr("src.workflow_runtime.ThreadPoolExecutor", _Executor)

    result = AgentRuntime(llm=object()).run_parallel(
        (_Agent, _Agent),
        {"expected_metrics": {}, "value": "ok"},
    )

    assert result == ["ok", "ok"]
    assert _Executor.max_workers_seen == 1


def test_workflow_runtime_env_attempt_helpers(monkeypatch):
    monkeypatch.setenv("EARNINGS_DEBATE_AGENT_MAX_WORKERS", "3")
    monkeypatch.setenv("EARNINGS_DEBATE_DEBATE_SELECTION_ATTEMPTS", "4")
    monkeypatch.setenv("EARNINGS_DEBATE_JUDGE_SELECTION_ATTEMPTS", "5")

    assert _agent_max_workers(7) == 3
    assert _debate_selection_attempts() == 4
    assert _judge_selection_attempts() == 5
