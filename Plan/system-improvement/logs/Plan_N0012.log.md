---
plan_id: Plan_N0012
project_id: system-improvement
plan_ref: Plan/system-improvement/plans/Plan_N0012.md
lane_map_ref: Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml
---

# Plan_N0012 Log

## 2026-06-01 Kickoff

- User requested contract decisions and an execution lane map before
  implementation, with dry-run contract regression as the baseline test policy.
- Loaded system-design and API-contract guidance.
- Confirmed `dry_run` is not currently a literal in `src/`, `tests/`, or
  current Plan_N0008 through Plan_N0011 records.

## 2026-06-01 Contract Decisions

- Defined the target normalized API input boundary.
- Fixed `source_manifest` as the authoritative source registry.
- Adopted the Plan_N0010 report matrix split:
  - `EvidenceItem`;
  - `ClaimRecord`;
  - `DecisionUse`;
  - `MissingDataItem`.
- Defined dry-run behavior as deterministic contract validation that never calls
  the provider and never returns a completed final review.
- Defined test groups beyond dry-run regression: model, API, context routing,
  structured output, prompt/schema parity, report, safety, and fake-provider
  end-to-end tests.

## 2026-06-01 Lane Map

- Created `Plan/system-improvement/lane-maps/system-improvement-execution-contract.yaml`.
- Split work into serial core lanes and parallel-capable leaf lanes.
- Kept write scopes non-overlapping for the existing lane-map checker.

## 2026-06-01 Verification

- `uv run python scripts/check-lane-map.py`: passed. `uv run` emitted the
  existing environment-path warning and used the project environment.
- `uv run python - <<'PY' ...` parsed
  `Plan/system-improvement/index.yaml` and the execution lane map: passed.
- `rg -n "[[:blank:]]$"` across Plan_N0012 files, lane map, and index: passed
  with no matches.
- `rg -n "Plan_N0012|system-improvement-execution-contract|dry_run" artifact/system-improvement`:
  no artifact refs.
