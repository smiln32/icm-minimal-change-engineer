#!/usr/bin/env bash
# Self-test for tests/validate_package.py — closes coverage gap G3:
# validator negative testing was previously ad hoc and never ran inside a
# git repository, which is exactly how the v0.2.2 .git empty-dir regression
# (F3) shipped. This script makes both directions reproducible, in a fixture
# that resembles how users actually receive the package: a git clone.
#
# Cases:
#   1. pristine copy, git-initialized, with the empty dirs a real .git
#      contains (.git/refs/tags, .git/branches) -> validator PASS
#   2. planted empty non-dot directory                -> FAIL, named
#   3. planted unexpected top-level entry             -> FAIL, named
#   4. retired status reintroduced in the agent file  -> FAIL
#   5. numeric self-test count claim reintroduced in README -> FAIL
#      (the duplicated fact that drifted three times is now banned outright)
#   6. syntax error appended to scope_gate.py         -> FAIL (F12 check)
#   7. gap in scenario numbering (renumbering error)  -> FAIL
#   8. scenario suite shrunk below its shipped floor  -> FAIL
#
# Usage: bash tests/validator_selftest.sh
# Exit 0 = validator behaved correctly in all cases.

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(dirname "$HERE")"
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
fails=0

fresh() {  # fresh git-initialized copy of the package
  rm -rf "$FIX/pkg"
  cp -r "$SRC" "$FIX/pkg"
  rm -rf "$FIX/pkg/.git"
  git -C "$FIX/pkg" init -q .
  mkdir -p "$FIX/pkg/.git/refs/tags" "$FIX/pkg/.git/branches"
}

expect_pass() {
  python3 "$FIX/pkg/tests/validate_package.py" "$FIX/pkg" >/dev/null 2>&1
  if [ $? -eq 0 ]; then echo "ok   $1"; else
    echo "FAIL $1"; python3 "$FIX/pkg/tests/validate_package.py" "$FIX/pkg" | head -5
    fails=$((fails+1)); fi
}

expect_fail() {  # expect_fail <label> <required-substring-of-output>
  out=$(python3 "$FIX/pkg/tests/validate_package.py" "$FIX/pkg" 2>&1)
  rc=$?
  if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "$2"; then echo "ok   $1"
  else echo "FAIL $1 (rc=$rc)"; printf '%s\n' "$out" | head -5; fails=$((fails+1)); fi
}

# 1. pristine clone passes despite .git's legitimate empty dirs
fresh
expect_pass "pristine git clone passes (F3 regression)"

# 2. empty non-dot directory still caught
fresh; mkdir "$FIX/pkg/agent/emptyjunk"
expect_fail "planted empty directory caught" "empty directory"

# 3. unexpected top-level entry caught
fresh; touch "$FIX/pkg/stray-file.txt"
expect_fail "unexpected top-level entry caught" "unexpected top-level"

# 4. retired status caught
fresh; printf '\nCOMPLETE — CHECKS PARTIAL\n' >> "$FIX/pkg/agent/icm-minimal-change-engineer.md"
expect_fail "retired status caught" "retired status"

# 5. reintroduced numeric count claim caught (single-source-of-truth ban)
fresh; python3 - "$FIX/pkg/README.md" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("The full suite passes for this release.",
              "All 99 scenarios pass for this release.")
open(p, "w").write(s)
PY
expect_fail "reintroduced numeric count claim caught" "counts live only in the self-test script"

# 6. broken shipped Python caught (F12)
fresh; printf '\ndef broken(:\n' >> "$FIX/pkg/tests/scope_gate.py"
expect_fail "syntax-broken gate caught" "syntax error"

# 7. numbering gap caught (rename a marker so 1..N is broken)
fresh; python3 - "$FIX/pkg/tests/scope_gate_selftest.sh" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("\n# 20. ", "\n# 22. ", 1)
open(p, "w").write(s)
PY
expect_fail "scenario-numbering gap caught" "not contiguous"

# 8. suite shrink below floor caught (delete the last scenario's marker line)
fresh; python3 - "$FIX/pkg/tests/scope_gate_selftest.sh" <<'PY'
import sys, re
p = sys.argv[1]; s = open(p).read()
# strip every body marker above 15 so max drops below the shipped floor
s = re.sub(r"^# (1[6-9]|20)\. ", r"# note: ", s, flags=re.M)
open(p, "w").write(s)
PY
expect_fail "suite shrink below shipped floor caught" "below its shipped floor"

echo
if [ "$fails" -eq 0 ]; then
  echo "PASS — validator self-test: all cases behaved as expected"
  exit 0
else
  echo "FAIL — validator self-test: $fails case(s) misbehaved"
  exit 1
fi
