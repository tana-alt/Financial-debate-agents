from __future__ import annotations

from src.llm import FakeProvider, get_provider
from src.workflow import ReviewWorkflow
from src.workflow_models import ReviewRequest
from tests.test_workflow_api import _request_payload


def test_fake_provider_factory(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    assert isinstance(get_provider(), FakeProvider)


def test_fake_provider_runs_seven_agent_workflow_without_keys(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    provider = FakeProvider()
    response = ReviewWorkflow(provider).run(ReviewRequest.model_validate(_request_payload()))

    assert len(provider.calls) == 7
    assert provider.calls.count("EarningsQualityAnalyst") == 1
    assert provider.calls.count("CashFlowRiskAnalyst") == 1
    assert provider.calls.count("ManagementIntentAnalyst") == 1
    assert provider.calls.count("GuidanceAnalyst") == 1
    assert provider.calls.count("BullAgent") == 1
    assert provider.calls.count("BearAgent") == 1
    assert provider.calls.count("JudgeAgent") == 1
    assert response.markdown_report
    for section in (
        "## レポート前提: canonical data",
        "## 要約",
        "## 判定理由",
        "## EPS/FCF見通し",
        "## Bull/Bear論点",
        "## Agent分析",
        "## 根拠マトリクス (Evidence Matrix)",
        "## 不確実性と不足データ",
        "## 品質ゲート (Quality Gates)",
        "## ソース付録 (Source Appendix)",
        "## 免責事項",
    ):
        assert section in response.markdown_report
    assert "| Claim ID | Fact | Interpretation | Implication | Time scope |" in (
        response.markdown_report
    )
    assert "Precomputed EPS and margin evidence support future EPS." in response.markdown_report
    assert "CapEx and working capital can delay FCF improvement." in response.markdown_report
