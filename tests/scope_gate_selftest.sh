#!/usr/bin/env bash
# Self-test for tests/scope_gate.py — DoD requirement 12:
# deterministic checks must pass on compliant examples and fail on deliberate violations.
#
# Builds a throwaway git repo fixture, then exercises the gate:
#   1. compliant change            -> expect exit 0, PASS
#   2. out-of-scope change         -> expect exit 1, scope FAIL
#   3. protected artifact change   -> expect exit 2, protected FAIL
#   4. untracked out-of-scope file -> expect exit 1
#   5. protected path in BOTH allowed + authorized -> expect exit 0
#   6. rename out of scope         -> expect exit 1
#   7. --base commit-range mode    -> expect exit 1
#   8. --base + untracked out-of-scope file -> expect exit 1  (v0.2.1 regression)
#   9. protected + authorized but NOT allowed -> expect exit 1 (v0.2.1 regression:
#      authorized_protected_paths must never substitute for allowed_paths; the
#      protected-authorization rule is satisfied, so the failure is a SCOPE
#      violation — the path was never placed in the change surface)
#  10. filename with space + double-quote, untracked out-of-scope -> expect
#      exit 1 and the raw name in output (v0.2.2: -z parsing, no C-quoting)
#  11. allowed_paths entry containing ./ and ../ components matches its
#      normalized target -> expect exit 0 (v0.2.2: normalize collapses . and ..)
#  12. normalize() unit checks incl. the lstrip bug: "../etc" must stay
#      parent-escaping, never become "etc" (v0.2.2)
#  13. usage errors exit 3, never 2 -> a typo'd flag must not be readable as
#      a protected-artifact violation (v0.2.3, F1)
#  14. '#' inside a path is data, not a comment; whitespace-preceded '#'
#      still strips (v0.2.3, F2)
#  15. .gitignore bypass closed: committed ignore rules leave ignored files
#      invisible (control, PASS), but a diff touching .gitignore pulls
#      ignored-untracked files into scope checking (FAIL) (v0.2.4, F5)
#  16. default-mode PASS carries the uncommitted-work-only note; --base PASS
#      does not (v0.2.4, F4)
#  17. parser strictness: duplicate keys last-wins; inline []/value closes a
#      key; dangling list items, indented tracked keys, and bare junk all
#      exit 3 instead of silently mis-parsing (v0.2.5, F8)
#  18. "." allows the whole repo but protected rules still apply on top;
#      case-only mismatches fail strictly WITH a casing hint (v0.2.5, F9)
#  19. malformed -z streams raise contracted errors, never IndexError, and a
#      nonexistent --base ref exits 3 — completes the exit-3 contract
#      coverage (v0.2.6, F7 + G1)
#  20. the F4 boundary, live: a committed out-of-scope change is invisible to
#      default mode (PASS + note) and caught by --base (v0.2.6, G2)
#  21. self-authorization (F13): an in-repo task file is an
#      authorization the audited work can rewrite. A modified, committed, or
#      newly created in-repo task file refuses to certify (exit 4) in both
#      modes and outranks scope/protected verdicts; configurations where the
#      check cannot run (task file outside the repo, task_path omitted) say
#      so on PASS instead of implying it ran
#
# Usage: bash tests/scope_gate_selftest.sh
# Exit 0 = all cases behaved as expected.

set -u
GATE="$(cd "$(dirname "$0")" && pwd)/scope_gate.py"
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
fails=0

expect() { # expect <label> <expected_exit> <actual_exit>
  if [ "$2" -eq "$3" ]; then echo "ok   $1 (exit $3)"; else echo "FAIL $1 (expected $2, got $3)"; fails=$((fails+1)); fi
}

# --- fixture repo (task files live OUTSIDE the repo so they are not diff noise)
mkdir -p "$FIX/repo"
cd "$FIX/repo"
git init -q .
git config user.email t@t; git config user.name t
mkdir -p src tests approvals decisions/approved
echo "x=1" > src/app.py
echo "assert True" > tests/app_test.py
echo "approved" > approvals/release.md
echo "sqlite" > decisions/approved/storage.md
echo "misc" > src/other.py
git add -A && git commit -qm init

cat > "$FIX/task.yaml" <<'EOF'
allowed_paths:
  - src/app.py
  - tests/app_test.py
protected_paths:
  - approvals/
  - decisions/approved/
authorized_protected_paths: []
EOF

# 1. compliant change
echo "x=2" > src/app.py
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "compliant change passes" 0 $?
git checkout -q -- .

# 2. out-of-scope modification
echo "y=9" > src/other.py
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "out-of-scope change fails" 1 $?
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
case "$out" in *"outside authorized scope"*"src/other.py"*) echo "ok   scope FAIL names offending file";; *) echo "FAIL scope output wrong: $out"; fails=$((fails+1));; esac
git checkout -q -- .

# 3. protected artifact modification (distinct exit + message)
echo "tampered" > approvals/release.md
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "protected artifact fails distinctly" 2 $?
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
case "$out" in *"protected artifact modified"*"approvals/release.md"*) echo "ok   protected FAIL names artifact";; *) echo "FAIL protected output wrong: $out"; fails=$((fails+1));; esac
git checkout -q -- .

# 4. untracked out-of-scope file counts as a change
echo "new" > src/sneaky.py
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "untracked out-of-scope fails" 1 $?
rm src/sneaky.py

# 5. protected path listed in BOTH allowed_paths and authorized_protected_paths passes
cat > "$FIX/task_auth.yaml" <<'EOF'
allowed_paths:
  - src/app.py
  - approvals/release.md
protected_paths:
  - approvals/
authorized_protected_paths:
  - approvals/release.md
EOF
echo "task-authorized edit" > approvals/release.md
python3 "$GATE" --task "$FIX/task_auth.yaml" --repo . >/dev/null; expect "protected in both lists passes" 0 $?
git checkout -q -- .

# 6. rename to out-of-scope path fails
git mv src/app.py src/renamed.py
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "out-of-scope rename fails" 1 $?
git mv src/renamed.py src/app.py

# 7. committed changes caught via --base
echo "z=3" > src/other.py
git add -A && git commit -qm "out of scope commit"
python3 "$GATE" --task "$FIX/task.yaml" --repo . --base HEAD~1 >/dev/null; expect "--base mode catches committed violation" 1 $?
git reset -q --hard HEAD~1   # drop the out-of-scope commit for later cases

# 8. --base mode + UNTRACKED out-of-scope file must fail (v0.2.1 regression)
echo "sneaky" > src/untracked_sneak.py
python3 "$GATE" --task "$FIX/task.yaml" --repo . --base HEAD >/dev/null; expect "--base catches untracked out-of-scope file" 1 $?
rm src/untracked_sneak.py

# 9. protected + authorized_protected but NOT in allowed_paths must fail as a
#    SCOPE violation (exit 1): authorization is satisfied, allowance is not.
cat > "$FIX/task_auth_only.yaml" <<'EOF'
allowed_paths:
  - src/app.py
protected_paths:
  - approvals/
authorized_protected_paths:
  - approvals/release.md
EOF
echo "edit" > approvals/release.md
python3 "$GATE" --task "$FIX/task_auth_only.yaml" --repo . >/dev/null
rc=$?
expect "authorized-but-not-allowed protected fails (scope class)" 1 $rc
out=$(python3 "$GATE" --task "$FIX/task_auth_only.yaml" --repo .)
case "$out" in *"approvals/release.md"*) echo "ok   substitution-bypass FAIL names the path";; *) echo "FAIL substitution output wrong: $out"; fails=$((fails+1));; esac
git checkout -q -- .

# 10. special-character filename (space + double quote) must be detected raw
sneaky='src/we"ird file.py'
printf 'x' > "$sneaky"
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "quoted-name untracked out-of-scope fails" 1 $?
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
case "$out" in *'we"ird file.py'*) echo "ok   quoted-name FAIL shows raw filename";; *) echo "FAIL quoted-name output wrong: $out"; fails=$((fails+1));; esac
rm "$sneaky"

# 11. dotted/parent components in allowed_paths normalize before matching
cat > "$FIX/task_dotted.yaml" <<'EOF'
allowed_paths:
  - ./src/../src/app.py
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
echo "x=7" > src/app.py
python3 "$GATE" --task "$FIX/task_dotted.yaml" --repo . >/dev/null; expect "dotted allowed_paths entry matches after normalize" 0 $?
git checkout -q -- .

# 12. normalize() unit checks (including the lstrip prefix bug)
python3 - "$GATE" <<'PYUNIT'
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
from scope_gate import normalize
assert normalize("src/../foo") == "foo"
assert normalize("./src/./bar") == "src/bar"
assert normalize("../etc") == "../etc", "lstrip bug: parent escape must be preserved"
assert normalize("src/a/../b/x.py") == "src/b/x.py"
assert normalize("src/we\\ird.py") == "src/we\\ird.py", "backslash is filename data, not a separator"
print("unit-ok")
PYUNIT
[ $? -eq 0 ] && echo "ok   normalize unit checks pass" || { echo "FAIL normalize unit checks"; fails=$((fails+1)); }

# 13. exit-code contract: usage errors must be 3 (F1 regression)
python3 "$GATE" --task "$FIX/task.yaml" --bogus-flag >/dev/null 2>&1; expect "unknown flag exits 3 not 2" 3 $?
python3 "$GATE" --repo . >/dev/null 2>&1; expect "missing required --task exits 3" 3 $?
python3 "$GATE" --task "$FIX/does-not-exist.yaml" --repo . >/dev/null 2>&1; expect "unreadable task file exits 3" 3 $?

# 14. '#' handling in task YAML (F2 regression)
python3 - "$GATE" <<'PYHASH'
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
from scope_gate import parse_task_yaml
t = parse_task_yaml("allowed_paths:\n  - src/app#old.py\n  - src/clean.py  # comment\n")
assert t["allowed_paths"] == ["src/app#old.py", "src/clean.py"], t["allowed_paths"]
print("hash-ok")
PYHASH
[ $? -eq 0 ] && echo "ok   hash-in-path parsing correct" || { echo "FAIL hash-in-path parsing"; fails=$((fails+1)); }

# 15. .gitignore bypass (F5)
# Control: ignore rules committed and untouched -> ignored file stays invisible
printf '*.tmp\n' > .gitignore
git add .gitignore && git commit -qm "add ignore rules"
echo "junk" > src/build.tmp          # ignored, untracked, out of scope
echo "x=3" > src/app.py              # the compliant in-scope change
python3 "$GATE" --task "$FIX/task.yaml" --repo . >/dev/null; expect "committed ignore rules: ignored file invisible (control)" 0 $?
git checkout -q -- src/app.py
# Bypass attempt: diff touches .gitignore -> ignored files join scope checking
cat > "$FIX/task_ign.yaml" <<'EOF'
allowed_paths:
  - src/app.py
  - .gitignore
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
printf '*.tmp\n*.log\n' > .gitignore   # in-scope edit of ignore rules
echo "hidden" > src/sneaky.log           # newly-ignored out-of-scope file
python3 "$GATE" --task "$FIX/task_ign.yaml" --repo . >/dev/null; expect "gitignore edit pulls ignored files into scope check" 1 $?
out=$(python3 "$GATE" --task "$FIX/task_ign.yaml" --repo .)
case "$out" in *"src/sneaky.log"*) echo "ok   bypass FAIL names the hidden file";; *) echo "FAIL bypass output wrong: $out"; fails=$((fails+1));; esac
rm src/build.tmp src/sneaky.log
git checkout -q -- .gitignore

# 16. default-mode note (F4)
echo "x=4" > src/app.py
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
case "$out" in *"uncommitted work only"*) echo "ok   default-mode PASS carries audit-boundary note";; *) echo "FAIL default-mode note missing: $out"; fails=$((fails+1)); esac
git add -A && git commit -qm "committed in-scope change"
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo . --base HEAD~1)
case "$out" in *"uncommitted work only"*) echo "FAIL --base PASS should not carry the note"; fails=$((fails+1));; *"PASS"*) echo "ok   --base PASS has no note (exit $?)";; *) echo "FAIL --base run unexpected: $out"; fails=$((fails+1));; esac

# 17. F8 parser strictness — malformed task files exit 3 via the CLI
printf 'protected_paths: []\n  - approvals/\nallowed_paths:\n  - src/app.py\n' > "$FIX/task_dangling.yaml"
python3 "$GATE" --task "$FIX/task_dangling.yaml" --repo . >/dev/null 2>&1; expect "dangling list item exits 3 (fail-closed)" 3 $?
printf '  allowed_paths:\n  - src/app.py\n' > "$FIX/task_indented.yaml"
python3 "$GATE" --task "$FIX/task_indented.yaml" --repo . >/dev/null 2>&1; expect "indented tracked key exits 3" 3 $?
printf 'garbage line\nallowed_paths:\n  - src/app.py\n' > "$FIX/task_junk.yaml"
python3 "$GATE" --task "$FIX/task_junk.yaml" --repo . >/dev/null 2>&1; expect "bare top-level junk exits 3" 3 $?
python3 - "$GATE" <<'PYPARSE'
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
from scope_gate import parse_task_yaml
t = parse_task_yaml("allowed_paths:\n  - a.py\nallowed_paths:\n  - b.py\n")
assert t["allowed_paths"] == ["b.py"], t
t = parse_task_yaml("allowed_paths: src/only.py\nprotected_paths: []\n")
assert t["allowed_paths"] == ["src/only.py"] and t["protected_paths"] == [], t
print("parse-ok")
PYPARSE
[ $? -eq 0 ] && echo "ok   last-wins and key-closing semantics correct" || { echo "FAIL parser semantics"; fails=$((fails+1)); }

# 18. F9 — "." whole-repo allowance with protected still enforced; case hint
cat > "$FIX/task_dot.yaml" <<'EOF'
allowed_paths:
  - .
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
echo "y=1" > src/other.py
python3 "$GATE" --task "$FIX/task_dot.yaml" --repo . >/dev/null; expect "dot entry allows arbitrary file" 0 $?
git checkout -q -- src/other.py
echo "tamper" > approvals/release.md
python3 "$GATE" --task "$FIX/task_dot.yaml" --repo . >/dev/null; expect "protected still fails under whole-repo allowance" 2 $?
git checkout -q -- approvals/release.md
cat > "$FIX/task_case.yaml" <<'EOF'
allowed_paths:
  - src/App.py
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
echo "z=1" > src/app.py
python3 "$GATE" --task "$FIX/task_case.yaml" --repo . >/dev/null; expect "case-only mismatch fails strictly" 1 $?
out=$(python3 "$GATE" --task "$FIX/task_case.yaml" --repo .)
case "$out" in *"only by"*"case"*) echo "ok   casing hint present on near-miss";; *) echo "FAIL casing hint missing: $out"; fails=$((fails+1));; esac
git checkout -q -- src/app.py

# 19. F7 + G1: malformed streams and bad refs hit the error contract
python3 - "$GATE" <<'PYF7'
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
import scope_gate
for fake, base in [("M\x00", "HEAD"), ("R100\x00old.py\x00", "HEAD")]:
    scope_gate.git = lambda repo, *a, _f=fake: _f if a[0] == "diff" else ""
    try:
        scope_gate.changed_paths(".", base=base); sys.exit(1)
    except RuntimeError:
        pass
    except IndexError:
        sys.exit(2)
scope_gate.git = lambda repo, *a: "R  new.py\x00"
try:
    scope_gate.changed_paths("."); sys.exit(1)
except RuntimeError:
    print("f7-ok")
PYF7
[ $? -eq 0 ] && echo "ok   malformed streams raise contracted errors" || { echo "FAIL F7 stream handling"; fails=$((fails+1)); }
python3 "$GATE" --task "$FIX/task.yaml" --repo . --base no-such-ref >/dev/null 2>&1; expect "nonexistent --base ref exits 3" 3 $?

# 20. G2: the documented default-mode boundary, exercised live
echo "committed-violation" > src/other.py
git add src/other.py && git commit -qm "out-of-scope committed"
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
rc=$?
expect "default mode is blind to committed violation (documented boundary)" 0 $rc
case "$out" in *"uncommitted work only"*) echo "ok   blindness carries the boundary note";; *) echo "FAIL boundary note absent: $out"; fails=$((fails+1));; esac
python3 "$GATE" --task "$FIX/task.yaml" --repo . --base HEAD~1 >/dev/null; expect "--base catches the committed violation" 1 $?
git reset -q --hard HEAD~1

# 21. self-authorization: a task file INSIDE the repo is an authorization the
# audited work can rewrite. Every case here uses an in-repo task file, unlike
# the rest of this suite (see the fixture comment) — which is precisely why
# the hole survived until F13 was found.
mkdir -p tasks
cat > tasks/live.yaml <<'EOF'
allowed_paths:
  - src/app.py
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
git add tasks/live.yaml && git commit -qm "governing task"

# 21a. control: in-repo task file, untouched -> ordinary verdict
echo "x=3" > src/app.py
python3 "$GATE" --task tasks/live.yaml --repo . >/dev/null; expect "in-repo task file, unmodified, passes normally" 0 $?

# 21b. the attack: widen own allowed_paths to the whole repo, then sneak
cat > tasks/live.yaml <<'EOF'
allowed_paths:
  - .
protected_paths: []
authorized_protected_paths: []
EOF
echo "unrequested" > src/sneaky.py
echo "tampered" > approvals/release.md
python3 "$GATE" --task tasks/live.yaml --repo . >/dev/null; expect "self-widened task file refuses to certify" 4 $?
out=$(python3 "$GATE" --task tasks/live.yaml --repo .)
case "$out" in *"task file changed"*"tasks/live.yaml"*) echo "ok   exit-4 report names the task file";; *) echo "FAIL self-auth output wrong: $out"; fails=$((fails+1));; esac
case "$out" in *"NOT evaluated"*) echo "ok   exit-4 report withholds a scope verdict";; *) echo "FAIL exit-4 report implies a scope verdict: $out"; fails=$((fails+1));; esac

# 21c. --base must not be an escape hatch
python3 "$GATE" --task tasks/live.yaml --repo . --base HEAD >/dev/null; expect "--base mode also refuses" 4 $?

# 21d. committing the widened task first must not launder it under --base
git add -A && git commit -qm "sneak"
python3 "$GATE" --task tasks/live.yaml --repo . --base HEAD~1 >/dev/null; expect "committed task edit still refuses under --base" 4 $?
git reset -q --hard HEAD~1

# 21e. a NEWLY CREATED (untracked) in-repo task file is the same self-authorization
cat > tasks/fresh.yaml <<'EOF'
allowed_paths:
  - .
protected_paths: []
authorized_protected_paths: []
EOF
python3 "$GATE" --task tasks/fresh.yaml --repo . >/dev/null; expect "untracked in-repo task file refuses" 4 $?
rm tasks/fresh.yaml

# 21f. exit 4 outranks scope and protected failures (declarations untrusted,
# so neither of those verdicts is meaningful). Scope and protected violations
# are both present here and would otherwise return 1 and 2.
cat > tasks/live.yaml <<'EOF'
# edited during the task: differs from the committed governing version
allowed_paths:
  - src/app.py
protected_paths:
  - approvals/
authorized_protected_paths: []
EOF
echo "out-of-scope" > src/other.py
echo "tampered" > approvals/release.md
python3 "$GATE" --task tasks/live.yaml --repo . >/dev/null; expect "exit 4 outranks scope+protected violations" 4 $?
git checkout -q -- . ; git clean -qfd >/dev/null 2>&1

# 21g. non-diff-verifiable configurations must announce themselves, not imply
# a check that did not happen
echo "x=4" > src/app.py
out=$(python3 "$GATE" --task "$FIX/task.yaml" --repo .)
case "$out" in *"outside the repository"*"not diff-verifiable"*) echo "ok   external task file PASS admits it is unverifiable";; *) echo "FAIL external-task note absent: $out"; fails=$((fails+1));; esac
python3 - "$GATE" <<'PYSA'
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
import scope_gate
task = {"allowed_paths": ["src/app.py"], "protected_paths": [],
        "authorized_protected_paths": []}
code, report = scope_gate.run_gate(".", task)          # task_path omitted
assert code == 0, code
assert "was not checked" in report, report
print("selfauth-ok")
PYSA
[ $? -eq 0 ] && echo "ok   omitted task_path is announced, not silently skipped" || { echo "FAIL omitted task_path note"; fails=$((fails+1)); }
git checkout -q -- .

echo
if [ "$fails" -eq 0 ]; then echo "PASS — scope gate self-test: all cases behaved as expected"; exit 0
else echo "FAIL — scope gate self-test: $fails case(s) misbehaved"; exit 1; fi
