---
plan_id: Plan_N0022
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0022.md
---

# Plan_N0022 Log

## 2026-06-07

- Started after user provided local presentation PDFs:
  - `data/NVDA-F1Q27-Quarterly-Presentation-FINAL.pdf`
  - `data/2026 Q3 ZS Shareholder Letter PDF FINAL.pdf`
- User requested running NVDA first and stopping on error.
- Built
  `artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_cli_input.json`
  using the NVDA PDF as `document_files[0]`.
- PDF extraction preflight:
  - `document_files_to_sections()` returned 16 presentation sections.
  - Maximum section text length was 4,254 chars, below the section validation
    gate.
- Fake-provider CLI preflight passed:
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_fake_preflight`
  - Output: `Verdict: good (confidence 0.76)`.
- Real LLM command:
  - `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_llm`
- Stop reason:
  - OpenAI HTTP calls mostly returned 200.
  - One `503 Service Unavailable` occurred and was retried by the OpenAI SDK,
    then returned 200.
  - Workflow stopped at `JudgeAgent` because the JudgeDecision LLM response was
    invalid JSON: `Unterminated string starting at`.
  - The repo-side repair loop is finite (`WorkflowAgent(max_retries=1)`) and
    exhausted after the invalid Judge JSON repair attempt.
  - The OpenAI client default observed in this environment is `max_retries=2`.
- No `workflow_result.json` or `report.md` was written for the real run because
  the workflow did not return a valid response.
