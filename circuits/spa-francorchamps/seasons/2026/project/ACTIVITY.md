---
schema: race-lab-project-activity/v1
initiative: spa-2026-calibration
mutation: append-only
---

# Activity History

## A-001 — 2026-07-15T15:38:52Z — Initial Codex review inventory

**Evidence status:** remotely-observed; reconstructed from PR review records.

**Starting state:** PR #1 contained the migrated Spa 2026 calibration specification and four implementation plans.

**Work performed:** Codex reviewed the initial plan package and identified a moved-path issue plus an initial batch of inline technical findings.

**Files changed:** none by this activity entry; this is a historical reconstruction.

**Verification:** review submissions and inline threads were read from GitHub.

**Publication / remote actions:** review comments were published by the Codex connector.

**Result:** review findings became inputs to the first reconciliation pass.

**Next action:** reconcile independent-review requirements and all deduplicated Codex findings before publishing another head.

**Lessons review:** historical reconstruction; lessons are recorded in `LESSONS.md`.

## A-002 — 2026-07-15T20:24:47Z — First plan reconciliation and fresh review

**Evidence status:** committed; pushed; remotely-observed; reviewed.

**Starting state:** reviewed head `0f6778b1c913e6648f18f80bae8a7fb74da9a848`; six mandatory independent-review resolutions and 23 inline findings inventoried.

**Work performed:** revised all four plans, created the reconciliation ledger, corrected the canonical verification scope, published commit `1ffaf2d232f6bafd134fafa94ca067683744b639`, resolved all 23 original inline threads, and requested a fresh Codex review.

**Files changed:** four Spa calibration plans, `2026-07-15-plan-reconciliation.md`, and `scripts/verify.sh`.

**Verification:** local verifier output was reported as passing in the attached execution trace. A retrievable CI run was not found during later inspection.

**Publication / remote actions:** commit pushed; original threads resolved; fresh `@codex review` requested. Reaction sweep stopped after 5 of 23 original comments; no inline replies were posted.

**Result:** fresh Codex review opened twelve unresolved findings against `1ffaf2d`.

**Next action:** evaluate the twelve fresh findings as a bounded second reconciliation pass.

**Lessons review:** new lessons recorded as `L-001` through `L-007`.

## A-003 — 2026-07-15T22:12:44Z — Project-control system design approved

**Evidence status:** user-approved; local-work-in-progress.

**Starting state:** no repository-backed `STATUS.md`, append-only activity history, decision register, lesson register, or automated freshness enforcement existed for the Spa initiative.

**Work performed:** approved a project-control design consisting of a maintenance README, status, activity, decisions, lessons, an executable PR #1 closeout plan, repository instructions, a project-control validator, tests, and a GitHub Actions verification workflow.

**Files changed:** project-control files and enforcement files were prepared in one publication unit.

**Verification:** targeted test-first verification and canonical verifier integration were pending at the time of this entry.

**Publication / remote actions:** none at that point; the authoritative PR head remained `1ffaf2d`.

**Result:** implementation of the approved control layer was authorized.

**Next action:** write failing validator tests, implement the validator, run targeted and canonical checks, then publish the coherent unit.

**Lessons review:** no-new-lesson; existing lessons already cover the continuity and enforcement failures that motivated this work.

## A-004 — 2026-07-15T22:25:42Z — Project-control layer verified and published

**Evidence status:** locally-verified; committed; pushed after the PR branch ref update; remote readback pending.

**Starting state:** PR #1 head `1ffaf2d232f6bafd134fafa94ca067683744b639`; twelve unresolved fresh Codex findings; no enforced living-record system.

**Work performed:** created the closeout plan, maintenance README, status, append-only activity history, decision register, lesson register, project-control validator, eight validator tests, repository instructions, canonical verifier integration, and a GitHub Actions workflow. The validator was developed test-first: the initial test run failed because the validator module did not exist, then passed after implementation.

**Files changed:** `AGENTS.md`, `scripts/verify.sh`, `scripts/verify_project_control.py`, `tests/test_project_control.py`, `.github/workflows/verify.yml`, the Spa 2026 README, the closeout plan, and all five project-control records.

**Verification:** targeted `python3 -m unittest tests/test_project_control.py -v` passed 8/8. `python3 scripts/verify_project_control.py` passed. A reconstructed checkout ran `bash scripts/verify.sh` with Python 3.13.5, pytest 9.0.2, and Ruff 0.15.21; canonical paths, project records, shell syntax, Python compilation, Ruff, and 8 tests passed. ShellCheck was unavailable and explicitly skipped. This is local verification, not scientific model validation or CI confirmation.

**Publication / remote actions:** the verified files were built on `staging/spa-project-control-20260715`; the PR branch was advanced once to the complete staging head rather than receiving partial file states. The last material staging commit before the record files was `6bdc71ae331f9387f353589f59cfdff5ba0461d7`.

**Result:** the repository now has durable project continuity records and automated maintenance checks. The twelve fresh Codex findings remain unresolved and no production calibration functionality was implemented.

**Next action:** verify and disposition `DATA-01` against the current data-pipeline plan before editing.

**Lessons review:** no-new-lesson; enforcement implements `L-001` through `L-007`.

## A-005 — 2026-07-15T22:28:08Z — Remote readback and CI confirmation

**Evidence status:** pushed; remotely-observed; CI-confirmed for material head `1d19f234f5d7edeabfbf86ceccc88c1aac49f620`.

**Starting state:** the PR branch had been advanced to `1d19f234f5d7edeabfbf86ceccc88c1aac49f620`; the living status still recorded CI as pending.

**Work performed:** read back PR #1, confirmed its head, retrieved the associated workflow run, and synchronized the living records with the direct evidence.

**Files changed:** `project/ACTIVITY.md` and `project/STATUS.md` only.

**Verification:** GitHub Actions workflow `Verify`, run ID `29455470610`, run number 2, completed successfully for `1d19f234f5d7edeabfbf86ceccc88c1aac49f620`.

**Publication / remote actions:** record synchronization was prepared on `staging/spa-project-control-20260715` and the PR branch was advanced once to the synchronized record head.

**Result:** the project-control publication is remotely observed and CI-confirmed for the recorded material head. The twelve fresh Codex findings remain the active work.

**Next action:** verify and disposition `DATA-01` against the current data-pipeline plan before editing.

**Lessons review:** no-new-lesson; the retained workflow ID demonstrates the `L-006` evidence guardrail.

## A-006 — 2026-07-15T22:35:00Z — Second reconciliation prepared

**Evidence status:** remotely-observed starting state; local-work-in-progress.

**Starting state:** PR #1 head `76738fa1a725a0bd507011c77ec19d783dd63408`; GitHub Actions run `29455579091` passed; 23 original threads resolved with 5 reactions and no replies; twelve fresh threads unresolved with no reactions or replies. The prior status snapshot still named material head `1d19f234...`, so this entry corrects that stale observation before relying on it.

**Work performed:** verified all twelve fresh findings against the current plans and revised the data, model, browser, closeout, reconciliation, and project-status contracts as a bounded planning-only pass.

**Files changed:** three implementation plans, the closeout plan, reconciliation ledger, status, and activity history.

**Verification:** pending canonical verification in the publication workflow.

**Publication / remote actions:** none yet; reactions, replies, and fresh-thread resolutions intentionally wait for a verified pushed head.

**Result:** corrected publication unit prepared without production calibration implementation.

**Next action:** run canonical verification, finalize the records, and publish one coherent head.

**Lessons review:** no-new-lesson; this pass applies `L-003`, `L-004`, `L-005`, and `L-007`.

## A-007 — 2026-07-15T22:50:00Z — Second reconciliation locally verified

**Evidence status:** locally-verified in GitHub Actions publication workflow `29457435803`; commit and push pending.

**Starting state:** the twelve accepted findings had been corrected in one working publication unit and `VERIFY-02` remained active.

**Work performed:** ran the canonical verifier, read the complete successful output, marked the plan-level verification task complete, and prepared the coherent unit for one push.

**Files changed:** project records and closeout checklist finalized after verification.

**Verification:** `bash scripts/verify.sh` passed before this finalization; the workflow reruns it after finalization before committing.

**Publication / remote actions:** push pending; no PR reaction, reply, or resolution count is advanced by this entry.

**Result:** all plan-correction tasks and local verification tasks are complete; only PR actions, final review, and merge remain.

**Next action:** push the corrected head and complete `PR-01` and `PR-02`.

**Lessons review:** no-new-lesson; horizontal review and fail-closed publication followed existing guardrails.

## A-008 — 2026-07-15T23:15:00Z — Later review batch reconciled

**Evidence status:** reviewed; locally-verified in isolated publication workflow; push and PR actions pending.

**Starting state:** corrected head `b9ffc3a47fd7afcfa09b6f9422f1368bfea4f55c` passed GitHub Actions `Verify` run `29457643476`; the refreshed numeric comment map revealed eleven additional unresolved Codex findings beyond the earlier twelve.

**Work performed:** verified all eleven findings, classified the season-window finding as already satisfied, corrected the other ten contracts, added regression coverage for the documented no-new-lesson sentinel, and extended the closeout/reconciliation/lesson records.

**Files changed:** data, model, and browser plans; project-control validator and tests; closeout plan; reconciliation ledger; status, activity, and lessons records.

**Verification:** canonical `bash scripts/verify.sh` passed in GitHub Actions follow-up publication workflow run `29458295544`; the workflow reruns it after this record finalization.

**Publication / remote actions:** none advanced by this entry; comment counters remain unchanged until authenticated reactions/replies/resolutions are observed.

**Result:** all known review findings now have explicit dispositions and corrections; PR actions remain pending.

**Next action:** run canonical verification, publish one squashed follow-up commit, then rate/reply/resolve the complete comment inventory.

**Lessons review:** new lesson `L-008` recorded.
