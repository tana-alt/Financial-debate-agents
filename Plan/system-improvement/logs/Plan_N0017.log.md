---
plan_id: Plan_N0017
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0017.md
---

# Plan_N0017 Log

## 2026-06-06 Kickoff

- User requested SEC normalization and centralized source management for SEC,
  yfinance, and presentation data.
- Goal created for end-to-end implementation and live data verification.
- Branch: `agent/financial-debate-agent/product/samples-followup`.
- Existing untracked Plan/artifact trees are local project records and are not
  assumed to be PR-tracked.
- Initial implementation direction:
  - add expected metric registry;
  - make presentation reference-only and non-cap;
  - implement SEC Company Facts P0 normalization;
  - integrate canonical availability into workflow caps;
  - verify with tests and live SEC/yfinance checks.

## 2026-06-06 Sub-Agent Findings

- Huygens reviewed expected metric registry integration:
  - keep public request/response schemas stable;
  - add small internal registry under `src/`;
  - use `FinancialMetrics.availability` as the output channel;
  - do not emit missing availability for absent presentation metrics;
  - keep presentation candidates out of canonical/derived metrics.
- Tesla reviewed SEC Company Facts normalization:
  - implement direct-quarter selection first, then YTD difference fallback;
  - normalize `PaymentsToAcquirePropertyPlantAndEquipment` and
    `PaymentsToAcquireProductiveAssets` as capex outflows;
  - derive canonical FCF from OCF and capex component refs;
  - avoid cap when one provider is missing but another accepted canonical source
    fills the metric.

## 2026-06-06 Implementation

- Added `src/expected_metrics.py`:
  - role-level expected metric registry;
  - required/optional/reference-only/not-in-contract classification;
  - presentation metrics marked reference-only and non-cap;
  - final canonical availability generation.
- Added `src/sec_company_facts.py`:
  - SEC CIK resolution and Company Facts fetch;
  - P0 selection for revenue, operating cash flow, capex;
  - direct-quarter preference and YTD-difference fallback;
  - capex sign normalization;
  - derived FCF through existing metric builder.
- Updated workflow integration:
  - specialist contexts receive readable `expected_metrics`;
  - workflow confidence caps use final canonical availability, not raw
    provider-specific missing flags;
  - yfinance and SEC are merged through `fetch_financial_metrics`;
  - SEC P0 values fill/replace canonical P0 values when period-verified;
  - yfinance EPS/consensus remain available without treating presentation as
    canonical.
- Updated tests for registry classification, SEC P0 normalization, SEC/yfinance
  merge behavior, and optional/presentation non-cap behavior.

## 2026-06-06 Verification So Far

- Initial TDD run failed as expected with missing `src.expected_metrics` and
  `src.sec_company_facts`.
- `uv run --active pytest -q tests/test_expected_metrics.py tests/test_sec_company_facts.py`
  passed: `9 passed`.
- `uv run --active pytest -q tests/test_expected_metrics.py tests/test_sec_company_facts.py tests/test_preprocessor.py tests/test_context_router.py tests/test_workflow_agents.py tests/test_workflow_api.py tests/test_report_quality_full.py tests/test_report_renderer.py`
  passed after updating optional/presentation cap expectations: `90 passed`, one
  existing Starlette warning.
- `uv run --active pytest -q tests/test_preprocessor.py tests/test_sec_company_facts.py tests/test_expected_metrics.py`
  passed: `24 passed`.
- Targeted format/lint/typecheck passed after formatting:
  `ruff format`, `ruff check`, and `mypy`.
- Live SEC/yfinance smoke checked `NVDA`, `AAPL`, `MSFT`, `AMZN`, and `META`.
  Result: all five passed. Required canonical availability for `revenue`, `eps`,
  `operating_cash_flow`, `capex`, and `free_cash_flow` was `available`.
  P0 providers were SEC Company Facts for revenue/OCF/capex, yfinance for EPS,
  and derived metric for FCF.

## 2026-06-06 Cross Review And Final Verification

- Cross-review round 1:
  - Godel flagged YTD immediate-prior handling, overwritten conflict
    availability, direct FCF source retention, and missing SEC trace metadata.
  - Mencius flagged top-level-only canonical availability, missing
    `expected_metrics` routing for BULL/BEAR/JUDGE, and test gaps.
  - Parent integrated fixes and expanded tests.
- Cross-review round 2:
  - Confucius flagged loose P0 source policy, SEC closest-period selection, and
    sample/API fixture sign/source issues.
  - Harvey flagged expected-metric routing gaps, stale-period source acceptance,
    report conflict visibility, and CLI local output shape mismatch.
  - Parent integrated fixes and expanded tests.
- Final cross-review:
  - Pasteur found no blocking issues.
  - Pasteur confirmed strict SEC canonical policy for revenue/OCF/capex,
    yfinance-only EPS, derived FCF, +/-15 day SEC period selection, all-role
    expected metric routing, conflict display, and CLI API-equivalent output.
- Parent verification:
  - Targeted tests: `85 passed`, one existing Starlette warning.
  - CLI fake local run produced `status=completed`, `claim_matrix`,
    `source_manifest`, and all required canonical metrics available. Verdict
    remained `good (confidence 0.76)`.
  - Live SEC/yfinance smoke for `NVDA`, `AAPL`, `MSFT`, `AMZN`, `META`: all
    required canonical metrics available without P0 gaps.
  - Full verification passed:
    `make test` (`268 passed`, one existing Starlette warning), `make lint`,
    `make format-check`, `make typecheck`, and `git diff --check`.
