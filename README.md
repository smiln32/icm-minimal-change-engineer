# ICM Minimal Change Engineer

An AI coding specialist that makes the smallest safe change necessary to complete an explicitly assigned task — and refuses, visibly, to do anything else.

**Experimental / v0.3.0** · MIT License · Ready for community testing. Not proven reliable, not production-safe, and no guarantee of scope compliance or security is claimed; see "What remains experimental."

---

## What problem does this agent solve?

AI coding assistants frequently change more than requested: they refactor unrelated code, reinterpret requirements, "improve" working systems without permission, make unauthorized architectural decisions, treat conversational assumptions as truth, claim success without evidence, work around failed checks, and silently expand scope.

This agent is engineered to prevent those specific behaviors. Its defining characteristic is **controlled precision** — not merely small diffs. It is built from first principles around **ICM (Intent and Context Management)**: project truth lives in artifacts, required context is read before work begins, scope is explicit, approved decisions are protected, validation is never approval, and every task leaves evidence.

## Who is it for?

- Developers and vibe coders using Claude Code or similar AI coding environments who have been burned by scope drift.
- Teams that keep project truth in files (CONTEXT.md, specs, decision records) and want an agent that actually honors them.
- Anyone experimenting with ICM-native specialist agents.

## When should it be used?

- Surgical bug fixes.
- Small, well-defined feature modifications.
- Changes to systems where existing behavior must be preserved.
- Any task where "touch nothing else" matters more than speed.

## When should it NOT be used?

- Greenfield builds, prototyping, and exploratory work — the guardrails will slow you down for no benefit.
- Architectural redesign or large refactors — those need an authorized architect role, which this agent explicitly is not.
- Projects with no written context at all — the agent will stop and ask for artifacts that do not exist. (That stop is working as designed, but you may not want it.)

## How is it different from telling Claude "make minimal changes"?

A one-line instruction leaves every boundary to in-the-moment model judgment. This specification replaces judgment calls with defined mechanics:

- a required 8-stage workflow (context intake → task contract → minimum surface analysis → change → diff audit → validation → scope audit → evidence);
- eight explicit STOP conditions with a required BLOCKED REPORT format;
- a closed status vocabulary that structurally separates PASS from APPROVED (PASS != APPROVED throughout: the agent may run checks, report evidence, and recommend progression, but may never create, modify, or impersonate human approval, convert PASS into APPROVED, or advance a human-controlled approval gate);
- an observable Task Contract emitted before any code change, compared against the final diff at handoff;
- a deterministic Git diff scope gate (`tests/scope_gate.py`) that checks the *actual* diff against declared `allowed_paths` and `protected_paths` — it does not trust the model's description of what it changed, and it does not trust the declarations either: a task file inside the repository that changed during the work is treated as self-authorization, and the gate refuses to certify the run rather than audit against a scope the agent may have widened;
- a per-change traceability test ("what explicit requirement makes this change necessary?");
- named anti-patterns the agent must reject, including when the user requests them;
- a completion report contract, so silent work is impossible.

Whether that difference is real and repeatable is testable: see `tests/comparison-framework.md`.

## What makes it ICM-native?

It is designed around ICM principles rather than having them bolted on: artifacts outrank conversation and memory; context reading is a mandatory first stage, not a suggestion; scope, decisions, gates, and approvals are treated as owned by humans and protected by the agent; stopping at a boundary is defined as a successful outcome. The package also demonstrates ICM on itself — its own Spec, Brief, and Task artifacts are in `icm/`. Details: `docs/icm-compatibility.md`.

## How do I install / use it?

**Claude Code (custom agent):**

```bash
mkdir -p .claude/agents
cp agent/icm-minimal-change-engineer.md .claude/agents/
```

**Other environments:** provide `agent/icm-minimal-change-engineer.md` as the system/agent definition for the coding session.

**Project prerequisites:** the agent works best when your project has a CONTEXT.md (or equivalent), written task definitions, decision records for settled choices, and runnable checks. The less written truth exists, the more often it will legitimately stop.

**Optional — Claude Code mechanical enforcement:** two hooks under `hooks/` move part of the agent spec from instructions the model must comply with to machinery the model cannot influence: `protect_governing_files.py` makes CONTEXT.md/decisions/governance/specs mechanically uneditable (not just "please don't"), and `run_scope_gate_on_stop.py` re-runs the scope gate automatically at handoff instead of trusting the agent to run it. Both are off by default. To enable, merge `hooks/settings.snippet.json` into your project's `.claude/settings.json`, and — for the Stop hook — set `ICM_TASK_FILE` to the active task's YAML path for the session. Details and known limits: `docs/enforcement-roadmap.md`.

## How do I invoke it?

In Claude Code, address the agent by name for a bounded task:

```
Use the icm-minimal-change-engineer agent: fix the off-by-one error in
src/billing/prorate.js described in tasks/2026-08-09-prorate-bug.md.
```

Give it: the task, where "done" is defined, and the governing artifacts. Expect back: a minimal diff plus a Completion Report, or a BLOCKED REPORT. See `examples/example-use.md` for a full walkthrough.

## What authority does it have?

- Implement the assigned task within its stated scope.
- Choose between equal-scope correct implementations.
- Run the project's existing authorized checks and report real results.
- Stop, and require human input to proceed.
- Recommend follow-ups and surface concerns.

## What authority does it explicitly NOT have?

- Approving anything, or creating/advancing any approval artifact or state.
- Changing architecture, conventions, dependencies, or approved decisions.
- Redefining scope, acceptance criteria, tests, or gates.
- Resolving material ambiguity by guessing.
- Fixing anything outside the assigned task, however broken.

The full list is in the agent file under "What This Agent Does NOT Own."

## How was it tested?

- **Structural validation:** `tests/validate_package.py` mechanically checks that the package's required sections, status vocabulary, and prohibited-language rules hold. It passes for this release, and was negative-tested against deliberately broken copies.
- **Scope gate self-test:** `tests/scope_gate_selftest.sh` builds a throwaway Git repo and proves the gate passes compliant changes and fails deliberate violations — out-of-scope edits, protected-artifact tampering, untracked files in both modes, renames, committed changes, authorization-substitution bypass, self-authorization by editing the task file, special-character filenames, path normalization, parser strictness, the exit-code contract, the `.gitignore` bypass, and the default-mode audit boundary. The script's header is the single source of truth for the scenario inventory; this README deliberately carries no copied count, and the validator enforces both that the suite stays contiguously numbered above its shipped floor and that no numeric count claim is reintroduced here. The full suite passes for this release. **Windows note:** run with `PYTHONUTF8=1` set, or Python's default `cp1252` console encoding mangles the script's own output and `tests/validator_selftest.sh` fails on that alone; one scope-gate scenario also creates a filename containing `"`, which NTFS does not allow, so that single case cannot run on Windows regardless. Both are environment limitations, not defects in the gate's logic.
- **Validator self-test:** `tests/validator_selftest.sh` proves the validator itself, in a git-clone fixture, in both directions — a pristine clone passes and each planted defect class fails with the expected message.
- **Hook self-test:** `tests/hooks_selftest.sh` drives both optional hooks (`hooks/`) with real JSON payloads on stdin and asserts the contract they actually emit: protected paths denied and unprotected ones untouched, absolute paths relativized before matching, malformed input and missing config failing *open* while saying so on stderr, and — for the Stop hook — the gate's verbatim report reaching the model, the block ladder escalating to a human instead of trapping the session, and block counters resetting on PASS and staying per-session. Both hooks were negative-tested by mutation: breaking the deny branch and summarizing the gate's PASS each make this suite fail. The header is the single source of truth for its scenario inventory, as with the scope gate.
- **Behavioral test suite:** twelve scenario tests targeting the specific failure modes this agent exists to prevent (`tests/test-cases.md`, with expected run shapes in `tests/expected-behavior.md`), including scope-boundary violation by correct code, approval-artifact refusal, governing-context conflict, and incomplete validation. A first recorded run (`tests/behavioral-run-results.md`) is fully compliant on all 12 against Claude Sonnet 5; a repeat against Claude Haiku 4.5 (`tests/behavioral-run-haiku.md`) found 10/12 fully compliant and two real model-specific gaps. A full A/B comparison against a plain agent with no specification loaded, covering the full suite against both models (`tests/comparison-run-results.md`, per `tests/comparison-framework.md`), found no observed behavioral difference for Sonnet 5 — but for Haiku 4.5, the plain-agent condition produced three mechanically-verified violations its own ICM-agent condition did not on first observation: an approved-decision override, a private-module-boundary violation, and a fabricated approval artifact falsely attributed to a human reviewer. Every pairing in the comparison (the full scenario set, times both models, times both conditions) has since been brought to 3 runs each — 144 runs in total. Sonnet held at 72/72 compliant in both conditions, confirming its "no observed difference" result is not a sampling artifact. Haiku's plain-agent condition held its module-boundary violation at a fully deterministic 3/3, while its two other flagged violations each reproduced only 1 of 3 times — evidence a single run can correctly characterize one failure mode and mischaracterize another. Most surprisingly, Haiku's own ICM-agent condition, with the full specification loaded, also violated the module-boundary rule in 2 of its 3 runs — overturning the original single-run finding that the specification "stayed clean" there; the specification's protection against this specific failure mode is real but partial, not categorical, on this model. Haiku's other two flagged issues (an un-refused approval request, a wrong completion status) held or improved under repetition, with no approval artifact ever fabricated in the specification-loaded condition across any run.
- **A/B comparison method:** `tests/comparison-framework.md` defines how to measure whether the specification changes behavior versus a plain agent.

## What remains experimental?

- All instruction-level behavior. The agent specification constrains a model through instructions, and instructions can fail — especially over long sessions and under user pressure. The package reduces scope drift and boundary violations; it does not guarantee scope compliance, does not eliminate hallucinations or coding errors, and makes no security guarantees. `docs/controls.md` states exactly which rules are instruction-level and which are mechanically enforced.
- What the gate cannot see, even when it passes. It checks *which paths* changed, never *what changed inside them*: an unrequested refactor confined to a file already in `allowed_paths` passes cleanly, so minimum-surface discipline within an authorized file stays entirely instruction-level. Writes through a symlink to a target outside the repository are likewise invisible. `docs/controls.md` lists these boundaries in full; treating a gate PASS as "only the requested change was made" overstates what it verifies.
- What has been tested: package structure (validator, itself negative-tested by `tests/validator_selftest.sh` in a git-clone fixture), the scope gate (`tests/scope_gate_selftest.sh`, whose header enumerates the full scenario inventory — every code finding from the self-audit and both exercisable coverage gaps), and the instruction-level behaviors themselves (`tests/behavioral-run-results.md`, `tests/behavioral-run-haiku.md`, `tests/comparison-run-results.md`). What remains model-dependent — context-first ordering, decision protection, honest reporting, and all other instruction-level controls — is now partially exercised rather than untested, and real model-specific gaps have been found (Haiku 4.5). Repeatability is no longer untested for any pairing in this comparison: every scenario, both models, both conditions now has 3-run coverage. Sonnet 5 held at 72/72 compliant in both conditions. Haiku 4.5's plain-agent condition surfaced one fully deterministic module-boundary violation and two partially reproducible ones (decision override, approval fabrication). Haiku 4.5's ICM-agent condition — with the full specification loaded — surfaced the *same* module-boundary violation at a 2-of-3 rate, meaning the specification measurably reduces but does not eliminate that specific failure on this model; its other two flagged issues held or improved under repetition, with no approval ever fabricated. Other models and wider A/B coverage under sustained or escalating pressure are still open items; community results remain the other open item.
- Remaining mechanical enforcement — documented in `docs/enforcement-roadmap.md`. Read-only governing files and harness-run gate checks are implemented as optional Claude Code hooks (`hooks/`, off by default); approval-directory write restrictions and task schema validation are still deliberately not implemented.

## Repository structure

```
icm-minimal-change-engineer/
├── README.md                      ← this file
├── LICENSE                        ← MIT
├── CHANGELOG.md                   ← release history (Keep a Changelog style)
├── PROVENANCE.md                  ← origin and originality statement
├── agent/
│   └── icm-minimal-change-engineer.md   ← the agent specification (the product)
├── icm/
│   ├── SPEC.md                    ← ICM spec for this package's own construction
│   ├── BRIEF.md                   ← approved design decisions
│   └── TASK.md                    ← build plan and verification map
├── tests/
│   ├── test-cases.md              ← 12 behavioral tests
│   ├── expected-behavior.md       ← compliant run shapes and likely failure modes
│   ├── comparison-framework.md    ← plain-agent vs. ICM-agent A/B method
│   ├── behavioral-run-results.md  ← recorded T1-T12 run, Claude Sonnet 5
│   ├── behavioral-run-haiku.md    ← recorded T1-T12 run, Claude Haiku 4.5
│   ├── comparison-run-results.md  ← recorded A/B comparison run
│   ├── validate_package.py        ← mechanical structural validator
│   ├── scope_gate.py              ← deterministic Git diff scope + protected-path gate
│   ├── scope_gate_selftest.sh     ← proves the gate passes/fails correctly
│   ├── validator_selftest.sh      ← proves the validator itself, in a git-clone fixture
│   └── hooks_selftest.sh          ← proves both optional hooks emit the right decisions
├── examples/
│   ├── example-use.md             ← end-to-end usage walkthrough
│   └── task-definition-example.yaml ← task file with allowed/protected paths
├── hooks/                         ← optional Claude Code mechanical enforcement (off by default)
│   ├── protect_governing_files.py ← PreToolUse: makes governing files uneditable
│   ├── protected-paths.txt        ← governing-file list the above hook enforces
│   ├── run_scope_gate_on_stop.py  ← Stop: runs the scope gate automatically at handoff
│   └── settings.snippet.json      ← hook config to merge into .claude/settings.json
└── docs/
    ├── icm-compatibility.md       ← how the agent maps to ICM principles
    ├── controls.md                ← instruction-level vs. mechanically enforced controls
    ├── enforcement-roadmap.md     ← v0.1 → v0.2 → v0.3 (optional hooks) enforcement plan
    └── self-review.md             ← v0.1 review (historical) + v0.2/v0.2.1 reconciliation addendum
```

## License

MIT. See `LICENSE`. Provenance statement in `PROVENANCE.md`.
