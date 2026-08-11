# Enforcement Roadmap

The project's hardening direction: move controls from *asked of the model* to *imposed by machinery*. Each stage below lists what is enforced and by what means. Future controls are documented here deliberately and are **not implemented** in v0.2.

## v0.1 — Prompt governed

Everything behavioral was instruction-level: scope limits, context-first ordering, decision protection, PASS/APPROVED separation, STOP conditions, evidence requirements. The only deterministic machinery was `tests/validate_package.py`, which validates the package's structure — not agent behavior.

## v0.2 — Diff and scope enforcement (current)

- **Deterministic Git diff scope gate** (`tests/scope_gate.py`): actual-diff comparison against declared `allowed_paths`; added/modified/renamed/deleted/untracked all count; machine-readable exit codes; PASS/FAIL output; no auto-fix or auto-revert.
- **Protected-artifact detection**: distinct failure class (exit 2) for changes under `protected_paths` without explicit `authorized_protected_paths` entry.
- **Gate self-test** (`tests/scope_gate_selftest.sh`): proves the gate passes compliant fixtures and fails deliberate violations, so the enforcement itself is verified.
- **Observable Task Contract**: interpretation moved from internal to emitted — reviewable after the fact, though its pre-implementation timing still depends on model compliance.
- **Unambiguous status model**: `IMPLEMENTATION COMPLETE — VALIDATION INCOMPLETE` replaces the misreadable partial-completion status; the COMPLETE prefix is structurally reserved for fully validated work.

## Future — Permission and filesystem enforcement (documented only)

Candidate controls, in rough order of value:

1. **Read-only governing files** — CONTEXT.md, specs, and decision records mounted or permissioned read-only for agent tooling, converting "do not edit" into "cannot edit."
2. **Write restrictions on approval directories** — `approvals/` writable only by human-held credentials, making approval impersonation impossible rather than prohibited.
3. **Schema validation for task definitions** — task YAML checked against a schema before work starts (required fields, path syntax, non-empty change surface), so malformed tasks fail fast instead of inviting interpretation.
4. **Automated gate execution** — the scope gate and required checks run by a harness on every handoff, not at the agent's initiative.
5. **Captured command output** — validation commands executed by the harness with recorded exit codes and output, so reported results cannot be invented.
6. **Signed or externally created approval artifacts** — approvals carrying a signature or origin the agent's environment cannot produce.
7. **Role-specific filesystem/tool permissions** — the minimal-change role granted only the write and execute permissions its jurisdiction requires; other ICM specialist roles receive different grants.

None of these are claimed as designed or scheduled; they are the documented direction, kept visible so v0.2's limits are never mistaken for the finished state.
