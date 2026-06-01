---
name: api-contract
description: "Use when creating or changing API endpoints, request/response schemas, status codes, pagination, auth, rate limits, webhooks, OpenAPI descriptions, generated clients/servers, or error formats."
---


## Purpose

Make API changes explicit and stable before implementation is considered done.

## Effect

When this skill fires, define or verify the externally observable HTTP contract
before treating implementation as complete. The contract decision should
constrain handler code, validation, docs/types, tests, and generated artifacts
where present.

## Use when

- Adding or changing an API route.
- Changing request or response shape.
- Adding pagination, filtering, sorting, rate limits, auth, or webhooks.
- Modifying error behavior or status codes.
- Creating, changing, or reviewing OpenAPI descriptions, generated API clients,
  generated servers, or HTTP API documentation.

## Do not use when

- The change is internal backend logic with no externally observable API
  contract change; use `backend-implementation`.
- The change only updates current third-party API usage or framework syntax;
  use `doc-lookup`.
- The primary risk is authorization, secrets, unsafe input handling, CORS, CSRF,
  or webhook trust validation rather than API shape/status/error behavior; use
  `security-check`.
- The change is only database schema or migration behavior with no API shape,
  status, or error impact; use `db-migration`.

## Success conditions

- Method, path, auth requirement, request schema, response schema, and error shape are clear.
- Pagination changes define parameters, default and maximum bounds, response envelope, and compatibility or migration path when an existing list shape changes.
- Webhook contracts define payload, acknowledgement statuses, retry/idempotency semantics, and route unresolved signature or replay validation to `security-check`.
- Error format changes define stable codes, message and field semantics, status mapping, and compatibility or migration path.
- Status codes distinguish success, validation errors, auth failures, forbidden access, missing resources, conflicts, and server errors.
- API behavior matches existing repo conventions.
- Contract docs, types, or OpenAPI-like references are updated if the repo uses them.

## OpenAPI mode

Use this mode when an OpenAPI file or generated contract is in scope.

- Validate operation `method` and `path` against the implementation route.
- Keep request bodies, parameters, headers, responses, auth, pagination, and
  error schemas explicit.
- Preserve compatibility unless the task explicitly allows a breaking contract.
- Prefer the repo's current OpenAPI version and generator conventions.
- Use `doc-lookup` for current OpenAPI specification details when needed.

## Constraints

- Do not use one generic `200` or `500` for all outcomes.
- Do not leak stack traces, internal IDs, secrets, or database details.
- Do not put verbs in REST resource paths unless the repo already uses that convention.
- Do not return unbounded lists.
- Do not trust client-side validation as the API contract.

## Stop guidance

Stop and clarify before implementation if method/path ownership, auth
requirement, breaking-change permission, request/response shape, or error format
is ambiguous.

## Output

- Contract summary: method, path, auth, request, response, errors, and
  pagination/rate-limit/webhook behavior if relevant.
- Compatibility note: backward-compatible, intentionally breaking, or unknown.
- Contract artifacts changed or not applicable.
- Verification command, contract test, generated-client check, or blocked reason.
