# HANDOFF — ICM Minimal Change Engineer

**Final version:** 0.2.7 · **Date:** 2026-08-09 · **License:** MIT · **Status:** experimental, ready to publish for community testing
**Deliverable:** `icm-minimal-change-engineer-v0.2.7.zip` (30 files)

---

## 1. What this is

An original, ICM-native AI coding specialist: an agent specification whose defining behavior is controlled precision — smallest justified change, artifacts over conversation, protected decisions, PASS never equals APPROVED, visible STOP at real boundaries — plus deterministic enforcement machinery (a Git diff scope gate), a behavioral test suite, and self-testing validation. It is intended as the first example of an ICM specialist-agent standard, and the package demonstrates ICM on its own construction (`icm/SPEC.md`, `BRIEF.md`, `TASK.md`).

## 2. Current state

Everything is closed. The external audit (Grok) and the internal self-audit produced findings F1–F12 and coverage gaps G1–G3; all are fixed or, where a boundary cannot be mechanized (F4), surfaced explicitly and tested live. No known open defects remain from either audit — which is a statement about the audits, not a claim that no defects exist.

**Verification (run all three from the repo root; each must end PASS):**

```bash
python3 tests/validate_package.py        # structural + self-consistency checks
bash tests/scope_gate_selftest.sh        # 20 gate scenarios + output assertions
bash tests/validator_selftest.sh         # 8 validator cases in a git-clone fixture
```

All three pass on the shipped tree.

## 3. Repository map

```
agent/icm-minimal-change-engineer.md   the product — drop into .claude/agents/
icm/                                   SPEC / BRIEF / TASK for this package's own build
tests/test-cases.md                    12 behavioral tests (T1–T12, human/model-run)
tests/expected-behavior.md             compliant run shapes per test
tests/comparison-framework.md          plain-agent vs ICM-agent A/B method
tests/scope_gate.py                    deterministic Git diff scope + protected-path gate
tests/scope_gate_selftest.sh           the gate's scenario inventory (source of truth)
tests/validate_package.py              package validator
tests/validator_selftest.sh            the validator's own negative test
examples/example-use.md                end-to-end walkthrough
examples/task-definition-example.yaml  task file with scope declarations
docs/controls.md                       instruction-level vs mechanical controls
docs/enforcement-roadmap.md            v0.1 → v0.2 → future enforcement stages
docs/icm-compatibility.md              principle-to-mechanism mapping
docs/self-review.md                    v0.1 review (historical) + reconciliation addendum
README / LICENSE / CHANGELOG / PROVENANCE
```

## 4. Version history, one line each

| Version | What happened |
|---------|---------------|
| 0.1.0 | Full package built via ICM method: agent spec, 8 tests, docs, validator |
| 0.2.0 | 17-item hardening: unambiguous statuses, observable Task Contract, scope declarations, deterministic gate, T9–T12, controls + roadmap docs |
| 0.2.1 | Gate bugs fixed (`--base` untracked detection; authorization-substitution bypass); self-authorization ban; all governing artifacts reconciled |
| 0.2.2 | Grok audit response: packaging artifact removed, normalize `.`/`..` + lstrip bug, `-z` git parsing, count harmonization, YAML subset documented |
| 0.2.3 | F1 exit-code collision, F2 `#`-in-path truncation, F3 validator `.git` regression |
| 0.2.4 | F4 default-mode boundary surfaced, F5 `.gitignore` bypass closed, F6 backslash corruption |
| 0.2.5 | F8 parser strictness (fail-closed), F9 whole-repo `.` entry + case-hint diagnostics |
| 0.2.6 | F7 stream-error contract, F10–F12 polish; G1–G3 coverage closed; validator self-test added |
| 0.2.7 | Duplicated scenario-count fact eliminated; validator inverted to source-integrity + reintroduction ban; drift window cured |

Full detail: `CHANGELOG.md`. Design decisions: `icm/BRIEF.md` (B1–B16).

## 5. Design rules that bind future changes

These are recorded in `icm/BRIEF.md` and enforced by the validator where possible:

1. **Both-lists rule:** touching a protected path requires it in `allowed_paths` AND `authorized_protected_paths`; neither substitutes for the other (B12).
2. **No self-authorized scope:** when the gate is required, `allowed_paths` comes from the governing task artifact; the agent never writes or widens declarations (B13).
3. **Addendum over rewrite:** versioned governing artifacts are reconciled by dated addenda with historical labels, never silent rewrites (B14).
4. **Fail closed:** ambiguity in scope-security parsing errors out rather than guessing (F8 pattern).
5. **Single source of truth:** living documents never carry numeric copies of facts owned elsewhere; the validator bans reintroduction. No check may fire predictably on known-intermediate authorial state (B16).

## 6. Honest limitations — publish these, do not soften them

- **Instruction-level controls are model-dependent.** Context-first ordering, honest reporting, decision protection: the gate cannot see these. `docs/controls.md` states exactly which rules are mechanical and which are trust.
- **Behavioral tests T1–T12 ship without aggregated results.** The suite and A/B method exist; community runs do not yet.
- **Gate residuals, documented:** `.git/info/exclude` and `core.excludesFile` are outside the diffable tree; a whitespace-preceded `#` comments even inside quoted YAML items; matching is deliberately case-sensitive (with hints); default mode audits uncommitted work only and says so.
- **Roadmap items are documented, not built:** read-only governing files, approval-directory write restrictions, task-schema validation, harness-captured check output, signed approvals.

## 7. Publishing checklist

1. Unzip, `git init`, initial commit, push to a new public GitHub repo.
2. Confirm the LICENSE copyright line — currently "Copyright (c) 2026 Carla (smiln32)"; change before pushing if you want different attribution.
3. Run the three verification commands post-clone (they are designed to pass in a real clone — that exact environment is tested).
4. Suggested repo description: "An ICM-native AI coding specialist that makes the smallest safe change — and refuses, visibly, to do anything else. Agent spec + deterministic scope gate + behavioral test suite."
5. Optional first issue to open yourself: "Call for A/B results" pointing at `tests/comparison-framework.md` — the package's central claims are testable and community data is the missing piece.

## 8. Picking this back up later

The chat environment's file system resets between sessions: to continue work, upload the v0.2.7 zip and say what's needed. For orientation in a fresh session, `icm/TASK.md` is the complete build log, the CHANGELOG is the behavior log, and `docs/self-review.md` holds the candid assessment. The next meaningful milestones, in recommended order: (1) run T1–T12 against a live model and record results, (2) roadmap item 1 (read-only governing files), (3) roadmap item 4 (harness-run gates) — each moves another control from trust to machinery, which is the project's stated direction.

---
*Handoff prepared 2026-08-09. Package verified by triple battery immediately before packaging.*

## Addendum — 2026-08-11

**Verification is now a four-command battery, not three.** §2's list predates `hooks/`; add `bash tests/hooks_selftest.sh`, which covers both hooks. On Windows, export `PYTHONUTF8=1` first (see the README's testing section) — without it Python's `cp1252` console encoding fails `tests/validator_selftest.sh` on encoding alone, and one scope-gate scenario needs a filename containing `"`, which NTFS cannot create at all. Both are environment limits, not defects.

All three of §8's next milestones are done: (1) T1–T12 run against a live model, results in `tests/behavioral-run-results.md` (11/12 conclusive and compliant; T8's fixture is a documented inconclusive, not a pass); (2) and (3) implemented together as optional, off-by-default Claude Code hooks under `hooks/`, documented in `docs/enforcement-roadmap.md`'s new v0.3 section. This note is additive per the project's own addendum-over-rewrite rule (B14) — §8's original text above is left as written.
