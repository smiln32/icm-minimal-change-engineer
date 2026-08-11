#!/usr/bin/env python3
"""Structural validator for the ICM Minimal Change Engineer package.

Mechanically checks that the release contains its required files, sections,
status vocabulary, and language constraints. This validates package structure
only; it does not (and cannot) validate agent runtime behavior — see
tests/test-cases.md for behavioral evaluation.

Usage:  python3 tests/validate_package.py [repo_root]
Exit 0 = all checks pass; exit 1 = one or more failures (listed).
"""

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md", "LICENSE", "CHANGELOG.md", "PROVENANCE.md",
    "agent/icm-minimal-change-engineer.md",
    "icm/SPEC.md", "icm/BRIEF.md", "icm/TASK.md",
    "tests/test-cases.md", "tests/expected-behavior.md",
    "tests/comparison-framework.md", "tests/validate_package.py",
    "tests/scope_gate.py", "tests/scope_gate_selftest.sh", "tests/validator_selftest.sh",
    "examples/example-use.md", "examples/task-definition-example.yaml",
    "docs/icm-compatibility.md", "docs/self-review.md",
    "docs/controls.md", "docs/enforcement-roadmap.md",
]

STATUSES = [
    "COMPLETE — CHECKS PASS", "IMPLEMENTATION COMPLETE — VALIDATION INCOMPLETE",
    "BLOCKED", "FAILED CHECK",
]

THEATRICAL = ["world-class", "decades of experience", "you remember every bug"]

README_QUESTIONS = [
    "What problem does this agent solve",
    "Who is it for",
    "When should it be used",
    "When should it NOT be used",
    "make minimal changes",          # differentiation question
    "What makes it ICM-native",
    "install / use",
    "How do I invoke it",
    "What authority does it have",
    "NOT have",
    "How was it tested",
    "What remains experimental",
]

AGENT_SECTIONS = [
    "Purpose", "ICM governing principles", "Role definition",
    "What This Agent Does NOT Own", "Inputs and outputs", "Operating workflow",
    "STOP conditions", "Output contract", "Anti-patterns", "Judgment boundaries",
]

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


# 1. Required files exist
for rel in REQUIRED_FILES:
    check((ROOT / rel).exists(), f"missing required file: {rel}")

# 2. Agent file structure
agent = read("agent/icm-minimal-change-engineer.md")
check(agent.startswith("---"), "agent file: missing YAML frontmatter")
check("name: icm-minimal-change-engineer" in agent, "agent frontmatter: missing name")
for sec in AGENT_SECTIONS:
    check(sec in agent, f"agent file: missing section '{sec}'")

# 2a. Ten governing principles (counted inside the principles section only,
# so numbered bold lists elsewhere cannot inflate the count)
_sect = agent.split("## 2. ICM governing principles", 1)[-1].split("\n## ", 1)[0]
principles = re.findall(r"^\d+\.\s+\*\*", _sect, re.M)
check(len(principles) >= 10, f"agent file: expected >=10 numbered bold principles in section 2, found {len(principles)}")

# 2b. Eight workflow stages
stages = re.findall(r"### Stage ([1-8]) [—-]", agent)
check(len(set(stages)) == 8, f"agent file: expected 8 workflow stages, found {len(set(stages))}")

# 2c. Eight STOP conditions S1..S8
stops = {m for m in re.findall(r"\| (S[1-8]) \|", agent)}
check(len(stops) == 8, f"agent file: expected STOP conditions S1..S8, found {sorted(stops)}")

# 2d. Closed status vocabulary present
for s in STATUSES:
    check(s in agent, f"agent file: status '{s}' not defined")

# 2e. Forbidden statuses never offered as agent-issued states
for bad in ["Status: APPROVED", "Status: CERTIFIED", "Status: PRODUCTION APPROVED",
            "Status: HUMAN APPROVAL COMPLETE"]:
    check(bad not in agent, f"agent file: forbidden agent-issued status present: {bad}")

# 2f. No theatrical language in agent file or README
readme = read("README.md")
for phrase in THEATRICAL:
    check(phrase.lower() not in agent.lower(), f"agent file: theatrical phrase '{phrase}'")
    check(phrase.lower() not in readme.lower(), f"README: theatrical phrase '{phrase}'")

# 2g. No overselling in README
check("production-grade" not in readme.lower(), "README: claims 'production-grade'")
check("eliminates hallucination" not in readme.lower(), "README: hallucination-elimination claim")

# 2h. v0.2: retired status must be gone everywhere except the changelog
for rel in [f for f in REQUIRED_FILES if f.endswith(".md") and f != "CHANGELOG.md"]:
    check("CHECKS PARTIAL" not in read(rel), f"{rel}: retired status 'CHECKS PARTIAL' still present")

# 2i. v0.2: observable Task Contract with all nine fields
check("TASK CONTRACT" in agent, "agent file: TASK CONTRACT block missing")
for fld in ["Requested outcome:", "Acceptance criteria:", "Governing artifacts:",
            "Authorized files/paths:", "Protected files/paths:",
            "Relevant approved decisions:", "Required checks:",
            "Known constraints:", "Out-of-scope items:"]:
    check(fld in agent, f"agent file: Task Contract missing field '{fld}'")
check("Contract Comparison" in agent, "agent file: Completion Report missing Contract Comparison")

# 2j. v0.2: scope declarations documented
for key in ["allowed_paths", "protected_paths", "authorized_protected_paths"]:
    check(key in agent, f"agent file: scope declaration '{key}' undocumented")

# 2k. v0.2: standard BLOCKED REPORT fields + conflict form
for fld in ["Blocking condition:", "Governing artifact involved:",
            "Why work cannot safely continue:", "What was completed before the block:",
            "What was not changed:", "Required next decision or input:",
            "Current project state:"]:
    check(fld in agent, f"agent file: BLOCKED REPORT missing field '{fld}'")
check("BLOCKED — GOVERNING CONTEXT CONFLICT" in agent, "agent file: conflict form missing")
for fld in ["Artifact A:", "Artifact B:", "Conflict:", "Why it affects the task:"]:
    check(fld in agent, f"agent file: conflict form missing field '{fld}'")

# 2l. v0.2: PASS != APPROVED stated consistently
for rel in ["agent/icm-minimal-change-engineer.md", "README.md",
            "docs/icm-compatibility.md", "docs/controls.md"]:
    check("PASS != APPROVED" in read(rel), f"{rel}: missing 'PASS != APPROVED' statement")

# 2m. v0.2: COMPLETE-prefix rule stated
check("no status beginning with `COMPLETE`" in agent,
      "agent file: COMPLETE-prefix rule missing")

# 2n. v0.2: controls doc separates the two categories
controls = read("docs/controls.md")
check("Instruction-level controls" in controls, "controls: missing instruction-level section")
check("Mechanically enforced controls" in controls, "controls: missing mechanical section")
check("cannot guarantee" in controls, "controls: missing cannot-guarantee statement")

# 2o. v0.2: roadmap has all three stages
roadmap = read("docs/enforcement-roadmap.md")
for stage in ["v0.1 — Prompt governed", "v0.2 — Diff and scope enforcement",
              "Future — Permission and filesystem enforcement"]:
    check(stage in roadmap, f"roadmap: missing stage '{stage}'")

# 3. Test suite: 12 tests, each with the four required fields
tests_md = read("tests/test-cases.md")
test_ids = re.findall(r"^## (T\d+) —", tests_md, re.M)
check(len(test_ids) >= 12, f"test-cases: expected >=12 tests, found {len(test_ids)}")
for tid in test_ids:
    block = tests_md.split(f"## {tid} —", 1)[1].split("\n## ", 1)[0]
    for field in ["**Scenario.**", "**Expected behavior.**", "**Prohibited behavior.**", "**PASS criteria.**"]:
        check(field in block, f"test-cases {tid}: missing field {field}")

# 3a. Expected-behavior covers every test id
expected = read("tests/expected-behavior.md")
for tid in test_ids:
    check(f"## {tid}" in expected, f"expected-behavior: missing section for {tid}")

# 3b. Comparison framework has 8 dimensions
comp = read("tests/comparison-framework.md")
dims = re.findall(r"^\| \*\*(.+?)\*\* \|", comp, re.M)
check(len(dims) >= 8, f"comparison-framework: expected >=8 dimensions, found {len(dims)}")

# 4. README answers all Part-10 questions
for q in README_QUESTIONS:
    check(q.lower() in readme.lower(), f"README: missing answer/heading for '{q}'")

# 5. LICENSE is MIT
lic = read("LICENSE")
check("MIT License" in lic and "Permission is hereby granted" in lic, "LICENSE: not MIT text")

# 6. Provenance statement exists with independence claim
prov = read("PROVENANCE.md")
check("independently designed" in prov, "PROVENANCE: missing independence statement")

# 7. Self-review answers all 8 questions
review = read("docs/self-review.md")
review_qs = re.findall(r"^## \d\.", review, re.M)
check(len(review_qs) >= 8, f"self-review: expected 8 numbered questions, found {len(review_qs)}")

# 7a2. v0.2.6 (F12): the shipped Python must parse and import — a validator
# that only checks file existence would happily bless a syntactically broken gate
import ast as _ast
import importlib.util as _ilu
for rel in ["tests/scope_gate.py", "tests/validate_package.py"]:
    src = read(rel)
    try:
        _ast.parse(src)
    except SyntaxError as e:
        check(False, f"{rel}: syntax error — {e}")
        continue
    if rel.endswith("scope_gate.py"):
        try:
            _spec = _ilu.spec_from_file_location("scope_gate_check", ROOT / rel)
            _mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            for fn in ("parse_task_yaml", "normalize", "covered_by",
                       "changed_paths", "run_gate", "main"):
                check(hasattr(_mod, fn), f"{rel}: missing required function {fn}()")
        except Exception as e:
            check(False, f"{rel}: import failed — {type(e).__name__}: {e}")

# 7b. v0.2.2: packaging hygiene — no unexpected top-level entries, no empty dirs
EXPECTED_TOP = {"README.md", "LICENSE", "CHANGELOG.md", "PROVENANCE.md",
                "agent", "icm", "tests", "examples", "docs"}
for entry in ROOT.iterdir():
    if entry.name.startswith("."):
        continue  # VCS/editor metadata is out of packaging scope
    check(entry.name in EXPECTED_TOP,
          f"packaging: unexpected top-level entry '{entry.name}'")
for d in ROOT.rglob("*"):
    if not d.is_dir():
        continue
    rel_parts = d.relative_to(ROOT).parts
    # Skip anything at or under a dot-directory (.git and friends): a real
    # clone legitimately contains empty dirs like .git/refs/tags, and VCS
    # internals are outside packaging scope.
    if any(part.startswith(".") for part in rel_parts):
        continue
    if not any(d.iterdir()):
        check(False, f"packaging: empty directory '{d.relative_to(ROOT)}'")

# 7c. v0.2.7: single-source-of-truth for the scenario inventory.
# The self-test script IS the inventory; the README must not carry a copied
# numeric count (a duplicated fact that drifted three times before this).
# The validator therefore checks the SOURCE for integrity, and the README
# for absence of the duplication:
#   (i)  markers are contiguous 1..N — catches renumbering gaps and
#        duplicates, the real hazards in a hand-numbered suite;
#   (ii) N never drops below the shipped floor — a one-way ratchet that
#        fires on deletion, never on growth, so it cannot train the author
#        to expect routine failures;
#   (iii) no numeric self-test count claim exists in the README.
SCENARIO_FLOOR = 20  # scenarios shipped as of v0.2.6; raise deliberately, never lower
selftest = read("tests/scope_gate_selftest.sh")
_markers = [int(m) for m in re.findall(r"^# (\d+)\.", selftest, re.M)]
n_scenarios = max(_markers) if _markers else 0
check(sorted(_markers) == list(range(1, n_scenarios + 1)),
      f"selftest: scenario markers are not contiguous 1..{n_scenarios} "
      f"(gaps or duplicates in numbering): {sorted(_markers)}")
check(n_scenarios >= SCENARIO_FLOOR,
      f"selftest: suite shrank below its shipped floor "
      f"({n_scenarios} < {SCENARIO_FLOOR})")
_claim = re.search(r"\b(\d+)\s+(?:scenarios?|(?:self-?test\s+)?cases?)\b",
                   read("README.md"), re.I)
check(_claim is None,
      f"README: numeric self-test count claim found ('{_claim.group(0) if _claim else ''}') — "
      f"counts live only in the self-test script; describe coverage without copying the number")

# 8. v0.2.1: stale cross-document version and control claims
# 8a. agent version must have a matching changelog entry
m = re.search(r"\*\*Version:\*\* ([\d.]+)", agent)
check(bool(m), "agent file: no version string")
if m:
    check(f"[{m.group(1)}]" in read("CHANGELOG.md"),
          f"CHANGELOG: no entry for agent version {m.group(1)} — stale version claim")

# 8b. reconciliation addenda must exist where v0.1 statements were superseded
check("Addendum" in read("icm/BRIEF.md"), "BRIEF: missing v0.2 addendum — stale design record")
check("Addendum" in read("docs/self-review.md"),
      "self-review: missing reconciliation addendum — v0.1 concerns presented as current")

# 8c. comparison framework must reference the current twelve-test suite
comp_text = read("tests/comparison-framework.md")
check("twelve" in comp_text and "eight for a full run" not in comp_text,
      "comparison-framework: stale test-count claim")

# 8d. self-authorization ban and both-lists semantics present in agent spec
check("self-authorize" in agent, "agent file: missing mechanical-scope self-authorization ban")
check("**both** lists" in agent, "agent file: missing both-lists protected-path semantics")

# Report
if failures:
    print(f"FAIL — {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("PASS — all structural checks passed.")
print(f"Checked root: {ROOT}")
sys.exit(0)
