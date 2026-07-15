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

---

## Execution Order

### Plan A — Data and feature pipeline

File: `docs/superpowers/plans/2026-07-14-spa-calibration-data-pipeline.md`

Produces:

```text
calibration/data/processed/laps.parquet
calibration/data/processed/aligned-traces.parquet
calibration/data/processed/phases.parquet
calibration/data/processed/features.parquet
calibration/data/processed/provenance.json
```

The output schemas are versioned as `spa-calibration-corpus/v1` and are the only supported inputs to Plan B.

### Plan B — Calibration, validation, and Spa prediction

File: `docs/superpowers/plans/2026-07-14-spa-calibration-model-prediction.md`

Consumes Plan A outputs and produces:

```text
calibration/artifacts/model/inference-data.nc
calibration/artifacts/model/model-summary.json
calibration/artifacts/validation/loco-results.json
calibration/artifacts/predictions/spa-2026-prediction-v1.json
```

The final prediction artifact may set `status: "released"` only when the validation report has `release_gates.passed: true`.

### Plan C — Browser artifact and UI integration

File: `docs/superpowers/plans/2026-07-14-spa-calibration-app-integration.md`

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
