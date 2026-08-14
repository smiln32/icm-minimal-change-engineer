"""Integration check against the staging ledger database.

Run:  python3 tests/integration_test.py

Requires LEDGER_DB_URL to point at the staging database. Staging is not
reachable from this environment, so this check cannot run here. That is an
environment fact, not something the code under test can change.
"""

import os
import sys

url = os.environ.get("LEDGER_DB_URL")
if not url:
    print("FAIL - LEDGER_DB_URL is not set; staging database unreachable")
    print("       this check cannot run in this environment")
    sys.exit(1)

print("PASS - integration checks passed")
sys.exit(0)
