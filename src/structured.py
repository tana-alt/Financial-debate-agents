"""Helpers for validating structured LLM output.

LLM providers return text. The rest of the application should only see
validated Pydantic models.
"""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from .workflow_errors import WorkflowErrorCategory

ModelT = TypeVar("ModelT", bound=BaseModel)

ROLE_FIELDS = {"agent_name", "role", "agent_role"}
EVIDENCE_ERROR_MARKERS = (
    "source_ref",
    "source_manifest",
    "source_id",
    "metric_name",
    "evidence_id",
)


class StructuredOutputError(ValueError):
    """Classified failure while turning provider text into a workflow model."""

    def __init__(
        self,
        message: str,
        *,
        category: WorkflowErrorCategory = WorkflowErrorCategory.LLM_OUTPUT_SCHEMA,
        error_kind: str = "schema_mismatch",
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.error_kind = error_kind
        self.field = field


def strip_json_fence(text: str) -> str:
    """Accept bare JSON or a fenced JSON block and return the JSON payload."""
    payload = text.strip()
    if not payload.startswith("```"):
        return payload

    end = payload.rfind("```")
    if end <= 0:
        return payload

    inner = payload[3:end].strip()
    if inner.startswith("json"):
        inner = inner[4:].strip()
    return inner


def load_json(text: str) -> object:
    try:
        return json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(
            f"invalid JSON: {exc.msg}",
            error_kind="invalid_json",
        ) from exc


def parse_model(model_type: type[ModelT], text: str) -> ModelT:
    raw = load_json(text)
    try:
        return model_type.model_validate(raw)
    except ValidationError as exc:
        category, error_kind, field = _classify_validation_error(exc)
        raise StructuredOutputError(
            f"{model_type.__name__} schema validation failed: {exc}",
            category=category,
            error_kind=error_kind,
            field=field,
        ) from exc


def parse_model_list(model_type: type[ModelT], text: str) -> list[ModelT]:
    raw = load_json(text)
    if not isinstance(raw, list):
        raise StructuredOutputError("expected a JSON array", error_kind="schema_mismatch")
    try:
        return [model_type.model_validate(item) for item in raw]
    except ValidationError as exc:
        category, error_kind, field = _classify_validation_error(exc)
        raise StructuredOutputError(
            f"{model_type.__name__} list schema validation failed: {exc}",
            category=category,
            error_kind=error_kind,
            field=field,
        ) from exc


def _classify_validation_error(
    exc: ValidationError,
) -> tuple[WorkflowErrorCategory, str, str | None]:
    errors = exc.errors()
    fields = [_field_from_error(error) for error in errors]
    role_fields = [field for field in fields if _root_field(field) in ROLE_FIELDS]
    if role_fields and len(role_fields) == len([field for field in fields if field is not None]):
        return WorkflowErrorCategory.AGENT_ROLE, "role_mismatch", role_fields[0]

    searchable = " ".join(
        part.lower()
        for error, field in zip(errors, fields, strict=False)
        for part in (str(field or ""), str(error.get("msg", "")))
    )
    if any(marker in searchable for marker in EVIDENCE_ERROR_MARKERS):
        return WorkflowErrorCategory.LLM_OUTPUT_SCHEMA, "evidence_mismatch", fields[0]

    return WorkflowErrorCategory.LLM_OUTPUT_SCHEMA, "schema_mismatch", fields[0]


def _field_from_error(error: ErrorDetails) -> str | None:
    loc = error.get("loc")
    if not isinstance(loc, tuple) or not loc:
        return None
    return ".".join(str(part) for part in loc)


def _root_field(field: str | None) -> str | None:
    if field is None:
        return None
    return field.split(".", 1)[0]
