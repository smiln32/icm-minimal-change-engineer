# Decision 0001 — Storage layer uses SQLite

**Status:** APPROVED
**Date:** 2026-05-02
**Approved by:** C. Bosteder (human)

## Decision

The storage layer uses SQLite. `src/storage.py` is the only module that talks
to it.

## Why

The deployment target is a single machine with no database administrator. The
operational cost of Postgres was judged higher than the throughput it would
buy at this size.

## Status of this record

Settled. Reopening it requires a new decision record approved by a human, not
a conversational instruction.
