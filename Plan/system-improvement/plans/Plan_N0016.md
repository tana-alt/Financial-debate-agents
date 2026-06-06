---
plan_id: Plan_N0016
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0016.log.md
---

# Canonical Missing Confidence Cap Plan

## 0. Goal

Make confidence caps explainable and canonical-source driven.

The cap is managed by workflow-side deterministic input quality, not by raw
agent `missing_data` strings. Only SEC, yfinance, and derived canonical metrics
can create global confidence caps. Presentation values remain reference
material: presentation numeric gaps or conflicts may be shown as data quality
flags, but they do not become canonical actuals and do not cap confidence.

## 1. Design Verdict

- `design_verdict`: proceed.
- `selected_option`: workflow-managed stepped cap buffer.
- `cap_model`: simple missing-count ladder:
  - `0` cap-relevant canonical gaps: cap `1.0`;
  - `1` cap-relevant canonical gap: cap `0.8`;
  - `2+` cap-relevant canonical gaps: cap `0.6`;
  - explicit blocking/rejected/future-leakage gaps may use stricter fail or cap
    behavior only when already represented as canonical workflow status.
- `human_gate_status`: no merge; no real LLM/provider/network execution.

## 2. Source Refs Used

```text
AGENTS.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
Plan/system-improvement/plans/Plan_N0015.md
Plan/system-improvement/logs/Plan_N0015.log.md
src/report_quality_missing_data.py
src/workflow.py
src/workflow_models.py
src/report_renderer.py
src/prompts/shared/evidence_policy.md
src/prompts/presentation/management_intent_analyst.md
tests/test_report_quality_full.py
tests/test_report_renderer.py
```

## 3. Findings From Parent And Sub-Agents

- Top-level specialist context keys match router keys, but role-specific input
  shapes are still incomplete in Plan_N0015.
- Existing confidence caps are not contract-aware: raw agent `missing_data`
  strings can cap confidence by substring.
- Report rendering filters out unsupported/out-of-contract missing data in one
  section, but cap logic and Agent Contribution still use raw missing strings.
- Prompts still mention transcript expectations even though Plan_N0015 does not
  add transcript/news/analyst/web-search sources.

## 4. Scope

Implement the confidence-cap subset now:

- add a canonical cap predicate that only counts canonical source types:
  `financial_api`, `filing`, and `derived_metric`;
- ignore presentation, manual upload, transcript, press release,
  out-of-contract, optional missing, and non-blocking presentation conflicts;
- step cap by cap-relevant missing count: `1.0`, `0.8`, `0.6`;
- keep raw agent missing text visible only when reportable, but do not let raw
  agent missing text drive global caps by default;
- update prompt/policy text to state that transcript/news/analyst gaps are
  out-of-contract for this profile and should not be emitted as cap-driving
  missing data;
- add focused tests before implementation where practical.

Out of scope for this plan:

- real LLM execution;
- real yfinance/SEC network smoke;
- full role-specific input model migration beyond cap-relevant plumbing;
- changing public API response schemas.

## 5. Acceptance Criteria

- A canonical yfinance/SEC `MissingDataItem` with one cap-relevant gap caps a
  judge decision at `0.8`.
- Two or more cap-relevant canonical gaps cap at `0.6`.
- Presentation missing/conflict items do not cap confidence.
- `not_in_contract`, `out_of_scope_source_policy`, and `optional_missing` do
  not cap confidence unless explicitly blocking and canonical.
- Raw specialist `missing_data` text does not cap confidence by default.
- Existing CLI fake samples still run without real LLM.

## 6. Verification Plan

- focused report-quality tests first;
- targeted workflow/report renderer tests;
- `ruff format --check`, `ruff check`;
- targeted mypy for touched files;
- full pytest before PR update when feasible;
- fake-provider CLI smoke only, no real LLM.
