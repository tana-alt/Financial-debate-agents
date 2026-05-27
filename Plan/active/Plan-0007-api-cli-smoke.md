# Plan-0007: API / CLI Smoke Tests

## Objective

Verify that both API and CLI entry points can produce the final structured
response and Markdown report.

## Scope

- FastAPI `POST /reviews`
- CLI `earnings-debate run --input-json --out`
- `workflow_result.json`
- `report.md`

## Out of Scope

- Real LLM provider quality checks
- README rewrite
- Browser/UI testing

## Dependencies

- `Plan-0005`
- `Plan-0006`

## Parallelization

Runs after FakeLLM and sample artifacts are available.

## Deliverables

- API smoke test
- CLI smoke test
- output file assertions

## Acceptance Criteria

- API smoke returns HTTP 200 and response contains `markdown_report`.
- API response report contains required report sections.
- CLI smoke writes `workflow_result.json` and `report.md`.
- CLI output files contain ticker, period, verdict, positive evidence, negative
  evidence, EPS outlook, and FCF outlook.

## Commands

```bash
LLM_PROVIDER=fake .venv/bin/python -m pytest tests/test_api_smoke.py tests/test_cli_smoke.py -q
```

## Log

### 2026-05-27

- Branch: `test/0007-api-cli-smoke`
- Commits: pending commit
- Done: Added FastAPI smoke test for `POST /reviews` and CLI smoke test that
  writes `workflow_result.json` and `report.md` using `LLM_PROVIDER=fake`.
- Decisions: Keep API response assertions separate from CLI file persistence
  assertions.
- Validation:
  - `LLM_PROVIDER=fake .venv/bin/python -m pytest tests/test_api_smoke.py tests/test_cli_smoke.py -q` passed with 2 tests.
- Risks / Follow-up: CLI test should avoid requiring a long-running external
  server by using a test server or request monkeypatch.
