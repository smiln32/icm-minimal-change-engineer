# Critical Self-Review

*Sections 1–8 below are the original v0.1.0 review, preserved unedited as a historical record. Statements in them describe v0.1 behavior; see the dated addendum at the end for what v0.2/v0.2.1 resolved and what still stands.*

A skeptical review of the v0.1.0 release, written before publication. The purpose is to state plainly where the design is weak, not to reassure.

## 1. Where could this agent still drift?

- **Stage 3 is the soft spot.** "Smallest safe and sufficient change" still requires judgment about *sufficient*, and a model inclined to over-build can justify a larger surface as "necessary for correctness." The Diff Audit catches unjustified changes only if the model audits honestly.
- **Long sessions.** Instruction adherence degrades over long contexts. A task that runs many turns risks the model reverting to default helpfulness ("I also cleaned up…"). The spec has no mid-session re-anchoring mechanism.
- **"Necessary" test creep.** Adding a test can nearly always be argued as required by acceptance criteria; the line in §10 helps but does not eliminate the argument.

## 2. Where could it accidentally assume authority?

- **Choosing between "equal-scope" implementations** (§10) is real authority; two implementations are rarely truly equal, and the choice can embed a de facto convention decision.
- **Deciding what counts as "governing context."** The agent selects which artifacts to read; selecting too narrowly is a quiet authority grab that looks like diligence.
- **BLOCKED reports that recommend options** can steer the human decision. Recommending is permitted, but a persuasive options list is soft authority.

## 3. Which rules are ambiguous?

- "Materially affects correctness" (S8) — material to whom, at what threshold? Two reasonable evaluators can disagree.
- "Meaningful changed block" in the Diff Audit — hunk? function? statement? Left undefined.
- "Relevant checks" in Stage 6 — on projects with slow or partial suites, "relevant" invites narrowing.
- The boundary between "conversation supplements artifacts" and "conversation overrides artifacts" is clear at the extremes and fuzzy when conversation fills a genuine artifact gap.

## 4. Which requirements are difficult to enforce by prompt alone?

- Prohibitions on *editing tests, decision records, governance files, and approval artifacts* — a prompt cannot prevent a write; it can only ask the model not to.
- "Read context before implementing" — ordering inside a single generation is unverifiable from the outside unless the environment logs tool calls.
- "Report actual check results" — a model can hallucinate a test run; nothing in the spec detects that.
- Diff-scope limits — nothing stops out-of-scope edits except the model's compliance.

## 5. What should eventually be enforced mechanically?

- **File-system boundaries:** read-only mounts or permission rules for `decisions/`, `approvals/`, test directories, and governance files. This converts the four hardest prompt rules into hard failures.
- **A diff gate:** a pre-handoff script that rejects any changed path outside the task's declared scope list.
- **Check attestation:** validation runs executed by a harness that captures real exit codes and output, so reported results cannot be invented.
- **Report schema validation:** the Completion/BLOCKED report checked against a schema (the pattern `tests/validate_package.py` already demonstrates for the package itself).
- **Approval states as environment state:** approval represented by artifacts the agent's credentials cannot write, making impersonation impossible rather than forbidden.

## 6. What would make this materially safer or more reliable?

The items in §5, in that order — the file-system boundary and diff gate alone would mechanically enforce the two most-violated behaviors (scope drift, artifact tampering). After that: a session re-anchoring rule (re-read the Task Contract every N tool calls), and published multi-model behavioral test results so claims rest on data instead of design intent.

## 7. Does any part merely sound rigorous without changing behavior?

Candidly, at risk:
- **Stage 2's internal restatement** — "restate internally" produces no observable artifact; a model can skip it invisibly. It would change behavior more if the contract had to be emitted.
- **The role-comparison table (§3)** — clarifying for humans; unclear it changes model behavior beyond what §4 already forbids.
- **Ordinal scales in the comparison framework** — they discipline evaluators, not the agent.
The eight-stage structure, STOP conditions, closed vocabulary, and traceability question are the parts most likely to actually alter behavior, because they demand observable outputs.

## 8. Is anything copied too closely from another framework?

The concepts — minimal change, scope control, regression prevention, PASS-vs-approval — are common engineering practice and appear across many methodologies. All prose, structure, tests, examples, and the ICM mapping were written fresh for this package; nothing was drawn from Agency Agents or any other agent repository. One inherent similarity is unavoidable: any "minimal change" agent will resemble other minimal-change agents in *goal*. The differentiation claimed here is the ICM mechanics (artifact supremacy, staged context intake, STOP-as-success, closed status vocabulary), and that claim is testable via the comparison framework rather than asserted.

---

**Reviewer's bottom line:** the specification is coherent and internally consistent, its honest weaknesses are prompt-level enforceability and mid-session drift, and its most load-bearing claims are testable rather than proven. That is an acceptable and clearly labeled state for a v0.1.0 released for community testing.

---

# v0.2 / v0.2.1 Addendum (2026-08-09)

Reconciliation of the v0.1 review against the shipped hardening.

**Resolved since v0.1:**
- *Q4/Q5/Q7 — "restate internally produces no observable artifact":* the Task Contract is now emitted visibly before implementation, in a fixed nine-field format, and compared in the Completion Report.
- *Q5 — "a diff gate" and "file-system boundaries for protected artifacts":* the deterministic Git diff scope gate ships (`tests/scope_gate.py`) with distinct protected-artifact detection and an 11-case self-test; it checks the real diff, including untracked files in `--base` mode (fixed v0.2.1).
- *Q3 — partial-completion ambiguity:* the ambiguous v0.1 partial-completion status is retired; the COMPLETE prefix is structurally reserved for fully validated work.
- *Scope self-authorization (not raised in v0.1, closed in v0.2.1):* when the gate is required, `allowed_paths` must come from the governing task artifact; the agent may not write or widen its own change surface, and `authorized_protected_paths` cannot substitute for allowance.

**Still standing — the honest remainder:**
- Long-session drift and mid-task re-anchoring (Q1) — no mechanism yet.
- Hallucinated check results (Q4) — reported validation output is still model-asserted; harness-captured output remains future work (roadmap item 5).
- In-generation ordering (Q4) — "context read before implementation" is still unverifiable without environment-level tool logging.
- Ambiguity thresholds (Q3): "materially affects correctness" and "meaningful changed block" remain judgment terms.
- Filesystem permissions, approval-write restrictions, task-schema validation, and signed approvals — documented in `docs/enforcement-roadmap.md`, deliberately unimplemented.

**Reviewer's bottom line, updated:** v0.2/v0.2.1 moved the two most-violated behaviors (scope drift, protected-artifact tampering) from instruction-level to mechanically checkable, and closed an authorization-bypass in its own gate. Everything the gate does not see is still trust in the model, and is labeled as such.
