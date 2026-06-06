# Plan_N0023 Log

## 2026-06-07

- Started from user request to convert debate/judge outputs to evidence-id
  selection, increase output caps, and confirm/upgrade traceability.
- Read AGENTS.md and core contracts.
- Traceability audit:
  - `LLMResponse` already carries provider `input_tokens` and `output_tokens`.
  - `WorkflowAgent.run` has finite JSON/schema repair attempts.
  - `DebateRunner._run_case` has finite evidence validation retry.
  - Existing success responses expose step-level status only; they do not expose
    per-agent attempt count, last error kind, or token usage.
  - Failure messages include schema error category/kind indirectly but not token
    totals or attempt summaries.
- Implementation:
  - Added internal `BullCaseSelection`, `BearCaseSelection`, and
    `JudgeDecisionSelection` contracts that emit evidence ID lists only.
  - Runtime maps selected IDs back to canonical `EvidenceItem` objects and
    builds existing public `BullCase`, `BearCase`, and `JudgeDecision` models.
  - Unknown evidence IDs remain hard validation failures after finite retry.
  - Raised agent output caps to 8,192 tokens for specialist/debate agents and
    12,000 tokens for Judge.
  - Added `AgentAttemptTrace` / `AgentExecutionTrace` and exposed successful run
    traces via `ReviewResponse.agent_traces`,
    `ReviewSuccessResponse.agent_traces`, and
    `quality_gate_result.agent_traces`.
- Verification:
  - `uv run --active pytest tests/test_workflow_agents.py tests/test_workflow_api.py tests/test_agent_assets.py tests/test_workflow_models.py -q`
    passed: 96 passed, 1 warning.
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 287 passed, 1 warning.
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local
    --input-json samples/request.example.json --out
    artifact/system-improvement/verification/Plan_N0023/cli_fake` passed:
    verdict `good`, confidence `0.76`.
  - CLI `workflow_result.json` contains 7 `agent_traces`; Judge trace uses
    `JudgeDecisionSelection`, while final `judge_decision.positive_evidence`
    is canonical evidence `EarningsQualityAnalyst:positive`.
- Subagent review:
  - Implementation subagent Mill reported the intended ID-selection/token-cap
    and traceability implementation shape.
  - Parent agent integrated and corrected the worktree diff in the main
    workspace.
  - Review subagent Carver performed read-only cross-review of the final
    parent-integrated diff.
  - Carver Medium finding: Judge prompt still said `FinalVerdict`; fixed to
    `JudgeDecisionSelection`.
  - Carver Low finding: `agent_traces.attempt_count` tracks retry attempts
    inside one `WorkflowAgent.run()`. Evidence-ID validation retry in
    `DebateRunner`/`JudgeRunner` is an outer finite retry and appears as
    another trace row for the same `public_role`, preserving traceability but
    requiring aggregation by `public_role` for total attempts.
  - Parent follow-up fix added repair-prompt guidance so schema retry also
    keeps `*_evidence_ids` as ID strings only.
  - Carver follow-up review after the parent fixes reported no new findings.
- Final parent verification:
  - `uv run --active ruff check src tests` passed.
  - `uv run --active pytest -q` passed: 287 passed, 1 warning.
  - `LLM_PROVIDER=fake uv run --active earnings-debate run --api-url local
    --input-json samples/request.example.json --out
    artifact/system-improvement/verification/Plan_N0023/cli_fake_parent`
    passed: verdict `good`, confidence `0.76`.
  - Parent checked generated `workflow_result.json`: `agent_traces=7`,
    Bull/Bear/Judge traces use `BullCaseSelection`, `BearCaseSelection`, and
    `JudgeDecisionSelection`; final public bull/judge outputs contain canonical
    evidence and do not contain selection-only ID fields.
- NVDA real LLM run:
  - Command:
    `LLM_PROVIDER=openai uv run --active earnings-debate run --api-url local
    --input-json artifact/system-improvement/verification/Plan_N0022/nvda_presentation_pdf_real_cli_input.json
    --out artifact/system-improvement/verification/Plan_N0023/nvda_presentation_pdf_real_llm`
  - Completed without stop condition: verdict `good`, confidence `0.88`.
  - Output report:
    `artifact/system-improvement/verification/Plan_N0023/nvda_presentation_pdf_real_llm/report.md`.
  - `workflow_result.json` contains 7 `agent_traces`; Bull/Bear/Judge traces
    use ID-selection output models and final public outputs contain canonical
    `EvidenceItem` objects only.
  - `ManagementIntentAnalyst` used one internal schema repair retry:
    first attempt `llm_output_schema/schema_mismatch`, second attempt success.
  - One non-blocking quality warning remained:
    `llm_numeric_grounding:e6`, removed from Judge candidate pool because
    grounded alternatives remained.
