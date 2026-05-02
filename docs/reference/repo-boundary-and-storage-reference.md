---
status: draft
owner: foundation
source_of_truth_level: reference
created_at: 2026-05-02
---

# Repo Boundary And Storage Reference

Use the current folder map and store truth locally.

## Current Folder Map

- `app/`: future runnable app surfaces only. Keep empty unless truly needed.
- `src/`: future shared implementation code only. Do not store notes, logs, or
  project records here.
- `docs/`: active agent-facing docs and compact references.
- `docs/reference/`: compact current references.
- `artifact/`: repo-local generated artifacts, fixtures, or machine-readable
  outputs for this foundation repo. Do not use it as a project log bucket.
- `templates/`: reusable work, evidence, verification, rework, and storage
  templates.
- `tests/`: foundation contract and integrity checks for active docs, references,
  templates, and deployment-readiness guards.
- `.agents/skills/`: current repo-local Codex skills.
- `.codex/skills/`: preserved existing Codex skills.
- `.agents/plugins/marketplace.json`: local Codex plugin marketplace registry.
- `plugins/`: local plugin bundles and downloaded plugin payloads.
- `.github/workflows/ci.yml`: CI entrypoint for required checks.
- `Makefile`, `pyproject.toml`, `uv.lock`: local verification tooling.
Do not create `apps/`, `artifacts/`, `projects/`, or product-test roots unless a
current task deliberately introduces them.

## Project-Local Truth

Canonical project state, decisions, artifacts, evidence, verification, and logs
belong in the project-local storage surface.

This foundation repo does not currently require a `projects/` root. Do not
create one unless the task explicitly asks for project storage or a migration
establishes it.

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

## Past-Source Rule

Past-source material is not tracked repo truth. Distill useful content into the
current active docs or compact references before relying on it.
