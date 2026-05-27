"""Preprocessor: fetches filing + market consensus, then segments the
filing into typed sections.

This module is THE answer to context engineering: the LLM never sees
the raw 80-page filing. By the time anything reaches an agent, it has
been (a) chunked semantically and (b) annotated with structured numbers.
"""

from __future__ import annotations

import os
import re
from math import isfinite
from pathlib import Path
from typing import Any

import requests
import structlog
import yfinance as yf
from bs4 import BeautifulSoup
from pydantic import ValidationError

from .errors import (
    APIConnectionError,
    APIHTTPStatusError,
    APIRateLimitError,
    APITimeoutError,
    DocumentExtractionError,
    SECParsingError,
)
from .workflow_models import DocumentFile, DocumentSection, FinancialMetrics, SourceRef, SourceType

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


class DocumentFileValidationError(DocumentExtractionError):
    """Raised when a local document file cannot be converted into sections."""


def _exception_text(exc: Exception) -> str:
    return f"{exc.__class__.__module__}.{exc.__class__.__name__}: {exc}".lower()


def _upstream_status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return status_code if isinstance(status_code, int) else None


def _yfinance_error(stage: str, ticker: str, exc: Exception):
    text = _exception_text(exc)
    status_code = _upstream_status_code(exc)
    details = {"ticker": ticker.upper(), "stage": stage}

    if isinstance(exc, requests.Timeout) or "timeout" in text or "timed out" in text:
        return APITimeoutError(
            f"yfinance {stage} request timed out for {ticker.upper()}",
            source="yfinance",
            details=details,
        )
    if status_code == 429 or "rate limit" in text or "too many requests" in text:
        return APIRateLimitError(
            f"yfinance {stage} request was rate limited for {ticker.upper()}",
            source="yfinance",
            upstream_status_code=status_code,
            details=details,
        )
    if isinstance(exc, requests.ConnectionError) or "connection" in text:
        return APIConnectionError(
            f"yfinance {stage} request failed to connect for {ticker.upper()}",
            source="yfinance",
            details=details,
        )
    if isinstance(exc, requests.HTTPError) or status_code is not None:
        return APIHTTPStatusError(
            f"yfinance {stage} request failed with HTTP status for {ticker.upper()}",
            source="yfinance",
            upstream_status_code=status_code,
            retryable=status_code is None or status_code >= 500,
            details={**details, "error_type": exc.__class__.__name__},
        )
    return None


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
    except OSError as exc:
        raise DocumentFileValidationError(
            f"failed to read text document: {document_file.path}"
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

    try:
        pages = list(reader.pages)
    except Exception as exc:
        raise DocumentFileValidationError(
            f"failed to read PDF pages: {document_file.path}"
        ) from exc

    sections = []
    for page_index, page in enumerate(pages, start=1):
        try:
            page_text = _normalize_document_text(page.extract_text() or "")
        except Exception as exc:
            raise DocumentFileValidationError(
                f"failed to extract text from PDF document: {document_file.path} page {page_index}"
            ) from exc
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


def build_financial_metrics(
    *,
    ticker: str,
    fiscal_period: str,
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
) -> FinancialMetrics:
    """Build normalized financial metrics passed to workflow agents."""
    if eps_surprise_pct is None:
        eps_surprise_pct = calculate_surprise_pct(eps, eps_consensus)
    if revenue_surprise_pct is None:
        revenue_surprise_pct = calculate_surprise_pct(revenue, revenue_consensus)
    if free_cash_flow is None and operating_cash_flow is not None and capex is not None:
        free_cash_flow = operating_cash_flow - abs(capex)

    return FinancialMetrics(
        ticker=ticker,
        fiscal_period=fiscal_period,
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
        source_refs=[
            SourceRef(
                source_id=f"financial_api:{ticker.upper()}:{fiscal_period}",
                source_type=SourceType.FINANCIAL_API,
                metric_name="consensus_snapshot",
                title="Financial API consensus snapshot",
            )
        ],
    )


def fetch_filing_html(url: str) -> str:
    """Fetch a SEC filing HTML. Caches under samples/cache/ to keep
    iteration cheap and deterministic (dev/prod parity, factor X)."""
    import hashlib

    cache_dir = Path("samples/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:12]
    cache_path = cache_dir / f"{key}.html"

    if cache_path.exists():
        log.info("filing.cache_hit", url=url)
        return cache_path.read_text(encoding="utf-8")

    ua = os.getenv("SEC_USER_AGENT", "earnings-debate-agent contact@example.com")
    try:
        r = requests.get(url, headers={"User-Agent": ua}, timeout=30)
    except requests.Timeout as exc:
        raise APITimeoutError(f"SEC filing request timed out: {url}", source="sec") from exc
    except requests.ConnectionError as exc:
        raise APIConnectionError(
            f"SEC filing request failed to connect: {url}", source="sec"
        ) from exc
    except requests.RequestException as exc:
        raise APIHTTPStatusError(
            f"SEC filing request failed before a response was received: {url}",
            source="sec",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    if r.status_code == 429:
        raise APIRateLimitError(
            f"SEC filing request was rate limited: {url}",
            source="sec",
            upstream_status_code=r.status_code,
        )
    try:
        r.raise_for_status()
    except requests.HTTPError as exc:
        raise APIHTTPStatusError(
            f"SEC filing request failed with HTTP {r.status_code}: {url}",
            source="sec",
            upstream_status_code=r.status_code,
            retryable=500 <= r.status_code < 600,
        ) from exc
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

    if not result:
        raise SECParsingError("SEC filing yielded no extractable document sections", source="sec")

    log.info("filing.segmented", sections={s.heading: len(s.text) for s in result})
    return result


def fetch_consensus(ticker: str, fiscal_period: str) -> FinancialMetrics:
    """Pull actual & consensus EPS and revenue from yfinance.

    NOTE: yfinance scrapes Yahoo Finance and the schema occasionally
    changes. This function is intentionally defensive — it fills what
    it can and leaves the rest as None for downstream agents to handle.
    """
    t = yf.Ticker(ticker)

    eps_actual = None
    eps_consensus = None
    eps_surprise_pct = None
    revenue_actual = None
    try:
        earnings_dates = t.earnings_dates
        if earnings_dates is not None and not earnings_dates.empty:
            row = earnings_dates.iloc[0]  # most recent
            eps_actual = safe_float(row.get("Reported EPS"))
            eps_consensus = safe_float(row.get("EPS Estimate"))
            eps_surprise_pct = safe_float(row.get("Surprise(%)"))
    except Exception as exc:
        log.warning("yfinance.eps_fetch_failed", error=str(exc))
        api_error = _yfinance_error("earnings_dates", ticker, exc)
        if api_error is not None:
            raise api_error from exc

    try:
        quarterly_financials = t.quarterly_financials
        if quarterly_financials is not None and not quarterly_financials.empty:
            if "Total Revenue" in quarterly_financials.index:
                revenue_actual = safe_float(quarterly_financials.loc["Total Revenue"].iloc[0])
    except Exception as exc:
        log.warning("yfinance.revenue_fetch_failed", error=str(exc))
        api_error = _yfinance_error("quarterly_financials", ticker, exc)
        if api_error is not None:
            raise api_error from exc

    return build_financial_metrics(
        ticker=ticker,
        fiscal_period=fiscal_period,
        eps=eps_actual,
        eps_consensus=eps_consensus,
        eps_surprise_pct=eps_surprise_pct,
        revenue=revenue_actual,
    )
