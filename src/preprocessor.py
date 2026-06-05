"""Preprocessor: fetches filing + market consensus, then segments the
filing into typed sections.

This module is THE answer to context engineering: the LLM never sees
the raw 80-page filing. By the time anything reaches an agent, it has
been (a) chunked semantically and (b) annotated with structured numbers.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from math import isfinite
from pathlib import Path
from typing import Any

import structlog
import yfinance as yf
from bs4 import BeautifulSoup
from pydantic import ValidationError

from .metric_normalizer import resolve_canonical_metric
from .workflow_models import (
    AvailabilityItem,
    AvailabilityStatus,
    ContextBudget,
    DerivedMetricValue,
    DocumentFile,
    DocumentSection,
    FinancialMetrics,
    InputProfile,
    MetricPeriodRole,
    MetricValue,
    NormalizedMetric,
    NormalizedReviewRequest,
    SourceManifestEntry,
    SourceRef,
    SourceType,
    UnmappedMetric,
    source_refs_from_financial_metrics,
)

log = structlog.get_logger()


SECTION_PATTERNS = {
    "revenue": re.compile(r"(net\s+revenue|total\s+revenue|net\s+sales)", re.I),
    "eps": re.compile(r"(earnings\s+per\s+share|diluted\s+eps)", re.I),
    "guidance": re.compile(r"(outlook|guidance)", re.I),
    "segments": re.compile(r"(segment|geographic|product\s+category)", re.I),
    "risk": re.compile(r"(risk\s+factor|forward[- ]looking\s+statement)", re.I),
}

SUPPORTED_DOCUMENT_FILE_SUFFIXES = {".pdf", ".txt", ".text", ".md"}
MAX_DOCUMENT_SECTION_CHARS = 8000
NORMALIZED_REVIEW_SCHEMA_VERSION = "normalized-review-request.v1"
DEFAULT_CONTEXT_BUDGET = {
    "max_input_tokens": 6000,
    "max_output_tokens": 2000,
    "max_total_tokens": 10000,
}


class DocumentFileValidationError(ValueError):
    """Raised when a local document file cannot be converted into sections."""


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "section"


def _normalize_document_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_text(text: str, *, max_chars: int = MAX_DOCUMENT_SECTION_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(paragraph) > max_chars:
            chunks.append(paragraph[:max_chars].strip())
            paragraph = paragraph[max_chars:].strip()
        current = paragraph
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]


def build_normalized_review_request(
    payload: Mapping[str, Any] | NormalizedReviewRequest,
) -> NormalizedReviewRequest:
    """Build normalized workflow input from CLI/local acquisition payloads."""
    if isinstance(payload, NormalizedReviewRequest):
        return payload

    data = dict(payload)
    if _looks_like_normalized_payload(data):
        return NormalizedReviewRequest.model_validate(data)

    ticker = _required_text(data, "ticker").upper()
    fiscal_period = _required_text(data, "fiscal_period", alias="quarter")
    target_earnings_date = _optional_date(data.get("target_earnings_date"))
    target_period_end_date = _optional_date(data.get("target_period_end_date"))
    prior_fiscal_period = data.get("prior_fiscal_period")
    input_profile = InputProfile(
        data.get("input_profile") or InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED
    )
    sections = _document_sections_from_local_payload(
        data,
        ticker=ticker,
        fiscal_period=fiscal_period,
    )

    should_fetch_sec = bool(data.get("use_sec", True)) and data.get("filing_url") is not None
    if should_fetch_sec:
        filing_url = str(data["filing_url"])
        sections.extend(segment_filing(fetch_filing_html(filing_url), url=filing_url))

    if not sections:
        raise ValueError(
            "document_sections, document_files, raw_text, local_path, or filing_url is required"
        )

    metrics = _financial_metrics_from_payload(
        data,
        ticker=ticker,
        fiscal_period=fiscal_period,
        target_earnings_date=target_earnings_date,
        target_period_end_date=target_period_end_date,
        prior_fiscal_period=str(prior_fiscal_period) if prior_fiscal_period else None,
        input_profile=input_profile,
    )
    source_manifest = _source_manifest_from_refs(metrics, sections)
    context_budget = ContextBudget.model_validate(
        data.get("context_budget") or DEFAULT_CONTEXT_BUDGET
    )

    return NormalizedReviewRequest(
        schema_version=str(data.get("schema_version") or NORMALIZED_REVIEW_SCHEMA_VERSION),
        request_id=str(data.get("request_id") or _slug(f"{ticker}:{fiscal_period}")),
        ticker=ticker,
        fiscal_period=fiscal_period,
        target_earnings_date=target_earnings_date,
        target_period_end_date=target_period_end_date,
        prior_fiscal_period=str(prior_fiscal_period) if prior_fiscal_period else None,
        input_profile=input_profile,
        financial_metrics=metrics,
        document_sections=sections,
        source_manifest=source_manifest,
        context_budget=context_budget,
        include_markdown=data.get("include_markdown", True),
        purpose=data.get("purpose", "earnings_review_not_investment_advice"),
        is_investment_advice=data.get("is_investment_advice", False),
        dry_run=data.get("dry_run", False),
    )


def _looks_like_normalized_payload(data: Mapping[str, Any]) -> bool:
    return {"schema_version", "financial_metrics", "source_manifest", "context_budget"}.issubset(
        data
    )


def _required_text(data: Mapping[str, Any], key: str, *, alias: str | None = None) -> str:
    value = data.get(key)
    if value is None and alias is not None:
        value = data.get(alias)
    if value is None or not str(value).strip():
        if alias is None:
            raise ValueError(f"{key} is required")
        raise ValueError(f"{key} is required")
    return str(value).strip()


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _document_sections_from_local_payload(
    data: Mapping[str, Any],
    *,
    ticker: str,
    fiscal_period: str,
) -> list[DocumentSection]:
    sections = [
        DocumentSection.model_validate(section) for section in data.get("document_sections") or []
    ]
    _validate_target_period_sections(sections, fiscal_period=fiscal_period)

    document_files = [
        DocumentFile.model_validate(document_file)
        for document_file in data.get("document_files") or []
    ]
    document_files.extend(_local_path_document_files(data.get("local_path")))
    _validate_target_period_document_files(document_files, fiscal_period=fiscal_period)
    if document_files:
        sections.extend(document_files_to_sections(document_files))

    if data.get("raw_text") is not None:
        sections.extend(
            _raw_text_to_sections(
                str(data["raw_text"]),
                ticker=ticker,
                fiscal_period=fiscal_period,
            )
        )

    return sections


def _validate_target_period_sections(
    sections: list[DocumentSection],
    *,
    fiscal_period: str,
) -> None:
    for section in sections:
        reported_period = section.source_ref.reported_period
        if reported_period is not None and reported_period != fiscal_period:
            raise ValueError(
                "document_sections must be target-period only: "
                f"{section.section_id} reported_period {reported_period} != {fiscal_period}"
            )


def _validate_target_period_document_files(
    document_files: list[DocumentFile],
    *,
    fiscal_period: str,
) -> None:
    for document_file in document_files:
        if document_file.fiscal_period is not None and document_file.fiscal_period != fiscal_period:
            raise ValueError(
                "document_files must be target-period only: "
                f"{document_file.document_id} fiscal_period {document_file.fiscal_period} "
                f"!= {fiscal_period}"
            )


def _local_path_document_files(value: Any) -> list[DocumentFile]:
    paths = _local_paths(value)
    document_files: list[DocumentFile] = []
    for index, path_value in enumerate(paths, start=1):
        path = Path(path_value).expanduser()
        suffix = f":{index}" if len(paths) > 1 else ""
        document_id = _slug(f"local:{path.stem or 'document'}{suffix}")
        document_files.append(
            DocumentFile(
                path=path_value,
                source_type=SourceType.MANUAL_UPLOAD,
                document_id=document_id,
                title=path.name or "Local document",
            )
        )
    return document_files


def _local_paths(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [str(path) for path in value]
    raise ValueError("local_path must be a path string or list of path strings")


def _raw_text_to_sections(
    raw_text: str,
    *,
    ticker: str,
    fiscal_period: str,
) -> list[DocumentSection]:
    text = _normalize_document_text(raw_text)
    if not text:
        raise DocumentFileValidationError("raw_text is empty")

    document_id = _slug(f"raw-text:{ticker}:{fiscal_period}")
    sections = []
    for index, chunk in enumerate(_chunk_text(text), start=1):
        section_id = _slug(f"{document_id}:section-{index}")
        sections.append(
            DocumentSection(
                section_id=section_id,
                source_ref=SourceRef(
                    source_id=section_id,
                    source_type=SourceType.MANUAL_UPLOAD,
                    document_id=document_id,
                    section_id=section_id,
                    title="Raw text input",
                ),
                heading=f"Raw text input section {index}",
                text=chunk,
            )
        )
    return sections


def _financial_metrics_from_payload(
    data: Mapping[str, Any],
    *,
    ticker: str,
    fiscal_period: str,
    target_earnings_date: date | None = None,
    target_period_end_date: date | None = None,
    prior_fiscal_period: str | None = None,
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED,
) -> FinancialMetrics:
    if data.get("financial_metrics") is None:
        return fetch_consensus(
            ticker,
            fiscal_period,
            target_earnings_date=target_earnings_date,
            target_period_end_date=target_period_end_date,
            prior_fiscal_period=prior_fiscal_period,
            input_profile=input_profile,
        )

    metrics = FinancialMetrics.model_validate(data["financial_metrics"])
    updates: dict[str, Any] = {}
    if target_earnings_date is not None and metrics.target_earnings_date is None:
        updates["target_earnings_date"] = target_earnings_date
    if target_period_end_date is not None and metrics.target_period_end_date is None:
        updates["target_period_end_date"] = target_period_end_date
    if prior_fiscal_period is not None and metrics.prior_fiscal_period is None:
        updates["prior_fiscal_period"] = prior_fiscal_period
    if metrics.input_profile != input_profile:
        updates["input_profile"] = input_profile
    return metrics.model_copy(update=updates) if updates else metrics


def _source_manifest_from_refs(
    metrics: FinancialMetrics,
    sections: list[DocumentSection],
) -> list[SourceManifestEntry]:
    manifest_by_id: dict[str, SourceManifestEntry] = {}
    for source_ref in [
        *source_refs_from_financial_metrics(metrics),
        *(section.source_ref for section in sections),
    ]:
        entry = _source_manifest_entry_from_ref(source_ref)
        existing = manifest_by_id.get(entry.source_id)
        if existing is not None:
            if existing.model_dump(mode="json", exclude_none=True) != entry.model_dump(
                mode="json", exclude_none=True
            ):
                raise ValueError(
                    f"duplicate source_id has inconsistent metadata: {entry.source_id}"
                )
            continue
        manifest_by_id[entry.source_id] = entry

    if not manifest_by_id:
        raise ValueError("source_manifest requires at least one source_ref")
    return list(manifest_by_id.values())


def _source_manifest_entry_from_ref(source_ref: SourceRef) -> SourceManifestEntry:
    return SourceManifestEntry(
        source_id=source_ref.source_id,
        source_type=source_ref.source_type,
        document_id=source_ref.document_id,
        title=source_ref.title,
        url=source_ref.url,
        section_id=source_ref.section_id,
        metric_name=source_ref.metric_name,
        page=source_ref.page,
        line_range=source_ref.line_range,
        reported_period=source_ref.reported_period,
        as_of_date=source_ref.as_of_date,
        provider=source_ref.provider,
        provider_row_date=source_ref.provider_row_date,
        provider_column_date=source_ref.provider_column_date,
        period_role=source_ref.period_role,
    )


def document_files_to_sections(document_files: list[DocumentFile]) -> list[DocumentSection]:
    """Expand local PDF/text documents into validated workflow sections."""
    sections: list[DocumentSection] = []
    for document_file in document_files:
        path = Path(document_file.path).expanduser()
        if not path.exists():
            raise DocumentFileValidationError(f"document file does not exist: {document_file.path}")
        if not path.is_file():
            raise DocumentFileValidationError(f"document path is not a file: {document_file.path}")

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_DOCUMENT_FILE_SUFFIXES:
            supported = ", ".join(sorted(SUPPORTED_DOCUMENT_FILE_SUFFIXES))
            raise DocumentFileValidationError(
                f"unsupported document file extension for {document_file.path}; supported: {supported}"
            )

        if suffix == ".pdf":
            sections.extend(_pdf_file_to_sections(path, document_file))
        else:
            sections.extend(_text_file_to_sections(path, document_file))

    if document_files and not sections:
        raise DocumentFileValidationError("document_files produced no document_sections")
    return sections


def _text_file_to_sections(path: Path, document_file: DocumentFile) -> list[DocumentSection]:
    try:
        text = _normalize_document_text(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise DocumentFileValidationError(
            f"text document must be UTF-8 encoded: {document_file.path}"
        ) from exc
    if not text:
        raise DocumentFileValidationError(f"text document is empty: {document_file.path}")

    sections = []
    for index, chunk in enumerate(_chunk_text(text), start=1):
        section_id = _slug(f"{document_file.document_id}:section-{index}")
        sections.append(
            _build_document_section(
                document_file=document_file,
                section_id=section_id,
                heading=f"{document_file.title} section {index}",
                text=chunk,
            )
        )
    return sections


def _pdf_file_to_sections(path: Path, document_file: DocumentFile) -> list[DocumentSection]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentFileValidationError(
            "PDF document ingestion requires the 'pypdf' package to be installed"
        ) from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise DocumentFileValidationError(
            f"failed to read PDF document: {document_file.path}"
        ) from exc

    sections = []
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = _normalize_document_text(page.extract_text() or "")
        if not page_text:
            continue
        for chunk_index, chunk in enumerate(_chunk_text(page_text), start=1):
            section_id = _slug(f"{document_file.document_id}:p{page_index}:section-{chunk_index}")
            sections.append(
                _build_document_section(
                    document_file=document_file,
                    section_id=section_id,
                    heading=f"{document_file.title} page {page_index}",
                    text=chunk,
                    page=page_index,
                )
            )

    if not sections:
        raise DocumentFileValidationError(
            f"PDF document yielded no extractable text: {document_file.path}"
        )
    return sections


def _build_document_section(
    *,
    document_file: DocumentFile,
    section_id: str,
    heading: str,
    text: str,
    page: int | None = None,
) -> DocumentSection:
    source_ref = SourceRef(
        source_id=section_id,
        source_type=document_file.source_type,
        document_id=document_file.document_id,
        section_id=section_id,
        page=page,
        title=document_file.title,
    )
    try:
        return DocumentSection(
            section_id=section_id,
            source_ref=source_ref,
            heading=heading,
            text=text,
            start_page=page,
            end_page=page,
        )
    except ValidationError as exc:
        raise DocumentFileValidationError(
            f"document section validation failed for {document_file.path}: {exc}"
        ) from exc


def safe_float(value: Any) -> float | None:
    """Convert external numeric values without leaking NaN into contracts."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def calculate_surprise_pct(actual: float | None, consensus: float | None) -> float | None:
    if actual is None or consensus is None or consensus == 0:
        return None
    return ((actual - consensus) / abs(consensus)) * 100


def _provider_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        try:
            return value.date()
        except (TypeError, ValueError):
            return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _target_earnings_row(frame: Any, target_earnings_date: date | None) -> tuple[Any, date | None]:
    if frame is None or getattr(frame, "empty", True) or target_earnings_date is None:
        return None, None
    if not hasattr(frame, "iterrows"):
        return None, None

    date_columns = ("Earnings Date", "EarningsDate", "earnings_date")
    for index, row in frame.iterrows():
        candidate = _provider_date(index)
        if candidate is None:
            for column in date_columns:
                if hasattr(row, "get") and column in row:
                    candidate = _provider_date(row.get(column))
                    break
        if candidate == target_earnings_date:
            return row, candidate
    return None, None


def _target_metric_value(
    frame: Any,
    canonical_key: str,
    target_period_end_date: date | None,
) -> tuple[float | None, date | None]:
    if frame is None or getattr(frame, "empty", True):
        return None, None
    if target_period_end_date is None:
        return None, None

    target_column = None
    target_column_date = None
    for column in getattr(frame, "columns", []):
        column_date = _provider_date(column)
        if column_date == target_period_end_date:
            target_column = column
            target_column_date = column_date
            break
    if target_column is None:
        return None, None

    for raw_key in frame.index:
        if resolve_canonical_metric("yfinance", raw_key) == canonical_key:
            row = frame.loc[raw_key]
            if hasattr(row, "get"):
                return safe_float(row.get(target_column)), target_column_date
            return safe_float(row), target_column_date
    return None, None


def _availability(
    key: str,
    status: AvailabilityStatus,
    reason: str,
    *,
    source_type: SourceType = SourceType.FINANCIAL_API,
    blocks_verdict: bool = False,
) -> AvailabilityItem:
    return AvailabilityItem(
        key=key,
        status=status,
        reason=reason,
        source_type=source_type,
        blocks_verdict=blocks_verdict,
    )


def _financial_source_ref(
    *,
    ticker: str,
    fiscal_period: str,
    metric_name: str,
    provider_row_date: date | None = None,
    provider_column_date: date | None = None,
    period_role: MetricPeriodRole = MetricPeriodRole.ACTUAL,
) -> SourceRef:
    return SourceRef(
        source_id=f"financial_api:{ticker.upper()}:{fiscal_period}:{metric_name}",
        source_type=SourceType.FINANCIAL_API,
        metric_name=metric_name,
        title="yfinance verified-period metric",
        reported_period=fiscal_period,
        provider="yfinance",
        provider_row_date=provider_row_date,
        provider_column_date=provider_column_date,
        period_role=period_role,
    )


def build_financial_metrics(
    *,
    ticker: str,
    fiscal_period: str,
    target_earnings_date: date | None = None,
    target_period_end_date: date | None = None,
    prior_fiscal_period: str | None = None,
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED,
    eps: float | None = None,
    eps_consensus: float | None = None,
    eps_surprise_pct: float | None = None,
    revenue: float | None = None,
    revenue_consensus: float | None = None,
    revenue_surprise_pct: float | None = None,
    operating_margin_pct: float | None = None,
    operating_cash_flow: float | None = None,
    free_cash_flow: float | None = None,
    capex: float | None = None,
    guidance: str | None = None,
    source_refs: list[SourceRef] | None = None,
    availability: list[AvailabilityItem] | None = None,
    segment_metrics: list[NormalizedMetric] | None = None,
    unmapped_metrics: list[UnmappedMetric] | None = None,
) -> FinancialMetrics:
    """Build normalized financial metrics passed to workflow agents."""
    source_refs = source_refs
    if source_refs is None:
        source_refs = [
            SourceRef(
                source_id=f"financial_api:{ticker.upper()}:{fiscal_period}",
                source_type=SourceType.FINANCIAL_API,
                metric_name="consensus_snapshot",
                title="Financial API consensus snapshot",
                reported_period=fiscal_period,
            )
        ]

    if eps_surprise_pct is None:
        eps_surprise_pct = calculate_surprise_pct(eps, eps_consensus)
    if revenue_surprise_pct is None:
        revenue_surprise_pct = calculate_surprise_pct(revenue, revenue_consensus)
    if operating_cash_flow is not None and capex is not None:
        free_cash_flow = operating_cash_flow - abs(capex)
    canonical_metrics = _canonical_metric_values(
        ticker=ticker,
        fiscal_period=fiscal_period,
        values={
            "eps": eps,
            "revenue": revenue,
            "operating_cash_flow": operating_cash_flow,
            "capex": capex,
            "free_cash_flow": free_cash_flow,
            "operating_margin_pct": operating_margin_pct,
        },
        source_refs=source_refs,
    )
    derived_metrics = _derived_metric_values(
        ticker=ticker,
        fiscal_period=fiscal_period,
        free_cash_flow=free_cash_flow,
        source_refs=source_refs,
    )

    return FinancialMetrics(
        ticker=ticker,
        fiscal_period=fiscal_period,
        target_earnings_date=target_earnings_date,
        target_period_end_date=target_period_end_date,
        prior_fiscal_period=prior_fiscal_period,
        period_end_date=target_period_end_date,
        input_profile=input_profile,
        eps=eps,
        eps_consensus=eps_consensus,
        eps_surprise_pct=eps_surprise_pct,
        revenue=revenue,
        revenue_consensus=revenue_consensus,
        revenue_surprise_pct=revenue_surprise_pct,
        operating_margin_pct=operating_margin_pct,
        operating_cash_flow=operating_cash_flow,
        free_cash_flow=free_cash_flow,
        capex=capex,
        guidance=guidance,
        canonical_metrics=canonical_metrics,
        derived_metrics=derived_metrics,
        availability=availability or [],
        segment_metrics=segment_metrics or [],
        unmapped_metrics=unmapped_metrics or [],
        source_refs=source_refs,
    )


def _canonical_metric_values(
    *,
    ticker: str,
    fiscal_period: str,
    values: Mapping[str, float | None],
    source_refs: list[SourceRef],
) -> list[MetricValue]:
    metrics: list[MetricValue] = []
    refs_by_metric = {ref.metric_name: ref for ref in source_refs if ref.metric_name}
    units = {
        "eps": "USD/share",
        "revenue": "USD",
        "operating_cash_flow": "USD",
        "capex": "USD",
        "free_cash_flow": "USD",
        "operating_margin_pct": "pct",
    }
    for metric_name, value in values.items():
        source_ref = refs_by_metric.get(metric_name)
        if value is None or source_ref is None:
            continue
        metrics.append(
            MetricValue(
                metric_id=_metric_id(ticker, fiscal_period, metric_name),
                metric_name=metric_name,
                value=float(value),
                unit=units.get(metric_name),
                fiscal_period=fiscal_period,
                period_role=MetricPeriodRole.ACTUAL,
                source_ref=source_ref,
            )
        )
    return metrics


def _derived_metric_values(
    *,
    ticker: str,
    fiscal_period: str,
    free_cash_flow: float | None,
    source_refs: list[SourceRef],
) -> list[DerivedMetricValue]:
    refs_by_metric = {ref.metric_name: ref for ref in source_refs if ref.metric_name}
    operating_ref = refs_by_metric.get("operating_cash_flow")
    capex_ref = refs_by_metric.get("capex")
    if free_cash_flow is None or operating_ref is None or capex_ref is None:
        return []

    derived_ref = SourceRef(
        source_id=_metric_id(ticker, fiscal_period, "free_cash_flow:derived"),
        source_type=SourceType.DERIVED_METRIC,
        metric_name="free_cash_flow",
        title="Derived free cash flow",
        reported_period=fiscal_period,
        period_role=MetricPeriodRole.ACTUAL,
    )
    return [
        DerivedMetricValue(
            metric_id=_metric_id(ticker, fiscal_period, "free_cash_flow"),
            metric_name="free_cash_flow",
            value=float(free_cash_flow),
            unit="USD",
            fiscal_period=fiscal_period,
            period_role=MetricPeriodRole.ACTUAL,
            source_ref=derived_ref,
            component_metric_ids=[
                _metric_id(ticker, fiscal_period, "operating_cash_flow"),
                _metric_id(ticker, fiscal_period, "capex"),
            ],
            component_source_refs=[operating_ref, capex_ref],
        )
    ]


def _metric_id(ticker: str, fiscal_period: str, metric_name: str) -> str:
    safe_metric = _slug(metric_name)
    return f"metric:{ticker.upper()}:{fiscal_period}:{safe_metric}"


def fetch_filing_html(url: str) -> str:
    """Fetch a SEC filing HTML. Caches under samples/cache/ to keep
    iteration cheap and deterministic (dev/prod parity, factor X)."""
    import hashlib

    import requests

    cache_dir = Path("samples/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:12]
    cache_path = cache_dir / f"{key}.html"

    if cache_path.exists():
        log.info("filing.cache_hit", url=url)
        return cache_path.read_text(encoding="utf-8")

    ua = os.getenv("SEC_USER_AGENT", "earnings-debate-agent contact@example.com")
    r = requests.get(url, headers={"User-Agent": ua}, timeout=30)
    r.raise_for_status()
    cache_path.write_text(r.text, encoding="utf-8")
    log.info("filing.fetched", url=url, bytes=len(r.text))
    return r.text


def segment_filing(html: str, url: str | None = None) -> list[DocumentSection]:
    """Split filing into typed sections by scanning headers."""
    soup = BeautifulSoup(html, "lxml")
    # Collect text from common structural elements
    blocks = []
    for tag in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "td"]):
        text = tag.get_text(" ", strip=True)
        if 80 <= len(text) <= 4000:
            blocks.append(text)

    sections: dict[str, list[str]] = {k: [] for k in SECTION_PATTERNS}
    sections["other"] = []
    for b in blocks:
        matched = False
        for name, pattern in SECTION_PATTERNS.items():
            if pattern.search(b):
                sections[name].append(b)
                matched = True
                break
        if not matched:
            sections["other"].append(b)

    result: list[DocumentSection] = []
    for name, chunks in sections.items():
        if not chunks:
            continue
        # Cap each section — context budget discipline
        joined = "\n\n".join(chunks)[:8000]
        section_id = f"filing:{name}"
        result.append(
            DocumentSection(
                section_id=section_id,
                source_ref=SourceRef.model_validate(
                    {
                        "source_id": section_id,
                        "source_type": SourceType.FILING,
                        "url": url,
                        "document_id": "filing-html",
                        "section_id": section_id,
                        "title": f"Filing section: {name}",
                    }
                ),
                heading=name,
                text=joined,
            )
        )

    log.info("filing.segmented", sections={s.heading: len(s.text) for s in result})
    return result


def fetch_consensus(
    ticker: str,
    fiscal_period: str,
    *,
    target_earnings_date: date | None = None,
    target_period_end_date: date | None = None,
    prior_fiscal_period: str | None = None,
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED,
) -> FinancialMetrics:
    """Pull actual & consensus EPS and revenue from yfinance.

    NOTE: yfinance scrapes Yahoo Finance and the schema occasionally
    changes. This function is intentionally defensive — it fills what
    it can for verified target dates and leaves the rest as None for
    downstream agents to handle.
    """
    t = yf.Ticker(ticker)

    eps_actual = None
    eps_consensus = None
    eps_surprise_pct = None
    revenue_actual = None
    operating_cash_flow = None
    capex = None
    free_cash_flow = None
    source_refs: list[SourceRef] = []
    availability: list[AvailabilityItem] = []
    try:
        earnings_dates = t.earnings_dates
        row, provider_row_date = _target_earnings_row(earnings_dates, target_earnings_date)
        if row is not None:
            eps_actual = safe_float(row.get("Reported EPS"))
            eps_consensus = safe_float(row.get("EPS Estimate"))
            eps_surprise_pct = safe_float(row.get("Surprise(%)"))
            if eps_actual is not None:
                source_refs.append(
                    _financial_source_ref(
                        ticker=ticker,
                        fiscal_period=fiscal_period,
                        metric_name="eps",
                        provider_row_date=provider_row_date,
                    )
                )
            if eps_consensus is not None:
                source_refs.append(
                    _financial_source_ref(
                        ticker=ticker,
                        fiscal_period=fiscal_period,
                        metric_name="eps_consensus",
                        provider_row_date=provider_row_date,
                        period_role=MetricPeriodRole.CONSENSUS,
                    )
                )
        elif target_earnings_date is None:
            availability.append(
                _availability(
                    "yfinance:eps",
                    AvailabilityStatus.PERIOD_UNVERIFIED,
                    "target_earnings_date was not supplied; yfinance EPS row was not promoted.",
                )
            )
        else:
            availability.append(
                _availability(
                    "yfinance:eps",
                    AvailabilityStatus.PERIOD_UNVERIFIED,
                    "No yfinance EPS row matched target_earnings_date.",
                )
            )
    except Exception as e:
        log.warning("yfinance.eps_fetch_failed", error=str(e))
        availability.append(
            _availability(
                "yfinance:eps",
                AvailabilityStatus.UNAVAILABLE,
                f"yfinance EPS fetch failed: {e}",
            )
        )

    try:
        quarterly_financials = t.quarterly_financials
        revenue_actual, revenue_column_date = _target_metric_value(
            quarterly_financials,
            "revenue",
            target_period_end_date,
        )
        if revenue_actual is not None:
            source_refs.append(
                _financial_source_ref(
                    ticker=ticker,
                    fiscal_period=fiscal_period,
                    metric_name="revenue",
                    provider_column_date=revenue_column_date,
                )
            )
        elif target_period_end_date is None:
            availability.append(
                _availability(
                    "yfinance:revenue",
                    AvailabilityStatus.PERIOD_UNVERIFIED,
                    "target_period_end_date was not supplied; yfinance financial column was not promoted.",
                )
            )
        else:
            availability.append(
                _availability(
                    "yfinance:revenue",
                    AvailabilityStatus.OPTIONAL_MISSING,
                    "No verified yfinance revenue value matched target_period_end_date.",
                )
            )
    except Exception as e:
        log.warning("yfinance.revenue_fetch_failed", error=str(e))
        availability.append(
            _availability(
                "yfinance:revenue",
                AvailabilityStatus.UNAVAILABLE,
                f"yfinance revenue fetch failed: {e}",
            )
        )

    try:
        quarterly_cashflow = t.quarterly_cashflow
        operating_cash_flow, operating_cash_flow_date = _target_metric_value(
            quarterly_cashflow,
            "operating_cash_flow",
            target_period_end_date,
        )
        capex, capex_date = _target_metric_value(
            quarterly_cashflow,
            "capex",
            target_period_end_date,
        )
        free_cash_flow, free_cash_flow_date = _target_metric_value(
            quarterly_cashflow,
            "free_cash_flow",
            target_period_end_date,
        )
        cashflow_values = {
            "operating_cash_flow": (operating_cash_flow, operating_cash_flow_date),
            "capex": (capex, capex_date),
            "free_cash_flow": (free_cash_flow, free_cash_flow_date),
        }
        for metric_name, (value, provider_column_date) in cashflow_values.items():
            if value is not None:
                source_refs.append(
                    _financial_source_ref(
                        ticker=ticker,
                        fiscal_period=fiscal_period,
                        metric_name=metric_name,
                        provider_column_date=provider_column_date,
                    )
                )
        if target_period_end_date is None:
            availability.append(
                _availability(
                    "yfinance:cash_flow",
                    AvailabilityStatus.PERIOD_UNVERIFIED,
                    "target_period_end_date was not supplied; yfinance cash-flow column was not promoted.",
                )
            )
        elif operating_cash_flow is None and capex is None and free_cash_flow is None:
            availability.append(
                _availability(
                    "yfinance:cash_flow",
                    AvailabilityStatus.OPTIONAL_MISSING,
                    "No verified yfinance cash-flow values matched target_period_end_date.",
                )
            )
    except Exception as e:
        log.warning("yfinance.cashflow_fetch_failed", error=str(e))
        availability.append(
            _availability(
                "yfinance:cash_flow",
                AvailabilityStatus.UNAVAILABLE,
                f"yfinance cash-flow fetch failed: {e}",
            )
        )

    return build_financial_metrics(
        ticker=ticker,
        fiscal_period=fiscal_period,
        target_earnings_date=target_earnings_date,
        target_period_end_date=target_period_end_date,
        prior_fiscal_period=prior_fiscal_period,
        input_profile=input_profile,
        eps=eps_actual,
        eps_consensus=eps_consensus,
        eps_surprise_pct=eps_surprise_pct,
        revenue=revenue_actual,
        operating_cash_flow=operating_cash_flow,
        capex=capex,
        free_cash_flow=free_cash_flow,
        source_refs=source_refs,
        availability=availability,
    )
