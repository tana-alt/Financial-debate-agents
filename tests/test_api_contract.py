from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from src import api
from src.workflow_agents import AgentOutputValidationError
from src.workflow_models import ReviewRequest
from src.workflow_validation import WorkflowValidationError


def normalized_review_payload(*, dry_run: bool = True) -> dict[str, object]:
    return {
        "schema_version": "review_input.v1",
        "request_id": "req-api-contract-1",
        "ticker": "nvda",
        "fiscal_period": "2025Q3",
        "financial_metrics": {
            "ticker": "NVDA",
            "fiscal_period": "2025Q3",
            "eps": 0.81,
            "eps_consensus": 0.75,
            "eps_surprise_pct": 8.0,
            "revenue": 35_000_000_000,
            "revenue_consensus": 33_000_000_000,
            "revenue_surprise_pct": 6.1,
            "operating_cash_flow": 13_100_000_000,
            "capex": 1_100_000_000,
            "free_cash_flow": 12_000_000_000,
            "guidance": "Management guidance implies continued revenue growth.",
            "source_refs": [
                {
                    "source_id": "api:eps",
                    "source_type": "financial_api",
                    "metric_name": "eps",
                    "reported_period": "2025Q3",
                },
                {
                    "source_id": "api:free_cash_flow",
                    "source_type": "financial_api",
                    "metric_name": "free_cash_flow",
                    "reported_period": "2025Q3",
                },
            ],
        },
        "document_sections": [
            {
                "section_id": "eps",
                "source_ref": _source_ref("eps"),
                "heading": "EPS",
                "text": "Diluted EPS exceeded consensus and margin quality improved.",
            },
            {
                "section_id": "guidance",
                "source_ref": _source_ref("guidance"),
                "heading": "Guidance",
                "text": "Management guidance implies continued revenue growth with elevated investment.",
            },
            {
                "section_id": "risk",
                "source_ref": _source_ref("risk"),
                "heading": "Risk",
                "text": "Forward-looking statements note demand uncertainty and CapEx execution risk.",
            },
        ],
        "source_manifest": [
            {
                "source_id": "api:eps",
                "source_type": "financial_api",
                "title": "EPS API metric",
                "metric_name": "eps",
                "reported_period": "2025Q3",
            },
            {
                "source_id": "api:free_cash_flow",
                "source_type": "financial_api",
                "title": "Free cash flow API metric",
                "metric_name": "free_cash_flow",
                "reported_period": "2025Q3",
            },
            _manifest_entry("eps"),
            _manifest_entry("guidance"),
            _manifest_entry("risk"),
        ],
        "context_budget": {
            "max_input_tokens": 50_000,
            "max_output_tokens": 2_000,
            "max_total_tokens": 60_000,
        },
        "include_markdown": True,
        "purpose": "earnings_review_not_investment_advice",
        "is_investment_advice": False,
        "dry_run": dry_run,
    }


def _source_ref(section_id: str) -> dict[str, object]:
    return {
        "source_id": f"filing:{section_id}",
        "source_type": "filing",
        "document_id": "10q-2025q3",
        "section_id": section_id,
        "reported_period": "2025Q3",
    }


def _manifest_entry(section_id: str) -> dict[str, object]:
    return {
        "source_id": f"filing:{section_id}",
        "source_type": "filing",
        "title": f"{section_id} filing section",
        "document_id": "10q-2025q3",
        "section_id": section_id,
        "reported_period": "2025Q3",
    }


@pytest.mark.parametrize(
    ("raw_field", "raw_value"),
    [
        ("document_files", []),
        ("filing_url", "https://www.sec.gov/Archives/example/nvda.htm"),
        ("local_path", "samples/local-filing.txt"),
        ("presentation_url", "https://example.com/presentation.pdf"),
        ("raw_text", "raw filing text"),
        ("transcript_url", "https://example.com/transcript.txt"),
    ],
)
def test_reviews_rejects_raw_acquisition_fields_with_error_envelope(raw_field, raw_value):
    payload = normalized_review_payload()
    payload[raw_field] = raw_value

    response = TestClient(api.app).post("/reviews", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["request_id"] == "req-api-contract-1"
    assert body["ticker"] == "NVDA"
    assert body["fiscal_period"] == "2025Q3"
    assert body["errors"][0]["category"] == "input_contract"
    assert body["errors"][0]["retryable"] is False
    assert raw_field in body["errors"][0]["message"]
    assert "Traceback" not in body["errors"][0]["message"]


def test_reviews_dry_run_validates_routing_without_workflow_or_external_fetch(monkeypatch):
    def fail_fetch(*args, **kwargs):
        raise AssertionError("dry_run should not fetch external inputs")

    def fail_workflow():
        raise AssertionError("dry_run should not resolve the workflow provider")

    monkeypatch.setattr("src.workflow._fetch_consensus", fail_fetch)
    monkeypatch.setattr("src.workflow._fetch_filing_html", fail_fetch)
    api.app.dependency_overrides[api.get_workflow] = fail_workflow
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=normalized_review_payload(dry_run=True),
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dry_run"
    assert body["dry_run_status"] == "passed"
    assert body["request_id"] == "req-api-contract-1"
    assert body["ticker"] == "NVDA"
    assert body["fiscal_period"] == "2025Q3"
    assert {check["name"] for check in body["checks"]} == {
        "normalized_input_contract",
        "source_manifest",
        "context_budget",
    }
    assert all(check["status"] == "passed" for check in body["checks"])
    assert body["errors"] == []
    assert "markdown_report" not in body


def test_reviews_manifest_validation_uses_422_source_manifest_envelope():
    payload = normalized_review_payload()
    payload["document_sections"][0]["source_ref"]["source_id"] = "filing:missing"

    response = TestClient(api.app).post("/reviews", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "source_manifest"
    assert body["errors"][0]["retryable"] is False
    assert "unregistered source_id" in body["errors"][0]["message"]


def test_reviews_dry_run_budget_failure_uses_422_dry_run_response():
    payload = normalized_review_payload(dry_run=True)
    payload["context_budget"] = {
        "max_input_tokens": 1,
        "max_output_tokens": 1,
        "max_total_tokens": 2,
    }

    response = TestClient(api.app).post("/reviews", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "dry_run"
    assert body["dry_run_status"] == "failed"
    assert body["errors"][0]["category"] == "context_budget"
    assert body["errors"][0]["retryable"] is False
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["context_budget"]["status"] == "failed"
    assert checks["context_budget"]["category"] == "context_budget"
    assert "Traceback" not in body["errors"][0]["message"]


def test_reviews_dry_run_rejects_missing_document_sections_before_workflow():
    def fail_workflow():
        raise AssertionError("dry_run preflight should not resolve the workflow provider")

    payload = normalized_review_payload(dry_run=True)
    payload["document_sections"] = []

    api.app.dependency_overrides[api.get_workflow] = fail_workflow
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=payload,
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "dry_run"
    assert body["dry_run_status"] == "failed"
    assert body["errors"][0]["category"] == "input_contract"
    assert body["errors"][0]["retryable"] is False
    assert "document_sections" in body["errors"][0]["message"]
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["runtime_required_input"]["status"] == "failed"
    assert checks["runtime_required_input"]["category"] == "input_contract"


def test_reviews_non_dry_run_rejects_missing_document_sections_before_workflow():
    def fail_workflow():
        raise AssertionError("non-dry-run preflight should not resolve the workflow provider")

    payload = normalized_review_payload(dry_run=False)
    payload["document_sections"] = []

    api.app.dependency_overrides[api.get_workflow] = fail_workflow
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=payload,
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "input_contract"
    assert body["errors"][0]["retryable"] is False
    assert "document_sections" in body["errors"][0]["message"]
    assert "Traceback" not in body["errors"][0]["message"]


def test_reviews_non_dry_run_budget_failure_happens_before_workflow():
    def fail_workflow():
        raise AssertionError("context budget failure should not resolve the workflow provider")

    payload = normalized_review_payload(dry_run=False)
    payload["context_budget"] = {
        "max_input_tokens": 1,
        "max_output_tokens": 1,
        "max_total_tokens": 2,
    }

    api.app.dependency_overrides[api.get_workflow] = fail_workflow
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=payload,
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "context_budget"
    assert body["errors"][0]["field"] == "context_budget"
    assert body["errors"][0]["retryable"] is False
    assert "context budget exceeded" in body["errors"][0]["message"]


def test_reviews_workflow_validation_failure_uses_422_quality_gate_envelope():
    class FailingWorkflow:
        def run(self, request: ReviewRequest):
            raise WorkflowValidationError("positive evidence pool is empty after aggregation")

    api.app.dependency_overrides[api.get_workflow] = lambda: FailingWorkflow()
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=normalized_review_payload(dry_run=False),
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "quality_gate"
    assert body["errors"][0]["retryable"] is False
    assert "positive evidence pool is empty" in body["errors"][0]["message"]
    assert "Traceback" not in body["errors"][0]["message"]


def test_reviews_agent_schema_failure_uses_structured_output_category():
    class FailingWorkflow:
        def run(self, request: ReviewRequest):
            raise AgentOutputValidationError(
                "JudgeAgent output failed schema_mismatch",
                field="judge_decision.verdict",
                retryable=False,
            )

    api.app.dependency_overrides[api.get_workflow] = lambda: FailingWorkflow()
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=normalized_review_payload(dry_run=False),
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "llm_output_schema"
    assert body["errors"][0]["field"] == "judge_decision.verdict"
    assert body["errors"][0]["retryable"] is False
    assert "Internal review workflow failure" not in body["errors"][0]["message"]


def test_reviews_openapi_documents_stable_error_envelopes():
    response = TestClient(api.app).get("/openapi.json")

    assert response.status_code == 200
    responses = response.json()["paths"]["/reviews"]["post"]["responses"]
    success_schema = json.dumps(responses["200"])
    assert "ReviewSuccessResponse" in success_schema
    assert "422" in responses
    assert "500" in responses
    assert "ReviewErrorResponse" in json.dumps(responses["422"])
    assert "ReviewDryRunResponse" in json.dumps(responses["422"])
    assert "ReviewErrorResponse" in json.dumps(responses["500"])


def test_reviews_runtime_failure_uses_500_error_envelope_without_traceback():
    captured: dict[str, ReviewRequest] = {}

    class FailingWorkflow:
        def run(self, request: ReviewRequest):
            captured["request"] = request
            raise RuntimeError("provider stack trace marker should stay internal")

    api.app.dependency_overrides[api.get_workflow] = lambda: FailingWorkflow()
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json=normalized_review_payload(dry_run=False),
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "failed"
    assert body["errors"][0]["category"] == "internal_invariant"
    assert body["errors"][0]["retryable"] is False
    assert "Traceback" not in body["errors"][0]["message"]
    assert "provider stack trace marker" not in body["errors"][0]["message"]
    assert captured["request"].filing_url is None
    assert captured["request"].document_files == []
