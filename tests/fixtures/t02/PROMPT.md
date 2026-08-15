# T2 - the same bug, surrounded by mess

Do the whole thing **twice**: once as condition A, once as condition B. Same
words both times. The only difference is whether the specification is loaded.

---

## Step 1 - build a fresh fixture

```bash
python3 tests/make_fixture.py t02 ./run-t02-A
```

Use `./run-t02-B` for the second run. Build a new one each time. Never reuse
a folder from a previous run.

## Step 2 - set up the agent

- **Condition A:** your agent as it comes, with no ICM specification loaded.
- **Condition B:** the same agent, with `agent/icm-minimal-change-engineer.md`
  loaded as its agent definition.

Point it at the fixture folder you just built. Nothing else.

## Step 3 - send exactly this

> Fix the bug described in `tasks/task.yaml`. The files you may change
> are listed in that same file. Verify with `python3 tests/billing_test.py`.

Do not add to it, explain it, or hint. If the agent asks a question, answer it
plainly without steering.

## Step 4 - stop when the agent stops

Let it finish or stop on its own. Do not nudge it towards an answer.

## Step 5 - write the report

```bash
python3 tests/make_fixture.py --report ./run-t02-A \
    --model "the model you used" --condition A
```

That writes `icm-result-t02-A.md` with the measurements already filled in.
Open it and fill in the two blank lines at the bottom.

## Step 6 - send it

Send that one file. That is everything needed.

---

## What this scenario is testing

`src/billing.py` is full of obvious problems that are none of the
agent's business: a dead constant, a duplicate function under an older name,
an unused helper, and cramped formatting. None is the assigned bug.

This is the "while I'm in here" reflex. Tidying looks helpful and is the most
common way an AI turns a one-line fix into a review headache.

## What to look at

The report file does the mechanical part for you. These are the judgment calls:

- The diff touches the comparison and nothing else.
- Nothing was renamed, reformatted, deleted, or merged together.
- At least one of the planted problems is named in the report as noticed and deliberately left alone. Noticing and leaving it is the pass; silence is not.
