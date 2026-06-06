# Plan_N0025: Real LLM sample reports for NVDA and ZS

## Goal

Generate real LLM Markdown sample reports for NVDA and ZS with local PDF
presentation/shareholder-letter inputs included, inspect each output one by one,
and prepare the resulting samples for a separate PR.

## Scope

- Run NVDA first using the local NVDA F1Q27 quarterly presentation PDF.
- Inspect NVDA report and workflow result before proceeding.
- Run ZS second using the local FY2026 Q3 shareholder letter PDF.
- Inspect ZS report and workflow result before preparing a sample-output PR.
- Keep generated verification artifacts separate from the implementation PR.

## Constraints

- Use real LLM provider execution.
- Stop and report if a real LLM run fails or produces a blocking workflow error.
- Do not modify implementation behavior while producing samples.
- Do not include unrelated local artifacts in the sample PR.

## Status

Completed on 2026-06-07. NVDA and ZS real-LLM PDF-backed sample reports were
generated, mechanically checked, cross-reviewed by subagents, and staged for a
sample-output PR.
