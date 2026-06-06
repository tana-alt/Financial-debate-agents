---
plan_id: Plan_N0020
project_id: system-improvement
status: completed
created_at: 2026-06-07
owner: parent-agent
log_ref: Plan/system-improvement/logs/Plan_N0020.log.md
---

# Plan_N0020: Extend Report And Context Length Gates

## Goal

Remove obsolete report-size blocking from real LLM runs and raise source/context
budgets enough for source-forward reports while keeping bounded contracts.

## Scope

- Extend `markdown_report` response limits that blocked real NVDA output.
- Audit other text/token gates that can block real CLI/API workflow.
- Raise default context budget, including presentation-heavy routing.
- Keep ordinary identifier/title/small field validation unchanged.
- Add focused tests and run verification.

## Acceptance Criteria

- `ReviewResponse` and API success responses accept source-forward reports
  larger than 20,000 characters.
- Default `ContextBudget` is above the previous 30,000-token presentation-era
  ceiling.
- Remaining length gates are identified and classified.
- Focused tests and lint/test verification pass.
