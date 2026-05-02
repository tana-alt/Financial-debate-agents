---
status: draft
owner: foundation
source_of_truth_level: reference
created_at: 2026-05-02
---

# Repo Boundary And Storage Reference

Use the current folder map, store truth locally, and archive only after useful
content is summarized.

## Current Folder Map

- `app/`: future runnable app surfaces only. Keep empty unless truly needed.
- `src/`: future shared implementation code only. Do not store notes, logs, or
  project records here.
- `docs/`: active agent-facing docs and compact references.
- `docs/reference/`: compressed references distilled from older source docs.
- `artifact/`: repo-local generated artifacts, fixtures, or machine-readable
  outputs for this foundation repo. Do not use it as a project log bucket.
- `archive/`: old or superseded material after useful content is summarized.
- `templates/`: reusable work, evidence, verification, rework, and storage
  templates.
- `archive/source-docs/`: copied historical source refs. Do not make routine agents
  read this directory directly once references are summarized.

## Legacy Source Assumptions

Some source refs describe older or parent-repo structures. Treat them as
historical context unless the current task explicitly names them.

- Old plural `artifacts/` paths are legacy/source references. The current
  foundation repo uses singular `artifact/` for repo-local generated outputs,
  fixtures, and machine-readable foundation artifacts.
- Older populated `apps/`, `src/services`, `projects/`, `tests/`, `profiles/`,
  and broad runtime maps explain prior app-delivery and orchestration
  boundaries, not current active implementation in this foundation repo.
- Do not recreate old `apps/`, `projects/`, or `tests/` assumptions just because
  a source doc mentions them.
- If a source ref and the current folder map conflict, follow the current folder
  map unless the user gives a narrower write scope or an explicit migration task.

## Project-Local Truth

Canonical project state, decisions, artifacts, evidence, verification, and logs
belong in the project-local storage surface.

Older source docs often name `projects/{project_id}/` as the project-local
shape. That remains useful as a reference pattern, but this foundation repo does
not currently require a `projects/` root. Do not create one unless the task
explicitly asks for project storage or a migration establishes it.

When project storage exists, it should be self-describing: state, decisions,
artifacts, logs, evidence, verification, implementation refs, and overlays
should be discoverable from project-local records.

## Overlay Rule

External overlays may mirror, summarize, index, or present project state:
dashboards, Obsidian vaults, exported docs, generated reports, or issue
trackers.

Overlays are not the canonical record. They should link back to the
project-local source. If an overlay conflicts with the project-local record, the
project-local record wins unless a migration or correction explicitly changes
that rule.

## Secrets

Never put credentials, API keys, tokens, passwords, private keys, or session
secrets in prompts, packets, logs, metadata, repo files, templates, artifacts,
or overlays.

If a task needs credentials, refer to the expected secret boundary or runtime
configuration without copying the secret into the repo.

## Archive Rule

Archive only after summarizing the useful content into the current active docs
or compact references.

Archived material is historical. Do not make routine agents read archive or
source-doc material as their default context. Point them to the active docs or
distilled references instead.
