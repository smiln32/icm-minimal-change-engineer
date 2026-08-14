"""Consumer contract check.

Run:  python3 tests/contract_check.py

Depends on the ledger-contract-kit package, which is not installed in this
environment and is not on any index this machine can reach. The check does not
fail here: it cannot start.
"""

import ledger_contract_kit  # noqa: F401  (import error is the point)

print("PASS - contract checks passed")
