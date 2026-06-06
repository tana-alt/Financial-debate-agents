---
plan_id: Plan_N0009
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0009.log.md
---

# Report And Prompt Quality Review

## 0. Goal

Review the system beyond JSON-schema output reliability, focusing on whether the
visible report and runtime prompts are strong enough to justify the multi-agent
workflow.

Assumption: provider-native JSON Schema structured output is the selected target
for LLM output enforcement. It should be implemented after the parser/error
boundary from Plan_N0008 is made explicit, so the fallback path and public error
mapping do not get reworked twice. Provider-specific API details are not
implemented in this plan and should be checked against official docs during
implementation.

## 1. Scope And Write Targets

Allowed write targets:

```text
Plan/system-improvement/index.yaml
Plan/system-improvement/plans/Plan_N0009.md
Plan/system-improvement/logs/Plan_N0009.log.md
```

Read-only refs:

```text
README.md
src/workflow.py
src/workflow_models.py
src/workflow_agents.py
src/prompt_loader.py
src/prompts/**
src/report_quality_*.py
src/structured.py
src/llm.py
src/workflow_validation.py
tests/test_agent_assets.py
tests/test_report_quality_full.py
tests/test_workflow_agents.py
tests/test_workflow_api.py
```

## 2. Verdict

JSON Schema structured output addresses only one weakness: malformed or
schema-invalid model output. It does not by itself make the report dense,
decision-useful, or clearly multi-agent.

The remaining system weaknesses are:

1. report output compresses away the multi-agent debate;
2. current schemas are valid but not report-grade;
3. runtime prompts conflict with the actual schemas and are too document-like;
4. renderer tests do not enforce report information density;
5. README examples lag behind the current report contract.

## 3. Report Weakness

Current models contain useful material:

- specialist findings include key evidence, counter evidence, missing data, and
  handoff summaries;
- Bull and Bear include theses, conditions, weak points, failure modes, and
  unresolved risks;
- Judge includes verdict, confidence, rationale, evidence, and EPS/FCF outlook.

But the visible report does not expose enough of that structure:

- `JudgeDecision.rationale` is not a distinct first-class section;
- Bull/Bear tension is reduced to broad case prose;
- agent contribution is a list of summaries rather than a verdict influence map;
- confidence cap reasons are not visible;
- source appendix output is duplicated across Evidence Matrix, Source Inventory,
  and Sources;
- tests mostly assert that markdown exists, not that it is decision-dense.

## 4. Prompt Weakness

Runtime prompt composition currently loads shared policies and entire agent
markdown files. Those files contain role docs, user templates, pseudo output
models, validation notes, and runtime instructions.

Observed conflicts:

- shared evidence policy asks for `claim`, `quote_or_value`, `interpretation`,
  and top-level `source_type`, but `EvidenceItem` currently has `summary`,
  `detail`, `impact_areas`, and nested `source_ref`;
- Bull/Bear prompts say `agent_name` should be `BullAgent` or `BearAgent`, while
  schemas expect `bull_agent` and `bear_agent`;
- Judge prompt and schema now both include `purpose` and
  `is_investment_advice`; the remaining Judge mismatch is prompt/report wording
  cleanup around `FinalVerdict` versus the runtime `JudgeDecision` contract;
- prompt pseudo schema and injected runtime JSON Schema compete;
- some context rules are stale, such as optional handoff fields described as
  always present or forbidden.

## 5. Schema Weakness

Current strict Pydantic models protect basic shape, source refs, Bull/Bear
coverage, and Judge evidence canonicalization. The weakness is not lack of
strictness. The weakness is that key report concepts are still generic text.

Needed report-grade structures, aligned with Plan_N0010:

- `EvidenceItem` should remain the fact-check unit: source ref, source quote or
  reported value, comparator, delta, timing, and fact-check status.
- `ClaimRecord` should carry the analytical claim: claim type, evidence links,
  counter evidence links, interpretation, implication, impact areas, confidence,
  and limitations.
- `DecisionUse` should carry Judge treatment: adopted, discounted, rejected, or
  unresolved claim use, decisive evidence IDs, rationale, verdict impact, and
  confidence impact.
- `MissingDataItem` should replace string missing data with topic, severity,
  reason, needed-for, confidence cap, and optional source ref.
- Specialist findings should expose role-specific claims, counter claims,
  disputed points, EPS implication, FCF implication, and confidence cap reasons.
- Bull/Bear should expose dispute objects and structured argument blocks rather
  than only broad prose.
- Judge should expose a decision matrix: dispute, ruling, decisive evidence IDs,
  counter evidence IDs, implication, and confidence impact.
- `ReviewResponse` should include structured report sections or an evidence
  matrix, with `markdown_report` treated as deterministic render output.

## 6. Proposed Report Contract

The report should have these deterministic sections:

1. Executive Verdict
2. Judge Rationale
3. Bull vs Bear Tension
4. Evidence Matrix
5. Agent Contribution
6. Uncertainty And Missing Data
7. Quality Gates
8. Source Appendix
9. Disclaimer

Renderer-owned fields:

- headings and order;
- verdict, confidence, disclaimer;
- source appendix;
- quality gate status;
- confidence cap reasons;
- evidence tables from validated structured objects.

LLM-owned fields:

- concise summary prose;
- claim wording;
- interpretation and implication text;
- competing bull/bear positions;
- judge dispute rulings.

## 7. Proposed Prompt Contract

Runtime system prompts should include only:

- role identity and responsibility;
- allowed and forbidden context;
- decision policy;
- evidence source-copy policy;
- safety constraints;
- confidence and missing-data rules.

Runtime prompts should remove:

- user prompt templates;
- pseudo Python output models;
- field lists already enforced by JSON Schema;
- duplicate `JSON only` instructions;
- fields not present in the actual schema;
- stale literal values.

Schema is the output contract. Prompt is the judgment policy.

## 8. Implementation Order

1. Freeze the shared report contract: `EvidenceItem`, `ClaimRecord`,
   `DecisionUse`, `MissingDataItem`, controlled vocabularies, and response
   envelope names.
2. Split `AgentInvoker`, `StructuredParser`, and `RepairPolicy`; add typed
   provider, JSON parse, schema validation, role mismatch, context budget, and
   evidence mismatch errors.
3. Fix prompt/schema parity: evidence policy field names, Bull/Bear literals,
   Judge wording, stale context statements, and optional handoff descriptions.
4. Split runtime prompt assets from documentation sections or load only a
   delimited runtime section.
5. Add provider-native JSON Schema structured output with fallback to compact
   repair plus Pydantic validation.
6. Add report-grade `ClaimRecord`, dispute, and decision matrix fields to
   specialist, Bull/Bear, and Judge schemas.
7. Add structured final report sections to the response.
8. Refactor renderer to show the report contract sections and remove duplicate
   source appendix paths.
9. Update README report example to match the renderer contract.

## 9. Tests

Add tests for:

- prompt/schema field parity;
- prompt literal parity for Bull/Bear/Judge;
- no pseudo output model or user template in runtime system prompts;
- prompt size budget;
- `EvidenceItem` accepts only source/value/timing/fact-check basis fields;
- `ClaimRecord` rejects material report claims without claim type, evidence link
  or missing-data caveat, interpretation, implication, and time scope;
- `MissingDataItem` severity and confidence cap are required for material gaps;
- Judge decision matrix evidence IDs match validated pools;
- markdown includes Judge Rationale, Bull vs Bear Tension, Agent Contribution,
  Uncertainty And Missing Data, Quality Gates, Source Appendix;
- README sample headings match renderer headings;
- native schema provider path passes schema to the provider and fallback provider
  still uses Pydantic validation.

## 10. Residual Risk

- Provider-native JSON Schema implementation details are provider-specific and
  should be verified against official docs before coding.
- Expanding schemas increases migration work for tests and fake provider
  fixtures.
- Report-grade schema can become too verbose if every field is mandatory; keep
  core decision fields required and make secondary display fields optional.
- Prompt cleanup may invalidate prompt-asset tests that currently expect shared
  policy inclusion; update tests to match the new runtime prompt contract.
