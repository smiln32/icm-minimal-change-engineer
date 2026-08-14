#!/usr/bin/env python3
"""Stop hook: runs tests/scope_gate.py automatically at handoff, instead of
trusting the agent to run it on its own initiative.

Implements enforcement-roadmap.md item 4 ("automated gate execution") for
Claude Code. The agent spec (Stage 7) already asks the model to run the
gate before reporting completion; this hook makes that happen regardless
of whether the model actually does it, by re-running the same check from
outside the model's control and blocking the Stop event on FAIL.

Wire-up (.claude/settings.json):
    {
      "hooks": {
        "Stop": [{
          "hooks": [{"type": "command",
                      "command": "python3 hooks/run_scope_gate_on_stop.py"}]
        }]
      }
    }

Applies only when the ICM_TASK_FILE environment variable is set to a task
YAML path for the current session (mirroring scope_gate.py's own explicit
--task requirement: no ambient default, no self-authorization). Unset ->
this hook is a silent no-op, so non-ICM-governed sessions are unaffected.

Runs in scope_gate.py's default mode (working tree + index vs HEAD). The
gate's own report -- including its "default mode audits uncommitted work
only" note -- is passed through verbatim, on PASS as well as FAIL:
summarizing or dropping it here would silently discard the exact caveat
this hook exists to make impossible to miss.

ICM_TASK_FILE is passed to the gate as the task path, not just parsed for
its contents, so the gate can check whether the session edited its own
declarations. Without it a session could widen allowed_paths in the task
file and be blessed by the hook that exists to catch exactly that.

On FAIL, blocks the Stop event (decision: "block") and feeds the gate's
own report back as the reason, so the model must address it or produce an
explicit BLOCKED REPORT rather than silently finishing with unreported
scope violations. To avoid trapping a session in an unresolvable loop
(e.g. the true answer is a human decision, not more edits), this stops
blocking after MAX_BLOCKS consecutive failures for the same session and
instead surfaces a warning -- a human must intervene at that point.
"""

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_PATH = HERE.parent / "tests" / "scope_gate.py"
MAX_BLOCKS = 3


def load_scope_gate():
    spec = importlib.util.spec_from_file_location("scope_gate", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def block_count_path(session_id):
    safe = "".join(c if c.isalnum() else "_" for c in (session_id or "unknown"))
    return Path(tempfile.gettempdir()) / f"icm-gate-stop-{safe}.count"


def main():
    task_file = os.environ.get("ICM_TASK_FILE")
    if not task_file:
        return 0  # not an ICM-governed session; nothing to enforce

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    session_id = payload.get("session_id")

    repo_root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())

    try:
        gate = load_scope_gate()
        with open(task_file, encoding="utf-8") as f:
            task = gate.parse_task_yaml(f.read())
    except (OSError, ValueError) as e:
        print(json.dumps({
            "systemMessage": f"run_scope_gate_on_stop: could not load "
                              f"ICM_TASK_FILE ({task_file}): {e}. Gate not run.",
        }))
        return 0

    if not task["allowed_paths"]:
        print(json.dumps({
            "systemMessage": f"run_scope_gate_on_stop: {task_file} declares "
                              f"no allowed_paths; gate cannot run.",
        }))
        return 0

    try:
        code, report = gate.run_gate(str(repo_root), task, base=None,
                                     task_path=task_file)
    except RuntimeError as e:
        print(json.dumps({
            "systemMessage": f"run_scope_gate_on_stop: gate error: {e}",
        }))
        return 0

    if code == 0:
        # gate passed: clear any prior block-count and let the stop proceed.
        # `report` is passed through verbatim -- it carries the "audits
        # uncommitted work only" note, which a bare "PASS" would hide.
        block_count_path(session_id).unlink(missing_ok=True)
        print(json.dumps({
            "systemMessage": f"Automated scope gate (task {task_file}):\n{report}",
        }))
        return 0

    counter = block_count_path(session_id)
    attempts = 0
    if counter.exists():
        try:
            attempts = int(counter.read_text().strip() or "0")
        except ValueError:
            attempts = 0
    attempts += 1

    if attempts > MAX_BLOCKS:
        print(json.dumps({
            "systemMessage": (
                f"Automated scope gate: FAIL after {attempts - 1} automatic "
                f"retries. No longer blocking Stop automatically -- this "
                f"needs a human decision.\n\n{report}"
            ),
        }))
        return 0

    counter.write_text(str(attempts))
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"Automated scope gate FAIL (task {task_file}), attempt "
            f"{attempts}/{MAX_BLOCKS}. This ran automatically at handoff, "
            f"not at your initiative -- resolve the violation (remove the "
            f"unauthorized change, or stop with a BLOCKED REPORT if it "
            f"cannot be resolved in scope) before finishing.\n\n{report}"
        ),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
