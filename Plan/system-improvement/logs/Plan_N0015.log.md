---
plan_id: Plan_N0015
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0015.md
---

# Plan_N0015 Log

## 2026-06-06 Kickoff

- User initially requested execution of `Plan_N0015` with parent/sub-agent
  implementation, review, integration, and reporting.
- Parent read active repo contracts, `Plan_N0015`, `Plan_N0014.log.md`,
  `Plan_N0013.log.md`, and narrow current `src/` and `tests/` surfaces.
- Parent observed that current `src/` is older than the final implementation
  state described in `Plan_N0014.log.md`.
- User then clarified the immediate goal: complete `Plan_N0015` in a shape that
  fits current repo truth before implementation.

## 2026-06-06 Sub-Agent Review

- Read-only review sub-agent returned blocking findings:
  - current code still uses yfinance latest-row behavior and lacks N0014
    temporal metadata;
  - guidance contexts still alias full `FinancialMetrics` as
    `guidance_consensus_deltas`;
  - SEC ingestion only runs when no sections exist;
  - presentation routing is still heading/section-id based;
  - report output lacks `Data Quality Flags` and availability-status filtering.
- Implementation sub-agent was interrupted after the user clarified the task
  should be plan completion first. It confirmed `src`/`tests` diff was empty
  and returned read-only plan guidance:
  - make N0014 baseline reconciliation Phase 0;
  - keep contract fields additive/defaulted;
  - implement deterministic presentation tagging and pure reconciliation before
    broad external acquisition changes;
  - keep revenue consensus optional and unsupported sources out of missing
    failures;
  - keep real network and LLM verification behind human gates.
- Parent accepted those findings and incorporated them into the revised plan.

## 2026-06-06 Plan Revision

- Added plan frontmatter required by `Plan/README.md`.
- Reframed the plan from an ideal full implementation spec into an
  implementation-ready, current-repo-aligned execution plan.
- Added Phase 0 to restore N0014 temporal safety before N0015 work.
- Preserved the current normalized API boundary for `POST /reviews`.
- Made SEC XBRL/company-facts coverage non-blocking for the first slice while
  keeping SEC filing text and explicit filing URL behavior in scope.
- Added explicit human review focus for default profile, SEC strictness, public
  schema compatibility, and real LLM provider execution.
- Reordered implementation phases so additive contracts, deterministic tagging,
  and pure reconciliation precede larger yfinance/SEC acquisition changes.

## 2026-06-06 Verification

- `python - <<'PY' ...`: passed.
  - Confirmed `Plan_N0015` plan frontmatter, log frontmatter, and
    `Plan/system-improvement/index.yaml` entry agree on plan ID, project ID,
    status, plan path, and log path.
- `rg -n "[[:blank:]]$" Plan/system-improvement/plans/Plan_N0015.md Plan/system-improvement/logs/Plan_N0015.log.md Plan/system-improvement/index.yaml`:
  passed; no trailing whitespace matches.
- `git diff -- src tests`: passed; no implementation or test diff remains
  after switching the task back to plan completion.
- `uv run --active pytest -q tests/test_foundation_integrity.py -k plan_project_records_keep_plan_id_log_and_index_in_sync`:
  passed, `1 passed`, `30 deselected`.

## 2026-06-06 Execution

- User requested execution of `Plan_N0015` with parent-agent coordination,
  sub-agent implementation, review, integration, and result reporting.
- Parent used the updated current-repo-aligned plan as the execution contract.
- Review sub-agent (`Gibbs`) ran read-only inspection and confirmed the same
  priority risks:
  - missing N0014 temporal baseline;
  - full `FinancialMetrics` aliasing in guidance delta contexts;
  - SEC fetch only when no sections exist;
  - heading-only presentation routing;
  - missing `Data Quality Flags` and availability filtering.
- Implementation sub-agent (`Copernicus`) produced a bounded router/report
  implementation candidate for:
  - body keyword presentation tagging and role routing;
  - removal of full-metrics guidance delta aliases in `ContextRouter`;
  - `Data Quality Flags`;
  - out-of-contract missing-data filtering.
- Parent integrated the sub-agent candidate, added workflow fallback/API/CLI
  propagation, restored yfinance target-date behavior, added additive contract
  models, and added reconciliation safeguards.

## 2026-06-06 Implementation Summary

- Added additive input contract models and metadata:
  - `InputProfile`;
  - `AvailabilityStatus` / `AvailabilityItem`;
  - `MetricPeriodRole`;
  - metric, guidance, presentation candidate, conflict, tagged-section, and
    agent-input models;
  - provider row/column dates and period role metadata on source refs and
    manifest entries.
- Restored temporal safety for yfinance:
  - EPS rows are selected only by `target_earnings_date`;
  - financial/cash-flow columns are selected only by `target_period_end_date`;
  - missing target dates produce `period_unverified` availability instead of
    promoting latest rows.
- Updated local normalization and workflow ingestion:
  - `use_sec=True` plus an explicit `filing_url` appends SEC sections even when
    presentation/manual sections already exist;
  - target-period-only document metadata is rejected when it conflicts with the
    request fiscal period;
  - normalized API boundary remains in place.
- Updated routing:
  - presentation/body keyword tags drive routing before fallback headings;
  - `GuidanceAnalyst` receives explicit guidance input structure and empty
    deltas unless explicit deltas exist;
  - both router and workflow fallback no longer alias full `FinancialMetrics`
    into `guidance_consensus_deltas` or `consensus_deltas`.
- Added report behavior:
  - `Data Quality Flags` renders before `Uncertainty And Missing Data`;
  - missing transcript/news/analyst-report/unsupported press-release gaps are
    filtered out of reportable missing failures;
  - prompt evidence policy was synchronized with new `ReportMatrix`,
    `MissingDataItem`, and `SourceRef` fields.
- Added reconciliation safeguards:
  - FCF derived from CFO and CapEx records component metric IDs and component
    source refs;
  - presentation actual candidates that conflict with canonical actuals beyond
    metric thresholds are retained as conflicting candidates and recorded as
    `MetricConflict`.

## 2026-06-06 Execution Verification

- `uv run --active pytest -q tests/test_preprocessor.py tests/test_workflow_models.py tests/test_context_router.py tests/test_report_renderer.py`:
  passed, `55 passed` before later reconciliation additions.
- `uv run --active pytest -q tests/test_workflow_api.py tests/test_cli_smoke.py tests/test_workflow_e2e.py tests/test_api_contract.py tests/test_api_smoke.py`:
  passed, `30 passed`, `1 warning`.
- `uv run --active pytest -q tests/test_workflow_api.py`:
  passed, `9 passed`, `1 warning`, after adding workflow fallback and SEC
  append tests.
- `uv run --active pytest -q tests/test_preprocessor.py tests/test_workflow_models.py tests/test_context_router.py tests/test_report_renderer.py tests/test_workflow_api.py tests/test_cli_smoke.py tests/test_workflow_e2e.py tests/test_api_contract.py tests/test_api_smoke.py`:
  passed, `89 passed`, `1 warning`, after reconciliation additions.
- `LLM_PROVIDER=fake uv run --active python -m src.main run --input-json samples/request.example.json --out /tmp/plan-n0015-cli.cSoPZl`:
  passed. Report output included `Data Quality Flags`, `Evidence Matrix`,
  `Source Appendix`, and `Disclaimer`; the legacy sample correctly reported
  `Period verification: unverified` and presentation tag coverage `no`.
- `LLM_PROVIDER=fake uv run --active python -m src.main run --input-json samples/request.current.local-presentation.example.json --out /tmp/plan-n0015-cli-presentation.2e1m7d`:
  initially exposed a fake-provider fallback bug for source refs, then passed
  after the fallback was changed to use available financial source refs when no
  non-financial refs are present. The output included tagged presentation
  source refs and guidance/management/cash_flow/risk coverage `yes`.
- `uv run --active pytest -q tests/test_cli_smoke.py`:
  passed, `4 passed`, after adding current local presentation CLI coverage.
- `uv run --active pytest -q`:
  passed, `233 passed`, `1 warning`.
- `uv run --active ruff format --check .`:
  passed, `49 files already formatted`.
- `uv run --active ruff check .`:
  passed, `All checks passed`.
- `uv run --active mypy src/workflow_models.py src/preprocessor.py src/context_router.py src/workflow.py src/report_renderer.py src/api.py src/main.py src/llm.py`:
  passed.
- `git diff --check`:
  passed.

## 2026-06-06 Gated Or Unverified

- No real LLM provider calls were run.
- No real yfinance or SEC network smoke was run.
- Full `uv run --active mypy .` was attempted and did not reach changed-code
  analysis because existing repo module-path duplication caused mypy to stop:
  `Source file found twice under different module names:
  "validate_agent_assets" and "scripts.validate_agent_assets"`.
- No merge, push, dependency change, CI/CD change, release, secret handling, or
  external write was performed.
