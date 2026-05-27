# Plan-0009: Final Integration Validation

## Objective

Run the full local validation suite, confirm all child plan logs are updated,
and prepare the repo for final README work.

## Scope

- pytest
- ruff
- mypy
- asset validator
- FakeLLM API/CLI smoke
- Plan log completion audit

## Out of Scope

- README rewrite
- New workflow features
- Real LLM mandatory CI gate

## Dependencies

- `Plan-0002`
- `Plan-0003`
- `Plan-0004`
- `Plan-0005`
- `Plan-0006`
- `Plan-0007`
- `Plan-0008`

## Parallelization

Runs last after all implementation plans are complete.

## Deliverables

- Updated `Plan-0009` validation log
- Confirmation that each `Plan-000X` log is updated
- Final validation command results

## Acceptance Criteria

- `ruff check` passes.
- `ruff format --check` passes.
- `mypy` passes.
- `pytest` passes.
- asset validator passes.
- FakeLLM API/CLI smoke tests pass.
- Each plan has a current Log entry.

## Commands

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src tests
.venv/bin/python -m pytest -q
.venv/bin/python scripts/validate_agent_assets.py
LLM_PROVIDER=fake .venv/bin/python -m pytest tests/test_api_smoke.py tests/test_cli_smoke.py -q
! rg -n "^- Validation: Pending implementation\\." Plan/active/Plan-000*.md
```

## Log

### 2026-05-27

- Branch: `integration/0009-final-validation`
- Commits: pending commit
- Done: Ran the full local quality, type, test, asset-validator, smoke, and
  Plan log audit after completing Plan-0002 through Plan-0008.
- Decisions: Keep README rewrite as the next phase after runtime and CI are
  verified.
- Validation:
  - `.venv/bin/python -m ruff check .` passed.
  - `.venv/bin/python -m ruff format --check .` passed.
  - `.venv/bin/python -m mypy src tests` passed.
  - `.venv/bin/python -m pytest -q` passed with 43 tests.
  - `.venv/bin/python scripts/validate_agent_assets.py` passed.
  - `LLM_PROVIDER=fake .venv/bin/python -m pytest tests/test_api_smoke.py tests/test_cli_smoke.py -q` passed with 2 tests.
  - `! rg -n "^- Validation: Pending implementation\\." Plan/active/Plan-000*.md` passed.
- Risks / Follow-up: CI may expose environment-specific issues not reproduced
  locally.
