"""API-first workflow contracts for earnings review.

These models define the boundary between workflow stages:
Data ingestion -> Financial Agents -> Presentation Agents ->
Evidence Aggregation -> Debate -> Judge -> MarkdownRenderer.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.workflow_errors import WorkflowErrorCategory

NonEmptyText = Annotated[str, Field(min_length=1)]
EvidenceId = Annotated[str, Field(min_length=1, max_length=80)]


class WorkflowModel(BaseModel):
    """Strict base for API contracts passed between workflow stages."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class VerdictLabel(str, Enum):
    GOOD = "good"
    NEUTRAL = "neutral"
    BAD = "bad"


class SourceType(str, Enum):
    FINANCIAL_API = "financial_api"
    DERIVED_METRIC = "derived_metric"
    EARNINGS_PRESENTATION = "earnings_presentation"
    FILING = "filing"
    EARNINGS_CALL = "earnings_call"
    PRESS_RELEASE = "press_release"
    MANUAL_UPLOAD = "manual_upload"


class InputProfile(str, Enum):
    YFINANCE_ONLY = "yfinance_only"
    YFINANCE_SEC = "yfinance_sec"
    YFINANCE_PRESENTATION_TAGGED = "yfinance_presentation_tagged"
    YFINANCE_SEC_PRESENTATION_TAGGED = "yfinance_sec_presentation_tagged"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    COMPUTED = "computed"
    OPTIONAL_MISSING = "optional_missing"
    REQUIRED_MISSING = "required_missing"
    UNAVAILABLE = "unavailable"
    PERIOD_UNVERIFIED = "period_unverified"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"
    AMBIGUOUS = "ambiguous"
    NOT_IN_CONTRACT = "not_in_contract"
    OUT_OF_SCOPE_SOURCE_POLICY = "out_of_scope_source_policy"


class MetricPeriodRole(str, Enum):
    ACTUAL = "actual"
    CONSENSUS = "consensus"
    GUIDANCE = "guidance"
    PREVIOUS_QUARTER = "previous_quarter"
    YEAR_AGO_QUARTER = "year_ago_quarter"
    PRIOR_PERIOD = "prior_period"
    FUTURE_GUIDANCE = "future_guidance"
    TARGET_PERIOD_DOCUMENT = "target_period_document"
    AUDIT_ONLY = "audit_only"


class PresentationTag(str, Enum):
    ACTUALS = "actuals"
    PNL = "pnl"
    CASH_FLOW = "cash_flow"
    BALANCE_SHEET = "balance_sheet"
    SEGMENT = "segment"
    GUIDANCE = "guidance"
    OUTLOOK = "outlook"
    ASSUMPTIONS = "assumptions"
    MANAGEMENT = "management"
    STRATEGY = "strategy"
    DEMAND = "demand"
    SUPPLY = "supply"
    CAPITAL_ALLOCATION = "capital_allocation"
    RISK = "risk"
    GAAP_NON_GAAP_RECONCILIATION = "gaap_non_gaap_reconciliation"
    ONE_TIME_ITEMS = "one_time_items"


class PresentationMetricCandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    CANONICAL = "canonical"
    CONFLICTING_WITH_CANONICAL = "conflicting_with_canonical"
    AMBIGUOUS_PERIOD = "ambiguous_period"
    AMBIGUOUS_UNIT = "ambiguous_unit"
    OUT_OF_SCOPE = "out_of_scope"


class EvidencePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    RISK = "risk"


class ClaimType(str, Enum):
    FACT = "fact"
    INTERPRETATION = "interpretation"
    FORECAST = "forecast"
    RISK = "risk"
    LIMITATION = "limitation"
    COUNTERPOINT = "counterpoint"


class FactCheckStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"
    NOT_CHECKABLE = "not_checkable"


class JudgeTreatment(str, Enum):
    DECISIVE = "decisive"
    SUPPORTING = "supporting"
    COUNTER_EVIDENCE = "counter_evidence"
    DISCOUNTED = "discounted"
    NOT_USED = "not_used"


class ReviewStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class DryRunStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class ImpactArea(str, Enum):
    EPS = "eps"
    FCF = "fcf"
    GUIDANCE = "guidance"
    BALANCE_SHEET = "balance_sheet"
    OVERALL = "overall"


class WorkflowStep(str, Enum):
    DATA_INGESTION = "data_ingestion"
    FINANCIAL_AGENTS = "financial_agents"
    PRESENTATION_AGENTS = "presentation_agents"
    EVIDENCE_AGGREGATION = "evidence_aggregation"
    DEBATE = "debate"
    JUDGE = "judge"
    MARKDOWN_RENDERER = "markdown_renderer"


class StepState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentRole(str, Enum):
    EARNINGS_QUALITY = "earnings_quality"
    CASH_FLOW_RISK = "cash_flow_risk"
    MANAGEMENT_INTENT = "management_intent"
    GUIDANCE = "guidance"
    BULL = "bull"
    BEAR = "bear"
    JUDGE = "judge"

    EPS_ANALYST = "earnings_quality"
    PNL_ANALYST = "earnings_quality"
    CFS_ANALYST = "cash_flow_risk"
    BS_ANALYST = "cash_flow_risk"
    MANAGEMENT_EVAL = "management_intent"
    RISK = "bear"
    EVAL = "judge"


class AgentTeam(str, Enum):
    FINANCIAL = "financial"
    PRESENTATION = "presentation"
    DEBATE = "debate"
    JUDGE = "judge"


LEGACY_AGENT_ROLE_VALUES = {
    "eps_analyst": AgentRole.EARNINGS_QUALITY,
    "pnl_analyst": AgentRole.EARNINGS_QUALITY,
    "cfs_analyst": AgentRole.CASH_FLOW_RISK,
    "bs_analyst": AgentRole.CASH_FLOW_RISK,
    "management_eval": AgentRole.MANAGEMENT_INTENT,
    "risk": AgentRole.BEAR,
    "eval": AgentRole.JUDGE,
}

RAW_ACQUISITION_FIELDS = frozenset(
    {
        "filing_url",
        "presentation_url",
        "transcript_url",
        "document_files",
        "raw_text",
        "local_path",
    }
)
MAX_MARKDOWN_REPORT_CHARS = 200_000


def raw_acquisition_fields_in(payload: Mapping[str, Any]) -> set[str]:
    """Return raw acquisition fields present in a normalized API payload."""

    return set(payload) & RAW_ACQUISITION_FIELDS


def reject_raw_acquisition_fields(payload: Mapping[str, Any]) -> None:
    raw_fields = sorted(raw_acquisition_fields_in(payload))
    if raw_fields:
        raise ValueError(
            "raw acquisition fields are not accepted by normalized review input: "
            f"{', '.join(raw_fields)}"
        )


def source_ids_from_manifest(source_manifest: list[SourceManifestEntry]) -> set[str]:
    return {source.source_id for source in source_manifest}


def source_manifest_by_id(
    source_manifest: list[SourceManifestEntry],
) -> dict[str, SourceManifestEntry]:
    return {source.source_id: source for source in source_manifest}


def validate_source_ref_registered_and_consistent(
    source_ref: SourceRef,
    source_manifest: list[SourceManifestEntry],
    context: str,
) -> None:
    manifest_entry = source_manifest_by_id(source_manifest).get(source_ref.source_id)
    if manifest_entry is None:
        raise ValueError(f"unregistered source_id in {context}: {source_ref.source_id}")

    if source_ref.source_type != manifest_entry.source_type:
        raise ValueError(
            "source_manifest mismatch in "
            f"{context} for {source_ref.source_id}: source_type "
            f"{source_ref.source_type.value} != {manifest_entry.source_type.value}"
        )

    fields_to_compare = (
        "metric_name",
        "document_id",
        "section_id",
        "page",
        "line_range",
        "reported_period",
        "as_of_date",
        "provider",
        "provider_row_date",
        "provider_column_date",
        "period_role",
    )
    for field_name in fields_to_compare:
        source_value = getattr(source_ref, field_name)
        manifest_value = getattr(manifest_entry, field_name)
        if (
            source_value is not None
            and manifest_value is not None
            and source_value != manifest_value
        ):
            raise ValueError(
                "source_manifest mismatch in "
                f"{context} for {source_ref.source_id}: {field_name} "
                f"{source_value} != {manifest_value}"
            )

    if source_ref.url is not None and manifest_entry.url is not None:
        if str(source_ref.url) != str(manifest_entry.url):
            raise ValueError(
                "source_manifest mismatch in "
                f"{context} for {source_ref.source_id}: url "
                f"{source_ref.url} != {manifest_entry.url}"
            )


class LineRange(WorkflowModel):
    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> LineRange:
        if self.end < self.start:
            raise ValueError("line_range.end must be greater than or equal to line_range.start")
        return self


class SourceRef(WorkflowModel):
    """Traceable reference for source-backed claims.

    Financial sources must identify the metric. Document-like sources must
    identify a document location, URL, or page so downstream validators can
    reject untraceable evidence.
    """

    source_id: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9_.:-]+$",
        description="Stable ID used to trace evidence back to source material.",
    )
    source_type: SourceType
    title: str | None = Field(default=None, max_length=300)
    url: AnyUrl | None = None
    document_id: str | None = Field(default=None, max_length=120)
    section_id: str | None = Field(default=None, max_length=120)
    page: int | None = Field(default=None, ge=1)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    line_range: LineRange | None = None
    metric_name: str | None = Field(default=None, max_length=120)
    reported_period: str | None = Field(default=None, max_length=40)
    as_of_date: date | None = None
    provider: str | None = Field(default=None, max_length=80)
    provider_row_date: date | None = None
    provider_column_date: date | None = None
    period_role: MetricPeriodRole | None = None

    @model_validator(mode="after")
    def validate_locator(self) -> SourceRef:
        if self.line_end is not None:
            if self.line_start is None:
                raise ValueError("line_end requires line_start")
            if self.line_end < self.line_start:
                raise ValueError("line_end must be greater than or equal to line_start")

        if self.source_type in {SourceType.FINANCIAL_API, SourceType.DERIVED_METRIC}:
            if not self.metric_name:
                raise ValueError("financial source_ref requires metric_name")
            return self

        has_document_locator = any(
            [self.document_id, self.section_id, self.page is not None, self.url]
        )
        if not has_document_locator:
            raise ValueError("document source_ref requires document_id, section_id, page, or url")
        return self


class SourceManifestEntry(WorkflowModel):
    """Authoritative source registration for normalized workflow input."""

    source_id: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9_.:-]+$",
        description="Stable ID referenced by sections, metrics, evidence, and report claims.",
    )
    source_type: SourceType
    document_id: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=300)
    url: AnyUrl | None = None
    section_id: str | None = Field(default=None, max_length=120)
    metric_name: str | None = Field(default=None, max_length=120)
    page: int | None = Field(default=None, ge=1)
    line_range: LineRange | None = None
    reported_period: str | None = Field(default=None, max_length=40)
    as_of_date: date | None = None
    provider: str | None = Field(default=None, max_length=80)
    provider_row_date: date | None = None
    provider_column_date: date | None = None
    period_role: MetricPeriodRole | None = None

    @model_validator(mode="after")
    def validate_locator(self) -> SourceManifestEntry:
        if self.source_type in {SourceType.FINANCIAL_API, SourceType.DERIVED_METRIC}:
            if not self.metric_name:
                raise ValueError("financial source_manifest entry requires metric_name")
            return self

        has_document_locator = any(
            [self.document_id, self.section_id, self.page is not None, self.url]
        )
        if not has_document_locator:
            raise ValueError(
                "document source_manifest entry requires document_id, section_id, page, or url"
            )
        return self


class DocumentSection(WorkflowModel):
    section_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    source_ref: SourceRef
    heading: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=12000)
    start_page: int | None = Field(default=None, ge=1)
    end_page: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_pages(self) -> DocumentSection:
        if self.end_page is not None:
            if self.start_page is None:
                raise ValueError("end_page requires start_page")
            if self.end_page < self.start_page:
                raise ValueError("end_page must be greater than or equal to start_page")
        return self


class DocumentFile(WorkflowModel):
    path: str = Field(min_length=1, max_length=500)
    source_type: SourceType = SourceType.MANUAL_UPLOAD
    document_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    title: str = Field(min_length=1, max_length=300)
    fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    period_role: MetricPeriodRole | None = None


class AvailabilityItem(WorkflowModel):
    key: str = Field(min_length=1, max_length=160)
    status: AvailabilityStatus
    reason: str = Field(min_length=1, max_length=1200)
    source_type: SourceType | None = None
    blocks_verdict: bool = False


class MetricValue(WorkflowModel):
    metric_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    metric_name: str = Field(min_length=1, max_length=120)
    value: float
    unit: str | None = Field(default=None, max_length=40)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    period_role: MetricPeriodRole
    source_ref: SourceRef


class DerivedMetricValue(MetricValue):
    component_metric_ids: list[str] = Field(min_length=1, max_length=20)
    component_source_refs: list[SourceRef] = Field(min_length=1, max_length=20)


class GuidanceMetric(MetricValue):
    low_value: float | None = None
    high_value: float | None = None
    assumptions: list[NonEmptyText] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_range_order(self) -> GuidanceMetric:
        if self.low_value is not None and self.high_value is not None:
            if self.high_value < self.low_value:
                raise ValueError("guidance high_value must be greater than or equal to low_value")
        return self


class GuidanceDelta(WorkflowModel):
    metric_name: str = Field(min_length=1, max_length=120)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    company_guidance: GuidanceMetric
    consensus_estimate: MetricValue
    delta_value: float
    delta_pct: float | None = None

    @model_validator(mode="after")
    def validate_matching_metric_and_period(self) -> GuidanceDelta:
        if self.company_guidance.metric_name != self.consensus_estimate.metric_name:
            raise ValueError("guidance delta requires matching metric names")
        if self.company_guidance.fiscal_period != self.consensus_estimate.fiscal_period:
            raise ValueError("guidance delta requires matching fiscal periods")
        if self.metric_name != self.company_guidance.metric_name:
            raise ValueError("guidance delta metric_name must match company guidance")
        if self.fiscal_period != self.company_guidance.fiscal_period:
            raise ValueError("guidance delta fiscal_period must match company guidance")
        return self


class TaggedPresentationSection(WorkflowModel):
    section: DocumentSection
    tags: list[PresentationTag] = Field(default_factory=list, max_length=20)


class PresentationMetricCandidate(WorkflowModel):
    candidate_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    metric_name: str = Field(min_length=1, max_length=120)
    raw_text: str = Field(min_length=1, max_length=500)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=40)
    fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    period_role: MetricPeriodRole | None = None
    status: PresentationMetricCandidateStatus = PresentationMetricCandidateStatus.CANDIDATE
    source_ref: SourceRef


class MetricConflict(WorkflowModel):
    conflict_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    metric_name: str = Field(min_length=1, max_length=120)
    period_role: MetricPeriodRole
    canonical_metric_id: str | None = Field(default=None, max_length=120)
    conflicting_metric_ids: list[str] = Field(min_length=1, max_length=20)
    reason: str = Field(min_length=1, max_length=1200)


class EarningsQualityInputs(WorkflowModel):
    metrics: list[MetricValue] = Field(default_factory=list, max_length=100)
    presentation_sections: list[TaggedPresentationSection] = Field(default_factory=list)
    sec_sections: list[DocumentSection] = Field(default_factory=list)
    availability: list[AvailabilityItem] = Field(default_factory=list)


class CashFlowRiskInputs(EarningsQualityInputs):
    derived_metrics: list[DerivedMetricValue] = Field(default_factory=list, max_length=50)


class ManagementIntentInputs(WorkflowModel):
    presentation_sections: list[TaggedPresentationSection] = Field(default_factory=list)
    sec_sections: list[DocumentSection] = Field(default_factory=list)
    availability: list[AvailabilityItem] = Field(default_factory=list)


class GuidanceInputs(WorkflowModel):
    company_guidance: list[GuidanceMetric] = Field(default_factory=list, max_length=50)
    consensus_estimates: list[MetricValue] = Field(default_factory=list, max_length=50)
    guidance_deltas: list[GuidanceDelta] = Field(default_factory=list, max_length=50)
    presentation_sections: list[TaggedPresentationSection] = Field(default_factory=list)
    sec_sections: list[DocumentSection] = Field(default_factory=list)
    availability: list[AvailabilityItem] = Field(default_factory=list)


class RawMetricBase(WorkflowModel):
    raw_key: str = Field(min_length=1, max_length=200)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=40)
    period: str | None = Field(default=None, max_length=40)
    source: str = Field(min_length=1, max_length=40)
    axis: str | None = Field(default=None, max_length=200)
    member: str | None = Field(default=None, max_length=200)
    scope: Literal["consolidated", "segment", "dimensional"] = "consolidated"


class NormalizedMetric(RawMetricBase):
    canonical_key: Literal[
        "revenue",
        "eps_basic",
        "eps_diluted",
        "operating_income",
        "operating_margin",
        "operating_cash_flow",
        "capex",
        "free_cash_flow",
    ]


class UnmappedMetric(RawMetricBase):
    reason: str | None = Field(default=None, max_length=200)


class FinancialMetrics(WorkflowModel):
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    target_earnings_date: date | None = None
    target_period_end_date: date | None = None
    prior_fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    period_end_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED

    revenue: float | None = None
    revenue_consensus: float | None = None
    revenue_surprise_pct: float | None = None

    eps: float | None = None
    eps_consensus: float | None = None
    eps_surprise_pct: float | None = None

    operating_margin_pct: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    capex: float | None = None

    guidance: str | None = Field(default=None, max_length=2000)
    source_refs: list[SourceRef] = Field(default_factory=list, max_length=100)
    canonical_metrics: list[MetricValue] = Field(default_factory=list, max_length=200)
    derived_metrics: list[DerivedMetricValue] = Field(default_factory=list, max_length=100)
    guidance_metrics: list[GuidanceMetric] = Field(default_factory=list, max_length=100)
    guidance_deltas: list[GuidanceDelta] = Field(default_factory=list, max_length=100)
    metric_conflicts: list[MetricConflict] = Field(default_factory=list, max_length=100)
    presentation_metric_candidates: list[PresentationMetricCandidate] = Field(
        default_factory=list,
        max_length=200,
    )
    availability: list[AvailabilityItem] = Field(default_factory=list, max_length=200)
    segment_metrics: list[NormalizedMetric] = Field(default_factory=list, max_length=500)
    unmapped_metrics: list[UnmappedMetric] = Field(default_factory=list, max_length=500)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized

    @model_validator(mode="after")
    def reconcile_presentation_candidates(self) -> FinancialMetrics:
        if not self.presentation_metric_candidates:
            return self

        canonical_values = {
            "eps": self.eps,
            "revenue": self.revenue,
            "operating_cash_flow": self.operating_cash_flow,
            "capex": self.capex,
            "free_cash_flow": self.free_cash_flow,
            "operating_margin_pct": self.operating_margin_pct,
        }
        existing_conflicts = list(self.metric_conflicts)
        updated_candidates: list[PresentationMetricCandidate] = []
        for candidate in self.presentation_metric_candidates:
            canonical_value = canonical_values.get(candidate.metric_name)
            if canonical_value is None or candidate.value is None:
                updated_candidates.append(candidate)
                continue
            if candidate.fiscal_period is None:
                updated_candidates.append(
                    candidate.model_copy(
                        update={"status": PresentationMetricCandidateStatus.AMBIGUOUS_PERIOD}
                    )
                )
                continue
            if candidate.fiscal_period != self.fiscal_period:
                updated_candidates.append(candidate)
                continue
            if candidate.period_role not in {None, MetricPeriodRole.ACTUAL}:
                updated_candidates.append(candidate)
                continue

            threshold = self._conflict_threshold(candidate.metric_name)
            denominator = max(abs(float(canonical_value)), 1.0)
            difference_ratio = abs(float(candidate.value) - float(canonical_value)) / denominator
            if difference_ratio > threshold:
                updated_candidates.append(
                    candidate.model_copy(
                        update={
                            "status": (PresentationMetricCandidateStatus.CONFLICTING_WITH_CANONICAL)
                        }
                    )
                )
                existing_conflicts.append(
                    MetricConflict(
                        conflict_id=self._safe_metric_id(
                            f"conflict:{self.ticker}:{self.fiscal_period}:{candidate.metric_name}:{candidate.candidate_id}"
                        ),
                        ticker=self.ticker,
                        fiscal_period=self.fiscal_period,
                        metric_name=candidate.metric_name,
                        period_role=MetricPeriodRole.ACTUAL,
                        canonical_metric_id=self._canonical_metric_id(candidate.metric_name),
                        conflicting_metric_ids=[candidate.candidate_id],
                        reason=(
                            f"Presentation candidate {candidate.value:g} conflicts with "
                            f"canonical {candidate.metric_name} {float(canonical_value):g}."
                        ),
                    )
                )
            else:
                updated_candidates.append(candidate)

        object.__setattr__(self, "presentation_metric_candidates", updated_candidates)
        object.__setattr__(self, "metric_conflicts", existing_conflicts)
        return self

    @staticmethod
    def _conflict_threshold(metric_name: str) -> float:
        if metric_name == "eps":
            return 0.02
        if metric_name in {"revenue"}:
            return 0.02
        if metric_name in {"free_cash_flow", "operating_cash_flow", "capex"}:
            return 0.05
        if metric_name in {"operating_margin_pct"}:
            return 0.01
        return 0.05

    def _canonical_metric_id(self, metric_name: str) -> str:
        for metric in self.canonical_metrics:
            if metric.metric_name == metric_name and metric.period_role == MetricPeriodRole.ACTUAL:
                return metric.metric_id
        return self._safe_metric_id(f"metric:{self.ticker}:{self.fiscal_period}:{metric_name}")

    @staticmethod
    def _safe_metric_id(value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-")
        return (normalized or "metric")[:120]


def source_refs_from_financial_metrics(metrics: FinancialMetrics) -> list[SourceRef]:
    """Return every metric-level source ref that may be emitted as evidence."""
    refs: list[SourceRef] = []
    seen: set[str] = set()

    def append(source_ref: SourceRef) -> None:
        if source_ref.source_id in seen:
            return
        seen.add(source_ref.source_id)
        refs.append(source_ref)

    for source_ref in metrics.source_refs:
        append(source_ref)
    for metric in metrics.canonical_metrics:
        append(metric.source_ref)
    for metric in metrics.derived_metrics:
        append(metric.source_ref)
        for component_ref in metric.component_source_refs:
            append(component_ref)
    for metric in metrics.guidance_metrics:
        append(metric.source_ref)
    for delta in metrics.guidance_deltas:
        append(delta.company_guidance.source_ref)
        append(delta.consensus_estimate.source_ref)
    for candidate in metrics.presentation_metric_candidates:
        append(candidate.source_ref)
    return refs


class ReviewRequest(WorkflowModel):
    request_id: str | None = Field(default=None, max_length=80)
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(
        validation_alias=AliasChoices("fiscal_period", "quarter"),
        pattern=r"^\d{4}Q[1-4]$",
    )
    target_earnings_date: date | None = None
    target_period_end_date: date | None = None
    prior_fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED
    use_sec: bool = True
    filing_url: AnyUrl | None = None
    presentation_url: AnyUrl | None = None
    transcript_url: AnyUrl | None = None
    financial_metrics: FinancialMetrics | None = None
    document_files: list[DocumentFile] = Field(default_factory=list, max_length=20)
    document_sections: list[DocumentSection] = Field(default_factory=list, max_length=200)
    source_refs: list[SourceRef] = Field(default_factory=list, max_length=100)
    source_manifest: list[SourceManifestEntry] = Field(default_factory=list, max_length=200)
    context_budget: ContextBudget | None = None
    include_markdown: bool = True
    purpose: Literal["earnings_review_not_investment_advice"] = (
        "earnings_review_not_investment_advice"
    )
    is_investment_advice: Literal[False] = False

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @model_validator(mode="after")
    def validate_embedded_metrics(self) -> ReviewRequest:
        if self.financial_metrics is None:
            return self
        if self.financial_metrics.ticker != self.ticker:
            raise ValueError("financial_metrics.ticker must match request ticker")
        if self.financial_metrics.fiscal_period != self.fiscal_period:
            raise ValueError("financial_metrics.fiscal_period must match request fiscal_period")
        return self


class ContextBudget(WorkflowModel):
    max_input_tokens: int = Field(gt=0, le=2_000_000)
    max_output_tokens: int = Field(gt=0, le=500_000)
    max_total_tokens: int = Field(gt=0, le=2_000_000)

    @model_validator(mode="after")
    def validate_budget(self) -> ContextBudget:
        if self.max_input_tokens + self.max_output_tokens > self.max_total_tokens:
            raise ValueError("max_input_tokens plus max_output_tokens must fit max_total_tokens")
        return self


class NormalizedReviewRequest(WorkflowModel):
    """Review input after external acquisition and normalization have completed."""

    schema_version: str = Field(min_length=1, max_length=40)
    request_id: str = Field(min_length=1, max_length=80)
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    target_earnings_date: date | None = None
    target_period_end_date: date | None = None
    prior_fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    input_profile: InputProfile = InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED
    financial_metrics: FinancialMetrics
    document_sections: list[DocumentSection] = Field(default_factory=list, max_length=200)
    tagged_presentation_sections: list[TaggedPresentationSection] = Field(
        default_factory=list,
        max_length=200,
    )
    availability: list[AvailabilityItem] = Field(default_factory=list, max_length=200)
    source_manifest: list[SourceManifestEntry] = Field(min_length=1, max_length=200)
    context_budget: ContextBudget
    include_markdown: bool
    purpose: Literal["earnings_review_not_investment_advice"]
    is_investment_advice: Literal[False]
    dry_run: bool

    @model_validator(mode="before")
    @classmethod
    def reject_raw_fields(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            reject_raw_acquisition_fields(data)
        return data

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @property
    def registered_source_ids(self) -> set[str]:
        return source_ids_from_manifest(self.source_manifest)

    @model_validator(mode="after")
    def validate_normalized_contract(self) -> NormalizedReviewRequest:
        if self.financial_metrics.ticker != self.ticker:
            raise ValueError("financial_metrics.ticker must match request ticker")
        if self.financial_metrics.fiscal_period != self.fiscal_period:
            raise ValueError("financial_metrics.fiscal_period must match request fiscal_period")

        registered_ids = self.registered_source_ids
        if len(registered_ids) != len(self.source_manifest):
            raise ValueError("source_manifest.source_id values must be unique")

        for section in self.document_sections:
            validate_source_ref_registered_and_consistent(
                section.source_ref,
                self.source_manifest,
                "document_sections",
            )

        for source_ref in source_refs_from_financial_metrics(self.financial_metrics):
            validate_source_ref_registered_and_consistent(
                source_ref,
                self.source_manifest,
                "financial_metrics.source_refs",
            )

        return self


class EvidenceItem(WorkflowModel):
    evidence_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.:-]+$")
    polarity: EvidencePolarity
    summary: str = Field(min_length=1, max_length=300)
    detail: str = Field(min_length=1, max_length=1200)
    impact_areas: list[ImpactArea] = Field(default_factory=lambda: [ImpactArea.OVERALL])
    source_ref: SourceRef
    metric_name: str | None = Field(default=None, max_length=120)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=40)
    quote: str | None = Field(default=None, max_length=1000)
    reported_period: str | None = Field(default=None, max_length=40)
    as_of_date: date | None = None
    fact_check_status: FactCheckStatus = FactCheckStatus.UNVERIFIED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ClaimRecord(WorkflowModel):
    claim_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    claim_type: ClaimType
    agent_role: AgentRole | None = None
    time_scope: str = Field(min_length=1, max_length=80)
    claim: str = Field(min_length=1, max_length=1200)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    counter_evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    interpretation: str = Field(min_length=1, max_length=2000)
    implication: str = Field(min_length=1, max_length=1200)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[NonEmptyText] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_evidence_ids(self) -> ClaimRecord:
        all_ids = self.evidence_ids + self.counter_evidence_ids
        if len(all_ids) != len(set(all_ids)):
            raise ValueError(
                "claim evidence_ids must be unique across support and counter evidence"
            )
        return self


class DecisionUse(WorkflowModel):
    decision_use_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    treatment: JudgeTreatment
    claim_id: str | None = Field(default=None, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    decisive_evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    rationale: str = Field(min_length=1, max_length=1200)
    verdict_impact: EvidencePolarity
    confidence_impact: float = Field(ge=-1.0, le=1.0)


class MissingDataItem(WorkflowModel):
    missing_data_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    topic: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=1200)
    materiality: Literal["low", "medium", "high"]
    requested_source_type: SourceType | None = None
    status: AvailabilityStatus = AvailabilityStatus.REQUIRED_MISSING
    blocks_verdict: bool = False


class ReportMatrix(WorkflowModel):
    """Traceable report contract separating facts, claims, and judge usage."""

    source_manifest: list[SourceManifestEntry] = Field(min_length=1, max_length=200)
    evidence_items: list[EvidenceItem] = Field(default_factory=list, max_length=100)
    claim_records: list[ClaimRecord] = Field(default_factory=list, max_length=100)
    decision_uses: list[DecisionUse] = Field(default_factory=list, max_length=100)
    missing_data_items: list[MissingDataItem] = Field(default_factory=list, max_length=50)
    data_quality_flags: list[AvailabilityItem] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_references(self) -> ReportMatrix:
        registered_ids = source_ids_from_manifest(self.source_manifest)
        if len(registered_ids) != len(self.source_manifest):
            raise ValueError("source_manifest.source_id values must be unique")

        evidence_ids: set[str] = set()
        for item in self.evidence_items:
            if item.evidence_id in evidence_ids:
                raise ValueError(f"duplicate evidence_id in report matrix: {item.evidence_id}")
            evidence_ids.add(item.evidence_id)
            validate_source_ref_registered_and_consistent(
                item.source_ref,
                self.source_manifest,
                "evidence_items",
            )

        claim_ids: set[str] = set()
        for claim in self.claim_records:
            if claim.claim_id in claim_ids:
                raise ValueError(f"duplicate claim_id in report matrix: {claim.claim_id}")
            claim_ids.add(claim.claim_id)
            for evidence_id in claim.evidence_ids + claim.counter_evidence_ids:
                if evidence_id not in evidence_ids:
                    raise ValueError(f"unregistered evidence_id in claim_records: {evidence_id}")

        for decision_use in self.decision_uses:
            if decision_use.claim_id is not None and decision_use.claim_id not in claim_ids:
                raise ValueError(f"unregistered claim_id in decision_uses: {decision_use.claim_id}")
            for evidence_id in decision_use.decisive_evidence_ids:
                if evidence_id not in evidence_ids:
                    raise ValueError(f"unregistered evidence_id in decision_uses: {evidence_id}")

        return self


class StepStatus(WorkflowModel):
    step: WorkflowStep
    state: StepState
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = Field(default=None, max_length=500)
    error: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_state_details(self) -> StepStatus:
        if self.state == StepState.FAILED and not self.error:
            raise ValueError("failed step requires error")
        if self.finished_at is not None and self.started_at is not None:
            if self.finished_at < self.started_at:
                raise ValueError("finished_at must be greater than or equal to started_at")
        return self


class AgentResult(WorkflowModel):
    agent_role: AgentRole
    team: AgentTeam
    status: StepStatus
    headline: str = Field(min_length=1, max_length=300)
    conclusion: str = Field(min_length=1, max_length=1200)
    key_evidence: list[EvidenceItem] = Field(default_factory=list, max_length=10)
    counter_evidence: list[EvidenceItem] = Field(default_factory=list, max_length=10)
    open_questions: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("agent_role", mode="before")
    @classmethod
    def normalize_legacy_agent_role(cls, value: AgentRole | str) -> AgentRole | str:
        if isinstance(value, str):
            return LEGACY_AGENT_ROLE_VALUES.get(value, value)
        return value


class AgentAttemptTrace(WorkflowModel):
    attempt: int = Field(ge=1)
    success: bool = False
    structured_output: bool = False
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    output_chars: int = Field(default=0, ge=0)
    category: WorkflowErrorCategory | None = None
    error_kind: str | None = Field(default=None, max_length=80)
    retryable: bool = False


class AgentExecutionTrace(WorkflowModel):
    public_role: str = Field(min_length=1, max_length=80)
    output_model: str = Field(min_length=1, max_length=120)
    max_retries: int = Field(ge=0)
    attempt_count: int = Field(ge=0)
    success: bool = False
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)
    attempts: list[AgentAttemptTrace] = Field(default_factory=list, max_length=10)


class AgentFinding(WorkflowModel):
    agent_name: str = Field(min_length=1, max_length=80)
    stance: Literal["positive", "negative", "mixed", "neutral", "unclear"]
    summary: str = Field(min_length=1, max_length=1200)
    key_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    counter_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_data: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    handoff_summary: str = Field(min_length=1, max_length=2000)


class EarningsQualityFinding(AgentFinding):
    agent_name: Literal[
        "EarningsQualityAnalyst",
        "EPSQualityAnalyst",
        "ProfitabilityAnalyst",
    ] = "EarningsQualityAnalyst"


class CashFlowRiskFinding(AgentFinding):
    agent_name: Literal[
        "CashFlowRiskAnalyst",
        "CashFlowFcfAnalyst",
        "BalanceSheetRiskAnalyst",
    ] = "CashFlowRiskAnalyst"


class ManagementIntentFinding(AgentFinding):
    agent_name: Literal["ManagementIntentAnalyst"] = "ManagementIntentAnalyst"


class GuidanceFinding(AgentFinding):
    agent_name: Literal["GuidanceAnalyst"] = "GuidanceAnalyst"


class EPSQualityFinding(EarningsQualityFinding):
    agent_name: Literal["EarningsQualityAnalyst", "EPSQualityAnalyst"] = "EarningsQualityAnalyst"


class ProfitabilityFinding(EarningsQualityFinding):
    agent_name: Literal["EarningsQualityAnalyst", "ProfitabilityAnalyst"] = "EarningsQualityAnalyst"


class CashFlowFcfFinding(CashFlowRiskFinding):
    agent_name: Literal["CashFlowRiskAnalyst", "CashFlowFcfAnalyst"] = "CashFlowRiskAnalyst"


class BalanceSheetRiskFinding(CashFlowRiskFinding):
    agent_name: Literal["CashFlowRiskAnalyst", "BalanceSheetRiskAnalyst"] = "CashFlowRiskAnalyst"


class FindingCoverage(str, Enum):
    SUPPORTING = "supporting"
    OPPOSING = "opposing"
    NOT_MATERIAL = "not_material"
    MISSING = "missing"


FindingCoverageKey = Literal[
    "earnings_quality",
    "cash_flow_risk",
    "management_intent",
    "guidance",
]
FindingCoverageMap = dict[FindingCoverageKey, FindingCoverage]
REQUIRED_FINDING_COVERAGE_KEYS = frozenset(
    {"earnings_quality", "cash_flow_risk", "management_intent", "guidance"}
)


def validate_finding_coverage_keys(coverage: FindingCoverageMap) -> FindingCoverageMap:
    keys = set(coverage)
    missing = REQUIRED_FINDING_COVERAGE_KEYS - keys
    extra = keys - REQUIRED_FINDING_COVERAGE_KEYS
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing keys: {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected keys: {', '.join(sorted(extra))}")
        message = "finding_coverage must include exactly the four specialist keys"
        raise ValueError(f"{message}; {'; '.join(details)}")
    return coverage


def validate_unique_evidence_ids(value: list[str]) -> list[str]:
    if len(value) != len(set(value)):
        raise ValueError("evidence ids must be unique")
    return value


class AnalysisBrief(WorkflowModel):
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    earnings_quality_finding: EarningsQualityFinding
    cash_flow_risk_finding: CashFlowRiskFinding
    management_intent_finding: ManagementIntentFinding
    guidance_finding: GuidanceFinding
    financial_agent_results: list[AgentResult] = Field(default_factory=list, max_length=8)
    presentation_agent_results: list[AgentResult] = Field(default_factory=list, max_length=8)
    positive_evidence_pool: list[EvidenceItem] = Field(default_factory=list, max_length=30)
    negative_evidence_pool: list[EvidenceItem] = Field(default_factory=list, max_length=30)
    risk_evidence_pool: list[EvidenceItem] = Field(default_factory=list, max_length=30)
    quality_warnings: list[AvailabilityItem] = Field(default_factory=list, max_length=100)
    synthesis: str = Field(min_length=1, max_length=2000)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized


class DebateResult(WorkflowModel):
    bull_case: str = Field(min_length=1, max_length=2000)
    bear_case: str = Field(min_length=1, max_length=2000)
    risk_case: str = Field(min_length=1, max_length=2000)
    evaluation: str = Field(min_length=1, max_length=2000)
    strongest_positive_evidence: list[EvidenceItem] = Field(default_factory=list, max_length=10)
    strongest_negative_evidence: list[EvidenceItem] = Field(default_factory=list, max_length=10)
    unresolved_questions: list[NonEmptyText] = Field(default_factory=list, max_length=8)


class BullCase(WorkflowModel):
    agent_name: Literal["bull_agent"] = "bull_agent"
    thesis: str = Field(min_length=1, max_length=2000)
    stance_strength: Literal["strong", "moderate", "weak"]
    strongest_positive_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    eps_bull_argument: str = Field(min_length=1, max_length=1200)
    fcf_bull_argument: str = Field(min_length=1, max_length=1200)
    conditions_needed: list[NonEmptyText] = Field(min_length=1, max_length=8)
    weak_points: list[NonEmptyText] = Field(min_length=1, max_length=8)
    finding_coverage: FindingCoverageMap = Field(min_length=4, max_length=4)
    disputed_points_to_watch: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_data: list[NonEmptyText] = Field(default_factory=list, max_length=8)

    @field_validator("finding_coverage")
    @classmethod
    def validate_finding_coverage(cls, value: FindingCoverageMap) -> FindingCoverageMap:
        return validate_finding_coverage_keys(value)


class BullCaseSelection(WorkflowModel):
    agent_name: Literal["bull_agent"] = "bull_agent"
    thesis: str = Field(min_length=1, max_length=2000)
    stance_strength: Literal["strong", "moderate", "weak"]
    strongest_positive_evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=3)
    eps_bull_argument: str = Field(min_length=1, max_length=1200)
    fcf_bull_argument: str = Field(min_length=1, max_length=1200)
    conditions_needed: list[NonEmptyText] = Field(min_length=1, max_length=8)
    weak_points: list[NonEmptyText] = Field(min_length=1, max_length=8)
    finding_coverage: FindingCoverageMap = Field(min_length=4, max_length=4)
    disputed_points_to_watch: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_data: list[NonEmptyText] = Field(default_factory=list, max_length=8)

    @field_validator("finding_coverage")
    @classmethod
    def validate_finding_coverage(cls, value: FindingCoverageMap) -> FindingCoverageMap:
        return validate_finding_coverage_keys(value)

    @field_validator("strongest_positive_evidence_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[str]) -> list[str]:
        return validate_unique_evidence_ids(value)


class BearCase(WorkflowModel):
    agent_name: Literal["bear_agent"] = "bear_agent"
    thesis: str = Field(min_length=1, max_length=2000)
    stance_strength: Literal["strong", "moderate", "weak"]
    strongest_negative_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    eps_bear_argument: str = Field(min_length=1, max_length=1200)
    fcf_bear_argument: str = Field(min_length=1, max_length=1200)
    failure_modes: list[NonEmptyText] = Field(min_length=1, max_length=8)
    counter_to_bull_case: list[NonEmptyText] = Field(min_length=1, max_length=8)
    finding_coverage: FindingCoverageMap = Field(min_length=4, max_length=4)
    unresolved_risks: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_data: list[NonEmptyText] = Field(default_factory=list, max_length=8)

    @field_validator("finding_coverage")
    @classmethod
    def validate_finding_coverage(cls, value: FindingCoverageMap) -> FindingCoverageMap:
        return validate_finding_coverage_keys(value)


class BearCaseSelection(WorkflowModel):
    agent_name: Literal["bear_agent"] = "bear_agent"
    thesis: str = Field(min_length=1, max_length=2000)
    stance_strength: Literal["strong", "moderate", "weak"]
    strongest_negative_evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=3)
    eps_bear_argument: str = Field(min_length=1, max_length=1200)
    fcf_bear_argument: str = Field(min_length=1, max_length=1200)
    failure_modes: list[NonEmptyText] = Field(min_length=1, max_length=8)
    counter_to_bull_case: list[NonEmptyText] = Field(min_length=1, max_length=8)
    finding_coverage: FindingCoverageMap = Field(min_length=4, max_length=4)
    unresolved_risks: list[NonEmptyText] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_data: list[NonEmptyText] = Field(default_factory=list, max_length=8)

    @field_validator("finding_coverage")
    @classmethod
    def validate_finding_coverage(cls, value: FindingCoverageMap) -> FindingCoverageMap:
        return validate_finding_coverage_keys(value)

    @field_validator("strongest_negative_evidence_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[str]) -> list[str]:
        return validate_unique_evidence_ids(value)


class JudgeDecision(WorkflowModel):
    verdict: VerdictLabel
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1, max_length=1200)
    rationale: str = Field(min_length=1, max_length=2000)
    positive_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    negative_evidence: list[EvidenceItem] = Field(min_length=1, max_length=10)
    eps_outlook: str = Field(min_length=1, max_length=1200)
    eps_outlook_reason: str = Field(min_length=1, max_length=2000)
    fcf_outlook: str = Field(min_length=1, max_length=1200)
    fcf_outlook_reason: str = Field(min_length=1, max_length=2000)
    purpose: Literal["earnings_review_not_investment_advice"] = (
        "earnings_review_not_investment_advice"
    )
    is_investment_advice: Literal[False] = False


FinalVerdict = JudgeDecision


class JudgeDecisionSelection(WorkflowModel):
    verdict: VerdictLabel
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1, max_length=1200)
    rationale: str = Field(min_length=1, max_length=2000)
    positive_evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=3)
    negative_evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=3)
    eps_outlook: str = Field(min_length=1, max_length=1200)
    eps_outlook_reason: str = Field(min_length=1, max_length=2000)
    fcf_outlook: str = Field(min_length=1, max_length=1200)
    fcf_outlook_reason: str = Field(min_length=1, max_length=2000)
    purpose: Literal["earnings_review_not_investment_advice"] = (
        "earnings_review_not_investment_advice"
    )
    is_investment_advice: Literal[False] = False

    @field_validator("positive_evidence_ids", "negative_evidence_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[str]) -> list[str]:
        return validate_unique_evidence_ids(value)


class ReviewResponse(WorkflowModel):
    request_id: str | None = Field(default=None, max_length=80)
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    steps: list[StepStatus] = Field(min_length=1, max_length=20)
    agent_traces: list[AgentExecutionTrace] = Field(default_factory=list, max_length=20)
    financial_metrics: FinancialMetrics | None = None
    analysis_brief: AnalysisBrief
    bull_case: BullCase
    bear_case: BearCase
    debate_result: DebateResult
    judge_decision: JudgeDecision
    markdown_report: str = Field(min_length=1, max_length=MAX_MARKDOWN_REPORT_CHARS)
    purpose: Literal["earnings_review_not_investment_advice"] = (
        "earnings_review_not_investment_advice"
    )
    is_investment_advice: Literal[False] = False
    disclaimer: str = Field(
        default="This report is an earnings analysis artifact and is not investment advice.",
        min_length=1,
        max_length=500,
    )

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @model_validator(mode="after")
    def validate_nested_periods(self) -> ReviewResponse:
        if self.analysis_brief.ticker != self.ticker:
            raise ValueError("analysis_brief.ticker must match response ticker")
        if self.analysis_brief.fiscal_period != self.fiscal_period:
            raise ValueError("analysis_brief.fiscal_period must match response fiscal_period")
        return self


class WorkflowErrorDetail(WorkflowModel):
    category: WorkflowErrorCategory
    message: str = Field(min_length=1, max_length=1200)
    field: str | None = Field(default=None, max_length=200)
    retryable: bool = False


class DryRunCheck(WorkflowModel):
    name: str = Field(min_length=1, max_length=120)
    status: DryRunStatus
    message: str | None = Field(default=None, max_length=1000)
    category: WorkflowErrorCategory | None = None


class ReviewSuccessResponse(WorkflowModel):
    status: Literal[ReviewStatus.COMPLETED] = ReviewStatus.COMPLETED
    request_id: str | None = Field(default=None, max_length=80)
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    steps: list[StepStatus] = Field(min_length=1, max_length=20)
    agent_traces: list[AgentExecutionTrace] = Field(default_factory=list, max_length=20)
    analysis_brief: AnalysisBrief
    claim_matrix: ReportMatrix
    bull_case: BullCase
    bear_case: BearCase
    debate_result: DebateResult
    judge_decision: JudgeDecision
    decision_uses: list[DecisionUse] = Field(default_factory=list, max_length=100)
    quality_gate_result: dict[str, Any] = Field(default_factory=dict)
    markdown_report: str = Field(min_length=1, max_length=MAX_MARKDOWN_REPORT_CHARS)
    disclaimer: str = Field(
        default="This report is an earnings analysis artifact and is not investment advice.",
        min_length=1,
        max_length=500,
    )

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @model_validator(mode="after")
    def validate_nested_identity(self) -> ReviewSuccessResponse:
        if self.analysis_brief.ticker != self.ticker:
            raise ValueError("analysis_brief.ticker must match response ticker")
        if self.analysis_brief.fiscal_period != self.fiscal_period:
            raise ValueError("analysis_brief.fiscal_period must match response fiscal_period")
        if self.decision_uses != self.claim_matrix.decision_uses:
            raise ValueError("decision_uses must match claim_matrix.decision_uses")
        return self


class ReviewErrorResponse(WorkflowModel):
    status: Literal[ReviewStatus.FAILED] = ReviewStatus.FAILED
    request_id: str | None = Field(default=None, max_length=80)
    ticker: str | None = Field(default=None, max_length=15)
    fiscal_period: str | None = Field(default=None, pattern=r"^\d{4}Q[1-4]$")
    errors: list[WorkflowErrorDetail] = Field(min_length=1, max_length=20)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized


class ReviewDryRunResponse(WorkflowModel):
    status: Literal[ReviewStatus.DRY_RUN] = ReviewStatus.DRY_RUN
    request_id: str = Field(min_length=1, max_length=80)
    ticker: str = Field(min_length=1, max_length=15)
    fiscal_period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    dry_run_status: DryRunStatus
    checks: list[DryRunCheck] = Field(min_length=1, max_length=50)
    errors: list[WorkflowErrorDetail] = Field(default_factory=list, max_length=20)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = str(value).upper().strip()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dots, or hyphens")
        return normalized

    @model_validator(mode="after")
    def validate_status_consistency(self) -> ReviewDryRunResponse:
        failed_checks = [check for check in self.checks if check.status == DryRunStatus.FAILED]
        if self.dry_run_status == DryRunStatus.PASSED and self.errors:
            raise ValueError("passed dry-run response cannot include errors")
        if self.dry_run_status == DryRunStatus.PASSED and failed_checks:
            raise ValueError("passed dry-run response cannot include failed checks")
        if self.dry_run_status == DryRunStatus.FAILED and not (failed_checks or self.errors):
            raise ValueError("failed dry-run response requires failed checks or errors")
        return self
