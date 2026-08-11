# TASK — Build Plan for v0.1.0

**Artifact type:** ICM Task (executable work breakdown from SPEC.md + BRIEF.md)
**Status:** COMPLETE — validator passed 2026-08-09; negative test confirmed detection of planted defects
**Date:** 2026-08-09

| # | Task | Output | Verified by |
|---|------|--------|-------------|
| T1 | Write ICM artifacts (Spec, Brief, Task) | icm/*.md | Validator: files exist, required sections present |
| T2 | Write agent specification | agent/icm-minimal-change-engineer.md | Validator: AC1, AC2 section and vocabulary checks; manual read against SPEC §3 |
| T3 | Write behavioral test suite (8 tests) | tests/test-cases.md | Validator: 8+ tests, each with 4 required fields |
| T4 | Write expected outcomes | tests/expected-behavior.md | Manual cross-check: every test ID present |
| T5 | Write comparison framework | tests/comparison-framework.md | Manual: 8 dimensions, ordinal scale |
| T6 | Write README | README.md | Validator + manual: all 12 Part-10 questions answered; no prohibited claims |
| T7 | Write ICM compatibility doc | docs/icm-compatibility.md | Manual read against SPEC §3 |
| T8 | Write example walkthrough | examples/example-use.md | Manual: shows invoke + output contract in use |
| T9 | Write LICENSE, PROVENANCE, CHANGELOG | root files | Validator: files exist; LICENSE is MIT text |
| T10 | Write and run package validator | tests/validate_package.py | Script exit code 0 |
| T11 | Critical self-review (8 questions) | docs/self-review.md | Manual: all 8 questions answered skeptically |
| T12 | Readiness verdict | final report | Judged against SPEC §7, not assumed |

**Order:** T1 → T2 → T3/T4/T5 → T6/T7/T8 → T9 → T10 → T11 → T12.
**Rule:** No task's output feeds forward until checked against its spec row.

---

# v0.2 Hardening Tasks (2026-08-09)

| # | Task | Output | Verified by |
|---|------|--------|-------------|
| H1 | Status model replacement + COMPLETE-prefix rule | agent spec §8 | Validator: new vocabulary present, old absent |
| H2 | Observable Task Contract | agent spec Stage 2; example walkthrough | Validator: TASK CONTRACT block + field names |
| H3 | Scope declarations | agent spec §5; examples/task-definition-example.yaml | Gate consumes it in self-test |
| H4 | Deterministic scope gate | tests/scope_gate.py | Self-test case 1 (PASS) + cases 2,4,6,7 (FAIL) |
| H5 | Protected-artifact detection | tests/scope_gate.py exit 2 | Self-test cases 3,5 |
| H6 | PASS != APPROVED consistency | agent, README, icm-compatibility, controls | Validator string check |
| H7 | Standard BLOCKED REPORT + conflict form | agent spec §7; example | Validator: required field lines |
| H8 | Conflict detection behavior | agent spec §7 | T11 (behavioral) |
| H9–H12 | Tests T9–T12 | tests/test-cases.md, expected-behavior.md | Validator: >=12 tests, 4 fields each |
| H13 | Controls doc | docs/controls.md | Validator: file + both category headings |
| H14 | Enforcement roadmap | docs/enforcement-roadmap.md | Validator: three stage headings |
| H15 | Provenance check | PROVENANCE.md | Verified compliant as-is; no change needed |
| H16 | README maturity language | README.md | Validator: v0.2 + non-claim phrases absent as claims |
| H17 | Preserve v0.1 strengths | whole package | Validator: all v0.1 structural checks still pass |

**Status:** COMPLETE — validator and gate self-test passed 2026-08-09; both negative-tested.

---

# v0.2.1 Reconciliation Tasks (2026-08-09)

| # | Task | Output | Verified by |
|---|------|--------|-------------|
| R1 | --base untracked detection | tests/scope_gate.py | Self-test case 8 |
| R2 | Authorization semantics fix | tests/scope_gate.py | Self-test cases 5 (both-lists pass) and 9 (substitution fails) |
| R3 | No self-authorized scope rule | agent §5; example yaml; controls | Validator: 'self-authorize' present; gate exit 3 on missing allowed_paths |
| R4 | Reconcile SPEC/BRIEF/TASK/self-review/icm-compatibility | addenda + historical labels | Validator: addendum presence checks |
| R5 | Historical-label v0.1-as-current statements | BRIEF B3, self-review header, README counts, comparison 'eight' | Validator + grep audit |
| R6 | Validator stale-claim checks | tests/validate_package.py | Negative-tested |

**Status:** COMPLETE — full battery passed 2026-08-09.

---

# v0.2.2 Audit-Response Tasks (2026-08-09)

| # | Task | Verified by |
|---|------|-------------|
| A1 | Remove brace-artifact dir; add packaging checks | Validator packaging checks; negative-tested |
| A2 | Fix normalize (dot collapse + lstrip bug) | Scenario 11 + unit checks (12) |
| A3 | -z path extraction, both modes | Scenarios 6, 7, 10 |
| A4 | Harmonize scenario counts | Validator count-consistency check |
| A5 | Document YAML subset | Docstring + example yaml |

**Status:** COMPLETE — full battery passed 2026-08-09.

---

# v0.2.3 Fix Tasks (2026-08-09) — authorized scope: F1, F2, F3 only

| # | Fix | Verified by |
|---|-----|-------------|
| X1 | F1 exit-code contract (GateArgumentParser -> exit 3) | Scenario 13, three sub-cases |
| X2 | F2 YAML-rule comment stripping | Scenario 14 + inline unit check |
| X3 | F3 dot-directory pruning in empty-dir check | Git-clone fixture, both directions |

Out of authorized scope, intentionally not changed: F4-F12, G1*-G3.
(*G1's exit-3 coverage gap was incidentally closed by F1's regression scenario.)

**Status:** COMPLETE — full battery passed 2026-08-09.

---

# v0.2.4 Fix Tasks (2026-08-09) — authorized scope: F4, F5, F6 only

| # | Fix | Verified by |
|---|-----|-------------|
| Y1 | F4 default-mode boundary surfaced (note + agent instruction) | Scenario 16, both modes |
| Y2 | F5 ignore-rule scrutiny closes bypass | Scenario 15, control + bypass directions |
| Y3 | F6 posixpath normalization; backslash is data | Unit assertion in scenario 12 block |

Out of authorized scope, intentionally not changed: F7-F12, G2-G3.

**Status:** COMPLETE — full battery passed 2026-08-09.

---

# v0.2.5 Fix Tasks (2026-08-09) — authorized scope: F8, F9 only

| # | Fix | Verified by |
|---|-----|-------------|
| Z1 | F8 parser strictness (last-wins, key-closing, exit-3 malformations, fail-closed dangling items) | Scenario 17 + unit sweep + example-file parse check |
| Z2 | F9 whole-repo "." entry with protected interplay; strict case + hint | Scenario 18, four sub-cases |

Out of authorized scope, intentionally not changed: F7, F10-F12, G2-G3.

**Status:** COMPLETE — full battery passed 2026-08-09.

---

# v0.2.6 Tasks (2026-08-09) — authorized scope: F7, F10, F11, F12, then G1-G3 last

| # | Item | Verified by |
|---|------|-------------|
| W1 | F7 contracted stream errors (3 branches; status-rename fail-open closed) | Scenario 19 units |
| W2 | F10 single annotated dual-violation report | Live fixture check, 1 occurrence, exit 2 |
| W3 | F11 validator regex robustness | Battery + validator self-test |
| W4 | F12 syntax/import self-check | Validator self-test case 6 |
| W5 | G1 exit-3 contract fully covered | Scenarios 13, 17, 19 |
| W6 | G2 default-mode boundary live | Scenario 20 |
| W7 | G3 reproducible validator self-test in git-clone fixture | tests/validator_selftest.sh, 6 cases |

**Audit ledger status: CLOSED** — F1-F12 and G1-G3 all addressed.
**Status:** COMPLETE — full battery (validator + gate self-test + validator self-test) passed 2026-08-09.

---

# v0.2.7 Tasks (2026-08-09) — authorized scope: eliminate the drift-prone duplicated count

| # | Item | Verified by |
|---|------|-------------|
| V1 | README count claims removed; coverage described qualitatively | Validator ban check passes on real README |
| V2 | Validator inverted: contiguity + floor ratchet + reintroduction ban | Validator self-test cases 5, 7, 8 |
| V3 | Drift window cured (growth with stale README = no false fire) | Live simulation, then reverted |
| V4 | Design recorded | BRIEF B16 |

**Status:** COMPLETE — triple battery passed 2026-08-09.
