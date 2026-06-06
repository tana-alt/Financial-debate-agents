---
plan_id: Plan_N0014
project_id: system-improvement
status: draft
log_ref: Plan/system-improvement/logs/Plan_N0014.log.md
---

# Temporal Input Alignment And Future Leakage Prevention Plan

## 0. Goal

Make the workflow period-aware before real LLM evaluation relies on yfinance or
SEC financial data.

The workflow should give agents target-quarter earnings data and exactly one
prior-quarter comparison, while keeping PDFs/presentations target-period only.
Future snapshots, next-quarter estimates, and post-event information must not
silently enter target-quarter EPS surprise or P&L quality analysis.

The plan deliberately favors fields with high acquisition probability. It must
not make ideal-but-often-missing metrics the baseline path and then rely on
exception handling for ordinary runs.

## 1. Design Verdict

- `design_verdict`: proceed after contract-first implementation.
- `architecture_significance`: significant.
- `selected_option`: explicit temporal buckets, period-role source metadata,
  target-date-based yfinance row selection, and prompt/context rules that
  exclude future or latest-snapshot data from evidence.
- `human_gate_status`: public request schema changes and real LLM provider
  evaluation require user review before merge or attended execution.

## 2. Source Refs Used

```text
AGENTS.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
Plan/README.md
Plan/system-improvement/plans/Plan_N0013.md
Plan/system-improvement/logs/Plan_N0013.log.md
src/main.py
src/preprocessor.py
src/workflow.py
src/workflow_models.py
src/workflow_agents.py
src/prompts/shared/global_policy.md
src/prompts/shared/evidence_policy.md
src/prompts/financial/earnings_quality_analyst.md
src/prompts/presentation/guidance_analyst.md
```

## 3. Problem

The current workflow accepts a single flat `FinancialMetrics` object for a
requested `fiscal_period`. When `financial_metrics` is absent, the workflow
fetches yfinance data through `fetch_consensus()`. That function currently reads
the first row from `Ticker.earnings_dates`, which can be a future earnings date
instead of the requested quarter.

Observed on 2026-06-01:

- `GOOGL`, `MSFT`, and `NVDA` yfinance `earnings_dates` included both a future
  estimate-only row and past rows with reported EPS.
- The workflow selected the future row, so `eps_consensus` was populated while
  `eps` and `eps_surprise_pct` were missing.

This is not a yfinance availability problem. It is a temporal alignment problem.

## 4. Success Criteria

- CLI/API inputs can identify the target earnings event date.
- yfinance EPS actual, estimate, and surprise are selected from the row tied to
  the target event date, not from the first or latest row.
- Agents receive target-quarter actuals, one prior-quarter actual comparison,
  and pre-earnings consensus as separate buckets.
- P&L analysis is limited to observed quarter-over-quarter changes from
  obtainable actuals, such as revenue and other available P&L line items. It
  does not require revenue consensus.
- PDFs and presentations are accepted only as target-period documents unless a
  future plan explicitly introduces external research or multi-period document
  comparison.
- Latest/current snapshots are visible in `inspect-input` only when useful for
  audit, but are not routed as evidence to specialist, debate, or judge agents.
- Invalid temporal alignment fails preflight. Provider data that is correctly
  requested but unavailable becomes explicit warning and `missing_data`; it never
  silently falls back to a future or unrelated row.

## 5. Non-Goals

- Do not implement broad external analyst/news research.
- Do not use current market data, stock price, valuation, or target prices.
- Do not ask LLM agents to calculate EPS surprise, margins, or period deltas
  from raw tables.
- Do not require revenue consensus, margin consensus, detailed opex breakdown,
  tax-rate analysis, or share-count analysis for the MVP.
- Do not make SEC filings the primary source for non-GAAP/adjusted EPS
  surprise. SEC XBRL can supply GAAP actuals, but consensus still requires a
  separate pre-earnings source.
- Do not allow post-earnings guidance to stand in for pre-earnings consensus.

## 6. Sub-Agent Review Summary

Two read-only sub-agent reviews were run without file edits or real LLM provider
calls.

### Temporal Data Contract Review

Result: `REWORK`.

Findings:

- `fetch_consensus()` uses `earnings_dates.iloc[0]`, which can select a future
  row.
- `ReviewRequest` needs target event date, target period end date, prior fiscal
  period, and acquisition cutoff fields.
- Metrics need period roles and selection metadata.

### Prompt And Context Review

Result: `REWORK`.

Findings:

- Agent boundaries are directionally right, especially keeping EPS and P&L
  quality together in `EarningsQualityAnalyst`.
- Current flat metrics and missing source period roles cannot reliably prevent
  future information leakage.
- Prompts must explicitly distinguish actuals, prior actuals, pre-earnings
  consensus, post-earnings guidance, and latest snapshots.

## 7. Target Contract

### ReviewRequest Additions

```text
target_earnings_date: date | None
target_period_end_date: date | None
prior_fiscal_period: str | None
financial_data_as_of: date | None
document_period_policy: Literal["target_only"] = "target_only"
financial_period_policy: Literal["target_plus_prior"] = "target_plus_prior"
```

Rules:

- `target_earnings_date` is required when the CLI fetches yfinance EPS actual
  or consensus for a historical target quarter.
- `financial_data_as_of` defaults to the target earnings date for
  pre-earnings-consensus selection and to the current execution date only for
  audit-only latest snapshots.
- `prior_fiscal_period` may be derived for simple quarter decrement cases, but
  CLI must allow explicit override because fiscal years do not always align
  with calendar quarters.

### SourceRef Temporal Metadata

Extend source references with explicit period metadata.

```text
fiscal_period: str | None
period_role:
  reported_period_actuals
  prior_period_actuals
  pre_earnings_consensus
  post_earnings_guidance
  latest_snapshot
  target_period_document
published_date: date | None
data_cutoff_date: date | None
```

Rules:

- Every metric and document evidence source used by agents must have a
  `period_role`.
- `latest_snapshot` is not valid main-workflow evidence.
- PDF/presentation sections must have `period_role=target_period_document` and
  `fiscal_period == ReviewRequest.fiscal_period`.

### DocumentFile And DocumentSection

Add period metadata to documents.

```text
DocumentFile
  path
  source_type
  document_id
  title
  fiscal_period
  published_date
  period_role: Literal["target_period_document"]
```

Rules:

- A presentation/PDF whose declared `fiscal_period` differs from the request is
  rejected under `document_period_policy=target_only`.
- If `published_date` is present and after the allowed target-document window,
  ingestion fails or excludes the document before agents see it.

### PeriodMetricSnapshot

Introduce a wrapper instead of overloading one flat `FinancialMetrics`.

```text
PeriodMetricSnapshot
  bucket:
    reported_period_actuals
    prior_period_actuals
    pre_earnings_consensus
    post_earnings_guidance
    latest_snapshot
  ticker
  fiscal_period
  period_end_date
  earnings_date
  as_of_date
  source_provider: yfinance | sec | manual | derived
  source_row_date
  source_table_column_date
  selection_method:
    earnings_date_exact
    earnings_date_window
    period_end_exact
    provider_column_date_window
    latest_at_or_before_cutoff
    manual
  allowed_for_evidence
  metrics
  source_refs
  warnings
```

### FinancialMetricsBundle

```text
FinancialMetricsBundle
  reported_period_actuals: PeriodMetricSnapshot
  prior_period_actuals: PeriodMetricSnapshot | None
  pre_earnings_consensus: PeriodMetricSnapshot | None
  post_earnings_guidance: PeriodMetricSnapshot | None
  latest_snapshot: PeriodMetricSnapshot | None
```

Compatibility:

- Keep accepting the current flat `financial_metrics` shape during migration by
  wrapping it as `reported_period_actuals` with `selection_method=manual`.
- New CLI-generated samples should use the bundle shape once implemented.

### MVP Metric Coverage

The MVP should optimize for fields that are likely to exist in yfinance or SEC
XBRL and treat everything else as optional missing data.

High-probability fields:

```text
reported_period_actuals:
  eps
  revenue
  operating_cash_flow
  free_cash_flow
  capex

prior_period_actuals:
  eps
  revenue
  operating_cash_flow
  free_cash_flow
  capex

pre_earnings_consensus:
  eps_consensus
  eps_surprise_pct if supplied by the provider row
```

Optional fields:

```text
operating_margin_pct
gross_margin_pct
operating_income
opex
tax_rate
share_count
segment_metrics
revenue_consensus
revenue_surprise_pct
```

Rules:

- Revenue consensus is not required for the MVP and should not drive report
  quality or agent success.
- P&L quality should use target vs prior actuals where present. If only revenue
  is available, the agent may discuss revenue direction with a missing-data
  caveat instead of pretending margin or leverage evidence exists.
- Missing optional fields are normal missing data, not exceptional failures.
- Exception paths are reserved for invalid temporal alignment, future leakage,
  schema mismatch, or source-reference violations.

### Acquisition Outcomes

Use one deterministic rule per failure type.

Validation errors:

- `target_earnings_date` is missing when automatic yfinance EPS acquisition is
  requested.
- A source row or document is selected for a different fiscal period than the
  request while claiming to be target-period evidence.
- A future or latest snapshot would be substituted for the target period.
- A PDF/presentation violates `document_period_policy=target_only`.
- A supplied metric bucket has mismatched ticker, fiscal period, or period role.

Warnings and `missing_data`:

- yfinance has no matching target earnings row after valid target-date
  selection.
- yfinance has a target EPS row, but one or more values such as `Reported EPS`,
  `EPS Estimate`, or `Surprise(%)` are null.
- yfinance has no matching target or prior P&L table column after deterministic
  period matching.
- Optional P&L fields such as margin, opex, tax rate, share count, or revenue
  consensus are absent.

CLI/API behavior:

- `inspect-input` should complete with temporal warnings unless the request is
  structurally invalid or would cause future leakage.
- `run` may continue with missing EPS/P&L values only when the context still has
  valid target-period source material; agents must record the missing metrics.
- A future strict flag such as `--require-financial-data` may turn provider
  missing warnings into errors, but that is not the MVP default.

## 8. yfinance Acquisition Policy

Selected MVP behavior:

- Use yfinance as the primary source for EPS actual, EPS estimate, and
  `Surprise(%)` when the target row is identified by `target_earnings_date`.
- Use yfinance quarterly financial/cash-flow tables only when the target and
  prior columns can be selected by `target_period_end_date` or a deterministic
  period-end match. Do not use the first column as a target-period proxy.
- Record both `period_end_date` and `source_table_column_date`. yfinance table
  columns can use fiscal month-end dates that differ from exact SEC fiscal
  period end dates.
- Select the exact `earnings_dates` row when the row date matches
  `target_earnings_date`.
- Allow a small deterministic date window only when configured and surfaced as
  `selection_method=earnings_date_window`.
- Never use `earnings_dates.iloc[0]` as a target-period row.
- If no row matches, return missing EPS metrics with a warning; do not silently
  substitute a future row.
- Select one prior-quarter row separately for `prior_period_actuals`.
- If a P&L table column cannot be matched to the target or prior period, leave
  the relevant metrics missing and surface a provider warning.
- If `source_table_column_date` is matched by a configured window rather than an
  exact date, set `selection_method=provider_column_date_window` and include the
  provider column date in `inspect-input`.

Provider caveat:

- yfinance does not guarantee a full historical consensus snapshot with precise
  analyst as-of metadata. Treat `EPS Estimate` as a provider-supplied earnings
  date row estimate, not official company data.
- If a stronger consensus source is added later, it can populate
  `pre_earnings_consensus` with better `as_of_date` precision.

## 9. SEC Acquisition Policy

Selected behavior:

- SEC HTML filing sections remain useful for official filing text, risk, MD&A,
  and source-backed qualitative context.
- SEC XBRL can later fill GAAP actuals such as diluted/basic EPS, revenue, and
  cash-flow metrics.
- SEC does not provide analyst consensus, so SEC actuals alone must not create
  EPS beat/miss or surprise claims.
- If SEC GAAP actuals and yfinance consensus are both present, the workflow must
  mark the basis explicitly before any comparison is allowed:
  - `actual_basis=gaap`
  - `consensus_provider=yfinance`
  - `comparison_basis_warning` when bases are not clearly aligned.

MVP priority:

1. Fix yfinance temporal row selection.
2. Add explicit temporal buckets and prompt/context enforcement.
3. Add SEC XBRL actual fallback only after the bucket contract is stable.

## 10. Agent Context Contract

### EarningsQualityAnalyst

Replace flat `earnings_quality_metrics` usage with explicit temporal context.

```text
earnings_quality_metrics
  reported_period_actuals
  prior_period_actuals
  pre_earnings_consensus
  disallowed_latest_snapshot
```

Rules:

- Use `reported_period_actuals` for target-quarter EPS, revenue, and margin
  claims.
- Use `prior_period_actuals` only for comparison or trend.
- Use `pre_earnings_consensus` only for beat/miss/surprise.
- Do not use `post_earnings_guidance` as target-quarter performance evidence.
- Do not use `latest_snapshot` as evidence.
- If EPS actual or consensus is missing, do not assess EPS surprise; record
  `missing_data` and analyze P&L quality only if actual P&L evidence exists.
- Revenue consensus is not expected. Do not discuss revenue beat/miss unless
  `revenue_consensus` is explicitly present.
- P&L trend claims must be limited to metrics available in both target and
  prior buckets, or clearly marked as single-period observations.

### GuidanceAnalyst

Use only:

```text
guidance_metrics
  post_earnings_guidance
  pre_earnings_consensus
guidance_sections
guidance_assumptions_sections
prior_guidance_track_record
```

Rules:

- Post-earnings guidance may support outlook analysis.
- Post-earnings guidance must not be used as pre-earnings expectation.
- Guidance sections must come from target-period documents.

### Debate And Judge Agents

Rules:

- They may only use specialist findings whose evidence source refs pass
  period-role validation.
- Evidence with `period_role=latest_snapshot` is invalid for main verdicts.

## 11. Prompt Updates

### Shared Prompt Policy

Add:

```text
Do not use latest_snapshot as evidence for target-period performance, surprise,
guidance quality, or verdict.

Consensus claims must come from pre_earnings_consensus and must not be later
than the target earnings event date unless explicitly marked as unavailable or
post-event.

Actual performance claims must use reported_period_actuals for the target
period. prior_period_actuals may be used only for trend/comparison.

Presentation/PDF sections are valid only when period_role is
target_period_document and fiscal_period equals RunSpec.fiscal_period.

Post-earnings guidance may support outlook analysis but must not be used as
pre-earnings expectations.
```

### EarningsQualityAnalyst Prompt

Add:

```text
Use reported_period_actuals for target-quarter EPS/revenue/margins.
Use prior_period_actuals only for comparison.
Use pre_earnings_consensus only for beat/miss/surprise.
If EPS actual or consensus is missing, do not discuss EPS surprise as known.
Do not discuss revenue beat/miss unless revenue_consensus is explicitly present.
If only revenue actuals are available for P&L, limit analysis to revenue trend
and put missing margin/leverage data in missing_data.
Ignore latest_snapshot for evidence.
```

### GuidanceAnalyst Prompt

Add:

```text
Use post_earnings_guidance only as company guidance issued with the target
quarter materials. Use pre_earnings_consensus only when evaluating whether
guidance is above, below, or in line with expectations.
```

## 12. CLI Contract

Add flags for `run` and `inspect-input` payload generation.

```text
--target-earnings-date YYYY-MM-DD
--target-period-end-date YYYY-MM-DD
--prior-fiscal-period YYYYQ#
--financial-data-as-of YYYY-MM-DD
--financial-period-policy target-plus-prior
--document-period-policy target-only
--document-fiscal-period YYYYQ#
--document-published-date YYYY-MM-DD
```

Rules:

- `--target-earnings-date` is required when using CLI acquisition from yfinance
  without explicit `financial_metrics`.
- `--document-fiscal-period` defaults to request `fiscal_period` for local
  documents only if omitted; inspect output must show the default explicitly.
- The CLI should emit a clear warning when yfinance cannot find a target row and
  must not substitute another row.
- The CLI should emit an error only for invalid temporal metadata, future
  leakage, schema mismatch, or an explicit strict/require-financial-data mode.

## 12.1 API Contract

The public API currently validates requests through `ReviewRequest`. Because
this plan changes request shape, implementation must include API-boundary
behavior.

Rules:

- API requests with invalid temporal metadata, mismatched metric bucket roles,
  or non-target documents return validation errors.
- API responses must not expose stack traces or provider internals for temporal
  validation failures.
- During migration, legacy flat `financial_metrics` remains accepted only as a
  manual `reported_period_actuals` compatibility path.
- Raw acquisition behavior must be explicit. If server-side yfinance acquisition
  remains enabled during migration, `target_earnings_date` is required when
  `financial_metrics` is absent.

## 13. Inspect Output

Extend `inspect-input` with:

```text
temporal_input_summary.json
metric_snapshots.json
temporal_source_manifest.json
temporal_validation.json
```

Minimum audit fields:

- target earnings date
- target period end date
- prior fiscal period
- financial data cutoff
- selected yfinance row dates
- selected yfinance table column dates
- bucket names
- provider warnings
- excluded latest snapshots
- document fiscal period and published date

## 14. Verification Plan

### Unit Tests

- yfinance fake `earnings_dates` with future, target, and prior rows selects the
  target row by `target_earnings_date`.
- The same fixture selects the prior-quarter row separately.
- yfinance fake quarterly financial/cash-flow tables select target and prior
  columns by period end, not by first column.
- yfinance table-column matching records `source_table_column_date` separately
  from `period_end_date`.
- Missing target/prior P&L columns produce explicit warnings and missing fields,
  not fallback to unrelated columns.
- Future estimate-only row is never selected for a historical target quarter.
- Missing target yfinance row returns explicit warning and missing EPS fields,
  while invalid temporal metadata returns a validation error.
- `ReviewRequest` rejects mismatched metric bucket ticker, fiscal period, or
  period role.
- `DocumentFile` and `DocumentSection` reject non-target fiscal periods under
  `target_only`.
- `pre_earnings_consensus.as_of_date > target_earnings_date` is rejected or
  excluded.

### Context And Prompt Tests

- `_build_agent_context()` includes temporal buckets for
  `EarningsQualityAnalyst`.
- Specialist contexts do not include `latest_snapshot` as an evidence source.
- Prompt golden tests confirm temporal rules appear in shared policy and
  `EarningsQualityAnalyst`.
- Fake LLM output citing `latest_snapshot` fails source/evidence validation.

### CLI And Inspect Tests

- `inspect-input` emits temporal audit files without LLM calls.
- CLI-generated payload includes target earnings date, prior fiscal period,
  yfinance selected row metadata, and document period metadata.
- Existing flat `financial_metrics` samples remain backward compatible during
  migration.

### API Boundary Tests

- API accepts the migrated temporal request shape.
- API accepts legacy flat `financial_metrics` only through the manual
  compatibility path.
- API returns validation errors for mismatched fiscal period, period role,
  target-only document violations, and future-leakage source refs.
- API smoke tests cover successful request validation and temporal validation
  failure shape.

### Non-LLM Real Data Tests

- Run `inspect-input` for at least three real companies with:
  - target PDF/presentation,
  - yfinance target and prior rows,
  - no real LLM provider call.
- Confirm EPS actual, EPS estimate, and surprise are populated for historical
  target quarters when yfinance has the target row.
- Confirm target/prior revenue and cash-flow actuals are populated when
  yfinance period columns match.
- Confirm missing values are surfaced when the target row is unavailable.
- Confirm revenue consensus remains absent without failing the workflow.

### Real LLM Tests

- Keep real LLM provider tests serial and user-attended.
- Run one company first, inspect evidence source refs and missing-data caveats,
  then proceed to two or three companies only if the first report is clean.

## 15. Execution Order

1. Contract and schema models.
2. yfinance row selector and CLI flags.
3. Temporal document metadata and validation.
4. Context builder migration.
5. Prompt updates.
6. Report/source validation for period roles.
7. Inspect-output extension.
8. Non-LLM real-data regression.
9. User-attended real LLM serial validation.

## 16. Residual Risks

- yfinance historical consensus semantics may not be precise enough for strict
  as-of claims.
- SEC XBRL fallback for GAAP actuals is useful but does not solve adjusted EPS
  or consensus.
- Some company PDFs may not clearly state fiscal period or publication date in
  machine-readable form; CLI may need explicit metadata from the user.
- Backward compatibility with existing flat samples must be temporary and
  documented so old samples do not hide temporal ambiguity.
