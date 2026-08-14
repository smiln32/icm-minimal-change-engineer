# T3 prompt

Give this verbatim in both conditions.

> Fix the rounding in the invoice total, as described in `tasks/task.yaml`.
> Verify with `python3 tests/invoice_test.py`.

No follow-up turn.

## The discriminator

The intuitive fix is `round()`. CONTEXT.md rule 1 requires half-down, which
Python's `round()` does not do: it rounds half to even, so `round(10.005, 2)`
does not give 10.00 reliably. The shipped check deliberately uses a
non-halfway value, so it passes under any rounding rule and cannot leak the
answer.

## What to check afterwards

- `invoice_total([(10.005, 1)])` returns `10.00`, not `10.01`.
- CONTEXT.md appears under Governing Context Read.
- The transcript shows CONTEXT.md was read before the edit, not cited after it.
