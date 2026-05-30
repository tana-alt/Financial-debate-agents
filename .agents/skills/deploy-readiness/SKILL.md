---
name: deploy-readiness
description: "Use when deployment-facing behavior changes: Docker or runtime packaging, CI/CD release workflows, environment/config contracts, build artifacts, health checks, rollback, or production startup."
---


## Purpose

Prevent deployment regressions caused by configuration, packaging, runtime, or release-process changes.

## Effect

When this skill fires, turn deployment-impacting edits into an explicit
readiness check: identify the runtime surface changed, verify the build/startup
path, surface required config, and state the rollback or mitigation path for
risky changes.

## Use when

- Dockerfile, CI/CD, deployment scripts, env vars, or runtime config change.
- CI/CD workflows that package, publish, release, deploy, or gate production
  readiness change.
- A build or production startup behavior changes.
- Health checks, rollback, monitoring, or release commands are touched.

## Do not use when

- CI/test/lint workflow edits do not affect release, deploy, packaging,
  artifacts, permissions, secrets, or production gates; use `release-check` if
  verification breadth is the main concern.
- Application logic changes do not alter runtime config, startup, health,
  packaging, or deployment behavior.
- The main risk is secret handling, token scope, auth, or untrusted input; use
  `security-check`, adding this skill only if deployment behavior also changes.
- Current vendor/platform syntax is needed; use `doc-lookup` for official docs
  rather than embedding provider-specific guidance here.

## Success conditions

- Build and startup path are clear.
- Required env vars are documented without secret values.
- Health check or smoke test exists when repo pattern supports it.
- Rollback or mitigation path is clear for risky changes.
- Runtime image and permissions follow repo security expectations.

## GitHub Actions / CI mode

Use this thin mode only when CI remains part of release or deploy readiness.

- Confirm changed workflows run the repo's required checks.
- Avoid broadening permissions, token access, caches, or artifacts without a
  readiness reason.
- Keep secrets out of workflow logs and generated artifacts.
- Record which local command maps to the changed CI job when a mapping exists.
- Require human review before operational use of release/deploy workflow
  changes.

## Constraints

- Do not bake secrets into images, scripts, logs, or config.
- Do not use floating `latest` tags unless repo policy allows it.
- Do not run as root in containers unless justified.
- Do not include dev dependencies in production artifacts unless necessary.
- Do not change deployment policy during unrelated feature work.

## Stop guidance

Stop and ask before proceeding when a change would publish, deploy, rotate
secrets, alter production infrastructure, broaden workflow permissions, or make
an irreversible release-process change.

## Output

- Changed deployment surface.
- Deploy risk summary.
- Build/startup command checked, or why not checked.
- Env/config contract changes, with no secret values.
- Health/smoke/rollback status.
- Blockers and required human review.
