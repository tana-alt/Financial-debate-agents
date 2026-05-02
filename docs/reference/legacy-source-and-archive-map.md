---
status: draft
owner: foundation
source_of_truth_level: reference
created_at: 2026-05-02
---

# Legacy Source And Archive Map

## Purpose

This map identifies which legacy and historical docs still matter, what has
already been summarized, and what should move to `archive/` after coverage
exists. It is a source-coverage map, not a new operating contract.

## Classification Rules

- `keep active`: still useful as a current entrypoint after any needed cleanup.
- `summarize then archive`: useful content should be carried into active docs or
  compact reference docs, then the source copy should leave the active surface.
- `source/reference only`: copied or detailed material that should be read only
  for migration, verification, or provenance.
- `legacy-only`: superseded material that should not guide current work except
  as history.

## Current Root Docs

- `AGENTS.md`: keep active. It is the current short routing map and names the
  desired three-doc active direction under `docs/`.
- `README.md`: keep active only as a human index. It should point readers to the
  current foundation docs and references, not preserve old runtime assumptions.
- `archive/legacy-root-docs/ARCHITECTURE.md`: archived source. If rewritten, a
  new architecture doc should describe current repo boundaries, not the old
  parent/subagent hierarchy.
- `archive/legacy-root-docs/rules.md`: archived source. It contains useful
  coding and verification principles, but its long absolute MODEL-APP-FLOW
  links are stale for this repo.
- `archive/legacy-root-docs/01-principles.md` through
  `archive/legacy-root-docs/06-rework-loop.md`: archived source covered by the
  three active docs.
- `archive/legacy-root-docs/10-test-and-verification-inventory.md`: archived
  source for verification reference.
- `archive/legacy-root-docs/20-agent-thinking-extraction.md`: archived source
  for worker-contract ideas.
- `archive/legacy-root-docs/30-repo-architecture-overview.md`: archived source
  for the old MODEL-APP-FLOW app/runtime layout.

## Source Docs

- `archive/source-docs/README.md`: source/reference only. It indexes copied historical
  refs, but lists missing `archive/source-docs/agent-thinking/AGENTS.md` and
  `archive/source-docs/agent-thinking/ARCHITECTURE.md`.
- `archive/source-docs/agent-thinking/`: source/reference only. It preserves context
  scope, agent I/O contracts, packet shapes, runtime policy, and harness
  material.
- `archive/source-docs/test-and-ci/`: source/reference only. It preserves Makefile, CI,
  strict typing, PR evidence, regression, infra, and human-gate material.
- `archive/source-docs/architecture/`: source/reference only. It preserves repo profile
  split, backend instructions, repo README, docs index, and profiles manifest.
- `archive/legacy-untitled-folder/`: legacy-only. It duplicates older AGENTS, ARCHITECTURE,
  rules, context-scope, dependency-map, harness, and project-operation docs.
- `archive/legacy-skills/`: legacy-only. It keeps old `.agents`, `.claude`,
  root `.codex` duplicates, and project-specific skills after consolidation.
- `archive/project-orchestration/`: legacy-only. It preserves the old project
  boundary policy without keeping it on the active surface.

## Known Conflicts

- `rules.md` contains many absolute links to
  `/Users/yamamotokaito/Desktop/MODEL-APP-FLOW/...`; these are legacy source
  references, not current Foundation-development paths.
- Older docs refer to `apps/`, populated `src/services`, `tests/`, and broad
  `artifacts/` roots as active implementation/runtime surfaces. In this repo,
  `app/` and `src/` are future surfaces, and `artifact/` is for repo-local
  generated artifacts.
- `archive/source-docs/README.md` lists missing files:
  `archive/source-docs/agent-thinking/AGENTS.md` and
  `archive/source-docs/agent-thinking/ARCHITECTURE.md`.
- Parent/subagent hierarchy, `main_lane`, `project_supervisor`,
  `channel_operator`, and related role maps are historical. Current foundation
  docs should keep the reusable ideas: scoped context, explicit contracts,
  evidence, verification, project-local truth, and small rework.
- Old Obsidian, SNS, LangGraph, and repo-profile export references are
  provenance unless a current task explicitly names that surface.
- Old `.agents/skills` and `.claude/skills` mirrors are archived. Current
  generic skills live under `.codex/skills` only. The allowed `.agents` surface
  is `.agents/plugins/marketplace.json` for local Codex plugin registration.

## Archive Rule

Do not archive source material until active docs and `docs/reference/` coverage
exist for the useful content. After coverage exists, archive old roots and
copied historical refs to reduce the active reading surface.

```text
legacy/source doc
  -> active contract doc or compact reference doc
  -> archive source copy
```

Archive moves should preserve provenance and should not change active contracts
at the same time.
