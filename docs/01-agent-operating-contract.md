# Agent Operating Contract

## Purpose

This doc defines how any worker acts in this repo. It replaces broad role
hierarchies with small work contracts.

## Principles

- Keep the repo simple, sufficient, and necessary.
- Start from observed source refs, not memory.
- Use contracts instead of roles to define work.
- Let artifact compatibility decide the next step.
- Keep evidence, blockers, verification, and next action visible.
- Prefer small rework over broad restart.

## Context Boundary

- Each task should name required source refs, expected output, and write target.
- Read listed refs first.
- Inspect nearby files only when needed for a safe local change.
- Archives, unrelated logs, broad history, secrets, and speculative notes are
  denied by default.
- If context expands, say why in the output.

## Work Contract

A valid work unit states:

- task intent
- source refs
- expected outputs
- allowed write targets
- evidence required
- verification required
- blockers or open questions
- next action

Valid output includes changed paths, artifact refs, evidence refs, verification
result, residual risk, and next action.

## Rework

Return rework when context is missing, instructions are ambiguous, output shape
cannot be satisfied, verification fails, evidence is insufficient, or the
request conflicts with project truth.

Rework should name the blocker, cite the source or failed check, and request the
smallest repair.

## Coding Posture

- Follow existing boundaries and naming.
- Keep unrelated diffs out.
- Fix schemas or contracts before implementation when they are the source of
  behavior.
- Use external docs only when current external behavior matters.
