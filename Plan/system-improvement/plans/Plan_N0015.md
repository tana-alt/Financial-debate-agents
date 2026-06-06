---
plan_id: Plan_N0015
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0015.log.md
---

# yfinance + SEC + Tagged Presentation Input Contract Plan

## 0. Goal

Bring the earnings review workflow to a realistic three-source input contract:

1. `yfinance` for obtainable market and financial API metrics.
2. `SEC` for official filing text and, when implemented safely, canonical
   reported actuals.
3. `presentation` for management commentary, outlook, guidance, assumptions,
   capital allocation, and risk evidence.

No transcript, analyst report, news, web search, price target, or stock
recommendation source is added by this plan.

This plan is intentionally aligned to the current repository state. It does
not assume the `Plan_N0014` implementation recorded in the log is already
present in `src/`; the current code still has the older `fetch_consensus()`
and heading-based routing behavior. The first implementation step must restore
the reviewed `Plan_N0014` temporal baseline before adding this contract.

## 1. Design Verdict

- `design_verdict`: proceed after Phase 0 baseline repair.
- `architecture_significance`: significant.
- `selected_option`: additive normalized-input contract plus deterministic
  acquisition, tagging, reconciliation, routing, and report-quality metadata.
- `compatibility`: preserve `POST /reviews` as a normalized-input endpoint;
  keep local CLI/raw acquisition normalization outside the API boundary.
- `human_gate_status`: public request schema changes require human review
  before merge; real LLM provider execution remains user-attended; external
  yfinance/SEC smoke runs are optional and must be non-LLM.

## 2. Source Refs Used

```text
AGENTS.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
docs/reference/git-worktree-and-branch-reference.md
docs/reference/verification-ci-and-pr-reference.md
docs/reference/packet-evidence-and-rework-reference.md
Plan/README.md
Plan/system-improvement/plans/Plan_N0015.md
Plan/system-improvement/logs/Plan_N0014.log.md
Plan/system-improvement/logs/Plan_N0013.log.md
src/workflow_models.py
src/preprocessor.py
src/context_router.py
src/workflow.py
src/report_renderer.py
src/api.py
src/main.py
tests/test_workflow_models.py
tests/test_preprocessor.py
tests/test_context_router.py
tests/test_report_renderer.py
```

## 3. Current Repo Reality

Current `src/` is not at the state described by the final `Plan_N0014.log.md`
implementation section:

- `ReviewRequest` lacks `target_earnings_date`, `target_period_end_date`,
  `prior_fiscal_period`, and related temporal policy fields.
- `SourceRef` and `SourceManifestEntry` lack period-role and provider date
  metadata needed to validate yfinance rows or SEC filing facts.
- `fetch_consensus()` still uses `earnings_dates.iloc[0]`, so a future
  estimate-only row can be selected as the target quarter.
- `ContextRouter` and the workflow fallback route still pass full
  `FinancialMetrics` as `guidance_consensus_deltas`.
- SEC filing ingestion currently runs only when no document sections exist.
- Presentation routing is still based on `section_id` and `heading`, not body
  tags.
- `ReportRenderer` has no `Data Quality Flags` section and missing data is not
  availability-status based.

These are not implementation details to ignore. They define the execution
order and acceptance criteria for this plan.

## 4. Review Feedback Incorporated

### User Review From Plan_N0014

- Revenue consensus is not required for the MVP. Treat it as optional missing
  data when yfinance does not provide it.
- Missing provider values are warnings and report caveats, not default errors.
- Fail only invalid temporal alignment, future leakage, schema mismatch,
  target-only document violations, source-reference violations, or explicit
  strict-mode failures.
- Keep presentations target-period only.
- Keep real LLM provider tests serial and user-attended.

### Sub-Agent Review For Plan_N0015

Read-only sub-agent reviews returned these blocking risks:

- restore `Plan_N0014` temporal safety before adding N0015 behavior;
- remove full `FinancialMetrics` aliasing in guidance delta contexts;
- fetch SEC when requested without replacing presentation sections;
- route presentation by deterministic body tags instead of headings only;
- add report-level data quality flags and availability-status filtering.
- keep new contract fields additive/defaulted until implementation tests prove
  migration safety;
- add deterministic models, taggers, and reconciliation pure functions before
  broad external acquisition changes.

This plan treats those findings as required scope.

## 5. API Contract

`POST /reviews` remains the public API endpoint.

- Auth: unchanged; no auth added.
- Request body: still `NormalizedReviewRequest`.
- Raw acquisition fields remain rejected at the API boundary.
- Response envelopes remain:
  - `ReviewSuccessResponse`
  - `ReviewDryRunResponse`
  - `ReviewErrorResponse`
- Error category and status behavior remain compatible unless a new validation
  failure is explicitly tied to source manifest, context budget, or input
  contract.

Additive normalized fields may be introduced on `NormalizedReviewRequest` and
`FinancialMetrics` only when they have deterministic local population and
tests. The local CLI/preprocessor may continue to accept raw acquisition
fields such as `filing_url`, `document_files`, `local_path`, and `raw_text`
before converting them into normalized API input.

## 6. Input Profile Contract

Add:

```python
class InputProfile(str, Enum):
    YFINANCE_ONLY = "yfinance_only"
    YFINANCE_SEC = "yfinance_sec"
    YFINANCE_PRESENTATION_TAGGED = "yfinance_presentation_tagged"
    YFINANCE_SEC_PRESENTATION_TAGGED = "yfinance_sec_presentation_tagged"
```

Default profile:

```python
InputProfile.YFINANCE_SEC_PRESENTATION_TAGGED
```

`yfinance_only` is degraded mode. It may run when SEC/presentation inputs are
unavailable, but the report must say which evidence is unavailable under the
chosen profile.

Profile behavior:

| Profile | yfinance | SEC | Presentation tags |
|---|---:|---:|---:|
| `yfinance_only` | yes | no | no |
| `yfinance_sec` | yes | yes | no |
| `yfinance_presentation_tagged` | yes | no | yes |
| `yfinance_sec_presentation_tagged` | yes | yes | yes |

## 7. Temporal Baseline Requirement

Phase 0 must restore the `Plan_N0014` safety properties before N0015 work:

- yfinance EPS rows are selected by `target_earnings_date` when supplied.
- yfinance financial/cash-flow columns are selected by
  `target_period_end_date` when supplied.
- missing matching provider rows never fallback to the first/latest row.
- provider row/table dates are represented in source metadata or metric
  metadata.
- latest/future snapshots are either rejected or kept audit-only, never routed
  as agent evidence.
- document files and presentation sections remain target-period only.

If a target date is absent, mark `period_unverified`; do not silently use the
latest row as a target-period actual.

## 8. Source Roles

### yfinance

Use for:

- EPS actual, estimate, and surprise only when target event date is verified.
- revenue and cash-flow statement snapshots only when target period-end date is
  verified.
- optional consensus estimates when available.

Do not use for:

- company guidance text;
- management intent;
- one-time item explanations;
- SEC-only filing facts;
- unsupported sell-side or news commentary.

### SEC

Use for:

- filing text sections such as risk, MD&A, liquidity, segment discussion, and
  official filing context;
- canonical reported actuals only when the implementation has a deterministic
  SEC/XBRL or statement extraction path with metric-level source refs.

SEC should be fetched when `use_sec=True` and a `filing_url` or validated SEC
locator is present, even if presentation sections already exist. Do not make
implicit CIK lookup or latest-filing discovery a default requirement for this
plan; if no SEC locator is available, record `sec_unavailable`.

### Presentation

Use as the primary source for:

- management intent;
- outlook and guidance;
- assumptions;
- strategy;
- demand and supply commentary;
- capital allocation;
- risk commentary;
- explicit GAAP/non-GAAP reconciliation and one-time item explanation.

Presentation-derived numbers start as candidates. They are not canonical
reported actuals unless period, unit, definition, and source role are verified.

## 9. Core Models To Add

Add models in `src/workflow_models.py` with strict validation and source-ref
discipline:

- `InputProfile`
- `AvailabilityStatus`
- `AvailabilityItem`
- `MetricPeriodRole`
- `MetricValue`
- `DerivedMetricValue`
- `GuidanceMetric`
- `GuidanceDelta`
- `PresentationTag`
- `TaggedPresentationSection`
- `PresentationMetricCandidateStatus`
- `PresentationMetricCandidate`
- `MetricConflict`
- agent-specific input models:
  - `EarningsQualityInputs`
  - `CashFlowRiskInputs`
  - `ManagementIntentInputs`
  - `GuidanceInputs`

Model rules:

- every metric has a metric-level `SourceRef`;
- derived metrics have component metric IDs and component source refs;
- `GuidanceDelta` is created only when both company guidance and matching
  consensus exist;
- `not_in_contract` and `out_of_scope_source_policy` availability items do not
  block verdicts and do not cap confidence.

## 10. Metric Reconciliation

Canonical selection priority:

1. SEC XBRL or validated filing statement facts for reported actuals.
2. yfinance verified-period financial metrics.
3. presentation metric candidates for guidance/supporting evidence only.
4. derived metrics with component refs.

Conflict key:

```text
ticker + fiscal_period + metric_name + period_role
```

Default thresholds:

| Metric type | Threshold |
|---|---:|
| EPS | 2% |
| revenue | 2% |
| FCF / CFO / CapEx | 5% |
| margin | 100 bps |
| cash / debt | 5% |

SEC/yfinance conflicts use the highest-priority source by default and record a
conflict. SEC/yfinance versus presentation actual conflicts must not promote
the presentation value to canonical actual.

NVDA acceptance: the same reported period must not retain both FCF `12.0B` and
FCF `48.6B` as canonical. The presentation value must be either
`conflicting_with_canonical`, reclassified to a different period/definition, or
left as an ambiguous candidate.

## 11. Presentation Tagging And Routing

Implement deterministic keyword tagging over section body text and heading.
Do not rely on heading alone.

Minimum tags:

```text
actuals, pnl, cash_flow, balance_sheet, segment, guidance, outlook,
assumptions, management, strategy, demand, supply, capital_allocation, risk,
gaap_non_gaap_reconciliation, one_time_items
```

Routing rules:

- `GuidanceAnalyst`: `guidance`, `outlook`, `assumptions`.
- `ManagementIntentAnalyst`: `management`, `strategy`, `demand`, `supply`,
  `capital_allocation`.
- `CashFlowRiskAnalyst`: `cash_flow`, `balance_sheet`, `capital_allocation`,
  `risk`, plus SEC liquidity sections.
- `EarningsQualityAnalyst`: `actuals`, `pnl`, `segment`,
  `gaap_non_gaap_reconciliation`, `one_time_items`.

Generic PDF page headings such as `page 5` must route correctly when body text
contains guidance or management signals.

## 12. Guidance Contract

Replace both existing full-metrics aliases:

- `ContextRouter`: no `guidance_consensus_deltas = metrics_json`.
- `ReviewWorkflow._build_agent_context` fallback: no
  `guidance_consensus_deltas = metrics_json`.

`GuidanceInputs` contains:

- `company_guidance: list[GuidanceMetric]`
- `consensus_estimates: list[MetricValue]`
- `guidance_deltas: list[GuidanceDelta]`
- `presentation_sections: list[TaggedPresentationSection]`
- `sec_sections: list[DocumentSection]`
- `availability: list[AvailabilityItem]`

If company guidance exists and consensus is absent, guidance deltas are empty
and availability records consensus as optional missing or yfinance unavailable.
If consensus exists and company guidance is absent, guidance deltas are empty
and availability records guidance/tag absence. Do not fabricate deltas.

## 13. Report Behavior

Add `Data Quality Flags` before `Uncertainty And Missing Data`:

```markdown
## Data Quality Flags

- Input profile: yfinance_sec_presentation_tagged
- Period verification: verified / partial / unverified
- Metric conflicts: none / listed
- Guidance delta status: computed / company_guidance_missing / consensus_missing
- Presentation tag coverage: guidance=yes, management=yes, cash_flow=yes, risk=yes
```

Missing data output should show:

- missing required items;
- unresolved conflicts;
- period-unverified flags;
- presentation extraction failures;
- unavailable guidance deltas due to missing company guidance or consensus.

Do not show:

- transcript missing;
- analyst report missing;
- news missing;
- unsupported press release missing;
- generic missing items outside the active source contract.

## 14. Implementation Order

### Phase 0: Restore Temporal Baseline

Files:

```text
src/workflow_models.py
src/preprocessor.py
src/workflow.py
src/context_router.py
src/main.py
tests/test_preprocessor.py
tests/test_workflow_models.py
tests/test_context_router.py
tests/test_cli_smoke.py
tests/test_workflow_api.py
```

Tasks:

- add target event and period metadata;
- stop `earnings_dates.iloc[0]` target fallback;
- validate source/provider dates;
- reject or audit-only latest/future snapshots;
- preserve current normalized API boundary.

### Phase 1: Contract-Only Additive Models

- add input profile and availability models;
- add metric/guidance/presentation/agent input models;
- add metric-level source refs and derived component refs;
- keep old `FinancialMetrics` fields as compatibility summary fields until all
  agents are migrated.

### Phase 2: Deterministic Presentation Tagging

- keep `DocumentSection` as the existing ingestion output;
- add tagged presentation sections as an additional normalized output;
- route by tags first and keep heading heuristics only as fallback;
- extract presentation metric candidates without promoting them.

### Phase 3: Pure Normalization And Reconciliation

- normalize metric names, units, period roles, and source priority;
- compute derived FCF and ratios only from component refs;
- detect conflicts and pick canonical metrics;
- keep ambiguous presentation numbers as candidates.

### Phase 4: Routing And Report Integration

- replace broad metrics context with agent-specific input models;
- route presentation by tags and SEC sections by typed headings;
- remove `guidance_consensus_deltas = metrics_json` in both router paths.
- add `Data Quality Flags`;
- filter missing data by availability status.

### Phase 5: yfinance And SEC Acquisition

- replace `fetch_consensus()` implementation with `fetch_yfinance_bundle()`;
- keep `fetch_consensus()` as a compatibility wrapper during migration;
- fetch SEC when `use_sec=True` and an explicit SEC locator exists, even when
  presentation sections exist;
- keep SEC CIK/latest-filing discovery out of default scope unless supplied;
- preserve success/dry-run/error response envelopes;
- update CLI inspect/dry-run outputs only if current CLI surfaces exist in the
  branch being implemented.

### Phase 6: Verification

Run focused tests first, then widen:

```text
uv run --active pytest -q tests/test_preprocessor.py tests/test_workflow_models.py tests/test_context_router.py tests/test_report_renderer.py
uv run --active pytest -q tests/test_workflow_api.py tests/test_cli_smoke.py tests/test_workflow_e2e.py
uv run --active ruff format --check .
uv run --active ruff check .
uv run --active pytest -q
git diff --check
```

Real LLM provider calls remain skipped unless the user explicitly approves the
provider, target companies, and run timing.

## 15. Required Tests

Add or update tests for:

- N0014 temporal baseline is restored before metric promotion;
- yfinance target event date selects the correct EPS row;
- yfinance missing target event date does not fallback to latest row;
- yfinance target period-end date selects the correct financial/cash-flow
  column;
- provider row/table date outside target window is rejected or marked
  period-unverified according to mode;
- latest/future snapshot metadata is not routed as agent evidence;
- SEC fetch runs with presentation sections present when `use_sec=True` and an
  explicit filing URL exists;
- presentation PDF/text sections preserve page source refs;
- body keyword tags route generic presentation headings to expected agents;
- guidance deltas are not aliases of full `FinancialMetrics`;
- presentation metric candidates are not promoted without period/unit/context;
- NVDA FCF `12.0B` versus `48.6B` creates one canonical metric and one
  conflict/candidate result;
- ZS Q3 actuals remain reported actuals while Q4/FY guidance remains future
  guidance;
- `not_in_contract` and `out_of_scope_source_policy` do not count as missing
  failures;
- metric refs are metric-level;
- derived metrics keep component source refs;
- `Data Quality Flags` render and unsupported source gaps do not render as
  missing failures.
- transcript, news, analyst report, and unsupported press release absence do
  not render as missing failures.

## 16. Non-Goals

Do not implement:

- transcript ingestion;
- analyst report ingestion;
- news/web search;
- stock recommendation logic;
- price target logic;
- OCR as the default PDF ingestion path;
- external consensus providers beyond yfinance;
- implicit latest SEC filing discovery without supplied CIK/accession policy;
- full SEC XBRL coverage as a blocking requirement for the first slice.

## 17. Acceptance Criteria

The implementation is accepted when:

- N0014 temporal safety is restored in current code.
- `POST /reviews` still accepts normalized input only.
- local CLI/preprocessor can produce normalized input for the selected profile.
- yfinance/SEC/presentation facts are not silently mixed without source role,
  period role, and conflict handling.
- guidance deltas are computed only from explicit company guidance and matching
  consensus.
- final report lists source profile, period verification, conflicts, guidance
  delta status, and presentation tag coverage.
- unsupported source gaps are treated as out of contract, not model failure.
- focused tests and the selected repo verification commands pass.

## 18. Human Review Focus

- Confirm that the default profile should be
  `yfinance_sec_presentation_tagged` even when SEC locator data is absent and
  represented as `sec_unavailable`.
- Confirm how strict the first implementation should be for SEC canonical
  reported actuals versus SEC filing-text supplementation.
- Confirm public request-schema compatibility before merge.
- Confirm real LLM provider smoke scope before any attended execution.

Human gate is not required for local contract-only models, deterministic pure
functions, and focused unit tests that do not perform external writes,
dependency changes, network verification, or public breaking changes.
