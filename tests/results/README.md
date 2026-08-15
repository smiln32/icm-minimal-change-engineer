# Submitted results

Where returned test results are filed.

## If you ran a test

You do not need write access here. Send the `icm-result-*.md` file that
`make_fixture.py --report` produced, or paste its contents into the "Call for
A/B results" issue. Filing it here is the maintainer's job.

A pull request adding your file is welcome too, if you would rather.

## Naming

`icm-result-<scenario>-<condition>.md` is what the tool produces. Where several
results would collide, add the model and a run number:

```
icm-result-t09-A.md
icm-result-t09-A-haiku-4-5-run2.md
```

## Why results are files rather than a table

Each file records what was measured and what the run was measured against: the
package version and commit that built the fixture, the platform, the real gate
exit code, and the real changed-file list. A summary table would lose all of
that on the way in, and a result you cannot trace back to a fixture version is
a result you cannot check later.

The project's own recorded runs (`../behavioral-run-results.md`,
`../comparison-run-results.md`) were written before the fixtures were
committed, so their fixtures no longer exist and nobody can reproduce them.
That is the mistake this directory exists to avoid repeating.

## What to do with them

Read individually first. Pool only across results that share a scenario, a
condition, and a model. Different models behave differently enough that
combining them hides the finding rather than strengthening it: Sonnet 5 held at
72 of 72 compliant in both conditions, while Haiku 4.5 broke a module boundary
in 2 of 3 runs *with* the specification loaded.
