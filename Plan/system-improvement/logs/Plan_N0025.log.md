# Plan_N0025 Log

## 2026-06-07

- Started real LLM sample-output pass for NVDA and ZS after PR #24 CI was fixed.
- User requested one-by-one execution with PDFs included, output inspection, and
  then a sample PR.
- Initial source files:
  - `data/NVDA-F1Q27-Quarterly-Presentation-FINAL.pdf`
  - `data/2026 Q3 ZS Shareholder Letter PDF FINAL.pdf`
- Existing NVDA real-LLM input found at
  `artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_cli_input.json`.
- Created Plan_N0025 CLI inputs:
  - `artifact/system-improvement/verification/Plan_N0025/nvda_presentation_pdf_real_cli_input.json`
  - `artifact/system-improvement/verification/Plan_N0025/zs_shareholder_letter_pdf_real_cli_input.json`
- Ran NVDA real LLM with PDF:
  - Command: `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0025/nvda_presentation_pdf_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0025/nvda_real_llm_pdf`
  - Result: completed; verdict `good`; confidence `0.82`; no warnings.
  - Outputs:
    - `artifact/system-improvement/verification/Plan_N0025/nvda_real_llm_pdf/report.md`
    - `artifact/system-improvement/verification/Plan_N0025/nvda_real_llm_pdf/workflow_result.json`
- Ran ZS real LLM with PDF:
  - Command: `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0025/zs_shareholder_letter_pdf_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0025/zs_real_llm_pdf`
  - Result: failed during `JudgeAgent` with OpenAI 429 TPM rate limit.
  - Error summary: `Rate limit reached for gpt-5.4-mini`; limit `200000`
    TPM, used `137209`, requested `64058`.
  - No ZS `report.md` or `workflow_result.json` was written.
- Stopped before sample PR creation because the requested two-sample output set
  is incomplete.
- Re-ran ZS real LLM with PDF:
  - Command: `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0025/zs_shareholder_letter_pdf_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0025/zs_real_llm_pdf`
  - Transient OpenAI 429 responses occurred during provider calls, but the SDK
    retry path recovered and the CLI exited successfully.
  - Result: completed; verdict `neutral`; confidence `0.87`.
  - Outputs:
    - `artifact/system-improvement/verification/Plan_N0025/zs_real_llm_pdf/report.md`
    - `artifact/system-improvement/verification/Plan_N0025/zs_real_llm_pdf/workflow_result.json`
  - Mechanical checks: quality gate `passed`; source_manifest entries `52`;
    earnings-presentation sources `36`; evidence items `16`; missing data
    items `0`; all seven agent traces succeeded with `attempt_count=1`.
- ZS subagent cross-review verdict: passed; no rework findings.
- Prepared sample outputs for PR:
  - `outputs/sample-nvda-20260607/report.md`
  - `outputs/sample-nvda-20260607/workflow_result.json`
  - `outputs/sample-zs-20260607/report.md`
  - `outputs/sample-zs-20260607/workflow_result.json`
