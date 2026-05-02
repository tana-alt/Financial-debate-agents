# Repo Boundary And Storage Contract

## Active Surface

Routine agents read `AGENTS.md` and the three active docs in `docs/`. Detailed
current material lives in `docs/reference/`.

## Folder Rules

- `app/`: runnable app code only when this repo truly needs it.
- `src/`: shared implementation code only.
- `docs/`: active docs and reference summaries.
- `artifact/`: foundation repo outputs, fixtures, or generated records.
- `templates/`: reusable templates only.
- `tests/`: foundation contract and integrity checks only.
- `.agents/skills/`: current repo-local Codex skills.
- `.codex/skills/`: preserved existing Codex skills; consult before changing.
- `.agents/plugins/marketplace.json`: Codex plugin registry.
- `plugins/`: local plugin bundles and downloaded plugin payloads.
- `.github/workflows/ci.yml`: CI entrypoint for required checks.
- `Makefile`, `pyproject.toml`, `uv.lock`: local verification tooling.

The current `tests/` root is deliberately introduced for this foundation repo's
verification checks. Do not treat `apps/`, `artifacts/`, `projects/`, or
product-test references as current roots unless those folders are deliberately
introduced.

Do not restore old `.agents` surfaces outside current skills and plugin
marketplace registry.
Do not commit local Serena runtime state; `.serena/` is ignored local tool state,
not project truth.
Do not commit past-source archives; `archive/` is ignored local material, not
project truth.

## Storage And Overlays

Project truth should be project-local when project repos exist. Overlays such as
dashboards, vaults, summaries, and generated views are not canonical unless a
storage map says so.

## Packets And Secrets

Packets carry refs such as `content_ref`, `body_ref`, and `evidence_refs`; they
must not embed raw content bodies or credentials.

Secrets, tokens, cookies, browser sessions, API keys, and private credentials
must not be written into prompts, packets, logs, metadata, or repo files.

## Past-Source Rule

Distill useful past-source content into active docs or current references before
using it. Past-source copies should stay outside tracked repo truth.
