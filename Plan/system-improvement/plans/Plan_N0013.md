---
plan_id: Plan_N0013
project_id: system-improvement
status: draft
log_ref: Plan/system-improvement/logs/Plan_N0013.log.md
---

# Real Data Input And Structured Output Hardening Plan

## 0. Goal

Prepare the final real-data verification phase by hardening the input CLI,
guidance routing, context budget preflight, and provider-side structured output
before running real LLM API calls.

This plan is the corrected follow-up to the reviewed execution plan. It
incorporates sub-agent review feedback that guidance detection must become a
routing and missing-data signal, not only a hard ingestion gate.

## 1. Design Verdict

- `design_verdict`: proceed after contract-first implementation.
- `architecture_significance`: significant.
- `selected_option`: deterministic ingestion audit plus provider-side structured
  output where supported, with Pydantic validation retained.
- `human_gate_status`: real LLM API calls are external provider calls and should
  be run only after the user confirms target companies, provider, and that the
  source documents may be sent to the provider.

## 2. Source Refs Used

```text
AGENTS.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
docs/reference/repo-boundary-and-storage-reference.md
Plan/README.md
Plan/system-improvement/plans/Plan_N0012.md
src/main.py
src/llm.py
src/preprocessor.py
src/report_quality_guidance.py
src/structured.py
src/workflow.py
src/workflow_agents.py
src/workflow_models.py
tests/test_cli_smoke.py
tests/test_workflow_api.py
tests/test_workflow_e2e.py
OpenAI Structured Outputs:
https://platform.openai.com/docs/guides/structured-outputs
Anthropic Structured Outputs:
https://platform.claude.com/docs/en/build-with-claude/structured-outputs
Anthropic Strict Tool Use:
https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
```

## 3. Review Feedback Incorporated

### System Design Review

Result: `REWORK` for the earlier plan draft.

Required corrections:

- Do not keep guidance detection as a hard ingestion gate by default.
- Do not discard `GuidanceFact`; propagate it into workflow context, inspect
  output, and report-quality inputs.
- Do not rely on `section_id` and `heading` heuristics to route guidance.
  PDF-derived headings are generic, so guidance found in page text can be missed
  by `GuidanceAnalyst`.
- Add an input-inspection CLI that performs no LLM call.
- Add deterministic context budget preflight before any real provider call.

### Provider Schema Review

Result: `PASS` for the plan item:

```text
Add provider-side structured output using JSON Schema where supported, keep
Pydantic validation and retry fallback.
```

Required constraints:

- OpenAI supports Structured Outputs with JSON Schema. The repo should use the
  provider-side schema path for supported models.
- Anthropic supports structured JSON outputs for supported Claude models, and
  strict tool use for tool input schemas. Agent output should prefer structured
  JSON output, not a fake tool call.
- Pydantic validation remains mandatory because provider-side schema does not
  enforce repo-specific semantics such as source-ref copying, role matching,
  investment-advice exclusion, numeric grounding, and quality gates.
- Unsupported models, rejected schemas, refusals, truncation, or SDK/API
  incompatibility must fall back to the current prompt-schema plus Pydantic
  retry path.

## 4. Corrected Product Behavior

### Input Source Priority

The intended operational input model is:

1. `yfinance` provides financial metrics when `financial_metrics` is absent.
2. Local PDF/text `document_files` provide earnings content and guidance or
   outlook context when available.
3. SEC `filing_url` is a fallback when local documents are absent, or a
   supplemental source only after an explicit implementation change allows
   additive SEC ingestion.
4. `presentation_url` and `transcript_url` remain request-contract placeholders
   unless a future ingestion feature explicitly downloads them.

### Guidance Behavior

Guidance detection exists to route source sections and account for missing data.
It is not primarily a stop condition.

Allowed statuses:

- `found`: guidance or outlook source-backed sections were identified.
- `not_disclosed`: a source-backed statement says guidance was not provided,
  withdrawn, or suspended.
- `ambiguous`: guidance-like language exists, but confidence is not strong
  enough for a found classification.
- `not_found`: no guidance or no-guidance disclosure was identified in routed
  sources.

Default behavior:

- `found`: continue and route matched sections to `GuidanceAnalyst`.
- `not_disclosed`: continue and route the disclosure section to
  `GuidanceAnalyst` or deterministic report-quality logic.
- `ambiguous`: continue, route candidate sections, and mark missing-data caveat.
- `not_found`: continue without asking an LLM to invent guidance. Record a
  missing-data item and reduce confidence or report quality as appropriate.

Strict behavior:

- strict mode fails ingestion for `ambiguous` and `not_found`.
- strict mode is opt-in for CLI/API testing, not the default production path.

## 5. Target Internal Contracts

### IngestedReviewInput

Introduce an internal object owned by ingestion, not necessarily a public API
contract in the first implementation pass.

```text
IngestedReviewInput
  request
  metrics
  sections
  guidance_fact
  source_manifest
  routing_report
  context_budget_report
```

The workflow should pass this object, or its fields, through context building
instead of recomputing guidance and routing state in separate places.

### GuidanceFact

Extend the current guidance fact shape so it is useful for routing and audit.

```text
GuidanceFact
  status
  confidence
  source_refs
  candidate_section_ids
  matched_terms
  matched_signal_strength
  reason
```

Signal categories:

- strong guidance: `guidance`, `outlook`, `forecast`, `financial outlook`,
  `business outlook`, period-specific outlook labels, and expected financial
  ranges.
- no-guidance disclosure: `does not provide guidance`, `not providing guidance`,
  `no guidance`, `withdrawn guidance`, `suspended guidance`.
- weak or risky signals: `forward-looking statements`, `long-term target`,
  `strategy`, `roadmap`, broad demand commentary. These should not classify as
  `found` without stronger financial-outlook evidence.

### Routing Report

Add deterministic reporting for which sections are routed to each agent.

```text
RoutingReport
  agent_name
  routed_section_ids
  routed_source_refs
  routing_reason
  empty_context_reason
```

`GuidanceAnalyst` routing must use `GuidanceFact.source_refs` and
`candidate_section_ids` first. Heading/topic inference is only a fallback.

### Missing Guidance Representation

Current `AgentFinding` requires at least one `key_evidence` and one
`counter_evidence`. Therefore `not_found` must not be handled by asking
`GuidanceAnalyst` to create evidence from absence.

Implementation must choose one of these before enabling `not_found` continuation:

1. Add a role-specific deterministic missing-guidance result that is accepted by
   evidence aggregation and report quality without fabricated evidence.
2. Introduce `MissingDataItem` into the workflow/report matrix and let guidance
   absence bypass `GuidanceAnalyst`.
3. Relax only the guidance-specific contract so `GuidanceFinding` can be valid
   with no evidence when `guidance_status` is `not_found`.

Preferred option: use `MissingDataItem` and avoid fabricated evidence.

### Context Budget Report

Add a deterministic budget estimate before provider calls.

```text
ContextBudgetReport
  agent_name
  estimated_input_tokens
  max_input_tokens
  estimated_output_tokens
  max_output_tokens
  status
  largest_context_keys
  remediation
```

The first implementation may use a conservative character-based estimate. If a
provider-specific tokenizer is later added, it should be an implementation
detail behind this report.

## 6. Implementation Phases

### Phase A: Guidance Classification And Routing

Change scope:

- Replace default use of `validate_guidance_required()` with a non-throwing
  `classify_guidance_sources()` path.
- Keep strict validation as an explicit option, not default ingestion behavior.
- Return and retain `GuidanceFact`.
- Build guidance routing from matched source refs or candidate section IDs.
- Add tests for PDF pages with generic headings and guidance in page text.
- Add tests for `forward-looking statements` as a weak signal that does not
  become `found` by itself.

Acceptance:

- Guidance found in PDF text is routed to `GuidanceAnalyst`.
- No-guidance disclosure is source-backed and auditable.
- Not-found guidance does not force LLM evidence fabrication.

### Phase B: Input Inspect CLI

Add:

```bash
earnings-debate inspect-input \
  --input-json samples/request.current.yfinance-pdf.example.json \
  --out outputs/input-audit/nvda
```

The command must not call any LLM provider.

Outputs:

```text
normalized_input_summary.json
normalized_metrics.json
source_manifest.json
document_sections.preview.json
guidance_audit.json
routing_report.json
context_budget.json
```

Storage rules:

- Do not track broad generated audit output by default.
- Do not store raw SEC HTML, raw PDF text, secrets, or provider payloads in repo
  truth.
- Sample files may include small sanitized fixtures and current request
  examples.

Acceptance:

- CLI exits non-zero for invalid input contracts, missing files, empty PDFs, or
  context budget failure.
- CLI exits zero for `guidance.status` in `found`, `not_disclosed`,
  `ambiguous`, or `not_found` unless strict mode is enabled.
- Output clearly shows whether `GuidanceAnalyst` will receive guidance
  candidate sections.

### Phase C: Context Budget Preflight

Add deterministic budget checks before real provider calls.

Scope:

- Estimate full prompt size per agent after context routing.
- Fail or warn before provider call according to configured budget policy.
- Include largest context keys so oversized PDF sections can be debugged.
- Add a test with an oversized PDF/text section that fails inspect-input before
  any provider call.

Acceptance:

- `run` and `inspect-input` share the same budget logic.
- A context-max risk is detected before the first real LLM request.

### Phase D: Provider-Side Structured Output

Add a structured provider boundary.

Suggested interface:

```text
LLMProvider.complete_structured(
  system,
  user,
  output_model,
  max_tokens,
  temperature
) -> LLMResponse
```

Implementation:

- OpenAI: use provider-side JSON Schema structured output for supported models.
- Anthropic: use structured JSON output for supported Claude models.
- Fallback: if unsupported or rejected, use current text completion with schema
  in prompt and Pydantic parse/retry.
- Always run Pydantic validation after provider response.
- Preserve current fake provider behavior for tests.

Schema adapter:

- Normalize Pydantic JSON Schema into provider-accepted JSON Schema.
- Ensure strict object schemas reject extra properties where provider requires
  it.
- Treat unsupported schema keywords as implementation errors or strip only when
  safe and tested.

Acceptance:

- Agent calls use provider-side schema when available.
- Existing Pydantic validation and retry tests continue to pass.
- Schema failure errors include provider, agent role, output model, and field
  validation summary when available.

### Phase E: Verification Order

Run tests in this order:

1. Guidance detector unit tests.
2. Guidance routing tests.
3. Inspect-input CLI tests.
4. Context budget failure tests.
5. Provider structured-output unit tests with mocked SDK clients.
6. Fake-provider workflow smoke.
7. Real LLM smoke for one company.
8. Real LLM smoke for two or three companies after the first passes.

Do not start real LLM smoke until phases A through D pass locally.

### Phase F: Current Samples

After successful fake-provider and selected real-provider runs, add or update
current samples:

```text
samples/request.current.yfinance-pdf.example.json
samples/request.current.sec-fallback.example.json
samples/request.current.guidance-missing.example.json
outputs/example-current/report.md
outputs/example-current/workflow_result.json
```

Sample rules:

- Request examples should match the current contract.
- Checked-in outputs should be small and sanitized.
- Real PDFs, SEC raw cache, and provider raw payloads stay untracked.
- If using actual company material, cite public source locators without storing
  broad raw documents.

## 7. Success Criteria

- Input inspection can prove metrics normalization, document sectioning,
  guidance classification, routing, and token budget without any LLM call.
- Guidance detection directly affects `GuidanceAnalyst` routing or missing-data
  accounting.
- Missing guidance no longer stops the default workflow or causes fabricated
  evidence.
- Real LLM calls use provider-side structured output when supported.
- All LLM outputs remain Pydantic-validated and source-ref-checked.
- Current samples reflect the actual supported input path.

## 8. Non-Goals

- Automatic discovery or download of earnings presentation URLs.
- High-precision SEC parser redesign.
- Stock-price forecasts, target prices, trading recommendations, or investment
  advice.
- Storing raw PDFs, SEC HTML, provider prompts, provider responses, or broad
  runtime audit logs as tracked repo truth.

## 9. Residual Risks

- Provider structured-output APIs and supported schema subsets may change. Keep
  fallback and Pydantic validation mandatory.
- PDF text extraction may miss visual tables or image-only slides. Inspect CLI
  must surface empty or weak extraction.
- Guidance classification remains heuristic unless a future deterministic
  parser or human review step is added.
- Real LLM smoke can still fail from provider rate limits, model availability,
  or document content that exceeds practical context budgets.
