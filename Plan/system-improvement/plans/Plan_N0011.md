---
plan_id: Plan_N0011
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0011.log.md
---

# Plan Review And Parallel Readiness

## 0. Goal

Review Plan_N0007 through Plan_N0010 against the current prompts and related
runtime code before starting parallel implementation.

The review answers one question: can implementation safely move to parallel
write lanes now?

## 1. Verdict

- `review_verdict`: fail for immediate parallel execution
- `design_verdict`: rework before parallel writes
- `architecture_significance`: significant
- `reason`: the architecture direction is sound, but shared contracts and lane
  boundaries are not frozen tightly enough to avoid merge conflicts or duplicated
  implementation work.

Do not start parallel product-code edits until the serial prerequisites in this
plan are complete.

## 2. Review Method

Three read-only review lanes were used:

1. system-design consistency across Plan_N0007 through Plan_N0010;
2. prompt, schema, and related code consistency;
3. parallel execution readiness.

The parent agent also checked current workflow and prompt/model code paths.

## 3. Blocking Findings

### Evidence Responsibility Conflict

Plan_N0009 treated `EvidenceItem` as a combined fact, claim, interpretation, and
implication object. Plan_N0010 correctly separates this into:

- `EvidenceItem`: fact-check unit;
- `ClaimRecord`: agent interpretation unit;
- `DecisionUse`: Judge usage unit.

Plan_N0009 has been aligned to Plan_N0010. The implementation must freeze this
model contract before parallel work starts because `src/workflow_models.py` is
the highest-collision file.

### Structured Output Order Conflict

Plan_N0008 required splitting invocation, parsing, repair, and typed errors
before adding provider-native structured output. Plan_N0009 placed
provider-native JSON Schema first.

Plan_N0009 has been corrected: native JSON Schema remains the target, but it
comes after the explicit parser/error boundary so fallback behavior and API
error mapping stay stable.

### Stale Judge Prompt Observation

Plan_N0009 said `JudgeDecision` lacked `purpose` and `is_investment_advice`.
Current `src/workflow_models.py` already defines both fields. The real Judge
cleanup item is narrower: prompt/report wording should align around the runtime
`JudgeDecision` contract and avoid competing pseudo schemas.

### Specialist Scheduling Ambiguity

Plan_N0008 implied the four specialist calls were serial. Current runtime uses
fixed parallel batches through `AgentRuntime.run_parallel`: two financial
specialists, then two presentation specialists. Bull, Bear, and Judge remain
order-dependent because Bear receives the Bull summary and Judge receives both
cases.

Plan_N0008 now states this explicitly and does not introduce a dynamic DAG.

### Missing Parallel Lane Map

Parallel implementation needs a lane map before write work begins:

- `work_id`;
- `base_ref`;
- `merge_target`;
- one branch and one external worktree per agent;
- `conflict_policy: no_overlap`;
- allowed write scopes per lane;
- owner for shared model and error taxonomy changes.

Without this map, lanes will collide on `src/workflow_models.py`,
`src/workflow_agents.py`, `src/workflow.py`, and tests.

## 4. Current Prompt And Code Consistency Notes

- `src/prompts/shared/evidence_policy.md` still asks for fields that do not match
  current `EvidenceItem`; prompt cleanup must follow the frozen report contract.
- Bull/Bear prompt literals use `BullAgent` and `BearAgent`, while schemas expect
  `bull_agent` and `bear_agent`.
- Runtime system prompts are built from full markdown prompt assets, including
  user prompt templates and pseudo output models, while runtime user prompts also
  inject schema instructions.
- The current workflow keeps ingestion, context assembly, orchestration,
  validation, and rendering too close inside `ReviewWorkflow`.

These are valid implementation targets, but they should not be edited in
parallel until the shared contract and lane map are locked.

## 5. Serial Prerequisites

Complete these in one serial lane first:

1. Freeze the shared model contract:
   `NormalizedReviewRequest`, `source_manifest`, `SourceRef`,
   `DocumentSection`, `EvidenceItem`, `ClaimRecord`, `DecisionUse`,
   `MissingDataItem`, success/error envelopes, and controlled vocabularies.
2. Freeze the workflow error taxonomy:
   `input_contract`, `source_manifest`, `context_budget`, `provider`,
   `llm_output_schema`, `agent_role`, `evidence_source`,
   `evidence_aggregation`, `quality_gate`, `render_response`, and
   `internal_invariant`.
3. Decide module boundaries:
   `context_router.py`, renderer extraction, and placement of `AgentInvoker`,
   `StructuredParser`, and `RepairPolicy`.
4. Create the parallel lane map under `Plan/system-improvement/` with
   non-overlapping write scopes.

## 6. Parallel Lanes After Gate

After the serial prerequisites pass, parallel implementation can be split as:

1. API boundary lane: `src/api.py`, API request rejection, response envelopes,
   API tests.
2. CLI ingestion lane: `src/main.py`, `src/preprocessor.py`, normalized input
   samples, CLI tests.
3. Context routing lane: `src/context_router.py`, narrow `src/workflow.py`
   integration, context-router tests.
4. Agent structured-output lane: `src/workflow_agents.py`, `src/structured.py`,
   `src/llm.py`, provider/fallback tests.
5. Prompt cleanup lane: `src/prompts/**`, `src/prompt_loader.py`, prompt asset
   tests.
6. Evidence and quality gate lane: `src/workflow_validation.py`,
   `src/report_quality_*.py`, quality tests.
7. Renderer/report lane: renderer module, report contract tests, README example
   update.

## 7. Pass Criteria For Re-Review

Parallel execution can pass only when:

- Plan_N0008 through Plan_N0011 no longer contradict each other;
- the shared model and error taxonomy have one owner and one implementation
  sequence;
- prompt/schema mismatches are assigned to a lane;
- every lane has non-overlapping write targets;
- verification commands are known per lane.

## 8. Residual Risk

- The model contract can become too strict for LLM output. Keep audit-critical
  fields required and secondary display prose optional.
- Provider-native JSON Schema behavior is provider-specific and must be checked
  against official docs during implementation.
- Synchronous API execution remains vulnerable to provider latency even after
  structured-output reliability improves.
