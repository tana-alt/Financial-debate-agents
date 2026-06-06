---
plan_id: Plan_N0007
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0007.log.md
---

# System Design ADR Plan

## 0. Goal

Create system-design ADRs for the next architecture decisions in the Earnings
Debate Agent submission refactor:

1. API ingestion and trust boundary for `filing_url` and `document_files`.
2. Agent graph alignment with the current runtime implementation.
3. Synchronous API execution as the MVP public contract.

The ADRs must explain options, tradeoffs, verification, rollback or mitigation,
and residual risk.

## 1. Scope And Write Targets

Allowed write targets:

```text
Plan/system-improvement/index.yaml
Plan/system-improvement/plans/Plan_N0007.md
Plan/system-improvement/logs/Plan_N0007.log.md
artifact/system-improvement/output/Plan_N0007/system-design-adr-index.md
artifact/system-improvement/output/Plan_N0007/adr-0001-api-ingestion-boundary.md
artifact/system-improvement/output/Plan_N0007/adr-0002-align-agent-graph-to-runtime.md
artifact/system-improvement/output/Plan_N0007/adr-0003-keep-synchronous-review-api.md
artifact/system-improvement/manifest.yaml
```

Read-only source refs:

```text
README.md
docs/01-agent-operating-contract.md
docs/02-output-verification-contract.md
docs/03-repo-boundary-and-storage-contract.md
docs/reference/repo-boundary-and-storage-reference.md
Plan/README.md
artifact/README.md
src/api.py
src/main.py
src/workflow.py
src/workflow_agents.py
src/workflow_runtime.py
src/workflow_models.py
src/preprocessor.py
src/llm.py
tests/
```

Out of scope:

```text
- implementing the ADR decisions in product code
- changing API behavior in this plan
- dependency changes
- external writes
- deployment, release, push, merge, or PR creation
```

## 2. Method

Use the `system-design` skill packet shape:

- problem, actors, success criteria, and non-goals
- constraints and affected boundaries
- observable quality targets
- options considered
- selected option and tradeoffs
- verification
- rollback or mitigation
- residual risk
- human gate status

## 3. Stop Conditions

The plan is complete when:

- the three ADRs exist under `artifact/system-improvement/output/Plan_N0007/`;
- ADR-0001 explains the API ingestion boundary in enough detail to guide a
  later implementation decision;
- ADR-0002 records the user's decision to align documentation and design with
  the current runtime agent graph;
- ADR-0003 records the user's decision to keep synchronous API execution;
- project index and artifact manifest reference the new output package;
- YAML files parse and touched files have no trailing whitespace.
