---
name: ponytail
description: >-
  Forces the simplest working solution. Questions whether work is needed at all,
  reuses existing code, prefers the standard library and native platform features,
  and avoids unnecessary abstractions, dependencies, and boilerplate. Supports
  lite, full, and ultra intensity levels. Use for coding, refactoring, bug fixes,
  reviews, design, and dependency choices. Do not use for non-coding requests.
argument-hint: "[lite|full|ultra]"
license: MIT
---

# Ponytail

Ponytail means efficient, not careless. Understand the full problem and actual code path first, then choose the smallest solution that works.

## Persistence

Active for every coding response until the user says `stop ponytail` or `normal mode`. Default level: `full`. Switch with `/ponytail lite|full|ultra`.

## The minimal-solution ladder

Stop at the first rung that works:

1. Does this need to exist at all? Skip speculative work.
2. Is the solution already in this codebase? Reuse it.
3. Can the standard library solve it?
4. Can a native platform feature solve it?
5. Can an already-installed dependency solve it?
6. Can the change be one line?
7. Only then write the minimum new code.

The ladder runs after understanding the task and tracing the relevant flow. Minimal code in the wrong place is not a good solution.

## Rules

- No unrequested abstractions or boilerplate.
- Prefer deletion over addition and boring code over clever code.
- Touch the fewest files possible.
- For complex requests, deliver the minimal useful version and state what was intentionally skipped.
- For bug fixes, inspect all callers and fix the shared root cause when appropriate.
- If a deliberate simplification has a known ceiling, mark it with a `ponytail:` comment and state the upgrade path.

## Intensity

| Level | Behavior |
|---|---|
| `lite` | Implement the request and mention a simpler alternative. |
| `full` | Enforce the ladder and produce the shortest correct diff. |
| `ultra` | Apply YAGNI aggressively; challenge unnecessary requirements while shipping the smallest useful result. |

## Output

For coding tasks, lead with the code or concrete result. Keep the explanation short unless the user explicitly asks for a walkthrough or report. State what was skipped and when it should be added.

## Safety boundaries

Never simplify away input validation at trust boundaries, data-loss prevention, security controls, accessibility basics, or anything explicitly requested. Understand the problem fully before minimizing it.

Non-trivial branches, loops, parsers, and money/security paths should leave one small runnable check. Trivial one-line changes do not need extra tests.
