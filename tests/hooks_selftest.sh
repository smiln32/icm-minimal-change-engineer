#!/usr/bin/env bash
# Self-test for hooks/protect_governing_files.py and hooks/run_scope_gate_on_stop.py.
#
# Until this file existed, the hooks were the only shipped code without an
# automated suite — verified once by hand-piped payloads, then trusted. That is
# exactly the "asked, not imposed" posture the hooks were built to replace, so
# the gap is closed here on the same terms as scope_gate_selftest.sh: real
# payloads on real stdin, assertions on the actual emitted contract.
#
# Both hooks speak the Claude Code hook protocol: a JSON payload on stdin, an
# optional JSON decision on stdout, exit 0 regardless. "Allow" is therefore
# empty stdout, not an exit code — several cases below assert exactly that,
# because a hook that fails open silently and a hook that never ran are
# indistinguishable to anything checking status alone.
#
# protect_governing_files.py (PreToolUse):
#   1. exact protected file  -> deny
#   2. file inside a protected directory -> deny
#   3. unprotected file      -> allow (empty stdout)
#   4. notebook_path honored as a target path key -> deny
#   5. tool_input with no path at all -> allow, no crash
#   6. unparseable stdin     -> fails OPEN, and says so on stderr
#   7. absolute file_path (what Claude Code actually sends) relativizes
#      against CLAUDE_PROJECT_DIR before matching -> deny
#   8. path escaping the project root is not matched against project entries
#   9. case-only mismatch is NOT denied — the documented case-sensitive
#      boundary, asserted so a silent change to it fails here first
#  10. missing protected-paths.txt -> fails OPEN with a stderr note
#  11. deny reason names the offending path and its config file
#
# run_scope_gate_on_stop.py (Stop):
#  12. ICM_TASK_FILE unset   -> silent no-op (non-ICM sessions unaffected)
#  13. unreadable task file  -> systemMessage, never a block
#  14. task declaring no allowed_paths -> systemMessage, never a block
#  15. compliant tree -> PASS passed through verbatim, INCLUDING the gate's
#      uncommitted-work-only note (the caveat a bare "PASS" would hide)
#  16. scope violation -> decision:block carrying the gate's own report
#  17. escalation ladder: blocks at 1/3, 2/3, 3/3, then stops blocking and
#      hands over to a human instead of trapping the session
#  18. a PASS clears the counter, so a later violation restarts at 1/3
#  19. counters are per-session: a second session_id starts its own ladder
#  20. ICM_TASK_FILE reaches the gate as a path, so a session that widens its
#      own in-repo task file is blocked rather than blessed (F13)
#
# Usage: bash tests/hooks_selftest.sh
# Exit 0 = all cases behaved as expected.

set -u
TESTS="$(cd "$(dirname "$0")" && pwd)"
HOOKS="$(cd "$(dirname "$0")/../hooks" && pwd)"
PROTECT="$HOOKS/protect_governing_files.py"
STOPHOOK="$HOOKS/run_scope_gate_on_stop.py"
FIX="$(mktemp -d)"
fails=0

SESSION_A=icmselftestsessionA
SESSION_B=icmselftestsessionB
SESSION_C=icmselftestsessionC

# The Stop hook keeps its per-session block counter in the system temp dir,
# which outlives this fixture. Ask Python for the same path it uses rather
# than guessing at $TMPDIR, which differs from tempfile.gettempdir() on
# Windows shells.
clear_counter() {
  python3 -c 'import sys, tempfile, pathlib
pathlib.Path(tempfile.gettempdir(), "icm-gate-stop-%s.count" % sys.argv[1]).unlink(missing_ok=True)' "$1"
}

cleanup() { rm -rf "$FIX"; clear_counter "$SESSION_A"; clear_counter "$SESSION_B"
            clear_counter "$SESSION_C"; }
trap cleanup EXIT

expect() { # expect <label> <expected_exit> <actual_exit>
  if [ "$2" -eq "$3" ]; then echo "ok   $1 (exit $3)"
  else echo "FAIL $1 (expected $2, got $3)"; fails=$((fails+1)); fi
}

expect_has() { # expect_has <label> <needle> <haystack>
  case "$3" in *"$2"*) echo "ok   $1";;
    *) echo "FAIL $1 — missing '$2' in: $3"; fails=$((fails+1));; esac
}

expect_lacks() { # expect_lacks <label> <needle> <haystack>
  case "$3" in *"$2"*) echo "FAIL $1 — unexpected '$2' in: $3"; fails=$((fails+1));;
    *) echo "ok   $1";; esac
}

expect_empty() { # expect_empty <label> <output>
  if [ -z "$2" ]; then echo "ok   $1"
  else echo "FAIL $1 — expected no output, got: $2"; fails=$((fails+1)); fi
}

# Assertions match ASCII fragments only: both hooks emit via json.dumps, which
# escapes the gate report's em dashes to —, so "FAIL —" never appears
# literally on stdout.

# Built through json.dumps rather than printf: case 7 feeds a native absolute
# path, and on Windows its backslashes are invalid JSON escapes if pasted raw.
pre_payload() { # pre_payload <path> [key]
  python3 -c 'import json, sys
print(json.dumps({"tool_name": "Edit", "tool_input": {sys.argv[2]: sys.argv[1]}}))' "$1" "${2:-file_path}"
}

# --- fixture repo -----------------------------------------------------------
# Task files are committed INSIDE the repo here (unlike scope_gate_selftest.sh,
# which keeps them outside): the Stop hook resolves ICM_TASK_FILE relative to
# the cwd, and a tracked, unmodified file adds no diff noise for the gate.
mkdir -p "$FIX/repo"
cd "$FIX/repo"
git init -q .
git config user.email t@t; git config user.name t
mkdir -p src decisions/approved specs
echo "project context" > CONTEXT.md
echo "x=1" > src/app.py
echo "misc" > src/other.py
echo "sqlite" > decisions/approved/storage.md
echo "spec" > specs/api.md

cat > task.yaml <<'EOF'
allowed_paths:
  - src/app.py
protected_paths:
  - decisions/
authorized_protected_paths: []
EOF

cat > task_empty.yaml <<'EOF'
allowed_paths: []
protected_paths:
  - decisions/
authorized_protected_paths: []
EOF

git add -A && git commit -qm init

# ===========================================================================
# protect_governing_files.py
# ===========================================================================

# 1. exact protected file
out=$(pre_payload "CONTEXT.md" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT"); rc=$?
expect "protected file: hook still exits 0 (deny travels in JSON)" 0 $rc
expect_has "protected file denied" '"permissionDecision": "deny"' "$out"

# 2. file inside a protected directory
out=$(pre_payload "decisions/approved/storage.md" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_has "file inside protected directory denied" '"permissionDecision": "deny"' "$out"

# 3. unprotected file — allow is empty stdout, not an exit code
out=$(pre_payload "src/app.py" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT"); rc=$?
expect "unprotected file allowed (exit)" 0 $rc
expect_empty "unprotected file emits no decision" "$out"

# 4. notebook_path is a target path key too
out=$(pre_payload "specs/api.md" notebook_path | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_has "notebook_path target denied" '"permissionDecision": "deny"' "$out"

# 5. tool_input carrying no path at all
out=$(printf '{"tool_name":"Edit","tool_input":{}}' | CLAUDE_PROJECT_DIR=. python3 "$PROTECT"); rc=$?
expect "pathless tool_input allowed (exit)" 0 $rc
expect_empty "pathless tool_input emits no decision" "$out"

# 6. unparseable stdin must fail OPEN and announce it — a mechanical control
# degrading to "not enforced" has to be visible, not silent either way
out=$(printf 'not json at all' | CLAUDE_PROJECT_DIR=. python3 "$PROTECT" 2>"$FIX/err.txt"); rc=$?
err=$(cat "$FIX/err.txt")
expect "unparseable stdin fails open (exit)" 0 $rc
expect_empty "unparseable stdin emits no decision" "$out"
expect_has "unparseable stdin announces non-enforcement" "enforcement is NOT active" "$err"

# 7. absolute path — the form Claude Code actually sends
abs=$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' CONTEXT.md)
out=$(pre_payload "$abs" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_has "absolute path relativized then denied" '"permissionDecision": "deny"' "$out"

# 8. a path outside the project root must not collide with project entries
out=$(pre_payload "../CONTEXT.md" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_empty "path outside project root not matched" "$out"

# 9. case-only mismatch is allowed — documented boundary, asserted so that
# changing it silently fails here rather than surprising someone downstream
out=$(pre_payload "context.md" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_empty "case-only mismatch not denied (case-sensitive boundary)" "$out"

# 10. missing config fails OPEN, with a note — enforcement must never vanish
# quietly. Needs a package copy, since the hook resolves its config and the
# gate relative to its own location.
# The gate IS copied and protected-paths.txt is NOT, so this isolates a
# missing config; copying neither would pass on the missing-gate branch instead.
mkdir -p "$FIX/pkg/hooks" "$FIX/pkg/tests"
cp "$HOOKS"/*.py "$FIX/pkg/hooks/"
cp "$TESTS/scope_gate.py" "$FIX/pkg/tests/"
[ -f "$FIX/pkg/tests/scope_gate.py" ] || { echo "FAIL fixture: scope_gate.py not copied"; fails=$((fails+1)); }
[ -f "$FIX/pkg/hooks/protected-paths.txt" ] && { echo "FAIL fixture: config should be absent"; fails=$((fails+1)); }
out=$(pre_payload "CONTEXT.md" | CLAUDE_PROJECT_DIR=. python3 "$FIX/pkg/hooks/protect_governing_files.py" 2>"$FIX/err.txt"); rc=$?
err=$(cat "$FIX/err.txt")
expect "missing config fails open (exit)" 0 $rc
expect_empty "missing config emits no decision" "$out"
expect_has "missing config announces non-enforcement" "enforcement is NOT active" "$err"

# 11. the denial has to be actionable: which path, and where to change it
out=$(pre_payload "CONTEXT.md" | CLAUDE_PROJECT_DIR=. python3 "$PROTECT")
expect_has "deny reason names the path" "CONTEXT.md" "$out"
# Match the filename, not a fixed prefix. The hook now reports the config
# relative to the project when it sits inside it (the installed .icm/ layout)
# and absolute otherwise, so a hard-coded "hooks/" prefix would assert the
# package layout rather than the contract, which is that the reader is told
# which file to edit.
expect_has "deny reason names its config file" "protected-paths.txt" "$out"

# ===========================================================================
# run_scope_gate_on_stop.py
# ===========================================================================

stop_payload() { printf '{"session_id":"%s"}' "$1"; }

# 12. no ICM_TASK_FILE -> silent no-op, so non-ICM sessions are untouched
out=$(stop_payload "$SESSION_A" | CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK"); rc=$?
expect "unset ICM_TASK_FILE is a no-op (exit)" 0 $rc
expect_empty "unset ICM_TASK_FILE emits nothing" "$out"

# 13. unreadable task file reports, never blocks — a broken pointer is a
# configuration problem, not a scope violation to hold the session on
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=nope.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK"); rc=$?
expect "unreadable task file (exit)" 0 $rc
expect_has "unreadable task file reports" "could not load" "$out"
expect_lacks "unreadable task file does not block" '"decision": "block"' "$out"

# 14. a task with no allowed_paths cannot be audited; say so, do not block
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task_empty.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "empty allowed_paths reports" "no allowed_paths" "$out"
expect_lacks "empty allowed_paths does not block" '"decision": "block"' "$out"

# 15. compliant change: PASS and — the point of the case — the gate's own
# caveat, verbatim. Summarizing this to "PASS" is the specific regression.
echo "x=2" > src/app.py
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK"); rc=$?
expect "compliant tree (exit)" 0 $rc
expect_has "compliant tree passes the gate" "all changed files are within authorized scope" "$out"
expect_has "PASS carries the uncommitted-only note verbatim" "default mode audits uncommitted work only" "$out"
expect_lacks "compliant tree does not block" '"decision": "block"' "$out"
git checkout -q -- .

# 16. scope violation blocks, carrying the gate's report rather than a summary
clear_counter "$SESSION_A"
echo "y=1" > src/other.py
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK"); rc=$?
expect "scope violation (exit)" 0 $rc
expect_has "scope violation blocks Stop" '"decision": "block"' "$out"
expect_has "block carries the gate report" "changed files outside authorized scope" "$out"
expect_has "block names the offending file" "src/other.py" "$out"
expect_has "block is attempt 1 of 3" "attempt 1/3" "$out"

# 17. the ladder: 2/3, 3/3, then hand over instead of trapping the session
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "second failure is attempt 2/3" "attempt 2/3" "$out"
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "third failure is attempt 3/3" "attempt 3/3" "$out"
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_lacks "fourth failure stops blocking" '"decision": "block"' "$out"
expect_has "fourth failure escalates to a human" "needs a human decision" "$out"
expect_has "escalation still carries the report" "changed files outside authorized scope" "$out"

# 18. a PASS resets the ladder, so an unrelated later violation is not
# pre-escalated by history the session already resolved
git checkout -q -- .
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "resolving the violation passes" "all changed files are within authorized scope" "$out"
echo "y=2" > src/other.py
out=$(stop_payload "$SESSION_A" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "PASS cleared the counter (back to 1/3)" "attempt 1/3" "$out"

# 19. counters are per-session, not global
out=$(stop_payload "$SESSION_B" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "a second session starts its own ladder" "attempt 1/3" "$out"
git checkout -q -- .

# 20. self-authorization at the hook layer (F13). ICM_TASK_FILE must
# reach the gate as a PATH, not just as parsed contents: a session that widens
# its own in-repo task file would otherwise be blessed by the very hook that
# exists to audit it. The regression this guards is a one-word change in the
# hook (dropping task_path=), so it is asserted here, not inferred from the
# gate's own suite.
clear_counter "$SESSION_C"
cat > task.yaml <<'EOF'
allowed_paths:
  - .
protected_paths: []
authorized_protected_paths: []
EOF
echo "unrequested" > src/sneaky.py
out=$(stop_payload "$SESSION_C" | ICM_TASK_FILE=task.yaml CLAUDE_PROJECT_DIR=. python3 "$STOPHOOK")
expect_has "self-widened task file blocks Stop" '"decision": "block"' "$out"
expect_has "block explains the task file changed" "task file changed" "$out"
expect_has "block withholds a scope verdict" "NOT evaluated" "$out"
git checkout -q -- . ; rm -f src/sneaky.py

# --- report -----------------------------------------------------------------
echo
if [ "$fails" -eq 0 ]; then
  echo "PASS - hooks self-test: all cases behaved as expected"
  exit 0
fi
echo "FAIL - hooks self-test: $fails case(s) misbehaved"
exit 1
