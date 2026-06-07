"""API-first workflow agent wrappers.

This module owns the LLM call boundary for the earnings-review workflow:
agents receive a small routed context, call ``LLMProvider.complete()``, and
return Pydantic-validated JSON objects.

``src.workflow_models`` is the canonical contract module.  This wrapper keeps a
small compatibility bridge for Plan/active models that may not have landed in
``workflow_models`` yet, but runtime agent specs always point at strict
workflow contracts rather than permissive ad-hoc fallback models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, Mapping, NoReturn

from pydantic import BaseModel, field_validator

from . import workflow_models as _workflow_models
from .expected_metrics import expected_metric_context
from .llm import LLMProvider
from .prompt_loader import build_system_prompt, resolve_skill_target
from .runtime_config import env_float, env_int
from .structured import StructuredOutputError, parse_model
from .workflow_errors import WorkflowErrorCategory


class WorkflowAgentError(RuntimeError):
    """Base exception for workflow agent failures."""

    def __init__(
        self,
        message: str,
        *,
        category: WorkflowErrorCategory | None = None,
        error_kind: str | None = None,
        field: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.error_kind = error_kind
        self.field = field
        self.retryable = retryable


class AgentOutputValidationError(WorkflowAgentError):
    """Raised when the LLM output cannot be parsed into the output contract."""

    def __init__(
        self,
        message: str,
        *,
        category: WorkflowErrorCategory = WorkflowErrorCategory.LLM_OUTPUT_SCHEMA,
        error_kind: str = "schema_mismatch",
        field: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(
            message,
            category=category,
            error_kind=error_kind,
            field=field,
            retryable=retryable,
        )


class AgentRoleMismatch(AgentOutputValidationError):
    """Raised when validated JSON belongs to a different agent role."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            message,
            category=WorkflowErrorCategory.AGENT_ROLE,
            error_kind="role_mismatch",
            field=field,
            retryable=retryable,
        )


REQUIRED_FINDING_COVERAGE_KEYS = {
    "earnings_quality",
    "cash_flow_risk",
    "management_intent",
    "guidance",
}

DEFAULT_AGENT_MAX_TOKENS = 8192
DEBATE_AGENT_MAX_TOKENS = 8192
JUDGE_AGENT_MAX_TOKENS = 12_000
DEFAULT_AGENT_TEMPERATURE = 0.2
JUDGE_AGENT_TEMPERATURE = 0.1
DEFAULT_AGENT_MAX_RETRIES = 1

EXPECTED_METRIC_ROLE_BY_PUBLIC_ROLE: dict[str, _workflow_models.AgentRole] = {
    "EarningsQualityAnalyst": _workflow_models.AgentRole.EARNINGS_QUALITY,
    "CashFlowRiskAnalyst": _workflow_models.AgentRole.CASH_FLOW_RISK,
    "ManagementIntentAnalyst": _workflow_models.AgentRole.MANAGEMENT_INTENT,
    "GuidanceAnalyst": _workflow_models.AgentRole.GUIDANCE,
    "BullAgent": _workflow_models.AgentRole.BULL,
    "BearAgent": _workflow_models.AgentRole.BEAR,
    "JudgeAgent": _workflow_models.AgentRole.JUDGE,
}


class _PlanFinding(_workflow_models.AgentFinding):
    """Strict bridge for Plan/active specialist contracts.

    The nested Plan objects are intentionally typed as JSON dictionaries here
    because ``workflow_models`` owns the final canonical shape.  This still
    forbids extra top-level fields and keeps the role-specific required fields
    visible in the output schema.
    """


class _BridgeEarningsQualityFinding(_PlanFinding):
    agent_name: Literal["EarningsQualityAnalyst"] = "EarningsQualityAnalyst"
    eps_surprise_assessment: dict[str, Any]
    quality_of_earnings: dict[str, Any]
    revenue_quality: dict[str, Any]
    margin_trend: dict[str, Any]
    operating_leverage: dict[str, Any]
    segment_mix_effect: dict[str, Any]
    eps_outlook_signal: dict[str, Any]
    fcf_implication: dict[str, Any]


class _BridgeCashFlowRiskFinding(_PlanFinding):
    agent_name: Literal["CashFlowRiskAnalyst"] = "CashFlowRiskAnalyst"
    fcf_trend_assessment: dict[str, Any]
    cash_conversion_assessment: dict[str, Any]
    capex_assessment: dict[str, Any]
    working_capital_effect: dict[str, Any]
    liquidity_assessment: dict[str, Any]
    leverage_or_financing_risk: dict[str, Any]
    fcf_outlook_signal: dict[str, Any]
    eps_constraint: dict[str, Any]


class _BridgeBullCase(_workflow_models.BullCase):
    finding_coverage: _workflow_models.FindingCoverageMap

    @field_validator("finding_coverage")
    @classmethod
    def require_all_specialist_findings(
        cls, value: _workflow_models.FindingCoverageMap
    ) -> _workflow_models.FindingCoverageMap:
        missing = REQUIRED_FINDING_COVERAGE_KEYS.difference(value)
        if missing:
            raise ValueError("finding_coverage missing keys: " + ", ".join(sorted(missing)))
        return value


class _BridgeBearCase(_workflow_models.BearCase):
    finding_coverage: _workflow_models.FindingCoverageMap

    @field_validator("finding_coverage")
    @classmethod
    def require_all_specialist_findings(
        cls, value: _workflow_models.FindingCoverageMap
    ) -> _workflow_models.FindingCoverageMap:
        missing = REQUIRED_FINDING_COVERAGE_KEYS.difference(value)
        if missing:
            raise ValueError("finding_coverage missing keys: " + ", ".join(sorted(missing)))
        return value


EarningsQualityFinding = getattr(
    _workflow_models, "EarningsQualityFinding", _BridgeEarningsQualityFinding
)
CashFlowRiskFinding = getattr(_workflow_models, "CashFlowRiskFinding", _BridgeCashFlowRiskFinding)
ManagementIntentFinding = getattr(_workflow_models, "ManagementIntentFinding")
GuidanceFinding = getattr(_workflow_models, "GuidanceFinding")

_WorkflowBullCase = getattr(_workflow_models, "BullCase")
_WorkflowBearCase = getattr(_workflow_models, "BearCase")
BullCase = (
    _WorkflowBullCase if "finding_coverage" in _WorkflowBullCase.model_fields else _BridgeBullCase
)
BearCase = (
    _WorkflowBearCase if "finding_coverage" in _WorkflowBearCase.model_fields else _BridgeBearCase
)
FinalVerdict = getattr(_workflow_models, "FinalVerdict", _workflow_models.JudgeDecision)
JudgeDecision = getattr(_workflow_models, "JudgeDecision", FinalVerdict)

# Import compatibility for older callers.  These models are not used by active
# runtime agent specs below.
EPSQualityFinding = getattr(_workflow_models, "EPSQualityFinding", EarningsQualityFinding)
ProfitabilityFinding = getattr(_workflow_models, "ProfitabilityFinding", EarningsQualityFinding)
CashFlowFcfFinding = getattr(_workflow_models, "CashFlowFcfFinding", CashFlowRiskFinding)
BalanceSheetRiskFinding = getattr(_workflow_models, "BalanceSheetRiskFinding", CashFlowRiskFinding)


JsonModel = type[BaseModel]
BullCaseSelection = _workflow_models.BullCaseSelection
BearCaseSelection = _workflow_models.BearCaseSelection
JudgeDecisionSelection = _workflow_models.JudgeDecisionSelection


@dataclass(frozen=True)
class AgentSpec:
    public_role: str
    output_agent_name: str
    output_model: JsonModel
    context_keys: tuple[str, ...]
    system_prompt: str
    task_prompt: str
    role_aliases: tuple[str, ...] = ()
    max_tokens: int = DEFAULT_AGENT_MAX_TOKENS
    temperature: float = DEFAULT_AGENT_TEMPERATURE

    @property
    def accepted_role_values(self) -> tuple[str, ...]:
        return (self.output_agent_name, self.public_role, *self.role_aliases)


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _to_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=_json_default,
    )


def _model_schema(model_type: JsonModel) -> dict[str, Any]:
    if hasattr(model_type, "model_json_schema"):
        return model_type.model_json_schema()
    return {"title": getattr(model_type, "__name__", str(model_type))}


def _extract_role(value: BaseModel) -> str | None:
    for field_name in ("agent_name", "role", "agent_role"):
        if hasattr(value, field_name):
            role = getattr(value, field_name)
            if role is None:
                return None
            enum_value = getattr(role, "value", None)
            return str(enum_value if enum_value is not None else role)
    return None


def _is_strict_openai_structured_output_schema(schema: Mapping[str, Any]) -> bool:
    """Return whether a JSON schema is safe for OpenAI strict structured output."""

    return _is_strict_openai_schema_node(schema)


def _is_strict_openai_schema_node(node: Any) -> bool:
    if isinstance(node, bool):
        return node
    if not isinstance(node, Mapping):
        return False
    if "default" in node or "$defs" in node or "$ref" in node:
        return False

    for keyword in ("anyOf", "oneOf", "allOf"):
        variants = node.get(keyword)
        if variants is not None:
            if not isinstance(variants, list) or not variants:
                return False
            return all(_is_strict_openai_schema_node(variant) for variant in variants)

    if node.get("type") == "array":
        return _is_strict_openai_schema_node(node.get("items"))

    if node.get("type") == "object" or "properties" in node:
        properties = node.get("properties")
        required = node.get("required")
        if not isinstance(properties, Mapping) or not isinstance(required, list):
            return False
        if node.get("additionalProperties") is not False:
            return False
        required_names = {name for name in required if isinstance(name, str)}
        if required_names != set(properties):
            return False
        return all(_is_strict_openai_schema_node(child) for child in properties.values())

    return True


class WorkflowAgent:
    """Small LLM wrapper for one specialist role."""

    spec: AgentSpec

    def __init__(
        self,
        llm: LLMProvider,
        *,
        max_retries: int | None = None,
        trace_sink: list[_workflow_models.AgentExecutionTrace] | None = None,
    ):
        self.llm = llm
        self.max_retries = _agent_max_retries() if max_retries is None else max(0, max_retries)
        self.trace_sink = trace_sink

    def __call__(self, **context: Any) -> BaseModel:
        return self.run(context)

    def run(self, context: Mapping[str, Any] | None = None, **kwargs: Any) -> BaseModel:
        merged: dict[str, Any] = {}
        if context:
            merged.update(context)
        merged.update(kwargs)
        resolve_skill_target(self.spec.public_role)
        routed_context = self._select_context(merged)
        schema = _model_schema(self.spec.output_model)
        user_prompt = self._build_user_prompt(routed_context, schema)

        last_error: AgentOutputValidationError | None = None
        attempts: list[_workflow_models.AgentAttemptTrace] = []
        for attempt in range(self.max_retries + 1):
            prompt = user_prompt if attempt == 0 else self._repair_prompt(user_prompt, last_error)
            try:
                response, structured_output = self._invoke_llm(prompt, schema)
            except Exception as exc:
                attempts.append(
                    self._attempt_trace(
                        attempt=attempt + 1,
                        success=False,
                        structured_output=False,
                        response=None,
                        error=exc,
                    )
                )
                self._record_trace(attempts)
                raise
            text = getattr(response, "text", response)
            try:
                parsed = self._parse_output(str(text))
                attempts.append(
                    self._attempt_trace(
                        attempt=attempt + 1,
                        success=True,
                        structured_output=structured_output,
                        response=response,
                        error=None,
                    )
                )
                self._record_trace(attempts)
                return parsed
            except AgentOutputValidationError as exc:
                last_error = exc
                attempts.append(
                    self._attempt_trace(
                        attempt=attempt + 1,
                        success=False,
                        structured_output=structured_output,
                        response=response,
                        error=exc,
                    )
                )
                if attempt >= self.max_retries or not self._should_repair(exc):
                    break

        if last_error is None:
            self._record_trace(attempts)
            raise AgentOutputValidationError(
                f"{self.spec.public_role} failed to produce an LLM response",
                error_kind="empty_response",
            )
        self._record_trace(attempts)
        self._raise_repair_exhausted(last_error, attempts)

    def _select_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        enriched_context = self._with_expected_metric_context(context)
        return {
            key: enriched_context[key]
            for key in self.spec.context_keys
            if key in enriched_context and enriched_context[key] is not None
        }

    def _with_expected_metric_context(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        if "expected_metrics" not in self.spec.context_keys or "expected_metrics" in context:
            return context
        role = EXPECTED_METRIC_ROLE_BY_PUBLIC_ROLE.get(self.spec.public_role)
        if role is None:
            return context
        return {**context, "expected_metrics": expected_metric_context(role)}

    def _build_user_prompt(
        self,
        routed_context: Mapping[str, Any],
        schema: Mapping[str, Any],
    ) -> str:
        return (
            f"{self.spec.task_prompt}\n\n"
            "制約:\n"
            "- 入力された routed_context だけを使う。\n"
            "- 財務指標を自分で計算しない。\n"
            "- missing/confidence低下の対象は `expected_metrics.required` にあり、"
            "`cap_if_missing=true` のcanonical/derived metricが同じ `period_role` で"
            "欠けている場合だけに限定する。\n"
            "- optional、reference_only、not_in_contract、presentation、transcript、"
            "news、analyst-reportの欠損やconflictではmissing_dataを書かず、"
            "confidenceを下げない。\n"
            "- 決算プレゼン、filing、shareholder letterなどの会社側テキストが、"
            "自分の担当領域に関係する重要な不確実性や条件付きリスクを会社自身の"
            "説明として明示している場合、その根拠をallowed fieldsに書き、"
            "自分のconfidenceを割り引く。未記述の予想や未開示データはこの扱いにしない。\n"
            "- summary、detail、handoff_summary、thesis、rationale、outlook理由など"
            "自然文のJSON field valueは日本語で書く。JSON schema key、enum値、"
            "evidence_id、source_id、metric_name、ticker、unitは変更しない。\n"
            "- 株価予測、目標株価、売買推奨を書かない。\n"
            "- EvidenceItem.source_ref は routed_context.source_index にある"
            " source_ref/source entry を正確にコピーする。source_id, source_type,"
            " url, document_id, section_id, metric_name, page, title を省略・変更しない。\n"
            "- `financial_api:NVDA:2027Q1` のような汎用source_idを新規作成しない。"
            " source_id は source_index に存在する値だけを使う。\n"
            "- routed_context に valid_positive_evidence_ids や valid_negative_evidence_ids が"
            "ある場合、positive/negative evidence と strongest evidence は"
            "`*_evidence_ids` fieldにID文字列だけを返し、該当一覧から完全一致で選ぶ。"
            "候補pool外のIDやnested EvidenceItemは返さない。\n"
            "- JSONのみを返す。Markdownや前置きは禁止。\n"
            f"- role field がある場合は {self.spec.output_agent_name!r} を入れる。\n\n"
            "# routed_context\n"
            f"{_to_json(routed_context)}\n\n"
            "# expected_output_schema\n"
            f"{_to_json(schema)}"
        )

    def _invoke_llm(self, prompt: str, schema: Mapping[str, Any]) -> tuple[Any, bool]:
        complete_structured = getattr(self.llm, "complete_structured", None)
        if callable(complete_structured) and _is_strict_openai_structured_output_schema(schema):
            try:
                return (
                    complete_structured(
                        system=self.spec.system_prompt,
                        user=prompt,
                        output_schema=schema,
                        schema_name=self.spec.output_model.__name__,
                        max_tokens=_agent_max_tokens(self.spec),
                        temperature=_agent_temperature(self.spec),
                    ),
                    True,
                )
            except NotImplementedError:
                pass

        return (
            self.llm.complete(
                system=self.spec.system_prompt,
                user=prompt,
                max_tokens=_agent_max_tokens(self.spec),
                temperature=_agent_temperature(self.spec),
            ),
            False,
        )

    def _parse_output(self, text: str) -> BaseModel:
        try:
            parsed = parse_model(self.spec.output_model, text)
        except StructuredOutputError as exc:
            raise AgentOutputValidationError(
                f"{self.spec.output_model.__name__} output failed {exc.error_kind}: {exc}",
                category=exc.category,
                error_kind=exc.error_kind,
                field=exc.field,
                retryable=True,
            ) from exc
        self._validate_role(parsed)
        return parsed

    def _should_repair(self, error: AgentOutputValidationError) -> bool:
        return error.category in {
            WorkflowErrorCategory.LLM_OUTPUT_SCHEMA,
            WorkflowErrorCategory.AGENT_ROLE,
        }

    def _raise_repair_exhausted(
        self,
        error: AgentOutputValidationError,
        attempts: list[_workflow_models.AgentAttemptTrace],
    ) -> NoReturn:
        trace_summary = self._trace_error_summary(attempts)
        message = (
            f"{self.spec.public_role} failed to produce valid JSON for "
            f"{self.spec.output_model.__name__}: {error}; {trace_summary}"
        )
        if error.category is WorkflowErrorCategory.AGENT_ROLE:
            raise AgentRoleMismatch(message, field=error.field, retryable=False) from error
        raise AgentOutputValidationError(
            message,
            category=error.category or WorkflowErrorCategory.LLM_OUTPUT_SCHEMA,
            error_kind=error.error_kind or "schema_mismatch",
            field=error.field,
            retryable=False,
        ) from error

    def _attempt_trace(
        self,
        *,
        attempt: int,
        success: bool,
        structured_output: bool,
        response: Any | None,
        error: Exception | None,
    ) -> _workflow_models.AgentAttemptTrace:
        text = getattr(response, "text", "") if response is not None else ""
        category = getattr(error, "category", None)
        error_kind = getattr(error, "error_kind", None)
        return _workflow_models.AgentAttemptTrace(
            attempt=attempt,
            success=success,
            structured_output=structured_output,
            input_tokens=int(getattr(response, "input_tokens", 0) or 0),
            output_tokens=int(getattr(response, "output_tokens", 0) or 0),
            output_chars=len(str(text)),
            category=category,
            error_kind=str(error_kind) if error_kind else None,
            retryable=bool(getattr(error, "retryable", False)),
        )

    def _record_trace(self, attempts: list[_workflow_models.AgentAttemptTrace]) -> None:
        if self.trace_sink is None:
            return
        self.trace_sink.append(
            _workflow_models.AgentExecutionTrace(
                public_role=self.spec.public_role,
                output_model=self.spec.output_model.__name__,
                max_retries=self.max_retries,
                attempt_count=len(attempts),
                success=bool(attempts and attempts[-1].success),
                total_input_tokens=sum(item.input_tokens for item in attempts),
                total_output_tokens=sum(item.output_tokens for item in attempts),
                attempts=attempts,
            )
        )

    def _trace_error_summary(
        self,
        attempts: list[_workflow_models.AgentAttemptTrace],
    ) -> str:
        if not attempts:
            return "attempts=0"
        return (
            f"attempts={len(attempts)}, "
            f"input_tokens={sum(item.input_tokens for item in attempts)}, "
            f"output_tokens={sum(item.output_tokens for item in attempts)}, "
            f"last_error_kind={attempts[-1].error_kind or 'unknown'}"
        )

    def _repair_prompt(self, original_prompt: str, error: Exception | None) -> str:
        details = [f"{type(error).__name__}: {error}"]
        category = getattr(error, "category", None)
        if category is not None:
            category_value = getattr(category, "value", category)
            details.append(f"category: {category_value}")
        error_kind = getattr(error, "error_kind", None)
        if error_kind:
            details.append(f"kind: {error_kind}")
        field = getattr(error, "field", None)
        if field:
            details.append(f"field: {field}")
        return (
            f"{original_prompt}\n\n"
            "# previous_output_error\n"
            f"{chr(10).join(details)}\n\n"
            "上のエラーを修正し、同じschemaに合うJSONのみを返してください。\n"
            f"role field がある場合は {self.spec.output_agent_name!r} を入れてください。\n"
            "自然文のJSON field valueは日本語で書いてください。JSON schema key、enum値、"
            "evidence_id、source_id、metric_name、ticker、unitは変更しないでください。\n"
            "schemaに `*_evidence_ids` field がある場合は、候補pool内の evidence_id "
            "文字列だけを返し、nested EvidenceItem や source_ref を出力しないでください。\n"
            "`source_ref` は routed_context.source_index に存在するentryを正確にコピーしてください。"
            "source_id, source_type, url, document_id, section_id, metric_name, page, title を"
            "省略・変更しないでください。source_indexに存在しないsource_idを作らないでください。\n"
            "`source_ref.source_type` が `financial_api` または `derived_metric` の場合、"
            "入力済みsource_refにある正確な `metric_name` を nested `source_ref` に必ず含めてください。"
            "metric_nameを新規作成したり、根拠を補正・捏造したりしないでください。"
        )

    def _validate_role(self, output: BaseModel) -> None:
        actual = _extract_role(output)
        if actual is None:
            return
        if actual not in self.spec.accepted_role_values:
            expected = ", ".join(repr(v) for v in self.spec.accepted_role_values)
            raise AgentRoleMismatch(
                f"{self.spec.public_role} expected role {expected}, got {actual!r}",
                field="agent_name",
            )


def _system(role: str, scope: str) -> str:
    return build_system_prompt(role, scope)


def _agent_max_tokens(spec: AgentSpec) -> int:
    if spec.public_role in {"BullAgent", "BearAgent"}:
        return env_int(
            "EARNINGS_DEBATE_DEBATE_MAX_TOKENS",
            spec.max_tokens,
            min_value=1,
        )
    if spec.public_role == "JudgeAgent":
        return env_int(
            "EARNINGS_DEBATE_JUDGE_MAX_TOKENS",
            spec.max_tokens,
            min_value=1,
        )
    return env_int(
        "EARNINGS_DEBATE_AGENT_MAX_TOKENS",
        spec.max_tokens,
        min_value=1,
    )


def _agent_temperature(spec: AgentSpec) -> float:
    if spec.public_role == "JudgeAgent":
        return env_float(
            "EARNINGS_DEBATE_JUDGE_TEMPERATURE",
            spec.temperature,
            min_value=0.0,
        )
    return env_float(
        "EARNINGS_DEBATE_AGENT_TEMPERATURE",
        spec.temperature,
        min_value=0.0,
    )


def _agent_max_retries() -> int:
    return env_int(
        "EARNINGS_DEBATE_AGENT_MAX_RETRIES",
        DEFAULT_AGENT_MAX_RETRIES,
        min_value=0,
    )


class EarningsQualityAnalyst(WorkflowAgent):
    spec = AgentSpec(
        public_role="EarningsQualityAnalyst",
        output_agent_name="EarningsQualityAnalyst",
        output_model=EarningsQualityFinding,
        context_keys=(
            "run_spec",
            "expected_metrics",
            "earnings_quality_metrics",
            "earnings_quality_sections",
            "source_index",
            "analysis_config",
        ),
        system_prompt=_system(
            "EarningsQualityAnalyst",
            (
                "EPS surpriseとP&Lの質を統合し、売上品質、margin trend、"
                "operating leverage、一時要因/継続要因、将来EPSへの示唆を分析する。"
            ),
        ),
        task_prompt="EarningsQualityFinding JSONを作成してください。",
        role_aliases=("eps_analyst", "pnl_analyst"),
    )


class CashFlowRiskAnalyst(WorkflowAgent):
    spec = AgentSpec(
        public_role="CashFlowRiskAnalyst",
        output_agent_name="CashFlowRiskAnalyst",
        output_model=CashFlowRiskFinding,
        context_keys=(
            "run_spec",
            "expected_metrics",
            "cash_flow_risk_metrics",
            "cash_flow_risk_sections",
            "cash_conversion_inputs",
            "source_index",
            "analysis_config",
        ),
        system_prompt=_system(
            "CashFlowRiskAnalyst",
            (
                "CFO、FCF、CapEx、working capital、liquidity、debt、"
                "financing constraintを統合し、将来FCF改善方向とリスクを分析する。"
            ),
        ),
        task_prompt="CashFlowRiskFinding JSONを作成してください。",
        role_aliases=("cfs_analyst", "bs_analyst"),
    )


# Legacy import aliases only.  They are intentionally excluded from
# SPECIALIST_AGENT_CLASSES and ALL_WORKFLOW_AGENT_CLASSES.
EPSQualityAnalyst = EarningsQualityAnalyst
ProfitabilityAnalyst = EarningsQualityAnalyst
CashFlowFcfAnalyst = CashFlowRiskAnalyst
BalanceSheetRiskAnalyst = CashFlowRiskAnalyst


class ManagementIntentAnalyst(WorkflowAgent):
    spec = AgentSpec(
        public_role="ManagementIntentAnalyst",
        output_agent_name="ManagementIntentAnalyst",
        output_model=ManagementIntentFinding,
        context_keys=(
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
        system_prompt=_system(
            "ManagementIntentAnalyst",
            "経営陣の意図、優先順位、投資判断、EPS/FCFへの時間軸別示唆を分析する。",
        ),
        task_prompt="ManagementIntentFinding JSONを作成してください。",
        role_aliases=("management_eval",),
    )


class GuidanceAnalyst(WorkflowAgent):
    spec = AgentSpec(
        public_role="GuidanceAnalyst",
        output_agent_name="GuidanceAnalyst",
        output_model=GuidanceFinding,
        context_keys=(
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
        system_prompt=_system(
            "GuidanceAnalyst",
            "guidanceとprecomputed consensus差分、前提、達成可能性、revision riskを分析する。",
        ),
        task_prompt="GuidanceFinding JSONを作成してください。",
        role_aliases=("guidance",),
    )


class BullAgent(WorkflowAgent):
    spec = AgentSpec(
        public_role="BullAgent",
        output_agent_name="bull_agent",
        output_model=BullCaseSelection,
        context_keys=(
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
            "valid_positive_evidence_ids",
            "valid_negative_evidence_ids",
            "disputed_points",
            "missing_data",
        ),
        system_prompt=_system(
            "BullAgent",
            "validated AnalysisBriefだけからgoodと評価できる最も強いcaseを作る。",
        ),
        task_prompt=(
            "BullCaseSelection JSONを作成してください。finding_coverageには earnings_quality, "
            "cash_flow_risk, management_intent, guidance を必ず含め、"
            "strongest_positive_evidence_idsには候補IDのみを返してください。"
        ),
        role_aliases=("BullAgent", "bull"),
        max_tokens=DEBATE_AGENT_MAX_TOKENS,
    )


class BearAgent(WorkflowAgent):
    spec = AgentSpec(
        public_role="BearAgent",
        output_agent_name="bear_agent",
        output_model=BearCaseSelection,
        context_keys=(
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
            "valid_positive_evidence_ids",
            "valid_negative_evidence_ids",
            "disputed_points",
            "missing_data",
        ),
        system_prompt=_system(
            "BearAgent",
            "validated AnalysisBriefと必要ならBullCaseSummaryからdownside/neutral caseを作る。",
        ),
        task_prompt=(
            "BearCaseSelection JSONを作成してください。finding_coverageには earnings_quality, "
            "cash_flow_risk, management_intent, guidance を必ず含め、"
            "strongest_negative_evidence_idsには候補IDのみを返してください。"
        ),
        role_aliases=("BearAgent", "bear"),
        max_tokens=DEBATE_AGENT_MAX_TOKENS,
    )


class JudgeAgent(WorkflowAgent):
    spec = AgentSpec(
        public_role="JudgeAgent",
        output_agent_name="judge_agent",
        output_model=JudgeDecisionSelection,
        context_keys=(
            "run_spec",
            "expected_metrics",
            "financial_snapshot_summary",
            "analysis_brief",
            "bull_case",
            "bear_case",
            "positive_evidence_pool",
            "negative_evidence_pool",
            "valid_positive_evidence_ids",
            "valid_negative_evidence_ids",
        ),
        system_prompt=_system(
            "JudgeAgent",
            "validated AnalysisBrief、BullCase、BearCaseを比較しgood/neutral/badを判定する。",
        ),
        task_prompt="JudgeDecisionSelection JSONを作成してください。",
        role_aliases=("JudgeAgent", "judge"),
        max_tokens=JUDGE_AGENT_MAX_TOKENS,
        temperature=JUDGE_AGENT_TEMPERATURE,
    )


SPECIALIST_AGENT_CLASSES: tuple[type[WorkflowAgent], ...] = (
    EarningsQualityAnalyst,
    CashFlowRiskAnalyst,
    ManagementIntentAnalyst,
    GuidanceAnalyst,
)

DEBATE_AGENT_CLASSES: tuple[type[WorkflowAgent], ...] = (BullAgent, BearAgent)

ALL_WORKFLOW_AGENT_CLASSES: tuple[type[WorkflowAgent], ...] = (
    *SPECIALIST_AGENT_CLASSES,
    *DEBATE_AGENT_CLASSES,
    JudgeAgent,
)


def build_default_agents(llm: LLMProvider) -> dict[str, WorkflowAgent]:
    """Create one wrapper per workflow role, keyed by public role name."""

    return {agent_cls.spec.public_role: agent_cls(llm) for agent_cls in ALL_WORKFLOW_AGENT_CLASSES}
