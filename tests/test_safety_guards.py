from __future__ import annotations

import pytest

from src.workflow import MarkdownRenderer, ReviewWorkflow, WorkflowValidationError
from src.workflow_models import ReviewRequest
from src.workflow_validation import WorkflowValidationGate
from tests.test_workflow_api import FakeLLM, InvestmentAdviceJudgeLLM, _request_payload


class InvestmentAdviceSpecialistLLM(FakeLLM):
    def _finding_json(self, role: str) -> str:
        return (
            super()
            ._finding_json(role)
            .replace(
                f"{role} summary",
                "Investors should buy the stock.",
                1,
            )
        )


class InvestmentAdviceMarkdownRenderer(MarkdownRenderer):
    def render(self, **kwargs) -> str:
        return "You should buy the stock.\n"


def test_specialist_output_containing_buy_the_stock_warns_and_redacts(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    workflow = ReviewWorkflow(llm=InvestmentAdviceSpecialistLLM())

    response = workflow.run(ReviewRequest.model_validate(_request_payload()))

    assert "buy the stock" not in response.markdown_report.lower()
    assert any(
        item.key.startswith("llm_investment_advice:")
        for item in response.analysis_brief.quality_warnings
    )


def test_judge_output_containing_target_price_language_warns_and_redacts(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    class TargetPriceJudgeLLM(InvestmentAdviceJudgeLLM):
        def _judge_json(self) -> str:
            return super()._judge_json().replace("buy the stock", "raise the price target")

    workflow = ReviewWorkflow(llm=TargetPriceJudgeLLM())

    response = workflow.run(ReviewRequest.model_validate(_request_payload()))

    assert "price target" not in response.markdown_report.lower()
    assert any(
        item.key.startswith("llm_investment_advice:judge_decision")
        for item in response.analysis_brief.quality_warnings
    )


def test_final_markdown_containing_investment_advice_warns_and_redacts(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    workflow = ReviewWorkflow(
        llm=FakeLLM(),
        renderer=InvestmentAdviceMarkdownRenderer(),
    )

    response = workflow.run(ReviewRequest.model_validate(_request_payload()))

    assert "buy the stock" not in response.markdown_report.lower()
    assert any(
        item.key == "llm_investment_advice:markdown_report"
        for item in response.analysis_brief.quality_warnings
    )


def test_investment_advice_redaction_does_not_change_source_metadata():
    validator = WorkflowValidationGate()
    payload = {
        "summary": "EPS improved by 8%.",
        "source_ref": {
            "source_id": "filing:price-target",
            "source_type": "filing",
            "document_id": "10q-2025q3",
            "section_id": "price-target",
            "title": "Price target appendix",
            "reported_period": "2025Q3",
        },
    }

    assert validator.investment_advice_warnings(payload, "finding") == []
    assert validator.sanitize_investment_advice_text(payload) == payload


def test_long_position_language_fails_direct_safety_gate():
    validator = WorkflowValidationGate()

    with pytest.raises(WorkflowValidationError, match="investment-advice language"):
        validator.validate_no_investment_advice_text(
            {"rationale": "Investors should initiate a long position in NVDA."},
            "judge_decision",
        )


@pytest.mark.parametrize(
    "phrase",
    [
        "Investors should establish a long position in NVDA.",
        "Investors should build a short position in NVDA.",
    ],
)
def test_position_building_language_fails_direct_safety_gate(phrase):
    validator = WorkflowValidationGate()

    with pytest.raises(WorkflowValidationError, match="investment-advice language"):
        validator.validate_no_investment_advice_text({"rationale": phrase}, "judge_decision")


def test_long_term_operating_language_does_not_fail_safety_gate():
    validator = WorkflowValidationGate()

    validator.validate_no_investment_advice_text(
        {"rationale": "Long term debt pressure may constrain cash conversion."},
        "judge_decision",
    )


def test_non_advice_disclaimer_continues_to_render(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    response = ReviewWorkflow(llm=FakeLLM()).run(ReviewRequest.model_validate(_request_payload()))

    assert "投資助言ではありません" in response.markdown_report
    assert "[removed investment-advice language]" not in response.markdown_report
    assert response.is_investment_advice is False
