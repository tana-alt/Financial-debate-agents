---
plan_id: Plan_N0017
project_id: system-improvement
status: completed
created_at: 2026-06-06
owner: parent-agent
---

# Plan_N0017: Canonical Metric Source Management

## Goal

Implement centralized metric-source management for SEC Company Facts, yfinance,
and presentation-derived candidates so workflow agents receive readable,
contract-aligned inputs.

## User Requirements

- Normalize and fetch SEC data.
- Manage SEC, yfinance, and presentation data through one expected/canonical
  metric layer.
- Treat presentation metrics as auxiliary/reference material only.
- Do not make presentation metrics canonical.
- Do not warn, cap confidence, or lower confidence solely because presentation
  data is missing.
- Separate required, optional, unavailable, and out-of-contract metrics.
- Prevent missing/cap behavior when a metric is optional or cannot reasonably be
  present in the input contract.
- Verify with real data acquisition.

## Scope

- Add expected metric registry for agent-facing metric requirements.
- Add source policy for canonical, derived, consensus, and reference-only
  metrics.
- Add SEC Company Facts P0 metric normalization for revenue, operating cash
  flow, capex, and derived free cash flow.
- Keep yfinance as canonical financial-api source where period-verified.
- Keep presentation candidates as reference-only and non-cap.
- Route structured availability from canonical requirements, not raw prompt
  missing text.

## Non-Goals

- Real LLM/provider execution.
- Broad P1/P2 financial statement expansion beyond P0 unless needed by tests.
- Making presentation or transcript numeric claims canonical.
- Investment advice, valuation, price target, or trading recommendations.

## Acceptance Criteria

- Registry distinguishes required, optional, reference-only, and not-in-contract
  metrics by agent role.
- Missing/cap logic ignores presentation-only gaps and out-of-contract metrics.
- SEC Company Facts P0 metrics can be fetched and normalized from live data.
- yfinance and SEC canonical values reconcile for checked tickers, or differences
  are surfaced as structured conflicts.
- Derived FCF is computed from canonical OCF and capex component refs.
- Unit tests cover registry classification, presentation non-cap behavior, SEC
  direct-quarter and YTD normalization, and workflow cap integration.
- Real-data smoke checks NVDA and peers without unresolved P0 canonical gaps.

## Sub-Agent Plan

- Agent A: review expected metric registry shape and workflow integration risks.
- Agent B: review SEC Company Facts normalization edge cases and test matrix.
- Parent: implement, integrate, verify, and report.
