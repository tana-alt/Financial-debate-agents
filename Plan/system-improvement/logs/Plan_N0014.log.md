---
plan_id: Plan_N0014
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0014.md
---

# Plan_N0014 Log

## 2026-06-01 Kickoff

- User requested a separate plan for temporal input alignment, including target
  quarter plus prior-quarter financial data, target-period-only PDFs, and
  prompt/yfinance consistency.
- Created `Plan_N0014` under `Plan/system-improvement/`.
- No `artifact/` output was created.

## 2026-06-01 Sub-Agent Reviews

- Temporal data contract reviewer returned `REWORK`.
  - Main issue: `fetch_consensus()` selects `earnings_dates.iloc[0]`, which can
    select a future row instead of the requested quarter.
  - Recommended request fields: target earnings date, target period end date,
    prior fiscal period, financial data cutoff, document period policy, and
    financial period policy.
  - Recommended period-role metadata and yfinance row-selection tests.
- Prompt/context reviewer returned `REWORK`.
  - Main issue: flat metrics and missing source period roles cannot prevent
    future information leakage.
  - Confirmed agent boundaries are directionally right.
  - Recommended temporal buckets, prompt constraints, context separation, and
    validation against `latest_snapshot` evidence.

## 2026-06-01 Plan Decisions

- Selected explicit temporal buckets instead of continuing with flat
  `FinancialMetrics`.
- Selected yfinance target-date row selection as MVP before adding SEC XBRL
  actual fallback.
- Kept PDFs/presentations target-period only.
- Decided that `latest_snapshot` can be audited but must not be routed as
  evidence to main workflow agents.
- Kept real LLM tests serial and user-attended.

## 2026-06-01 P&L Scope Adjustment

- User clarified that revenue consensus should not be part of the MVP.
- Updated the plan so P&L analysis focuses on quarter-over-quarter changes from
  obtainable actuals rather than ideal but often missing consensus or detailed
  margin inputs.
- Added MVP metric coverage:
  - high-probability target/prior actuals: EPS, revenue, operating cash flow,
    free cash flow, and capex;
  - high-probability consensus: EPS estimate and provider-supplied EPS surprise
    when available;
  - optional fields: operating margin, gross margin, operating income, opex,
    tax rate, share count, segment metrics, revenue consensus, and revenue
    surprise.
- Clarified that missing optional fields are normal missing data, not
  exceptional failures.
- Clarified that exception paths should be reserved for invalid temporal
  alignment, future leakage, schema mismatch, or source-reference violations.

## 2026-06-01 Plan Review And Real Data Feasibility

- Plan/prompt/API reviewer returned `REWORK`.
  - The plan mixed warning, validation error, and CLI error behavior for missing
    yfinance target rows.
  - The plan did not explicitly cover API-boundary tests even though
    `ReviewRequest` changes affect `src/api.py`.
- Real-data feasibility reviewer returned `PASS` with one Plan adjustment.
  - Checked `GOOGL`, `MSFT`, `NVDA`, `AAPL`, and `AMD` using yfinance and
    lightweight SEC reads.
  - All five had a future estimate-only first yfinance earnings row, confirming
    that `earnings_dates.iloc[0]` is unsafe.
  - All five had a recent historical EPS row with estimate, actual, and
    surprise, plus a prior EPS row.
  - All five had target/prior yfinance financial and cash-flow columns.
  - Revenue consensus was absent, supporting the MVP decision to keep it
    optional.
  - SEC company facts were available, but yfinance EPS can differ materially
    from SEC GAAP EPS, so basis metadata remains necessary.
- Updated the plan to:
  - separate validation errors from provider-missing warnings;
  - keep absent target/provider values as warnings and `missing_data` rather
    than default errors;
  - fail only invalid temporal metadata, future leakage, schema mismatch,
    target-only document violations, or explicit strict modes;
  - add API-boundary rules and tests;
  - distinguish `period_end_date` from yfinance `source_table_column_date`.
- Re-review sub-agent returned `PASS`.
  - Confirmed fail-vs-missing behavior is now executable and mode-specific.
  - Confirmed API contract and API-boundary tests are explicit enough for the
    next implementation phase.
  - Confirmed `source_table_column_date` is reflected in contract, yfinance
    policy, inspect output, and tests.

## 2026-06-01 Implementation

- Implemented temporal request metadata:
  - `target_earnings_date`
  - `target_period_end_date`
  - `prior_fiscal_period`
  - `financial_data_as_of`
  - document period policy and financial period policy
- Added source/document temporal metadata:
  - `fiscal_period`
  - `period_role`
  - `published_date`
  - `data_cutoff_date`
  - provider row/table dates
- Updated yfinance acquisition:
  - selects EPS row by `target_earnings_date`;
  - never uses `earnings_dates.iloc[0]` as a target-period proxy;
  - selects target/prior financial and cash-flow columns by period-end match;
  - records `source_table_column_date`;
  - leaves missing provider data as warnings and `missing_data`-eligible fields.
- Added temporal audit output to `inspect-input`:
  - `temporal_input_summary.json`
  - `metric_snapshots.json`
  - `temporal_source_manifest.json`
  - `temporal_validation.json`
- Added CLI flags for target earnings date, target period end date, prior
  fiscal period, financial data cutoff, and document period metadata.
- Updated prompts so agents distinguish target actuals, prior actuals,
  pre-earnings consensus, post-earnings guidance, and disallowed latest
  snapshots.
- Added API validation handling for workflow validation errors.

## 2026-06-01 Review Rework

- Code-review sub-agent initially returned `REWORK`.
  - `latest_snapshot` could enter prompts through raw `temporal_snapshots`.
  - `financial_data_as_of` was recorded but not enforced.
  - provider-dated embedded `financial_metrics` could bypass target date checks.
  - `document_files` with target date could omit fiscal period metadata.
  - a CLI smoke test did not sufficiently prove yfinance selection was mocked.
- Fixed the findings:
  - reject `latest_snapshot` in supplied financial source refs or temporal
    snapshots;
  - exclude raw `temporal_snapshots` from broad agent metric contexts;
  - validate provider row/table dates against target dates for supplied
    `financial_metrics`;
  - require `document_files` fiscal period and period role when target earnings
    date is present;
  - reject `financial_data_as_of` before the target earnings date;
  - add direct tests for the above cases.
- Second code-review pass returned one remaining `REWORK`:
  - supplied `source_table_column_date` was not compared to the target period
    end window.
- Added `source_table_column_date` window validation and test coverage.
- Final code-review sub-agent returned `PASS`.

## 2026-06-01 Real CLI Verification

- Ran real non-LLM CLI scenarios under `/tmp/eda-plan-n0014-final.IIz77x`.
- Target PDF + yfinance:
  - `NVDA 2027Q1`
  - selected yfinance row: `2026-05-20`
  - selected table column: `2026-04-30`
  - temporal validation: `passed`
  - EPS actual/consensus: `1.87` / `1.77`
- No target yfinance row:
  - `NVDA 2026Q2` with target earnings date `2025-06-15`
  - selected yfinance row: `null`
  - selected table column: `2025-07-31`
  - temporal validation: `passed_with_warnings`
  - warning: no earnings row for the target date
  - EPS fields remained missing instead of substituting another row.
- P&L matching:
  - `MSFT 2026Q3`
  - selected yfinance row: `2026-04-29`
  - selected table column: `2026-03-31`
  - temporal validation: `passed`
  - target/prior P&L and cash-flow values were available.
- Negative controls:
  - missing `target_earnings_date` failed validation;
  - wrong document fiscal period failed validation.
- Fake-provider run:
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local --input-json samples/request.example.json --out /tmp/eda-plan-n0014-final.IIz77x/fake-run`
  - completed `7` workflow steps with verdict `good`.
- CLI evidence review sub-agent returned `PASS` for the earlier generated
  scenario bundle and found only expected warning behavior.

## 2026-06-01 Final Verification

- `uv run --active ruff format --check .`: passed.
- `uv run --active ruff check .`: passed.
- `uv run --active pytest -q`: passed, `167 passed`, `1 warning`.
- `git diff --check`: passed.
- Real LLM provider calls were not run.
