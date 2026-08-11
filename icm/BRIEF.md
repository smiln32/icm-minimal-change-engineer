# BRIEF — Design Decisions for v0.1.0

**Artifact type:** ICM Brief (approved design decisions derived from SPEC.md)
**Status:** ACTIVE
**Date:** 2026-08-09

## Decision log

**B1 — Agent file format.** The agent file uses YAML frontmatter (`name`, `description`) followed by the full operational specification, making it drop-in compatible with Claude Code custom agents (`.claude/agents/`) while remaining a readable standalone document for other environments.

**B2 — Repository structure.** Extend the proposed structure with three additions, each with a stated reason:
- `icm/` — the Spec/Brief/Task artifacts for the package itself. An ICM-native standard should demonstrate ICM on its own construction.
- `tests/validate_package.py` — a mechanical validator. Behavioral tests require a human or model runner; the validator gives one check that runs deterministically, and models the eventual shift from trusted-prompt rules to enforced rules.
- `PROVENANCE.md` at root plus `docs/self-review.md` — provenance and self-critique are release artifacts, not buried notes.

**B3 — Authority model.** The agent's authority is defined positively (what it may do) and negatively (what it may never do), with the negative list controlling in any conflict. Status vocabulary is closed: originally the four statuses in SPEC AC2 *(historical — AC2 superseded by AC9; the current closed vocabulary is defined in the v0.2 addendum below)*.

**B4 — Artifact discovery order.** The agent looks for governing context in this order: explicit task-provided artifacts → CONTEXT.md → decision records → PRD/spec files → configuration/governance files. Missing required context is a STOP, not a guess.

**B5 — Tone.** Operational language throughout. Imperatives, tables, and checklists. No persona traits, no experience claims, no motivational framing.

**B6 — Test design.** Each behavioral test targets one failure mode from the problem statement. PASS criteria are observable behaviors (stopped, reported, asked, refrained), never subjective quality scores.

**B7 — Comparison framework.** Eight dimensions matching the brief, scored on a three-level ordinal scale (Compliant / Partial / Violated) per dimension per run — ordinal levels are observable; numeric scores would be manufactured precision.

**B8 — Versioning.** v0.1.0, semantic versioning, CHANGELOG in Keep-a-Changelog style.

**B9 — Honest limitations.** README and self-review state plainly that prompt-level rules are not mechanically enforced and can fail; the package claims to *reduce*, not eliminate, scope drift.

---

# v0.2 / v0.2.1 Addendum — Hardening Decisions (2026-08-09)

**B10 — Gate placement.** The deterministic scope gate lives in `tests/` alongside the package validator rather than a new top-level directory: minimal structural change, and both are deterministic checking machinery.

**B11 — Dependency-free gate.** The gate parses its task-YAML subset with a built-in mini-parser instead of requiring PyYAML, so it runs anywhere Python runs.

**B12 — Authorization semantics (corrected v0.2.1).** `allowed_paths` is necessary for every change; `authorized_protected_paths` is an additional requirement for protected paths and never substitutes for allowance. Touching a protected artifact requires the path in both lists. An authorized-but-not-allowed protected change fails as a scope violation (exit 1), because the authorization rule is satisfied and the scope rule is not.

**B13 — No self-authorized mechanical scope.** When the gate is required, `allowed_paths` must come from the governing task artifact; the agent never writes, widens, or infers the declarations. The gate enforces this half mechanically by refusing to run (exit 3) without declared `allowed_paths`.

**B14 — Addendum-over-rewrite.** Versioned governing artifacts (SPEC, BRIEF, TASK, self-review) are reconciled by dated addenda plus historical labels on superseded statements, never by silently rewriting the original record.

**B15 — v0.2.1 --base completeness.** In `--base` mode the gate unions `git diff` output with untracked files (`git ls-files --others --exclude-standard`), since git diff reports tracked files only and an untracked file must not escape the gate.

**B16 — Single source of truth for derived facts (v0.2.7).** A fact stored twice drifts; the scenario count drifted three times before this rule. Living documents (README) may not carry numeric copies of facts owned elsewhere; they describe and point to the source. The validator's role inverts accordingly: it checks the source's own integrity (contiguous 1..N numbering, a one-way floor ratchet that fires on deletion and never on growth) and bans reintroduction of the copied number. Design constraint honored: no check may fire predictably on the author's known-intermediate state, because routine failures train alarm fatigue — the same operator-trust concern that motivated the F1 exit-code fix.
