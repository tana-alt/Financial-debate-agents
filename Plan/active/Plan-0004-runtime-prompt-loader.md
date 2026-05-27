# Plan-0004: Runtime Prompt Loader

## Objective

Unify runtime prompt composition around shared prompt policies plus exactly one
agent prompt file per LLM call.

## Scope

- Prompt mapping from runtime agent role to `src/prompts/.../*.md`
- Shared prompt composition
- Stable role markers for FakeLLM and tests
- Runtime exclusion of prompt index files

## Out of Scope

- Editing prompt wording for quality beyond loader compatibility
- `.agents/skills` content changes, except where asset validation requires them
- README rewrite

## Dependencies

- `Plan-0001`

Coordination note: `Plan-0003` may run in parallel, but the final implementation
must align with its validated runtime agent and prompt asset mapping before
`Plan-0009`.

## Parallelization

Can begin in parallel after `Plan-0001`. Cross-plan consistency with
`Plan-0003` is verified during `Plan-0009`.

## Deliverables

- Prompt loader module or function
- Updated `WorkflowAgent` prompt composition
- Tests that verify shared prompts and one agent prompt are loaded

## Acceptance Criteria

- Runtime system prompt includes shared policies and the requested agent prompt.
- Runtime system prompt includes a stable public role marker.
- `src/prompts/index/*` is never loaded into runtime prompts.
- Existing Pydantic output validation still passes.

## Commands

```bash
.venv/bin/python -m pytest tests/test_workflow_agents.py -q
```

## Log

### 2026-05-27

- Branch: `runtime/0004-prompt-loader`
- Commits: pending commit
- Done: Added `src/prompt_loader.py`, composed shared prompt policies with
  exactly one agent prompt per runtime role, and connected `WorkflowAgent`
  system prompts to the loader with stable `<!-- ROLE: ... -->` markers.
- Decisions: Keep `.agents/skills` separate from runtime prompt text.
- Validation:
  - `.venv/bin/python -m pytest tests/test_agent_assets.py tests/test_workflow_agents.py -q` passed with 14 tests.
- Risks / Follow-up: Prompt text changes can break FakeLLM if role markers are
  not stable.
