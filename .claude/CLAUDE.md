# CLAUDE.md — Working rules for icm-minimal-change-engineer

Rules for working in this repository. This file is deliberately short. The
governing truth for this project lives in `icm/SPEC.md`, not here.

---

## 1. GOVERNING ARTIFACTS

- **`icm/SPEC.md` is the source of truth for this package.** Read it before any
  substantive change. Its §3 governing principles rank above anything in this
  file; where the two conflict, SPEC wins.
  - _Why: this package's premise is that project truth lives in artifacts, not
    in model memory or conversation. A rules file that restated SPEC §3 would
    be a second copy of it, which §3 of this file forbids._

- **`icm/BRIEF.md` records the approved design decisions (B1–B17).** They are
  settled. Surface a conflict and stop; never silently reconsider one.

- **`HANDOFF.md` carries current state, newest addendum last.** Amend it by
  appending a dated addendum, never by rewriting the history above it (B14).

- **`icm/TASK.md`** is the completed v0.1.0 build plan, retained as history.

---

## 2. GIT

- **Never push. The maintainer pushes, and only when they choose to.** Do not
  run `git push` under any circumstances, including when a task feels
  finished, when asked to "wrap up," or when a commit is the last step.
  Commit, report the branch name and how many commits are unpushed, and stop
  there.
  - _Why: publication timing is the maintainer's decision alone. This replaced
    an inherited "push after every commit" rule; see the 2026-08-12 addendum
    in `HANDOFF.md`._

- **Never work directly on `main`.** Branch from it: `feature/`, `fix/`,
  `chore/`, or `experiment/` plus a lowercase hyphenated description.

- **Commit each working change as it lands**, formatted `type: short
  description`. Do not batch a session's work into one commit.

---

## 3. SINGLE SOURCE OF TRUTH (BRIEF B16)

- **A fact may be stored once.** Living documents describe a fact and point at
  the artifact that owns it. They never carry a copy of it. This binds hardest
  on counts, versions, and inventories.
  - _Why: a fact stored twice drifts. The self-test scenario count drifted
    three times before this rule existed._

- The self-test script headers own their scenario inventories. `README.md`
  describes them and deliberately carries no numeric count;
  `tests/validate_package.py` fails if one is reintroduced, and enforces
  contiguous numbering and a one-way floor ratchet on the suites themselves.

- **No check may fire predictably on a known-intermediate state.**
  - _Why: routine failures train alarm fatigue, and an alarm the author has
    learned to ignore is not a control._

- An unperformed check must never read as a passed one (B9). Where a check
  cannot run, say so in the output rather than staying silent.

---

## 4. VERIFYING WORK HERE

Run all four before reporting anything complete. This is the "four-command
battery" referenced throughout `CHANGELOG.md` and `HANDOFF.md`.

```bash
python3 tests/validate_package.py
bash tests/scope_gate_selftest.sh
bash tests/validator_selftest.sh
bash tests/hooks_selftest.sh
```

On Windows, set `PYTHONUTF8=1` first, or `cp1252` console encoding mangles the
scripts' own output. One scope-gate scenario creates a filename containing `"`,
which NTFS cannot represent, so that single case fails there regardless. Both
are environment limits, not defects; every other case must pass.
