---
plan_id: Plan_N0019
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0019.md
---

# Plan_N0019 Log

## 2026-06-07

- Started after real-LLM NVDA run stopped on numeric-grounding gate.
- User accepted the principle that upstream integrity should be harder while
  LLM-output quality issues should favor stable report generation with warnings.
- Implementation subtask completed:
  - Added reusable numeric-grounding failure collection while keeping
    `validate_numeric_grounding()` available as a standalone hard validator.
  - Aggregation now warns on ungrounded material LLM evidence and removes it
    from positive/negative Judge candidate pools when grounded alternatives
    remain.
  - `AnalysisBrief.quality_warnings` now feeds `ReportMatrix.data_quality_flags`
    for deterministic report visibility.
  - Specialist, debate, and judge investment-advice phrasing is redacted with
    `llm_investment_advice:*` warnings; final markdown advice detection remains
    hard-blocking.
  - Source-ref mismatch and evidence-id mismatch tests remain hard-blocking.
- Verification:
  - `uv run --active pytest tests/test_workflow_api.py::test_workflow_degrades_ungrounded_material_evidence_when_alternative_exists -q`
    passed.
  - `uv run --active pytest tests/test_workflow_api.py::test_workflow_rejects_judge_evidence_source_ref_changes tests/test_workflow_api.py::test_workflow_rejects_bull_case_evidence_not_in_analysis_brief -q`
    passed.
  - `uv run --active ruff check src/report_quality_numeric_grounding.py src/workflow_validation.py src/workflow.py src/workflow_runtime.py src/workflow_models.py tests/test_workflow_api.py tests/test_safety_guards.py`
    passed.
  - `uv run --active pytest tests/test_report_quality_full.py tests/test_workflow_api.py tests/test_safety_guards.py tests/test_report_renderer.py -q`
    passed.
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 278 passed, 1 warning.
- Parent review found one integration issue: filtering a finding's only degraded
  evidence could leave that finding with an empty `key_evidence`/`counter_evidence`
  list through `model_copy()`, bypassing the specialist schema contract.
- Parent fix:
  - Added a non-claim quality-warning placeholder when a finding evidence field
    would otherwise become empty after degraded evidence removal.
  - Kept removed ungrounded evidence IDs out of candidate pools and finding
    evidence containers.
  - Expanded investment-advice redaction skip keys so structured source metadata
    such as `source_ref.title` is not redacted before source validation.
- Parent focused verification:
  - `uv run --active ruff check src/workflow_validation.py tests/test_workflow_api.py tests/test_safety_guards.py`
    passed.
  - `uv run --active pytest tests/test_workflow_api.py::test_workflow_degrades_ungrounded_material_evidence_when_alternative_exists tests/test_workflow_api.py::test_workflow_keeps_degraded_finding_schema_valid_when_field_would_empty tests/test_workflow_api.py::test_workflow_rejects_judge_evidence_source_ref_changes tests/test_workflow_api.py::test_workflow_rejects_bull_case_evidence_not_in_analysis_brief tests/test_safety_guards.py -q`
    passed: 13 passed, 1 warning.
- Parent full verification:
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 280 passed, 1 warning.
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local --input-json samples/request.example.json --out artifact/system-improvement/verification/Plan_N0019/cli_fake`
    passed with `Verdict: good (confidence 0.76)`.
  - Output check on
    `artifact/system-improvement/verification/Plan_N0019/cli_fake/workflow_result.json`
    confirmed `status=completed`, `claim_matrix.data_quality_flags` present,
    and no fake-run quality warnings.
- Parent final hard/soft gate boundary verification:
  - Added a focused test for the case where every item in a polarity pool is an
    ungrounded material claim. The workflow keeps the evidence and emits
    `llm_numeric_grounding:*` warning instead of emptying the polarity pool.
  - `uv run --active pytest tests/test_report_quality_full.py::test_numeric_grounding_degrade_keeps_only_polarity_evidence_with_warning -q`
    passed.
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 281 passed, 1 warning.
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local --input-json samples/request.example.json --out artifact/system-improvement/verification/Plan_N0019/cli_fake_parent`
    passed with `Verdict: good (confidence 0.76)`.
- Real LLM sequential validation:
  - Started with NVDA per user instruction; ZS was not run because NVDA failed.
  - Command:
    `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local --input-json artifact/system-improvement/verification/Plan_N0018/nvda_real_cli_input.json --out artifact/system-improvement/verification/Plan_N0019/real_llm_nvda`
  - OpenAI chat completion requests returned HTTP 200, but local workflow stopped
    when constructing `ReviewResponse`.
  - Stop reason:
    `ReviewResponse.markdown_report` exceeded its Pydantic `max_length=20000`
    contract after deterministic markdown rendering.
  - No `workflow_result.json` or `report.md` was written because `src/main.py`
    writes output only after the workflow returns a valid response.
