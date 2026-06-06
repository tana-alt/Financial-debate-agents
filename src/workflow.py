"""API-first earnings review workflow.

The API calls this module; the CLI should only be a thin client around the API.
The workflow itself is fixed and explicit:

Data ingestion/normalization -> financial agents -> presentation agents ->
evidence aggregation -> debate agents -> judge -> Markdown renderer.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from .context_router import ContextRouter
from .expected_metrics import canonical_metric_availability, with_canonical_metric_availability
from .llm import LLMProvider
from .report_quality_guidance import validate_guidance_required
from .report_quality_missing_data import apply_confidence_caps
from .report_quality_numeric_grounding import validate_numeric_grounding
from .report_renderer import ReportRenderer
from .workflow_agents import (
    CashFlowRiskAnalyst,
    EarningsQualityAnalyst,
    GuidanceAnalyst,
    ManagementIntentAnalyst,
)
from .workflow_models import (
    AgentRole,
    AnalysisBrief,
    AvailabilityItem,
    AvailabilityStatus,
    ClaimRecord,
    ClaimType,
    DebateResult,
    DecisionUse,
    DocumentSection,
    EvidenceItem,
    EvidencePolarity,
    FinancialMetrics,
    JudgeDecision,
    JudgeTreatment,
    MissingDataItem,
    NormalizedReviewRequest,
    ReportMatrix,
    ReviewRequest,
    ReviewResponse,
    SourceManifestEntry,
    SourceRef,
    SourceType,
    StepState,
    StepStatus,
    VerdictLabel,
    WorkflowStep,
    source_refs_from_financial_metrics,
)
from .workflow_runtime import AgentRuntime, DebateRunner, JudgeRunner
from .workflow_validation import WorkflowValidationError, WorkflowValidationGate


def _fetch_consensus(ticker: str, quarter: str, **kwargs):
    from .preprocessor import fetch_financial_metrics

    return fetch_financial_metrics(ticker, quarter, **kwargs)


def _fetch_filing_html(url: str) -> str:
    from .preprocessor import fetch_filing_html

    return fetch_filing_html(url)


def _segment_filing(html: str, url: str | None = None):
    from .preprocessor import segment_filing

    return segment_filing(html, url=url)


def _document_files_to_sections(document_files):
    from .preprocessor import document_files_to_sections

    return document_files_to_sections(document_files)


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


def _merge_source_manifest(
    source_manifest: list[SourceManifestEntry],
    source_refs: list[SourceRef],
) -> list[SourceManifestEntry]:
    by_id = {source.source_id: source for source in source_manifest}
    for source_ref in source_refs:
        by_id.setdefault(source_ref.source_id, _source_manifest_entry_from_ref(source_ref))
    return list(by_id.values())


class MarkdownRenderer:
    """Deterministic Markdown rendering from validated structured results."""

    def render(
        self,
        *,
        request: ReviewRequest,
        brief: AnalysisBrief,
        debate: DebateResult,
        decision: JudgeDecision,
    ) -> str:
        matrix = self.build_report_matrix(
            request=request,
            brief=brief,
            debate=debate,
            decision=decision,
        )
        return ReportRenderer().render(
            request=request,
            brief=brief,
            debate=debate,
            decision=decision,
            matrix=matrix,
        )

    def build_report_matrix(
        self,
        *,
        request: ReviewRequest,
        brief: AnalysisBrief,
        debate: DebateResult,
        decision: JudgeDecision,
    ) -> ReportMatrix:
        evidence_items = self._matrix_evidence_items(brief, debate, decision)
        return ReportMatrix(
            source_manifest=self._source_manifest(request, evidence_items),
            evidence_items=evidence_items,
            claim_records=self._claim_records(
                evidence_items,
                decision,
                request.fiscal_period,
            ),
            decision_uses=self._decision_uses(evidence_items, decision),
            missing_data_items=self._missing_data_items(brief),
            data_quality_flags=self._data_quality_flags(request),
        )

    def _matrix_evidence_items(
        self,
        brief: AnalysisBrief,
        debate: DebateResult,
        decision: JudgeDecision,
    ) -> list[EvidenceItem]:
        items: list[EvidenceItem] = [
            *brief.positive_evidence_pool,
            *brief.negative_evidence_pool,
            *brief.risk_evidence_pool,
            *debate.strongest_positive_evidence,
            *debate.strongest_negative_evidence,
            *decision.positive_evidence,
            *decision.negative_evidence,
        ]
        for finding in (
            brief.earnings_quality_finding,
            brief.cash_flow_risk_finding,
            brief.management_intent_finding,
            brief.guidance_finding,
        ):
            items.extend(finding.key_evidence)
            items.extend(finding.counter_evidence)

        by_id: dict[str, EvidenceItem] = {}
        for item in items:
            by_id.setdefault(item.evidence_id, item)
        return list(by_id.values())

    def _source_manifest(
        self,
        request: ReviewRequest,
        evidence_items: list[EvidenceItem],
    ) -> list[SourceManifestEntry]:
        metric_source_refs = (
            source_refs_from_financial_metrics(request.financial_metrics)
            if request.financial_metrics is not None
            else []
        )
        if request.source_manifest:
            return _merge_source_manifest(
                list(request.source_manifest),
                metric_source_refs,
            )

        by_id: dict[str, SourceManifestEntry] = {}
        for ref in [*(item.source_ref for item in evidence_items), *metric_source_refs]:
            by_id.setdefault(
                ref.source_id,
                _source_manifest_entry_from_ref(ref),
            )
        return list(by_id.values())

    def _claim_records(
        self,
        evidence_items: list[EvidenceItem],
        decision: JudgeDecision,
        fiscal_period: str,
    ) -> list[ClaimRecord]:
        return [
            ClaimRecord(
                claim_id=self._claim_id(item),
                claim_type=ClaimType.FACT,
                time_scope=self._evidence_time_scope(item, fiscal_period),
                claim=item.summary,
                evidence_ids=[item.evidence_id],
                interpretation=item.detail,
                implication=self._evidence_implication(item, decision),
                confidence=item.confidence,
            )
            for item in evidence_items
        ]

    def _decision_uses(
        self,
        evidence_items: list[EvidenceItem],
        decision: JudgeDecision,
    ) -> list[DecisionUse]:
        decision_evidence_ids = {
            item.evidence_id: item.polarity
            for item in [*decision.positive_evidence, *decision.negative_evidence]
        }
        uses: list[DecisionUse] = []
        for item in evidence_items:
            polarity = decision_evidence_ids.get(item.evidence_id)
            if polarity == EvidencePolarity.POSITIVE:
                treatment = JudgeTreatment.SUPPORTING
                rationale = decision.rationale
            elif polarity in {EvidencePolarity.NEGATIVE, EvidencePolarity.RISK}:
                treatment = JudgeTreatment.COUNTER_EVIDENCE
                rationale = decision.rationale
            else:
                treatment = JudgeTreatment.NOT_USED
                rationale = (
                    "Evidence was retained in the matrix but not explicitly used by the judge."
                )
            uses.append(
                DecisionUse(
                    decision_use_id=self._safe_id(f"decision:{item.evidence_id}"),
                    treatment=treatment,
                    claim_id=self._claim_id(item),
                    decisive_evidence_ids=([item.evidence_id] if polarity is not None else []),
                    rationale=rationale,
                    verdict_impact=polarity or item.polarity,
                    confidence_impact=0.0,
                )
            )
        return uses

    def _missing_data_items(self, brief: AnalysisBrief) -> list[MissingDataItem]:
        return []

    def _data_quality_flags(self, request: ReviewRequest) -> list[AvailabilityItem]:
        metrics = request.financial_metrics
        profile = metrics.input_profile if metrics is not None else request.input_profile
        items = [
            AvailabilityItem(
                key="input_profile",
                status=AvailabilityStatus.AVAILABLE,
                reason=f"Input profile: {profile.value}",
            )
        ]
        if metrics is not None:
            items.extend(metrics.availability)

        period_verified = bool(request.target_earnings_date or request.target_period_end_date)
        items.append(
            AvailabilityItem(
                key="period_verification",
                status=(
                    AvailabilityStatus.AVAILABLE
                    if period_verified
                    else AvailabilityStatus.PERIOD_UNVERIFIED
                ),
                reason=(
                    "Period verification: verified"
                    if period_verified
                    else "Period verification: unverified"
                ),
                source_type=SourceType.FINANCIAL_API,
            )
        )
        return items

    def confidence_cap_items(self, request: ReviewRequest) -> list[MissingDataItem]:
        metrics = request.financial_metrics
        flags = canonical_metric_availability(metrics) if metrics is not None else []
        items: list[MissingDataItem] = []
        for flag in flags:
            if flag.status in {AvailabilityStatus.AVAILABLE, AvailabilityStatus.COMPUTED}:
                continue
            items.append(
                MissingDataItem(
                    missing_data_id=self._safe_id(f"cap:{flag.key}"),
                    topic=flag.key,
                    reason=flag.reason,
                    materiality="high" if flag.blocks_verdict else "medium",
                    requested_source_type=flag.source_type,
                    status=flag.status,
                    blocks_verdict=flag.blocks_verdict,
                )
            )
        return items

    def _claim_id(self, item: EvidenceItem) -> str:
        return self._safe_id(f"claim:{item.evidence_id}")

    def _safe_id(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-")
        return (normalized or "item")[:100]

    def _evidence_time_scope(self, item: EvidenceItem, fiscal_period: str) -> str:
        return str(
            item.reported_period
            or item.as_of_date
            or item.source_ref.reported_period
            or item.source_ref.as_of_date
            or fiscal_period
        )

    def _evidence_implication(self, item: EvidenceItem, decision: JudgeDecision) -> str:
        if item.polarity == EvidencePolarity.POSITIVE:
            return decision.eps_outlook_reason
        if item.polarity in {EvidencePolarity.NEGATIVE, EvidencePolarity.RISK}:
            return decision.fcf_outlook_reason
        return decision.rationale


class ReviewWorkflow:
    """Synchronous API workflow runner."""

    financial_agent_classes = (
        EarningsQualityAnalyst,
        CashFlowRiskAnalyst,
    )
    presentation_agent_classes = (ManagementIntentAnalyst, GuidanceAnalyst)

    def __init__(
        self,
        llm: LLMProvider,
        renderer: MarkdownRenderer | None = None,
        validator: WorkflowValidationGate | None = None,
        agent_runtime: AgentRuntime | None = None,
        debate_runner: DebateRunner | None = None,
        judge_runner: JudgeRunner | None = None,
    ):
        self.llm = llm
        self.renderer = renderer or MarkdownRenderer()
        self.validator = validator or WorkflowValidationGate()
        self.agent_runtime = agent_runtime or AgentRuntime(llm)
        self.debate_runner = debate_runner or DebateRunner(llm, self.validator)
        self.judge_runner = judge_runner or JudgeRunner(llm, self.validator)

    def run(self, request: ReviewRequest) -> ReviewResponse:
        steps: list[StepStatus] = []

        metrics, sections = self._record_step(
            steps,
            WorkflowStep.DATA_INGESTION,
            lambda: self._ingest(request),
        )
        runtime_request = self._runtime_request(request, metrics)
        context = self._build_agent_context(runtime_request, metrics, sections)

        financial_findings = self._record_step(
            steps,
            WorkflowStep.FINANCIAL_AGENTS,
            lambda: self.agent_runtime.run_parallel(self.financial_agent_classes, context),
        )
        self.validator.validate_no_investment_advice_text(financial_findings, "financial_findings")
        presentation_findings = self._record_step(
            steps,
            WorkflowStep.PRESENTATION_AGENTS,
            lambda: self.agent_runtime.run_parallel(self.presentation_agent_classes, context),
        )
        self.validator.validate_no_investment_advice_text(
            presentation_findings, "presentation_findings"
        )

        brief = self._record_step(
            steps,
            WorkflowStep.EVIDENCE_AGGREGATION,
            lambda: self.validator.aggregate_evidence(
                runtime_request,
                metrics,
                sections,
                financial_findings,
                presentation_findings,
            ),
        )

        bull_case, bear_case, debate = self._record_step(
            steps,
            WorkflowStep.DEBATE,
            lambda: self.debate_runner.run(runtime_request, metrics, brief),
        )

        decision = self._record_step(
            steps,
            WorkflowStep.JUDGE,
            lambda: self.judge_runner.run(runtime_request, metrics, brief, bull_case, bear_case),
        )
        decision = self.validator.validate_judge_decision(decision, brief)
        decision = apply_confidence_caps(
            decision,
            brief,
            missing_data_items=self.renderer.confidence_cap_items(runtime_request),
        )
        validate_numeric_grounding([*decision.positive_evidence, *decision.negative_evidence])

        markdown = self._record_step(
            steps,
            WorkflowStep.MARKDOWN_RENDERER,
            lambda: (
                self.renderer.render(
                    request=runtime_request,
                    brief=brief,
                    debate=debate,
                    decision=decision,
                )
                if runtime_request.include_markdown
                else "Markdown rendering was disabled for this request."
            ),
        )
        self.validator.validate_no_investment_advice_text(markdown, "markdown_report")

        return ReviewResponse(
            request_id=runtime_request.request_id,
            ticker=runtime_request.ticker,
            fiscal_period=runtime_request.fiscal_period,
            steps=steps,
            financial_metrics=metrics,
            analysis_brief=brief,
            bull_case=bull_case,
            bear_case=bear_case,
            debate_result=debate,
            judge_decision=decision,
            markdown_report=markdown,
        )

    def _record_step(self, steps: list[StepStatus], step: WorkflowStep, fn):
        started_at = datetime.now(timezone.utc)
        try:
            result = fn()
        except Exception as exc:
            steps.append(
                StepStatus(
                    step=step,
                    state=StepState.FAILED,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                    error=self._step_error_message(exc),
                )
            )
            raise
        steps.append(
            StepStatus(
                step=step,
                state=StepState.COMPLETED,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
        )
        return result

    def _step_error_message(self, exc: Exception) -> str:
        message = str(exc)
        if len(message) <= 1000:
            return message
        return message[:997] + "..."

    def _ingest(self, request: ReviewRequest) -> tuple[FinancialMetrics, list[DocumentSection]]:
        metrics = self._normalize_metrics(
            request.financial_metrics or self._fetch_financial_metrics(request)
        )
        sections = list(request.document_sections)
        if request.document_files:
            sections.extend(_document_files_to_sections(request.document_files))

        if request.use_sec and request.filing_url is not None:
            filing_url = str(request.filing_url)
            html = _fetch_filing_html(filing_url)
            sections.extend(_segment_filing(html, url=filing_url))

        if not sections:
            raise WorkflowValidationError(
                "document_sections, document_files, or filing_url is required"
            )

        validate_guidance_required(metrics, sections)

        return metrics, sections

    def _runtime_request(self, request: ReviewRequest, metrics: FinancialMetrics) -> ReviewRequest:
        source_manifest = list(request.source_manifest)
        if source_manifest:
            source_manifest = _merge_source_manifest(
                source_manifest,
                source_refs_from_financial_metrics(metrics),
            )
        return request.model_copy(
            update={
                "financial_metrics": metrics,
                "source_manifest": source_manifest,
            },
        )

    def _normalize_metrics(self, metrics: FinancialMetrics) -> FinancialMetrics:
        payload = metrics.model_dump(exclude_none=True)
        if "eps_surprise_pct" not in payload:
            surprise = self._calculate_surprise_pct(metrics.eps, metrics.eps_consensus)
            if surprise is not None:
                payload["eps_surprise_pct"] = surprise
        if "revenue_surprise_pct" not in payload:
            surprise = self._calculate_surprise_pct(metrics.revenue, metrics.revenue_consensus)
            if surprise is not None:
                payload["revenue_surprise_pct"] = surprise
        if "free_cash_flow" not in payload:
            if metrics.operating_cash_flow is not None and metrics.capex is not None:
                payload["free_cash_flow"] = metrics.operating_cash_flow - abs(metrics.capex)
        normalized = FinancialMetrics.model_validate(payload)
        return with_canonical_metric_availability(self._with_inferred_metric_values(normalized))

    def _with_inferred_metric_values(self, metrics: FinancialMetrics) -> FinancialMetrics:
        from .preprocessor import build_financial_metrics

        inferred = build_financial_metrics(
            ticker=metrics.ticker,
            fiscal_period=metrics.fiscal_period,
            target_earnings_date=metrics.target_earnings_date,
            target_period_end_date=metrics.target_period_end_date,
            prior_fiscal_period=metrics.prior_fiscal_period,
            input_profile=metrics.input_profile,
            eps=metrics.eps,
            eps_consensus=metrics.eps_consensus,
            eps_surprise_pct=metrics.eps_surprise_pct,
            revenue=metrics.revenue,
            revenue_consensus=metrics.revenue_consensus,
            revenue_surprise_pct=metrics.revenue_surprise_pct,
            operating_margin_pct=metrics.operating_margin_pct,
            operating_cash_flow=metrics.operating_cash_flow,
            free_cash_flow=metrics.free_cash_flow,
            capex=metrics.capex,
            guidance=metrics.guidance,
            source_refs=self._metric_value_source_refs(metrics),
            availability=list(metrics.availability),
            segment_metrics=list(metrics.segment_metrics),
            unmapped_metrics=list(metrics.unmapped_metrics),
        )
        return inferred.model_copy(
            update={
                "currency": metrics.currency,
                "guidance_metrics": metrics.guidance_metrics,
                "guidance_deltas": metrics.guidance_deltas,
                "presentation_metric_candidates": metrics.presentation_metric_candidates,
                "metric_conflicts": metrics.metric_conflicts,
            },
        )

    def _metric_value_source_refs(self, metrics: FinancialMetrics) -> list[SourceRef]:
        refs: list[SourceRef] = []
        seen: set[str] = set()

        def append(source_ref: SourceRef) -> None:
            if source_ref.source_id in seen:
                return
            seen.add(source_ref.source_id)
            refs.append(source_ref)

        for metric in metrics.canonical_metrics:
            append(metric.source_ref)
        for metric in metrics.derived_metrics:
            append(metric.source_ref)
            for component_ref in metric.component_source_refs:
                append(component_ref)
        for source_ref in metrics.source_refs:
            append(source_ref)
        return refs

    def _calculate_surprise_pct(
        self,
        actual: float | None,
        consensus: float | None,
    ) -> float | None:
        if actual is None or consensus is None or consensus == 0:
            return None
        return ((actual - consensus) / abs(consensus)) * 100

    def _fetch_financial_metrics(self, request: ReviewRequest) -> FinancialMetrics:
        return _fetch_consensus(
            request.ticker,
            request.fiscal_period,
            target_earnings_date=request.target_earnings_date,
            target_period_end_date=request.target_period_end_date,
            prior_fiscal_period=request.prior_fiscal_period,
            input_profile=request.input_profile,
            use_sec=request.use_sec,
        )

    def _build_agent_context(
        self,
        request: ReviewRequest,
        metrics: FinancialMetrics,
        sections: list[DocumentSection],
    ) -> dict[str, Any] | Mapping[AgentRole, dict[str, Any]]:
        routed_contexts = self._build_routed_agent_contexts(request, metrics, sections)
        if routed_contexts is not None:
            return routed_contexts

        run_spec = {
            "ticker": request.ticker,
            "fiscal_period": request.fiscal_period,
            "purpose": request.purpose,
            "is_investment_advice": request.is_investment_advice,
        }
        source_index = [
            *[section.source_ref for section in sections],
            *source_refs_from_financial_metrics(metrics),
        ]
        by_topic = self._sections_by_topic(sections)
        metrics_json = metrics.model_dump(mode="json", exclude_none=True)
        minimal_snapshot = {
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
        }

        return {
            "run_spec": run_spec,
            "source_index": source_index,
            "analysis_config": {
                "max_retry": 1,
                "verdict_labels": [label.value for label in VerdictLabel],
                "not_investment_advice": True,
            },
            "financial_snapshot_summary": minimal_snapshot,
            "financial_snapshot_minimal": minimal_snapshot,
            "earnings_quality_metrics": metrics_json,
            "cash_flow_risk_metrics": metrics_json,
            "cash_conversion_inputs": metrics_json,
            "guidance_metrics": self._guidance_inputs(metrics_json, by_topic["guidance"]),
            "guidance_consensus_deltas": [],
            "consensus_deltas": [],
            "earnings_quality_sections": (
                by_topic["actuals"]
                + by_topic["pnl"]
                + by_topic["eps"]
                + by_topic["revenue"]
                + by_topic["segments"]
                + by_topic["gaap_non_gaap_reconciliation"]
                + by_topic["one_time_items"]
                + by_topic["other"]
            ),
            "cash_flow_risk_sections": (
                by_topic["other"]
                + by_topic["risk"]
                + by_topic["cash_flow"]
                + by_topic["balance_sheet"]
                + by_topic["capital_allocation"]
            ),
            "risk_sections": by_topic["risk"],
            "management_sections": (
                by_topic["management"]
                + by_topic["strategy"]
                + by_topic["guidance"]
                + by_topic["segments"]
            ),
            "management_intent_sections": by_topic["management"]
            + by_topic["strategy"]
            + by_topic["capital_allocation"]
            + by_topic["guidance"]
            + by_topic["segments"]
            + by_topic["other"],
            "strategy_sections": (
                by_topic["strategy"]
                + by_topic["management"]
                + by_topic["capital_allocation"]
                + by_topic["segments"]
                + by_topic["other"]
            ),
            "mdna_sections": by_topic["other"],
            "guidance_sections": by_topic["guidance"],
            "guidance_assumptions_sections": by_topic["guidance"],
            "prior_guidance_track_record": [],
            "management_intent_handoff": None,
        }

    def _build_routed_agent_contexts(
        self,
        request: ReviewRequest,
        metrics: FinancialMetrics,
        sections: list[DocumentSection],
    ) -> Mapping[AgentRole, dict[str, Any]] | None:
        if not request.source_manifest or request.context_budget is None:
            return None

        normalized_request = NormalizedReviewRequest(
            schema_version="runtime-review-request.v1",
            request_id=request.request_id or f"{request.ticker}:{request.fiscal_period}:runtime",
            ticker=request.ticker,
            fiscal_period=request.fiscal_period,
            target_earnings_date=request.target_earnings_date,
            target_period_end_date=request.target_period_end_date,
            prior_fiscal_period=request.prior_fiscal_period,
            input_profile=request.input_profile,
            financial_metrics=metrics,
            document_sections=sections,
            source_manifest=request.source_manifest,
            context_budget=request.context_budget,
            include_markdown=request.include_markdown,
            purpose=request.purpose,
            is_investment_advice=request.is_investment_advice,
            dry_run=False,
        )
        routed = ContextRouter().route(normalized_request)
        return {
            role: role_context.context
            for role, role_context in routed.by_role.items()
            if role
            in {
                AgentRole.EARNINGS_QUALITY,
                AgentRole.CASH_FLOW_RISK,
                AgentRole.MANAGEMENT_INTENT,
                AgentRole.GUIDANCE,
            }
        }

    def _guidance_inputs(
        self,
        metrics_json: Mapping[str, Any],
        guidance_sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        company_guidance = []
        if metrics_json.get("guidance"):
            company_guidance.append(
                {
                    "metric_name": "guidance_text",
                    "text": metrics_json["guidance"],
                    "reported_period": metrics_json.get("fiscal_period"),
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
                        "reported_period": metrics_json.get("fiscal_period"),
                    }
                )

        return {
            "company_guidance": company_guidance,
            "consensus_estimates": consensus_estimates,
            "guidance_deltas": [],
            "presentation_sections": guidance_sections,
            "sec_sections": [],
            "availability": metrics_json.get("availability", []),
        }

    def _sections_by_topic(
        self,
        sections: list[DocumentSection],
    ) -> dict[str, list[dict[str, Any]]]:
        return ContextRouter()._sections_by_topic(sections)

    def _infer_topic(self, section: DocumentSection) -> str:
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
