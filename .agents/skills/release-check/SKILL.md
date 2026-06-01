---
name: release-check
description: "Use before PR, merge, release, or handoff, or after high-blast-radius changes, to choose and run the narrowest available verification set and report pass, rework, blocked, and residual risk."
---


## Purpose

Confirm that a change is shippable or clearly report why it is not.

## Effect

When this skill fires, verification breadth is matched to release risk. Identify
the smallest command set that can support handoff, avoid unrelated QA expansion,
and make unverified risk explicit.

## Use when

- Before PR handoff, merge, release, or resumable task handoff.
- After broad or high-blast-radius changes such as build, dependency, auth,
  data, deployment, or release-critical user flows.
- When the user asks whether the completed change is ready to ship or hand off.

## Do not use when

- The task is still in design, research, or implementation and no readiness
  verdict is needed.
- A narrow domain skill owns the primary concern, such as `security-check`,
  `deploy-readiness`, `browser-verification`, or `tdd-scope`, and no
  handoff/release verdict is requested.
- The change is a small local edit where the relevant implementation skill's
  focused verification is enough.

## Success conditions

- Relevant commands are selected from current repo files such as `Makefile`,
  package scripts, test config, scripts, or CI config.
- Typecheck, lint, unit tests, build, security audit, and e2e are run only when relevant and available.
- Results are summarized as `pass`, `rework`, or `blocked`.
- Failures include the minimal next fix, not a broad diagnosis essay.

## Constraints

- Do not invent commands when repo scripts exist.
- Do not run destructive commands.
- Do not claim pass if verification was not run.
- Do not chase unrelated failures unless they block the task.
- Do not expand into full QA when a narrow verification is enough.

## Stop guidance

- Stop at the first blocking failure that prevents a meaningful readiness
  verdict, then report `blocked` or `rework` with the next minimal fix.
- Do not continue into unrelated failures unless they affect the changed surface
  or release readiness.
- If commands are missing, report the gap and residual risk instead of inventing
  substitutes.

## Output

- Verdict: `pass`, `rework`, or `blocked`.
- Scope checked: changed surfaces and why the selected commands were sufficient.
- Commands run with result.
- Relevant failure summary and minimal next fix.
- Residual risk, including verification that was skipped, unavailable, or
  intentionally out of scope.
