---
schema: race-lab-project-lessons/v1
initiative: spa-2026-calibration
---

# Lessons and Guardrails

## L-001 — Active — Continuity must be reconstructed from evidence

**Friction:** A prior status answer initially understated cross-project continuity and later relied on stale conversational state.

**Systemic cause:** Project memory and chat history were treated as sufficient evidence of current repository state.

**Consequence:** The user had to provide a prior message and execution trace to establish what had actually happened.

**Guardrail:** At session start, read project records and inspect repository/PR state before answering status questions or acting.

**Enforcement:** `project/README.md`, `AGENTS.md`, and diff-coupled updates in `verify_project_control.py`.

**Evidence of effectiveness:** pending future session use.

## L-002 — Active — Local, committed, pushed, reviewed, and CI states are not interchangeable

**Friction:** Locally performed work and reported verification were easy to mistake for published or CI-confirmed work.

**Systemic cause:** State claims lacked an explicit evidence vocabulary.

**Consequence:** A PR comment claimed GitHub Actions success that could not later be retrieved.

**Guardrail:** Label important claims using the evidence vocabulary and require direct workflow evidence for `CI-confirmed`.

**Enforcement:** maintenance README, status schema, activity-entry verification fields, and review during session closeout.

**Evidence of effectiveness:** `STATUS.md` now records the prior Actions claim as `reported but unverified`.

## L-003 — Active — Partial procedural loops must be explicit

**Friction:** The reaction sweep stopped after five comments without a durable partial-state record.

**Systemic cause:** Procedural counts were not first-class project state.

**Consequence:** Later sessions had to inspect reactions one comment at a time to reconstruct progress.

**Guardrail:** Record exact totals and completed counts for every multi-item sweep before handoff.

**Enforcement:** required status counters and validator bounds checks.

**Evidence of effectiveness:** current status records 5/23 original comments rated and 0/12 fresh comments rated.

## L-004 — Active — “Addressed” must not collapse distinct PR actions

**Friction:** All original threads were resolved, but most comments were unrated and none had inline replies.

**Systemic cause:** Artifact changes, reactions, replies, and resolutions were treated as one outcome.

**Consequence:** The user’s explicit PR-hygiene request was only partially completed.

**Guardrail:** Track six review actions independently and make all applicable actions part of closeout criteria.

**Enforcement:** `D-005`, status counters, activity records, and closeout tasks `PR-01` through `PR-03`.

**Evidence of effectiveness:** pending completion of the second reconciliation pass.

## L-005 — Active — Interface changes require horizontal review

**Friction:** The reconciled plans still contained mismatched signatures, omitted fields, invalid fixtures, and inconsistent release predicates.

**Systemic cause:** Plans were revised vertically by file rather than horizontally across producers and consumers.

**Consequence:** A fresh review found twelve concrete contradictions after a large reconciliation.

**Guardrail:** Before publication, search every producer and consumer across data, model, artifact, CLI, generator, browser, tests, and documentation.

**Enforcement:** closeout task `VERIFY-01`; future targeted static checks may be added only when stable and non-brittle.

**Evidence of effectiveness:** pending the next corrected head.

## L-006 — Active — Verification claims require retrievable evidence

**Friction:** A prior record asserted remote Actions verification without a workflow result available to later inspection.

**Systemic cause:** Reported success was copied into project state without preserving a run identifier or equivalent evidence.

**Consequence:** CI status became ambiguous.

**Guardrail:** Record workflow run ID, URL/reference, head SHA, conclusion, and observation time before using `CI-confirmed`.

**Enforcement:** evidence vocabulary, activity template, and GitHub Actions workflow added by `CTRL-02`.

**Evidence of effectiveness:** the current state refuses to claim CI confirmation for `1ffaf2d`.

## L-007 — Active — Final review should run only on a stable publication unit

**Friction:** Review and procedural cleanup can interleave, causing repeated findings and incomplete reaction/reply work.

**Systemic cause:** No explicit gate separated local reconciliation, publication, PR hygiene, and final review request.

**Consequence:** The initiative accumulated a new review batch before the previous action sweep was fully complete.

**Guardrail:** Publish one coherent corrected head, complete applicable PR actions, then request exactly one fresh review.

**Enforcement:** closeout tasks `VERIFY-02`, `PR-01`, `PR-02`, and `PR-03`.

**Evidence of effectiveness:** pending the second reconciliation pass.

## L-008 — Active — Refresh the full review inventory immediately before closeout

**Friction:** A twelve-thread snapshot was treated as the complete fresh review set, but eleven later Codex comments already existed by the time PR actions began.

**Systemic cause:** Review state was refreshed before plan correction but not again immediately before reaction/reply/resolution work.

**Consequence:** The first closeout pass would have falsely reported all fresh findings handled while a second unresolved batch remained.

**Guardrail:** Re-list every inline thread and export the numeric comment map immediately before PR actions; update totals and task IDs before closing anything.

**Enforcement:** `PR-01` and `PR-02` require a same-head thread refresh; `STATUS.md` counters must match the refreshed inventory.

**Evidence of effectiveness:** this session stopped the action sweep, added FOLLOWUP-01 through FOLLOWUP-11, and corrected the additional batch before resolution.

## L-009 — Active — Connector-only mutation is not executable integration

**Friction:** Remote text writes can look complete without an extracted workspace, RED/GREEN evidence, executable validation, or a coherent multi-file tree.

**Systemic cause:** Repository mutation capability was conflated with an executable development environment.

**Consequence:** Plausible remote replacements could have bypassed integration and truncation checks.

**Guardrail:** Code and controls changes require an executable local workspace plus connector-backed remote state; stop before publication when either is absent.

**Enforcement:** maintenance rules, capability gate, canonical verification, and exact blob/tree readback.

**Evidence of effectiveness:** this reconstruction performed the controls RED/GREEN cycle and local verification before preparing a new publication candidate.

## L-010 — Active — Full-file worker rewrites require independent truncation checks

**Friction:** The data worker reported success while its file deleted 2,132 lines from the complete plan.

**Systemic cause:** Worker self-report was treated as potential evidence without comparing the exact base, complete result, and diff statistics.

**Consequence:** Direct integration would have destroyed most of the authoritative plan.

**Guardrail:** Compare byte count, line count, diff statistics, complete content, and affected interfaces for every worker full-file rewrite; a dramatic unexplained collapse blocks integration.

**Enforcement:** maintenance rules, closeout publication gates, and explicit rejection of data commit `e205f171ab95700a4f26708d46aa3431ed0b175d` as a file source.

**Evidence of effectiveness:** the complete 91 KB data plan was patched in place and remains larger than the base.

## L-011 — Active — Verify workspace identity before declaring work lost

**Friction:** A shallow filesystem check led to an incorrect claim that the prior workspace had disappeared.

**Systemic cause:** A familiar parent path was inspected without verifying the exact repository root, `.git`, branch, commit, and file inventory.

**Consequence:** An unnecessary reconstruction path was started and the user had to challenge the state report.

**Guardrail:** Before declaring a workspace present or lost, resolve the exact path, require `.git`, read `git status`, `HEAD`, branch/worktree identity, and enumerate the expected files.

**Enforcement:** start-of-session recovery procedure and activity evidence requirements.

**Evidence of effectiveness:** the deeper preserved workspace was subsequently found and used to recover authoritative status, activity, and ledger records.

## L-012 — Active — Temporary branches require immediate reconciliation

**Friction:** Repeated automation and worker attempts accumulated thirteen branches and obscured which branch owned PR #1.

**Systemic cause:** Temporary refs were created as transport and execution mechanisms without a cleanup gate.

**Consequence:** Publication state became difficult to inspect and user trust declined.

**Guardrail:** No new temporary branch when an existing controlled ref can serve; archive evidence before deletion; after a bounded task retain only `main`, the active PR branch, and at most one named evidence archive.

**Enforcement:** branch inventory and cleanup before further publication.

**Evidence of effectiveness:** eleven stale automation/worker refs were removed after the three worker tips were preserved in archive commit `b105df73de22059161959673d110e31cb2177daa`.


## L-013 — Cross-snippet producer/consumer parity requires executable horizontal contracts

**Friction:** repeated review passes corrected one side of interfaces while stale consumers, fixtures, defaults, or manifest examples remained elsewhere in the planning package. Syntax and project-control checks stayed green because each snippet was individually parseable.

**Systemic cause:** verification emphasized local snippet validity and record consistency rather than executable parity across every producer, adapter, consumer, fixture, validator, and CLI/browser boundary sharing an interface.

**Consequence:** nullable outcomes, profile identity, attempt evidence, report checks, chronology, geometry provenance, and manifest arguments remained inconsistent and blocked safe merge after a nominal final review.

**Enforceable guardrail:** every review correction must name its producer/consumer chain and add a focused cross-contract assertion or fixture that fails when either side drifts. The pre-publication audit must enumerate every touched interface and verify all producers and consumers together.

**Check:** the `POSTFINAL-01` through `POSTFINAL-13` reconciliation ledger records each chain; the independent cross-contract audit and fenced-snippet sweep are mandatory publication gates.
