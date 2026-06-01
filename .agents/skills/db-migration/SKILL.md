---
name: db-migration
description: "Use when changing database schema, indexes, constraints, migrations, seed data, backfills, or data migration strategy."
---


## Purpose

Make database changes deployable and reversible enough for the repo's release model.

## Effect

When this skill fires, pause implementation long enough to define migration
order, data safety, rollback or mitigation, backfill approach, and app
compatibility before editing code or migration files.

## Use when

- Adding, changing, or removing columns, tables, indexes, constraints, or enums.
- Writing migrations, seed changes, backfills, or data cleanup scripts.
- Changing data access assumptions that depend on schema.

## Do not use when

- The change only reads or queries existing schema without changing data shape
  or migration strategy.
- The task is ordinary backend logic, validation, or repository code with no
  schema/data migration impact; use `backend-implementation`.
- The task is release, environment, CI/CD, or runtime configuration readiness
  without database change; use `deploy-readiness`.
- The task is only API request/response shape or status-code design without
  persisted data change; use `api-contract`.

## Success conditions

- Migration is forward-safe for existing data.
- Rollback or mitigation is considered according to repo policy.
- Large-table locking and long-running operations are considered.
- Large backfills and hardening steps use batched, resumable/idempotent, or
  non-blocking approaches where relevant.
- App code and migration order are compatible.
- Rolling deployments are accounted for before constraints reject old writers.
- Indexes match new query patterns where relevant.

## Constraints

- Do not edit already-applied migrations unless the repo policy allows it.
- Do not combine risky schema and data migration without reason.
- Do not drop data before consumers are migrated.
- Do not guess business rules for ambiguous production data cleanup; require an
  owner-approved resolution rule.
- Do not assume nullable/non-nullable changes are safe without checking existing data.
- Do not run destructive migrations without explicit approval.

## Stop

Return rework instead of editing or running destructive commands when existing
data shape is unknown, rollback/mitigation is undefined for a risky change,
destructive migration approval is missing, or migration order would break
currently deployed app code.

## Output

- Migration intent and ordered steps.
- Forward-compatibility and rollback/mitigation note.
- Backfill or data cleanup plan, if relevant.
- Locking/large-table risk, if relevant.
- App/migration deployment order.
- Verification command or blocked reason.
