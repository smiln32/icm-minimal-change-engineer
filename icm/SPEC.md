# SPEC — ICM Minimal Change Engineer

**Artifact type:** ICM Specification (source of truth for this build)
**Status:** ACTIVE
**Owner:** Carla (human)
**Date:** 2026-08-09

## 1. What is being built

A new, original AI coding specialist named **ICM Minimal Change Engineer**, packaged as a small public MIT-licensed repository suitable for Claude Code and similar AI coding environments, and intended as the first example of an ICM-native specialist-agent standard.

ICM = **Intent and Context Management**: the practice of keeping project truth in designated artifacts, reading required context before acting, bounding work to explicit scope, protecting approved decisions, and leaving evidence.

## 2. Problem statement

AI coding assistants routinely change more than requested, refactor unrelated code, reinterpret requirements, silently expand scope, treat conversation as truth, claim success without evidence, and work around failed checks. This agent exists to actively prevent those behaviors. Its defining characteristic is **controlled precision**, not merely small diffs.

## 3. Governing principles (rank above all role behavior)

1. Project truth lives in artifacts, not model memory.
2. Required context must be read before work begins.
3. Scope is explicit; the assigned task defines the work boundary.
4. Approved decisions cannot be silently reconsidered.
5. Minimum change means minimum **justified** change, not minimum diff.
6. Validation is not approval. PASS ≠ APPROVED.
7. Failed gates cannot be bypassed.
8. Failure must be explicit; STOP is a successful outcome of the control system.
9. Work must leave evidence.
10. Human authority remains human.

## 4. Required deliverables

| ID | Deliverable | Location |
|----|-------------|----------|
| D1 | Agent specification (complete, usable agent file) | agent/icm-minimal-change-engineer.md |
| D2 | Behavioral test suite (8+ controlled-behavior tests) | tests/test-cases.md |
| D3 | Expected test outcomes | tests/expected-behavior.md |
| D4 | Plain-agent comparison framework | tests/comparison-framework.md |
| D5 | README answering all Part 10 questions | README.md |
| D6 | ICM compatibility document | docs/icm-compatibility.md |
| D7 | Repository structure with file explanations | README.md + this repo |
| D8 | MIT license + provenance note | LICENSE, PROVENANCE.md |
| D9 | Critical self-review (8 questions) | docs/self-review.md |
| D10 | Mechanical package validator | tests/validate_package.py |
| D11 | Example usage walkthrough | examples/example-use.md |
| D12 | Changelog | CHANGELOG.md |

## 5. Acceptance criteria

- AC1: Agent file contains role definition, "What This Agent Does NOT Own," the 8-stage workflow, STOP conditions, output contract with the exact four-status vocabulary, and anti-patterns.
- AC2 (superseded by AC9 in the v0.2 addendum): the original v0.1 four-status vocabulary, including the retired partial-completion status. No APPROVED/CERTIFIED/PRODUCTION APPROVED/HUMAN APPROVAL COMPLETE as agent-issued states — this half of AC2 remains in force.
- AC3: Eight or more behavioral tests, each with scenario, expected behavior, prohibited behavior, and PASS criteria. No manufactured failure counts or arbitrary numeric quality scores.
- AC4: README answers all twelve Part 10 questions without overselling ("production-grade," hallucination-elimination claims prohibited).
- AC5: All prose is newly written; no distinctive text, examples, or structure copied from another agent repository.
- AC6: No theatrical persona language ("world-class," "decades of experience," etc.).
- AC7: Package validator runs and passes against the assembled repository.
- AC8: Deliverable returned in the 13-part brief's FINAL DELIVERABLE order, ending with a readiness verdict that is judged, not assumed.

## 6. Out of scope for v0.1.0

- Runtime enforcement hooks (file-system sandboxes, permission schemas) — documented as future work only.
- Multi-agent orchestration.
- Any non-MIT licensing analysis.

## 7. Definition of done

All deliverables D1–D12 exist, validator passes, self-review completed honestly, verdict issued with justification.

---

# v0.2 Addendum — Hardening (2026-08-09)

Governed by the v0.2 hardening task (17 items). Scope: those items only; no redesign. Acceptance criteria added:

- AC9: Status vocabulary is exactly COMPLETE — CHECKS PASS / IMPLEMENTATION COMPLETE — VALIDATION INCOMPLETE / BLOCKED / FAILED CHECK, with the COMPLETE prefix barred while any required validation is incomplete.
- AC10: Task Contract emitted visibly before implementation, in the fixed nine-field format, compared in the completion report.
- AC11: Tasks can declare allowed_paths / protected_paths / authorized_protected_paths.
- AC12: Deterministic Git diff scope gate exists, uses real diff output, treats add/modify/rename/delete/untracked as changes, returns machine-readable exit codes, reports protected-artifact violations distinctly, never auto-fixes, and runs independently of the agent.
- AC13: Gate proven by self-test to pass compliant fixtures and fail deliberate violations.
- AC14: Standard eight-field BLOCKED REPORT plus BLOCKED — GOVERNING CONTEXT CONFLICT form.
- AC15: Tests T9–T12 cover scope violation by correct code, approval-artifact refusal, context conflict, and incomplete validation.
- AC16: docs/controls.md separates instruction-level from mechanical controls; docs/enforcement-roadmap.md stages v0.1 → v0.2 → future.
- AC17: v0.1 strengths preserved; package validator updated and passing.

## v0.2.1 note (2026-08-09)

- AC18: In `--base` mode the gate detects untracked files as changes.
- AC19: `allowed_paths` is necessary for every changed path; `authorized_protected_paths` is additional for protected paths and never substitutes for allowance (both lists required to touch a protected artifact).
- AC20: When the gate is required, `allowed_paths` must be declared by the governing task artifact; the agent may not self-authorize mechanically enforced scope.
- AC21: All governing artifacts and documentation reconciled to v0.2 behavior; superseded v0.1 statements historically labeled, per BRIEF B14.

## v0.2.2 note (2026-08-09)

External audit response (five items): AC25 packaging contains no unexpected or empty entries, validator-enforced; AC26 path normalization collapses dot components, preserves parent escapes, and never character-strips prefixes; AC27 git paths read NUL-terminated with rename layouts handled per mode; AC28 self-test scenario count consistent across documents, validator-enforced; AC29 supported YAML subset documented at both consumption points.
