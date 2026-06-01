"""FastAPI entry point for the earnings review workflow."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .context_router import ContextRouter, ContextRouterError, ContextSourceScopeError
from .llm import get_provider
from .preprocessor import DocumentFileValidationError
from .workflow import MarkdownRenderer, ReviewRequest, ReviewResponse, ReviewWorkflow
from .workflow_agents import WorkflowAgentError
from .workflow_errors import WorkflowContractError, WorkflowErrorCategory
from .workflow_models import (
    DryRunCheck,
    DryRunStatus,
    NormalizedReviewRequest,
    ReviewDryRunResponse,
    ReviewErrorResponse,
    ReviewSuccessResponse,
    WorkflowErrorDetail,
)
from .workflow_validation import WorkflowValidationError

app = FastAPI(title="Earnings Debate Agent API")

REVIEW_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {
        "model": ReviewErrorResponse | ReviewDryRunResponse,
        "description": "Normalized input, source manifest, context budget, or dry-run preflight failure.",
    },
    500: {
        "model": ReviewErrorResponse,
        "description": "Internal review workflow failure.",
    },
}


def get_workflow() -> ReviewWorkflow:
    return ReviewWorkflow(llm=get_provider())


@app.post(
    "/reviews",
    response_model=ReviewSuccessResponse | ReviewDryRunResponse,
    responses=REVIEW_ERROR_RESPONSES,
)
def create_review(
    payload: Any = Body(...),
) -> ReviewSuccessResponse | ReviewDryRunResponse | JSONResponse:
    if not isinstance(payload, Mapping):
        return _error_response(
            422,
            {},
            WorkflowErrorCategory.INPUT_CONTRACT,
            "Request body must be a JSON object matching NormalizedReviewRequest.",
        )

    try:
        request = NormalizedReviewRequest.model_validate(payload)
    except ValidationError as exc:
        return _validation_error_response(payload, exc)

    if request.dry_run:
        return _dry_run_response(request)

    preflight_error = _runtime_required_input_error(request)
    if preflight_error is not None:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.INPUT_CONTRACT,
            preflight_error,
            field="document_sections",
        )

    context_error = _execution_context_error_response(request)
    if context_error is not None:
        return context_error

    try:
        legacy_request = _legacy_review_request(request)
        result = _resolve_workflow().run(legacy_request)
        return _success_response(legacy_request, result)
    except DocumentFileValidationError as exc:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.INPUT_CONTRACT,
            str(exc),
        )
    except WorkflowContractError as exc:
        category = exc.category
        return _error_response(
            _status_for_category(category),
            request,
            category,
            str(exc),
            field=exc.field,
        )
    except WorkflowAgentError as exc:
        category = exc.category or WorkflowErrorCategory.LLM_OUTPUT_SCHEMA
        return _error_response(
            _status_for_category(category),
            request,
            category,
            str(exc),
            field=exc.field,
            retryable=exc.retryable,
        )
    except WorkflowValidationError as exc:
        return _error_response(
            422,
            request,
            _workflow_validation_category(str(exc)),
            str(exc),
        )
    except ContextSourceScopeError as exc:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.SOURCE_MANIFEST,
            str(exc),
        )
    except ContextRouterError as exc:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.CONTEXT_BUDGET,
            str(exc),
        )
    except Exception:
        return _error_response(
            500,
            request,
            WorkflowErrorCategory.INTERNAL_INVARIANT,
            "Internal review workflow failure.",
        )


def _resolve_workflow() -> ReviewWorkflow:
    override = app.dependency_overrides.get(get_workflow)
    if override is not None:
        return override()
    return get_workflow()


def _legacy_review_request(request: NormalizedReviewRequest) -> ReviewRequest:
    return ReviewRequest(
        request_id=request.request_id,
        ticker=request.ticker,
        fiscal_period=request.fiscal_period,
        financial_metrics=request.financial_metrics,
        document_sections=request.document_sections,
        source_refs=[
            *request.financial_metrics.source_refs,
            *(section.source_ref for section in request.document_sections),
        ],
        source_manifest=request.source_manifest,
        context_budget=request.context_budget,
        include_markdown=request.include_markdown,
        purpose=request.purpose,
        is_investment_advice=request.is_investment_advice,
    )


def _success_response(request: ReviewRequest, result: ReviewResponse) -> ReviewSuccessResponse:
    claim_matrix = MarkdownRenderer().build_report_matrix(
        request=request,
        brief=result.analysis_brief,
        debate=result.debate_result,
        decision=result.judge_decision,
    )
    return ReviewSuccessResponse(
        request_id=result.request_id,
        ticker=result.ticker,
        fiscal_period=result.fiscal_period,
        steps=result.steps,
        analysis_brief=result.analysis_brief,
        claim_matrix=claim_matrix,
        bull_case=result.bull_case,
        bear_case=result.bear_case,
        debate_result=result.debate_result,
        judge_decision=result.judge_decision,
        decision_uses=claim_matrix.decision_uses,
        quality_gate_result=_quality_gate_result(claim_matrix),
        markdown_report=result.markdown_report,
        disclaimer=result.disclaimer,
    )


def _quality_gate_result(claim_matrix: Any) -> dict[str, Any]:
    return {
        "status": "passed",
        "source_manifest_entries": len(claim_matrix.source_manifest),
        "evidence_items": len(claim_matrix.evidence_items),
        "claim_records": len(claim_matrix.claim_records),
        "decision_uses": len(claim_matrix.decision_uses),
        "missing_data_items": len(claim_matrix.missing_data_items),
    }


def _dry_run_response(request: NormalizedReviewRequest) -> ReviewDryRunResponse | JSONResponse:
    checks = [
        DryRunCheck(
            name="normalized_input_contract",
            status=DryRunStatus.PASSED,
            message="NormalizedReviewRequest validation passed.",
        ),
        DryRunCheck(
            name="source_manifest",
            status=DryRunStatus.PASSED,
            message=f"{len(request.source_manifest)} source manifest entries registered.",
        ),
    ]

    preflight_error = _runtime_required_input_error(request)
    if preflight_error is not None:
        return _failed_dry_run_response(
            422,
            request,
            checks,
            "runtime_required_input",
            WorkflowErrorCategory.INPUT_CONTRACT,
            preflight_error,
            field="document_sections",
        )

    try:
        budget_report = ContextRouter().check_budget(request)
    except ContextSourceScopeError as exc:
        return _failed_dry_run_response(
            422,
            request,
            checks,
            "source_manifest",
            WorkflowErrorCategory.SOURCE_MANIFEST,
            str(exc),
        )
    except ContextRouterError as exc:
        return _failed_dry_run_response(
            422,
            request,
            checks,
            "context_budget",
            WorkflowErrorCategory.CONTEXT_BUDGET,
            str(exc),
        )
    except Exception:
        return _error_response(
            500,
            request,
            WorkflowErrorCategory.INTERNAL_INVARIANT,
            "Internal dry-run validation failure.",
        )

    if not budget_report.within_budget:
        return _failed_dry_run_response(
            422,
            request,
            checks,
            "context_budget",
            WorkflowErrorCategory.CONTEXT_BUDGET,
            _budget_failure_message(budget_report.failures),
        )

    checks.append(
        DryRunCheck(
            name="context_budget",
            status=DryRunStatus.PASSED,
            message=f"Context budget check passed for {len(budget_report.estimates)} roles.",
        )
    )
    return ReviewDryRunResponse(
        request_id=request.request_id,
        ticker=request.ticker,
        fiscal_period=request.fiscal_period,
        dry_run_status=DryRunStatus.PASSED,
        checks=checks,
    )


def _execution_context_error_response(
    request: NormalizedReviewRequest,
) -> JSONResponse | None:
    try:
        budget_report = ContextRouter().check_budget(request)
    except ContextSourceScopeError as exc:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.SOURCE_MANIFEST,
            str(exc),
        )
    except ContextRouterError as exc:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.CONTEXT_BUDGET,
            str(exc),
        )
    except Exception:
        return _error_response(
            500,
            request,
            WorkflowErrorCategory.INTERNAL_INVARIANT,
            "Internal context validation failure.",
        )

    if not budget_report.within_budget:
        return _error_response(
            422,
            request,
            WorkflowErrorCategory.CONTEXT_BUDGET,
            _budget_failure_message(budget_report.failures),
            field="context_budget",
        )

    return None


def _failed_dry_run_response(
    status_code: int,
    request: NormalizedReviewRequest,
    checks: list[DryRunCheck],
    check_name: str,
    category: WorkflowErrorCategory,
    message: str,
    *,
    field: str | None = None,
) -> JSONResponse:
    message = _truncate_message(message)
    response = ReviewDryRunResponse(
        request_id=request.request_id,
        ticker=request.ticker,
        fiscal_period=request.fiscal_period,
        dry_run_status=DryRunStatus.FAILED,
        checks=[
            *checks,
            DryRunCheck(
                name=check_name,
                status=DryRunStatus.FAILED,
                message=message,
                category=category,
            ),
        ],
        errors=[
            WorkflowErrorDetail(
                category=category,
                message=message,
                field=field,
                retryable=_is_retryable(category),
            )
        ],
    )
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))


def _runtime_required_input_error(request: NormalizedReviewRequest) -> str | None:
    if not request.document_sections:
        return (
            "document_sections must contain at least one normalized document section "
            "for executable review input."
        )
    return None


def _validation_error_response(payload: Mapping[str, Any], exc: ValidationError) -> JSONResponse:
    message, field = _validation_summary(exc)
    category = _validation_category(message, field)
    return _error_response(
        422,
        payload,
        category,
        message,
        field=field,
    )


def _validation_summary(exc: ValidationError) -> tuple[str, str | None]:
    errors = exc.errors(include_input=False)
    if not errors:
        return "Request did not match the normalized review input contract.", None

    parts: list[str] = []
    first_field: str | None = None
    for error in errors[:3]:
        loc = ".".join(str(part) for part in error.get("loc", ()) if part != "__root__")
        field = loc or None
        if first_field is None:
            first_field = field
        message = _clean_validation_message(str(error.get("msg", "Invalid value.")))
        parts.append(f"{field}: {message}" if field else message)

    remaining = len(errors) - len(parts)
    if remaining > 0:
        parts.append(f"{remaining} more validation error(s)")

    return "; ".join(parts), first_field


def _clean_validation_message(message: str) -> str:
    return message.removeprefix("Value error, ").strip()


def _validation_category(message: str, field: str | None) -> WorkflowErrorCategory:
    haystack = f"{field or ''} {message}".lower()
    if "source_manifest" in haystack or "source_id" in haystack:
        return WorkflowErrorCategory.SOURCE_MANIFEST
    if (
        "context_budget" in haystack
        or "max_input_tokens" in haystack
        or "max_output_tokens" in haystack
        or "max_total_tokens" in haystack
    ):
        return WorkflowErrorCategory.CONTEXT_BUDGET
    return WorkflowErrorCategory.INPUT_CONTRACT


def _error_response(
    status_code: int,
    source: Mapping[str, Any] | NormalizedReviewRequest,
    category: WorkflowErrorCategory,
    message: str,
    *,
    field: str | None = None,
    retryable: bool | None = None,
) -> JSONResponse:
    request_id, ticker, fiscal_period = _identity_fields(source)
    response = ReviewErrorResponse(
        request_id=request_id,
        ticker=ticker,
        fiscal_period=fiscal_period,
        errors=[
            WorkflowErrorDetail(
                category=category,
                message=_truncate_message(message),
                field=field,
                retryable=_is_retryable(category) if retryable is None else retryable,
            )
        ],
    )
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))


def _identity_fields(
    source: Mapping[str, Any] | NormalizedReviewRequest,
) -> tuple[str | None, str | None, str | None]:
    if isinstance(source, NormalizedReviewRequest):
        return source.request_id, source.ticker, source.fiscal_period

    request_id_value: str | None = None
    request_id = source.get("request_id")
    if isinstance(request_id, str) and 1 <= len(request_id) <= 80:
        request_id_value = request_id

    ticker_value: str | None = None
    ticker = source.get("ticker")
    if isinstance(ticker, str):
        normalized = ticker.upper().strip()
        if re.fullmatch(r"[A-Z0-9.\-]{1,15}", normalized):
            ticker_value = normalized

    fiscal_period_value: str | None = None
    fiscal_period = source.get("fiscal_period")
    if isinstance(fiscal_period, str) and re.fullmatch(r"\d{4}Q[1-4]", fiscal_period):
        fiscal_period_value = fiscal_period

    return request_id_value, ticker_value, fiscal_period_value


def _budget_failure_message(failures: list[Any]) -> str:
    roles = ", ".join(failure.role.value for failure in failures) or "unknown"
    return f"context budget exceeded for role(s): {roles}"


def _workflow_validation_category(message: str) -> WorkflowErrorCategory:
    if message == "document_sections, document_files, or filing_url is required":
        return WorkflowErrorCategory.INPUT_CONTRACT
    return WorkflowErrorCategory.QUALITY_GATE


def _truncate_message(message: str) -> str:
    if len(message) <= 1200:
        return message
    return message[:1197] + "..."


def _status_for_category(category: WorkflowErrorCategory) -> int:
    if category in {
        WorkflowErrorCategory.INPUT_CONTRACT,
        WorkflowErrorCategory.SOURCE_MANIFEST,
        WorkflowErrorCategory.CONTEXT_BUDGET,
    }:
        return 422
    return 500


def _is_retryable(category: WorkflowErrorCategory) -> bool:
    return category is WorkflowErrorCategory.PROVIDER_TRANSIENT
