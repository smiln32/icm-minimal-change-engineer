"""Dependency-free checks for the ledger.

Run:  python3 tests/billing_test.py
Exit 0 = every check passed. No test framework, no packages to install.
"""

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import billing
import storage

failures = []


def check(label, actual, expected):
    if actual == expected:
        print("ok   %s" % label)
    else:
        print("FAIL %s: expected %r, got %r" % (label, expected, actual))
        failures.append(label)


check("no discount below the tier 2 minimum",
      billing.bulk_discount_rate(9), 0.0)
check("tier 2 rate applies at the minimum",
      billing.bulk_discount_rate(10), 0.10)
check("tier 2 rate applies above the minimum",
      billing.bulk_discount_rate(50), 0.10)
check("line total applies the discount",
      billing.line_total(10.0, 10), 90.0)
check("invoice lookup returns the record",
      storage.get_invoice("inv-2")["quantity"], 3)
check("invoice search honours its limit",
      storage.find_invoices("c-100", limit=1), ["inv-1"])

print()
if failures:
    print("FAIL - %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS - all checks passed")
sys.exit(0)
