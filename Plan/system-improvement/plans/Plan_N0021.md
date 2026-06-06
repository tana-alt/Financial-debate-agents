---
plan_id: Plan_N0021
project_id: system-improvement
status: completed
created_at: 2026-06-07
owner: parent-agent
log_ref: Plan/system-improvement/logs/Plan_N0021.log.md
---

# Plan_N0021: Final Markdown Advice Warning And Evidence Prompt Audit

## Goal

Make final markdown investment-advice detection non-blocking while confirming
that prompts and runtime context instruct agents to use only validated evidence
and source references.

## Scope

- Convert final markdown investment-advice detection from hard block to
  warning/report metadata.
- Keep deterministic source/evidence integrity validation hard-blocking.
- Audit specialist/debate/judge prompts and runtime context for candidate-only
  evidence selection instructions.
- Add focused tests and run verification.

## Acceptance Criteria

- A final markdown report containing investment-advice language completes with a
  `llm_investment_advice:*` warning and redacted final markdown.
- Source/evidence integrity gates remain hard-blocking.
- Prompt/context audit identifies whether agents are instructed to stay inside
  candidate/source pools.
- Focused tests and lint/test verification pass.
