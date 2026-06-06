"""Central registry for agent-facing expected financial metrics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .workflow_models import (
    AgentRole,
    AvailabilityItem,
    AvailabilityStatus,
    FinancialMetrics,
    MetricPeriodRole,
    MetricValue,
    SourceRef,
    SourceType,
)


class MetricRequirement(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    REFERENCE_ONLY = "reference_only"
    NOT_IN_CONTRACT = "not_in_contract"


class MetricSourcePolicy(str, Enum):
    CANONICAL = "canonical"
    CONSENSUS = "consensus"
    DERIVED = "derived"
    PRESENTATION_REFERENCE = "presentation_reference"
    DOCUMENT_TEXT = "document_text"


@dataclass(frozen=True)
class ExpectedMetricSpec:
    metric_key: str
    roles: tuple[AgentRole, ...]
    requirement: MetricRequirement
    source_policy: MetricSourcePolicy
    preferred_sources: tuple[str, ...]
    period_role: MetricPeriodRole
    cap_if_missing: bool = False
    source_type: SourceType = SourceType.FINANCIAL_API
    sec_tags: tuple[str, ...] = ()
    description: str = ""

    def for_context(self) -> dict[str, Any]:
        return {
            "metric_key": self.metric_key,
            "requirement": self.requirement.value,
            "source_policy": self.source_policy.value,
            "preferred_sources": list(self.preferred_sources),
            "period_role": self.period_role.value,
            "cap_if_missing": self.cap_if_missing,
            "source_type": self.source_type.value,
            "sec_tags": list(self.sec_tags),
            "description": self.description,
        }


REQUIRED_CANONICAL_PERIOD_ROLES = (
    MetricPeriodRole.ACTUAL,
    MetricPeriodRole.PREVIOUS_QUARTER,
    MetricPeriodRole.YEAR_AGO_QUARTER,
)
REQUIRED_CANONICAL_METRIC_KEYS = (
    "revenue",
    "eps",
    "operating_cash_flow",
    "capex",
    "free_cash_flow",
)


def _period_description(period_role: MetricPeriodRole) -> str:
    if period_role is MetricPeriodRole.ACTUAL:
        return "Current-period"
    if period_role is MetricPeriodRole.PREVIOUS_QUARTER:
        return "Previous-quarter"
    if period_role is MetricPeriodRole.YEAR_AGO_QUARTER:
        return "Year-ago-quarter"
    return period_role.value


def _required_canonical_metrics() -> tuple[ExpectedMetricSpec, ...]:
    specs: list[ExpectedMetricSpec] = []
    for period_role in REQUIRED_CANONICAL_PERIOD_ROLES:
        period_text = _period_description(period_role)
        specs.extend(
            [
                ExpectedMetricSpec(
                    metric_key="revenue",
                    roles=(
                        AgentRole.EARNINGS_QUALITY,
                        AgentRole.MANAGEMENT_INTENT,
                        AgentRole.GUIDANCE,
                        AgentRole.BULL,
                        AgentRole.BEAR,
                        AgentRole.JUDGE,
                    ),
                    requirement=MetricRequirement.REQUIRED,
                    source_policy=MetricSourcePolicy.CANONICAL,
                    preferred_sources=("sec_company_facts",),
                    period_role=period_role,
                    cap_if_missing=True,
                    sec_tags=(
                        "Revenues",
                        "SalesRevenueNet",
                        "RevenueFromContractWithCustomerExcludingAssessedTax",
                        "RevenueFromContractWithCustomerIncludingAssessedTax",
                    ),
                    description=f"{period_text} revenue.",
                ),
                ExpectedMetricSpec(
                    metric_key="eps",
                    roles=(
                        AgentRole.EARNINGS_QUALITY,
                        AgentRole.GUIDANCE,
                        AgentRole.BULL,
                        AgentRole.BEAR,
                        AgentRole.JUDGE,
                    ),
                    requirement=MetricRequirement.REQUIRED,
                    source_policy=MetricSourcePolicy.CANONICAL,
                    preferred_sources=("yfinance",),
                    period_role=period_role,
                    cap_if_missing=True,
                    sec_tags=("EarningsPerShareDiluted", "EarningsPerShareBasic"),
                    description=(
                        f"{period_text} actual EPS. SEC GAAP EPS requires basis "
                        "metadata before reconciliation."
                    ),
                ),
                ExpectedMetricSpec(
                    metric_key="operating_cash_flow",
                    roles=(
                        AgentRole.CASH_FLOW_RISK,
                        AgentRole.MANAGEMENT_INTENT,
                        AgentRole.BULL,
                        AgentRole.BEAR,
                        AgentRole.JUDGE,
                    ),
                    requirement=MetricRequirement.REQUIRED,
                    source_policy=MetricSourcePolicy.CANONICAL,
                    preferred_sources=("sec_company_facts",),
                    period_role=period_role,
                    cap_if_missing=True,
                    sec_tags=("NetCashProvidedByUsedInOperatingActivities",),
                    description=f"{period_text} operating cash flow.",
                ),
                ExpectedMetricSpec(
                    metric_key="capex",
                    roles=(
                        AgentRole.CASH_FLOW_RISK,
                        AgentRole.MANAGEMENT_INTENT,
                        AgentRole.BULL,
                        AgentRole.BEAR,
                        AgentRole.JUDGE,
                    ),
                    requirement=MetricRequirement.REQUIRED,
                    source_policy=MetricSourcePolicy.CANONICAL,
                    preferred_sources=("sec_company_facts",),
                    period_role=period_role,
                    cap_if_missing=True,
                    sec_tags=(
                        "PaymentsToAcquirePropertyPlantAndEquipment",
                        "PaymentsToAcquireProductiveAssets",
                    ),
                    description=f"{period_text} capital expenditures, normalized as an outflow.",
                ),
                ExpectedMetricSpec(
                    metric_key="free_cash_flow",
                    roles=(
                        AgentRole.CASH_FLOW_RISK,
                        AgentRole.MANAGEMENT_INTENT,
                        AgentRole.BULL,
                        AgentRole.BEAR,
                        AgentRole.JUDGE,
                    ),
                    requirement=MetricRequirement.REQUIRED,
                    source_policy=MetricSourcePolicy.DERIVED,
                    preferred_sources=("derived_from_operating_cash_flow_and_capex",),
                    period_role=period_role,
                    cap_if_missing=True,
                    source_type=SourceType.DERIVED_METRIC,
                    description=f"{period_text} FCF derived as OCF minus absolute CapEx.",
                ),
            ]
        )
    return tuple(specs)


EXPECTED_METRICS: tuple[ExpectedMetricSpec, ...] = (
    *_required_canonical_metrics(),
    ExpectedMetricSpec(
        metric_key="revenue_consensus",
        roles=(AgentRole.EARNINGS_QUALITY, AgentRole.GUIDANCE),
        requirement=MetricRequirement.OPTIONAL,
        source_policy=MetricSourcePolicy.CONSENSUS,
        preferred_sources=("yfinance",),
        period_role=MetricPeriodRole.CONSENSUS,
        description="Consensus revenue estimate when available.",
    ),
    ExpectedMetricSpec(
        metric_key="eps_consensus",
        roles=(AgentRole.EARNINGS_QUALITY, AgentRole.GUIDANCE),
        requirement=MetricRequirement.OPTIONAL,
        source_policy=MetricSourcePolicy.CONSENSUS,
        preferred_sources=("yfinance",),
        period_role=MetricPeriodRole.CONSENSUS,
        description="Consensus EPS estimate when available.",
    ),
    ExpectedMetricSpec(
        metric_key="operating_margin_pct",
        roles=(AgentRole.EARNINGS_QUALITY, AgentRole.MANAGEMENT_INTENT),
        requirement=MetricRequirement.OPTIONAL,
        source_policy=MetricSourcePolicy.CANONICAL,
        preferred_sources=("yfinance", "sec_company_facts"),
        period_role=MetricPeriodRole.ACTUAL,
        description="Operating margin if precomputed.",
    ),
    ExpectedMetricSpec(
        metric_key="presentation_metric_candidates",
        roles=(
            AgentRole.EARNINGS_QUALITY,
            AgentRole.CASH_FLOW_RISK,
            AgentRole.MANAGEMENT_INTENT,
            AgentRole.GUIDANCE,
        ),
        requirement=MetricRequirement.REFERENCE_ONLY,
        source_policy=MetricSourcePolicy.PRESENTATION_REFERENCE,
        preferred_sources=("earnings_presentation",),
        period_role=MetricPeriodRole.AUDIT_ONLY,
        source_type=SourceType.EARNINGS_PRESENTATION,
        description=(
            "Presentation numeric candidates are auxiliary only and must not be "
            "canonical or confidence-cap inputs."
        ),
    ),
    ExpectedMetricSpec(
        metric_key="transcript_metrics",
        roles=(AgentRole.MANAGEMENT_INTENT, AgentRole.GUIDANCE),
        requirement=MetricRequirement.NOT_IN_CONTRACT,
        source_policy=MetricSourcePolicy.DOCUMENT_TEXT,
        preferred_sources=("earnings_call",),
        period_role=MetricPeriodRole.AUDIT_ONLY,
        source_type=SourceType.EARNINGS_CALL,
        description="Transcript metrics are not part of the current canonical input contract.",
    ),
)


def expected_metric_specs(role: AgentRole | None = None) -> tuple[ExpectedMetricSpec, ...]:
    if role is None:
        return EXPECTED_METRICS
    return tuple(spec for spec in EXPECTED_METRICS if role in spec.roles)


def expected_metric_context(role: AgentRole) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {
        requirement.value: [] for requirement in MetricRequirement
    }
    for spec in expected_metric_specs(role):
        grouped[spec.requirement.value].append(spec.for_context())
    return {"role": role.value, **grouped}


def canonical_metric_availability(metrics: FinancialMetrics) -> list[AvailabilityItem]:
    items: list[AvailabilityItem] = []
    seen: set[tuple[str, MetricPeriodRole]] = set()
    for spec in EXPECTED_METRICS:
        spec_key = (spec.metric_key, spec.period_role)
        if (
            spec_key in seen
            or spec.requirement is not MetricRequirement.REQUIRED
            or spec.source_policy is MetricSourcePolicy.PRESENTATION_REFERENCE
            or not spec.cap_if_missing
        ):
            continue
        seen.add(spec_key)
        availability_key = _availability_key(spec)
        if not _canonical_metric_is_available(metrics, spec):
            items.append(
                AvailabilityItem(
                    key=availability_key,
                    status=AvailabilityStatus.REQUIRED_MISSING,
                    reason=(
                        f"Required canonical metric {availability_key} was not available "
                        "from accepted SEC/yfinance/derived source refs."
                    ),
                    source_type=spec.source_type,
                    blocks_verdict=False,
                )
            )
        else:
            items.append(
                AvailabilityItem(
                    key=availability_key,
                    status=AvailabilityStatus.AVAILABLE,
                    reason=f"Required canonical metric {availability_key} is available.",
                    source_type=spec.source_type,
                )
            )
    return items


def _canonical_metric_is_available(metrics: FinancialMetrics, spec: ExpectedMetricSpec) -> bool:
    if not _metric_value_present(metrics, spec):
        return False
    if spec.source_policy is MetricSourcePolicy.DERIVED:
        return _has_accepted_derived_metric(metrics, spec)
    return _has_accepted_source_ref(metrics, spec)


def _availability_key(spec: ExpectedMetricSpec) -> str:
    if spec.period_role is MetricPeriodRole.ACTUAL:
        return spec.metric_key
    return f"{spec.period_role.value}:{spec.metric_key}"


def _metric_value_present(metrics: FinancialMetrics, spec: ExpectedMetricSpec) -> bool:
    if spec.source_policy is MetricSourcePolicy.DERIVED:
        if any(
            metric.metric_name == spec.metric_key
            and metric.period_role == spec.period_role
            and metric.fiscal_period == metrics.fiscal_period
            for metric in metrics.derived_metrics
        ):
            return True
        return (
            spec.period_role is MetricPeriodRole.ACTUAL
            and getattr(metrics, spec.metric_key, None) is not None
        )
    if any(
        metric.metric_name == spec.metric_key
        and metric.period_role == spec.period_role
        and metric.fiscal_period == metrics.fiscal_period
        for metric in metrics.canonical_metrics
    ):
        return True
    return (
        spec.period_role is MetricPeriodRole.ACTUAL
        and getattr(metrics, spec.metric_key, None) is not None
    )


def _has_accepted_source_ref(metrics: FinancialMetrics, spec: ExpectedMetricSpec) -> bool:
    for metric in metrics.canonical_metrics:
        if (
            metric.metric_name != spec.metric_key
            or metric.period_role != spec.period_role
            or metric.fiscal_period != metrics.fiscal_period
        ):
            continue
        if _source_ref_satisfies(metric.source_ref, spec, metrics.fiscal_period):
            return True
    return any(
        ref.metric_name == spec.metric_key
        and _source_ref_satisfies(ref, spec, metrics.fiscal_period)
        for ref in metrics.source_refs
    )


def _has_accepted_derived_metric(metrics: FinancialMetrics, spec: ExpectedMetricSpec) -> bool:
    component_specs = {
        component.metric_key: component
        for component in EXPECTED_METRICS
        if component.metric_key in {"operating_cash_flow", "capex"}
        and component.requirement is MetricRequirement.REQUIRED
        and component.period_role is spec.period_role
    }
    for metric in metrics.derived_metrics:
        if (
            metric.metric_name != spec.metric_key
            or metric.period_role != spec.period_role
            or metric.fiscal_period != metrics.fiscal_period
        ):
            continue
        if metric.source_ref.source_type is not SourceType.DERIVED_METRIC:
            continue
        if metric.source_ref.reported_period != metrics.fiscal_period:
            continue
        component_refs = {ref.metric_name: ref for ref in metric.component_source_refs}
        if all(
            component_key in component_refs
            and _source_ref_satisfies(
                component_refs[component_key],
                component_spec,
                metrics.fiscal_period,
            )
            for component_key, component_spec in component_specs.items()
        ):
            return True
    source_refs_by_metric = {
        (ref.metric_name, ref.period_role): ref
        for ref in metrics.source_refs
        if ref.metric_name and ref.period_role
    }
    derived_ref = source_refs_by_metric.get((spec.metric_key, spec.period_role))
    if derived_ref is None or derived_ref.source_type is not SourceType.DERIVED_METRIC:
        return False
    if derived_ref.period_role is not spec.period_role:
        return False
    if derived_ref.reported_period != metrics.fiscal_period:
        return False
    return all(
        (component_key, spec.period_role) in source_refs_by_metric
        and _source_ref_satisfies(
            source_refs_by_metric[(component_key, spec.period_role)],
            component_spec,
            metrics.fiscal_period,
        )
        for component_key, component_spec in component_specs.items()
    )


def _source_ref_satisfies(ref: Any, spec: ExpectedMetricSpec, fiscal_period: str) -> bool:
    if ref.source_type is not spec.source_type:
        return False
    if ref.period_role is not spec.period_role:
        return False
    if ref.reported_period != fiscal_period:
        return False
    provider = ref.provider
    if spec.preferred_sources and provider not in spec.preferred_sources:
        return False
    return True


def with_canonical_metric_availability(metrics: FinancialMetrics) -> FinancialMetrics:
    canonical_items = canonical_metric_availability(metrics)
    canonical_keys = {item.key for item in canonical_items}
    provider_items = [
        item
        for item in metrics.availability
        if item.key not in canonical_keys or item.status is AvailabilityStatus.CONFLICTING
    ]
    return metrics.model_copy(update={"availability": [*provider_items, *canonical_items]})


def canonical_metric_period_context(metrics: FinancialMetrics) -> dict[str, dict[str, Any]]:
    """Return a compact agent-readable view of required canonical metrics by period."""

    availability_by_key = {item.key: item for item in canonical_metric_availability(metrics)}
    metric_by_key = {
        (metric.metric_name, metric.period_role): metric
        for metric in [*metrics.canonical_metrics, *metrics.derived_metrics]
        if metric.metric_name in REQUIRED_CANONICAL_METRIC_KEYS
        and metric.period_role in REQUIRED_CANONICAL_PERIOD_ROLES
    }
    refs_by_key = {
        (ref.metric_name, ref.period_role): ref
        for ref in metrics.source_refs
        if ref.metric_name in REQUIRED_CANONICAL_METRIC_KEYS
        and ref.period_role in REQUIRED_CANONICAL_PERIOD_ROLES
    }

    grouped: dict[str, dict[str, Any]] = {}
    for period_role in REQUIRED_CANONICAL_PERIOD_ROLES:
        role_values: dict[str, Any] = {}
        for metric_key in REQUIRED_CANONICAL_METRIC_KEYS:
            spec = _required_spec(metric_key, period_role)
            if spec is None:
                continue
            availability_key = _availability_key(spec)
            availability = availability_by_key.get(availability_key)
            metric = metric_by_key.get((metric_key, period_role))
            source_ref = (
                metric.source_ref
                if metric is not None
                else refs_by_key.get((metric_key, period_role))
            )
            role_values[metric_key] = _metric_period_entry(
                metric=metric,
                source_ref=source_ref,
                availability=availability,
                availability_key=availability_key,
            )
        grouped[period_role.value] = role_values
    return grouped


def _required_spec(
    metric_key: str,
    period_role: MetricPeriodRole,
) -> ExpectedMetricSpec | None:
    return next(
        (
            spec
            for spec in EXPECTED_METRICS
            if spec.metric_key == metric_key
            and spec.period_role is period_role
            and spec.requirement is MetricRequirement.REQUIRED
        ),
        None,
    )


def _metric_period_entry(
    *,
    metric: MetricValue | None,
    source_ref: SourceRef | None,
    availability: AvailabilityItem | None,
    availability_key: str,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "availability_key": availability_key,
        "status": (
            availability.status.value
            if availability is not None
            else AvailabilityStatus.REQUIRED_MISSING.value
        ),
    }
    if availability is not None:
        entry["reason"] = availability.reason
    if metric is not None:
        entry.update(
            {
                "metric_id": metric.metric_id,
                "value": metric.value,
                "unit": metric.unit,
            }
        )
    if source_ref is not None:
        entry["source_ref"] = _compact_source_ref(source_ref)
    return entry


def _compact_source_ref(source_ref: SourceRef) -> dict[str, Any]:
    return {
        key: value
        for key, value in source_ref.model_dump(mode="json", exclude_none=True).items()
        if key
        in {
            "source_id",
            "source_type",
            "metric_name",
            "reported_period",
            "as_of_date",
            "provider",
            "provider_row_date",
            "provider_column_date",
            "period_role",
        }
    }
