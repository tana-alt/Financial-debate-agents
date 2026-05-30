---
name: doc-lookup
description: "Use when current framework, library, API, CLI, or platform documentation is needed to avoid stale or guessed implementation. Do not use for stable repo-local behavior."
---


## Purpose

Confirm current external behavior before implementing code that depends on it.

## Effect

When this skill fires, current official or primary documentation should
constrain the next implementation decision. Repo-local contracts and inspected
code remain authoritative for local behavior.

## Use when

- A library, SDK, CLI, or platform may have changed.
- Version-specific behavior matters.
- The implementation depends on auth, billing, webhooks, deployment, routing, caching, or browser behavior.
- The agent is not confident about the API surface.

## Do not use when

- The question is answered by inspected repo code, active contracts, or stable
  project conventions.
- The task is broad pre-build discovery; use `research-before-build` unless the
  specific need is current external documentation.
- The issue is security review of untrusted docs/tool output; route material
  trust-boundary concerns to `security-check`.

## Success conditions

- Prefer official documentation or primary source material.
- Capture only the 1-3 constraints that affect implementation.
- Note the relevant version or date when available.
- Apply the constraint directly to the implementation plan.

## Constraints

- Do not use memory alone for change-prone external APIs.
- Do not paste long documentation into the task context.
- Do not continue searching after the implementation constraint is clear.
- Do not treat third-party blog posts as authoritative when official docs exist.

## Stop guidance

Stop once the implementation-relevant constraint is clear. Do not collect
examples, tutorials, migration history, or alternate sources unless the first
source is ambiguous.

## Output

- Source checked, with official/primary preference.
- Version/date or doc freshness signal when available.
- One to three implementation constraints.
- Concrete implication for the current task.
- If docs cannot be checked, blocked reason and next source to check instead of inferred constraints.
- Open uncertainty only if docs are conflicting or version is unknown.
