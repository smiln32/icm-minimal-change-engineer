# Controls — Instruction-Level vs. Mechanically Enforced

Every rule in this package belongs to one of two categories, and the difference matters: **instruction-level controls can reduce undesirable behavior but cannot guarantee enforcement.** A model can fail to follow an instruction; a script cannot be persuaded. This document states which category each control lives in as of v0.2, so nobody mistakes a request for a guarantee.

## Instruction-level controls

Rules the agent is *told* to follow. They shape behavior through the agent specification and depend entirely on model compliance:

- Remain within task scope; make only the minimum justified change.
- Read governing context before implementation begins.
- Emit the Task Contract before any code change, and never silently rewrite it.
- Do not reinterpret or override approved decisions; a better idea is not permission.
- Surface uncertainty; stop instead of guessing when correctness is materially affected.
- PASS != APPROVED: never create, modify, or impersonate approval; never convert PASS into APPROVED.
- Report actual check results without optimism; produce a Completion or BLOCKED report every time.
- Reject the anti-patterns (drive-by refactors, validation laundering, silent scope growth, and the rest) even when the user requests them.

**Honest status:** these hold only as well as the model holds them. Long sessions, ambiguous tasks, and user pressure all degrade compliance. Behavioral tests T1–T12 exist to measure how well they hold in practice.

## Mechanically enforced controls

Rules verified or imposed by deterministic machinery that does not consult the model:

- **Git diff scope gate** (`tests/scope_gate.py`): compares the *actual* Git diff — added, modified, renamed, deleted, and untracked files — against the task's declared `allowed_paths`. Machine-readable exit codes; does not rely on the model describing what it changed. If the diff touches any `.gitignore`, ignored-untracked files join the scope check, closing the hide-by-ignore-rule bypass. Default mode audits uncommitted work only and says so in its PASS output — committed work requires `--base`. Paths are forward-slash on all platforms; backslash is filename data. (v0.2, hardened v0.2.1–v0.2.4, shipped and self-tested.)
- **Protected-path detection** (same gate, distinct failure class and exit code): every changed path must match `allowed_paths` first; a change under `protected_paths` must additionally be in `authorized_protected_paths`, and neither list substitutes for the other. (v0.2, semantics hardened v0.2.1, shipped and self-tested.)
- **Task-file integrity** (same gate, exit 4): the declarations are the authorization for the entire audit, so the gate checks whether the task file itself is part of the diff before evaluating anything else. A task file inside the repository that was modified, committed, or newly created during the audited work causes the gate to refuse to certify — it reports the tampering and withholds a scope verdict rather than auditing against declarations the audited work may have written. Until this shipped, "the agent may not self-authorize its own change surface" was listed here as mechanical while only its weaker half (refusing to run with no `allowed_paths` at all) actually was: an agent that widened its own in-repo task file to `allowed_paths: [.]` received a PASS. The optional PreToolUse hook blocks the edit up front; the gate catches it after the fact. (F13, shipped and self-tested, negative-tested by mutation.)
- **Deterministic package validation** (`tests/validate_package.py`): structural checks on the package itself — required files, sections, status vocabulary, prohibited language. (v0.1, extended in v0.2.)
- **Filesystem permissions** on governing/approval directories: makes tampering impossible rather than forbidden. (Future — documented in `docs/enforcement-roadmap.md`, not yet implemented.)
- **Approval-file write restrictions** (credentials the agent's tooling does not hold): same principle applied to approval artifacts. (Future.)

## What the mechanical controls still cannot see

The gate reasons about a Git diff, so anything that changes state without appearing in one is outside its reach. These are documented boundaries, not defects, and none of them is closed by the checks above:

- **Content within an authorized file.** The gate checks *which* paths changed, never *what* changed inside them. An unrequested refactor confined to a file listed in `allowed_paths` passes cleanly. Minimum-surface discipline inside an allowed file remains entirely instruction-level, and it is the single largest gap between "verified in scope" and "only made the requested change."
- **Writes through a symlink to a target outside the repository.** A symlink inside an allowed directory can redirect a write to a file the repository does not track; git records no change and the gate reports PASS. A symlink pointing at an in-repo file *is* caught, because git sees the real target modified.
- **A task file the agent committed, in default mode.** The integrity check inherits the default-mode audit boundary: work already committed is invisible without `--base`. A session that commits its widened task file evades the check in default mode — which is the mode the Stop hook uses — though the PASS still carries its uncommitted-work-only note. `--base` catches it, and the PreToolUse hook prevents the edit from happening at all.
- **Ignore rules outside the tree** (`.git/info/exclude`, `core.excludesFile`) and **task files stored outside the repository**, whose integrity is not diff-verifiable; a PASS says so explicitly rather than implying the check ran.

## How the categories interact

The gate does not make the instructions unnecessary; it makes one class of instruction *checkable*. "Stay in scope" is instruction-level while the agent works, and mechanically verified at Stage 7 when the gate runs. The roadmap (`docs/enforcement-roadmap.md`) tracks the deliberate migration of controls from the first category to the second — the direction this project treats as the definition of hardening.
