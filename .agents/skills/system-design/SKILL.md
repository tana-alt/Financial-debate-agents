---
name: system-design
description: "Use before implementing a new app/service/module boundary, public or external contract, persistent data ownership, trust boundary, external write path, queue/worker/scheduler, deployment topology, irreversible migration, or materially tradeoff-heavy architecture change."
---

# System Design

## Purpose
Improve significant architecture work before implementation without expanding
active docs or broad repo context.

## Effect
Before implementation, decide whether the change is architecturally significant,
identify the affected boundaries and rollback constraints, compare viable
options, and return a compact design packet that can guide implementation or
force rework.

## Use when
- Creating or materially changing a long-lived boundary or shared abstraction.
- Adding or changing a public or externally consumed contract.
- Changing persistent data ownership, auth, privacy, secrets, or trust boundaries.
- Adding an external write path, queue, worker, scheduler, deployment topology,
  irreversible migration, or hard-to-rollback behavior.
- Multiple plausible designs have material reliability, security, data,
  operations, or compatibility tradeoffs.

## Do not use when
- The change is typo, formatting, copy, or mechanical cleanup.
- The change is a small internal edit inside an existing boundary.
- The task is only choosing code organization inside an established pattern.
- The task is API shape, migration mechanics, deployment readiness, or security
  review with no broader architecture choice; use the domain skill first.
- The task is research to discover repo patterns or external constraints before
  a design choice is known; use `research-before-build` first.
- Existing repo patterns make the design choice obvious and reversible.

## Required design packet
- problem, actors, success criteria, and non-goals
- constraints and affected boundaries
- observable quality targets
- options considered
- selected option and tradeoffs
- verification
- rollback or mitigation
- residual risk
- human gate status when required by existing repo rules

## Stop conditions
Return rework when required design inputs, verification, or rollback/mitigation
are missing. Treat an input as required only when its absence prevents choosing
boundaries, options, verification, or rollback; otherwise state the unknown as
residual risk.

Return `needs_human_review` when the design can be stated but an existing or
likely required human gate or approval must happen before implementation. If
the gate source is unavailable, state that as residual risk instead of inventing
a gate. External writes, irreversible/protected actions, security-sensitive
trust-boundary changes, deployment topology changes, and persistent data
ownership changes are likely gates even when the exact repo rule is out of scope.

Return `not_significant` when inspection shows the task fits an existing,
reversible pattern and should continue under a narrower implementation skill.

## Constraints
- Do not read broad docs by default.
- Do not create repo-wide ADRs for local edits.
- Do not add dependencies, services, queues, or storage roots without explicit need.
- Prefer existing repo patterns over new abstractions.

## Output
- `design_verdict`: proceed / rework / blocked / needs_human_review / not_significant
- `architecture_significance`: significant / not_significant, with reason
- `design_packet`
- `affected_boundaries`, `options_considered`, `selected_option`, `tradeoffs`
- `verification_plan`, `rollback_or_mitigation`
- `required_follow_on_skills`
- `human_gate_status`
- `skill_refs_used`
- `residual_risk`
