#!/usr/bin/env python3
"""Build a ready-made evaluation fixture for one behavioral scenario.

Every tester who builds their own fixture measures something slightly
different, and results from different fixtures cannot be pooled or compared.
This builds the same repository from the same files every time, so a result
from one machine means the same thing as a result from another.

Usage:
    python3 tests/make_fixture.py t01              # build into ./icm-fixture-t01
    python3 tests/make_fixture.py t09 /tmp/work    # build into a chosen path
    python3 tests/make_fixture.py --list           # show the scenarios
    python3 tests/make_fixture.py --verify         # build all, check each one

What it produces: a committed Git repository containing the shared ledger
project, the scenario's own source files, the task at tasks/task.yaml, and a
copy of the scope gate at tools/scope_gate.py.

PROMPT.md is deliberately NOT copied into the fixture. It carries the exact
wording to give the agent, the trap being tested, and the evaluation criteria;
placing it inside the repository would hand the agent the answer key. It is
printed for the tester instead.

Exit codes:
    0  built (or verified) successfully
    1  a scenario did not behave as its expectation table says it should
    2  bad usage
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
BASE = os.path.join(FIXTURES, "_base")
GATE = os.path.join(HERE, "scope_gate.py")

# Whether the fixture's own checks already fail before the agent touches
# anything. Verified on every --verify run: a scenario whose planted bug
# stopped being reachable would otherwise keep producing confident,
# meaningless results.
STARTS_FAILING = {
    "t01": True,   "t02": True,  "t03": True,  "t04": True,
    "t05": True,   "t06a": False, "t06b": True, "t07": True,
    "t08": False,  "t09": False, "t10": True,  "t11": False,
    "t12a": True,  "t12b": True,
}

# The check command each scenario's own checks run under.
CHECK = {"t03": "tests/invoice_test.py"}
DEFAULT_CHECK = "tests/billing_test.py"


def scenarios():
    return sorted(d for d in os.listdir(FIXTURES)
                  if not d.startswith("_") and
                  os.path.isdir(os.path.join(FIXTURES, d)))


def copy_tree(src, dst):
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target, exist_ok=True)
        for name in files:
            shutil.copy2(os.path.join(root, name), os.path.join(target, name))


def git(repo, *args):
    result = subprocess.run(["git"] + list(args), cwd=repo,
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout


def build(scenario, target):
    """Assemble, commit, and return the fixture path."""
    src = os.path.join(FIXTURES, scenario)
    if not os.path.isdir(src):
        raise SystemExit("unknown scenario %r; try --list" % scenario)

    copy_tree(BASE, target)
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        for name in files:
            if name in ("PROMPT.md", "task.yaml"):
                continue                      # answer key / placed separately
            dest_dir = os.path.join(target, rel) if rel != "." else target
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(os.path.join(root, name),
                         os.path.join(dest_dir, name))

    os.makedirs(os.path.join(target, "tasks"), exist_ok=True)
    shutil.copy2(os.path.join(src, "task.yaml"),
                 os.path.join(target, "tasks", "task.yaml"))
    os.makedirs(os.path.join(target, "tools"), exist_ok=True)
    shutil.copy2(GATE, os.path.join(target, "tools", "scope_gate.py"))

    git(target, "init", "-q", ".")
    git(target, "config", "user.email", "fixture@example.invalid")
    git(target, "config", "user.name", "Fixture")
    git(target, "add", "-A")
    git(target, "commit", "-qm", "fixture: %s starting state" % scenario)
    return target


def run_check(repo, script):
    """Exit code of the fixture's own check script, or None if absent."""
    path = os.path.join(repo, script)
    if not os.path.exists(path):
        return None
    return subprocess.run([sys.executable, script], cwd=repo,
                          capture_output=True, text=True).returncode


def public_functions(path):
    with open(path, encoding="utf-8") as handle:
        return set(re.findall(r"^def ([a-z]\w*)", handle.read(), re.M))


def verify():
    """Build every scenario and check it is still the test it claims to be."""
    failures = []

    def fail(scenario, message):
        print("FAIL %s: %s" % (scenario, message))
        failures.append(scenario)

    for scenario in scenarios():
        workspace = tempfile.mkdtemp(prefix="icmfix-")
        repo = os.path.join(workspace, scenario)
        try:
            build(scenario, repo)

            if git(repo, "status", "--porcelain").strip():
                fail(scenario, "working tree is dirty straight after commit")

            # Order matters: run the checks FIRST, then the gate. Running the
            # checks is what a tester does, and it leaves __pycache__ behind.
            # Gating before that hides the pollution and lets a fixture ship
            # where every run fails for a reason unrelated to the agent.
            script = CHECK.get(scenario, DEFAULT_CHECK)
            code = run_check(repo, script)

            gate = subprocess.run(
                [sys.executable, "tools/scope_gate.py",
                 "--task", "tasks/task.yaml", "--repo", "."],
                cwd=repo, capture_output=True, text=True)
            if gate.returncode != 0:
                fail(scenario, "gate does not pass on the untouched fixture "
                               "after its checks have run (exit %d): %s"
                     % (gate.returncode, gate.stdout.strip()))

            if code is None:
                fail(scenario, "check script %s is missing" % script)
            elif STARTS_FAILING[scenario] and code == 0:
                fail(scenario, "%s passes, but this scenario's planted bug "
                               "should make it fail" % script)
            elif not STARTS_FAILING[scenario] and code != 0:
                fail(scenario, "%s fails before the agent has done anything"
                     % script)

            # T8 only tests what it claims to if storage exposes no sanctioned
            # route to customer records. An earlier version of this scenario
            # left a public escape hatch and the run proved nothing, so the
            # absence is asserted rather than assumed.
            if scenario == "t08":
                public = public_functions(os.path.join(repo, "src",
                                                       "storage.py"))
                if public != {"get_invoice", "find_invoices"}:
                    fail(scenario, "storage.py exposes %s; an unexpected "
                                   "public function may be a legitimate route "
                                   "to the override, which would void the "
                                   "scenario" % sorted(public))
            if not failures or failures[-1] != scenario:
                print("ok   %s" % scenario)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    print()
    if failures:
        print("FAIL - %d scenario(s) are not the test they claim to be"
              % len(failures))
        return 1
    print("PASS - all %d scenarios build and behave as described"
          % len(scenarios()))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Build an evaluation fixture for one behavioral scenario.")
    parser.add_argument("scenario", nargs="?", help="scenario id, e.g. t01")
    parser.add_argument("target", nargs="?", help="where to build it")
    parser.add_argument("--list", action="store_true",
                        help="list the available scenarios")
    parser.add_argument("--verify", action="store_true",
                        help="build every scenario and check each one")
    parser.add_argument("--force", action="store_true",
                        help="replace the target directory if it exists")
    args = parser.parse_args()

    if args.list:
        for scenario in scenarios():
            print(scenario)
        return 0
    if args.verify:
        return verify()
    if not args.scenario:
        parser.print_usage()
        return 2

    target = os.path.abspath(
        args.target or os.path.join(os.getcwd(), "icm-fixture-%s" % args.scenario))
    if os.path.exists(target):
        if not args.force:
            print("error - %s already exists; pass --force to replace it"
                  % target, file=sys.stderr)
            return 2
        shutil.rmtree(target)
    os.makedirs(target)

    build(args.scenario, target)
    prompt = os.path.join(FIXTURES, args.scenario, "PROMPT.md")
    print("Built %s at:\n  %s\n" % (args.scenario, target))
    print("The wording to give the agent, and what to check afterwards:")
    print("  %s\n" % prompt)
    print("Run the same scenario in both conditions, from the same starting")
    print("state, and rebuild between runs rather than reusing a dirty tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
