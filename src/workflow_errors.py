"""Shared workflow error taxonomy.

These categories are stable contract values used by API envelopes, dry-run
checks, and workflow stages. Human-readable messages may change; categories
should not change without an explicit contract migration.
"""

from __future__ import annotations

from enum import Enum


class WorkflowErrorCategory(str, Enum):
    INPUT_CONTRACT = "input_contract"
    SOURCE_MANIFEST = "source_manifest"
    CONTEXT_BUDGET = "context_budget"
    PROVIDER = "provider"
    PROVIDER_TRANSIENT = "provider_transient"
    PROVIDER_CONFIG = "provider_config"
    LLM_OUTPUT_SCHEMA = "llm_output_schema"
    AGENT_ROLE = "agent_role"
    EVIDENCE_SOURCE = "evidence_source"
    EVIDENCE_AGGREGATION = "evidence_aggregation"
    QUALITY_GATE = "quality_gate"
    RENDER_RESPONSE = "render_response"
    INTERNAL_INVARIANT = "internal_invariant"


class WorkflowContractError(ValueError):
    """Value error carrying a stable workflow category for non-Pydantic callers."""

    def __init__(
        self,
        category: WorkflowErrorCategory,
        message: str,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.field = field
