---
plan_id: Plan_N0012
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0012.log.md
lane_map_ref: Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml
---

# Contract And Execution Lane Map

## 0. Goal

Freeze the implementation contract before product-code refactoring, then define
which work must stay serial and which work can later run in independent lanes.

This plan keeps all new planning output under `Plan/system-improvement/` and
does not create new artifact output.

## 1. Design Verdict

- `design_verdict`: proceed after serial contract work
- `architecture_significance`: significant
- `selected_option`: serial core contract, limited parallel leaf lanes, serial
  integration
- `human_gate_status`: no external writes or product-code edits in this plan.
  Later public API behavior changes should receive human review before merge.

## 2. Source Refs Used

```text
AGENTS.md
README.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
templates/parallel-lane-map.yaml
scripts/check-lane-map.py
Plan/system-improvement/plans/Plan_N0008.md
Plan/system-improvement/plans/Plan_N0009.md
Plan/system-improvement/plans/Plan_N0010.md
Plan/system-improvement/plans/Plan_N0011.md
src/api.py
src/main.py
src/workflow.py
src/workflow_models.py
src/workflow_agents.py
src/workflow_runtime.py
src/workflow_validation.py
tests/
```

## 3. Shared Contract Decisions

### Input Boundary

The implementation target is `NormalizedReviewRequest`.

Required normalized input:

```text
schema_version
request_id
ticker
fiscal_period
financial_metrics
document_sections
source_manifest
context_budget
include_markdown
purpose
is_investment_advice
dry_run
```

API mode rejects raw acquisition fields:

```text
filing_url
presentation_url
transcript_url
document_files
raw_text
local_path
```

CLI/local ingestion owns those raw fields and converts them into normalized
sections plus `source_manifest`.

`filing_url` means an SEC filing URL used only by CLI/local ingestion to acquire
and segment source text. It is not an API review input after this refactor.

### Source Manifest

`source_manifest` is the authoritative source registry. `source_refs` should be
removed from the API request or kept only as a backward-compatible alias during
migration.

Each registered source must have a stable `source_id` and enough locator detail
to audit claims:

```text
source_id
source_type
document_id
title
url
section_id
metric_name
page
line_range
reported_period
as_of_date
```

Every `DocumentSection`, metric source, `EvidenceItem`, `ClaimRecord`, and
`DecisionUse` must reference registered IDs only.

### Report Matrix

Use the Plan_N0010 three-layer split:

- `EvidenceItem`: fact-check unit. It carries source/value/quote/timing and
  `fact_check_status`.
- `ClaimRecord`: agent interpretation unit. It carries claim type, time scope,
  evidence links, counter evidence links, interpretation, implication,
  confidence, and limitations.
- `DecisionUse`: Judge usage unit. It carries adopted/discounted/rejected/
  unresolved treatment, decisive evidence IDs, rationale, verdict impact, and
  confidence impact.

`MissingDataItem` replaces free-form missing-data strings for material gaps.

### Controlled Vocabularies

Initial required vocabularies:

```text
ClaimType
FactCheckStatus
JudgeTreatment
WorkflowErrorCategory
ReviewStatus
DryRunStatus
```

These should be implemented as enums or literals before prompts and renderer
are changed.

### Error Contract

Workflow failures use typed categories:

```text
input_contract
source_manifest
context_budget
provider
provider_transient
provider_config
llm_output_schema
agent_role
evidence_source
evidence_aggregation
quality_gate
render_response
internal_invariant
```

The API maps these to a stable error envelope. Do not return partial failure as
a completed `ReviewSuccessResponse`.

### Response Envelopes

Success:

```text
ReviewSuccessResponse
  status: completed
  request_id
  steps
  analysis_brief
  claim_matrix
  bull_case
  bear_case
  debate_result
  judge_decision
  decision_uses
  quality_gate_result
  markdown_report
  disclaimer
```

Failure:

```text
ReviewErrorResponse
  status: failed | partial
  request_id
  failed_step
  steps
  error_code
  error_category
  message
  retryable
  available_outputs
  missing_outputs
  quality_gate_result
  diagnostic_report
```

Dry run:

```text
ReviewDryRunResponse
  status: dry_run_passed | dry_run_failed
  request_id
  normalized_input_summary
  source_manifest_report
  context_budget_report
  planned_steps
  schema_contract_version
  prompt_contract_report
  errors
```

## 4. Dry-Run Contract

Dry run is a contract check, not a report-generation shortcut.

When `dry_run` is true:

- validate normalized input and rejected raw fields;
- validate `source_manifest` completeness and unique IDs;
- run deterministic context routing and budget checks;
- build prompt metadata or prompt size reports without calling the LLM provider;
- validate output schemas can be generated and referenced by role;
- return `ReviewDryRunResponse`;
- do not return `ReviewSuccessResponse`;
- do not call external providers;
- do not fetch SEC URLs;
- do not read local files beyond explicitly provided CLI input;
- do not emit final `judge_decision` or `markdown_report`.

CLI ingestion may have its own acquisition dry-run, but API dry-run starts from
normalized input only.

## 5. Serial Work

Serial work must happen first because it changes shared contracts or central
wiring:

1. `contract-core`: shared models, dry-run response, error taxonomy, response
   envelopes.
2. `context-router`: `ContextRouter` output contract and budget reports.
3. `integration-runner`: workflow orchestration wiring and final end-to-end
   verification.

Do not start parallel leaf lanes until `contract-core` passes its focused tests.

## 6. Parallel-Capable Work

After `contract-core` passes, these lanes can be executed independently if their
write scopes remain non-overlapping:

- `api-boundary`;
- `cli-ingestion`;
- `prompt-cleanup`;
- `agent-structured`;
- `evidence-quality`;
- `renderer-report`.

The durable execution map is:

```text
Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml
```

## 7. Test Policy

Dry-run contract regression is the baseline, but it is not enough.

Required test groups:

1. Dry-run contract tests:
   - `dry_run=true` never calls the provider;
   - raw acquisition fields are rejected in API dry-run;
   - invalid source manifest fails before provider call;
   - oversized routed context fails before provider call;
   - dry-run response never contains final report fields.
2. Model contract tests:
   - `EvidenceItem`, `ClaimRecord`, `DecisionUse`, and `MissingDataItem`
     validate required audit fields;
   - controlled vocabularies reject unknown values;
   - backward-compatible adapters preserve existing fixtures until migration
     finishes.
3. API contract tests:
   - `POST /reviews` accepts normalized input only;
   - error envelopes contain stable `error_category`, `error_code`,
     `retryable`, and `failed_step`;
   - HTTP status mapping matches Plan_N0008.
4. Context routing tests:
   - every routed source ID exists in `source_manifest`;
   - each role receives only allowed context keys;
   - budget failures happen before LLM invocation.
5. Structured-output and repair tests:
   - invalid JSON, schema mismatch, role mismatch, and evidence mismatch follow
     the retry policy;
   - repair exhaustion maps to `llm_output_schema` or `evidence_source`;
   - provider config and transient failures are not hidden as schema failures.
6. Prompt/schema parity tests:
   - runtime prompts do not include user templates or pseudo Python models;
   - prompt literal values match schema literals;
   - evidence field names match the frozen contract;
   - prompt size stays under the configured budget.
7. Report contract tests:
   - rendered report includes Judge Rationale, Bull vs Bear Tension, Evidence
     Matrix, Agent Contribution, Uncertainty And Missing Data, Quality Gates,
     Source Appendix, and Disclaimer;
   - visible matrix distinguishes fact, interpretation, implication, time scope,
     fact-check status, and Judge treatment;
   - source appendix is not duplicated across unrelated sections.
8. Safety and grounding tests:
   - no investment advice text appears in agent outputs or rendered report;
   - numeric claims cite `EvidenceItem` or derived metric basis;
   - management statements and forward-looking assumptions are labeled as such.
9. Fake-provider end-to-end tests:
   - completed success path still works without network;
   - representative failure path returns `ReviewErrorResponse`;
   - existing fake-provider fixtures are migrated without weakening strict
     schemas.

Live provider, live SEC fetch, performance, and broad integration tests are not
required for the first contract implementation. They can be added after the fake
provider path is stable.

## 8. Verification Commands

Narrow checks for this planning step:

```text
uv run python scripts/check-lane-map.py
uv run python - <<'PY'
from pathlib import Path
import yaml
yaml.safe_load(Path("Plan/system-improvement/index.yaml").read_text())
yaml.safe_load(Path("Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml").read_text())
PY
rg -n "[[:blank:]]$" Plan/system-improvement/plans/Plan_N0012.md Plan/system-improvement/logs/Plan_N0012.log.md Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml Plan/system-improvement/index.yaml
```

First implementation checks should start with:

```text
uv run pytest tests/test_workflow_models.py tests/test_contract_models.py
uv run pytest tests/test_api_smoke.py tests/test_workflow_api.py
uv run pytest tests/test_agent_assets.py tests/test_workflow_agents.py
uv run pytest tests/test_report_quality_full.py tests/test_safety_guards.py
uv run pytest tests/test_workflow_e2e.py
```

## 9. Residual Risk

- Introducing `dry_run` is a new explicit contract because the current codebase
  does not define a `dry_run` literal today.
- Response envelope migration can break FastAPI response-model assumptions if
  not done with a focused API contract lane.
- Report-grade schemas can increase LLM output failure until provider-native
  JSON Schema and compact repair are in place.
- The lane map is a planning/control record, not a runtime lock. It must be
  updated before any lane changes write scope.
