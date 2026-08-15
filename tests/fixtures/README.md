# Evaluation fixtures

Ready-made starting repositories for the behavioral tests in
`../test-cases.md` and the A/B method in `../comparison-framework.md`.

## Why these exist

The test suite used to describe the repository state and leave building it to
each tester. Two things went wrong with that. Results from different fixtures
cannot be pooled, because a scenario's difficulty lives in the fixture, not in
the description. And the recorded runs in `../behavioral-run-results.md` used
throwaway repositories that no longer exist, so nobody can reproduce them.

Building one fixture is also harder than it looks. The first T8 fixture in
this project's own recorded run left an accidental public escape hatch, so the
agent solved the task legitimately and the run proved nothing
(`../behavioral-run-results.md`, T8 note). That was caught only because the
author knew what the scenario was supposed to prove.

## Building one

```bash
python3 tests/make_fixture.py --list        # the scenario ids
python3 tests/make_fixture.py t09           # build ./icm-fixture-t09
python3 tests/make_fixture.py t09 /tmp/run  # build somewhere specific
```

Each build produces a committed Git repository: the shared ledger project, the
scenario's own files, the task at `tasks/task.yaml`, and the scope gate at
`tools/scope_gate.py`.

Build a fresh one for every run. Reusing a dirty tree makes the scope gate
report the previous run's changes.

## Giving the task to the agent

Each scenario directory has a `PROMPT.md` written as numbered steps: build,
set up the agent, send this exact message, send this second message, generate
the report, send it. Follow it top to bottom.

## Reporting a run

```bash
python3 tests/make_fixture.py --report ./run-t09-A \
    --model "Claude Haiku 4.5" --condition A
```

This writes `icm-result-t09-A.md` with everything measurable already filled
in: the real gate exit code, the real changed-file list, whether anything was
written under `approvals/` or `decisions/` or `tasks/`, the platform, and the
package version and commit that built the fixture. Two lines are left for the
tester, because no tool reads them reliably out of a transcript: the status the
agent reported, and anything worth noting.

`--model` and `--condition` are required rather than optional. A result with
neither recorded cannot be compared with anything, and a default would let one
be produced by accident.

Send the file, or paste it into the results issue. `../results/` is where
returned files are filed.

**`PROMPT.md` is not copied into the built fixture.** It names the trap and the
evaluation criteria, so putting it where the agent can read it would hand over
the answer key. Read it yourself; give the agent only the quoted prompt.

Use identical wording in both conditions. The only difference between
Condition A and Condition B is whether
`agent/icm-minimal-change-engineer.md` is loaded as the agent definition.

## Checking the result

Check the repository, not the transcript. Several scenarios turn on whether a
file was written, and an agent's own account of that is exactly what the
scope gate exists to not rely on:

```bash
git -C <fixture> status --porcelain
git -C <fixture> diff --name-only
python3 <fixture>/tools/scope_gate.py --task tasks/task.yaml --repo <fixture>
```

## Keeping the fixtures honest

```bash
python3 tests/make_fixture.py --verify
```

Builds all of them and checks each is still the test it claims to be: the tree
is clean after commit, the gate passes on the untouched fixture *after its
checks have run*, each scenario's planted bug still makes its checks fail (or
still does not, where the scenario starts clean), and T8 still exposes no
sanctioned route to the customer override.

Run it after editing any fixture. A scenario that quietly stops testing what
it claims still produces confident results.

## Layout

- `_base/` — the shared ledger project every scenario starts from
- `t01/` … `t12b/` — per-scenario overrides, task file, and prompt

Scenarios with variants in `test-cases.md` are split into separate ids: T6
becomes `t06a` and `t06b`, T12 becomes `t12a` and `t12b`. Fourteen buildable
fixtures for twelve numbered scenarios.
