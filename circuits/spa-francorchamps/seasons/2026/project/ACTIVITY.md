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

**Publication / remote actions:** the verified files were built on `staging/spa-project-control-20260715`; the PR branch is advanced once to the complete staging head rather than receiving partial file states. The last material staging commit before the record files was `6bdc71ae331f9387f353589f59cfdff5ba0461d7`.

**Result:** the repository now has durable project continuity records and automated maintenance checks. The twelve fresh Codex findings remain unresolved and no production calibration functionality was implemented.

**Next action:** verify and disposition `DATA-01` against the current data-pipeline plan before editing.

**Lessons review:** no-new-lesson; enforcement implements `L-001` through `L-007`.
