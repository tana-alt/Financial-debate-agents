from __future__ import annotations

from fastapi.testclient import TestClient

from src import api
from src.llm import FakeProvider
from src.workflow import ReviewWorkflow
from tests.test_workflow_api import _request_payload


def test_reviews_api_fake_smoke_returns_markdown_report(monkeypatch):
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    provider = FakeProvider()

    def override_workflow() -> ReviewWorkflow:
        return ReviewWorkflow(provider)

    api.app.dependency_overrides[api.get_workflow] = override_workflow
    try:
        response = TestClient(api.app).post("/reviews", json=_request_payload())
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["markdown_report"]
    for section in (
        "## Verdict",
        "## Positive Evidence",
        "## Negative Evidence",
        "## EPS Outlook",
        "## FCF Outlook",
    ):
        assert section in body["markdown_report"]
