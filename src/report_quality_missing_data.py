"""Missing-data rendering and confidence caps."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .workflow_models import AvailabilityStatus, SourceType

IMPORTANT_MISSING_PATTERNS = (
    "guidance",
    "cash flow",
    "fcf",
    "capex",
    "working capital",
    "eps bridge",
    "consensus",
    "source",
)

CANONICAL_CAP_SOURCE_TYPES = {
    SourceType.FINANCIAL_API.value,
    SourceType.FILING.value,
    SourceType.DERIVED_METRIC.value,
}
NON_CAP_STATUSES = {
    AvailabilityStatus.AVAILABLE.value,
    AvailabilityStatus.COMPUTED.value,
    AvailabilityStatus.OPTIONAL_MISSING.value,
    AvailabilityStatus.NOT_IN_CONTRACT.value,
    AvailabilityStatus.OUT_OF_SCOPE_SOURCE_POLICY.value,
}
CAP_RELEVANT_STATUSES = {
    AvailabilityStatus.REQUIRED_MISSING.value,
    AvailabilityStatus.UNAVAILABLE.value,
    AvailabilityStatus.PERIOD_UNVERIFIED.value,
    AvailabilityStatus.REJECTED.value,
    AvailabilityStatus.CONFLICTING.value,
    AvailabilityStatus.AMBIGUOUS.value,
}


def _findings(brief) -> list:
    return [
        getattr(brief, "earnings_quality_finding", None),
        getattr(brief, "cash_flow_risk_finding", None),
        getattr(brief, "management_intent_finding", None),
        getattr(brief, "guidance_finding", None),
    ]


def _selected_missing_data_items(
    brief: Any,
    missing_data_items: Iterable[Any] | None,
) -> list[Any]:
    if missing_data_items is not None:
        return list(missing_data_items)
    return list(getattr(brief, "missing_data_items", []) or [])


def collect_missing_data(
    brief: Any,
    *,
    missing_data_items: Iterable[Any] | None = None,
    include_agent_missing: bool = True,
) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    matrix_missing_data = _selected_missing_data_items(brief, missing_data_items)
    for item in matrix_missing_data:
        materiality = str(getattr(item, "materiality", "") or "").lower()
        blocks_verdict = bool(getattr(item, "blocks_verdict", False))
        if blocks_verdict:
            severity = "blocking_gap"
        elif materiality in {"high", "medium"}:
            severity = "material_caveat"
        else:
            severity = "non_blocking"

        topic = str(getattr(item, "topic", "Missing data") or "Missing data")
        reason = str(getattr(item, "reason", "") or "").strip()
        requested = getattr(item, "requested_source_type", None)
        requested_value = getattr(requested, "value", requested)
        requested_text = f" Requested source: {requested_value}." if requested_value else ""
        rows.append(("ReportMatrix", severity, f"{topic}: {reason}{requested_text}".strip()))

    if include_agent_missing:
        for finding in _findings(brief):
            if finding is None:
                continue
            agent = getattr(finding, "agent_name", "UnknownAgent")
            for item in getattr(finding, "missing_data", []) or []:
                text = str(item)
                severity = (
                    "material_caveat"
                    if any(p in text.lower() for p in IMPORTANT_MISSING_PATTERNS)
                    else "non_blocking"
                )
                rows.append((agent, severity, text))
    return rows


def missing_data_lines(
    brief: Any,
    decision: Any = None,
    *,
    missing_data_items: Iterable[Any] | None = None,
) -> list[str]:
    rows = collect_missing_data(brief, missing_data_items=missing_data_items)
    if not rows:
        return ["- No material missing-data caveats were emitted by specialist agents."]
    lines = ["| Agent | Severity | Missing data / confidence limit |", "|---|---|---|"]
    for agent, severity, text in rows:
        safe = text.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {agent} | {severity} | {safe} |")
    return lines


def confidence_cap(
    brief: Any,
    decision: Any = None,
    *,
    missing_data_items: Iterable[Any] | None = None,
    include_agent_missing: bool = False,
) -> tuple[float, list[str]]:
    cap_items = _selected_missing_data_items(brief, missing_data_items)
    cap_count = sum(1 for item in cap_items if is_cap_relevant_missing_item(item))
    cap = missing_count_cap(cap_count)
    reasons = [f"canonical missing data: {cap_count}"] if cap_count else []

    if include_agent_missing:
        rows = collect_missing_data(
            brief,
            missing_data_items=[],
            include_agent_missing=True,
        )
        if any(severity == "material_caveat" for _, severity, _ in rows):
            cap = min(cap, 0.6)
            reasons.append("agent material missing data")
    return cap, reasons


def missing_count_cap(cap_count: int) -> float:
    if cap_count <= 0:
        return 1.0
    if cap_count == 1:
        return 0.8
    return 0.6


def is_cap_relevant_missing_item(item: Any) -> bool:
    source_type = _enum_value(
        getattr(item, "requested_source_type", None) or getattr(item, "source_type", None)
    )
    if source_type not in CANONICAL_CAP_SOURCE_TYPES:
        return False

    status = _enum_value(getattr(item, "status", None))
    if status in NON_CAP_STATUSES:
        return False
    if bool(getattr(item, "blocks_verdict", False)):
        return True
    if status in CAP_RELEVANT_STATUSES:
        return True

    materiality = str(getattr(item, "materiality", "") or "").lower()
    return materiality in {"medium", "high"}


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value)).lower()


def apply_confidence_caps(
    decision: Any,
    brief: Any,
    *,
    missing_data_items: Iterable[Any] | None = None,
    include_agent_missing: bool = False,
):
    cap, _ = confidence_cap(
        brief,
        decision,
        missing_data_items=missing_data_items,
        include_agent_missing=include_agent_missing,
    )
    current = float(getattr(decision, "confidence", 0.0) or 0.0)
    if current <= cap:
        return decision
    if hasattr(decision, "model_copy"):
        return decision.model_copy(update={"confidence": cap})
    return decision
