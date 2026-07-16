# Spa Calibration Data Pipeline Implementation Plan

> **For implementation agents:** follow the repository's planning and test-driven-development procedures. This document is planning-only; it does not implement production calibration functionality or authorize a prediction release.

## Objective and release boundary

Build a deterministic, provenance-rich qualifying corpus for 2024 controls and paired 2025–2026 analysis. The corpus aligns eligible OpenF1 observations to immutable canonical circuit geometry, classifies source quality before interpolation, extracts coherent lap/phase features, and writes an exactly defined checksummed artifact set.

The provisional Spa 2026 `1:40.4` estimate remains suppressed. Completing this plan, passing software tests, or building a corpus does not validate or release that estimate. Release still requires the separately approved calibration, rolling-origin validation, uncertainty-calibration, provenance, physical-feasibility, and baseline-performance gates.

## Non-negotiable invariants

1. **Planning-only scope.** Tasks below describe future implementation under `calibration/`; this plan does not add runtime calibration behavior.
2. **Season identity.** Event resolution uses `meeting_key` when frozen. Otherwise it requires `meeting_name`, `circuit_short_name`, and a bounded event-date window and must resolve exactly one session. Country alone is insufficient.
3. **Coherent qualifying selection.** Select Q3/SQ3 first for each coherent car-driver profile; fall back in declared order to Q2/SQ2 and Q1/SQ1. Persist `selection_fallback`, `fallback_reason`, and source segment.
4. **Raw evidence first.** Compute source coverage, inter-sample gaps, progress reversals, and channel coverage on observed coupled rows before monotonic repair or canonical-grid interpolation. Resampling cannot upgrade an ineligible lap.
5. **Immutable geometry.** Canonical geometry comes only from a frozen manifest. The loader verifies the exact source-file SHA-256 before parsing. Source location coordinates may estimate progress but may not overwrite canonical distance, curvature, gradient, sector, width, or provenance.
6. **Bounded progress.** Final aligned outputs are monotonic, remain within `[0, 1]`, include the exact start and track-length endpoints once, and never extrapolate beyond canonical length.
7. **Nullable braking onset.** Missing braking onset remains null. It is not zero-filled or imputed. An onset delta exists only when both paired seasons observe the outcome.
8. **Exact corpus closure.** A valid corpus contains exactly four Parquet artifacts—`laps.parquet`, `aligned-traces.parquet`, `phases.parquet`, and `features.parquet`—plus `provenance.json`. The manifest and directory must agree exactly, and every required checksum must match.
9. **Timezone discipline.** Event windows and source timestamps accept ISO strings or already-parsed timezone-aware `datetime` objects through one normalizer. Naive or unsupported values fail closed.
10. **No networked tests.** Unit and fixture tests never refresh live sources.

## File and module map

```text
calibration/
├── pyproject.toml
├── README.md
├── config/
│   ├── events.yaml
│   ├── circuit-geometry-sources.yaml
│   ├── circuits.yaml                    # generated and frozen
│   ├── complexes.yaml
│   ├── source-eligibility.yaml
│   └── feature-requirements.yaml
├── data/
│   ├── raw/openf1/
│   ├── geometry/
│   ├── reference/
│   ├── fixtures/
│   └── processed/
├── manifests/
│   ├── source-eligibility.json
│   ├── circuit-year-eligibility.json
│   └── lap-selection.json
├── src/spa_calibration/
│   ├── schemas.py
│   ├── hashing.py
│   ├── cache.py
│   ├── openf1.py
│   ├── eligibility.py
│   ├── quality.py
│   ├── geometry.py
│   ├── alignment.py
│   ├── phases.py
│   ├── features.py
│   ├── corpus.py
│   ├── pipeline.py
│   └── cli.py
└── tests/
    ├── test_schemas.py
    ├── test_cache.py
    ├── test_openf1.py
    ├── test_eligibility.py
    ├── test_quality.py
    ├── test_alignment.py
    ├── test_phases.py
    ├── test_features.py
    ├── test_corpus.py
    └── test_pipeline.py
```

## Shared typed contracts

The implementation must use one definition of each contract; tests and fixtures import these definitions rather than reproducing stale local variants.

```python
@dataclass(frozen=True)
class LapKey:
    season: int
    meeting_key: int
    session_key: int
    driver_number: int
    lap_number: int

@dataclass(frozen=True)
class RawCoverage:
    progress_start: float
    progress_end: float
    coverage_ratio: float
    channel_coverage: dict[str, float]
    maximum_gap_s: float
    maximum_progress_reversal: float

@dataclass(frozen=True)
class GeometrySource:
    path: Path
    format: str
    source_name: str
    source_license: str
    checksum: str

@dataclass(frozen=True)
class CanonicalTrack:
    circuit_id: str
    length_m: float
    distance_m: NDArray[np.float64]
    x_m: NDArray[np.float64]
    y_m: NDArray[np.float64]
    elevation_m: NDArray[np.float64]
    heading_rad: NDArray[np.float64]
    curvature_per_m: NDArray[np.float64]
    gradient: NDArray[np.float64]
    sector: NDArray[np.int16]
    geometry_source: GeometrySource

@dataclass(frozen=True)
class LapContext:
    rainfall: bool | None
    race_control_flags: tuple[str, ...]
    is_pit_out: bool
    aborted: bool
    raw_coverage: RawCoverage
```

`LapQuality` persists the six raw-coverage fields, the accepted flag, score, flags, and weather state. `FeatureRecord.braking_onset_distance_m` and `FeatureRecord.braking_onset_from_complex_start_m` are nullable. `CorpusManifest` requires `source_eligibility_checksum`, `circuit_year_eligibility_checksum`, `lap_selection_checksum`, source checksums, and artifact checksums under schema `spa-calibration-corpus/v1`.

## Task 0 — Freeze source eligibility

**Deliverables**

- `config/source-eligibility.yaml`
- `config/feature-requirements.yaml`
- `eligibility.py`
- fixture-backed eligibility tests
- evaluated `source-eligibility.json` and `circuit-year-eligibility.json`

Each circuit-season-session record includes source query identity, adapter version, channel semantics and units, raw sample counts, observed median/p95 interval, gaps, quantization, known delays, licensing/redistribution terms, derivable features, prohibited claims, quality flags, and the resulting eligibility level: `excluded`, `sector-only`, `phase`, or `corner`.

Tests must reject unknown units, absent licensing, absent observed resolution, or an eligibility claim whose required channels are unavailable. The feasibility spike covers Silverstone/Suzuka, Montreal, Spielberg, Barcelona, and Miami before generalization.

## Task 1 — Package and schemas

Create the Python package and strict frozen Pydantic models. Extra fields fail validation. SHA-256 fields accept exactly 64 lowercase hexadecimal characters. Qualifying session and segment enums remain explicit. `LapKey.slug` is stable. `PhaseRecord` rejects zero- or negative-length phases. Manifest construction tests supply every required eligibility/selection checksum.

Verification target:

```bash
cd calibration
python -m pip install -e '.[dev]'
python -m pytest tests/test_schemas.py -q
```

## Task 2 — Immutable OpenF1 cache and event resolution

Implement canonical JSON serialization, SHA-256 addressing, immutable cache paths, deterministic query encoding, rate limiting, and strict list-payload validation.

`EventSpec` must contain either a frozen `meeting_key` or all fallback identity fields. `resolve_session()` filters by session name, exact meeting name, exact circuit short name, and normalized bounded dates and fails unless exactly one candidate remains.

`config/events.yaml` lists 2024, 2025, and 2026 event windows for every configured circuit. YAML may parse timestamps into `datetime`; downstream code must not assume they remain strings.

Tests use `respx` and content-addressed fixtures only. No test reaches OpenF1.

## Task 3 — Raw quality classification

`RawCoverage` is defined in `quality.py` and imported by alignment before `measure_raw_source_coverage()` is declared. Every `LapContext` constructor—including quality fixtures and pipeline call sites—supplies `raw_coverage`.

`measure_raw_source_coverage()` receives observed coupled rows sorted by source time and computes:

- coverage from unwrapped observed progress;
- channel non-null ratios on observed rows;
- maximum gap from `np.diff(observed_elapsed_s)` only;
- maximum reversal from negative differences of unwrapped observed progress.

A one-sample observation uses an infinite gap and is ineligible. The classifier must not seed a gap with lap duration, recalculate gaps from a repaired or resampled trace, or recalculate reversals after `maximum.accumulate`.

Acceptance requires all of:

```text
coverage_ratio >= 0.94
maximum_gap_s <= 1.5
maximum_progress_reversal <= 0.006
valid dry qualifying lap
no pit-out, abort, affected race-control window, or invalid lap time
```

Required tests:

1. clean complete dry lap accepted;
2. observed large gap and yellow flag rejected;
3. small raw reversal tolerated;
4. material raw reversal rejected even when the trace passed to `classify_lap()` is already monotonic-repaired;
5. all quality fixtures explicitly construct `RawCoverage`.

## Task 4 — Frozen geometry and alignment

### Geometry source manifest

`config/circuit-geometry-sources.yaml` is human-authored and includes, for every circuit:

```yaml
geometry: data/geometry/example.csv
geometry_format: csv
source: named-source
source_license: license-id
```

Spa uses `data/reference/spa-reference.json` with `geometry_format: spa-reference-json`. The implementation must not invent checksums in this source declaration.

A deterministic freeze command reads each exact file and generates `config/circuits.yaml` with:

```yaml
geometry: <root-relative path>
geometry_format: <supported adapter>
source: <immutable source name>
source_license: <license>
checksum: <sha256 of exact file bytes>
```

`GeometrySource.from_manifest(row, calibration_root)` requires all five fields, validates the digest syntax, and resolves paths relative to the `calibration/` root. `load_canonical_track()` calls `verify_geometry_source()` before CSV/JSON parsing. A content mismatch raises `ValueError` containing `geometry checksum mismatch`.

Every `CanonicalTrack` constructor, including the alignment fixture, supplies `geometry_source`. Resampled trace rows retain:

- `geometry_checksum`
- `geometry_source_name`
- `geometry_source_license`
- `geometry_format`

The corpus source-checksum map also contains `geometry:<circuit_id>`.

### Alignment

Project source `x/y` to nearest canonical geometry only to estimate `progress_raw`. Measure raw quality first. Then unwrap start/finish crossing, preserve `progress_observed`, apply bounded monotonic repair to the downstream `progress`, derive canonical distance, and resample at 5 m. Continuous channels interpolate; discrete channels use previous-observation semantics; geometry and sectors come from the canonical track.

Required tests:

1. start/finish unwrap remains monotonic;
2. coordinate projection maps known fixture points;
3. 5 m resampling uses correct continuous and discrete semantics;
4. a middle-60% trace remains 60% covered and cannot be stretched into eligibility;
5. freeze populates `geometry_format` and the exact file checksum;
6. tampering is rejected before geometry parsing;
7. canonical fixture provenance is present on the returned track and trace.

## Task 5 — Driving phases

Detect ordered non-zero-length phases within validated complex windows. Braking phases are omitted where braking onset is not observed. Braking onset is stored as both absolute canonical distance and offset from `complex_start_distance_m`. Full power begins at the detected full-power sample and ends at the complex-window end. Tests cover a braking hairpin and a flat high-speed complex.

`config/complexes.yaml` is derived for every configured canonical track, then receives only explicit reviewed overrides. Validation rejects no-complex circuits, overlap, out-of-range apexes, or windows beyond track length.

## Task 6 — Features and paired outcomes

Feature extraction uses canonical geometry and fixed downstream distances. It retains coherent lap/profile keys, season, team, driver, circuit, complex, phase, geometry metrics, quality weight, and nullable braking onset.

Pairing keys are:

```text
circuit_id, complex_id, phase_type, team_name, driver_acronym, archetype, sector
```

Dense measures and geometry use quality-weighted observed means. Braking onset uses a dedicated observed-only weighted mean:

```python
observed = group[column].notna()
if not observed.any():
    return float("nan")
return np.average(group.loc[observed, column], weights=group.loc[observed, "quality_weight"])
```

After the 2026/2025 merge:

```python
paired["braking_onset_pair_observed"] = (
    paired["braking_onset_from_complex_start_m_treatment"].notna()
    & paired["braking_onset_from_complex_start_m_reference"].notna()
)
paired["delta_braking_onset_from_complex_start_m"] = (
    paired["braking_onset_from_complex_start_m_treatment"]
    - paired["braking_onset_from_complex_start_m_reference"]
).where(paired["braking_onset_pair_observed"])
```

Plan B fits the onset outcome only where `braking_onset_pair_observed` is true. Rows with missing onset remain eligible for other outcomes. Tests prove no zero-fill or implicit imputation occurs.

## Task 7 — Deterministic corpus writing and exact verification

The writer deterministically sorts and writes exactly:

```python
REQUIRED_CORPUS_ARTIFACTS = frozenset({
    "laps.parquet",
    "aligned-traces.parquet",
    "phases.parquet",
    "features.parquet",
})
```

`provenance.json` records the schema, generation timestamp, source cutoff, circuits, seasons, row counts, source checksums, geometry checksums, the three eligibility/selection manifest checksums, and all four artifact checksums.

`verify_corpus(output)` must:

1. parse and validate `provenance.json`;
2. require `set(manifest.artifact_checksums) == REQUIRED_CORPUS_ARTIFACTS`;
3. require `{p.name for p in output.glob("*.parquet")} == REQUIRED_CORPUS_ARTIFACTS`;
4. require every named path to be a regular file;
5. hash every required file and compare it with the manifest;
6. fail on a missing declaration, missing file, undeclared extra Parquet file, or mismatch.

Fixture corpus construction receives and hashes fixture copies of:

- `source-eligibility.json`
- `circuit-year-eligibility.json`
- `lap-selection.json`

Required tests build twice and compare checksums, remove a required manifest entry, add a rogue Parquet file, corrupt each required artifact in turn, and verify all failures are closed.

## Task 8 — Fixture and live orchestration

### Timestamp normalizer

All pipeline boundaries use:

```python
def normalize_datetime(value: str | datetime, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError(f"{field_name} must be an ISO string or datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)
```

Use it for YAML window starts/ends, lap starts, weather/control timestamps, session source cutoffs, persisted lap timestamps, source retrieval timestamps, live `generated_at`, and CLI parsing. Do not call `.replace("Z", "+00:00")` on a value that may already be a `datetime`.

Tests parameterize an ISO string and an already-parsed aware `datetime`, and reject a naive `datetime` and unsupported types.

### Build sequence

For each event/session:

1. normalize and resolve the circuit-unique session;
2. fetch and cache session metadata, laps, drivers, weather, and race control;
3. select coherent candidate laps with explicit fallback metadata;
4. fetch immutable car-data/location bundles per lap;
5. couple observed channels by source time;
6. load and checksum-verify canonical geometry;
7. project observed locations and compute `RawCoverage`;
8. align/repair only after raw metrics exist;
9. classify using `LapContext(raw_coverage=...)`;
10. discard ineligible laps;
11. resample accepted laps with immutable geometry provenance;
12. derive phases and features;
13. write the exact corpus and provenance manifests.

`build_corpus_from_fixture_bundle()` requires all three manifest paths and passes their checksums to `build_corpus_from_bundles()`. Its test call must supply `eligibility_path`, `circuit_year_eligibility_path`, and `lap_selection_path`; no signature/call-site mismatch is permitted.

`build_corpus_from_bundles()` resolves geometry with `calibration_root=circuits_config.parent.parent`, records `geometry:<circuit_id>`, and uses normalized session dates for `source_cutoff`.

The live CLI requires explicit `--generated-at`; it is normalized before the client or writer receives it. Unit tests exercise fixture orchestration and command help only.

## Horizontal consistency checklist

Before implementation commits, search all producers and consumers for these exact names and contracts:

- `RawCoverage` definition/import and every `LapContext(...)` constructor;
- `maximum_gap_s` and `maximum_progress_reversal` producer, classifier, schema, fixtures, and persisted rows;
- `geometry_format`, `checksum`, `GeometrySource`, `geometry_source`, freeze command, loader, fixture constructors, trace metadata, and corpus source checksums;
- nullable `braking_onset_from_complex_start_m`, aggregate helper, observation mask, paired delta, tests, and Plan B filter;
- `REQUIRED_CORPUS_ARTIFACTS`, writer, manifest, verifier, fixture builder, CLI, and completion command;
- `normalize_datetime` and every event/source/persisted timestamp boundary;
- event identity fields and season-specific windows;
- all fixture-builder signatures and call sites.

Reject stale aliases or duplicate contradictory definitions. Do not let a sample snippet override the normative contracts above.

## Verification sequence

Targeted checks:

```bash
cd calibration
python -m pytest -q \
  tests/test_schemas.py \
  tests/test_cache.py \
  tests/test_openf1.py \
  tests/test_eligibility.py \
  tests/test_quality.py \
  tests/test_alignment.py \
  tests/test_phases.py \
  tests/test_features.py \
  tests/test_corpus.py \
  tests/test_pipeline.py

spa-calibration geometry freeze-manifest \
  --sources config/circuit-geometry-sources.yaml \
  --output config/circuits.yaml
spa-calibration geometry validate --circuits config/circuits.yaml

spa-calibration corpus build-fixture \
  --fixtures data/fixtures \
  --output /tmp/spa-corpus-a
spa-calibration corpus build-fixture \
  --fixtures data/fixtures \
  --output /tmp/spa-corpus-b
cmp /tmp/spa-corpus-a/provenance.json /tmp/spa-corpus-b/provenance.json
spa-calibration corpus verify --output /tmp/spa-corpus-a
spa-calibration corpus refresh --help
```

Repository integration also runs the repository's canonical verification command. Executable success confirms software-contract implementation only; it does not by itself validate a scientific model or authorize release.

## Completion criteria

Plan A is complete only when:

- every targeted and canonical test passes without a network request;
- every configured geometry file matches its frozen checksum before parsing;
- quality acceptance uses raw observed gaps and reversals;
- every accepted lap retains raw coverage and immutable geometry provenance;
- nullable braking onset is never imputed and paired observation status is explicit;
- the manifest and output directory contain exactly the required four Parquet artifacts and every checksum matches;
- 2024 remains a control and 2025–2026 treatment pairing remains coherent;
- malformed, stale, incomplete, or unverified downstream prediction artifacts remain calibration pending;
- the provisional `1:40.4` estimate remains suppressed pending all approved release gates.
