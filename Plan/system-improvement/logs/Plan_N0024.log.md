# Plan_N0024 Log

## 2026-06-07

- Started from user direction to make the report Japanese, reader-facing, and
  to place canonical data used by the report as a premise.
- Read current renderer, workflow call sites, prompt assets, and report/API/CLI
  tests.
- Initial finding:
  - `src/report_renderer.py` uses a fixed English template.
  - `src/workflow.py` passes only `DebateResult` and `JudgeDecision` into the
    renderer, so detailed `BullCase` / `BearCase` fields are available in the
    workflow response but are mostly unused in final Markdown.
  - Agent prompts are largely Japanese, but no shared rule requires all
    natural-language JSON fields to be Japanese.
  - Current tests assert English report headings and need to be updated with
    the new Markdown contract.
- Spawned implementation subagent Linnaeus
  (`019e9e3a-6298-79c0-876a-0154ae414a31`) to implement the bounded renderer,
  prompt, workflow, and focused test changes.
- Implementation completed:
  - `src/report_renderer.py` now renders a Japanese reader-facing report and
    starts with `レポート前提: canonical data`.
  - The premise table reads only `financial_metrics.canonical_metrics` and
    `financial_metrics.derived_metrics`; presentation candidates are explicitly
    described as supplementary.
  - `MarkdownRenderer.render()` and the main workflow path pass optional
    `BullCase` / `BearCase` objects into `ReportRenderer` so rich debate fields
    appear in final Markdown.
  - Shared/runtime prompts instruct agents to write natural-language JSON field
    values in Japanese while preserving schema keys, enums, evidence IDs,
    source IDs, metric names, ticker symbols, and units.
  - The Japanese disclaimer avoids terms that the safety sanitizer treats as
    investment-advice language, and a regression test confirms the disclaimer
    is not redacted.
- Parent focused verification:
  - `uv run --active pytest tests/test_report_renderer.py
    tests/test_agent_assets.py tests/test_cli_smoke.py tests/test_api_smoke.py
    tests/test_workflow_e2e.py tests/test_workflow_api.py -q`
    passed: 64 passed, 1 warning.
- Parent fake CLI verification:
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local
    --input-json samples/request.example.json --out
    artifact/system-improvement/verification/Plan_N0024/cli_fake`
    passed: verdict `good`, confidence `0.76`.
  - Generated report contains the Japanese title and section headings,
    canonical premise table, rich Bull/Bear details, evidence matrix, data
    quality, quality gates, source appendix, and non-redacted disclaimer.
  - The premise area did not contain presentation source IDs.
- Closed implementation subagent Linnaeus after collecting its completion
  report.
- Spawned review subagent Hubble
  (`019e9e44-c633-7650-aebc-01efb2f871ac`) for read-only cross-review of the
  final Plan_N0024 diff.
- Review subagent Hubble reported one Low finding: fixed labels inside the
  `Bull/Bear論点` section still contained English labels such as `thesis`,
  `strength`, `confidence`, `failure modes`, `Risk case`, and `Judge tension`.
- Parent follow-up fix:
  - Replaced those fixed labels with Japanese reader-facing labels while
    keeping schema values, IDs, and source references unchanged.
  - Added regression assertions in `tests/test_report_renderer.py` so the old
    fixed labels do not return.
- Parent re-verification after the review fix:
  - `uv run --active pytest tests/test_report_renderer.py
    tests/test_agent_assets.py tests/test_cli_smoke.py tests/test_api_smoke.py
    tests/test_workflow_e2e.py tests/test_workflow_api.py
    tests/test_safety_guards.py -q` passed: 72 passed, 1 warning.
  - Regenerated fake CLI report in
    `artifact/system-improvement/verification/Plan_N0024/cli_fake`.
  - `uv run --active ruff check src tests` passed.
- Follow-up review:
  - Hubble re-reviewed the parent fix and reported no remaining findings.
  - Residual risk: if a real LLM ignores the Japanese-language instruction,
    natural-language field values could still be English, but deterministic
    renderer labels are now Japanese.
- Final verification:
  - `uv run --active pytest -q` passed: 290 passed, 1 warning.
- Follow-up prompt constraint:
  - Added one shared/runtime prompt constraint: if routed company-authored text
    explicitly acknowledges a material uncertainty or contingency relevant to
    the agent's assigned role, the agent should discount its own confidence and
    explain it inside allowed fields.
  - Kept the existing rule that absent forecasts or undisclosed data are not
    treated as missing data or acknowledged uncertainty.
  - `uv run --active pytest tests/test_agent_assets.py -q` passed: 28 passed.
  - `uv run --active ruff check src/prompts/shared/global_policy.md
    src/workflow_agents.py tests/test_agent_assets.py` passed.

## Result

Completed Plan_N0024 on 2026-06-07.
- Implementation subagent update:
  - Added Japanese fixed report sections and disclaimer in `src/report_renderer.py`.
  - Added the first report section `レポート前提: canonical data`, sourced only
    from `financial_metrics.canonical_metrics` and `derived_metrics`.
  - Kept presentation metric candidates out of canonical premise rows.
  - Extended Markdown rendering to use detailed `BullCase` / `BearCase` fields
    when the workflow has them.
  - Updated shared and runtime prompt constraints so natural-language JSON
    field values are Japanese while schema keys, enums, IDs, metric names,
    tickers, and units stay unchanged.
  - Updated focused renderer, prompt, CLI/API smoke, workflow, and safety tests.
  - Verification:
    - `uv run --active pytest -q tests/test_report_renderer.py`
    - `uv run --active pytest -q tests/test_agent_assets.py tests/test_workflow_e2e.py tests/test_cli_smoke.py tests/test_api_smoke.py tests/test_workflow_api.py`
    - `uv run --active pytest -q tests/test_workflow_agents.py tests/test_safety_guards.py tests/test_report_renderer.py`
    - `uv run --active pytest -q tests/test_report_renderer.py tests/test_agent_assets.py tests/test_workflow_agents.py tests/test_safety_guards.py tests/test_workflow_e2e.py tests/test_cli_smoke.py tests/test_api_smoke.py tests/test_workflow_api.py`
    - `uv run --active ruff check src/report_renderer.py src/workflow.py src/workflow_agents.py tests/test_report_renderer.py tests/test_agent_assets.py tests/test_cli_smoke.py tests/test_api_smoke.py tests/test_workflow_e2e.py tests/test_workflow_api.py tests/test_safety_guards.py`
  - Final focused verification result: `94 passed`, `ruff check` passed.
