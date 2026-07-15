---
schema: race-lab-closeout-plan/v1
initiative: spa-2026-calibration
plan_id: SPA-PR1-CLOSEOUT-2026-07-15
status: active
scope: planning-only
source_head: 1ffaf2d232f6bafd134fafa94ca067683744b639
---

# Spa 2026 PR #1 Closeout Plan

> **For agentic workers:** Execute this plan task-by-task. Before substantive work, read `../project/README.md`, `../project/STATUS.md`, and the latest entries in `ACTIVITY.md`, `DECISIONS.md`, and `LESSONS.md`. Do not implement production calibration functionality in this closeout.

**Goal:** Correct the twelve fresh Codex findings on PR #1, restore cross-plan consistency, complete review hygiene, and merge a coherent planning package without reopening approved architecture.

**Architecture:** This is a bounded reconciliation pass over the existing four-plan package. Data, model, browser, project-control, verification, and PR actions remain separate work units, but all are published only after a horizontal consistency review. The provisional Spa 2026 `1:40.4` estimate remains suppressed.

**Canonical verification:**

```bash
bash scripts/verify.sh
```

## Global constraints

- Planning and documentation only; no production calibration implementation.
- Evaluate external review findings before editing.
- Preserve the approved estimand, condition scenario, complete coherent profile draws, temporal isolation, and fail-closed release behavior.
- Keep observed, derived, inferred, simulated, provisional, and validated quantities distinct.
- Track finding evaluation, artifact change, reaction, inline reply, thread resolution, and fresh-review request separately.
- Update `project/STATUS.md` and append `project/ACTIVITY.md` before publication.
- Update `project/DECISIONS.md` when a load-bearing decision changes.
- Update `project/LESSONS.md`, or record `lessons_reviewed: no-new-lesson`, for every review-reconciliation publication.

---

### CTRL-01 — Establish durable project records

**Files:**
- Create: `circuits/spa-francorchamps/seasons/2026/project/README.md`
- Create: `circuits/spa-francorchamps/seasons/2026/project/STATUS.md`
- Create: `circuits/spa-francorchamps/seasons/2026/project/ACTIVITY.md`
- Create: `circuits/spa-francorchamps/seasons/2026/project/DECISIONS.md`
- Create: `circuits/spa-francorchamps/seasons/2026/project/LESSONS.md`

- [x] Define authority, mutation rules, freshness policy, and recovery procedure.
- [x] Seed current state from the remotely observed PR and review state.
- [x] Reconstruct prior activity without rewriting or overstating evidence.
- [x] Record load-bearing decisions and reusable lessons with stable IDs.

### CTRL-02 — Enforce project-record maintenance

**Files:**
- Create: `scripts/verify_project_control.py`
- Create: `tests/test_project_control.py`
- Modify: `scripts/verify.sh`
- Modify: `AGENTS.md`
- Create: `.github/workflows/verify.yml`

- [x] Validate required project-control files and front matter.
- [x] Validate stable task, activity, decision, and lesson IDs.
- [x] Validate active-task references and review-action counters.
- [x] Enforce append-only activity history when a merge base contains prior history.
- [x] Enforce diff-coupled updates to status, activity, decisions, and lessons.
- [x] Run the canonical verifier in GitHub Actions.

---

### DATA-01 — Complete the event-resolution contract

**Finding:** `PRRT_kwDOTZdGvM6RO8R2`

- [x] Verify the finding against the current data-pipeline plan.
- [x] Require every event row to contain either `meeting_key` or the complete fallback discriminator set: `meeting_name`, `circuit_short_name`, `date_start`, and `date_end`.
- [x] Update every example `events.yaml` row, not only Miami.
- [x] Add plan tests for missing metadata and multiple events in one country.
- [x] Record disposition and regression evidence in the reconciliation ledger.

### DATA-02 — Reconcile the canonical-geometry loader interface

**Finding:** `PRRT_kwDOTZdGvM6RO8R-`

- [x] Verify the declaration and every call site.
- [x] Adopt one exact signature that consumes the configured geometry path and source metadata.
- [x] Search all producers and consumers for the old signature.
- [x] Add a plan test covering a non-CSV Spa adapter and retained provenance.

### DATA-03 — Measure source coverage before normalization

**Finding:** `PRRT_kwDOTZdGvM6RO8SK`

- [x] Verify that truncated source progress is currently stretched to `0..1`.
- [x] Specify raw coverage against the complete canonical track before monotonic repair or resampling.
- [x] Add a middle-60%-of-lap fixture that remains incomplete and rejected.
- [x] Confirm resampling cannot upgrade an ineligible lap.

---

### MODEL-01 — Preserve coherent-lap identity in validation

**Finding:** `PRRT_kwDOTZdGvM6RO8Rw`

- [x] Preserve `lap_slug` through model and baseline projections and joins.
- [x] Aggregate and score by coherent lap/profile before fold-level aggregation.
- [x] Add a multi-profile regression fixture that would fail under fleet-wide summation.

### MODEL-02 — Represent every configured release gate

**Finding:** `PRRT_kwDOTZdGvM6RO8R8`

- [x] Reconcile `ReleaseGates` with every key in `release-gates.yaml`.
- [x] Reject unknown or silently dropped configuration keys.
- [x] Route all release evidence through one `combine_release_evidence()` authority.
- [x] Confirm 95% coverage, WIS, CRPS, rolling-origin, physical-feasibility, identifiability, baseline, and point-error gates all participate in `passed`.

### MODEL-03 — Reconcile the control-constraint solver interface

**Finding:** `PRRT_kwDOTZdGvM6RO8SA`

- [x] Verify every `_solve_speed_envelope()` declaration and call.
- [x] Define the exact `control_constraints` type and ownership.
- [x] Add a plan test that exercises the same signature used by `simulate_lap()`.

### MODEL-04 — Integrate elapsed time over actual path segments

**Finding:** `PRRT_kwDOTZdGvM6RO8SN`

- [x] Replace the artificial post-finish segment with `n - 1` actual segments for `n` samples.
- [x] Emit elapsed time as zero plus cumulative segment times.
- [x] Require exact agreement among trace endpoint, lap summary, sectors, and artifact.
- [x] Add constant-speed, nonuniform-spacing, and no-post-finish-segment tests.

### MODEL-05 — Require complete field draws

**Finding:** `PRRT_kwDOTZdGvM6RO8SR`

- [x] Freeze the supported profile set before sampling.
- [x] Require every profile and both declared attempts in every field draw.
- [x] Reject duplicate, missing, filtered, or solver-failed profiles rather than silently changing the represented field.
- [x] Make incomplete field draws release-blocking.

### MODEL-06 — Validate release semantics before checksum finalization

**Finding:** `PRRT_kwDOTZdGvM6RO8Ry`

- [x] Build the unsigned artifact.
- [x] Run complete semantic release validation before hashing.
- [x] Compute and attach the checksum only after semantic validation passes.
- [x] Run final checksum-plus-schema validation before serialization.
- [x] Add fixtures for malformed intervals, unsupported scenarios, and stale timestamps.

---

### APP-01 — Validate every artifact status before bundling

**Finding:** `PRRT_kwDOTZdGvM6RO8SC`

- [x] Invoke `validateCalibrationArtifact()` for pending, failed-validation, and released artifacts.
- [x] Verify checksums where required, but never treat checksum validity as semantic release validity.
- [x] Replace any invalid artifact with the frozen pending fallback.
- [x] Confirm unreleased artifacts cannot expose field, team, or predicted-corner estimates.

### APP-02 — Remove legacy telemetry keys at the adapter boundary

**Finding:** `PRRT_kwDOTZdGvM6RO8SI`

- [x] Destructure and discard `speed`, `throttle`, and `brake`.
- [x] Emit only normalized `speedKph`, `throttlePct`, and `brakePct` channels.
- [x] Add tests asserting both value parity and absence of legacy keys.

### APP-03 — Repair the released browser-schema fixture

**Finding:** `PRRT_kwDOTZdGvM6RO8SV`

- [x] Create one complete valid released-artifact fixture helper.
- [x] Include all release reports, provenance, scenario metadata, timestamps, intervals, and released prediction data.
- [x] Mutate exactly one property per negative test so each guard is actually exercised.

---

### DOCS-01 — Extend the reconciliation ledger

**File:** `circuits/spa-francorchamps/seasons/2026/reviews/2026-07-15-plan-reconciliation.md`

- [x] Add section `C. Fresh Codex review of 1ffaf2d`.
- [x] Record thread ID, severity, verification, disposition, affected interfaces, changes, regression evidence, reaction, reply, and resolution for all twelve findings.
- [x] Record any rejected or modified finding with technical reasoning.

### VERIFY-01 — Perform a horizontal contract review

- [x] Check Plan A outputs against every Plan B consumer.
- [x] Check Plan B artifact fields against every Plan C validator and renderer.
- [x] Check Python builder, Python validator, CLI, JavaScript generator, and browser validator against one release predicate.
- [x] Check scenario, estimand, complete-profile, attempt-count, and uncertainty semantics across all four plans.
- [x] Search the complete package for superseded signatures and field names.

### VERIFY-02 — Run and record canonical verification

- [x] Run `bash scripts/verify.sh` from a clean checkout with declared tooling installed.
- [x] Read the complete output and record the exact command, exit status, and relevant versions.
- [x] Distinguish local verification from CI confirmation.
- [x] Do not treat software checks as scientific model validation.

---

### PR-01 — Finish the original review-action sweep

- [ ] Re-check all 23 original inline comments.
- [ ] Apply reactions to the 18 comments that remain unrated, based on documented technical evaluation.
- [ ] Confirm the original action ledger separately records `rated`, `replied`, and `resolved` counts.

### PR-02 — Reconcile the twelve fresh findings

- [ ] Apply a reaction to every fresh comment after evaluation.
- [ ] Reply in the corresponding inline thread with disposition, revised section, and verification evidence.
- [ ] Resolve only threads whose finding is fully addressed or explicitly rejected with evidence.
- [ ] Refresh exact counts in `project/STATUS.md` and append `project/ACTIVITY.md`.

### PR-03 — Request one final review

- [ ] Confirm the intended head is stable and canonical verification passes.
- [ ] Post one summary comment linking the reconciliation ledger and project status.
- [ ] Request exactly one fresh Codex review.
- [ ] Reassess any new finding without reopening approved architecture unless it exposes a genuine contradiction.

### PR-04 — Merge and hand off

- [ ] Confirm no valid blocking review findings remain.
- [ ] Confirm all required reactions, replies, and resolutions are complete.
- [ ] Update `STATUS.md`, append `ACTIVITY.md`, and review `DECISIONS.md` and `LESSONS.md`.
- [ ] Merge PR #1 using the repository's chosen merge method.
- [ ] Record the merge commit as remotely observed and CI-confirmed only when direct evidence exists.
- [ ] Set the next exact action to Plan A source-feasibility and eligibility execution.

## Completion definition

PR #1 closeout is complete only when all twelve fresh findings have documented dispositions, the plan package has no known cross-plan contradictions, canonical verification passes, all required PR actions are individually accounted for, one final review has no valid blocking findings, the provisional `1:40.4` estimate remains suppressed, and no production calibration functionality has entered the planning-only PR.
