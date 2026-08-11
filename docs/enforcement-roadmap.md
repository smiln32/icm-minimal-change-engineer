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

1. **Read-only governing files** — CONTEXT.md, specs, and decision records mounted or permissioned read-only for agent tooling, converting "do not edit" into "cannot edit." **Implemented for Claude Code, optional — see v0.3 below.**
2. **Write restrictions on approval directories** — `approvals/` writable only by human-held credentials, making approval impersonation impossible rather than prohibited.
3. **Schema validation for task definitions** — task YAML checked against a schema before work starts (required fields, path syntax, non-empty change surface), so malformed tasks fail fast instead of inviting interpretation.
4. **Automated gate execution** — the scope gate and required checks run by a harness on every handoff, not at the agent's initiative. **Implemented for Claude Code, optional — see v0.3 below.**
5. **Captured command output** — validation commands executed by the harness with recorded exit codes and output, so reported results cannot be invented.
6. **Signed or externally created approval artifacts** — approvals carrying a signature or origin the agent's environment cannot produce.
7. **Role-specific filesystem/tool permissions** — the minimal-change role granted only the write and execute permissions its jurisdiction requires; other ICM specialist roles receive different grants.

Items 2, 3, 5, 6, 7 remain documented only — not claimed as designed or scheduled, kept visible so v0.2's limits are never mistaken for the finished state.

## v0.3 — Claude Code hook enforcement (current, optional)

Roadmap items 1 and 4, implemented as opt-in Claude Code hooks rather than agent-spec instructions — machinery the model cannot see or influence, per this project's stated direction of moving controls from *asked* to *imposed*. Ships under `hooks/`; nothing here is active until a project wires the hooks into `.claude/settings.json` (see `hooks/settings.snippet.json` and the README).

- **`hooks/protect_governing_files.py`** (`PreToolUse`, matcher `Write|Edit|NotebookEdit`) — denies any edit whose target path matches an entry in `hooks/protected-paths.txt` (defaults: `CONTEXT.md`, `decisions/`, `governance/`, `specs/`), using `tests/scope_gate.py`'s own `covered_by()` for matching so there is one matching implementation, not two that could drift apart. This list is independent of any task's `protected_paths`/`authorized_protected_paths` — it is a standing, task-independent block, not a per-task audit. There is no in-session override; a human edits the config file or the request is refused.
- **`hooks/run_scope_gate_on_stop.py`** (`Stop`) — re-runs `scope_gate.py` against the task named by the `ICM_TASK_FILE` environment variable (unset = silent no-op; this hook only activates when a session explicitly opts in) and blocks the Stop event with the gate's own FAIL report on violation, so a scope violation cannot leave the session unreported. Blocking stops after 3 consecutive failures for the same session — past that point the true fix is a human decision, not another automatic retry, and continuing to block would just trap the session. Runs in the gate's default mode (blind to committed work, exactly like every other invocation of the gate) and always passes the gate's report through verbatim — including its audit-boundary note on PASS — rather than summarizing it into a bare "PASS", which would silently hide that same caveat. It does not yet expose a `--base` equivalent for sessions that commit mid-task; that would be a real gap worth raising as its own proposal, not something to fold into this hook silently.

**Known limits, stated plainly:** both hooks are Claude-Code-specific (the "other environments" install path in the README has no equivalent yet). The Stop hook's `ICM_TASK_FILE` convention is a single global pointer per session — it does not support multiple concurrently-tracked tasks, and has no way to audit committed work (see above). Neither hook has its own automated test suite yet (unlike `scope_gate_selftest.sh`); they were verified via the hook-input pipe-test method (real stdin payloads piped directly into each script) during development. A live end-to-end fire test (wiring the PreToolUse hook into `.claude/settings.local.json` and triggering a real Write) was also attempted once and did not observe the hook firing — the settings watcher only picks up hook config from directories that already had a settings file when the session started, so a config file created mid-session needs a `/hooks` reload or restart, which the pipe-tests already prove is not a logic defect. Both are optional and off by default — adopting them is a per-project choice, made by editing `.claude/settings.json`, not something this package does for you.
