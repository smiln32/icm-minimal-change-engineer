#!/usr/bin/env python3
"""PreToolUse hook: makes governing files (CONTEXT.md, decisions/, etc.)
mechanically uneditable, regardless of model compliance.

Implements enforcement-roadmap.md item 1 ("read-only governing files") for
Claude Code: converts "do not edit" (an instruction the agent can violate)
into "cannot edit" (a denial the tool layer enforces before the edit
happens). This is independent of tests/scope_gate.py's per-task
allowed_paths/protected_paths audit, which runs after the fact against a
task's own declared scope; this hook runs before the fact against a
standing, task-independent list (hooks/protected-paths.txt) and has no
concept of authorized_protected_paths — there is no override short of
editing that file yourself.

Wire-up (.claude/settings.json):
    {
      "hooks": {
        "PreToolUse": [{
          "matcher": "Write|Edit|NotebookEdit",
          "hooks": [{"type": "command",
                      "command": "python3 hooks/protect_governing_files.py"}]
        }]
      }
    }

Reads the PreToolUse hook JSON on stdin, matches tool_input's target path
against hooks/protected-paths.txt using tests/scope_gate.py's own
normalize()/covered_by() (imported directly — one matching implementation,
not two that could drift), and denies the call via
hookSpecificOutput.permissionDecision when it matches. Fails open (allows
the call, prints a note to stderr) if the hook input can't be parsed or the
config file is missing, so a broken hook cannot silently disable editing
altogether -- the mechanical control degrading to "not enforced" must be
visible, not "everything is blocked" or "everything is silently unblocked."
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "protected-paths.txt"


def find_gate():
    """Locate scope_gate.py in either the package layout or an installed one.

    In this repository the gate sits at ../tests/scope_gate.py. install.py
    puts it at ../scope_gate.py inside a project's .icm/ directory, because
    dropping a tests/ folder into someone else's project root would collide
    with the tests/ folder they already have. Both are supported rather than
    one being converted to the other, so the hooks keep working here and there
    with no edit at install time.
    """
    override = os.environ.get("ICM_GATE")
    candidates = ([Path(override)] if override else []) + [
        HERE.parent / "tests" / "scope_gate.py",
        HERE.parent / "scope_gate.py",
        HERE / "scope_gate.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


GATE_PATH = find_gate()


def config_label():
    """How to refer to the config file in a message the user will act on.

    Relative to the project when it sits inside it (the installed .icm/
    layout), absolute otherwise. Naming a path the reader cannot find is
    worse than naming none.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        return CONFIG_PATH.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(CONFIG_PATH)


def load_scope_gate():
    spec = importlib.util.spec_from_file_location("scope_gate", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_protected_entries(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if line:
                entries.append(line)
    return entries


def target_path(tool_input):
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"protect_governing_files: unreadable hook input, allowing "
              f"({e}); enforcement is NOT active for this call", file=sys.stderr)
        return 0

    tool_input = payload.get("tool_input", {})
    raw_path = target_path(tool_input)
    if not raw_path:
        return 0  # nothing to check (e.g. NotebookEdit variants without a path)

    try:
        gate = load_scope_gate()
        entries = load_protected_entries(CONFIG_PATH)
    except OSError as e:
        print(f"protect_governing_files: cannot load config/gate, allowing "
              f"({e}); enforcement is NOT active for this call", file=sys.stderr)
        return 0

    repo_root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    try:
        rel = os.path.relpath(raw_path, repo_root)
    except ValueError:
        rel = raw_path  # different drive on Windows; compare as given
    rel = rel.replace("\\", "/")

    if any(gate.covered_by(rel, entry) for entry in entries):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"'{rel}' is a protected governing file "
                    f"({config_label()}). Governing files are "
                    f"read-only for agent tooling: inspect them, never "
                    f"edit them. If this file genuinely needs to change, "
                    f"a human must edit it directly outside this session, "
                    f"or edit {config_label()} to descope it."
                ),
            }
        }))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
