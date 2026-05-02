# Repo Boundary And Storage Contract

## Active Surface

Routine agents read `AGENTS.md` and the three active docs in `docs/`. Detailed
or historical material lives in `docs/reference/`, `archive/source-docs/`, or
`archive/`.

## Folder Rules

- `app/`: runnable app code only when this repo truly needs it.
- `src/`: shared implementation code only.
- `docs/`: active docs and reference summaries.
- `artifact/`: foundation repo outputs, fixtures, or generated records.
- `templates/`: reusable templates only.
- `archive/`: summarized old material.

Do not treat legacy `apps/`, `artifacts/`, `projects/`, or `tests/` references
as current roots unless those folders are deliberately introduced.

## Storage And Overlays

Project truth should be project-local when project repos exist. Overlays such as
dashboards, vaults, summaries, and generated views are not canonical unless a
storage map says so.

## Packets And Secrets

Packets carry refs such as `content_ref`, `body_ref`, and `evidence_refs`; they
must not embed raw content bodies or credentials.

Secrets, tokens, cookies, browser sessions, API keys, and private credentials
must not be written into prompts, packets, logs, metadata, or repo files.

## Archive Rule

Summarize useful content into active docs or references before archiving old
docs. After summary, old source material should not remain routine context.
