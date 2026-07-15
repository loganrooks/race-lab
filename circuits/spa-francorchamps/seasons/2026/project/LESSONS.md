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
