# ICM Compatibility — How This Agent Implements Intent and Context Management

**ICM (Intent and Context Management)** is a working discipline for AI-assisted projects: project intent is written down in designated artifacts; context is read before action; scope, decisions, gates, and approvals are owned by humans; agents leave evidence and stop at boundaries instead of improvising. This document maps each ICM principle to the concrete mechanism that implements it in the agent specification, so the mapping can be audited rather than taken on faith.

| # | ICM principle | Implementing mechanism in the agent spec |
|---|---------------|------------------------------------------|
| 1 | Truth lives in artifacts, not model memory | §2.1 artifact hierarchy; conversation defined as supplemental only; T3/T4 test the boundary |
| 2 | Required context is read before work | Stage 1 (Context Intake) is mandatory and first; missing context is STOP S1, not a guess; the Stage 2 Task Contract is emitted visibly before any code change |
| 3 | Scope is explicit | Stage 2 (Task Contract) fixes the boundary; tasks declare allowed_paths/protected_paths (mandatory when the gate is required — the agent may not self-authorize its change surface); Stage 7 runs the deterministic Git diff scope gate (tests/scope_gate.py) against the real diff; §4 assigns scope ownership to the human |
| 4 | Approved decisions are protected | §2.4 "a better idea is not permission"; anti-pattern "Helpful redesign"; STOP S2 for material conflicts; T4 tests it |
| 5 | Minimum change = minimum justified change | Stage 3 (Minimum Surface Analysis) plus Stage 5 (Diff Audit) traceability question: "what explicit requirement makes this change necessary?" |
| 6 | Validation ≠ approval | PASS != APPROVED stated as rule; closed status vocabulary (§8) with the COMPLETE prefix reserved for fully validated work; STOP S6; anti-pattern "Approval impersonation"; T7 and T10 test it, T10 with mechanical verification |
| 7 | Gates cannot be bypassed | §2.7 enumerated bypass prohibitions; STOP S5/S7; anti-pattern "Validation laundering"; T6 tests it |
| 8 | Failure is explicit | Eight STOP conditions with a required BLOCKED REPORT format and a specialized GOVERNING CONTEXT CONFLICT form for S2; a legitimate STOP defined as a successful outcome |
| 9 | Work leaves evidence | Output contract (§8): one Completion Report per task, seven required sections; T1 PASS criteria require it |
| 10 | Human authority remains human | §3 role table, §4 non-ownership list, §10 judgment boundaries with a default-out tie-breaker |

## What an ICM-native project provides to this agent

The agent consumes ICM artifacts; it does not create the governance layer itself.

- **CONTEXT.md** (or equivalent): standing project truth — domain rules, constraints, conventions.
- **Task definition:** what to change and what "done" means, written, per task.
- **Decision records:** settled choices the agent must not reopen.
- **Acceptance criteria / checks:** the project's own definition of validation.
- **Approval artifacts:** human-controlled; the agent reads and reports them, never writes them.

A project missing these still gets value — the workflow, diff audit, and output contract apply regardless — but the agent will stop more often, because ICM treats missing truth as a boundary rather than an invitation to guess.

## Toward an ICM specialist-agent standard

This package is intended as a first example, and it suggests a minimal shape any ICM-native specialist could share:

1. A governing-principles section that outranks role behavior.
2. A role definition with explicit non-ownership.
3. A staged workflow with context intake first and evidence last.
4. Enumerated STOP conditions with a blocked-report format.
5. A closed status vocabulary separating validation from approval.
6. Named anti-patterns the agent rejects even on request.
7. Behavioral tests targeting the role's specific failure modes.

Other specialists (e.g., an ICM Reviewer or ICM Architect) would change the role, scope, and authority sections while keeping this skeleton. Nothing here is proposed as final; it is a v0.1.0 shape offered for community iteration.
