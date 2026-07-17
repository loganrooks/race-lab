# Spa 2026 Calibration Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the provisional Spa 2026 lap-time claim with a reproducible, backtested corner-transfer prediction and expose its evidence and uncertainty in Spa Race Lab.

**Architecture:** The program is split into three independently reviewable plans. Plan A builds a deterministic paired 2025–2026 telemetry corpus and phase-level feature store. Plan B fits and validates the hierarchical correction model, composes it with the minimum-time vehicle prior, and emits a versioned Spa prediction artifact. Plan C adapts that artifact for the browser and adds prediction, comparison, uncertainty, and calibration-report interfaces without fitting models client-side.

**Tech Stack:** Python 3.11+, NumPy, pandas, SciPy, PyArrow, scikit-learn, PyMC, ArviZ, Pydantic, httpx, Typer, pytest; existing vanilla HTML/CSS/JavaScript, Node test runner, esbuild, Playwright.

## Global Constraints

- The app must not display a calibrated Spa pole estimate until every release gate in the approved specification passes.
- Preserve the current coupled dynamics lap only as an explicitly **uncalibrated educational simulation**.
- Keep observed source data, derived features, fitted model state, and browser artifacts in separate directories.
- Historical OpenF1 progress synchronization is observed; lateral road placement remains illustrative unless a source explicitly supports it.
- Do not infer proprietary battery state, electrical power flow, downforce, drag, or exact active-aero commands as observed telemetry.
- Every generated artifact must include model version, source-data cutoff, training circuits, held-out circuits, regulation identifiers, hyperparameters, random seed, validation metrics, checksum, and generation timestamp.
- Whole-circuit scaling is a baseline only; the release model must outperform it on held-out lap-time and telemetry-shape metrics.
- Initial release gates: lap-time MAE ≤ 0.7 s; sector MAE ≤ 0.25 s; minimum-speed MAE ≤ 8 km/h; braking-onset MAE ≤ 25 m or the source-resolution equivalent; no persistent signed error across principal Spa archetypes.
- All data refreshes are explicit CLI operations; tests use frozen, auditable fixtures and never depend on live APIs.
- No new runtime dependency is added to the browser app.


## Reconciled Programme Contract — 2026-07-15

This section is normative and supersedes any less-specific wording or illustrative snippet later in the four-plan package.

### Prediction estimand and Spa scenario

The primary estimand is **the distribution of the best clean dry qualifying lap achievable by each supported 2026 car-driver profile under the declared Spa reference scenario**. It is not an expected actual pole, not a theoretical unconstrained minimum, and not the best of independently selected sectors. Each profile distribution represents the best of **two independent representative push attempts** after one preparation lap; attempt-level execution variation is sampled within profile. The field-best distribution is the draw-wise minimum across complete, coherent profile attempts.

The release scenario is versioned as `spa-2026-dry-qualifying-reference/v1` and fixes: soft-compound new-tyre state; qualifying fuel and legal operating state; dry track; no traffic, tow, yellow flag, or interruption; DRS/active-aero/ERS operation only where legal and physically feasible. Track temperature, ambient temperature, pressure/air density, wind vector, and grip evolution are sampled from declared pre-event scenario distributions. The artifact must contain those distributions and the scenario checksum. A separate expected-session-pole model is explicitly out of scope.

### Release eligibility

`released` requires the conjunction of all of the following, evaluated by one shared validator used by the model, CLI, browser generator, and browser runtime:

1. source and circuit-year eligibility manifests pass;
2. leave-one-circuit-out geometric-transfer gates pass;
3. rolling-origin temporal-forecast gates pass;
4. point-estimate gates pass per coherent lap/profile;
5. 80% and 95% interval coverage, weighted interval score, and CRPS gates pass at supported granularities;
6. required baselines are outperformed and ablations justify retained complexity;
7. identifiability and profile-support rules pass;
8. every sampled trajectory passes physical, ERS, geometry, and convergence checks;
9. complete provenance and checksums validate.

Failure of any required gate yields `failed-validation` or `pending`; it never yields a partially released central estimate. The provisional `1:40.4` value remains suppressed.

### Empirical-to-physics contract

The hierarchical model emits a **joint correction draw** with named correction families. Each observed effect has exactly one owner:

- effective-envelope corrections alter bounded physical capacities before solving;
- control-landmark corrections alter braking/throttle constraints or objective penalties;
- phase-duration residuals may be used only for validation diagnostics in v1 and are not added to the released lap time;
- direct output-channel residuals are prohibited in a released coupled trace.

A correction ledger records family, units, source outcome, solver target, and application count. Duplicate ownership or application count other than one is a release failure. Each uncertainty draw is solved and re-optimized as one joint trajectory.

### Validation and evidence outputs

Plan A additionally produces source-feasibility, circuit-year eligibility, raw-coverage, and selection-fallback manifests. Plan B additionally produces rolling-origin, uncertainty-calibration, baseline, ablation, identifiability, and physical-feasibility reports. Plan C consumes only artifacts accepted by the shared release validator.

---

## Execution Order

### Plan A — Data and feature pipeline

File: `circuits/spa-francorchamps/seasons/2026/plans/2026-07-14-spa-calibration-data-pipeline.md`

Produces:

```text
calibration/data/processed/laps.parquet
calibration/data/processed/aligned-traces.parquet
calibration/data/processed/phases.parquet
calibration/data/processed/features.parquet
calibration/data/processed/provenance.json
calibration/manifests/source-eligibility.json
calibration/manifests/circuit-year-eligibility.json
calibration/manifests/lap-selection.json
```

The output schemas are versioned as `spa-calibration-corpus/v1` and are the only supported inputs to Plan B.

### Plan B — Calibration, validation, and Spa prediction

File: `circuits/spa-francorchamps/seasons/2026/plans/2026-07-14-spa-calibration-model-prediction.md`

Consumes Plan A outputs and produces:

```text
calibration/artifacts/model/inference-data.nc
calibration/artifacts/model/model-summary.json
calibration/artifacts/validation/loco-results.json
calibration/artifacts/validation/rolling-origin-results.json
calibration/artifacts/validation/uncertainty-calibration.json
calibration/artifacts/validation/baselines-ablations.json
calibration/artifacts/validation/identifiability.json
calibration/artifacts/predictions/spa-2026-prediction-v1.json
```

The final prediction artifact may set `status: "released"` only when the validation report has `release_gates.passed: true`.

### Plan C — Browser artifact and UI integration

File: `circuits/spa-francorchamps/seasons/2026/plans/2026-07-14-spa-calibration-app-integration.md`

Consumes the Plan B prediction artifact and produces:

```text
js/calibration-data.js
spa-race-lab-standalone.html
spa-race-lab.zip
```

The UI must render `Calibration pending` whenever the generated artifact is absent, invalid, stale, or not released.

## Cross-Plan Interfaces

### Corpus manifest

```python
class CorpusManifest(BaseModel):
    schema_version: Literal["spa-calibration-corpus/v1"]
    generated_at: datetime
    source_cutoff: datetime
    circuits: list[str]
    seasons: list[int]
    lap_count: int
    trace_point_count: int
    phase_count: int
    feature_count: int
    source_checksums: dict[str, str]
    artifact_checksums: dict[str, str]
```

### Prediction artifact

```typescript
type SpaPredictionArtifact = {
  schemaVersion: "spa-calibration-prediction/v1";
  status: "pending" | "failed-validation" | "released";
  modelVersion: string;
  generatedAt: string;
  sourceCutoff: string;
  fieldBest: null | LapPrediction;
  teams: LapPrediction[];
  historicalReferences: HistoricalTraceSummary[];
  analogueTraces: AnalogueTraceSummary[];
  corners: CornerPrediction[];
  validation: ValidationSummary;
  provenance: PredictionProvenance;
  checksum: string;
};
```

### Release state transition

```text
pending
  ├── missing corpus/model/artifact → remain pending
  ├── validation gates fail         → failed-validation
  └── all gates pass                → released
```

The browser must never infer `released` from the presence of a central lap time.

## Program-Level Verification

Run after all three plans are complete:

```bash
cd calibration
python -m pytest -q
python -m spa_calibration.cli validate --artifact artifacts/predictions/spa-2026-prediction-v1.json
cd ..
npm run verify
python -m zipfile -t /mnt/data/spa-race-lab.zip
```

Expected:

```text
all Python tests passed
prediction artifact schema valid
release state agrees with validation gates
all Node and Playwright tests passed
Done testing of archive. No errors detected.
```

## Commit Sequence

Each plan uses small commits. The final integration commit must not combine generated source-data refreshes with hand-written application code. Use this order:

```text
feat(calibration-data): add deterministic corpus pipeline
feat(calibration-model): add hierarchical transfer and LOCO validation
feat(spa-prediction): generate gated Spa prediction artifact
feat(app): integrate calibrated prediction evidence
chore(data): refresh calibration corpus through <cutoff-date>
```

## Specification Coverage Matrix

| Approved requirement | Implemented by |
|---|---|
| Paired 2025–2026 dry qualifying corpus with provenance and quality weights | Plan A Tasks 1–3 and 7–8 |
| Canonical geometry, distance alignment, adaptive smoothing, and source-resolution disclosure | Plan A Tasks 4–5 |
| Driving-phase detection and continuous corner/archetype features | Plan A Tasks 5–6 |
| Whole-circuit and archetype baselines | Plan B Task 1 |
| Hierarchical team, driver, circuit, phase, archetype, and team×archetype effects | Plan B Tasks 2–3 |
| Energy-constrained coupled dynamics and minimum-time line optimization | Plan B Task 4 |
| Regulation-regime selection and leave-one-circuit-out validation | Plan B Task 5 |
| Spa analogue transfer, coherent team laps, field-best distribution, and corner uncertainty | Plan B Task 6 |
| Gated, versioned, checksum-protected prediction artifact | Plan B Task 7 |
| Pending/failed/released UI states and suppression of provisional 1:40.4 | Plan C Tasks 1–3 and 7 |
| Trace replay, telemetry comparison, uncertainty bands, corner evidence, and calibration report | Plan C Tasks 2 and 4–7 |
| Offline standalone/ZIP release and clean-checkout verification | Plan C Task 7 and program-level verification |

## Completion Definition

The program is complete only when:

1. every Plan A/B/C task is checked off;
2. the full verification command succeeds from a clean checkout;
3. the prediction artifact checksum is reproducible with the documented seed and corpus manifest;
4. the app shows no provisional 1:40.4 field-best claim;
5. the released UI displays central estimate, uncertainty, evidence, limitations, and data cutoff—or clearly displays `Calibration pending` if gates fail.
