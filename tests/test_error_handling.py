from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient

from src import api
from src.errors import (
    APIConnectionError,
    APIHTTPStatusError,
    APIRateLimitError,
    APITimeoutError,
    SECParsingError,
)
from src.preprocessor import (
    DocumentFileValidationError,
    document_files_to_sections,
    fetch_consensus,
    fetch_filing_html,
    segment_filing,
)
from src.report_quality_numeric_grounding import NumericGroundingError
from src.workflow import WorkflowValidationError
from src.workflow_agents import EarningsQualityAnalyst, WorkflowAgentError
from src.workflow_models import DocumentFile


class _FailingWorkflow:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def run(self, request):
        raise self.exc


def test_fetch_filing_html_raises_timeout_error(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise requests.Timeout("read timed out")

    monkeypatch.setattr("src.preprocessor.requests.get", raise_timeout)

    with pytest.raises(APITimeoutError) as exc_info:
        fetch_filing_html("https://www.sec.gov/Archives/timeout-test.htm")

    assert exc_info.value.to_api_detail()["code"] == "api_timeout"
    assert exc_info.value.to_api_detail()["source"] == "sec"


def test_fetch_filing_html_raises_rate_limit_error(monkeypatch):
    class Response:
        status_code = 429
        text = "rate limited"

        def raise_for_status(self):
            raise AssertionError("429 should be handled before raise_for_status")

    monkeypatch.setattr("src.preprocessor.requests.get", lambda *args, **kwargs: Response())

    with pytest.raises(APIRateLimitError) as exc_info:
        fetch_filing_html("https://www.sec.gov/Archives/rate-limit-test.htm")

    detail = exc_info.value.to_api_detail()
    assert detail["code"] == "api_rate_limit"
    assert detail["upstream_status_code"] == 429


def test_fetch_filing_html_raises_connection_error(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("connection failed")

    monkeypatch.setattr("src.preprocessor.requests.get", raise_connection_error)

    with pytest.raises(APIConnectionError) as exc_info:
        fetch_filing_html("https://www.sec.gov/Archives/connection-error-test.htm")

    assert exc_info.value.to_api_detail()["code"] == "api_connection_error"
    assert exc_info.value.to_api_detail()["source"] == "sec"


def test_fetch_filing_html_maps_http_5xx_status(monkeypatch):
    class Response:
        status_code = 503
        text = "service unavailable"

        def raise_for_status(self):
            raise requests.HTTPError("503 Service Unavailable")

    monkeypatch.setattr("src.preprocessor.requests.get", lambda *args, **kwargs: Response())

    with pytest.raises(APIHTTPStatusError) as exc_info:
        fetch_filing_html("https://www.sec.gov/Archives/http-503-test.htm")

    detail = exc_info.value.to_api_detail()
    assert detail["code"] == "api_http_status_error"
    assert detail["upstream_status_code"] == 503
    assert detail["retryable"] is True


def test_segment_filing_raises_when_no_sections_can_be_extracted():
    with pytest.raises(SECParsingError, match="no extractable document sections"):
        segment_filing("<html><body><p>too short</p></body></html>")


def test_fetch_consensus_maps_yfinance_timeout(monkeypatch):
    class TimeoutTicker:
        @property
        def earnings_dates(self):
            raise requests.Timeout("read timed out")

    monkeypatch.setattr("src.preprocessor.yf.Ticker", lambda ticker: TimeoutTicker())

    with pytest.raises(APITimeoutError) as exc_info:
        fetch_consensus("NVDA", "2025Q3")

    assert exc_info.value.to_api_detail()["source"] == "yfinance"


def test_fetch_consensus_keeps_partial_data_for_yfinance_schema_errors(monkeypatch):
    class SchemaChangedTicker:
        @property
        def earnings_dates(self):
            raise KeyError("Reported EPS")

        @property
        def quarterly_financials(self):
            return None

    monkeypatch.setattr("src.preprocessor.yf.Ticker", lambda ticker: SchemaChangedTicker())

    metrics = fetch_consensus("NVDA", "2025Q3")

    assert metrics.ticker == "NVDA"
    assert metrics.eps is None
    assert metrics.revenue is None


def test_text_document_os_error_is_document_validation_error(monkeypatch, tmp_path):
    path = tmp_path / "presentation.txt"
    path.write_text("placeholder", encoding="utf-8")

    def raise_os_error(self: Path, encoding: str = "utf-8"):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", raise_os_error)

    with pytest.raises(DocumentFileValidationError, match="failed to read text document"):
        document_files_to_sections(
            [
                DocumentFile(
                    path=str(path),
                    source_type="earnings_presentation",
                    document_id="presentation",
                    title="Presentation",
                )
            ]
        )


def test_pdf_extract_text_error_is_document_validation_error(monkeypatch, tmp_path):
    path = tmp_path / "presentation.pdf"
    path.write_bytes(b"%PDF-1.4")

    class BadPage:
        def extract_text(self):
            raise RuntimeError("extract failed")

    class FakePdfReader:
        def __init__(self, file_path: str) -> None:
            self.pages = [BadPage()]

    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=FakePdfReader))

    with pytest.raises(DocumentFileValidationError, match="page 1"):
        document_files_to_sections(
            [
                DocumentFile(
                    path=str(path),
                    source_type="earnings_presentation",
                    document_id="presentation",
                    title="Presentation",
                )
            ]
        )


def test_reviews_endpoint_maps_expected_domain_errors():
    api.app.dependency_overrides[api.get_workflow] = lambda: _FailingWorkflow(
        APITimeoutError("upstream timed out", source="sec")
    )
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json={"ticker": "NVDA", "fiscal_period": "2025Q3"},
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json()["detail"] == {
        "code": "api_timeout",
        "message": "upstream timed out",
        "source": "sec",
        "retryable": True,
    }


def test_reviews_endpoint_maps_rate_limit_domain_errors():
    api.app.dependency_overrides[api.get_workflow] = lambda: _FailingWorkflow(
        APIRateLimitError("upstream rate limited", source="sec", upstream_status_code=429)
    )
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json={"ticker": "NVDA", "fiscal_period": "2025Q3"},
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 429
    detail = response.json()["detail"]
    assert detail["code"] == "api_rate_limit"
    assert detail["upstream_status_code"] == 429
    assert detail["retryable"] is True


def test_reviews_endpoint_maps_workflow_validation_errors():
    api.app.dependency_overrides[api.get_workflow] = lambda: _FailingWorkflow(
        WorkflowValidationError("judge_decision.negative_evidence must not be empty")
    )
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json={"ticker": "NVDA", "fiscal_period": "2025Q3"},
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "workflow_validation_error"


def test_reviews_endpoint_maps_numeric_grounding_as_workflow_validation_error():
    api.app.dependency_overrides[api.get_workflow] = lambda: _FailingWorkflow(
        NumericGroundingError("material claim lacks numeric grounding")
    )
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json={"ticker": "NVDA", "fiscal_period": "2025Q3"},
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "workflow_validation_error"


def test_reviews_endpoint_maps_workflow_agent_errors():
    api.app.dependency_overrides[api.get_workflow] = lambda: _FailingWorkflow(
        WorkflowAgentError("agent failed")
    )
    try:
        response = TestClient(api.app, raise_server_exceptions=False).post(
            "/reviews",
            json={"ticker": "NVDA", "fiscal_period": "2025Q3"},
        )
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "workflow_agent_error"


def test_llm_provider_timeout_is_typed_api_error():
    class TimeoutLLM:
        def complete(self, *args, **kwargs):
            raise TimeoutError("provider timed out")

    with pytest.raises(APITimeoutError) as exc_info:
        EarningsQualityAnalyst(TimeoutLLM()).run({})

    assert exc_info.value.to_api_detail()["source"] == "llm"
