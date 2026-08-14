# HANDOFF — ICM Minimal Change Engineer

**Final version:** 0.2.7 · **Date:** 2026-08-09 · **License:** MIT · **Status:** experimental, ready to publish for community testing
**Deliverable:** `icm-minimal-change-engineer-v0.2.7.zip` (30 files)
*(historical — superseded by the 2026-08-14 addendum: current version is 0.3.0, and the package now ships from this git repository rather than a zip.)*

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

All three of §8's next milestones are done: (1) T1–T12 run against a live model, results in `tests/behavioral-run-results.md` (11/12 conclusive and compliant; T8's fixture is a documented inconclusive, not a pass); (2) and (3) implemented together as optional, off-by-default Claude Code hooks under `hooks/`, documented in `docs/enforcement-roadmap.md`'s new v0.3 section. This note is additive per the project's own addendum-over-rewrite rule (B14) — §8's original text above is left as written.

## Addendum — 2026-08-12

**Verification is a four-command battery now, not three.** §2's list predates `hooks/`. Run all four from the repo root; each must end PASS:

```bash
python3 tests/validate_package.py
bash tests/scope_gate_selftest.sh
bash tests/validator_selftest.sh
bash tests/hooks_selftest.sh          # added this session
```

**On Windows, export `PYTHONUTF8=1` first.** Without it, Python's `cp1252` console encoding fails `tests/validator_selftest.sh` on encoding alone — a false failure that says nothing about the validator. With it set, three of the four pass outright; the fourth reports one failing case, `scope_gate_selftest.sh` scenario 10, which needs a filename containing `"` that NTFS cannot create at any encoding. Both are environment limits, documented in the README's testing section, not defects.

**What changed this session.** `tests/hooks_selftest.sh` closes the gap the v0.3 section flagged when the hooks shipped: they were the only shipped code verified once by hand and thereafter trusted, which is the posture the hooks exist to replace. It drives each hook with real JSON payloads on stdin and asserts the decision contract actually emitted. The cases worth knowing about, because they are the ones that rot without anyone noticing:

- **"Allow" is empty stdout, not exit 0.** Both hooks exit 0 on every path, so a hook that failed open and a hook that never ran are indistinguishable to anything checking status. Several cases assert the absence of output specifically.
- **Fail-open branches must announce themselves.** Unparseable stdin and a missing `protected-paths.txt` both allow the call — correctly — but must say so on stderr. A mechanical control degrading to "not enforced" has to be visible.
- **Absolute `file_path` values**, the form Claude Code actually sends, relativized against `CLAUDE_PROJECT_DIR` before matching.
- **The gate's report reaches the model verbatim on PASS**, including the uncommitted-work-only note. Summarizing that to a bare "PASS" is the specific regression guarded against, and it is caught.
- **The Stop hook's block ladder** escalates to a human after `MAX_BLOCKS` rather than trapping the session, resets on PASS, and keeps counters per-session.

Negative-tested by mutation rather than trusted: disabling the deny branch fails 7 assertions, summarizing the gate's PASS fails 3.

`validate_package.py` also gained `hooks/` in `REQUIRED_FILES` — it had never required the hook files to exist at all, so a release could have shipped without them and still validated.

**Next, in recommended order:**

1. **Roadmap item 3, task-schema validation.** The most tractable of the remaining documented-only items: task YAML checked against a schema before work starts, so malformed tasks fail fast instead of inviting interpretation.
2. **The Stop hook's `--base` gap.** `docs/enforcement-roadmap.md` calls this out as a real gap deserving its own proposal, not a silent fold-in: sessions that commit mid-task are audited by a hook that only sees uncommitted work.
3. **A live end-to-end fire test.** The pipe-tests and the new suite both exercise the hooks directly; neither proves Claude Code actually invokes them. The one attempt on record did not observe the PreToolUse hook firing, attributed to the settings watcher rather than to logic. This repo now has a `.claude/` directory, so the conditions to retry it exist.
4. **Roadmap item 2, approval-directory write restrictions.**
5. **Open the "Call for A/B results" issue** (§7 item 5). The package's central claims are testable and community data is still the missing piece.

**Also this session, outside the package's own scope:** `.claude/CLAUDE.md` now carries this project's coding-agent rules. Its inherited "push after every commit" rule was replaced with a never-push rule — pushing is the maintainer's decision alone.

---
*Handoff addendum prepared 2026-08-12. Four-command battery run immediately before commit; results as described above.*

## Addendum — 2026-08-14

**Release-readiness review of the enforcement machinery, and one real defect found (F13).** The four-command battery passed on the shipped tree before any change, so the review went after the machinery adversarially instead: build a fixture repo, play the attacker, and see what a non-compliant agent could actually get past the gate.

**What was found.** The gate audited the real diff but trusted the declarations it was handed. With task files inside the repository — the arrangement the package's own example encourages — those declarations are agent-writable. A session could rewrite its own task file to `allowed_paths: [.]`, add an unrequested module, tamper with an approved decision record, and collect a clean PASS. It passed in default mode, in `--base` mode, and through the Stop hook, which reported that PASS to the model as automated verification. The README's central claim — "it does not trust the model's description of what it changed" — was defeated by editing the description. The existing self-test could not have caught it: its fixture deliberately keeps task files *outside* the repo to avoid diff noise, which made the scenario structurally unobservable.

**What changed.** The gate checks the task file's integrity before evaluating scope and returns a new exit 4 — naming the file and withholding a scope verdict rather than reporting one computed from untrusted declarations. The Stop hook passes `ICM_TASK_FILE` as a path, not just parsed contents. `hooks/protected-paths.txt` gains `tasks/`. Coverage: gate scenario 21, hooks case 20, mutation-tested four ways. Design record: BRIEF B17. Full detail in the CHANGELOG's Unreleased section.

**Two accuracy corrections, worth more than the code fix in some ways.** `docs/controls.md` had listed self-authorization prevention under *mechanically enforced* when only its weaker half was. And nothing anywhere said plainly that the gate checks *which paths* changed, never *what changed inside them* — so an unrequested refactor confined to an already-allowed file passes cleanly. That is the largest remaining gap between "gate PASS" and "only the requested change was made," and `docs/controls.md` now has a section listing it alongside the symlink and committed-task-file boundaries.

**Release decisions left to the maintainer:**

1. ~~**Version number.**~~ Resolved: cut as **0.3.0** on 2026-08-14. A minor bump rather than a patch because the new gate exit code (4) is a contract change for anything keying on exit status, and because the release carries the optional hooks and the A/B evidence as well as the F13 fix. Agent file and README version strings updated to match.
2. **The LICENSE copyright line** (§7 item 2) is still unconfirmed.
3. **The "Call for A/B results" issue** (§7 item 5) is still unopened.

**Next, in recommended order** — unchanged from the 2026-08-12 list except that the task-schema item now has a second reason to exist:

1. **Roadmap item 3, task-schema validation.** Beyond fail-fast on malformed tasks, a schema is where a "task files must be committed and protected" convention could be checked rather than documented.
2. **The Stop hook's `--base` gap.** Now load-bearing for F13 too: default mode is blind to a task file the agent committed, so the pre-hoc PreToolUse block is currently the stronger of the two protections.
3. **A live end-to-end fire test** of the hooks under Claude Code.
4. **Roadmap item 2, approval-directory write restrictions.**

---
*Handoff addendum prepared 2026-08-14. Four-command battery run immediately before commit; all four PASS.*
