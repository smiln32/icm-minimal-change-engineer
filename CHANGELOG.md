# Changelog

All notable changes to this project are documented in this file.
Format follows Keep a Changelog conventions; versioning follows Semantic Versioning.

## [Unreleased]

### Added
- First recorded T1–T12 behavioral test run (`tests/behavioral-run-results.md`): 12 of 12 conclusive and fully compliant. T8's first fixture had a design flaw (an unintended public escape hatch); rebuilt with no allowed-paths-only solution possible and re-run, producing a correct zero-diff `BLOCKED` (S4) report.
- Optional Claude Code mechanical enforcement under `hooks/`, implementing enforcement-roadmap items 1 and 4 (off by default): `protect_governing_files.py` (PreToolUse) makes CONTEXT.md/decisions/governance/specs mechanically uneditable; `run_scope_gate_on_stop.py` (Stop) re-runs the scope gate automatically at handoff when a session opts in via `ICM_TASK_FILE`. Both reuse `tests/scope_gate.py`'s own path-matching functions rather than duplicating the logic. See `docs/enforcement-roadmap.md` for the design and known limits.
- `.gitignore` for Python cache artifacts.

## [0.2.7] - 2026-08-09

### Changed
- Eliminated the duplicated scenario-count fact rather than continuing to police it. The self-test script's numbered header is now the single source of truth for the scenario inventory; the README describes coverage qualitatively and carries no copied number. The validator's check inverted from copy-consistency to source integrity plus reintroduction ban: scenario markers must be contiguous 1..N (catches renumbering gaps and duplicates), the suite may never shrink below its shipped floor (a one-way ratchet — fires on deletion, never on growth), and any numeric self-test count claim in the README is rejected outright. Verified that the historical drift condition — suite grows while README lags — no longer produces a false fire, ending the mild alarm-fatigue pattern the old design guaranteed.

### Added
- Validator self-test cases for all three new failure modes: reintroduced numeric claim, scenario-numbering gap, and suite shrink below the floor — each proven to fail with its expected message in the git-clone fixture.
- Design record BRIEF B16 (single source of truth for derived facts; no check may fire predictably on known-intermediate authorial state).

## [0.2.6] - 2026-08-09

### Fixed
- F7: truncated or malformed NUL-terminated git output now raises the contracted error (mapped to exit 3) in all three parse branches instead of crashing with IndexError — including the status-rename branch, where silent tolerance of truncation would have *dropped* a changed path (a fail-open found while fixing the crash).
- F10: a path violating both the scope and protected rules is reported once, under the graver protected classification, annotated "(also outside authorized scope)"; exit-code precedence unchanged.
- F11: validator robustness — stage counting accepts dash variants; the ten-principle count is scoped to the governing-principles section so numbered lists elsewhere cannot inflate it; the scenario count derives from the highest marker number, immune to duplicate mentions.
- F12: the validator now syntax-parses both shipped Python files and import-checks the gate's required functions, so a syntactically broken gate can no longer pass structural validation.

### Closed coverage gaps (last, as directed)
- G1: the exit-3 error contract is now fully exercised — usage errors, unreadable and malformed task files, malformed streams, and nonexistent `--base` refs (scenarios 13, 17, 19).
- G2: the default-mode audit boundary is exercised live — a committed out-of-scope change passes default mode with the boundary note and is caught under `--base` (scenario 20).
- G3: validator negative testing is now reproducible and runs where users run it — `tests/validator_selftest.sh` exercises the validator in a git-clone fixture, both directions, six cases; the exact blind spot that let the F3 regression ship.

### Audit ledger
All findings from the v0.2.2 self-audit are now closed: F1–F12 fixed (F4 surfaced as a documented boundary), G1–G3 covered. No known open defects remain from that audit; that statement is about the audit's findings, not a claim that no defects exist.

## [0.2.5] - 2026-08-09

### Fixed
- F8: the task-YAML parser now follows YAML semantics and fails closed. Duplicate tracked keys: last occurrence wins. An inline value or `[]` closes its key, so stray `- item` lines can no longer leak into it. Structurally malformed input — indented tracked keys, bare top-level junk, or dangling list items outside any open key — exits 3 instead of silently mis-parsing. The dangling-item rule was added mid-fix after diff audit: items silently dropped after `protected_paths: []` would have meant silently-unprotected paths, a fail-open.
- F9: an `allowed_paths` entry of `.` explicitly grants the whole repository, with `protected_paths` rules still enforced on top (verified: protected violations still exit 2 under a whole-repo allowance). Path matching remains case-sensitive by design — case-folding would silently widen scope on case-sensitive filesystems — but a scope failure that would match ignoring case now carries a casing hint naming the near-miss.

### Added
- Self-test scenarios 17 (three exit-3 malformation cases via CLI plus last-wins/key-closing unit checks) and 18 (whole-repo allowance, protected-under-dot interplay, strict case failure with hint).

### Still open (from the v0.2.2 self-audit)
- F7 malformed-stream IndexError, F10–F12 minor, coverage gaps G2–G3.

## [0.2.4] - 2026-08-09

### Fixed
- F5: the hide-by-ignore-rule bypass is closed — if a diff touches any `.gitignore`, ignored-untracked files join the changed set and face `allowed_paths` like every other change. Deliberate tradeoff: pre-existing ignored artifacts surface whenever ignore rules change. Residual, documented: `.git/info/exclude` and `core.excludesFile` live outside the diffable tree and stay beyond this gate's reach (roadmap: filesystem enforcement).
- F6: path normalization uses `posixpath.normpath`, so `/` is the only separator and a backslash is preserved as ordinary POSIX filename data; the speculative Windows `.replace()` that corrupted such names is removed. Paths in task files must use forward slashes on all platforms.

### Changed
- F4: the default-mode audit boundary is now explicit — a default-mode PASS appends a note that only uncommitted work (working tree + index vs HEAD) was audited, and the agent specification instructs treating a post-commit default-mode PASS as no evidence, re-running with `--base <pre-task ref>`. The gate cannot know the task's start commit unless told; this boundary is surfaced rather than silently held.

### Added
- Self-test scenarios 15 (ignore-bypass, both directions: committed rules leave ignored files invisible; a `.gitignore` edit pulls them into the scope check and names the hidden file) and 16 (default-mode note present; absent under `--base`); backslash-preservation assertion added to the normalize unit checks.

### Still open (from the v0.2.2 self-audit)
- F7 malformed-stream IndexError, F8–F12 minor parser/validator looseness, coverage gaps G2–G3.

## [0.2.3] - 2026-08-09

### Fixed
- F1: usage errors in the scope gate now exit 3 per the documented contract; argparse's default exit 2 collided with the protected-artifact violation code, so a typo'd flag could be read by exit-code-keying wrappers as protected tampering.
- F2: comment stripping in the task-YAML parser follows the YAML rule — '#' starts a comment only at line start or after whitespace — so paths containing '#' (src/app#old.py) survive as data instead of being truncated into unintentionally broader scope entries. Residual deviation documented: a whitespace-preceded '#' comments even inside quoted items.
- F3: the validator's empty-directory check no longer descends into dot-directories, so it passes on real git clones (which legitimately contain empty dirs such as .git/refs/tags) while still failing on planted non-dot empty directories. Regression introduced by the v0.2.2 packaging checks and missed because earlier fixtures were never git repositories.

### Added
- Self-test scenarios 13 (usage errors exit 3: unknown flag, missing --task, unreadable task file) and 14 ('#'-in-path preserved, whitespace-preceded '#' stripped).
- F3 verified in a git-clone fixture in both directions (clean clone passes; planted empty dir still fails).

### Known and deliberately unfixed (from the v0.2.2 self-audit)
- F4 default-mode blindness to committed changes, F5 .gitignore bypass, F6 backslash-filename corruption, F7 malformed-stream IndexError, F8–F12 minor parser/validator looseness, and coverage gaps G2–G3 remain open and on record.

## [0.2.2] - 2026-08-09

### Fixed
- Packaging: removed a spurious empty directory (literal unexpanded brace-expansion name) created during initial scaffolding; the validator now rejects unexpected top-level entries and empty directories anywhere in the package.
- `normalize()` in the scope gate: now collapses `.` and `..` components (`src/../foo` matches `foo`), strips only a literal `./` prefix instead of `lstrip("./")` — the old character-stripping silently turned `../etc` into `etc`, converting a parent-escaping path into an innocent-looking in-repo one — and preserves leading `..` so parent-escaping paths remain visibly out of scope.
- Git path extraction switched to NUL-terminated output (`-z`) for `diff --name-status`, `status --porcelain=v1`, and `ls-files`, eliminating C-style quote handling entirely; filenames with spaces, quotes, and non-ASCII are read raw. Rename record layouts differ under `-z` and both parsers were restructured accordingly (status `-z` reports the new path first, then the original).

### Added
- Three self-test scenarios: special-character filename detected raw (10), dotted/parent components in `allowed_paths` match after normalization (11), and `normalize()` unit checks including the lstrip parent-escape regression (12).
- Validator packaging-hygiene and scenario-count-consistency checks.

### Changed
- Case-count language harmonized to "N scenarios plus output assertions" across README and self-test; the 0.2.1 changelog entry's miscount is corrected in place with a dated note, while the accurate 0.2.0 count is left as historical record.
- Scope-gate docstring and example task file now state the supported YAML subset explicitly and warn that unrecognized structure is ignored rather than rejected.

## [0.2.1] - 2026-08-09

### Fixed
- Scope gate `--base` mode now detects untracked files (git diff reports tracked files only; untracked out-of-scope files could previously escape the gate in commit-range mode).
- Authorization-substitution bypass closed: every changed path must match `allowed_paths`; `authorized_protected_paths` is an additional requirement for protected paths and never substitutes for allowance. Touching a protected artifact now requires the path in both lists. An authorized-but-not-allowed protected change fails as a scope violation (exit 1).

### Added
- Two gate regression self-tests: `--base` + untracked out-of-scope file must FAIL; protected + authorized-but-not-allowed must FAIL as a scope violation. *(This entry originally miscounted the suite as "eleven cases"; the accurate count at 0.2.1 was 9 scenarios plus output assertions — corrected in 0.2.2.)*
- Self-authorization ban for mechanically governed tasks: when the gate is required, `allowed_paths` must be declared by the governing task artifact; the agent may not write, widen, or infer scope declarations (agent spec, example task file, controls doc).
- Package validator stale-claim checks: agent version must appear in the changelog; v0.2 addenda required in BRIEF and self-review; comparison framework must reference the twelve-test suite; self-authorization rule must be present.

### Changed
- Reconciled all governing artifacts and documentation to current behavior: BRIEF and self-review received dated v0.2/v0.2.1 addenda with superseded v0.1 statements historically labeled; comparison framework updated from eight to twelve tests with T9/T12 added as sharp discriminators; README test counts and self-review references corrected; ICM compatibility mapping notes the declared-surface requirement.

## [0.2.0] - 2026-08-09

### Changed
- Status model: replaced ambiguous `COMPLETE — CHECKS PARTIAL` with `IMPLEMENTATION COMPLETE — VALIDATION INCOMPLETE`; added the hard rule that no COMPLETE-prefixed status may be used while any required validation or gate is unexecuted or failing.
- Task Contract (Stage 2) is now observable: emitted in a fixed format before any code change, immutable once implementation begins, and compared against the finished work in the Completion Report (new Contract Comparison section).
- BLOCKED REPORT upgraded to a standard eight-field format; added the specialized `BLOCKED — GOVERNING CONTEXT CONFLICT` form for material artifact disagreements (S2).
- PASS != APPROVED semantics stated consistently across the agent spec, README, and compatibility documentation.
- README maturity language updated to Experimental / v0.2 with explicit non-claims (no proven reliability, production safety, guaranteed scope compliance, or security guarantees).

### Added
- Task scope declarations: `allowed_paths`, `protected_paths`, and `authorized_protected_paths` in task definitions (`examples/task-definition-example.yaml`).
- Deterministic Git diff scope gate (`tests/scope_gate.py`): compares the actual diff — added/modified/renamed/deleted/untracked — against authorized paths; distinct exit code and message for protected-artifact violations; runnable independently of any agent; never auto-fixes.
- Gate self-test (`tests/scope_gate_selftest.sh`): nine fixture cases proving PASS on compliant changes and FAIL on deliberate violations.
- Behavioral tests T9–T12: scope-boundary violation by correct code, approval-artifact refusal with mechanical verification, inseparable governing-context conflict, and incomplete-validation status discipline.
- `docs/controls.md`: instruction-level vs. mechanically enforced controls, with the explicit statement that instructions reduce but cannot guarantee.
- `docs/enforcement-roadmap.md`: v0.1 prompt-governed → v0.2 diff/scope enforcement → future permission and filesystem enforcement (documented only).

### Preserved (unchanged by design)
- Source-of-truth hierarchy, context-first workflow, strict scope boundaries, explicit non-authority, STOP conditions, evidence requirements, existing tests T1–T8, self-review, and ICM compatibility documentation.

## [0.1.0] - 2026-08-09

### Added
- Initial release of the ICM Minimal Change Engineer agent specification (`agent/icm-minimal-change-engineer.md`): governing principles, role definition and non-ownership boundaries, eight-stage operating workflow, eight STOP conditions with BLOCKED REPORT format, closed-vocabulary output contract, anti-pattern catalog, and judgment boundaries.
- Behavioral test suite of eight controlled-behavior scenarios (`tests/test-cases.md`) with expected run shapes (`tests/expected-behavior.md`).
- Plain-agent vs. ICM-agent comparison framework (`tests/comparison-framework.md`).
- Mechanical package validator (`tests/validate_package.py`).
- ICM artifacts for the package's own construction (`icm/SPEC.md`, `icm/BRIEF.md`, `icm/TASK.md`).
- Documentation: README, ICM compatibility mapping (`docs/icm-compatibility.md`), critical self-review (`docs/self-review.md`), end-to-end example (`examples/example-use.md`).
- MIT license and provenance statement.

### Known limitations
- All behavioral rules are prompt-level; none are mechanically enforced yet.
- Behavioral test results across models are not yet collected; the suite and method ship without aggregated data.
