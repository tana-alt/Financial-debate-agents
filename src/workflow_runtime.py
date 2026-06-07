"""Agent execution runtime for the earnings review workflow."""

from __future__ import annotations

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

from pydantic import BaseModel

from .expected_metrics import canonical_metric_period_context, expected_metric_context
from .llm import LLMProvider
from .runtime_config import env_int
from .workflow_agents import BearAgent, BullAgent, JudgeAgent
from .workflow_models import (
    AgentExecutionTrace,
    AgentRole,
    AnalysisBrief,
    AvailabilityItem,
    BearCase,
    BullCase,
    DebateResult,
    EvidenceItem,
    EvidencePolarity,
    FinancialMetrics,
    JudgeDecision,
    ReviewRequest,
)
from .workflow_validation import WorkflowValidationError, WorkflowValidationGate

AGENT_ROLE_BY_PUBLIC_ROLE: dict[str, AgentRole] = {
    "EarningsQualityAnalyst": AgentRole.EARNINGS_QUALITY,
    "CashFlowRiskAnalyst": AgentRole.CASH_FLOW_RISK,
    "ManagementIntentAnalyst": AgentRole.MANAGEMENT_INTENT,
    "GuidanceAnalyst": AgentRole.GUIDANCE,
    "BullAgent": AgentRole.BULL,
    "BearAgent": AgentRole.BEAR,
    "JudgeAgent": AgentRole.JUDGE,
}


class AgentRuntime:
    """Run independent specialist agents against a shared routed context."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run_parallel(
        self,
        agent_classes: tuple[type, ...],
        context: dict[str, Any] | Mapping[AgentRole, dict[str, Any]],
        *,
        trace_sink: list[AgentExecutionTrace] | None = None,
    ):
        with ThreadPoolExecutor(max_workers=_agent_max_workers(len(agent_classes))) as executor:
            futures = [
                executor.submit(
                    agent_class(self.llm, trace_sink=trace_sink).run,
                    self._context_for(agent_class, context),
                )
                for agent_class in agent_classes
            ]
            return [future.result() for future in futures]

    def _context_for(
        self,
        agent_class: type,
        context: dict[str, Any] | Mapping[AgentRole, dict[str, Any]],
    ) -> dict[str, Any]:
        public_role = str(getattr(getattr(agent_class, "spec", None), "public_role", ""))
        role = AGENT_ROLE_BY_PUBLIC_ROLE.get(public_role)
        if self._is_role_context_map(context):
            if role is None:
                raise KeyError(f"unsupported routed agent role: {public_role}")
            return context[role]
        flat_context = cast(dict[str, Any], context)
        if role is None or "expected_metrics" in flat_context:
            return flat_context
        return {**flat_context, "expected_metrics": expected_metric_context(role)}

    def _is_role_context_map(
        self,
        context: dict[str, Any] | Mapping[AgentRole, dict[str, Any]],
    ) -> bool:
        return bool(context) and all(isinstance(key, AgentRole) for key in context)


class DebateRunner:
    """Run Bull/Bear agents and validate their evidence selections."""

    def __init__(self, llm: LLMProvider, validator: WorkflowValidationGate):
        self.llm = llm
        self.validator = validator

    def run(
        self,
        request: ReviewRequest,
        metrics: FinancialMetrics,
        brief: AnalysisBrief,
        *,
        trace_sink: list[AgentExecutionTrace] | None = None,
    ) -> tuple[BaseModel, BaseModel, DebateResult, list[AvailabilityItem]]:
        metrics_json = metrics.model_dump(mode="json", exclude_none=True)
        metrics_json["canonical_metric_periods"] = canonical_metric_period_context(metrics)
        context = {
            "run_spec": {"ticker": request.ticker, "fiscal_period": request.fiscal_period},
            "financial_snapshot_summary": metrics_json,
            "analysis_brief": brief,
            "earnings_quality_finding": brief.earnings_quality_finding,
            "cash_flow_risk_finding": brief.cash_flow_risk_finding,
            "management_intent_finding": brief.management_intent_finding,
            "guidance_finding": brief.guidance_finding,
            "positive_evidence_pool": brief.positive_evidence_pool,
            "negative_evidence_pool": brief.negative_evidence_pool,
            "valid_positive_evidence_ids": [
                item.evidence_id for item in brief.positive_evidence_pool
            ],
            "valid_negative_evidence_ids": [
                item.evidence_id for item in brief.negative_evidence_pool
            ],
            "disputed_points": brief.risk_evidence_pool,
            "missing_data": [],
        }
        positive_by_id = {item.evidence_id: item for item in brief.positive_evidence_pool}
        negative_by_id = {item.evidence_id: item for item in brief.negative_evidence_pool}

        bull_case, positive, bull_quality_warnings = self._run_case(
            BullAgent,
            context,
            "strongest_positive_evidence",
            positive_by_id,
            "bull_case",
            EvidencePolarity.POSITIVE,
            trace_sink=trace_sink,
        )
        bear_context = {
            **context,
            "bull_case_summary": {
                "thesis": self.validator.text_attr(bull_case, "thesis")
                or self.validator.text_attr(bull_case, "summary"),
                "weak_points": self.validator.list_attr(bull_case, "weak_points"),
                "finding_coverage": getattr(bull_case, "finding_coverage", {}),
            },
        }
        bear_case, negative, bear_quality_warnings = self._run_case(
            BearAgent,
            bear_context,
            "strongest_negative_evidence",
            negative_by_id,
            "bear_case",
            EvidencePolarity.NEGATIVE,
            trace_sink=trace_sink,
        )

        debate = DebateResult(
            bull_case=(self.validator.text_attr(bull_case, "thesis") or "Bull case was generated.")[
                :2000
            ],
            bear_case=(self.validator.text_attr(bear_case, "thesis") or "Bear case was generated.")[
                :2000
            ],
            risk_case="; ".join(item.summary for item in negative[:3])
            or "No unresolved risks were identified.",
            evaluation="Bull and Bear cases were generated from validated AnalysisBrief only.",
            strongest_positive_evidence=positive[:10],
            strongest_negative_evidence=negative[:10],
            unresolved_questions=self.validator.list_attr(bear_case, "unresolved_risks")[:8],
        )
        return (
            bull_case,
            bear_case,
            debate,
            [
                *bull_quality_warnings,
                *bear_quality_warnings,
            ],
        )

    def _run_case(
        self,
        agent_class: Any,
        context: dict[str, Any],
        evidence_field: str,
        evidence_by_id: dict[str, EvidenceItem],
        case_name: str,
        expected_polarity: EvidencePolarity,
        *,
        trace_sink: list[AgentExecutionTrace] | None = None,
    ) -> tuple[BaseModel, list[EvidenceItem], list[AvailabilityItem]]:
        evidence_ids_field = (
            f"{evidence_field}_ids"
            if f"{evidence_field}_ids" in agent_class.spec.output_model.model_fields
            else evidence_field
        )
        last_error: WorkflowValidationError | None = None
        for _ in range(_debate_selection_attempts()):
            run_context = context
            if last_error is not None:
                run_context = {
                    **context,
                    "evidence_validation_error": str(last_error),
                    "valid_evidence_ids": sorted(evidence_by_id),
                }
            selection = agent_class(self.llm, trace_sink=trace_sink).run(run_context)
            case = selection
            self.validator.validate_finding_coverage(case, case_name)
            quality_warnings = self.validator.investment_advice_warnings(case, case_name)
            if quality_warnings:
                case = self.validator.sanitize_investment_advice_text(case)
            try:
                if evidence_ids_field != evidence_field:
                    evidence_ids = getattr(case, evidence_ids_field)
                    evidence = self.validator.validated_evidence_ids(
                        evidence_ids,
                        evidence_by_id,
                        f"{case_name}.{evidence_ids_field}",
                    )
                else:
                    evidence = self.validator.validated_case_evidence(
                        case,
                        evidence_field,
                        evidence_by_id,
                        case_name,
                        expected_polarity,
                    )
            except WorkflowValidationError as exc:
                last_error = exc
                continue
            public_case = self._public_case(
                case,
                case_name,
                evidence_field,
                evidence_ids_field,
                evidence,
            )
            return public_case, evidence, quality_warnings
        assert last_error is not None
        raise last_error

    def _public_case(
        self,
        selection: BaseModel,
        case_name: str,
        evidence_field: str,
        evidence_ids_field: str,
        evidence: list[EvidenceItem],
    ) -> BaseModel:
        if evidence_ids_field == evidence_field:
            return selection.model_copy(update={evidence_field: evidence})
        payload = selection.model_dump(mode="json", exclude={evidence_ids_field})
        payload[evidence_field] = evidence
        if case_name == "bull_case":
            return BullCase.model_validate(payload)
        if case_name == "bear_case":
            return BearCase.model_validate(payload)
        raise WorkflowValidationError(f"unsupported debate case bridge: {case_name}")


class JudgeRunner:
    """Run the judge agent and normalize the structured verdict contract."""

    def __init__(self, llm: LLMProvider, validator: WorkflowValidationGate):
        self.llm = llm
        self.validator = validator

    def run(
        self,
        request: ReviewRequest,
        metrics: FinancialMetrics,
        brief: AnalysisBrief,
        bull_case: BaseModel,
        bear_case: BaseModel,
        *,
        trace_sink: list[AgentExecutionTrace] | None = None,
    ) -> tuple[JudgeDecision, list[AvailabilityItem]]:
        positive_by_id = {item.evidence_id: item for item in brief.positive_evidence_pool}
        negative_by_id = {item.evidence_id: item for item in brief.negative_evidence_pool}
        base_context = {
            "run_spec": {"ticker": request.ticker, "fiscal_period": request.fiscal_period},
            "financial_snapshot_summary": {
                **metrics.model_dump(mode="json", exclude_none=True),
                "canonical_metric_periods": canonical_metric_period_context(metrics),
            },
            "analysis_brief": brief,
            "bull_case": bull_case,
            "bear_case": bear_case,
            "positive_evidence_pool": brief.positive_evidence_pool,
            "negative_evidence_pool": brief.negative_evidence_pool,
            "valid_positive_evidence_ids": [
                item.evidence_id for item in brief.positive_evidence_pool
            ],
            "valid_negative_evidence_ids": [
                item.evidence_id for item in brief.negative_evidence_pool
            ],
        }
        last_error: WorkflowValidationError | None = None
        for _ in range(_judge_selection_attempts()):
            run_context = base_context
            if last_error is not None:
                run_context = {
                    **base_context,
                    "evidence_validation_error": str(last_error),
                }
            selection = JudgeAgent(self.llm, trace_sink=trace_sink).run(run_context)
            try:
                positive = self.validator.validated_evidence_ids(
                    getattr(selection, "positive_evidence_ids"),
                    positive_by_id,
                    "judge_decision.positive_evidence_ids",
                )
                negative = self.validator.validated_evidence_ids(
                    getattr(selection, "negative_evidence_ids"),
                    negative_by_id,
                    "judge_decision.negative_evidence_ids",
                )
            except WorkflowValidationError as exc:
                last_error = exc
                continue
            decision = JudgeDecision.model_validate(
                selection.model_dump(
                    mode="json",
                    exclude={"positive_evidence_ids", "negative_evidence_ids"},
                )
                | {
                    "positive_evidence": positive,
                    "negative_evidence": negative,
                }
            )
            break
        else:
            assert last_error is not None
            raise last_error
        quality_warnings = self.validator.investment_advice_warnings(decision, "judge_decision")
        if quality_warnings:
            decision = self.validator.sanitize_investment_advice_text(decision)
        return decision, quality_warnings


def _agent_max_workers(default: int) -> int:
    return env_int("EARNINGS_DEBATE_AGENT_MAX_WORKERS", default, min_value=1)


def _debate_selection_attempts() -> int:
    return env_int("EARNINGS_DEBATE_DEBATE_SELECTION_ATTEMPTS", 2, min_value=1)


def _judge_selection_attempts() -> int:
    return env_int("EARNINGS_DEBATE_JUDGE_SELECTION_ATTEMPTS", 2, min_value=1)
