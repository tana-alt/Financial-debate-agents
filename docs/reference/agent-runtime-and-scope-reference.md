---
status: draft
owner: foundation
source_of_truth_level: reference
created_at: 2026-05-02
---

# Agent Runtime And Scope Reference

This reference summarizes runtime, scope, invocation, and dependency-map rules.
It is reference material, not routine context for every worker.

Routine agents start from the user request, named source refs, and nearest
relevant files. They do not begin by reading broad runtime maps or the repo.

A bounded work contract names task intent, `source_refs`, expected outputs,
allowed write targets, evidence and verification requirements, and the blocker
or rework path.

Named source refs come first. Required context is the smallest set of refs
needed to perform the work safely. Optional context may improve quality, but it
is not a default reading surface.

Denied-by-default context includes archive, broad logs, unrelated history,
secret material, and broad runtime maps. Read it only when the task explicitly
names it or a concrete blocker requires scoped expansion.

Context may expand when a named ref points to a required schema, template, or
nearby implementation; verification requires nearby files; the contract cannot
be satisfied without a missing source ref; or a security, compliance, or
data-sensitivity concern appears.

Missing context becomes a focused question or rework record. Workers must not
invent facts, requirements, strategy, state, paths, or implementation details.

The main lane or scheduler may read routing maps when resolving work shape,
target skill, dependency edges, call validity, or contract drift.

Specialist workers receive scoped input docs named by the packet or handoff,
output docs and write targets, local skill docs, packet templates named by the
handoff, and compact lesson or runtime identity refs when explicitly provided.

Specialists should not self-expand into broad maps, archive, root history, or
unrelated project context. If their scoped context is insufficient, they emit
rework or ask for a scoped handoff.

Workflow is output-to-input compatibility, not role hierarchy.

```text
prior output artifact
  -> next input requirement
  -> next bounded work unit
```

Each output should carry artifact or packet refs, changed paths, evidence refs,
verification results, blockers or open questions, and `next_owner` or terminal
status. If the prior output does not satisfy the next input contract, the next
step is rework or scoped clarification.

Agent calls have three layers:

- trigger source: human request, scheduled job, monitor signal, handoff, or
  rework packet
- call decider: main lane for human, ambiguous, monitor, handoff, or rework
  routing; registered scheduler for pre-registered scheduled work
- actual invoker: runtime

Specialists request the next owner by emitting a packet, handoff, rework,
operation record, or `next_owner` field. They do not directly spawn broad agent
work.

Runtime validates the resolved call, starts the target skill scope, injects the
scoped request, records activity, and enforces preflight and postflight checks.
Runtime is not a strategy owner and must not inject whole-repo context.

Use runtime maps when resolving source-ref scope, target skill or call request
validity, input and output contract compatibility, registered output or
write-target boundaries, or runtime preflight, postflight, session, rate-limit,
and secret checks.

Treat legacy runtime wording as compatibility history when it conflicts with
the active Foundation direction.

Cron and scheduled work use the same scoped contract concept as human work.

A scheduled request should name target skill, task intent, runtime identity or
project refs, source refs, expected outputs, write targets, and verification or
evidence requirements.

If a scheduled request is ambiguous or missing required refs, route it to the
main lane or emit rework instead of widening context automatically.

Do not promote old SNS/channel/project_supervisor details into the current
active Foundation structure. Older source docs may contain useful runtime
principles, but their domain-specific examples are historical source material
unless an active work contract explicitly names them.