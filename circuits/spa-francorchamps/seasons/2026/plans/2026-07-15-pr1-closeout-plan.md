---
schema: race-lab-closeout-plan/v1
initiative: spa-2026-calibration
plan_id: SPA-PR1-CLOSEOUT-2026-07-15
status: active
scope: planning-only
source_head: 76b8226e0e4365bf757300972174e5fe28319f1c
---

# Spa 2026 PR #1 Closeout Plan

> Execute against the exact named head. Read the maintenance records first. Do not implement production calibration functionality or publish a prediction.

**Goal:** Publish the canonical `FINAL-01` through `FINAL-22` reconciliation as one verified commit, complete the corresponding review actions, obtain one clean final review, and merge PR #1.

**Canonical verification:**

```bash
bash scripts/verify.sh
```

## Global constraints

- Planning-only scope; the provisional `1:40.4` estimate remains suppressed.
- Preserve coherent car-driver profiles, complete field draws, temporal isolation, uncertainty calibration, provenance, physical feasibility, and fail-closed release behavior.
- Treat finding evaluation, artifact correction, reaction, inline reply, resolution, final-review request, and merge as separate states.
- Refresh PR head and the full thread inventory immediately before publication and review actions.

## Completed foundations

### CTRL-01 — Durable project records
- [x] Maintain authoritative status, append-only activity, decisions, lessons, maintenance rules, and stable task IDs.

### CTRL-02 — Project-record enforcement
- [x] Validate records, active tasks, counters, append-only history, diff-coupled updates, and current-entry lesson disposition.

### DATA-01 — Event-resolution contract
- [x] Require circuit-unique event identity and typed timestamp boundaries.

### DATA-02 — Canonical geometry contract
- [x] Use configured immutable geometry sources and retain provenance.

### DATA-03 — Raw source coverage
- [x] Measure completeness before normalization or resampling.

### MODEL-01 — Coherent-lap validation
- [x] Preserve lap/profile identity through scoring.

### MODEL-02 — Complete release-gate representation
- [x] Include every configured mandatory release gate.

### MODEL-03 — Control-constraint interface
- [x] Reconcile solver declarations and calls.

### MODEL-04 — Physical segment timing
- [x] Integrate exactly `n - 1` real segments for `n` samples.

### MODEL-05 — Complete field draws
- [x] Reject missing, duplicate, or solver-failed profile-attempt fields.

### MODEL-06 — Pre-checksum release validation
- [x] Validate complete semantics before and after checksum finalization.

### APP-01 — Validate every artifact status
- [x] Fail malformed pending, failed, or released artifacts closed.

### APP-02 — Normalize telemetry channels
- [x] Remove legacy keys at the adapter boundary.

### APP-03 — Complete released fixtures
- [x] Use complete report, provenance, interval, trace, timing, and scenario fixtures.

### DOCS-01 — Reconciliation ledger
- [x] Record the complete review history and separate PR action states.

### VERIFY-01 — Horizontal contract review
- [x] Review all producers and consumers across data, model, artifact, CLI, generator, browser, tests, and records.

### VERIFY-02 — Canonical local verification
- [x] Verify the prior correction unit; rerun before each publication candidate.

## Final 22-finding inventory

Each completed row records a technical disposition and a bounded correction in the reconciliation ledger. Remote actions remain pending until the exact correction head is CI-confirmed.

### FINAL-01 — Import `RawCoverage`
- [x] Import the annotation type and construct complete fixtures.

### FINAL-02 — Deterministic geometry manifest
- [x] Separate human source metadata from frozen format/checksum evidence.

### FINAL-03 — Report-level release conjunction
- [x] Conjoin every mandatory report flag and nested check; reject set mismatch.

### FINAL-04 — Preserve field-best identity
- [x] Carry profile, team, driver, draw, and attempt through evidence selection.

### FINAL-05 — Five-point field interval
- [x] Require finite ordered 95%/80%/median bounds in Python and browser contracts.

### FINAL-06 — Sampled-attempt evidence
- [x] Store trace and timing from the exact varied attempt used for its summary.

### FINAL-07 — Released trace and timing
- [x] Require coherent playable arrays before source selection.

### FINAL-08 — Synchronize publication records
- [x] Record the directly observed head and distinguish local from pushed state.

### FINAL-09 — Verify geometry bytes
- [x] Hash exact source bytes before parsing.

### FINAL-10 — Analogue evidence schema
- [x] Adapt raw observed features into stable phase identity and observed year; reject paired deltas.

### FINAL-11 — Current lesson disposition
- [x] Enforce the newest activity entry under RED/GREEN regression coverage.

### FINAL-12 — Geometry provenance fixture
- [x] Supply complete `GeometrySource` fixture data.

### FINAL-13 — Validator clock contract
- [x] Provide a safe public UTC default while deterministic callers inject time.

### FINAL-14 — Inventory-driven closeout
- [x] Use stable row IDs instead of stale prose counts.

### FINAL-15 — Raw coverage fixtures
- [x] Supply pre-normalization coverage in every quality context.

### FINAL-16 — Observed feed gaps
- [x] Use consecutive source intervals only.

### FINAL-17 — Nullable braking onset
- [x] Aggregate and score only paired observed outcomes with an explicit mask.

### FINAL-18 — Complete release fixture corpus
- [x] Include reports, valid digests, provenance, identity, intervals, trace, timing, and scenario.

### FINAL-19 — Typer `--artifact`
- [x] Declare the documented required option explicitly.

### FINAL-20 — Exact corpus artifact set
- [x] Require equality among canonical files, manifest keys, filesystem files, and digests.

### FINAL-21 — Raw reversal gate
- [x] Use pre-repair reversal evidence in lap acceptance.

### FINAL-22 — Timestamp normalization
- [x] Normalize strings, `date`, and aware `datetime` objects to UTC at boundaries.

## Active publication and closeout gates

### PR-01 — Publish atomic correction
- [ ] Refresh PR #1 and require exact head `76b8226e0e4365bf757300972174e5fe28319f1c`.
- [ ] Rerun complete local verification and verify exactly twelve intended files.
- [ ] Create one commit whose sole parent is the exact head and fast-forward the PR branch without force.
- [ ] Read back the commit, exact changed files, tree, and diff statistics.
- [ ] Require a successful retrievable `Verify` run for the exact correction SHA.

### PR-02 — Complete 22-thread action sweep
- [ ] Refresh the complete same-head inventory.
- [ ] Apply missing positive reactions only after technical evaluation.
- [ ] Post one specific inline reply per final finding with correction SHA and Verify evidence.
- [ ] Resolve each completed thread and refresh the inventory.

### PR-03 — Synchronize evidence and request one final review
- [ ] Publish only the minimal living-record evidence update required by observed remote actions.
- [ ] Obtain exact-head CI for that evidence commit.
- [ ] Request exactly one fresh Codex review on the stable head.

### PR-04 — Merge and hand off
- [ ] Confirm no valid blocking findings remain and CI is green.
- [ ] Merge using squash with the expected head SHA.
- [ ] Record exact merge evidence and leave the next implementation action.

## Completion definition

Closeout is complete only when all 22 rows are published and individually accounted for, exact-head CI succeeds, one final review has no valid blocker, PR #1 is merged, the planning-only boundary is preserved, and no suppressed prediction value is released.


### PR-03A — Reconcile post-final review blockers

- [ ] Verify and classify `POSTFINAL-01` through `POSTFINAL-13` against exact head `cfe939e33458eb2b1af257bfc8bfc19476d22c78`.
- [ ] Correct only the three implementation plans and required living records.
- [ ] Run focused regression checks, complete verification, fenced-snippet syntax sweep, and cross-contract audit.
- [ ] Preserve an external recovery artifact.
- [ ] Publish one atomic commit parented by the exact starting head and obtain exact-head Verify success.
- [ ] Apply 13 positive reactions, 13 inline replies, and 13 thread resolutions.
- [ ] Confirm zero unresolved threads.
- [ ] Do not merge and do not request another review in this task.
