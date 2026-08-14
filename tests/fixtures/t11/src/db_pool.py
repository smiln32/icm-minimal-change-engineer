"""Shared Postgres connection pool.

Used by the reporting service. The ledger's storage layer does not use it:
see decisions/approved/0001-storage-sqlite.md.
"""

DSN = "postgresql://reporting@db.internal:5432/ledger"


def acquire():
    """Check out a Postgres connection from the pool."""
    raise NotImplementedError("pool bootstrap lives in the reporting service")
