"""Deterministic context routing for normalized earnings-review requests.

The router intentionally uses an approximate token counter instead of a provider
tokenizer.  The estimate serializes routed context as stable compact JSON and
rounds ``character_count / 4`` up to the next integer.  This is conservative
enough for pre-invocation budget gates and remains deterministic in tests.
"""

from __future__ import annotations

import json
from math import ceil
from typing import Any, Mapping

from pydantic import BaseModel, Field

from src.expected_metrics import canonical_metric_period_context, expected_metric_context
from src.workflow_models import (
    AgentRole,
    ContextBudget,
    DocumentSection,
    NormalizedReviewRequest,
    SourceManifestEntry,
    SourceRef,
    SourceType,
    WorkflowModel,
    source_refs_from_financial_metrics,
    validate_source_ref_registered_and_consistent,
)

APPROX_TOKEN_COUNTER_NAME = "approx_json_chars_div_4_v1"


ROLE_CONTEXT_KEYS: dict[AgentRole, tuple[str, ...]] = {
    AgentRole.EARNINGS_QUALITY: (
        "run_spec",
        "expected_metrics",
        "earnings_quality_metrics",
        "earnings_quality_sections",
        "source_index",
        "analysis_config",
    ),
    AgentRole.CASH_FLOW_RISK: (
        "run_spec",
        "expected_metrics",
        "cash_flow_risk_metrics",
        "cash_flow_risk_sections",
        "cash_conversion_inputs",
        "source_index",
        "analysis_config",
    ),
    AgentRole.MANAGEMENT_INTENT: (
        "run_spec",
        "expected_metrics",
        "financial_snapshot_minimal",
        "management_sections",
        "management_intent_sections",
        "strategy_sections",
        "mdna_sections",
        "risk_sections",
        "source_index",
        "analysis_config",
    ),
    AgentRole.GUIDANCE: (
        "run_spec",
        "expected_metrics",
        "guidance_metrics",
        "guidance_consensus_deltas",
        "consensus_deltas",
        "guidance_sections",
        "guidance_assumptions_sections",
        "prior_guidance_track_record",
        "management_intent_handoff",
        "source_index",
        "analysis_config",
    ),
    AgentRole.BULL: (
        "run_spec",
        "expected_metrics",
        "financial_snapshot_summary",
        "analysis_brief",
        "earnings_quality_finding",
        "cash_flow_risk_finding",
        "management_intent_finding",
        "guidance_finding",
        "positive_evidence_pool",
        "negative_evidence_pool",
        "disputed_points",
        "missing_data",
    ),
    AgentRole.BEAR: (
        "run_spec",
        "expected_metrics",
        "financial_snapshot_summary",
        "analysis_brief",
        "earnings_quality_finding",
        "cash_flow_risk_finding",
        "management_intent_finding",
        "guidance_finding",
        "bull_case_summary",
        "positive_evidence_pool",
        "negative_evidence_pool",
        "disputed_points",
        "missing_data",
    ),
    AgentRole.JUDGE: (
        "run_spec",
        "expected_metrics",
        "financial_snapshot_summary",
        "analysis_brief",
        "bull_case",
        "bear_case",
    ),
}

PRESENTATION_TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "actuals": ("actual", "actuals", "reported", "results", "delivered"),
    "pnl": ("eps", "earnings", "gross margin", "operating income", "profitability"),
    "cash_flow": (
        "cash flow",
        "free cash flow",
        "operating cash flow",
        "fcf",
        "capex",
        "capital expenditure",
    ),
    "balance_sheet": (
        "balance sheet",
        "cash and equivalents",
        "debt",
        "liquidity",
        "working capital",
    ),
    "segment": ("segment", "segments"),
    "guidance": ("guidance", "guided", "guide", "forecast", "target"),
    "outlook": ("outlook", "next quarter", "full year", "fiscal year", "expect"),
    "assumptions": ("assume", "assumes", "assuming", "assumption", "assumptions"),
    "management": ("management", "ceo", "cfo", "leadership", "executive"),
    "strategy": ("strategy", "strategic", "roadmap", "priority", "priorities"),
    "demand": ("demand", "pipeline", "backlog", "customer", "adoption"),
    "supply": ("supply", "inventory", "capacity", "constraints", "lead time"),
    "capital_allocation": (
        "capital allocation",
        "buyback",
        "repurchase",
        "dividend",
        "shareholder return",
    ),
    "risk": ("risk", "risks", "headwind", "pressure", "challenge", "uncertainty"),
    "gaap_non_gaap_reconciliation": ("gaap", "non-gaap", "non gaap", "reconciliation"),
    "one_time_items": ("one-time", "one time", "nonrecurring", "impairment", "restructuring"),
}

TAG_ROUTING_TOPICS: dict[str, tuple[str, ...]] = {
    "actuals": ("actuals",),
    "pnl": ("pnl",),
    "cash_flow": ("cash_flow",),
    "balance_sheet": ("balance_sheet",),
    "segment": ("segments",),
    "guidance": ("guidance",),
    "outlook": ("guidance",),
    "assumptions": ("guidance",),
    "management": ("management",),
    "strategy": ("strategy",),
    "demand": ("management",),
    "supply": ("management",),
    "capital_allocation": ("capital_allocation",),
    "risk": ("risk",),
    "gaap_non_gaap_reconciliation": ("gaap_non_gaap_reconciliation",),
    "one_time_items": ("one_time_items",),
}


class ContextRouterError(ValueError):
    """Base error for deterministic context routing failures."""


class ContextSourceScopeError(ContextRouterError):
    """Raised when routed context references a source outside the manifest."""


class ContextBudgetExceeded(ContextRouterError):
    """Raised when routed context does not fit the request context budget."""

    def __init__(self, report: "ContextBudgetReport"):
        self.report = report
        failed_roles = ", ".join(failure.role.value for failure in report.failures)
        super().__init__(f"context budget exceeded for role(s): {failed_roles}")


class RoutedRoleContext(WorkflowModel):
    role: AgentRole
    context: dict[str, Any]
    context_keys: list[str]
    routed_source_ids: list[str]
    estimated_input_tokens: int = Field(ge=1)


class RoleBudgetEstimate(WorkflowModel):
    role: AgentRole
    context_keys: list[str]
    estimated_input_tokens: int = Field(ge=1)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    max_total_tokens: int = Field(gt=0)
    estimated_total_tokens: int = Field(gt=0)
    within_budget: bool
    failure_reasons: list[str] = Field(default_factory=list)


class ContextBudgetReport(WorkflowModel):
    token_counter: str
    estimates: list[RoleBudgetEstimate]
    failures: list[RoleBudgetEstimate]
    within_budget: bool


class RoutedContextBundle(WorkflowModel):
    request_id: str
    ticker: str
    fiscal_period: str
    by_role: dict[AgentRole, RoutedRoleContext]
    budget_report: ContextBudgetReport


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def approximate_token_count(value: Any) -> int:
    """Return the deterministic approximate input-token count used by the router."""

    stable_json = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return max(1, ceil(len(stable_json) / 4))


class ContextRouter:
    """Build source-scoped role contexts from normalized review input."""

    def route(self, request: NormalizedReviewRequest) -> RoutedContextBundle:
        role_contexts = self._build_role_contexts(request)
        budget_report = self._build_budget_report(role_contexts, request.context_budget)
        if not budget_report.within_budget:
            raise ContextBudgetExceeded(budget_report)

        return RoutedContextBundle(
            request_id=request.request_id,
            ticker=request.ticker,
            fiscal_period=request.fiscal_period,
            by_role=role_contexts,
            budget_report=budget_report,
        )

    def check_budget(self, request: NormalizedReviewRequest) -> ContextBudgetReport:
        """Return the deterministic budget report without invoking any provider."""

        role_contexts = self._build_role_contexts(request)
        return self._build_budget_report(role_contexts, request.context_budget)

    def _build_role_contexts(
        self,
        request: NormalizedReviewRequest,
    ) -> dict[AgentRole, RoutedRoleContext]:
        self._validate_source_scope(request)

        sections_by_topic = self._sections_by_topic(request.document_sections)
        metrics_json = request.financial_metrics.model_dump(mode="json", exclude_none=True)
        canonical_periods = canonical_metric_period_context(request.financial_metrics)
        financial_source_ids = [
            source_ref.source_id
            for source_ref in source_refs_from_financial_metrics(request.financial_metrics)
        ]
        earnings_quality_topics = {
            "actuals",
            "pnl",
            "eps",
            "revenue",
            "segments",
            "gaap_non_gaap_reconciliation",
            "one_time_items",
            "other",
        }
        cash_flow_risk_topics = {
            "cash_flow",
            "balance_sheet",
            "capital_allocation",
            "risk",
            "other",
        }
        management_intent_topics = {
            "management",
            "strategy",
            "capital_allocation",
            "segments",
            "guidance",
        }
        guidance_topics = {"guidance"}

        earnings_quality_sections = self._sections_for_topics(
            sections_by_topic,
            earnings_quality_topics,
        )
        cash_flow_risk_sections = self._sections_for_topics(
            sections_by_topic,
            cash_flow_risk_topics,
        )
        management_sections = self._sections_for_topics(
            sections_by_topic,
            {"management", "guidance", "segments"},
        )
        management_intent_sections = self._sections_for_topics(
            sections_by_topic,
            management_intent_topics | {"other"},
        )
        strategy_sections = self._sections_for_topics(
            sections_by_topic,
            {"strategy", "management", "capital_allocation", "segments", "other"},
        )
        guidance_sections = self._sections_for_topics(sections_by_topic, guidance_topics)
        guidance_assumptions_sections = self._sections_for_topics(
            sections_by_topic,
            {"guidance"},
        )
        guidance_inputs = self._guidance_inputs(
            request,
            metrics_json,
            canonical_periods,
            guidance_sections,
            guidance_assumptions_sections,
        )
        guidance_deltas = guidance_inputs["guidance_deltas"]

        raw_contexts: dict[AgentRole, tuple[dict[str, Any], list[str]]] = {
            AgentRole.EARNINGS_QUALITY: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.EARNINGS_QUALITY),
                    "earnings_quality_metrics": metrics_json,
                    "earnings_quality_sections": earnings_quality_sections,
                    "analysis_config": self._analysis_config(),
                },
                [
                    *financial_source_ids,
                    *self._source_ids_for_topics(
                        request.document_sections,
                        earnings_quality_topics,
                    ),
                ],
            ),
            AgentRole.CASH_FLOW_RISK: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.CASH_FLOW_RISK),
                    "cash_flow_risk_metrics": metrics_json,
                    "cash_flow_risk_sections": cash_flow_risk_sections,
                    "cash_conversion_inputs": metrics_json,
                    "analysis_config": self._analysis_config(),
                },
                [
                    *financial_source_ids,
                    *self._source_ids_for_topics(
                        request.document_sections,
                        cash_flow_risk_topics,
                    ),
                ],
            ),
            AgentRole.MANAGEMENT_INTENT: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.MANAGEMENT_INTENT),
                    "financial_snapshot_minimal": self._minimal_snapshot(
                        metrics_json,
                        canonical_periods,
                    ),
                    "management_sections": management_sections,
                    "management_intent_sections": management_intent_sections,
                    "strategy_sections": strategy_sections,
                    "mdna_sections": sections_by_topic["other"],
                    "risk_sections": sections_by_topic["risk"],
                    "analysis_config": self._analysis_config(),
                },
                [
                    *financial_source_ids,
                    *self._source_ids_for_topics(
                        request.document_sections,
                        management_intent_topics | {"other", "risk"},
                    ),
                ],
            ),
            AgentRole.GUIDANCE: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.GUIDANCE),
                    "guidance_metrics": guidance_inputs,
                    "guidance_consensus_deltas": guidance_deltas,
                    "consensus_deltas": guidance_deltas,
                    "guidance_sections": guidance_sections,
                    "guidance_assumptions_sections": guidance_assumptions_sections,
                    "prior_guidance_track_record": [],
                    "management_intent_handoff": None,
                    "analysis_config": self._analysis_config(),
                },
                [
                    *financial_source_ids,
                    *self._source_ids_for_topics(
                        request.document_sections,
                        guidance_topics,
                    ),
                ],
            ),
            AgentRole.BULL: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.BULL),
                    "financial_snapshot_summary": self._minimal_snapshot(
                        metrics_json,
                        canonical_periods,
                    ),
                },
                [],
            ),
            AgentRole.BEAR: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.BEAR),
                    "financial_snapshot_summary": self._minimal_snapshot(
                        metrics_json,
                        canonical_periods,
                    ),
                },
                [],
            ),
            AgentRole.JUDGE: (
                {
                    "run_spec": self._run_spec(request),
                    "expected_metrics": expected_metric_context(AgentRole.JUDGE),
                    "financial_snapshot_summary": self._minimal_snapshot(
                        metrics_json,
                        canonical_periods,
                    ),
                },
                [],
            ),
        }

        return {
            role: self._finalize_role_context(
                role,
                raw_context,
                routed_source_ids,
                request.source_manifest,
            )
            for role, (raw_context, routed_source_ids) in raw_contexts.items()
        }

    def _finalize_role_context(
        self,
        role: AgentRole,
        raw_context: Mapping[str, Any],
        routed_source_ids: list[str],
        source_manifest: list[SourceManifestEntry],
    ) -> RoutedRoleContext:
        allowed_keys = ROLE_CONTEXT_KEYS[role]
        context = {
            key: raw_context[key]
            for key in allowed_keys
            if key in raw_context and raw_context[key] is not None
        }

        source_ids = self._dedupe_in_manifest_order(routed_source_ids, source_manifest)
        if not source_ids and "source_index" in allowed_keys:
            source_ids = [source.source_id for source in source_manifest]
        if source_ids and "source_index" in allowed_keys:
            context["source_index"] = self._source_index(source_ids, source_manifest)

        context_keys = sorted(context)
        return RoutedRoleContext(
            role=role,
            context=context,
            context_keys=context_keys,
            routed_source_ids=source_ids if "source_index" in context else [],
            estimated_input_tokens=approximate_token_count(context),
        )

    def _validate_source_scope(self, request: NormalizedReviewRequest) -> None:
        registered_ids = {source.source_id for source in request.source_manifest}
        if len(registered_ids) != len(request.source_manifest):
            raise ContextSourceScopeError("source_manifest.source_id values must be unique")

        for section in request.document_sections:
            self._validate_source_ref(
                section.source_ref,
                request.source_manifest,
                "document_sections",
            )

        for source_ref in source_refs_from_financial_metrics(request.financial_metrics):
            self._validate_source_ref(
                source_ref,
                request.source_manifest,
                "financial_metrics.source_refs",
            )

    def _validate_source_ref(
        self,
        source_ref: SourceRef,
        source_manifest: list[SourceManifestEntry],
        context: str,
    ) -> None:
        try:
            validate_source_ref_registered_and_consistent(
                source_ref,
                source_manifest,
                context,
            )
        except ValueError as exc:
            raise ContextSourceScopeError(str(exc)) from exc

    def _source_index(
        self,
        source_ids: list[str],
        source_manifest: list[SourceManifestEntry],
    ) -> list[dict[str, Any]]:
        manifest_by_id = {source.source_id: source for source in source_manifest}
        source_index: list[dict[str, Any]] = []
        for source_id in source_ids:
            source = manifest_by_id.get(source_id)
            if source is None:
                raise ContextSourceScopeError(f"unregistered routed source_id: {source_id}")
            source_index.append(source.model_dump(mode="json", exclude_none=True))
        return source_index

    def _dedupe_in_manifest_order(
        self,
        source_ids: list[str],
        source_manifest: list[SourceManifestEntry],
    ) -> list[str]:
        requested = set(source_ids)
        manifest_ordered = [
            source.source_id for source in source_manifest if source.source_id in requested
        ]
        missing = sorted(requested.difference(manifest_ordered))
        if missing:
            raise ContextSourceScopeError(f"unregistered routed source_id: {missing[0]}")
        return manifest_ordered

    def _build_budget_report(
        self,
        role_contexts: Mapping[AgentRole, RoutedRoleContext],
        budget: ContextBudget,
    ) -> ContextBudgetReport:
        estimates: list[RoleBudgetEstimate] = []
        for role_context in role_contexts.values():
            estimated_total = role_context.estimated_input_tokens + budget.max_output_tokens
            failure_reasons: list[str] = []
            if role_context.estimated_input_tokens > budget.max_input_tokens:
                failure_reasons.append("estimated_input_tokens exceeds max_input_tokens")
            if estimated_total > budget.max_total_tokens:
                failure_reasons.append(
                    "estimated_input_tokens plus max_output_tokens exceeds max_total_tokens"
                )

            estimates.append(
                RoleBudgetEstimate(
                    role=role_context.role,
                    context_keys=role_context.context_keys,
                    estimated_input_tokens=role_context.estimated_input_tokens,
                    max_input_tokens=budget.max_input_tokens,
                    max_output_tokens=budget.max_output_tokens,
                    max_total_tokens=budget.max_total_tokens,
                    estimated_total_tokens=estimated_total,
                    within_budget=not failure_reasons,
                    failure_reasons=failure_reasons,
                )
            )

        failures = [estimate for estimate in estimates if not estimate.within_budget]
        return ContextBudgetReport(
            token_counter=APPROX_TOKEN_COUNTER_NAME,
            estimates=estimates,
            failures=failures,
            within_budget=not failures,
        )

    def _run_spec(self, request: NormalizedReviewRequest) -> dict[str, Any]:
        return {
            "schema_version": request.schema_version,
            "request_id": request.request_id,
            "ticker": request.ticker,
            "fiscal_period": request.fiscal_period,
            "purpose": request.purpose,
            "is_investment_advice": request.is_investment_advice,
        }

    def _analysis_config(self) -> dict[str, Any]:
        return {
            "max_retry": 1,
            "not_investment_advice": True,
        }

    def _minimal_snapshot(
        self,
        metrics_json: Mapping[str, Any],
        canonical_periods: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = {
            key: metrics_json.get(key)
            for key in (
                "ticker",
                "fiscal_period",
                "revenue",
                "revenue_surprise_pct",
                "eps",
                "eps_surprise_pct",
                "operating_margin_pct",
                "operating_cash_flow",
                "free_cash_flow",
                "capex",
                "guidance",
            )
            if key in metrics_json
        }
        if canonical_periods is not None:
            snapshot["canonical_metric_periods"] = canonical_periods
        return snapshot

    def _guidance_inputs(
        self,
        request: NormalizedReviewRequest,
        metrics_json: Mapping[str, Any],
        canonical_periods: Mapping[str, Any],
        guidance_sections: list[dict[str, Any]],
        guidance_assumptions_sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        company_guidance = []
        if metrics_json.get("guidance"):
            company_guidance.append(
                {
                    "metric_name": "guidance_text",
                    "text": metrics_json["guidance"],
                    "reported_period": request.fiscal_period,
                }
            )

        consensus_estimates = []
        for metric_name in ("revenue", "eps"):
            consensus_key = f"{metric_name}_consensus"
            if metrics_json.get(consensus_key) is not None:
                consensus_estimates.append(
                    {
                        "metric_name": metric_name,
                        "value": metrics_json[consensus_key],
                        "reported_period": request.fiscal_period,
                    }
                )

        availability: list[dict[str, str]] = []
        if not company_guidance:
            availability.append(
                {
                    "item": "company_guidance",
                    "status": "company_guidance_missing",
                    "reason": "No company guidance text is available in routed inputs.",
                }
            )
        elif not consensus_estimates:
            availability.append(
                {
                    "item": "guidance_deltas",
                    "status": "consensus_missing",
                    "reason": "No consensus estimate is available for guidance comparison.",
                }
            )
        else:
            availability.append(
                {
                    "item": "guidance_deltas",
                    "status": "company_guidance_metric_missing",
                    "reason": (
                        "No explicit company guidance metric is available for consensus comparison."
                    ),
                }
            )

        return {
            "company_guidance": company_guidance,
            "consensus_estimates": consensus_estimates,
            "guidance_deltas": [],
            "canonical_metric_periods": canonical_periods,
            "presentation_sections": [
                section
                for section in guidance_sections
                if section.get("source_ref", {}).get("source_type")
                == SourceType.EARNINGS_PRESENTATION.value
            ],
            "sec_sections": [
                section
                for section in guidance_assumptions_sections
                if section.get("source_ref", {}).get("source_type") == SourceType.FILING.value
            ],
            "availability": availability,
        }

    def _sections_for_topics(
        self,
        sections_by_topic: Mapping[str, list[dict[str, Any]]],
        topics: set[str],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for topic in sorted(topics):
            for section in sections_by_topic.get(topic, []):
                source_id = section.get("source_ref", {}).get("source_id", "")
                section_id = section.get("section_id", "")
                key = (str(source_id), str(section_id))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(section)
        return merged

    def _sections_by_topic(
        self,
        sections: list[DocumentSection],
    ) -> dict[str, list[dict[str, Any]]]:
        topic_names = (
            "actuals",
            "pnl",
            "cash_flow",
            "balance_sheet",
            "eps",
            "revenue",
            "guidance",
            "segments",
            "management",
            "strategy",
            "capital_allocation",
            "risk",
            "gaap_non_gaap_reconciliation",
            "one_time_items",
            "other",
        )
        grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in topic_names}
        for section in sections:
            payload = self._section_payload(section)
            for topic in self._routing_topics(section):
                grouped[topic].append(payload)
        return grouped

    def _source_ids_for_topics(
        self,
        sections: list[DocumentSection],
        topics: set[str],
    ) -> list[str]:
        return [
            section.source_ref.source_id
            for section in sections
            if set(self._routing_topics(section)) & topics
        ]

    def _section_payload(self, section: DocumentSection) -> dict[str, Any]:
        payload = section.model_dump(mode="json", exclude_none=True)
        tags = self._presentation_tags(section)
        if tags:
            payload["presentation_tags"] = tags
        return payload

    def _routing_topics(self, section: DocumentSection) -> tuple[str, ...]:
        tags = self._presentation_tags(section)
        if not tags:
            return (self._fallback_topic(section),)

        topics: list[str] = []
        for tag in tags:
            for topic in TAG_ROUTING_TOPICS.get(tag, ()):
                if topic not in topics:
                    topics.append(topic)
        return tuple(topics or (self._fallback_topic(section),))

    def _presentation_tags(self, section: DocumentSection) -> list[str]:
        if section.source_ref.source_type != SourceType.EARNINGS_PRESENTATION:
            return []

        body_tags = self._keyword_tags(section.text)
        if body_tags:
            return body_tags
        return self._keyword_tags(f"{section.section_id} {section.heading}")

    def _keyword_tags(self, text: str) -> list[str]:
        lowered = text.lower()
        return [
            tag
            for tag, keywords in PRESENTATION_TAG_KEYWORDS.items()
            if any(keyword in lowered for keyword in keywords)
        ]

    def _fallback_topic(self, section: DocumentSection) -> str:
        label = f"{section.section_id} {section.heading}".lower()
        if "eps" in label or "earnings" in label:
            return "eps"
        if "guidance" in label or "outlook" in label:
            return "guidance"
        if "segment" in label:
            return "segments"
        if "risk" in label:
            return "risk"
        if "revenue" in label or "sales" in label:
            return "revenue"
        return "other"
