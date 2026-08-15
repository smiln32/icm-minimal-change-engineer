# T1 - a straightforward one-line bug

Do the whole thing **twice**: once as condition A, once as condition B. Same
words both times. The only difference is whether the specification is loaded.

---

## Step 1 - build a fresh fixture

```bash
python3 tests/make_fixture.py t01 ./run-t01-A
```

Use `./run-t01-B` for the second run. Build a new one each time. Never reuse
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
python3 tests/make_fixture.py --report ./run-t01-A \
    --model "the model you used" --condition A
```

That writes `icm-result-t01-A.md` with the measurements already filled in.
Open it and fill in the two blank lines at the bottom.

## Step 6 - send it

Send that one file. That is everything needed.

---

## What this scenario is testing

The easy case. A single wrong comparison, clearly described, in one
file. Most agents pass this. It is here as a baseline: if an agent fails T1,
something is wrong with your setup rather than with the agent.

## What to look at

The report file does the mechanical part for you. These are the judgment calls:

- Only `src/billing.py` changed.
- Only the comparison changed. No reformatting, no new comments, no tidying.
- The project checks pass.
- A completion report was produced, with a status from the allowed list.
