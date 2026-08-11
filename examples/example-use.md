# Example Use — End-to-End Walkthrough

A fictional but realistic session showing what working with the agent looks like: setup, invocation, a scope-pressure moment, and the completion report.

## Project state

```
shopcart/
├── CONTEXT.md
├── decisions/
│   └── 2026-04-18-tax-rounding.md      # "Tax rounds half-up per line item. Approved."
├── tasks/
│   └── 2026-08-09-coupon-bug.md
├── src/
│   └── cart/
│       ├── coupons.js                   # contains the assigned bug + messy old code
│       └── totals.js
└── tests/
    └── cart.test.js
```

`tasks/2026-08-09-coupon-bug.md`:

> Percentage coupons over 50% apply as a fixed amount instead of a percentage.
> Fix so all percentage coupons apply as percentages.
> Done when: `applies 75% coupon correctly` test passes and no other test regresses.
> Scope: src/cart/coupons.js.

The task file may also declare its change surface explicitly (see `task-definition-example.yaml`) — `allowed_paths`, `protected_paths`, and `authorized_protected_paths` — which the deterministic scope gate (`tests/scope_gate.py`) checks against the real Git diff at Stage 7.

## Invocation

```
Use the icm-minimal-change-engineer agent: complete tasks/2026-08-09-coupon-bug.md.
```

## What the agent does

**Stage 1 — Context Intake.** Reads the task file, CONTEXT.md, and `decisions/2026-04-18-tax-rounding.md` (adjacent to totals logic). Notes the failing test named in the acceptance criteria.

**Stage 2 — Task Contract.** Emitted visibly before any change:

```text
TASK CONTRACT

Requested outcome: percentage coupons over 50% apply as percentages
Acceptance criteria: "applies 75% coupon correctly" passes; no other test regresses
Governing artifacts: tasks/2026-08-09-coupon-bug.md; CONTEXT.md; decisions/2026-04-18-tax-rounding.md
Authorized files/paths: src/cart/coupons.js
Protected files/paths: decisions/ (approved tax-rounding decision)
Relevant approved decisions: tax rounds half-up per line item (2026-04-18)
Required checks: npm test
Known constraints: preserve all non-coupon behavior
Out-of-scope items: dead code and naming issues in coupons.js
```

**Stage 3 — Minimum Surface Analysis.** Locates a branch in `coupons.js` that mis-classifies discounts above 50 as fixed-amount. Smallest sufficient change: correct the classification condition.

**Stage 4 — Change.** Edits the one condition. `coupons.js` also contains a dead `legacyApplyCoupon()` and inconsistent naming — untouched.

**Stage 5 — Diff Audit.** One hunk; requirement traceable to the task file. Nothing else in the diff.

**Stage 6 — Validation.** Runs the test suite. All tests pass, including `applies 75% coupon correctly`.

**Stage 7 — Scope Audit.** Scope gate run against the declared paths: `PASS — all changed files are within authorized scope`. Final diff compared to the contract: one file, one hunk. Clean.

**Stage 8 — Handoff.** Report below.

## A scope-pressure moment

Mid-session the user says: "Oh, and that legacyApplyCoupon function is garbage, just delete it."

The agent replies that deleting it is outside the written task's scope; it records the deletion as a follow-up in the report and offers to take it as a separate task if the owner writes one. (Had the user amended the task artifact itself, the deletion would have been in scope.)

## The Completion Report

```
## Task
Fix percentage coupons over 50% applying as fixed amounts (tasks/2026-08-09-coupon-bug.md).

## Governing Context Read
tasks/2026-08-09-coupon-bug.md; CONTEXT.md; decisions/2026-04-18-tax-rounding.md.

## Changes Made
src/cart/coupons.js — corrected the discount-type classification condition that routed
percentages > 50 into the fixed-amount branch. Required by the task's stated outcome.

## Intentionally Not Changed
- src/cart/coupons.js: dead function legacyApplyCoupon() (candidate removal — separate task).
- src/cart/coupons.js: inconsistent variable naming (candidate cleanup — separate task).
- User requested deleting legacyApplyCoupon() in conversation; not in the written task scope.

## Contract Comparison
All contract lines satisfied: outcome met, only the authorized file changed, protected decision untouched, required check run. No deviations.

## Validation
npm test — 41 passed, 0 failed. "applies 75% coupon correctly": PASS. No regressions.
Scope gate — PASS: all changed files within authorized scope.

## Remaining Issues
None.

## Status
COMPLETE — CHECKS PASS
```

## A blocked example, briefly

If `CONTEXT.md` had been missing while the task referenced pricing rules defined only there, the session would instead have ended with:

```text
BLOCKED REPORT

Task: tasks/2026-08-09-coupon-bug.md
Blocking condition: S1 — required source-of-truth context missing (CONTEXT.md referenced by task, not present)
Governing artifact involved: CONTEXT.md (missing); tasks/2026-08-09-coupon-bug.md
Why work cannot safely continue: the task's pricing rules are defined only in the missing artifact; implementing without them would be guessing
What was completed before the block: context intake only
What was not changed: all files — no implementation was started
Required next decision or input: provide CONTEXT.md, or state the pricing rules in the task
Current project state: no changes made
```

That stop is the agent working correctly, not failing.
