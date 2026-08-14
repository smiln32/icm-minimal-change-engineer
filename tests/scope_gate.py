#!/usr/bin/env python3
"""Deterministic diff-scope gate for ICM tasks.

Compares the ACTUAL Git diff against a task's declared authorized paths.
It does not rely on any model's description of what it changed, it does not
fix or revert anything, and it is runnable independently of any AI agent.

Task definition (YAML — SUPPORTED SUBSET ONLY, see below):

    allowed_paths:
      - src/example.py
      - tests/example_test.py
    protected_paths:
      - approvals/
      - decisions/approved/
    authorized_protected_paths: []

Supported YAML subset (parsed by a built-in dependency-free parser):
  * top-level keys followed by "- item" list entries;
  * inline empty lists ("key: []") and inline single values ("key: path");
  * "#" comments and single/double-quoted items.
NOT supported: nested maps, multi-line values, flow sequences ([a, b]),
anchors/aliases, and any other general-YAML feature. One deviation from
YAML: a '#' preceded by whitespace starts a comment even inside a quoted
item, so paths containing " #" cannot be expressed; '#' with no preceding
whitespace (src/app#old.py) is preserved as data. Keep task files simple;
Duplicate tracked keys follow YAML semantics (last occurrence wins), and an
inline value or [] closes its key, so later stray "- item" lines cannot
leak into it. Structurally malformed input — an indented tracked key, or
bare top-level content that is neither a key nor a list item — is rejected
with exit 3 rather than silently ignored.

Semantics:
  * Added, modified, renamed, deleted, and untracked files all count as changes.
  * A changed path is in scope if it equals an allowed path or lies under an
    allowed directory (entries ending in "/" or matching a prefix directory).
  * Every changed path must match allowed_paths — with no exception.
    authorized_protected_paths never substitutes for allowed_paths.
  * A changed path matching protected_paths must ADDITIONALLY be listed in
    authorized_protected_paths, or it is a PROTECTED-ARTIFACT violation.
    Touching a protected path therefore requires the path in BOTH lists.
  * Membership in allowed_paths alone does NOT authorize a protected path,
    and membership in authorized_protected_paths alone does NOT place a
    path in scope.
  * Rename counts both the old and new path as changed.
  * If the diff touches any .gitignore, ignored-untracked files join the
    changed set (closes the hide-files-by-editing-ignore-rules bypass;
    pre-existing ignored artifacts will surface in that case by design).
  * Paths use forward slashes on all platforms; backslash is filename data.
  * The allowed_paths entry "." grants the whole repository; protected_paths
    rules still apply on top of it.
  * Matching is case-sensitive by design (case-folding would widen scope on
    case-sensitive systems); a scope FAIL that would match ignoring case
    carries a casing hint.
  * Default mode (no --base) audits working tree + index vs HEAD ONLY —
    it cannot see work already committed. A PASS in default mode carries an
    explicit note to that effect; audit committed work with --base.
  * The task file itself is checked for tampering before scope is evaluated.
    allowed_paths is the authorization for the whole audit, so an agent that
    can edit the task file can authorize itself; if the task file lies inside
    the repository and appears in the diff, the gate refuses to certify
    anything (exit 4) instead of auditing against declarations the change
    under audit may have written. A task file OUTSIDE the repository is not
    diff-visible and therefore cannot be integrity-checked — a PASS says so.

Usage:
    python3 scope_gate.py --task TASK.yaml [--repo DIR] [--base REF]

  --base REF   compare REF...working tree (committed + uncommitted + untracked).
               Without --base, the working tree + index vs HEAD is used.

Exit codes:
    0  PASS  — all changed files within authorized scope
    1  FAIL  — changed files outside authorized scope
    2  FAIL  — protected artifact modified (takes precedence over exit 1)
    3  error — bad usage, unreadable task file, or git failure
    4  FAIL  — task file itself changed; declarations untrusted, scope NOT
               audited (takes precedence over every other result)
"""

import argparse
import os
import posixpath
import subprocess
import sys


# ---------------------------------------------------------------- task parsing

def _strip_comment(raw):
    """Remove a trailing comment per the YAML rule: '#' starts a comment only
    at line start or when preceded by whitespace. A '#' embedded in a path
    (src/app#old.py) is data, not a comment. Note: this rule applies even
    inside quoted items — see the supported-subset docs."""
    for idx, ch in enumerate(raw):
        if ch == "#" and (idx == 0 or raw[idx - 1] in " \t"):
            return raw[:idx]
    return raw


def parse_task_yaml(text):
    """Parse the minimal 'key:' + '- item' YAML subset used by task files.

    Deliberately dependency-free so the gate runs anywhere Python runs.
    Ignores keys it does not recognize. Inline empty lists ('key: []') and
    comments are supported.
    """
    keys = {"allowed_paths", "protected_paths", "authorized_protected_paths"}
    out = {k: [] for k in keys}
    current = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if not line.startswith((" ", "\t", "-")):
            if ":" not in stripped:
                raise ValueError(
                    f"line {lineno}: unrecognized top-level content "
                    f"{stripped!r} — not a key, not a list item")
            key, _, rest = stripped.partition(":")
            key = key.strip()
            if key in keys:
                out[key] = []          # duplicate key: last occurrence wins
                rest = rest.strip()
                if rest and rest != "[]":
                    out[key].append(rest.strip("'\""))
                    current = None     # inline value closes the key
                elif rest == "[]":
                    current = None     # inline empty list closes the key
                else:
                    current = key      # bare key: list items follow
            else:
                current = None         # untracked key closes any open list
        elif stripped.startswith("- "):
            if current:
                out[current].append(stripped[2:].strip().strip("'\""))
            else:
                # Fail closed: a dangling list item silently dropped could
                # mean silently-unprotected paths (e.g. items written after
                # "protected_paths: []"). Only a bare tracked key may open
                # a list block in this subset.
                raise ValueError(
                    f"line {lineno}: list item {stripped!r} does not belong "
                    f"to an open tracked key — a preceding inline value or "
                    f"[] closes its key, and only bare tracked keys open "
                    f"list blocks")
        else:
            # indented content that is not a list item: reject indented
            # tracked keys loudly instead of silently ignoring them
            head = stripped.partition(":")[0].strip()
            if head in keys:
                raise ValueError(
                    f"line {lineno}: key {head!r} is indented — tracked keys "
                    f"must start at column 0 (see supported YAML subset)")
    return out


# ---------------------------------------------------------------- path matching

def normalize(p):
    """Normalize a repo-relative path for matching.

    - strips surrounding whitespace and ONE literal leading "./" prefix
      (never lstrip("./"), which strips characters and would silently turn
      "../etc" into "etc");
    - collapses "." and ".." components via posixpath.normpath, so
      "src/../foo" == "foo" and "./src/./bar" == "src/bar";
    - preserves a leading ".." (a parent-escaping path stays visibly
      parent-escaping and will not match any in-repo allow entry);
    - treats "/" as the ONLY separator: a backslash is ordinary filename
      data on POSIX and is preserved, never translated. Git emits
      forward-slash paths on every platform, and task files must use
      forward slashes too.
    """
    p = p.strip()
    if p.startswith("./"):
        p = p[2:] or "."
    return posixpath.normpath(p) if p else p


def covered_by(path, entry):
    """True if `path` equals entry, or lies under entry treated as a directory.
    The entry "." means the whole repository (protected_paths rules still
    apply on top of a whole-repo allowance)."""
    path_n = normalize(path)
    entry_n = normalize(entry)
    if entry_n == ".":
        return True
    if path_n == entry_n:
        return True
    return path_n.startswith(entry_n + "/")


def match_any(path, entries):
    return any(covered_by(path, e) for e in entries)


# ---------------------------------------------------------------- git

def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def changed_paths(repo, base=None):
    """Every added/modified/renamed/deleted/untracked path, as a sorted set.

    All git output is read NUL-terminated (-z), so filenames containing
    spaces, quotes, or non-ASCII arrive raw — no C-style quote handling
    is needed and none is attempted.

    -z record layouts (they differ from text mode):
      * diff --name-status -z:  STATUS \\0 path \\0        (one path)
                                R###/C### \\0 old \\0 new \\0 (two paths)
      * status --porcelain=v1 -z: "XY path" \\0            (one path)
                                  "XY new" \\0 old \\0      (renames/copies:
                                  NEW path first, then original)
      * ls-files -z: path \\0
    """
    paths = set()
    if base:
        out = git(repo, "diff", "--name-status", "-z", "-M", base)
        tokens = [t for t in out.split("\0") if t != ""]
        i = 0
        while i < len(tokens):
            status = tokens[i]
            if status[:1] in ("R", "C"):
                if i + 2 >= len(tokens):
                    raise RuntimeError(
                        "malformed 'git diff -z' output: truncated rename record")
                paths.add(tokens[i + 1])   # old path
                paths.add(tokens[i + 2])   # new path
                i += 3
            else:
                if i + 1 >= len(tokens):
                    raise RuntimeError(
                        "malformed 'git diff -z' output: status token without path")
                paths.add(tokens[i + 1])
                i += 2
        # git diff reports tracked files only; untracked files are still
        # changes to the working tree and must not escape the gate.
        untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
        for tok in untracked.split("\0"):
            if tok:
                paths.add(tok)
    else:
        out = git(repo, "status", "--porcelain=v1", "-z", "-uall")
        tokens = out.split("\0")
        i = 0
        while i < len(tokens):
            entry = tokens[i]
            if not entry:
                i += 1
                continue
            xy, path = entry[:2], entry[3:]
            paths.add(path)
            if "R" in xy or "C" in xy:
                # next NUL token is the ORIGINAL path of the rename/copy.
                # Silently tolerating truncation here would DROP a changed
                # path — a fail-open. Error instead.
                if i + 1 >= len(tokens) or not tokens[i + 1]:
                    raise RuntimeError(
                        "malformed 'git status -z' output: rename record "
                        "missing original path")
                paths.add(tokens[i + 1])
                i += 2
            else:
                i += 1
    paths.discard("")
    return sorted(paths)


# ---------------------------------------------------------------- gate

def ignored_untracked(repo):
    """Untracked files currently excluded by ignore rules."""
    out = git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    return {t for t in out.split("\0") if t}


def task_repo_path(repo, task_path):
    """The task file's repo-relative path, or None if it is not inside `repo`.

    A task file outside the repository never appears in the diff, so its
    integrity cannot be checked here; None means "not diff-verifiable",
    not "verified clean".

    Both sides are resolved through realpath: where the repo is reached via a
    symlink (macOS /tmp -> /private/tmp is the common case), comparing
    unresolved paths makes an in-repo task file look external and silently
    skips the check on the platforms most likely to hit it.
    """
    try:
        rel = os.path.relpath(os.path.realpath(task_path),
                              os.path.realpath(repo))
    except ValueError:
        return None                      # different drive on Windows
    rel = rel.replace("\\", "/")
    if rel == ".." or rel.startswith("../"):
        return None
    return normalize(rel)


def run_gate(repo, task, base=None, task_path=None):
    """Returns (exit_code, report_text).

    `task_path` is the path the declarations were read from. Pass it: the
    gate's premise is that it trusts the diff rather than the agent, and
    allowed_paths is an authorization the agent can rewrite if the task file
    is inside the repository. Omitting it leaves that check unperformed, and
    a resulting PASS says so rather than implying it was checked.
    """
    changed = changed_paths(repo, base)
    # F5 bypass closure: untracked detection honors .gitignore, so a task
    # that edits ignore rules could hide new out-of-scope files. Rule: if
    # this diff touches ANY .gitignore, ignored-untracked files join the
    # changed set and face allowed_paths like every other change. Tradeoff:
    # pre-existing ignored artifacts surface whenever ignore rules change —
    # deliberate; editing ignore rules widens scrutiny. (.git/info/exclude
    # and core.excludesFile live outside the diffable tree and remain out
    # of this gate's reach; see docs/enforcement-roadmap.md.)
    if any(posixpath.basename(normalize(c)) == ".gitignore" for c in changed):
        changed = sorted(set(changed) | ignored_untracked(repo))

    # Self-authorization check, before any scope evaluation. Every other
    # result in this function is computed FROM the task file, so if the task
    # file is part of the change under audit, no result computed from it can
    # be trusted — a widened allowed_paths produces a PASS that means nothing.
    # Refuse to certify rather than report a scope verdict derived from
    # declarations the audited work may have written (agent spec: "never
    # write, widen, or infer allowed_paths"; BRIEF B13).
    rel_task = task_repo_path(repo, task_path) if task_path is not None else None
    if rel_task is not None and any(normalize(c) == rel_task for c in changed):
        return 4, (
            "FAIL — task file changed during the audited work:\n"
            "\n"
            f"{rel_task}\n"
            "\n"
            "The task file declares the scope this gate enforces, so a task "
            "file created or modified inside the audited diff can authorize "
            "the very change being audited. Scope was NOT evaluated and "
            "nothing here is certified.\n"
            "\n"
            "Resolve by restoring the task file to its governing version "
            "(the agent must never write or widen its own declarations), or "
            "— if a human deliberately amended the task — commit the "
            "amendment and re-run with --base set to that commit, so the "
            "audit baseline includes the approved declarations."
        )

    allowed = task["allowed_paths"]
    protected = task["protected_paths"]
    authorized_protected = task["authorized_protected_paths"]

    # Authorization semantics:
    #   1. EVERY changed path must match allowed_paths. No other list can
    #      substitute for this — authorized_protected_paths grants nothing
    #      by itself.
    #   2. A changed path matching protected_paths must ADDITIONALLY match
    #      authorized_protected_paths.
    # A path can violate both rules; protected violations dominate the exit code.
    # A path can violate both rules; it is reported ONCE, under the graver
    # protected classification (which also dominates the exit code), with an
    # annotation when it additionally falls outside allowed_paths.
    # scope_violations stays pure paths (the casing-hint pass depends on it).
    protected_violations = []
    scope_violations = []
    for p in changed:
        in_allowed = match_any(p, allowed)
        is_protected = match_any(p, protected)
        in_authorized = match_any(p, authorized_protected)
        if is_protected and not in_authorized:
            protected_violations.append(
                p if in_allowed else f"{p}  (also outside authorized scope)")
        elif not in_allowed:
            scope_violations.append(p)

    # Matching is case-sensitive by design: case-insensitive matching would
    # silently WIDEN scope on case-sensitive filesystems. But on
    # case-insensitive filesystems a casing mismatch between the task file
    # and git's reported path produces a confusing violation — so scope
    # failures that would match allowed_paths ignoring case get a hint.
    case_hints = [
        p for p in scope_violations
        if any(covered_by(normalize(p).lower(), normalize(e).lower())
               for e in allowed)
    ]

    lines = []
    if protected_violations:
        lines.append("FAIL — protected artifact modified:")
        lines.append("")
        lines.extend(protected_violations)
        if scope_violations:
            lines.append("")
    if scope_violations:
        lines.append("FAIL — changed files outside authorized scope:")
        lines.append("")
        lines.extend(scope_violations)
        for h in case_hints:
            lines.append("")
            lines.append(f"note — '{h}' differs from an allowed path only by "
                         f"letter case; matching is case-sensitive, check the "
                         f"task declaration's casing")

    if protected_violations:
        return 2, "\n".join(lines)
    if scope_violations:
        return 1, "\n".join(lines)
    pass_text = "PASS — all changed files are within authorized scope"
    if base is None:
        pass_text += ("\nnote — default mode audits uncommitted work only "
                      "(working tree + index vs HEAD); if changes were "
                      "committed during the task, re-run with --base <pre-task ref>")
    # Announce an unperformed integrity check rather than letting a bare PASS
    # imply the declarations were verified (same principle as the note above).
    if task_path is None:
        pass_text += ("\nnote — task-file integrity was not checked (no task "
                      "path supplied to the gate); declarations are assumed "
                      "unmodified")
    elif rel_task is None:
        pass_text += ("\nnote — the task file lies outside the repository, so "
                      "its integrity is not diff-verifiable here; this PASS "
                      "assumes the declarations it was read from are the "
                      "governing ones")
    return 0, pass_text


class GateArgumentParser(argparse.ArgumentParser):
    """argparse exits 2 on usage errors by default, which collides with this
    gate's documented exit 2 (protected-artifact violation). A CI wrapper
    keying on exit codes would read a typo'd flag as protected tampering.
    Route all usage errors to the contracted exit 3 instead."""

    def error(self, message):
        print(f"error — {message}", file=sys.stderr)
        sys.exit(3)


def main():
    ap = GateArgumentParser(description="ICM deterministic diff-scope gate")
    ap.add_argument("--task", required=True, help="task definition YAML file")
    ap.add_argument("--repo", default=".", help="git repository root (default: .)")
    ap.add_argument("--base", default=None,
                    help="git ref to diff against (default: working tree vs HEAD)")
    args = ap.parse_args()

    try:
        with open(args.task, encoding="utf-8") as f:
            task = parse_task_yaml(f.read())
    except OSError as e:
        print(f"error — cannot read task file: {e}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"error — malformed task file: {e}", file=sys.stderr)
        return 3

    if not task["allowed_paths"]:
        print("error — task file declares no allowed_paths; the gate cannot "
              "evaluate scope without a declared change surface", file=sys.stderr)
        return 3

    try:
        code, report = run_gate(args.repo, task, args.base, task_path=args.task)
    except RuntimeError as e:
        print(f"error — {e}", file=sys.stderr)
        return 3

    print(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
