---
plan_id: Plan_N0019
project_id: system-improvement
status: completed
created_at: 2026-06-07
owner: parent-agent
log_ref: Plan/system-improvement/logs/Plan_N0019.log.md
---

# Plan_N0019: Robust LLM Quality Gate Degradation

## Goal

Keep source/schema/context integrity as hard-blocking gates while converting
LLM-quality failures that can be represented safely into warnings or degraded
evidence so reports are produced more reliably.

## Scope

- Preserve hard blocks for malformed JSON, schema mismatch, source scope
  violations, evidence pool mismatches, and context budget failures.
- Treat numeric-grounding failures from LLM evidence as report-quality warnings
  instead of final hard failures.
- Prefer removing ungrounded material evidence from Judge candidate pools before
  debate/Judge selection.
- Keep investment-advice detection out of hard blocking where final output can
  be safely reported with warnings.
- Save raw LLM output as diagnostic artifact is considered but not required for
  this first pass unless it fits existing boundaries.

## Acceptance Criteria

- A report can complete when one LLM evidence item is material but numerically
  ungrounded, provided other valid evidence remains.
- Ungrounded material evidence is not promoted as decisive Judge evidence.
- Source and schema integrity failures remain hard blocks.
- Quality warnings are visible in deterministic report data.
- Focused tests and full lint/test verification pass.
