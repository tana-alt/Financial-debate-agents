# Plan_N0024: Japanese reader report with canonical data premise

## Goal

Restore the final Markdown report as a Japanese reader-facing earnings review
while preserving the current source-forward validation model.

## Scope

- Add a report premise section that lists the canonical data used by the report.
- Keep SEC, yfinance, and derived metrics as canonical report premises.
- Keep presentation-derived values supplementary; do not present them as
  canonical premises.
- Make final Markdown headings, fixed labels, and no-advice framing Japanese.
- Instruct runtime LLM agents to write natural-language JSON fields in
  Japanese while keeping schema keys, enums, IDs, metric names, and source IDs
  unchanged.
- Reuse existing rich Bull/Bear/Judge structured fields in the deterministic
  report instead of only showing compact debate summaries.
- Update focused report/prompt/API/CLI tests and run verification.

## Acceptance

- Final Markdown starts with a Japanese report premise section for canonical
  data before the main narrative.
- Canonical premise rows come from `financial_metrics.canonical_metrics` and
  `financial_metrics.derived_metrics`, not presentation candidates.
- Bull/Bear/Judge detailed fields appear in the reader-facing sections when
  available.
- Existing evidence matrix, source appendix, quality gate, and missing-data
  traceability remain visible.
- Runtime prompts explicitly require Japanese natural-language fields.
- Focused tests and relevant CLI/API smoke tests pass.

## Constraints

- Do not call real LLM APIs for this implementation pass.
- Do not revert unrelated dirty worktree changes.
- Keep API response schemas compatible; this plan changes Markdown content and
  renderer inputs only.
- Use subagents for implementation and review; parent agent owns integration.

## Status

Completed on 2026-06-07. See
`Plan/system-improvement/logs/Plan_N0024.log.md` for implementation,
cross-review, CLI verification, and test results.
