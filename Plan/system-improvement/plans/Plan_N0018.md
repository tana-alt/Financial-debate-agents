---
plan_id: Plan_N0018
project_id: system-improvement
status: completed
created_at: 2026-06-06
owner: parent-agent
log_ref: Plan/system-improvement/logs/Plan_N0018.log.md
---

# Plan_N0018: Three-Period Canonical Metric Contract

## Goal

Promote canonical current, previous-quarter, and year-ago-quarter metrics into
the explicit input contract so workflow agents can evaluate trends without
treating unavailable auxiliary data as missing.

## User Requirements

- Make previous-quarter and year-ago-quarter data required for canonical metrics.
- Keep auxiliary data optional/reference-only.
- Only canonical required metric gaps should create missing/cap behavior.
- Instruct agents to lower confidence only for canonical required gaps.
- Do not lower confidence for missing presentation, transcript, consensus, or
  other auxiliary data.
- Use sub-agents for execution review and cross-review.
- Verify with real yfinance and SEC data for representative tickers, including
  NVDA and ZS.

## Scope

- Extend metric period roles to distinguish current, previous quarter, and
  year-ago quarter.
- Expand expected metric registry to express required canonical metrics per
  period.
- Fetch and normalize SEC Company Facts revenue, operating cash flow, and capex
  for current, previous-quarter, and year-ago periods.
- Fetch yfinance EPS for current, previous-quarter, and year-ago earnings rows.
- Derive free cash flow per period from canonical OCF and CapEx.
- Keep consensus, presentation, transcript, guidance text, and other auxiliary
  data out of missing/cap logic.
- Add prompt and renderer guards so out-of-contract or auxiliary gaps do not
  appear as confidence-limiting missing data.

## Non-Goals

- Real LLM/provider execution.
- Making presentation metrics canonical.
- Making consensus estimates required.
- Broad financial statement expansion beyond the current canonical metric set.
- Investment advice, valuation, price target, or trading recommendation output.

## Acceptance Criteria

- Current, previous-quarter, and year-ago canonical metrics are available to
  agents with readable period roles.
- Required canonical metrics are:
  revenue, eps, operating_cash_flow, capex, and free_cash_flow for each required
  period.
- Missing/cap logic counts only required canonical gaps.
- Auxiliary data gaps do not create missing/cap behavior and do not instruct
  agents to lower confidence.
- Tests cover period-role availability, SEC/yfinance multi-period selection,
  derived FCF per period, prompt guard text, and report filtering.
- Real-data CLI checks pass for NVDA and ZS, plus representative peers, or
  explain genuine ticker-specific canonical gaps.

## Sub-Agent Plan

- Agent A: inspect expected metric and workflow contract changes needed for
  three-period canonical inputs.
- Agent B: inspect SEC/yfinance acquisition risks and period matching edge cases.
- Parent: implement, integrate, verify, and report.

## Result

- Implemented three-period canonical metric requirements.
- Verified NVDA, ZS, AAPL, MSFT, and META through non-LLM CLI with real
  yfinance and SEC Company Facts acquisition.
- Cross-review findings were integrated, including compact canonical-period
  inputs for non-financial agents and yfinance earnings-date tolerance.
