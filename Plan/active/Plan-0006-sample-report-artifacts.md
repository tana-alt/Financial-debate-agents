# Plan-0006: Sample Input / Report Artifacts

## Objective

Add reproducible sample input and final report artifacts that demonstrate the
workflow without depending on external data fetching.

## Scope

- sample request JSON with `financial_metrics`
- sample request JSON with `document_sections`
- generated example `report.md`
- generated example `workflow_result.json` when appropriate

## Out of Scope

- README rewrite
- Real SEC filing download
- Full PDF parsing

## Dependencies

- `Plan-0001`
- `Plan-0005`

## Parallelization

Should run after FakeLLM can generate deterministic reports.

## Deliverables

- `samples/nvda_2025q3_request.json`
- `outputs/example/report.md`
- optional `outputs/example/workflow_result.json`

## Acceptance Criteria

- Sample request validates as `ReviewRequest`.
- Sample request requires no network calls.
- Example report matches the renderer section structure.
- Artifact generation command is documented in this plan log.

## Commands

```bash
LLM_PROVIDER=fake .venv/bin/earnings-debate run \
  --input-json samples/nvda_2025q3_request.json \
  --out outputs/example
```

## Log

### 2026-05-27

- Branch: `samples/0006-report-artifacts`
- Commits: pending commit
- Done: Added reproducible NVDA sample request and generated fake-provider
  example artifacts at `outputs/example/report.md` and
  `outputs/example/workflow_result.json`.
- Decisions: Use explicit `financial_metrics` and `document_sections` for
  reproducibility.
- Validation:
  - `LLM_PROVIDER=fake .venv/bin/earnings-debate run --input-json samples/nvda_2025q3_request.json --out outputs/example` passed.
  - Sample request validates as `ReviewRequest`.
- Risks / Follow-up: `outputs/example` should stay small and reviewable.
