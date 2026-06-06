from __future__ import annotations

from fastapi.testclient import TestClient

from src import api
from src.llm import FakeProvider
from src.workflow import ReviewWorkflow
from tests.test_api_contract import normalized_review_payload


def test_reviews_api_fake_smoke_returns_markdown_report(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    provider = FakeProvider()

    def override_workflow() -> ReviewWorkflow:
        return ReviewWorkflow(provider)

    api.app.dependency_overrides[api.get_workflow] = override_workflow
    try:
        response = TestClient(api.app).post(
            "/reviews",
            json=normalized_review_payload(dry_run=False),
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["request_id"] == "req-api-contract-1"
    assert body["quality_gate_result"]["status"] == "passed"
    assert body["quality_gate_result"]["source_manifest_entries"] == 18
    assert {source["source_id"] for source in body["claim_matrix"]["source_manifest"]} == {
        "financial_api:NVDA:2025Q3:yfinance:eps",
        "financial_api:NVDA:2025Q3:sec:revenue",
        "financial_api:NVDA:2025Q3:sec:operating_cash_flow",
        "financial_api:NVDA:2025Q3:sec:capex",
        "metric:NVDA:2025Q3:free_cash_flow:derived",
        "financial_api:NVDA:2025Q3:yfinance:previous_quarter:eps",
        "financial_api:NVDA:2025Q3:sec:previous_quarter:revenue",
        "financial_api:NVDA:2025Q3:sec:previous_quarter:operating_cash_flow",
        "financial_api:NVDA:2025Q3:sec:previous_quarter:capex",
        "metric:NVDA:2025Q3:previous_quarter:free_cash_flow:derived",
        "financial_api:NVDA:2025Q3:yfinance:year_ago_quarter:eps",
        "financial_api:NVDA:2025Q3:sec:year_ago_quarter:revenue",
        "financial_api:NVDA:2025Q3:sec:year_ago_quarter:operating_cash_flow",
        "financial_api:NVDA:2025Q3:sec:year_ago_quarter:capex",
        "metric:NVDA:2025Q3:year_ago_quarter:free_cash_flow:derived",
        "filing:eps",
        "filing:guidance",
        "filing:risk",
    }
    assert body["markdown_report"]
    assert "financial_api:NVDA:2025Q3:yfinance:eps" in body["markdown_report"]
    assert "metric:NVDA:2025Q3:free_cash_flow:derived" in body["markdown_report"]
    for section in (
        "## レポート前提: canonical data",
        "## 判定理由",
        "## 根拠マトリクス (Evidence Matrix)",
        "## 品質ゲート (Quality Gates)",
        "## 免責事項",
    ):
        assert section in body["markdown_report"]


def test_reviews_api_rejects_raw_document_files_with_error_envelope(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)

    def override_workflow() -> ReviewWorkflow:
        return ReviewWorkflow(FakeProvider())

    payload = normalized_review_payload(dry_run=False)
    payload["document_files"] = [
        {
            "path": "tests/fixtures/missing_presentation.txt",
            "source_type": "earnings_presentation",
            "document_id": "sample-presentation",
            "title": "Sample earnings presentation",
        }
    ]

    api.app.dependency_overrides[api.get_workflow] = override_workflow
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
    assert "document_files" in body["errors"][0]["message"]
