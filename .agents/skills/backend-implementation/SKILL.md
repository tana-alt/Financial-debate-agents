---
name: backend-implementation
description: "Use when implementing or changing backend runtime behavior such as services, repositories, jobs, database access, business rules, server validation, middleware, or integrations after API contract and schema decisions are clear."
---


## Purpose

Keep backend changes explicit, bounded, observable, and safe at trust boundaries.

## Effect

Make backend runtime changes conform to existing service, repository, job, and
integration boundaries; preserve trust-boundary validation; and choose focused
verification for the touched behavior.

## Use when

- Adding or changing service, repository, job, middleware, API handler, or database logic.
- Implementing business rules or server-side validation.
- Implementing already-defined third-party integrations, webhooks, queues, or
  background jobs.

## Do not use when

- Designing API request/response contracts, status codes, error formats,
  pagination, auth semantics, or OpenAPI/client schemas before implementation;
  use `api-contract` first.
- Changing database schema, indexes, constraints, migrations, seed data, or
  backfills; use `db-migration`.
- Changing deployment, runtime config, CI/CD, health checks, or release process;
  use `deploy-readiness`.
- Reviewing auth, secrets, uploads, webhooks, untrusted input, or
  security-sensitive behavior as the primary risk; use `security-check`.

## Success conditions

- Existing repo boundaries are followed before adding a new service, repository,
  job, or integration abstraction.
- API-facing behavior matches the established contract rather than inventing
  contract details during implementation.
- Business logic, data access, and transport concerns are separated according to repo pattern.
- Inputs are validated at server-side trust boundaries.
- Errors are handled with repo-standard categories and messages.
- Queries are bounded and avoid obvious N+1 behavior.
- Jobs and retries are idempotent where required.

## Constraints

- Do not use `select *` or unbounded queries unless the repo explicitly permits it.
- Do not log secrets, tokens, full request bodies, or sensitive user data.
- Do not return raw internal exceptions to users.
- Do not skip authorization because the caller is an internal API.
- Do not add new infrastructure if a local repo pattern already exists.

## Stop guidance

Stop and route to the adjacent skill when the backend change depends on an
unresolved API contract, migration strategy, deployment/runtime decision, or
material security gate.

## Output

- Backend surfaces changed.
- Data access and trust boundaries touched.
- Idempotency/retry impact for jobs or integrations.
- Focused verification run, skipped, or blocked.
