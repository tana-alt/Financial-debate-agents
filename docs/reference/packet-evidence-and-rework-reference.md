---
status: draft
owner: foundation
source_of_truth_level: reference
created_at: 2026-05-02
---

# Packet, Evidence, And Rework Reference
## Purpose
Use this reference when creating or reviewing work contracts, packets, evidence
records, verification records, and rework records. Keep records small. Carry
refs, checks, and repair needs forward; do not embed raw bodies, credentials,
secrets, or unrelated context.
## Work Contract
A work contract defines one bounded unit of work for a human, LLM session,
script, automation, review lane, or release lane.
Required field groups:
- `identity`: `work_id`, `project_id`, `work_type`, `status`, `created_at`
- `intent`: `task_intent`, `success_criteria`, `non_goals`
- `inputs`: `source_refs`, `required_context`, `optional_context`, `templates`
- `boundaries`: `allowed_write_targets`, `denied_context`, `risk_flags`
- `outputs`: `expected_outputs`, `artifact_refs`, `changed_paths`, `decision_refs`
- `evidence_and_verification`: `evidence_required`, `verification_required`,
  `verification_results`, `residual_risk`
- `continuation`: `blockers`, `open_questions`, `next_action`
Template `work_type` values: `implementation`, `research`, `planning`,
`design`, `review`, `verification`, `release`, `docs`.
Template `next_action` values: `complete`, `rework`, `review`, `continue`,
`release`, `archive`.
Valid output shape:
- expected artifacts or changes
- evidence refs
- changed paths
- verification results
- blockers or open questions when present
- next action
If the valid output shape cannot be satisfied, return a rework record.
## Evidence Rules
Evidence records make work auditable. Separate observed facts from inferences.
Allowed sources include local files, command output, test results, screenshots,
visual inspection, product requirements, user decisions, external references,
and prior project records.
Rules:
- Cite concrete `source_refs`.
- Put observed items under `facts`.
- Put conclusions under `inferences` and label them as inference.
- Record decisions separately from facts and inferences.
- Do not include secrets, credentials, private keys, tokens, or raw sensitive data.
- Keep evidence compact and relevant.
- Preserve enough detail for another worker to reproduce the reasoning.
- State missing evidence, stale refs, confidence, and residual risk.
## Verification Records
Verification records describe checks and unverified surfaces. Common checks
include lint, typecheck, unit tests, integration tests, runtime smoke tests,
visual QA, schema validation, and manual review.
Verification result states:
- `passed`: check ran and passed.
- `failed`: check ran and failed.
- `blocked`: check could not run because of a blocker.
- `skipped`: check was intentionally not run.
- `not_applicable`: check does not apply to this work unit.
Each check should include name, command when applicable, result, `evidence_ref`,
and notes. Include `unverified_surfaces`, `residual_risk`, and `next_action`.
## Packet And Body Boundary
Packets route work and evidence between lanes. They carry refs, not raw bodies.
Packet fields may include `packet_id`, `schema_version`, `from`, `to`,
`project_graph`, `task`, `required_context`, `expected_output`,
`gate_required`, `memo`, `content_ref`, `evidence_refs`, `reason`,
`requested_change`, and `severity`.
`content_ref` may include `content_id`, `project_id`, `offer_id`, `channel_id`,
`content_type`, `status`, `body_ref`, `asset_refs`, `evidence_refs`, and
`reaction_refs`.
Boundary rules:
- Use `body_ref`, `content_ref`, `asset_refs`, `evidence_refs`, and
  `reaction_refs` to point at stored material.
- Do not embed raw content bodies in packets.
- Do not embed credentials or secrets in packets.
- Evidence packets support interpretation; they are not final project decisions.
## Rework
Use rework when work is incomplete, unsafe, unverifiable, or mismatched to the
contract.
Triggers: required context is missing; task intent is ambiguous; expected output
format cannot be satisfied; verification fails; evidence is insufficient; a
safety, privacy, compliance, or security risk appears; or the requested change
conflicts with existing project truth.
Rework types: `missing_context`, `ambiguous_instruction`, `contract_mismatch`,
`verification_failed`, `evidence_gap`, `unsafe_assumption`,
`blocked_dependency`, `scope_conflict`.
A useful rework record includes `work_id`, `project_id`, rework `type`,
`blocker_summary`, `failed_or_missing_requirement`, `evidence_refs`,
`requested_repair`, and `suggested_next_action`.
Return the smallest useful repair request: name the blocker, cite the source or
verification that exposed it, and ask only for the missing artifact, context,
check, or decision needed to continue.
Rework closes when the missing input is supplied, the contract is updated,
verification passes, the risky assumption is removed, or the work is abandoned
with a recorded reason.
## Template Locations
Use `templates/work-contract.yaml`, `templates/evidence-record.yaml`,
`templates/verification-record.yaml`, `templates/rework-record.yaml`,
`archive/packets/handoff-packet.yaml`, `archive/packets/evidence-packet.yaml`,
and `archive/packets/rework-packet.yaml`.
