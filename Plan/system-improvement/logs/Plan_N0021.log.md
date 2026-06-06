---
plan_id: Plan_N0021
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0021.md
---

# Plan_N0021 Log

## 2026-06-07

- Started after user decided final markdown investment-advice language should be
  handled as warning instead of block.
- User asked whether source/evidence integrity constraints are already stated
  in prompts, specifically candidate-only evidence selection.
- Prompt/context audit subagent result:
  - Specialist agents already instruct exact `source_ref` copy from
    `source_index`.
  - Bull/Bear agents already receive `valid_positive_evidence_ids` /
    `valid_negative_evidence_ids` and prompt instructions to choose from
    candidate pools.
  - Judge deterministic validation already hard-blocks candidate-id/source-ref
    mismatches, but Judge prompt/context was less explicit than Bull/Bear.
- Implemented final markdown investment-advice warning:
  - Replaced final markdown hard validation with `investment_advice_warnings()`
    plus `sanitize_investment_advice_text()`.
  - Final markdown advice warnings are attached to
    `AnalysisBrief.quality_warnings`; API success matrix can surface them via
    `data_quality_flags`.
- Implemented Judge prompt/context reinforcement:
  - `JudgeRunner` now passes `positive_evidence_pool`,
    `negative_evidence_pool`, `valid_positive_evidence_ids`, and
    `valid_negative_evidence_ids`.
  - `JudgeAgent` context keys route those fields into the runtime prompt.
  - Runtime prompt constraint now covers Judge `positive_evidence` /
    `negative_evidence` as well as Bull/Bear strongest evidence.
  - `src/prompts/debate/judge_agent.md` now explicitly requires exact
    candidate-pool evidence/source copying.
- Focused verification:
  - `uv run --active pytest tests/test_safety_guards.py -q` passed.
  - `uv run --active pytest tests/test_workflow_agents.py::test_judge_agent_prompt_routes_candidate_evidence_ids_and_pools tests/test_agent_assets.py::test_judge_prompt_requires_candidate_pool_evidence_copy -q` passed.
- Final verification:
  - `uv run --active pytest tests/test_safety_guards.py tests/test_workflow_agents.py tests/test_agent_assets.py tests/test_workflow_api.py::test_workflow_rejects_judge_evidence_source_ref_changes tests/test_workflow_api.py::test_workflow_rejects_bull_case_evidence_not_in_analysis_brief -q`
    passed: 57 passed, 1 warning.
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 285 passed, 1 warning.
