# AGENTS.md

This is the first file agents read. Keep this repo simple, sufficient, and
necessary.

## Mindset
- Keep it simple. Don't create anything you can't explain the reasoning behind.
- Don't rely solely on inference. Build your results on observation and facts.
- Break down the problem into its smallest components. Make plan and set success criteria and constraints before creating deliverables.
- Everything in this repo is not to minimize effort but to maximize the quality of the output.

## Read Order

Routine agents read only these active docs:

1. `docs/01-agent-operating-contract.md`
2. `docs/02-output-verification-contract.md`
3. `docs/03-repo-boundary-and-storage-contract.md`

Open `docs/reference/` only when the task needs detail.

## Reference Map
1. `docs/reference/agent-runtime-and-scope-reference.md`
2. `docs/reference/packet-evidence-and-rework-reference.md`
3. `docs/reference/repo-boundary-and-storage-reference.md`
4. `docs/reference/verification-ci-and-pr-reference.md`

## Behavior

- Read named source refs first; do not read the whole repo by default.
- Understand task intent, expected output, write target, and verification before
  editing.
- Keep changes small and local.
- Do not invent missing facts, paths, state, roles, or requirements.
- If required context is missing or verification fails, return rework instead of
  guessing.
- You should understand the structure of this repo.
- Keep past-source material out of the current repo truth.

## Folder Map

- `app/`: future runnable app surfaces only.
- `src/`: future shared implementation code only.
- `docs/`: active docs and compact references.
- `docs/reference/`: detailed reference summaries.
- `artifact/`: foundation repo outputs or fixtures, not project logs.
- `templates/`: reusable templates.
- `tests/`: foundation contract and integrity checks.
- `.agents/skills/`: current repo-local Codex skills.
- `.codex/skills/`: preserved existing Codex skills; consult before changing.
- `.agents/plugins/marketplace.json`: local Codex plugin registry.
- `plugins/`: local plugin bundles and downloaded plugin payloads.
- `.github/workflows/ci.yml`: CI entrypoint for required checks.
- `Makefile`, `pyproject.toml`, `uv.lock`: local verification tooling.
- `Plan/`: planning and shared logs.
