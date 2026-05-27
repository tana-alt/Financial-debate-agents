"""Typed exception classes for API, ingestion, and workflow boundaries."""

from __future__ import annotations

from typing import Any


class EarningsReviewError(ValueError):
    """Base class for expected runtime errors that can be returned by the API."""

    error_code = "earnings_review_error"
    status_code = 500
    source = "workflow"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        status_code: int | None = None,
        retryable: bool | None = None,
        upstream_status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.source = source or self.source
        self.status_code = status_code or self.status_code
        self.retryable = self.retryable if retryable is None else retryable
        self.upstream_status_code = upstream_status_code
        self.details = details or {}

    def to_api_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "code": self.error_code,
            "message": str(self),
            "source": self.source,
            "retryable": self.retryable,
        }
        if self.upstream_status_code is not None:
            detail["upstream_status_code"] = self.upstream_status_code
        if self.details:
            detail["details"] = self.details
        return detail


class ExternalAPIError(EarningsReviewError):
    """Base class for expected upstream API failures."""

    error_code = "external_api_error"
    status_code = 502
    source = "external_api"
    retryable = True


class APITimeoutError(ExternalAPIError):
    """Raised when an upstream API call times out."""

    error_code = "api_timeout"
    status_code = 504
    retryable = True


class APIRateLimitError(ExternalAPIError):
    """Raised when an upstream API returns a rate-limit response."""

    error_code = "api_rate_limit"
    status_code = 429
    retryable = True


class APIConnectionError(ExternalAPIError):
    """Raised when an upstream API cannot be reached."""

    error_code = "api_connection_error"
    status_code = 503
    retryable = True


class APIHTTPStatusError(ExternalAPIError):
    """Raised when an upstream API returns a non-rate-limit HTTP error."""

    error_code = "api_http_status_error"
    status_code = 502


class DataAcquisitionError(EarningsReviewError):
    """Base class for failures while converting external data into workflow inputs."""

    error_code = "data_acquisition_error"
    status_code = 502
    source = "data_ingestion"
    retryable = False


class YFinanceFetchError(DataAcquisitionError):
    """Raised when yfinance cannot provide usable financial data."""

    error_code = "yfinance_fetch_failed"
    source = "yfinance"
    retryable = True


class SECParsingError(DataAcquisitionError):
    """Raised when a fetched SEC filing cannot be segmented into document sections."""

    error_code = "sec_parsing_failed"
    source = "sec"


class DocumentExtractionError(EarningsReviewError):
    """Raised when local document text extraction fails."""

    error_code = "document_extraction_failed"
    status_code = 422
    source = "document"
    retryable = False


class WorkflowExecutionError(EarningsReviewError):
    """Raised when the deterministic workflow fails outside a validation gate."""

    error_code = "workflow_execution_error"
    status_code = 500
    source = "workflow"
    retryable = False


def api_error_detail(
    code: str,
    message: str,
    *,
    source: str,
    retryable: bool,
    upstream_status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "code": code,
        "message": message,
        "source": source,
        "retryable": retryable,
    }
    if upstream_status_code is not None:
        detail["upstream_status_code"] = upstream_status_code
    if details:
        detail["details"] = details
    return detail


def format_api_error_detail(detail: Any) -> str:
    """Render FastAPI error details into a concise CLI message."""

    if isinstance(detail, dict):
        code = detail.get("code")
        message = detail.get("message")
        if code and message:
            return f"{code}: {message}"
        if message:
            return str(message)
    return str(detail)
