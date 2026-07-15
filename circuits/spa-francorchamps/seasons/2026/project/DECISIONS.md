---
schema: race-lab-project-decisions/v1
initiative: spa-2026-calibration
---

# Decision Register

## D-001 — Accepted — Prediction estimand and condition scenario

**Decision:** The primary estimand is the distribution of the best clean dry qualifying lap achievable by each supported 2026 car-driver profile under `spa-2026-dry-qualifying-reference/v1`, using two representative push attempts and complete coherent field draws.

**Rationale:** One precise target is required across training, simulation, validation, artifacts, and UI. It prevents expected-pole claims, theoretical-minimum claims, and impossible composite laps from being conflated.

**Rejected alternatives:** expected actual pole as the v1 target; unconstrained theoretical minimum; independently selected best sectors; incomplete field minima.

**Affected interfaces:** scenario provenance, profile/attempt sampling, field-best aggregation, artifact schema, browser copy.

**Reversal conditions:** a separately approved estimand migration with new validation, artifact version, and UI contract.

## D-002 — Accepted — Release is a conjunction of evidence gates

**Decision:** `released` requires source eligibility, geometric-transfer validation, rolling-origin validation, uncertainty calibration, baseline improvement, identifiability, physical feasibility, complete provenance, scenario validity, freshness, and shared validator agreement.

**Rationale:** No single checksum, point metric, or software test establishes scientific release eligibility.

**Rejected alternatives:** LOCO-only release; checksum-only release; optional temporal or uncertainty gates; independent browser/model predicates.

**Affected interfaces:** release-gate configuration, report schemas, artifact builder, CLI, generator, browser validator.

**Reversal conditions:** an approved versioned release contract supported by evidence at least as strong as the current conjunction.

## D-003 — Accepted — PR #1 remains planning-only

**Decision:** PR #1 establishes repository structure, governing specifications, reviews, plans, verification, and project controls. It does not implement the production calibration pipeline or release a prediction.

**Rationale:** Mixing production implementation into closeout would blur proposal, implementation, validation, and release states and make review evidence ambiguous.

**Rejected alternatives:** opportunistic implementation inside plan reconciliation; publication of the provisional `1:40.4` estimate.

**Affected interfaces:** PR scope, completion criteria, merge decision, next-phase handoff.

**Reversal conditions:** merge PR #1 first, then authorize a separate implementation unit.

## D-004 — Accepted — Repository-backed living records are authoritative

**Decision:** The Spa initiative uses `project/STATUS.md`, append-only `ACTIVITY.md`, `DECISIONS.md`, `LESSONS.md`, a dated closeout plan, and `project/README.md` as durable control records.

**Rationale:** Cross-chat memory and narrative summaries were insufficient to distinguish discussed, local, committed, pushed, reviewed, and CI-confirmed states.

**Rejected alternatives:** conversation memory only; a single mutable status document; fully generated history without reasoning records.

**Affected interfaces:** session start/end procedures, verification, PR closeout, handoff.

**Reversal conditions:** a replacement system that preserves at least the same authority, append-only history, decisions, lessons, evidence labels, and automated freshness checks.

## D-005 — Accepted — Review actions are separate state dimensions

**Decision:** Finding evaluation, artifact change, reaction, inline reply, thread resolution, and fresh-review request are tracked separately.

**Rationale:** The previous use of “addressed” hid an interrupted reaction sweep and absence of inline replies despite resolved threads.

**Rejected alternatives:** one binary addressed/not-addressed field.

**Affected interfaces:** status counters, activity entries, reconciliation ledger, PR closeout criteria.

**Reversal conditions:** none unless the replacement remains at least as explicit.
