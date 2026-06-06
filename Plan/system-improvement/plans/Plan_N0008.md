---
plan_id: Plan_N0008
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0008.log.md
---

# Workflow IO And Gate Redesign Plan

## 0. Goal

Create a compact system-design packet for improving workflow logic, input
boundaries, output contracts, quality gates, and report rendering after the
adoption of ADR-0001 through ADR-0003.

The design must keep the system simple, robust, and responsibility-separated
while preserving the current fixed seven-call workflow.

## 1. Scope And Write Targets

Allowed write targets:

```text
Plan/system-improvement/index.yaml
Plan/system-improvement/plans/Plan_N0008.md
Plan/system-improvement/logs/Plan_N0008.log.md
```

Read-only source refs:

```text
artifact/system-improvement/output/Plan_N0007/
README.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
src/api.py
src/main.py
src/workflow.py
src/workflow_agents.py
src/workflow_runtime.py
src/workflow_validation.py
src/workflow_models.py
src/structured.py
src/llm.py
src/preprocessor.py
src/report_quality_*.py
tests/
```

Out of scope:

```text
- implementing product-code refactors
- adding dependencies
- adding queues, databases, workers, or runtime storage
- external writes, deployment, release, push, merge, or PR creation
```

## 2. Method

Use three subagent review lanes:

1. workflow and gate logic;
2. input and context boundary;
3. output and report design.

The parent agent integrates these into one implementation-guiding design packet.

## 3. Stop Conditions

The plan is complete when:

- all three subagent findings are incorporated;
- this plan states boundaries, gates, owners, tradeoffs, verification,
  rollback/mitigation, and residual risk;
- project index references Plan_N0008;
- YAML parses and touched files have no trailing whitespace.

## 4. Design Verdict

- `design_verdict`: proceed
- `architecture_significance`: significant
- `selected_option`: keep the fixed seven-call workflow, but separate input
  normalization, context routing, agent invocation, structured parsing, evidence
  aggregation, quality gates, error mapping, and report rendering.
- `affected_boundaries`: public API, CLI ingestion, workflow stage contract, LLM
  provider boundary, structured output boundary, source evidence boundary,
  report output contract.
- `human_gate_status`: no external writes in this design record. Later
  implementation changes public API and trust boundaries, so it should receive
  human review before merge.

## 5. Adopted Baseline

This design assumes the accepted ADR directions:

- ADR-0001: API accepts pre-ingested input only. CLI/local ingestion owns raw
  files and SEC filing URL acquisition.
- ADR-0002: The design story aligns to the current runtime graph.
- ADR-0003: `POST /reviews` remains synchronous for the MVP.

The workflow remains fixed. Specialist work is not a free-form DAG: the current
runtime executes fixed specialist batches with `AgentRuntime.run_parallel`, then
continues through order-dependent debate and judge stages.

```text
NormalizedReviewRequest
  -> request/preflight gates
  -> ContextRouter
  -> Financial specialist batch
       - EarningsQualityAnalyst
       - CashFlowRiskAnalyst
  -> Presentation specialist batch
       - ManagementIntentAnalyst
       - GuidanceAnalyst
  -> EvidenceAggregator
  -> DebateRunner
       - BullAgent
       - BearAgent
  -> JudgeAgent
  -> QualityGateRunner
  -> MarkdownRenderer
```

Collapsing the two specialist batches into one fixed four-agent batch is a later
safe scheduling optimization only if tests prove no stage dependency is encoded.
It is not required for this refactor.

## 6. Problem

The current workflow-first shape is good, but responsibilities are mixed:

- `ReviewWorkflow` sequences stages, performs ingestion, builds context,
  invokes agents, runs validation, and calls the renderer.
- `WorkflowAgent` invokes the provider, builds prompts, parses JSON, validates
  Pydantic models, checks roles, and builds repair prompts.
- `WorkflowValidationGate` validates invariants but also aggregates evidence and
  canonicalizes source refs.
- API only maps `DocumentFileValidationError`; LLM output errors, provider
  failures, evidence mismatch, context budget overflow, and renderer failures do
  not have a clear public error contract.
- `ReviewResponse` is success-only. A failed run can record a failed step
  internally, but the API cannot return a structured partial or failure report.
- The renderer is deterministic, but it does not expose quality gate results,
  confidence cap reasons, or partial failure summaries.

## 7. Responsibility Separation

### API Layer

Owns accepting only pre-ingested review input, mapping workflow errors to public
HTTP status/error envelopes, and returning success only after final response
validation passes. It does not read local files, fetch external URLs, construct
prompts, or aggregate evidence.

### CLI Ingestion Layer

Owns local files, accepted SEC filing URLs, raw-text chunking, local/raw input
normalization, and `source_manifest` generation. It does not own LLM review,
debate/judge decisions, or final quality gates.

### Workflow Orchestrator

Owns fixed stage sequencing, `WorkflowRunState`, stage status, accepted artifact
recording, and halting on gate failures. It does not own provider-specific
structured output, detailed source routing, or report formatting.

### ContextRouter

Owns role-specific context assembly, agent-scoped source manifest subsets,
deterministic section ranking/truncation, context budget reports, and fail-fast
before provider calls.

### AgentInvoker, StructuredParser, RepairPolicy

`AgentInvoker` owns one role invocation, provider error normalization, and retry
budget. `StructuredParser` owns JSON/Pydantic validation and typed parse errors.
`RepairPolicy` owns whether parse/schema/evidence mismatch is retryable and
builds compact repair prompts. None of these should canonicalize evidence or map
API errors.

### EvidenceAggregator

Owns specialist role completeness, evidence deduplication, positive/negative
pool checks, canonical source exact matching, and `AnalysisBrief` construction.

### QualityGateRunner

Owns no-investment-advice checks, numeric grounding, guidance acquisition
status, missing-data disclosure, confidence caps, and unsupported claim/source
coverage warnings. It should not rewrite LLM conclusions or choose the final
verdict.

### MarkdownRenderer

Owns deterministic success and partial/failure report rendering, source
appendix, and quality gate sections. It should not perform LLM reasoning,
source lookup, or evidence validation.

## 8. Boundary Gate Matrix

| Boundary | Owner | Pass Criteria | Failure Category | Retry |
|---|---|---|---|---|
| API request | API layer | pre-ingested fields only, required metrics/sections, no raw file/url fields | `input_contract` | no |
| CLI ingestion | CLI ingestion | files/URLs converted into bounded sections and source manifest | `ingestion` | no LLM retry |
| Source manifest | Input preflight | unique source IDs, every section/metric source registered, locators stable | `source_manifest` | no |
| Context routing | ContextRouter | agent-scoped context under hard budget, source subset only | `context_budget` | no |
| Provider call | AgentInvoker | provider returns before timeout | `provider` | transient only |
| JSON/schema parse | StructuredParser | valid JSON and Pydantic model | `llm_output_schema` | one compact repair |
| Role validation | AgentInvoker | output role matches expected role | `agent_role` | one compact repair |
| Specialist evidence source | Validation gate | evidence source is in routed source manifest | `evidence_source` | one compact repair |
| Team completion | Orchestrator | four specialist roles completed exactly once | `stage_incomplete` | no |
| Evidence aggregation | EvidenceAggregator | positive/negative pools exist, canonical sources match | `evidence_aggregation` | no |
| Debate evidence | DebateRunner | Bull/Bear selected evidence IDs from validated pools | `debate_evidence` | one compact repair |
| Judge evidence | JudgeRunner | Judge selected evidence IDs from validated pools | `judge_evidence` | one compact repair |
| Quality gates | QualityGateRunner | no advice, grounded numbers, missing data disclosed | `quality_gate` | no LLM retry |
| Render response | MarkdownRenderer/API | deterministic report and response model validate | `render_response` | no |

## 9. Input And Context Contract

API should accept `NormalizedReviewRequest`, not raw acquisition inputs.

Minimum fields:

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
```

Rejected in API mode:

```text
filing_url
document_files
presentation_url
transcript_url
unused top-level source_refs
```

`source_refs` should either be removed from API input or renamed to
`source_manifest` and made authoritative.

Each normalized section should include `section_id`, `source_ref`, `heading`,
`text`, `topic`, and `char_count`.

`source_manifest` is the canonical registry: source IDs are unique, all section
and metric refs are registered, and source signatures include source ID, type,
document ID, section ID, metric name, page, title, URL, line range, and as-of
date when present.

`ContextRouter` should output:

```text
RoutedContext
  role
  run_spec
  role_specific_metrics
  sections
  source_index
  budget_report
  routing_reasons
```

Context max handling order:

1. fail fast if normalized input or routed context exceeds hard budget;
2. rank sections by topic/source/heading priority and keep top N;
3. deterministic section excerpts with original source locators preserved;
4. summarization only as a later explicit stage with source trace.

For MVP, use fail-fast, ranking, and deterministic excerpting. Do not add LLM
summarization until route and budget tests are stable.

## 10. Agent Invocation And Repair

Stabilize prompt-only structured output in this order:

1. separate `AgentInvoker`, `StructuredParser`, and `RepairPolicy`;
2. produce typed errors for provider, JSON parse, schema validation, role
   mismatch, context budget, and evidence mismatch;
3. use compact repair prompts that include only the error, expected schema
   summary, and valid IDs/source subset;
4. later add provider-native structured output as the default path.

Repair is allowed for invalid JSON, schema mismatch, role mismatch, and evidence
ID/source mismatch for debate and judge.

Repair is not allowed for context budget overflow, missing input sources, empty
evidence pools, investment advice gate failure, or provider auth/config errors.

## 11. Response Contract

Keep current `ReviewResponse` behavior for backward-compatible success where
useful, but introduce explicit success and error envelopes.

```text
ReviewSuccessResponse
  status: completed
  steps
  analysis_brief
  bull_case
  bear_case
  debate_result
  judge_decision
  quality_gate_result
  markdown_report
  disclaimer
```

```text
ReviewErrorResponse
  status: failed | partial
  failed_step
  steps
  error_code
  message
  retryable
  available_artifacts
  missing_outputs
  quality_gate_result
  human_readable_report
```

Use HTTP status to signal failure. Do not return a partial review as a completed
success. The partial report is diagnostic output, not the final earnings review.

Recommended mapping:

| Category | HTTP Status | Notes |
|---|---:|---|
| `input_contract` | 422 | bad API fields or missing normalized inputs |
| `source_manifest` | 422 | unknown, duplicate, or inconsistent source refs |
| `context_budget` | 422 | request too large for configured workflow budget |
| `llm_output_schema` | 502 | provider returned unusable structured output |
| `provider_transient` | 503 | timeout/rate limit/transient provider error |
| `provider_config` | 500 | missing key, invalid provider setup |
| `evidence_source` | 502 | model cited invalid source after repair exhaustion |
| `quality_gate` | 422 or 502 | deterministic input issue or LLM unsafe output |
| `internal_invariant` | 500 | unexpected implementation bug |

## 12. Report Structure

The final report should be deterministic and generated from validated objects:

1. Executive Summary: ticker, fiscal period, verdict, confidence, one-line
   conclusion.
2. Verdict: label, confidence, confidence cap reasons.
3. Evidence Table: direction, claim, value or quote, interpretation, source,
   timing, confidence.
4. Bull Case: thesis, strongest evidence, conditions needed, weak points.
5. Bear Case: thesis, failure modes, unresolved risks, counter to bull.
6. Uncertainty And Missing Data: material caveats and confidence impact.
7. Quality Gates: source coverage, numeric grounding, guidance acquisition,
   missing-data disclosure, no investment advice, unsupported claims.
8. Source Appendix: source id, type, locator, title, timing, used-for, URL.
9. Disclaimer: fixed non-investment-advice statement.

The renderer must not ask an LLM to create URLs, source IDs, locators, or quality
gate status. It should only render validated structured values.

## 13. Tradeoffs

- Smaller API vs direct convenience: raw ingestion outside API reduces SSRF,
  path traversal, local secret read, latency, and context-bloat risk. The cost is
  a CLI ingestion step or prebuilt normalized sample.
- Fail-fast vs automatic summarization: fail-fast can reject large inputs, but
  it makes context limits explicit and testable. Ranking/excerpting can handle
  common cases before adding summarization.
- More internal classes vs simpler runtime behavior: more types/files, but each
  boundary becomes testable and error categories become stable.
- Partial diagnostic output vs final report: partial reports help debugging but
  must stay under error envelopes and never masquerade as completed reviews.

## 14. Implementation Sequence

1. Contracts and error taxonomy: `WorkflowError`, `WorkflowRunState`,
   `StageResult`, success/error envelopes, `QualityGateResult`, API mapping.
2. Input boundary and CLI ingestion: enforce ADR-0001, add/rename
   `source_manifest`, add preflight, move raw URL/file ingestion to CLI/local.
3. ContextRouter: route specs, agent-scoped `source_index`, budget reports,
   fail-fast checks, remove full-metrics duplication and broad `other` fanout.
4. Agent invocation and repair: split invocation/parsing/repair, compact repair
   prompts, judge evidence mismatch repair, then provider-native structured
   output.
5. Evidence and quality gates: move aggregation out of `WorkflowValidationGate`,
   keep validation deterministic, aggregate report gates, surface confidence cap
   reasons.
6. Renderer and report contract: move `MarkdownRenderer` to its own module, add
   success and partial/failure rendering, enforce section order and source
   appendix from validated objects.

## 15. Verification Plan

Add or update tests for:

- API rejects raw acquisition fields.
- CLI ingestion converts local fixture and accepted SEC URL into normalized JSON.
- source manifest duplicate and missing refs fail fast.
- context budget failure occurs before provider call.
- routed context contains only agent-scoped source refs.
- invalid JSON repair succeeds and repair exhaustion fails with typed error.
- provider timeout/rate limit/context max maps to expected category/status.
- one parallel specialist failure records role status and blocks aggregation.
- specialist evidence outside routed source manifest fails before aggregation.
- Bull/Bear evidence mismatch repair success and failure.
- Judge evidence mismatch repair success and failure.
- no-investment-advice gates run at specialist, debate, judge, and markdown
  boundaries.
- success report contains required sections in order.
- partial/failure report includes completed steps, failed step, missing outputs,
  and available artifacts.
- evidence table and source appendix render only from validated
  `EvidenceItem`/`SourceRef` values.

## 16. Rollback Or Mitigation

If implementation becomes too large:

1. keep current workflow sequencing;
2. implement only `WorkflowError`, API mapping, and input preflight first;
3. add `ContextRouter` with fail-fast only;
4. defer provider-native structured output and partial report rendering.

Do not roll back to arbitrary API file/url ingestion or broad source fanout.

## 17. Residual Risk

- Provider-native structured output requires provider-specific implementation
  and current documentation review before coding.
- Renaming `source_refs` to `source_manifest` may require fixture and README
  updates.
- Strict context budgets can reject valid but large earnings documents until
  ranking/excerpting is tuned.
- Union API responses may require FastAPI/OpenAPI contract work.
- Keeping synchronous execution still risks real provider latency in hosted
  environments.
