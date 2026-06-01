---
name: research-before-build
description: "Use before building when the change may already have a repo pattern, external API constraint, dependency/version issue, or known implementation approach. Do not use for obvious local refactors."
---


## Purpose

Prevent unnecessary custom work by checking existing repo patterns and external constraints before implementation.

## Effect

This skill pauses implementation long enough to identify the decisive existing
pattern, external constraint, or dependency/version fact. It should narrow the
implementation path, not produce broad research.

## Use when

- Adding a feature, integration, or behavior where the repo may already contain
  a reusable pattern.
- Touching an external API, SDK, framework, or dependency behavior.
- Unsure whether the repo already has a pattern for the task.
- The task has multiple plausible implementation paths.

## Do not use when

- The change is an obvious local refactor with no new behavior or dependency
  risk.
- The task is only to look up current official docs; use `doc-lookup`.
- The task needs architecture options, ownership boundaries, rollout, or
  rollback design; use `system-design`.
- The user is asking for code review, release verification, or test execution
  rather than pre-implementation direction.

## Success conditions

- Existing repo patterns are checked first.
- External constraints are checked only when relevant.
- The chosen path is stated as `reuse`, `extend`, `replace`, or `build new`,
  unless decisive evidence is missing.
- The implementation scope is narrowed before coding.

## Constraints

- Do not browse or research broadly when local code is sufficient.
- Do not add a dependency unless it clearly reduces complexity or risk.
- Do not copy external patterns blindly; adapt to the repo's conventions.
- Keep the research note to the minimum needed decision.

## Output

- Decision: `reuse`, `extend`, `replace`, or `build new`; if decisive
  evidence is missing, say implementation is blocked instead of forcing a path.
- Evidence checked: local files/patterns first, external docs only if relevant.
- Decisive constraint or pattern.
- Implementation direction and narrowed scope.
- Stop condition: begin implementation once the decisive pattern or constraint
  is known; do not continue researching for completeness.
- Remaining uncertainty, if any.
