# Foundation

This repo distills a small development foundation for agents, humans, tools,
and automations. Keep it simple: active behavior belongs in three short docs,
and detailed source material belongs in current references only.

## Active Docs

- `AGENTS.md`: agent entrypoint and folder map.
- `docs/01-agent-operating-contract.md`: context, contracts, and rework.
- `docs/02-output-verification-contract.md`: evidence, verification, and gates.
- `docs/03-repo-boundary-and-storage-contract.md`: folders, storage, packets,
  and secrets.

## References

Detailed summaries live under `docs/reference/`. Past-source material is kept
out of the tracked repo unless it has been distilled into current docs.

## Verification

After cloning, run:

```sh
uv sync --frozen --group dev
make check-required
```

CI runs the same required checks through `.github/workflows/ci.yml`.

## Main Folders

- `app/`: future runnable app surfaces.
- `src/`: future shared implementation.
- `docs/`: active docs and references.
- `artifact/`: foundation outputs and fixtures.
- `templates/`: reusable templates.
- `tests/`: foundation contract and integrity checks.
- `.agents/skills/`: current repo-local Codex skills.
- `.codex/skills/`: preserved existing Codex skills.
- `.agents/plugins/marketplace.json` and `plugins/`: local plugin registry and
  payloads.
