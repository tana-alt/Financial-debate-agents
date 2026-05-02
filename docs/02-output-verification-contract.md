# Output Verification Contract

## Complete Output

Every meaningful output must state:

- source refs used
- changed paths or artifact refs
- verification attempted
- result: passed, failed, blocked, skipped, or not applicable
- unverified surfaces
- residual risk
- human gate status when relevant

Do not claim verification that did not run.

## Verification Order

Start with the smallest relevant check, then widen only when the touched surface
requires it.

1. closest local review, schema check, unit, or command
2. lint, typecheck, build, or contract check if available
3. smoke check for runnable app or plugin changes
4. broader suite only when scope justifies it

If a check cannot run, record the check name, reason, and risk.

## PR Or Handoff Evidence

PRs, handoffs, and review packets should include:

- intent
- scope
- changed paths or artifacts
- verifier results
- docs impact
- known risks or follow-up
- human review focus

## Human Gate

Escalate before merge, release, or irreversible action involving secrets, auth,
billing, database migration, deployment, CI/CD, GitHub Actions, infra, public
release, dependency risk, or security-sensitive changes.

## Source Commands

Old Makefile, CI, pytest, mypy, and app build commands in source docs are
reference material unless the corresponding files exist in this repo.
