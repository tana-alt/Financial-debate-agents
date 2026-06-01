---
name: tdd-scope
description: "Use when a bug fix, regression-prone logic change, API behavior change, or reusable component has clear expected behavior and should be implemented test-first with a focused failing test."
---


## Purpose

Use tests to define behavior before changing implementation when the behavior is important or regression-prone.

## Effect

When this skill fires, capture expected behavior in the smallest useful failing
test before implementation when practical. The test should protect externally
visible behavior, regression proof, or API contract behavior rather than
implementation trivia.

## Use when

- Fixing a bug with clear reproduction.
- Adding important domain logic.
- Changing API behavior.
- Adding reusable components or utilities.
- Preventing a regression from returning.

## Do not use when

- The change is trivial styling, copy, formatting, renaming, mechanical
  migration, or dependency-only work.
- The task is only to add tests after an already-complete implementation.
- Expected behavior is ambiguous and needs `system-design`, `api-contract`, or
  user clarification first.
- The main need is release verification; use `release-check`.

## Success conditions

- A focused failing test exists first when practical.
- The implementation is the smallest change that passes the test.
- Edge/error cases are covered when they define the behavior.
- Existing relevant tests still pass.

## Constraints

- Do not force TDD for trivial styling or mechanical renames.
- Do not add broad snapshot tests when behavior tests are better.
- Do not leave skipped, disabled, or brittle tests.
- Do not overfit tests to implementation details unless necessary.

## Stop guidance

Stop before implementation if no focused failing test can be written and explain
why. Stop if behavior is unclear or requires contract/design decisions first.
Stop expanding tests once the regression or behavior boundary is covered.

## Output

- Behavior being protected.
- Failing test name/path and why it fails before implementation, when practical.
- Minimal implementation change made to pass it.
- Verification command/result.
- Any behavior intentionally left untested.
