# Plan-0003: Skill / Prompt / Hook Asset Validator

## Objective

Make the seven-agent skill and prompt assets verifiable without relying on an
external editor-specific hook runtime.

## Scope

- `.agents/skills/*/SKILL.md`
- `src/prompts/shared/*.md`
- one runtime prompt file per agent
- exclusion of `src/prompts/index/*` from runtime prompt loading
- development hook/validator script

## Out of Scope

- Runtime prompt loader implementation
- README rewrite
- CI wiring beyond exposing a command that CI can call later

## Dependencies

- `Plan-0001`

## Parallelization

Can run in parallel with `Plan-0002`, `Plan-0004`, and `Plan-0008`.

## Deliverables

- `scripts/validate_agent_assets.py`
- Tests for the validator
- Optional `.claude/settings.json` hook wiring that calls the validator

## Acceptance Criteria

- Validator confirms all seven runtime agents have a matching skill directory.
- Validator confirms all seven runtime agents have a matching prompt file.
- Validator confirms shared policy prompt files exist.
- Validator confirms index prompt files are not part of runtime prompt mapping.
- Validator exits non-zero on missing assets.

## Commands

```bash
.venv/bin/python scripts/validate_agent_assets.py
.venv/bin/python -m pytest tests/test_agent_assets.py -q
```

## Log

### 2026-05-27

- Branch: current workspace
- Branch: `agent-assets/0003-validator-hook`
- Commits: pending commit
- Done: Added `scripts/validate_agent_assets.py` and tests that verify the
  seven runtime agents have matching skill and prompt assets, shared policies
  exist, and runtime prompt mapping excludes `src/prompts/index`.
- Decisions: Treat `.agents/skills` as contract assets; runtime prompt text
  should come from `src/prompts`.
- Validation:
  - `.venv/bin/python scripts/validate_agent_assets.py` passed.
  - `.venv/bin/python -m pytest tests/test_agent_assets.py tests/test_workflow_agents.py -q` passed with 14 tests.
- Risks / Follow-up: Hook path should not be assumed until verified; validator
  remains the portable source of truth.
