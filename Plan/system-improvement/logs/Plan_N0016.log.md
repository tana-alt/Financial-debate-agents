---
plan_id: Plan_N0016
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0016.md
---

# Plan_N0016 Log

## 2026-06-06 Kickoff

- User requested a new Plan for workflow-managed confidence caps.
- Parent selected a simple cap buffer: `1.0 -> 0.8 -> 0.6`, driven by the count
  of cap-relevant SEC/yfinance/derived canonical gaps.
- Presentation numeric gaps/conflicts remain reference/data-quality material and
  must not become canonical actuals or cap confidence.
- No real LLM or external network smoke is in scope.

## 2026-06-06 Sub-Agent Review And Integration

- Jason implemented the focused cap behavior in the missing-data quality module,
  workflow cap plumbing, and focused report-quality tests.
- Noether reviewed the cap design and requested five integration fixes:
  canonical-only structured cap predicate, workflow-owned structured cap inputs,
  no raw-agent promotion into matrix missing items, Agent Contribution filtering,
  and prompt updates for deterministic workflow caps.
- Parent integrated the remaining renderer and workflow changes:
  - `confidence_cap` now uses only canonical `financial_api`, `filing`, and
    `derived_metric` cap-relevant items.
  - Cap ladder is `0 -> 1.0`, `1 -> 0.8`, `2+ -> 0.6`.
  - `MarkdownRenderer.confidence_cap_items` converts
    `FinancialMetrics.availability` into workflow-owned cap candidates.
  - Raw specialist `missing_data` is no longer promoted to
    `ReportMatrix.missing_data_items`.
  - Agent Contribution uses the same out-of-contract/transcript/news filtering
    as the uncertainty section.
  - Prompt policy now states that final global caps are workflow-managed and
    canonical-source driven.

## 2026-06-06 Verification

- `uv run --active pytest -q tests/test_report_quality_full.py tests/test_report_renderer.py tests/test_workflow_api.py`
  passed: `39 passed`, with one existing FastAPI/Starlette deprecation warning.
- `uv run --active pytest -q tests/test_cli_smoke.py tests/test_workflow_e2e.py tests/test_safety_guards.py`
  passed: `14 passed`, with one existing FastAPI/Starlette deprecation warning.
- `uv run --active ruff format --check src/report_quality_missing_data.py src/report_renderer.py src/workflow.py tests/test_report_quality_full.py tests/test_report_renderer.py tests/test_workflow_api.py`
  passed.
- `uv run --active ruff check .` passed.
- `uv run --active mypy` passed.
- `uv run --active pytest -q` passed: `244 passed`, with one existing
  FastAPI/Starlette deprecation warning.
- CLI fake smoke passed with no real LLM:
  `LLM_PROVIDER=fake uv run --active earnings-debate run --input-json samples/request.example.json`.
  Output verdict was `good` with confidence `0.76`, and the generated report
  contained Judge Rationale, Bull vs Bear Tension, Evidence Matrix, Agent
  Contribution, Data Quality Flags, Uncertainty And Missing Data, Quality Gates,
  Source Appendix, and Disclaimer.

## 2026-06-06 Completion

- Plan_N0016 acceptance criteria are complete.
- No real LLM/provider or external network smoke was run.

## 2026-06-06 External SEC/yfinance Readiness Check

- User requested a live SEC/yfinance consistency check for NVDA and several
  peers before treating data acquisition as ready.
- Checked `NVDA`, `AAPL`, `MSFT`, `AMZN`, and `META` against live yfinance and
  SEC Company Facts data.
- Compared latest common quarterly revenue, operating cash flow, capex, and
  derived free cash flow with a 7-day period-end tolerance for yfinance
  month-end rounding versus SEC fiscal period end.
- Initial check found no value conflict, but `NVDA` and `AMZN` capex were
  missing because SEC uses `PaymentsToAcquireProductiveAssets`.
- Parent added that SEC tag to the capex alias map in `src/metric_normalizer.py`
  and protected it with `tests/test_metric_normalizer.py`.
- Re-run result: all five tickers passed with no unresolved canonical missing
  values across the checked metrics.
- Verification:
  `uv run --active pytest -q tests/test_metric_normalizer.py tests/test_preprocessor.py`
  passed with `34 passed`;
  `uv run --active ruff format --check src/metric_normalizer.py tests/test_metric_normalizer.py`
  passed;
  `uv run --active ruff check src/metric_normalizer.py tests/test_metric_normalizer.py`
  passed;
  `git diff --check` passed.
- Commit `6e56728 Add SEC productive assets capex alias` was pushed to PR #24.
