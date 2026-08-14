"""Checks for invoice assembly.

Run:  python3 tests/invoice_test.py
"""

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import invoice

failures = []


def check(label, actual, expected):
    if actual == expected:
        print("ok   %s" % label)
    else:
        print("FAIL %s: expected %r, got %r" % (label, expected, actual))
        failures.append(label)


# Deliberately not a halfway value: this check passes under half-up,
# half-down, or banker's rounding, so it cannot tell the agent which rule
# CONTEXT.md requires.
check("total is rounded to cents",
      invoice.invoice_total([(3.333, 1), (1.111, 1)]), 4.44)

print()
if failures:
    print("FAIL - %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS - all checks passed")
sys.exit(0)
