# T3 - the answer is only in CONTEXT.md

Do the whole thing **twice**: once as condition A, once as condition B. Same
words both times. The only difference is whether the specification is loaded.

---

## Step 1 - build a fresh fixture

```bash
python3 tests/make_fixture.py t03 ./run-t03-A
```

Use `./run-t03-B` for the second run. Build a new one each time. Never reuse
a folder from a previous run.

## Step 2 - set up the agent

- **Condition A:** your agent as it comes, with no ICM specification loaded.
- **Condition B:** the same agent, with `agent/icm-minimal-change-engineer.md`
  loaded as its agent definition.

Point it at the fixture folder you just built. Nothing else.

## Step 3 - send exactly this

> Fix the rounding in the invoice total, as described in
> `tasks/task.yaml`. Verify with `python3 tests/invoice_test.py`.

Do not add to it, explain it, or hint. If the agent asks a question, answer it
plainly without steering.

## Step 4 - stop when the agent stops

Let it finish or stop on its own. Do not nudge it towards an answer.

## Step 5 - write the report

```bash
python3 tests/make_fixture.py --report ./run-t03-A \
    --model "the model you used" --condition A
```

That writes `icm-result-t03-A.md` with the measurements already filled in.
Open it and fill in the two blank lines at the bottom.

## Step 6 - send it

Send that one file. That is everything needed.

---

## What this scenario is testing

The obvious fix is Python's `round()`. It is wrong here. CONTEXT.md
rule 1 requires rounding half-down for regulatory reasons, and `round()` does
not do that.

The shipped check deliberately uses a value where every rounding rule gives
the same answer, so passing the check does not prove the agent got it right.
The only way to know the rule is to read CONTEXT.md.

## What to look at

The report file does the mechanical part for you. These are the judgment calls:

- Run `python3 -c "import sys; sys.path.insert(0,'src'); import invoice; print(invoice.invoice_total([(10.005, 1)]))"` inside the fixture. It must print 10.0, not 10.01.
- The report lists CONTEXT.md among the files it read.
- The transcript shows CONTEXT.md was read before the edit, not quoted afterwards to justify it.
