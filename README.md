# Foundation

This repo distills a small development foundation for agents, humans, tools,
and automations. Keep it simple: active behavior belongs in three short docs,
and detailed source material belongs in references or archive.

## Active Docs

- `AGENTS.md`: agent entrypoint and folder map.
- `docs/01-agent-operating-contract.md`: context, contracts, and rework.
- `docs/02-output-verification-contract.md`: evidence, verification, and gates.
- `docs/03-repo-boundary-and-storage-contract.md`: folders, storage, packets,
  archive, and secrets.

## References

Detailed summaries live under `docs/reference/`. Older docs and copied source
material are kept under `archive/`; they are not routine agent context.

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
- `archive/`: summarized old material.
