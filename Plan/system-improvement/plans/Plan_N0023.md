# Plan_N0023: ID-selection debate/judge outputs and agent traceability

## Goal

Make real LLM execution more robust after the NVDA presentation PDF run stopped
with truncated Judge JSON.

## Scope

- Change Bull/Bear/Judge LLM outputs to select canonical evidence by
  `evidence_id` instead of emitting full `EvidenceItem` objects.
- Map selected IDs back to existing public `BullCase`, `BearCase`, and
  `JudgeDecision` workflow models at runtime.
- Keep source/evidence integrity hard-blocking through canonical pool lookup.
- Increase output token caps enough to reduce truncation risk.
- Audit and improve per-agent traceability for attempts, retry exhaustion, error
  kind, and provider token usage without external LLM/API calls.

## Acceptance

- Public workflow response models for bull/bear/judge remain structurally
  compatible for downstream rendering.
- Debate/Judge prompts and runtime context instruct ID selection from validated
  pools.
- Unknown evidence IDs still fail validation after finite retry.
- Successful responses expose agent attempt/token trace data.
- Focused tests and repo lint/tests pass.

## Status

Completed on 2026-06-07. See
`Plan/system-improvement/logs/Plan_N0023.log.md` for verification.

## Constraints

- Do not call real LLM/network APIs.
- Do not revert unrelated worktree changes.
- Use repo-local verification only.
