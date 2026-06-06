---
plan_id: Plan_N0020
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0020.md
---

# Plan_N0020 Log

## 2026-06-07

- Started after real NVDA LLM run passed provider calls but stopped because
  `ReviewResponse.markdown_report` exceeded `max_length=20000`.
- User stated this report max gate is obsolete now that sources are surfaced in
  the report, and asked whether other character gates exist.
- Audit subagent completed a read-only length/token gate review.
- High-priority gates found:
  - `ReviewResponse.markdown_report` and `ReviewSuccessResponse.markdown_report`
    both had `max_length=20000`.
  - `DEFAULT_CONTEXT_BUDGET` was still `16000/2000/20000`, despite source-forward
    SEC/presentation routing.
- No active `30000` presentation-specific token constant was found in `src` or
  tests. The effective presentation/source context gate is the shared
  `ContextBudget`.
- Implemented:
  - Added `MAX_MARKDOWN_REPORT_CHARS = 200_000` and used it for both workflow
    and API success response markdown fields.
  - Raised default context budget to `max_input_tokens=96_000`,
    `max_output_tokens=8_000`, `max_total_tokens=128_000`.
  - Added focused tests for source-forward markdown response acceptance and
    default context budget.
- Other gates identified but left unchanged in this pass:
  - `DocumentSection.text max_length=12000`; file ingestion chunks at 8,000 chars,
    but direct normalized sections above 12,000 still fail validation.
  - PDF presentation ingestion uses `pypdf.Page.extract_text()` and then chunks
    each page through `_chunk_text()` with `MAX_DOCUMENT_SECTION_CHARS = 8000`.
    This is a character chunking gate, not a token gate. It should not reject a
    long PDF by itself unless resulting section validation fails, but it controls
    how much extracted page text is placed into each routed section.
  - Source-heavy count gates: document/source/manifest/report-matrix list caps
    can still block unusually large source sets.
  - Agent output `max_tokens` remains role JSON-output budget rather than report
    length budget.
- The real NVDA/ZS CLI inputs used for Plan_N0019 did not contain explicit
  `document_sections` or `context_budget`, so the observed NVDA stop was not
  caused by local presentation PDF text extraction.
