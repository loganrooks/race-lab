# Spa Calibration Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, provenance-rich paired 2025–2026 qualifying telemetry corpus aligned to canonical circuit geometry and segmented into reusable driving phases and corner features.

**Architecture:** A Python package under `calibration/` owns source retrieval, caching, quality classification, geometry alignment, phase segmentation, feature extraction, and corpus manifests. Raw API responses are immutable content-addressed JSON; normalized and derived tables are Parquet. Live refresh commands are separate from fixture-backed tests, and every downstream row retains a source lap identifier and quality flags.

**Tech Stack:** Python 3.11+, Pydantic, httpx, PyYAML, NumPy, pandas, SciPy, PyArrow, scikit-learn, Typer, orjson, pytest, respx, Hypothesis.

## Global Constraints

- Schema version is exactly `spa-calibration-corpus/v1`.
- Source refreshes must never run during unit tests.
- Raw source responses are immutable and addressed by SHA-256.
- Prefer dry Q3 laps from multiple competitive cars; fall back to another qualifying segment only with explicit flags.
- OpenF1 location is used for progress alignment, not measured lateral racing-line placement.
- Every lap retains source, session key, driver, team, season, session, lap number, retrieval date, license, query, sample counts, checksums, and limitations.
- Exclude pit-out, aborted, wet/mixed, race-control-affected, feed-gap, non-monotonic, and materially incomplete laps under deterministic rules.
- Use 2024 only as a control season; do not mix it into the 2025→2026 treatment label.
- All generated tables sort deterministically before writing.


## Mandatory Review Resolutions

The following contracts are normative for every task and snippet in this plan.

- **Source feasibility first:** `calibration/config/source-eligibility.yaml` declares channel semantics, units, nominal and observed sampling, anomalies, licensing, derivable features, prohibited claims, and eligibility. `calibration/manifests/circuit-year-eligibility.json` records the evaluated result for every circuit-season-session. No downstream feature is produced unless its declared requirements pass.
- **Circuit-unique sessions:** each event row supplies `meeting_key` when frozen, otherwise `meeting_name`, `circuit_short_name`, and a bounded event-date window. Resolution must return exactly one candidate or fail; country alone is never sufficient.
- **Qualifying selection:** selection is Q3/SQ3 first per coherent car-driver profile. Q2/SQ2 and then Q1/SQ1 are permitted only by declared ordered fallback, with `selection_fallback`, `fallback_reason`, and source segment retained in every lap and manifest.
- **Raw coverage precedes resampling:** completeness, source gaps, reversals, and channel coverage are computed on coupled/aligned source rows before a full canonical grid is created. Resampling cannot upgrade an ineligible lap.
- **Canonical geometry is immutable:** resampled telemetry receives geometry by joining/interpolating from the configured canonical track. Source coordinates never overwrite canonical distance, curvature, gradient, sector, widths, or provenance.
- **Bounded progress:** every output has `0 <= progress <= 1`, is monotonic, contains the exact zero and track-length endpoints once, and never extends beyond canonical length.
- **Phase semantics:** braking onset is an absolute canonical distance plus a corner-relative offset from `complex_start_distance_m`; full-power begins at the detected full-power sample and ends at the complex window end. Zero-length phases are invalid.
- **Lap coherence:** all validation identifiers include lap/profile keys so Plan B aggregates phases into coherent laps, not fleet-wide sums.

---

## File Map

```text
calibration/
├── pyproject.toml
├── README.md
├── config/
│   ├── events.yaml
│   ├── circuits.yaml
│   ├── source-eligibility.yaml
│   └── feature-requirements.yaml
├── data/
│   ├── raw/openf1/
│   ├── geometry/
│   ├── fixtures/
│   └── processed/
├── manifests/
│   ├── source-eligibility.json
│   ├── circuit-year-eligibility.json
│   └── lap-selection.json
├── src/spa_calibration/
│   ├── __init__.py
│   ├── schemas.py
│   ├── hashing.py
│   ├── cache.py
│   ├── openf1.py
│   ├── quality.py
│   ├── geometry.py
│   ├── alignment.py
│   ├── phases.py
│   ├── features.py
│   ├── corpus.py
│   └── cli.py
└── tests/
    ├── test_schemas.py
    ├── test_cache.py
    ├── test_openf1.py
    ├── test_quality.py
    ├── test_alignment.py
    ├── test_phases.py
    ├── test_features.py
    └── test_corpus.py
```

## Shared Interfaces

```python
@dataclass(frozen=True)
class LapKey:
    season: int
    meeting_key: int
    session_key: int
    driver_number: int
    lap_number: int

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

@dataclass(frozen=True)
class AlignedLap:
    lap: LapRecord
    trace: pd.DataFrame
    quality: LapQuality
```

---


### Task 0: Establish source feasibility and circuit-year eligibility

**Files:**
- Create: `calibration/config/source-eligibility.yaml`
- Create: `calibration/config/feature-requirements.yaml`
- Create: `calibration/src/spa_calibration/eligibility.py`
- Create: `calibration/tests/test_eligibility.py`
- Generate: `calibration/manifests/source-eligibility.json`
- Generate: `calibration/manifests/circuit-year-eligibility.json`

**Interfaces:**
- Produces `SourceEligibilityManifest`, `CircuitYearEligibility`, `EligibilityEvaluation.required_channels()`, and a deterministic feasibility-spike report.
- Eligibility levels are `excluded`, `sector-only`, `phase`, and `corner`; downstream modules request a level and fail closed when it is unavailable.
- Required varied-circuit spike: Silverstone/Suzuka (high speed), Montreal (heavy braking), Spielberg (elevation), Barcelona (sustained load), Miami (traction/long straight).

- [ ] **Step 1: Write failing manifest tests** that reject unknown units, missing licensing, missing observed resolution, and a feature declared eligible without all required channels.
- [ ] **Step 2: Run `python -m pytest tests/test_eligibility.py -q` and verify RED.**
- [ ] **Step 3: Implement versioned YAML input and JSON evaluated manifests.** Every circuit-year-session row records source query identity, adapter version, channels, raw sample counts, median/p95 sampling interval, gaps, quantization, semantic delays, derivable features, prohibited claims, redistribution policy, quality flags, and eligibility level.
- [ ] **Step 4: Run the frozen feasibility fixtures and verify GREEN.**
- [ ] **Step 5: Commit the executable eligibility contract.**

---
### Task 1: Bootstrap the calibration package and versioned schemas

**Files:**
- Create: `calibration/pyproject.toml`
- Create: `calibration/src/spa_calibration/__init__.py`
- Create: `calibration/src/spa_calibration/schemas.py`
- Create: `calibration/tests/test_schemas.py`

**Interfaces:**
- Consumes: none.
- Produces: `LapKey`, `SourceQuery`, `LapRecord`, `LapQuality`, `PhaseRecord`, `FeatureRecord`, `CorpusManifest`, and `model_dump_json_sorted()`.

- [ ] **Step 1: Write the failing schema tests**

```python
# calibration/tests/test_schemas.py
from datetime import UTC, date, datetime, time
import pytest
from pydantic import ValidationError
from spa_calibration.schemas import CorpusManifest, LapKey, LapQuality, LapRecord


def test_lap_key_is_stable_and_stringifiable() -> None:
    key = LapKey(season=2026, meeting_key=1300, session_key=9901, driver_number=4, lap_number=18)
    assert key.slug == "2026-1300-9901-4-18"


def test_lap_record_rejects_non_qualifying_session() -> None:
    with pytest.raises(ValidationError):
        LapRecord(
            key=LapKey(season=2026, meeting_key=1, session_key=2, driver_number=4, lap_number=3),
            circuit_id="silverstone",
            session_name="Race",
            session_segment="R",
            driver_acronym="NOR",
            driver_name="Lando Norris",
            team_name="McLaren",
            lap_time_s=95.2,
            date_start=datetime(2026, 7, 4, tzinfo=UTC),
            source_name="OpenF1",
            source_license="CC BY-NC-SA 4.0",
            source_query="session_key=2&driver_number=4",
            retrieved_at=datetime(2026, 7, 14, tzinfo=UTC),
            raw_checksum="a" * 64,
        )


def test_manifest_requires_matching_counts_and_checksums() -> None:
    manifest = CorpusManifest(
        generated_at=datetime(2026, 7, 14, tzinfo=UTC),
        source_cutoff=datetime(2026, 7, 13, tzinfo=UTC),
        circuits=["silverstone"],
        seasons=[2025, 2026],
        lap_count=2,
        trace_point_count=100,
        phase_count=18,
        feature_count=18,
        source_checksums={"openf1": "b" * 64},
        artifact_checksums={"features.parquet": "c" * 64},
    )
    assert manifest.schema_version == "spa-calibration-corpus/v1"


def test_quality_score_is_bounded() -> None:
    assert LapQuality(score=0.75).score == 0.75
    with pytest.raises(ValidationError):
        LapQuality(score=1.1)
```

- [ ] **Step 2: Run the schema tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_schemas.py -q
```

Expected:

```text
ERROR collecting tests/test_schemas.py
ModuleNotFoundError: No module named 'spa_calibration'
```

- [ ] **Step 3: Add package metadata and exact schema implementation**

```toml
# calibration/pyproject.toml
[build-system]
requires = ["hatchling>=1.25,<2"]
build-backend = "hatchling.build"

[project]
name = "spa-calibration"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27,<1",
  "numpy>=2.1,<3",
  "orjson>=3.10,<4",
  "pandas>=2.2,<3",
  "pyarrow>=17,<21",
  "pydantic>=2.9,<3",
  "pyyaml>=6.0,<7",
  "scikit-learn>=1.5,<2",
  "scipy>=1.14,<2",
  "typer>=0.12,<1",
]

[project.optional-dependencies]
dev = [
  "hypothesis>=6.112,<7",
  "pytest>=8.3,<9",
  "pytest-cov>=5,<7",
  "pytest-asyncio>=0.24,<1",
  "respx>=0.21,<1",
]

[project.scripts]
spa-calibration = "spa_calibration.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/spa_calibration"]

[tool.pytest.ini_options]
addopts = "-ra --strict-markers"
testpaths = ["tests"]
```

```python
# calibration/src/spa_calibration/schemas.py
from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
QualifyingSession = Literal["Qualifying", "Sprint Qualifying"]
QualifyingSegment = Literal["Q1", "Q2", "Q3", "SQ1", "SQ2", "SQ3", "UNKNOWN"]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class LapKey(FrozenModel):
    season: int = Field(ge=2024, le=2100)
    meeting_key: int = Field(gt=0)
    session_key: int = Field(gt=0)
    driver_number: int = Field(gt=0, le=99)
    lap_number: int = Field(gt=0)

    @property
    def slug(self) -> str:
        return "-".join(map(str, (self.season, self.meeting_key, self.session_key, self.driver_number, self.lap_number)))


class LapQuality(FrozenModel):
    score: float = Field(ge=0, le=1)
    accepted: bool = False
    flags: tuple[str, ...] = ()
    raw_progress_start: float = Field(default=0, ge=0, le=1)
    raw_progress_end: float = Field(default=0, ge=0, le=1)
    raw_coverage_ratio: float = Field(default=0, ge=0, le=1)
    raw_channel_coverage: dict[str, float] = Field(default_factory=dict)
    maximum_gap_s: float = Field(default=0, ge=0)
    maximum_progress_reversal: float = Field(default=0, ge=0)
    weather: Literal["dry", "wet", "mixed", "unknown"] = "unknown"


class LapRecord(FrozenModel):
    key: LapKey
    circuit_id: str = Field(pattern=r"^[a-z0-9-]+$")
    session_name: QualifyingSession
    session_segment: QualifyingSegment
    selection_fallback: bool = False
    fallback_reason: str | None = None
    driver_acronym: str = Field(min_length=2, max_length=4)
    driver_name: str = Field(min_length=2)
    team_name: str = Field(min_length=2)
    lap_time_s: float = Field(gt=60, lt=240)
    date_start: datetime
    source_name: Literal["OpenF1"]
    source_license: Literal["CC BY-NC-SA 4.0"]
    source_query: str = Field(min_length=3)
    retrieved_at: datetime
    raw_checksum: Sha256
    quality: LapQuality = LapQuality(score=0)


class PhaseRecord(FrozenModel):
    lap_slug: str
    circuit_id: str
    complex_id: str
    phase_index: int = Field(ge=0)
    phase_type: Literal[
        "approach", "braking-onset", "peak-braking", "brake-release",
        "turn-in", "apex", "throttle-pickup", "exit-acceleration", "full-power"
    ]
    start_distance_m: float = Field(ge=0)
    end_distance_m: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    detector_version: str

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "PhaseRecord":
        if self.end_distance_m <= self.start_distance_m:
            raise ValueError("phase end must be greater than phase start")
        return self


class FeatureRecord(FrozenModel):
    lap_slug: str
    circuit_id: str
    season: int
    team_name: str
    driver_acronym: str
    complex_id: str
    phase_type: str
    archetype: str
    sector: int = Field(ge=1, le=3)
    track_length_m: float = Field(gt=0)
    complex_start_distance_m: float = Field(ge=0)
    complex_end_distance_m: float = Field(gt=0)
    phase_start_distance_m: float = Field(ge=0)
    phase_end_distance_m: float = Field(gt=0)
    apex_distance_m: float = Field(ge=0)
    phase_time_s: float = Field(gt=0)
    entry_speed_kph: float = Field(ge=0)
    minimum_speed_kph: float = Field(ge=0)
    exit_speed_50m_kph: float = Field(ge=0)
    exit_speed_100m_kph: float = Field(ge=0)
    braking_onset_distance_m: float | None
    braking_onset_from_complex_start_m: float | None
    braking_length_m: float = Field(ge=0)
    throttle_pickup_m: float
    full_throttle_fraction: float = Field(ge=0, le=1)
    mean_curvature_per_m: float
    peak_curvature_per_m: float
    curvature_change_per_m2: float
    gradient_mean: float
    entry_straight_m: float = Field(ge=0)
    exit_straight_m: float = Field(ge=0)
    sustained_load_s: float = Field(ge=0)
    quality_weight: float = Field(gt=0, le=1)


class CorpusManifest(FrozenModel):
    schema_version: Literal["spa-calibration-corpus/v1"] = "spa-calibration-corpus/v1"
    generated_at: datetime
    source_cutoff: datetime
    circuits: list[str]
    seasons: list[int]
    lap_count: int = Field(ge=0)
    trace_point_count: int = Field(ge=0)
    phase_count: int = Field(ge=0)
    feature_count: int = Field(ge=0)
    source_checksums: dict[str, Sha256]
    artifact_checksums: dict[str, Sha256]
    source_eligibility_checksum: Sha256
    circuit_year_eligibility_checksum: Sha256
    lap_selection_checksum: Sha256
```

```python
# calibration/src/spa_calibration/__init__.py
from .schemas import CorpusManifest, FeatureRecord, LapKey, LapQuality, LapRecord, PhaseRecord

__all__ = ["CorpusManifest", "FeatureRecord", "LapKey", "LapQuality", "LapRecord", "PhaseRecord"]
```

- [ ] **Step 4: Install the package and verify GREEN**

Run:

```bash
cd calibration
python -m pip install -e '.[dev]'
python -m pytest tests/test_schemas.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit the package and schemas**

```bash
git add calibration/pyproject.toml calibration/src/spa_calibration calibration/tests/test_schemas.py
git commit -m "feat(calibration-data): define versioned corpus schemas"
```

---

### Task 2: Add immutable content-addressed caching and deterministic OpenF1 retrieval

**Files:**
- Create: `calibration/src/spa_calibration/hashing.py`
- Create: `calibration/src/spa_calibration/cache.py`
- Create: `calibration/src/spa_calibration/openf1.py`
- Create: `calibration/config/events.yaml`
- Create: `calibration/tests/test_cache.py`
- Create: `calibration/tests/test_openf1.py`
- Create: `calibration/data/fixtures/openf1-session.json`
- Create: `calibration/data/fixtures/openf1-laps.json`

**Interfaces:**
- Consumes: Task 1 `LapKey`, `LapRecord`.
- Produces: `ContentAddressedCache`, `OpenF1Client`, `EventSpec`, `CachedResponse`, and `resolve_session()`.

- [ ] **Step 1: Write failing cache and retrieval tests**

```python
# calibration/tests/test_cache.py
from spa_calibration.cache import ContentAddressedCache


def test_same_payload_has_same_content_path(tmp_path) -> None:
    cache = ContentAddressedCache(tmp_path)
    first = cache.put_json({"b": 2, "a": 1})
    second = cache.put_json({"a": 1, "b": 2})
    assert first.checksum == second.checksum
    assert first.path == second.path
    assert first.path.read_bytes() == b'{"a":1,"b":2}'
```

```python
# calibration/tests/test_openf1.py
from datetime import UTC, datetime
import httpx
import pytest
import respx
from spa_calibration.cache import ContentAddressedCache
from spa_calibration.openf1 import EventSpec, OpenF1Client


@pytest.mark.asyncio
@respx.mock
async def test_client_caches_exact_query_and_payload(tmp_path) -> None:
    route = respx.get("https://api.openf1.org/v1/sessions", params={
        "year": "2026", "country_name": "Great Britain", "session_name": "Qualifying"
    }).mock(return_value=httpx.Response(200, json=[{
        "meeting_key": 1300,
        "session_key": 9901,
        "session_name": "Qualifying",
        "date_start": "2026-07-04T14:00:00+00:00"
    }]))
    client = OpenF1Client(cache=ContentAddressedCache(tmp_path), retrieved_at=datetime(2026, 7, 14, tzinfo=UTC))
    result = await client.resolve_session(EventSpec(season=2026, circuit_id="silverstone", country_name="Great Britain", session_name="Qualifying", meeting_name="British Grand Prix", circuit_short_name="Silverstone", event_date_start=datetime(2026, 7, 3, tzinfo=UTC), event_date_end=datetime(2026, 7, 6, tzinfo=UTC)))
    assert result.session_key == 9901
    assert route.call_count == 1
    assert result.source.query == "country_name=Great+Britain&session_name=Qualifying&year=2026"
    assert len(result.source.checksum) == 64
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_cache.py tests/test_openf1.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.cache'
```

- [ ] **Step 3: Implement canonical hashing, cache, client, and event manifest**

```python
# calibration/src/spa_calibration/hashing.py
from hashlib import sha256
import orjson


def canonical_json_bytes(value: object) -> bytes:
    return orjson.dumps(value, option=orjson.OPT_SORT_KEYS)


def sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()
```

```python
# calibration/src/spa_calibration/cache.py
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import orjson
from .hashing import canonical_json_bytes, sha256_bytes


@dataclass(frozen=True)
class CachedObject:
    checksum: str
    path: Path


class ContentAddressedCache:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def put_json(self, value: object) -> CachedObject:
        payload = canonical_json_bytes(value)
        checksum = sha256_bytes(payload)
        path = self.root / checksum[:2] / f"{checksum}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(payload)
        return CachedObject(checksum=checksum, path=path)

    def read_json(self, checksum: str) -> object:
        path = self.root / checksum[:2] / f"{checksum}.json"
        return orjson.loads(path.read_bytes())
```

```python
# calibration/src/spa_calibration/openf1.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from urllib.parse import urlencode
import asyncio
import httpx
from pydantic import BaseModel, ConfigDict, model_validator
from .cache import ContentAddressedCache


class EventSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    season: int
    circuit_id: str
    country_name: str
    session_name: Literal["Qualifying", "Sprint Qualifying"]
    meeting_key: int | None = None
    meeting_name: str | None = None
    circuit_short_name: str | None = None
    event_date_start: datetime | None = None
    event_date_end: datetime | None = None

    @model_validator(mode="after")
    def require_circuit_unique_identity(self) -> "EventSpec":
        fallback = (
            self.meeting_name,
            self.circuit_short_name,
            self.event_date_start,
            self.event_date_end,
        )
        if self.meeting_key is None and any(value is None for value in fallback):
            raise ValueError(
                "event requires meeting_key or meeting_name, circuit_short_name, "
                "event_date_start, and event_date_end"
            )
        if self.event_date_start and self.event_date_end and self.event_date_end <= self.event_date_start:
            raise ValueError("event_date_end must follow event_date_start")
        return self


@dataclass(frozen=True)
class SourceEnvelope:
    endpoint: str
    query: str
    checksum: str
    retrieved_at: datetime
    license: str = "CC BY-NC-SA 4.0"


@dataclass(frozen=True)
class SessionResolution:
    meeting_key: int
    session_key: int
    date_start: datetime
    source: SourceEnvelope


class OpenF1Client:
    def __init__(
        self,
        cache: ContentAddressedCache,
        retrieved_at: datetime,
        base_url: str = "https://api.openf1.org/v1",
        minimum_interval_s: float = 1.05,
    ) -> None:
        self.cache = cache
        self.retrieved_at = retrieved_at
        self.base_url = base_url.rstrip("/")
        self.minimum_interval_s = minimum_interval_s
        self._last_request = 0.0

    async def get(self, endpoint: str, params: dict[str, object]) -> tuple[list[dict], SourceEnvelope]:
        loop = asyncio.get_running_loop()
        delay = self.minimum_interval_s - (loop.time() - self._last_request)
        if delay > 0:
            await asyncio.sleep(delay)
        query = urlencode(sorted((key, str(value)) for key, value in params.items()))
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", params=params, headers={"accept": "application/json"})
        self._last_request = loop.time()
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError(f"OpenF1 {endpoint} returned {type(payload).__name__}, expected list")
        cached = self.cache.put_json(payload)
        return payload, SourceEnvelope(endpoint, query, cached.checksum, self.retrieved_at)

    async def resolve_session(self, spec: EventSpec) -> SessionResolution:
        params: dict[str, object] = {"year": spec.season, "session_name": spec.session_name}
        if spec.meeting_key is not None:
            params["meeting_key"] = spec.meeting_key
        else:
            params["country_name"] = spec.country_name
        rows, source = await self.get("sessions", params)
        candidates = [
            row for row in rows
            if row.get("session_name") == spec.session_name
            and (spec.meeting_key is not None or spec.event_date_start <= datetime.fromisoformat(row["date_start"]) <= spec.event_date_end)
            and (spec.meeting_key is not None or row.get("meeting_name") == spec.meeting_name)
            and (spec.meeting_key is not None or row.get("circuit_short_name") == spec.circuit_short_name)
        ]
        if len(candidates) != 1:
            raise LookupError(f"Expected one circuit-unique session for {spec.circuit_id}, found {len(candidates)}")
        row = candidates[0]
        return SessionResolution(
            meeting_key=int(row["meeting_key"]),
            session_key=int(row["session_key"]),
            date_start=datetime.fromisoformat(row["date_start"]),
            source=source,
        )
```

```yaml
# calibration/config/events.yaml
seasons: [2024, 2025, 2026]
sessions: [Qualifying]
events:
  - circuit_id: melbourne
    country_name: Australia
    meeting_name: Australian Grand Prix
    circuit_short_name: Melbourne
    event_date_windows:
      2024: {start: 2024-03-01T00:00:00Z, end: 2024-04-01T00:00:00Z}
      2025: {start: 2025-03-01T00:00:00Z, end: 2025-04-01T00:00:00Z}
      2026: {start: 2026-03-01T00:00:00Z, end: 2026-04-01T00:00:00Z}
  - circuit_id: shanghai
    country_name: China
    meeting_name: Chinese Grand Prix
    circuit_short_name: Shanghai
    event_date_windows:
      2024: {start: 2024-04-01T00:00:00Z, end: 2024-05-01T00:00:00Z}
      2025: {start: 2025-03-01T00:00:00Z, end: 2025-05-01T00:00:00Z}
      2026: {start: 2026-03-01T00:00:00Z, end: 2026-05-01T00:00:00Z}
  - circuit_id: suzuka
    country_name: Japan
    meeting_name: Japanese Grand Prix
    circuit_short_name: Suzuka
    event_date_windows:
      2024: {start: 2024-03-15T00:00:00Z, end: 2024-05-01T00:00:00Z}
      2025: {start: 2025-03-15T00:00:00Z, end: 2025-05-01T00:00:00Z}
      2026: {start: 2026-03-01T00:00:00Z, end: 2026-05-01T00:00:00Z}
  - circuit_id: miami
    country_name: United States
    meeting_name: Miami Grand Prix
    circuit_short_name: Miami
    event_date_windows:
      2024: {start: 2024-04-15T00:00:00Z, end: 2024-06-01T00:00:00Z}
      2025: {start: 2025-04-15T00:00:00Z, end: 2025-06-01T00:00:00Z}
      2026: {start: 2026-04-15T00:00:00Z, end: 2026-06-01T00:00:00Z}
  - circuit_id: montreal
    country_name: Canada
    meeting_name: Canadian Grand Prix
    circuit_short_name: Montreal
    event_date_windows:
      2024: {start: 2024-05-15T00:00:00Z, end: 2024-07-01T00:00:00Z}
      2025: {start: 2025-05-15T00:00:00Z, end: 2025-07-01T00:00:00Z}
      2026: {start: 2026-05-15T00:00:00Z, end: 2026-07-01T00:00:00Z}
  - circuit_id: monaco
    country_name: Monaco
    meeting_name: Monaco Grand Prix
    circuit_short_name: Monaco
    event_date_windows:
      2024: {start: 2024-05-01T00:00:00Z, end: 2024-06-15T00:00:00Z}
      2025: {start: 2025-05-01T00:00:00Z, end: 2025-06-15T00:00:00Z}
      2026: {start: 2026-05-01T00:00:00Z, end: 2026-06-15T00:00:00Z}
  - circuit_id: barcelona
    country_name: Spain
    meeting_name: Spanish Grand Prix
    circuit_short_name: Barcelona
    event_date_windows:
      2024: {start: 2024-05-15T00:00:00Z, end: 2024-07-15T00:00:00Z}
      2025: {start: 2025-05-15T00:00:00Z, end: 2025-07-15T00:00:00Z}
      2026: {start: 2026-05-15T00:00:00Z, end: 2026-07-15T00:00:00Z}
  - circuit_id: spielberg
    country_name: Austria
    meeting_name: Austrian Grand Prix
    circuit_short_name: Spielberg
    event_date_windows:
      2024: {start: 2024-06-01T00:00:00Z, end: 2024-07-31T00:00:00Z}
      2025: {start: 2025-06-01T00:00:00Z, end: 2025-07-31T00:00:00Z}
      2026: {start: 2026-06-01T00:00:00Z, end: 2026-07-31T00:00:00Z}
  - circuit_id: silverstone
    country_name: Great Britain
    meeting_name: British Grand Prix
    circuit_short_name: Silverstone
    event_date_windows:
      2024: {start: 2024-06-15T00:00:00Z, end: 2024-08-01T00:00:00Z}
      2025: {start: 2025-06-15T00:00:00Z, end: 2025-08-01T00:00:00Z}
      2026: {start: 2026-06-15T00:00:00Z, end: 2026-08-01T00:00:00Z}
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
cd calibration
python -m pytest tests/test_cache.py tests/test_openf1.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit retrieval and cache**

```bash
git add calibration/src/spa_calibration/{hashing,cache,openf1}.py calibration/config/events.yaml calibration/tests/test_cache.py calibration/tests/test_openf1.py calibration/data/fixtures
git commit -m "feat(calibration-data): add deterministic OpenF1 cache"
```

---

### Task 3: Implement deterministic lap quality classification and provenance rows

**Files:**
- Create: `calibration/src/spa_calibration/quality.py`
- Create: `calibration/tests/test_quality.py`
- Create: `calibration/data/fixtures/lap-quality-clean.json`
- Create: `calibration/data/fixtures/lap-quality-yellow.json`

**Interfaces:**
- Consumes: OpenF1 lap, car-data, location, weather, and race-control rows.
- Produces: `classify_lap(lap, channels, context) -> LapQuality` and `select_candidate_laps(...) -> list[LapRecord]`.

- [ ] **Step 1: Write failing quality tests with exact thresholds**

```python
# calibration/tests/test_quality.py
import pandas as pd
from spa_calibration.quality import LapContext, RawCoverage, classify_lap


def complete_raw_coverage(*, maximum_gap_s: float = 0.27, maximum_progress_reversal: float = 0.0) -> RawCoverage:
    return RawCoverage(
        progress_start=0.0, progress_end=1.0, coverage_ratio=1.0,
        channel_coverage={"speed_kph": 1.0},
        maximum_gap_s=maximum_gap_s,
        maximum_progress_reversal=maximum_progress_reversal,
    )


def clean_trace() -> pd.DataFrame:
    return pd.DataFrame({
        "elapsed_s": [0, 0.27, 0.54, 0.81, 1.08],
        "progress": [0, 0.25, 0.5, 0.75, 1.0],
        "speed_kph": [290, 180, 90, 210, 300],
    })


def test_clean_dry_complete_lap_is_accepted() -> None:
    quality = classify_lap(
        lap_time_s=100.0,
        trace=clean_trace(),
        context=LapContext(rainfall=False, race_control_flags=(), is_pit_out=False, aborted=False, raw_coverage=complete_raw_coverage()),
    )
    assert quality.accepted is True
    assert quality.flags == ()
    assert quality.score >= 0.9


def test_yellow_flag_and_large_gap_are_rejected() -> None:
    trace = clean_trace().copy()
    trace.loc[3, "elapsed_s"] = 4.5
    quality = classify_lap(
        lap_time_s=100.0,
        trace=trace,
        context=LapContext(rainfall=False, race_control_flags=("YELLOW",), is_pit_out=False, aborted=False, raw_coverage=complete_raw_coverage(maximum_gap_s=3.69)),
    )
    assert quality.accepted is False
    assert "race-control" in quality.flags
    assert "feed-gap" in quality.flags


def test_small_progress_noise_is_tolerated_but_reversal_is_not() -> None:
    trace = clean_trace().copy()
    trace["progress"] = [0, .26, .255, .75, 1]
    assert classify_lap(100, trace, LapContext(False, (), False, False, complete_raw_coverage())).accepted
    trace["progress"] = [0, .26, .19, .75, 1]
    result = classify_lap(100, trace, LapContext(False, (), False, False, complete_raw_coverage()))
    assert not result.accepted
    assert "non-monotonic-progress" in result.flags
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_quality.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.quality'
```

- [ ] **Step 3: Implement quality metrics and deterministic acceptance rule**

```python
# calibration/src/spa_calibration/quality.py
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .schemas import LapQuality


@dataclass(frozen=True)
class RawCoverage:
    progress_start: float
    progress_end: float
    coverage_ratio: float
    channel_coverage: dict[str, float]
    maximum_gap_s: float
    maximum_progress_reversal: float


@dataclass(frozen=True)
class LapContext:
    rainfall: bool | None
    race_control_flags: tuple[str, ...]
    is_pit_out: bool
    aborted: bool
    raw_coverage: RawCoverage


def classify_lap(lap_time_s: float, trace: pd.DataFrame, context: LapContext) -> LapQuality:
    elapsed = trace["elapsed_s"].to_numpy(float)
    progress = trace["progress"].to_numpy(float)
    gaps = np.diff(elapsed) if len(elapsed) > 1 else np.array([lap_time_s])
    reversals = np.maximum(0, -np.diff(progress)) if len(progress) > 1 else np.array([1.0])
    coverage = context.raw_coverage.coverage_ratio
    maximum_gap = context.raw_coverage.maximum_gap_s
    maximum_reversal = context.raw_coverage.maximum_progress_reversal

    flags: list[str] = []
    if context.is_pit_out:
        flags.append("pit-out")
    if context.aborted or coverage < 0.94:
        flags.append("incomplete")
    if context.rainfall is True:
        flags.append("wet-or-mixed")
    if any(flag in {"YELLOW", "DOUBLE YELLOW", "RED", "VSC", "SC"} for flag in context.race_control_flags):
        flags.append("race-control")
    if maximum_gap > 1.5:
        flags.append("feed-gap")
    if maximum_reversal > 0.006:
        flags.append("non-monotonic-progress")
    if not 60 < lap_time_s < 240:
        flags.append("invalid-lap-time")

    penalties = {
        "pit-out": .4,
        "incomplete": .5,
        "wet-or-mixed": .5,
        "race-control": .35,
        "feed-gap": .2,
        "non-monotonic-progress": .35,
        "invalid-lap-time": .7,
    }
    score = max(0.0, 1.0 - sum(penalties[flag] for flag in dict.fromkeys(flags)))
    accepted = not flags and coverage >= .94 and maximum_gap <= 1.5 and maximum_reversal <= .006
    weather = "wet" if context.rainfall is True else "dry" if context.rainfall is False else "unknown"
    return LapQuality(
        score=score,
        accepted=accepted,
        flags=tuple(dict.fromkeys(flags)),
        raw_progress_start=context.raw_coverage.progress_start,
        raw_progress_end=context.raw_coverage.progress_end,
        raw_coverage_ratio=coverage,
        raw_channel_coverage=context.raw_coverage.channel_coverage,
        maximum_gap_s=maximum_gap,
        maximum_progress_reversal=maximum_reversal,
        weather=weather,
    )
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
cd calibration
python -m pytest tests/test_quality.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit quality classification**

```bash
git add calibration/src/spa_calibration/quality.py calibration/tests/test_quality.py calibration/data/fixtures/lap-quality-*.json
git commit -m "feat(calibration-data): classify qualifying lap quality"
```

---

### Task 4: Load canonical circuit geometry and align telemetry to monotonic distance

**Files:**
- Create: `calibration/config/circuits.yaml`
- Create: `calibration/src/spa_calibration/geometry.py`
- Create: `calibration/src/spa_calibration/alignment.py`
- Create: `calibration/tests/test_alignment.py`
- Create: `calibration/data/geometry/silverstone.csv`
- Create: `calibration/data/fixtures/silverstone-location.json`

**Interfaces:**
- Consumes: immutable geometry bytes selected by a human-readable source manifest. A generated frozen manifest records the normalized format and SHA-256 digest used by the loader; the loader hashes exact bytes before parsing.
- Produces: `load_canonical_track() -> CanonicalTrack`, `align_lap() -> AlignedLap`, and a distance-indexed trace at 5 m spacing.

- [ ] **Step 1: Write failing alignment tests**

```python
# calibration/tests/test_alignment.py
import numpy as np
import pandas as pd
from spa_calibration.alignment import align_progress_to_track, measure_raw_source_coverage, resample_aligned_trace
import pytest
from spa_calibration.geometry import CanonicalTrack, GeometrySource


def track() -> CanonicalTrack:
    distance = np.linspace(0, 1000, 101)
    return CanonicalTrack(
        circuit_id="test-ring",
        length_m=1000,
        distance_m=distance,
        x_m=np.cos(distance / 1000 * 2 * np.pi) * 100,
        y_m=np.sin(distance / 1000 * 2 * np.pi) * 100,
        elevation_m=np.zeros(101),
        heading_rad=np.linspace(0, 2 * np.pi, 101),
        curvature_per_m=np.full(101, 0.01),
        gradient=np.zeros(101),
        sector=np.ones(101, dtype=np.int16),
        geometry_source=GeometrySource(
            path=Path("data/geometry/test-ring.csv"), format="csv",
            source_name="fixture", source_license="CC0-1.0", checksum="0" * 64,
        ),
    )


def test_alignment_unwraps_start_finish_and_remains_monotonic() -> None:
    location = pd.DataFrame({
        "elapsed_s": [0, 1, 2, 3, 4],
        "progress_raw": [.94, .98, .02, .08, .16],
    })
    aligned = align_progress_to_track(location, track())
    assert np.all(np.diff(aligned["distance_m"]) >= 0)
    assert aligned["distance_m"].iloc[-1] > aligned["distance_m"].iloc[0]


def test_xy_projection_maps_locations_to_track_progress() -> None:
    canonical = track()
    location = pd.DataFrame({
        "elapsed_s": [0, 1, 2],
        "x": [canonical.x_m[10], canonical.x_m[30], canonical.x_m[70]],
        "y": [canonical.y_m[10], canonical.y_m[30], canonical.y_m[70]],
    })
    from spa_calibration.alignment import project_locations_to_track
    projected = project_locations_to_track(location, canonical)
    assert projected.progress_raw.tolist() == [0.1, 0.3, 0.7]


def test_resampling_emits_fixed_distance_grid_and_interpolates_channels() -> None:
    trace = pd.DataFrame({
        "distance_m": [0, 10, 20],
        "elapsed_s": [0, .5, 1],
        "speed_kph": [100, 150, 200],
        "throttle_pct": [0, 50, 100],
        "brake": [1, 0, 0],
        "gear": [2, 3, 4],
    })
    result = resample_aligned_trace(trace, track=track(), spacing_m=5)
    assert result["distance_m"].tolist() == [0, 5, 10, 15, 20]
    assert result.loc[result.distance_m == 5, "speed_kph"].item() == 125
    assert result.loc[result.distance_m == 5, "gear"].item() == 2


def test_middle_sixty_percent_is_not_stretched_to_a_complete_lap() -> None:
    location = pd.DataFrame({
        "elapsed_s": [0, 1, 2, 3],
        "progress_raw": [.20, .40, .60, .80],
        "speed_kph": [200, 210, 220, 230],
    })
    coverage = measure_raw_source_coverage(location, required_channels=("speed_kph",))
    aligned = align_progress_to_track(location, track())
    assert coverage.coverage_ratio == pytest.approx(.60)
    assert aligned.progress.iloc[-1] == pytest.approx(.60)
    assert coverage.coverage_ratio < .94
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_alignment.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.alignment'
```

- [ ] **Step 3: Implement canonical geometry derivation and alignment**

```python
# calibration/src/spa_calibration/geometry.py
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.signal import savgol_filter
from scipy.spatial import cKDTree
from .hashing import sha256_bytes


@dataclass(frozen=True)
class GeometrySource:
    path: Path
    format: str
    source_name: str
    source_license: str
    checksum: str

    @classmethod
    def from_manifest(cls, row: dict[str, object], config_root: Path) -> "GeometrySource":
        required = {"geometry", "geometry_format", "source", "source_license", "checksum"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"geometry manifest missing fields: {sorted(missing)}")
        return cls(
            path=(config_root / str(row["geometry"])).resolve(),
            format=str(row["geometry_format"]),
            source_name=str(row["source"]),
            source_license=str(row["source_license"]),
            checksum=str(row["checksum"]),
        )


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


def _read_geometry_frame(source: GeometrySource) -> pd.DataFrame:
    payload = source.path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != source.checksum:
        raise ValueError(f"geometry checksum mismatch: {actual} != {source.checksum}")
    if source.format == "csv":
        return pd.read_csv(BytesIO(payload))
    if source.format == "spa-reference-json":
        return adapt_spa_reference_geometry_bytes(payload)
    raise ValueError(f"unsupported geometry format: {source.format}")


def load_canonical_track(circuit_id: str, source: GeometrySource) -> CanonicalTrack:
    frame = _read_geometry_frame(source).sort_values("distance_m").reset_index(drop=True)
    required = {"distance_m", "x_m", "y_m", "elevation_m", "sector"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{circuit_id} geometry missing columns: {sorted(missing)}")
    distance = frame.distance_m.to_numpy(float)
    x = frame.x_m.to_numpy(float)
    y = frame.y_m.to_numpy(float)
    elevation = frame.elevation_m.to_numpy(float)
    heading = np.unwrap(np.arctan2(np.gradient(y, distance), np.gradient(x, distance)))
    curvature = savgol_filter(np.gradient(heading, distance), 21, 3, mode="wrap")
    gradient = savgol_filter(np.gradient(elevation, distance), 21, 3, mode="wrap")
    return CanonicalTrack(
        circuit_id=circuit_id,
        length_m=float(distance[-1]),
        distance_m=distance,
        x_m=x,
        y_m=y,
        elevation_m=elevation,
        heading_rad=heading,
        curvature_per_m=curvature,
        gradient=gradient,
        sector=frame.sector.to_numpy(np.int16),
        geometry_source=source,
    )
```

```python
# calibration/src/spa_calibration/alignment.py
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from .geometry import CanonicalTrack
from .quality import RawCoverage


def project_locations_to_track(location: pd.DataFrame, track: CanonicalTrack) -> pd.DataFrame:
    result = location.sort_values("elapsed_s").copy()
    tree = cKDTree(np.column_stack([track.x_m, track.y_m]))
    _, indices = tree.query(result[["x", "y"]].to_numpy(float), k=1)
    raw = track.distance_m[np.asarray(indices, dtype=int)] / track.length_m
    result["progress_raw"] = raw
    return result


def unwrap_observed_progress(progress_raw: np.ndarray) -> np.ndarray:
    unwrapped = progress_raw.astype(float, copy=True)
    offset = 0.0
    for index in range(1, len(unwrapped)):
        if progress_raw[index] + offset < unwrapped[index - 1] - .5:
            offset += 1.0
        unwrapped[index] = progress_raw[index] + offset
    return unwrapped - unwrapped[0]


def measure_raw_source_coverage(location: pd.DataFrame, required_channels: tuple[str, ...]) -> RawCoverage:
    raw = location["progress_raw"].to_numpy(float)
    if not len(raw):
        return RawCoverage(0.0, 0.0, 0.0, {name: 0.0 for name in required_channels}, float("inf"), 1.0)
    unwrapped = raw.copy()
    offset = 0.0
    for index in range(1, len(unwrapped)):
        if raw[index] + offset < unwrapped[index - 1] - 0.5:
            offset += 1.0
        unwrapped[index] = raw[index] + offset
    progress_start = float(unwrapped[0])
    progress_end = float(unwrapped[-1])
    coverage = float(np.clip(progress_end - progress_start, 0.0, 1.0))
    elapsed = location["elapsed_s"].to_numpy(float)
    gaps = np.diff(elapsed) if len(elapsed) > 1 else np.array([float("inf")])
    reversals = np.maximum(0.0, -np.diff(unwrapped)) if len(unwrapped) > 1 else np.array([1.0])
    channel_coverage = {
        channel: float(location[channel].notna().mean()) if channel in location else 0.0
        for channel in required_channels
    }
    return RawCoverage(
        progress_start=progress_start, progress_end=progress_end, coverage_ratio=coverage,
        channel_coverage=channel_coverage, maximum_gap_s=float(gaps.max(initial=0.0)),
        maximum_progress_reversal=float(reversals.max(initial=0.0)),
    )


def align_progress_to_track(location: pd.DataFrame, track: CanonicalTrack) -> pd.DataFrame:
    result = location.sort_values("elapsed_s").copy()
    observed = unwrap_observed_progress(result["progress_raw"].to_numpy(float))
    result["progress_observed"] = observed
    result["progress"] = np.maximum.accumulate(np.clip(observed, 0.0, 1.0))
    result["distance_m"] = result["progress"] * track.length_m
    return result


def resample_aligned_trace(trace: pd.DataFrame, track: CanonicalTrack, spacing_m: float = 5.0) -> pd.DataFrame:
    ordered = trace.sort_values("distance_m").drop_duplicates("distance_m", keep="last")
    interior = np.arange(0.0, track.length_m, spacing_m, dtype=float)
    grid = np.unique(np.r_[interior, track.length_m])
    output = pd.DataFrame({"distance_m": grid})
    continuous = ["elapsed_s", "speed_kph", "throttle_pct", "rpm"]
    discrete = ["brake", "gear", "drs"]
    for column in continuous:
        if column in ordered:
            output[column] = np.interp(grid, ordered.distance_m, ordered[column])
    for column in discrete:
        if column in ordered:
            indices = np.searchsorted(ordered.distance_m.to_numpy(), grid, side="right") - 1
            indices = np.clip(indices, 0, len(ordered) - 1)
            output[column] = ordered[column].to_numpy()[indices]
    for column, values in {
        "x_m": track.x_m, "y_m": track.y_m, "elevation_m": track.elevation_m,
        "heading_rad": track.heading_rad, "curvature_per_m": track.curvature_per_m,
        "gradient": track.gradient,
    }.items():
        output[column] = np.interp(grid, track.distance_m, values)
    sector_indices = np.searchsorted(track.distance_m, grid, side="right") - 1
    sector_indices = np.clip(sector_indices, 0, len(track.distance_m) - 1)
    output["sector"] = np.asarray(track.sector, dtype=int)[sector_indices]
    output["progress"] = np.clip(output.distance_m / track.length_m, 0.0, 1.0)
    assert output.progress.is_monotonic_increasing
    assert output.progress.iloc[0] == 0.0 and output.progress.iloc[-1] == 1.0
    return output
```

```yaml
# calibration/config/geometry-sources.yaml — human-authored inputs
circuits:
  melbourne:   {geometry: data/geometry/melbourne.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  shanghai:    {geometry: data/geometry/shanghai.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  suzuka:      {geometry: data/geometry/suzuka.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  miami:       {geometry: data/geometry/miami.csv, geometry_format: csv, source: project-curated, source_license: project}
  montreal:    {geometry: data/geometry/montreal.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  monaco:      {geometry: data/geometry/monaco.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  barcelona:   {geometry: data/geometry/barcelona.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  spielberg:   {geometry: data/geometry/spielberg.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  silverstone: {geometry: data/geometry/silverstone.csv, geometry_format: csv, source: TUMFTM, source_license: BSD-3-Clause}
  spa:         {geometry: ../data/reference/spa-reference.json, geometry_format: spa-reference-json, source: TUMFTM-project-adapter, source_license: BSD-3-Clause}
```

Freeze the consumed manifest from measured bytes; `circuits.yaml` is generated and reviewed, never hand-filled with example digests:

```python
# calibration/scripts/freeze_circuit_manifest.py
from hashlib import sha256
from pathlib import Path
import yaml


def freeze_geometry_sources(source_path: Path, output_path: Path) -> None:
    source = yaml.safe_load(source_path.read_text())
    frozen = {"circuits": {}}
    for circuit_id, row in sorted(source["circuits"].items()):
        geometry_path = (source_path.parent / row["geometry"]).resolve()
        payload = geometry_path.read_bytes()
        frozen["circuits"][circuit_id] = {
            **row,
            "geometry": row["geometry"],
            "geometry_format": row["geometry_format"],
            "checksum": sha256(payload).hexdigest(),
        }
    output_path.write_text(yaml.safe_dump(frozen, sort_keys=True))
```

```bash
python calibration/scripts/freeze_circuit_manifest.py \
  --source calibration/config/geometry-sources.yaml \
  --output calibration/config/circuits.yaml
```

`GeometrySource.from_manifest()` consumes only generated `circuits.yaml` rows containing `geometry`, `geometry_format`, and a measured lowercase 64-character SHA-256 `checksum`.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
cd calibration
python -m pytest tests/test_alignment.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit geometry and alignment**

```bash
git add calibration/config/circuits.yaml calibration/src/spa_calibration/{geometry,alignment}.py calibration/tests/test_alignment.py calibration/data/geometry/silverstone.csv calibration/data/fixtures/silverstone-location.json
git commit -m "feat(calibration-data): align laps to canonical distance"
```

---

### Task 5: Detect reproducible driving phases

**Files:**
- Create: `calibration/src/spa_calibration/phases.py`
- Create: `calibration/tests/test_phases.py`
- Create: `calibration/data/fixtures/phase-hairpin.parquet`
- Create: `calibration/data/fixtures/phase-high-speed.parquet`

**Interfaces:**
- Consumes: 5 m aligned trace and canonical geometry.
- Produces: `detect_complex_phases(trace, track, complex_spec) -> list[PhaseRecord]`.

- [ ] **Step 1: Write failing hairpin and high-speed phase tests**

```python
# calibration/tests/test_phases.py
import pandas as pd
from spa_calibration.phases import ComplexSpec, detect_complex_phases


def test_hairpin_phases_are_ordered_and_cover_brake_to_full_power() -> None:
    trace = pd.read_parquet("data/fixtures/phase-hairpin.parquet")
    phases = detect_complex_phases(trace, ComplexSpec("hairpin", 100, 300, 200))
    names = [phase.phase_type for phase in phases]
    assert names == [
        "approach", "braking-onset", "peak-braking", "brake-release",
        "turn-in", "apex", "throttle-pickup", "exit-acceleration", "full-power"
    ]
    assert all(left.end_distance_m <= right.start_distance_m for left, right in zip(phases, phases[1:]))


def test_flat_high_speed_complex_omits_false_braking_phases() -> None:
    trace = pd.read_parquet("data/fixtures/phase-high-speed.parquet")
    phases = detect_complex_phases(trace, ComplexSpec("flat-sweeper", 100, 300, 210))
    names = [phase.phase_type for phase in phases]
    assert "peak-braking" not in names
    assert names == ["approach", "turn-in", "apex", "throttle-pickup", "exit-acceleration", "full-power"]
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_phases.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.phases'
```

- [ ] **Step 3: Implement threshold and change-point phase detection**

```python
# calibration/src/spa_calibration/phases.py
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.spatial import cKDTree
from .schemas import PhaseRecord


@dataclass(frozen=True)
class ComplexSpec:
    complex_id: str
    start_distance_m: float
    end_distance_m: float
    apex_hint_m: float


def test_duplicate_phase_anchors_are_normalized_without_overlap(flat_trace, simple_complex) -> None:
    phases = detect_complex_phases(flat_trace, simple_complex)
    assert phases
    assert all(left.end_distance_m <= right.start_distance_m for left, right in zip(phases, phases[1:]))
    assert all(phase.end_distance_m > phase.start_distance_m for phase in phases)


def test_unsupported_zero_length_phase_is_omitted(flat_trace, simple_complex) -> None:
    phases = detect_complex_phases(flat_trace.iloc[:2], simple_complex)
    assert all(phase.end_distance_m > phase.start_distance_m for phase in phases)


def detect_complex_phases(trace: pd.DataFrame, spec: ComplexSpec, lap_slug: str = "fixture", circuit_id: str = "fixture") -> list[PhaseRecord]:
    window = trace[(trace.distance_m >= spec.start_distance_m) & (trace.distance_m <= spec.end_distance_m)].copy()
    distance = window.distance_m.to_numpy(float)
    elapsed = window.elapsed_s.to_numpy(float)
    speed_ms = savgol_filter(window.speed_kph.to_numpy(float) / 3.6, 9, 2, mode="interp")
    acceleration = np.gradient(speed_ms, elapsed)
    curvature = np.abs(window.curvature_per_m.to_numpy(float))
    throttle = window.throttle_pct.to_numpy(float)
    brake = window.brake.to_numpy(float) > .5

    apex_index = int(np.argmin(np.abs(distance - spec.apex_hint_m)))
    local_minimum = int(np.argmin(speed_ms[max(0, apex_index - 8): min(len(speed_ms), apex_index + 9)])) + max(0, apex_index - 8)
    apex_index = local_minimum
    turn_candidates = np.where((curvature >= max(np.quantile(curvature, .65), .0015)) & (np.arange(len(curvature)) <= apex_index))[0]
    turn_in = int(turn_candidates[0]) if len(turn_candidates) else max(0, apex_index - 3)
    brake_candidates = np.where(brake | (acceleration < -3.5))[0]
    braking_onset = int(brake_candidates[0]) if len(brake_candidates) and brake_candidates[0] < apex_index else None
    peak_braking = int(np.argmin(acceleration[:apex_index + 1])) if braking_onset is not None else None
    release_candidates = np.where((np.arange(len(brake)) > (peak_braking or -1)) & (~brake) & (acceleration > -1.5))[0]
    brake_release = int(release_candidates[0]) if braking_onset is not None and len(release_candidates) else None
    pickup_candidates = np.where((np.arange(len(throttle)) >= apex_index) & (throttle >= 60))[0]
    throttle_pickup = int(pickup_candidates[0]) if len(pickup_candidates) else apex_index
    full_candidates = np.where((np.arange(len(throttle)) >= throttle_pickup) & (throttle >= 95) & (curvature < .0015))[0]
    full_power = int(full_candidates[0]) if len(full_candidates) else len(window) - 1

    anchors: list[tuple[str, int]] = [("approach", 0)]
    if braking_onset is not None:
        anchors.extend([
            ("braking-onset", braking_onset),
            ("peak-braking", peak_braking or braking_onset),
            ("brake-release", brake_release or turn_in),
        ])
    anchors.extend([
        ("turn-in", turn_in),
        ("apex", apex_index),
        ("throttle-pickup", throttle_pickup),
        ("exit-acceleration", max(throttle_pickup, min(full_power - 1, len(window) - 2))),
        ("full-power", min(full_power, len(window) - 2)),
    ])
    ordered: list[tuple[str, int]] = []
    for name, index in anchors:
        normalized = int(np.clip(index, 0, len(window) - 1))
        if ordered and normalized <= ordered[-1][1]:
            # Duplicate/collapsed anchors do not define a supported phase boundary.
            continue
        ordered.append((name, normalized))
    records: list[PhaseRecord] = []
    final_index = len(window) - 1
    for phase_index, ((name, start_index), (_, next_index)) in enumerate(zip(ordered, ordered[1:] + [("end", final_index)])):
        end_index = min(next_index, final_index)
        if end_index <= start_index:
            continue
        records.append(PhaseRecord(
            lap_slug=lap_slug,
            circuit_id=circuit_id,
            complex_id=spec.complex_id,
            phase_index=phase_index,
            phase_type=name,
            start_distance_m=float(distance[min(start_index, len(distance) - 1)]),
            end_distance_m=float(distance[min(end_index, len(distance) - 1)]),
            confidence=.9 if name in {"apex", "turn-in"} else .8,
            detector_version="phase-detector/v1",
        ))
    return records
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
cd calibration
python -m pytest tests/test_phases.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit phase segmentation**

```bash
git add calibration/src/spa_calibration/phases.py calibration/tests/test_phases.py calibration/data/fixtures/phase-*.parquet
git commit -m "feat(calibration-data): segment driving phases"
```

---

### Task 6: Extract continuous phase features and pair 2025 with 2026

**Files:**
- Create: `calibration/src/spa_calibration/features.py`
- Create: `calibration/tests/test_features.py`
- Create: `calibration/data/fixtures/paired-features.parquet`

**Interfaces:**
- Consumes: aligned traces, `PhaseRecord`, canonical geometry, lap metadata.
- Produces: `extract_phase_features() -> FeatureRecord` and `build_paired_deltas() -> pd.DataFrame`.

- [ ] **Step 1: Write failing feature invariants and pairing tests**

```python
# calibration/tests/test_features.py
import pandas as pd
from spa_calibration.features import build_paired_deltas, extract_phase_features
from spa_calibration.schemas import PhaseRecord


def test_feature_extraction_uses_fixed_downstream_exit_speeds() -> None:
    trace = pd.DataFrame({
        "distance_m": [0, 25, 50, 75, 100, 125, 150],
        "elapsed_s": [0, .2, .5, .9, 1.3, 1.65, 1.95],
        "speed_kph": [250, 200, 120, 90, 140, 190, 230],
        "throttle_pct": [100, 20, 0, 20, 70, 100, 100],
        "brake": [0, 1, 1, 0, 0, 0, 0],
        "gear": [7, 5, 3, 2, 3, 5, 6],
        "curvature_per_m": [0, .002, .008, .012, .006, .002, 0],
        "gradient": [0] * 7,
    })
    phase = PhaseRecord(
        lap_slug="lap", circuit_id="test", complex_id="hairpin", phase_index=0,
        phase_type="apex", start_distance_m=50, end_distance_m=100,
        confidence=.9, detector_version="phase-detector/v1"
    )
    feature = extract_phase_features(trace, phase, metadata={
        "season": 2026, "team_name": "Team", "driver_acronym": "DRV",
        "archetype": "slow-hairpin", "sector": 1, "entry_straight_m": 300, "exit_straight_m": 500,
        "track_length_m": 150, "complex_start_distance_m": 0, "complex_end_distance_m": 150,
        "apex_distance_m": 75, "quality_weight": .95,
    })
    assert feature.minimum_speed_kph == 90
    assert feature.exit_speed_50m_kph == 230
    assert 0 <= feature.full_throttle_fraction <= 1


def test_pairing_uses_circuit_complex_team_and_phase() -> None:
    features = pd.read_parquet("data/fixtures/paired-features.parquet")
    paired = build_paired_deltas(features, treatment_season=2026, reference_season=2025)
    assert set(paired["delta_phase_time_s"]) == {-0.1, 0.05}
    assert paired["pair_id"].is_unique
    assert set(paired["treatment_season"]) == {2026}
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_features.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.features'
```

- [ ] **Step 3: Implement feature extraction and deterministic pairing**

```python
# calibration/src/spa_calibration/features.py
from __future__ import annotations
import numpy as np
import pandas as pd
from .schemas import FeatureRecord, PhaseRecord


def _nearest_value(trace: pd.DataFrame, distance_m: float, column: str) -> float:
    index = (trace.distance_m - distance_m).abs().idxmin()
    return float(trace.loc[index, column])


def extract_phase_features(trace: pd.DataFrame, phase: PhaseRecord, metadata: dict[str, object]) -> FeatureRecord:
    window = trace[(trace.distance_m >= phase.start_distance_m) & (trace.distance_m <= phase.end_distance_m)].copy()
    if len(window) < 2:
        raise ValueError(f"phase {phase.complex_id}/{phase.phase_type} has fewer than two samples")
    start = float(window.distance_m.iloc[0])
    end = float(window.distance_m.iloc[-1])
    phase_time = float(window.elapsed_s.iloc[-1] - window.elapsed_s.iloc[0])
    brake_rows = window[window.brake > .5]
    throttle_rows = window[window.throttle_pct >= 60]
    full_throttle = float((window.throttle_pct >= 95).mean())
    curvature = window.curvature_per_m.to_numpy(float)
    elapsed = window.elapsed_s.to_numpy(float)
    sustained = float(np.sum(np.diff(elapsed, append=elapsed[-1])[(np.abs(curvature) >= .004)]))
    return FeatureRecord(
        lap_slug=phase.lap_slug,
        circuit_id=phase.circuit_id,
        season=int(metadata["season"]),
        team_name=str(metadata["team_name"]),
        driver_acronym=str(metadata["driver_acronym"]),
        complex_id=phase.complex_id,
        phase_type=phase.phase_type,
        archetype=str(metadata["archetype"]),
        sector=int(metadata["sector"]),
        track_length_m=float(metadata["track_length_m"]),
        complex_start_distance_m=float(metadata["complex_start_distance_m"]),
        complex_end_distance_m=float(metadata["complex_end_distance_m"]),
        phase_start_distance_m=phase.start_distance_m,
        phase_end_distance_m=phase.end_distance_m,
        apex_distance_m=float(metadata["apex_distance_m"]),
        phase_time_s=phase_time,
        entry_speed_kph=float(window.speed_kph.iloc[0]),
        minimum_speed_kph=float(window.speed_kph.min()),
        exit_speed_50m_kph=_nearest_value(trace, min(trace.distance_m.max(), end + 50), "speed_kph"),
        exit_speed_100m_kph=_nearest_value(trace, min(trace.distance_m.max(), end + 100), "speed_kph"),
        braking_onset_distance_m=float(brake_rows.distance_m.iloc[0]) if len(brake_rows) else None,
        braking_onset_from_complex_start_m=(
            float(brake_rows.distance_m.iloc[0] - metadata["complex_start_distance_m"]) if len(brake_rows) else None
        ),
        braking_length_m=float(brake_rows.distance_m.iloc[-1] - brake_rows.distance_m.iloc[0]) if len(brake_rows) > 1 else 0.0,
        throttle_pickup_m=float(throttle_rows.distance_m.iloc[0] - start) if len(throttle_rows) else end - start,
        full_throttle_fraction=full_throttle,
        mean_curvature_per_m=float(np.mean(np.abs(curvature))),
        peak_curvature_per_m=float(np.max(np.abs(curvature))),
        curvature_change_per_m2=float(np.mean(np.abs(np.gradient(curvature, window.distance_m.to_numpy(float))))),
        gradient_mean=float(window.gradient.mean()),
        entry_straight_m=float(metadata["entry_straight_m"]),
        exit_straight_m=float(metadata["exit_straight_m"]),
        sustained_load_s=max(0.0, sustained),
        quality_weight=float(metadata["quality_weight"]),
    )


def build_paired_deltas(features: pd.DataFrame, treatment_season: int = 2026, reference_season: int = 2025) -> pd.DataFrame:
    keys = [
        "circuit_id", "complex_id", "phase_type", "team_name", "driver_acronym",
        "archetype", "sector"
    ]
    measures = [
        "phase_time_s", "minimum_speed_kph", "exit_speed_50m_kph", "exit_speed_100m_kph",
        "braking_length_m", "full_throttle_fraction"
    ]
    nullable_measures = ["braking_onset_from_complex_start_m"]
    geometry = [
        "mean_curvature_per_m", "peak_curvature_per_m", "curvature_change_per_m2",
        "gradient_mean", "entry_straight_m", "exit_straight_m", "sustained_load_s"
    ]

    def aggregate(group: pd.DataFrame) -> pd.Series:
        weights = group.quality_weight.to_numpy(float)
        values = {column: float(np.average(group[column], weights=weights)) for column in measures + geometry}
        for column in nullable_measures:
            observed = group[column].notna().to_numpy()
            values[column] = (
                float(np.average(group.loc[observed, column], weights=weights[observed])) if observed.any() else None
            )
            values[f"{column}_observed"] = bool(observed.any())
        values["quality_weight"] = float(np.mean(weights))
        return pd.Series(values)

    grouped = features.groupby(keys + ["season"], as_index=False).apply(aggregate, include_groups=False).reset_index(drop=True)
    treatment = grouped[grouped.season == treatment_season].drop(columns="season")
    reference = grouped[grouped.season == reference_season].drop(columns="season")
    paired = treatment.merge(reference, on=keys, suffixes=("_treatment", "_reference"), validate="one_to_one")
    paired["pair_id"] = paired[keys].astype(str).agg("|".join, axis=1)
    paired["treatment_season"] = treatment_season
    paired["reference_season"] = reference_season
    paired["quality_weight"] = np.minimum(paired.quality_weight_treatment, paired.quality_weight_reference)
    for column in geometry:
        paired[column] = (paired[f"{column}_treatment"] + paired[f"{column}_reference"]) / 2
    for measure in measures:
        paired[f"delta_{measure}"] = paired[f"{measure}_treatment"] - paired[f"{measure}_reference"]
    for measure in nullable_measures:
        mask = paired[f"{measure}_observed_treatment"] & paired[f"{measure}_observed_reference"]
        paired[f"delta_{measure}_observed"] = mask
        paired[f"delta_{measure}"] = (paired[f"{measure}_treatment"] - paired[f"{measure}_reference"]).where(mask)
    return paired.sort_values("pair_id").reset_index(drop=True)
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
cd calibration
python -m pytest tests/test_features.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit feature extraction**

```bash
git add calibration/src/spa_calibration/features.py calibration/tests/test_features.py calibration/data/fixtures/paired-features.parquet
git commit -m "feat(calibration-data): extract paired phase features"
```

---

### Task 7: Orchestrate corpus generation, checksums, and frozen fixtures

**Files:**
- Create: `calibration/src/spa_calibration/corpus.py`
- Create: `calibration/src/spa_calibration/cli.py`
- Create: `calibration/tests/test_corpus.py`
- Create: `calibration/README.md`
- Modify: `calibration/pyproject.toml`

**Interfaces:**
- Consumes: Tasks 1–6.
- Produces: five deterministic processed artifacts and `spa-calibration corpus build` / `spa-calibration corpus verify` commands.

- [ ] **Step 1: Write failing reproducibility test**

```python
# calibration/tests/test_corpus.py
from pathlib import Path
from spa_calibration.corpus import build_fixture_corpus, verify_corpus


def test_fixture_corpus_is_byte_reproducible(tmp_path: Path) -> None:
    first = build_fixture_corpus(Path("data/fixtures"), tmp_path / "first", source_cutoff="2026-07-13T23:59:59Z")
    second = build_fixture_corpus(Path("data/fixtures"), tmp_path / "second", source_cutoff="2026-07-13T23:59:59Z")
    assert first.artifact_checksums == second.artifact_checksums
    assert verify_corpus(tmp_path / "first").schema_version == "spa-calibration-corpus/v1"
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
cd calibration
python -m pytest tests/test_corpus.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'spa_calibration.corpus'
```

- [ ] **Step 3: Implement sorted writes, manifest checksums, and CLI**

```python
# calibration/src/spa_calibration/corpus.py
from __future__ import annotations
from datetime import UTC, datetime
from pathlib import Path
import json
import pandas as pd
from .hashing import sha256_bytes
from .schemas import CorpusManifest

ARTIFACTS = ("laps.parquet", "aligned-traces.parquet", "phases.parquet", "features.parquet")


def _write_parquet(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = frame.sort_values(sort_by).reset_index(drop=True)
    ordered.to_parquet(path, index=False, compression="zstd", version="2.6")
    return sha256_bytes(path.read_bytes())


def write_corpus(
    output: Path,
    *,
    laps: pd.DataFrame,
    traces: pd.DataFrame,
    phases: pd.DataFrame,
    features: pd.DataFrame,
    source_cutoff: datetime,
    source_checksums: dict[str, str],
    source_eligibility_checksum: str,
    circuit_year_eligibility_checksum: str,
    lap_selection_checksum: str,
    generated_at: datetime,
) -> CorpusManifest:
    checksums = {
        "laps.parquet": _write_parquet(laps, output / "laps.parquet", ["lap_slug"]),
        "aligned-traces.parquet": _write_parquet(traces, output / "aligned-traces.parquet", ["lap_slug", "distance_m"]),
        "phases.parquet": _write_parquet(phases, output / "phases.parquet", ["lap_slug", "complex_id", "phase_index"]),
        "features.parquet": _write_parquet(features, output / "features.parquet", ["circuit_id", "lap_slug", "complex_id", "phase_type"]),
    }
    manifest = CorpusManifest(
        generated_at=generated_at,
        source_cutoff=source_cutoff,
        circuits=sorted(features.circuit_id.unique().tolist()),
        seasons=sorted(int(value) for value in features.season.unique()),
        lap_count=len(laps),
        trace_point_count=len(traces),
        phase_count=len(phases),
        feature_count=len(features),
        source_checksums=dict(sorted(source_checksums.items())),
        artifact_checksums=checksums,
        source_eligibility_checksum=source_eligibility_checksum,
        circuit_year_eligibility_checksum=circuit_year_eligibility_checksum,
        lap_selection_checksum=lap_selection_checksum,
    )
    payload = manifest.model_dump_json(indent=2).encode()
    (output / "provenance.json").write_bytes(payload)
    return manifest


def verify_corpus(output: Path) -> CorpusManifest:
    manifest = CorpusManifest.model_validate_json((output / "provenance.json").read_text())
    declared = set(manifest.artifact_checksums)
    actual_files = {path.name for path in output.iterdir() if path.is_file() and path.name != "provenance.json"}
    required = set(ARTIFACTS)
    if declared != required or actual_files != required:
        raise ValueError(f"corpus artifact set mismatch: declared={sorted(declared)} actual={sorted(actual_files)}")
    for filename in ARTIFACTS:
        actual = sha256_bytes((output / filename).read_bytes())
        expected = manifest.artifact_checksums[filename]
        if actual != expected:
            raise ValueError(f"checksum mismatch for {filename}: {actual} != {expected}")
    return manifest


def build_fixture_corpus(fixtures: Path, output: Path, source_cutoff: str) -> CorpusManifest:
    return write_corpus(
        output,
        laps=pd.read_parquet(fixtures / "corpus-laps.parquet"),
        traces=pd.read_parquet(fixtures / "corpus-traces.parquet"),
        phases=pd.read_parquet(fixtures / "corpus-phases.parquet"),
        features=pd.read_parquet(fixtures / "corpus-features.parquet"),
        source_cutoff=datetime.fromisoformat(source_cutoff.replace("Z", "+00:00")),
        source_checksums={"fixtures": "0" * 64},
        source_eligibility_checksum="1" * 64,
        circuit_year_eligibility_checksum="2" * 64,
        lap_selection_checksum="3" * 64,
        generated_at=datetime(2026, 7, 14, tzinfo=UTC),
    )
```

```python
# calibration/src/spa_calibration/cli.py
from datetime import UTC, datetime
from pathlib import Path
import typer
from .corpus import build_fixture_corpus, verify_corpus

app = typer.Typer(no_args_is_help=True)
corpus_app = typer.Typer(no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")


@corpus_app.command("build-fixture")
def build_fixture(
    fixtures: Path = typer.Option(Path("data/fixtures")),
    output: Path = typer.Option(Path("data/processed")),
    source_cutoff: str = typer.Option("2026-07-13T23:59:59Z"),
) -> None:
    manifest = build_fixture_corpus(fixtures, output, source_cutoff)
    typer.echo(manifest.model_dump_json(indent=2))


@corpus_app.command("verify")
def verify(output: Path = typer.Option(Path("data/processed"))) -> None:
    manifest = verify_corpus(output)
    typer.echo(f"verified {manifest.schema_version}: {manifest.feature_count} features")
```

- [ ] **Step 4: Run full Plan A verification**

Run:

```bash
cd calibration
python -m pytest -q tests/test_schemas.py tests/test_cache.py tests/test_openf1.py tests/test_quality.py tests/test_alignment.py tests/test_phases.py tests/test_features.py tests/test_corpus.py
spa-calibration corpus build-fixture --fixtures data/fixtures --output /tmp/spa-corpus-a
spa-calibration corpus build-fixture --fixtures data/fixtures --output /tmp/spa-corpus-b
cmp /tmp/spa-corpus-a/provenance.json /tmp/spa-corpus-b/provenance.json
spa-calibration corpus verify --output /tmp/spa-corpus-a
```

Expected:

```text
all tests passed
cmp exits 0
verified spa-calibration-corpus/v1
```

- [ ] **Step 5: Commit corpus orchestration and documentation**

```bash
git add calibration/src/spa_calibration/{corpus,cli}.py calibration/tests/test_corpus.py calibration/README.md calibration/pyproject.toml calibration/data/fixtures/corpus-*.parquet
git commit -m "feat(calibration-data): build reproducible feature corpus"
```

### Task 8: Build the live paired-season corpus from explicit event manifests

**Files:**
- Create: `calibration/src/spa_calibration/pipeline.py`
- Create: `calibration/tests/test_pipeline.py`
- Modify: `calibration/src/spa_calibration/cli.py`
- Create: `calibration/data/fixtures/pipeline-openf1-bundle.json`
- Create: `calibration/config/complexes.yaml`

**Interfaces:**
- Consumes: event and circuit manifests plus Tasks 1–7.
- Produces: `build_live_corpus()`, one immutable source bundle per lap, and `spa-calibration corpus refresh`.

- [ ] **Step 1: Write the failing end-to-end fixture test**

```python
# calibration/tests/test_pipeline.py
from datetime import UTC, datetime
from pathlib import Path
import pytest
from spa_calibration.pipeline import build_corpus_from_fixture_bundle


def test_fixture_bundle_builds_2025_2026_pairs_and_2024_controls(tmp_path: Path) -> None:
    manifest = build_corpus_from_fixture_bundle(
        Path("data/fixtures/pipeline-openf1-bundle.json"),
        circuits_config=Path("config/circuits.yaml"),
        eligibility_path=Path("manifests/source-eligibility.json"),
        circuit_year_eligibility_path=Path("manifests/circuit-year-eligibility.json"),
        lap_selection_path=Path("manifests/lap-selection.json"),
        output=tmp_path,
        generated_at=datetime(2026, 7, 14, tzinfo=UTC),
    )
    assert manifest.seasons == [2024, 2025, 2026]
    assert manifest.circuits == ["silverstone"]
    assert manifest.lap_count >= 6
    assert (tmp_path / "features.parquet").exists()
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_pipeline.py -q
```

Expected: missing `spa_calibration.pipeline`.

- [ ] **Step 3: Implement source coupling and live corpus orchestration**

```python
# calibration/src/spa_calibration/pipeline.py
from __future__ import annotations
from datetime import UTC, datetime, timedelta
from pathlib import Path
import asyncio
import orjson
import pandas as pd
import yaml
from .alignment import align_progress_to_track, measure_raw_source_coverage, project_locations_to_track, resample_aligned_trace
from .cache import ContentAddressedCache
from .corpus import write_corpus
from .features import extract_phase_features
from .geometry import GeometrySource, load_canonical_track
from .openf1 import EventSpec, OpenF1Client
from .phases import ComplexSpec, detect_complex_phases
from .quality import LapContext, classify_lap


def _timestamp_frame(rows: list[dict], start: datetime, timestamp_key: str = "date") -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    timestamps = pd.to_datetime(frame[timestamp_key], utc=True)
    frame["elapsed_s"] = (timestamps - pd.Timestamp(start)).dt.total_seconds()
    return frame.sort_values("elapsed_s").reset_index(drop=True)


def couple_channels(car_rows: list[dict], location_rows: list[dict], start: datetime) -> pd.DataFrame:
    car = _timestamp_frame(car_rows, start).rename(columns={
        "speed": "speed_kph", "throttle": "throttle_pct", "n_gear": "gear"
    })
    location = _timestamp_frame(location_rows, start)
    columns = [column for column in ["elapsed_s", "speed_kph", "throttle_pct", "brake", "gear", "rpm", "drs"] if column in car]
    coupled = pd.merge_asof(
        location.sort_values("elapsed_s"),
        car[columns].sort_values("elapsed_s"),
        on="elapsed_s",
        direction="nearest",
        tolerance=.45,
    )
    return coupled.dropna(subset=["speed_kph", "x", "y"]).reset_index(drop=True)


def _rainfall_during(weather_rows: list[dict], start: datetime, end: datetime) -> bool | None:
    relevant = [row for row in weather_rows if start <= datetime.fromisoformat(row["date"]) <= end]
    return any(bool(row.get("rainfall")) for row in relevant) if relevant else None


def _flags_during(control_rows: list[dict], start: datetime, end: datetime) -> tuple[str, ...]:
    return tuple(str(row.get("flag") or row.get("category") or "").upper() for row in control_rows if start <= datetime.fromisoformat(row["date"]) <= end)


async def fetch_session_bundle(client: OpenF1Client, spec: EventSpec) -> dict[str, object]:
    session = await client.resolve_session(spec)
    session_key = session.session_key
    laps, laps_source = await client.get("laps", {"session_key": session_key})
    drivers, drivers_source = await client.get("drivers", {"session_key": session_key})
    weather, weather_source = await client.get("weather", {"session_key": session_key})
    control, control_source = await client.get("race_control", {"session_key": session_key})
    return {
        "event": spec.model_dump(),
        "session": {"meeting_key": session.meeting_key, "session_key": session_key, "date_start": session.date_start.isoformat()},
        "laps": laps, "drivers": drivers, "weather": weather, "race_control": control,
        "sources": [session.source.__dict__, laps_source.__dict__, drivers_source.__dict__, weather_source.__dict__, control_source.__dict__],
    }


async def fetch_lap_channels(client: OpenF1Client, session_key: int, lap: dict) -> dict[str, object]:
    start = datetime.fromisoformat(lap["date_start"])
    end = start + timedelta(seconds=float(lap["lap_duration"]))
    query = {
        "session_key": session_key,
        "driver_number": int(lap["driver_number"]),
        "date>=": (start - timedelta(seconds=1)).isoformat(),
        "date<=": (end + timedelta(seconds=1)).isoformat(),
    }
    car, car_source = await client.get("car_data", query)
    location, location_source = await client.get("location", query)
    return {"lap": lap, "car_data": car, "location": location, "sources": [car_source.__dict__, location_source.__dict__]}
```

The orchestration function must use this exact acceptance and write sequence:

```python
def build_corpus_from_bundles(
    bundles,
    circuits_config: Path,
    output: Path,
    generated_at: datetime,
    eligibility: EligibilityEvaluation,
    *,
    source_eligibility_checksum: str,
    circuit_year_eligibility_checksum: str,
    lap_selection_checksum: str,
):
    circuit_rows = yaml.safe_load(circuits_config.read_text())["circuits"]
    lap_rows, trace_rows, phase_rows, feature_rows = [], [], [], []
    source_checksums = {}
    for session_bundle in bundles:
        circuit_id = session_bundle["event"]["circuit_id"]
        geometry_row = circuit_rows[circuit_id]
        geometry_source = GeometrySource.from_manifest(geometry_row, config_root=circuits_config.parent)
        track = load_canonical_track(circuit_id, geometry_source)
        drivers = {int(row["driver_number"]): row for row in session_bundle["drivers"]}
        for lap_bundle in session_bundle["lap_bundles"]:
            lap = lap_bundle["lap"]
            start = datetime.fromisoformat(lap["date_start"])
            end = start + timedelta(seconds=float(lap["lap_duration"]))
            coupled = couple_channels(lap_bundle["car_data"], lap_bundle["location"], start)
            projected = project_locations_to_track(coupled, track)
            raw_coverage = measure_raw_source_coverage(
                projected,
                required_channels=eligibility.required_channels(circuit_id, session_bundle["event"]["season"]),
            )
            aligned = align_progress_to_track(projected, track)
            quality = classify_lap(
                float(lap["lap_duration"]), aligned,
                LapContext(
                    rainfall=_rainfall_during(session_bundle["weather"], start, end),
                    race_control_flags=_flags_during(session_bundle["race_control"], start, end),
                    is_pit_out=bool(lap.get("is_pit_out_lap")),
                    aborted=raw_coverage.progress_end < .94,
                    raw_coverage=raw_coverage,
                ),
            )
            if not quality.accepted:
                continue
            trace = resample_aligned_trace(aligned, track, 5)
            driver = drivers[int(lap["driver_number"])]
            lap_slug = f"{session_bundle['event']['season']}-{session_bundle['session']['meeting_key']}-{session_bundle['session']['session_key']}-{lap['driver_number']}-{lap['lap_number']}"
            trace = trace.assign(lap_slug=lap_slug, circuit_id=circuit_id)
            phases = []
            for spec in load_complex_specs(circuit_id):
                phases.extend(detect_complex_phases(trace, spec, lap_slug, circuit_id))
            features = [
                extract_phase_features(trace, phase, metadata_for_phase(session_bundle, driver, quality, phase, track))
                for phase in phases
            ]
            lap_rows.append(lap_record_row(session_bundle, lap_bundle, driver, quality, lap_slug))
            trace_rows.append(trace)
            phase_rows.extend(record.model_dump() for record in phases)
            feature_rows.extend(record.model_dump() for record in features)
            for source in session_bundle["sources"] + lap_bundle["sources"]:
                source_checksums[f"{source['endpoint']}?{source['query']}"] = source["checksum"]
    return write_corpus(
        output,
        laps=pd.DataFrame(lap_rows),
        traces=pd.concat(trace_rows, ignore_index=True),
        phases=pd.DataFrame(phase_rows),
        features=pd.DataFrame(feature_rows),
        source_cutoff=max(datetime.fromisoformat(row["session"]["date_start"]) for row in bundles),
        source_checksums=source_checksums,
        source_eligibility_checksum=source_eligibility_checksum,
        circuit_year_eligibility_checksum=circuit_year_eligibility_checksum,
        lap_selection_checksum=lap_selection_checksum,
        generated_at=generated_at,
    )
```

Add the pure manifest adapters in the same file:

```python
def load_complex_specs(circuit_id: str, manifest_path: Path = Path("config/complexes.yaml")) -> list[ComplexSpec]:
    payload = yaml.safe_load(manifest_path.read_text())
    rows = payload["circuits"][circuit_id]
    return [ComplexSpec(
        complex_id=row["id"],
        start_distance_m=float(row["start_distance_m"]),
        end_distance_m=float(row["end_distance_m"]),
        apex_hint_m=float(row["apex_hint_m"]),
    ) for row in rows]


def complex_metadata(circuit_id: str, complex_id: str, manifest_path: Path = Path("config/complexes.yaml")) -> dict[str, object]:
    rows = yaml.safe_load(manifest_path.read_text())["circuits"][circuit_id]
    row = next(item for item in rows if item["id"] == complex_id)
    return {
        "archetype": row["archetype"],
        "entry_straight_m": float(row["entry_straight_m"]),
        "exit_straight_m": float(row["exit_straight_m"]),
        "sector": int(row["sector"]),
        "complex_start_distance_m": float(row["start_distance_m"]),
        "complex_end_distance_m": float(row["end_distance_m"]),
        "apex_distance_m": float(row["apex_hint_m"]),
    }


def metadata_for_phase(session_bundle, driver, quality, phase, track):
    event = session_bundle["event"]
    return {
        "season": int(event["season"]),
        "team_name": driver.get("team_name") or "Unknown team",
        "driver_acronym": driver.get("name_acronym") or str(driver["driver_number"]),
        "quality_weight": quality.score,
        "track_length_m": track.length_m,
        **complex_metadata(event["circuit_id"], phase.complex_id),
    }


def lap_record_row(session_bundle, lap_bundle, driver, quality, lap_slug):
    event = session_bundle["event"]
    lap = lap_bundle["lap"]
    sources = session_bundle["sources"] + lap_bundle["sources"]
    checksum = next(source["checksum"] for source in reversed(sources) if source["endpoint"] in {"car_data", "laps"})
    return {
        "lap_slug": lap_slug,
        "season": int(event["season"]),
        "meeting_key": int(session_bundle["session"]["meeting_key"]),
        "session_key": int(session_bundle["session"]["session_key"]),
        "driver_number": int(lap["driver_number"]),
        "lap_number": int(lap["lap_number"]),
        "circuit_id": event["circuit_id"],
        "session_name": event["session_name"],
        "session_segment": lap.get("segment", "UNKNOWN"),
        "selection_fallback": bool(lap.get("selection_fallback", False)),
        "fallback_reason": lap.get("fallback_reason"),
        "driver_acronym": driver.get("name_acronym") or str(driver["driver_number"]),
        "driver_name": driver.get("full_name") or driver.get("broadcast_name") or str(driver["driver_number"]),
        "team_name": driver.get("team_name") or "Unknown team",
        "lap_time_s": float(lap["lap_duration"]),
        "date_start": lap["date_start"],
        "source_name": "OpenF1",
        "source_license": "CC BY-NC-SA 4.0",
        "source_query": next(source["query"] for source in reversed(sources) if source["endpoint"] in {"car_data", "laps"}),
        "retrieved_at": max(source["retrieved_at"] for source in sources),
        "raw_checksum": checksum,
        "quality_score": quality.score,
        "quality_flags": list(quality.flags),
    }


def profile_key(row: dict) -> tuple[str, str]:
    return (
        str(row.get("team_name") or "Unknown team"),
        str(row.get("driver_acronym") or row.get("driver_number")),
    )


def select_candidate_laps(laps: list[dict], session_name: str, maximum_per_profile: int = 2) -> list[dict]:
    preferred = ["SQ3", "SQ2", "SQ1"] if session_name == "Sprint Qualifying" else ["Q3", "Q2", "Q1"]
    valid = [row for row in laps if row.get("date_start") and row.get("lap_duration") and not row.get("is_pit_out_lap")]
    selected: list[dict] = []
    profile_counts: dict[tuple[str, str], int] = {}
    profiles = sorted({profile_key(row) for row in valid})
    for profile in profiles:
        profile_rows = [row for row in valid if profile_key(row) == profile]
        for segment_index, segment in enumerate(preferred):
            candidates = sorted(
                (row for row in profile_rows if row.get("segment") == segment),
                key=lambda row: float(row["lap_duration"]),
            )
            for row in candidates:
                if profile_counts.get(profile, 0) >= maximum_per_profile:
                    break
                selected.append({
                    **row,
                    "profile_id": "|".join(profile),
                    "selection_fallback": segment_index > 0,
                    "fallback_reason": None if segment_index == 0 else f"no eligible {preferred[0]} lap for profile",
                })
                profile_counts[profile] = profile_counts.get(profile, 0) + 1
            if profile_counts.get(profile, 0):
                break
    return sorted(selected, key=lambda row: float(row["lap_duration"]))[:12]


def test_candidate_lap_limit_preserves_both_team_profiles() -> None:
    laps = [
        {"team_name": "Example", "driver_acronym": "AAA", "driver_number": 1, "segment": "Q3", "lap_duration": 90.0, "date_start": "2026-01-01T00:00:00Z"},
        {"team_name": "Example", "driver_acronym": "AAA", "driver_number": 1, "segment": "Q3", "lap_duration": 90.1, "date_start": "2026-01-01T00:02:00Z"},
        {"team_name": "Example", "driver_acronym": "BBB", "driver_number": 2, "segment": "Q3", "lap_duration": 91.0, "date_start": "2026-01-01T00:04:00Z"},
        {"team_name": "Example", "driver_acronym": "BBB", "driver_number": 2, "segment": "Q3", "lap_duration": 91.1, "date_start": "2026-01-01T00:06:00Z"},
    ]
    selected = select_candidate_laps(laps, "Qualifying", maximum_per_profile=2)
    assert {row["profile_id"] for row in selected} == {"Example|AAA", "Example|BBB"}


def build_corpus_from_fixture_bundle(
    bundle_path: Path,
    circuits_config: Path,
    output: Path,
    generated_at: datetime,
    eligibility_path: Path,
    circuit_year_eligibility_path: Path,
    lap_selection_path: Path,
):
    bundles = orjson.loads(bundle_path.read_bytes())
    eligibility = EligibilityEvaluation.model_validate_json(eligibility_path.read_text())
    return build_corpus_from_bundles(
        bundles,
        circuits_config,
        output,
        generated_at,
        eligibility,
        source_eligibility_checksum=sha256_bytes(eligibility_path.read_bytes()),
        circuit_year_eligibility_checksum=sha256_bytes(circuit_year_eligibility_path.read_bytes()),
        lap_selection_checksum=sha256_bytes(lap_selection_path.read_bytes()),
    )




def normalize_utc_timestamp(value: str | date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min, tzinfo=UTC)
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError(f"unsupported timestamp value: {type(value).__name__}")
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(UTC)


async def build_live_corpus(events_path: Path, circuits_path: Path, raw_cache: Path, output: Path, generated_at: datetime):
    event_config = yaml.safe_load(events_path.read_text())
    client = OpenF1Client(ContentAddressedCache(raw_cache), retrieved_at=generated_at)
    bundles = []
    for season in event_config["seasons"]:
        for event in event_config["events"]:
            window = event.get("event_date_windows", {}).get(season) or event.get("event_date_windows", {}).get(str(season))
            for session_name in event_config["sessions"]:
                payload = {
                    "season": season,
                    "circuit_id": event["circuit_id"],
                    "country_name": event["country_name"],
                    "session_name": session_name,
                    "meeting_key": event.get("meeting_keys", {}).get(season) or event.get("meeting_keys", {}).get(str(season)),
                    "meeting_name": event.get("meeting_name"),
                    "circuit_short_name": event.get("circuit_short_name"),
                    "event_date_start": normalize_utc_timestamp(window["start"]) if window else None,
                    "event_date_end": normalize_utc_timestamp(window["end"]) if window else None,
                }
                spec = EventSpec.model_validate(payload)
                session_bundle = await fetch_session_bundle(client, spec)
                drivers = {int(row["driver_number"]): row for row in session_bundle["drivers"]}
                enriched_laps = [{**lap, "team_name": drivers.get(int(lap["driver_number"]), {}).get("team_name")} for lap in session_bundle["laps"]]
                lap_bundles = []
                for lap in select_candidate_laps(enriched_laps, session_name=session_name):
                    lap_bundles.append(await fetch_lap_channels(client, session_bundle["session"]["session_key"], lap))
                session_bundle["lap_bundles"] = lap_bundles
                bundles.append(session_bundle)
    eligibility, source_manifest_path, circuit_year_manifest_path, lap_selection_path = evaluate_eligibility(
        events_path, circuits_path
    )
    return build_corpus_from_bundles(
        bundles,
        circuits_path,
        output,
        generated_at,
        eligibility,
        source_eligibility_checksum=sha256_bytes(source_manifest_path.read_bytes()),
        circuit_year_eligibility_checksum=sha256_bytes(circuit_year_manifest_path.read_bytes()),
        lap_selection_checksum=sha256_bytes(lap_selection_path.read_bytes()),
    )
```

Create a validated complex manifest. Every listed circuit must have at least one complex and the full set of rows must cover all timed corner regions without overlap:

```yaml
# calibration/config/complexes.yaml
schema_version: spa-calibration-complexes/v1
circuits:
  silverstone:
    - id: village-loop
      start_distance_m: 500
      apex_hint_m: 780
      end_distance_m: 1050
      archetype: slow-direction-change
      sector: 1
      entry_straight_m: 420
      exit_straight_m: 190
  spa:
    - id: la-source
      start_distance_m: 40
      apex_hint_m: 395
      end_distance_m: 690
      archetype: slow-hairpin
      sector: 1
      entry_straight_m: 310
      exit_straight_m: 1180
```

Generate the complete manifest from canonical geometry, then apply only explicit override rows:

```python
def derive_complex_rows(track: CanonicalTrack) -> list[dict[str, object]]:
    distance = track.distance_m
    curvature = np.abs(track.curvature_per_m)
    active = curvature >= .0015
    dilation_points = max(1, int(round(60 / np.median(np.diff(distance)))))
    active = np.convolve(active.astype(int), np.ones(dilation_points, dtype=int), mode="same") > 0
    boundaries = np.flatnonzero(np.diff(np.r_[False, active, False].astype(int)))
    intervals = [(int(start), int(end - 1)) for start, end in boundaries.reshape(-1, 2)]
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and distance[start] - distance[merged[-1][1]] < 75:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    rows = []
    for number, (start, end) in enumerate(merged, start=1):
        local = curvature[start:end + 1]
        apex = start + int(np.argmax(local))
        signed = track.curvature_per_m[start:end + 1]
        direction_changes = int(np.sum(np.diff(np.sign(signed)) != 0))
        minimum_radius = 1 / max(float(local.max()), 1e-9)
        sustained_length = float(distance[end] - distance[start])
        archetype = (
            "rapid-high-speed-direction-change" if direction_changes >= 2 and minimum_radius > 80
            else "medium-speed-direction-change" if direction_changes >= 1
            else "slow-hairpin" if minimum_radius < 35
            else "sustained-high-speed" if minimum_radius > 100 and sustained_length > 180
            else "medium-speed-single-apex"
        )
        rows.append({
            "id": f"auto-{number:02d}",
            "start_distance_m": float(distance[start]),
            "apex_hint_m": float(distance[apex]),
            "end_distance_m": float(distance[end]),
            "archetype": archetype,
            "sector": int(track.sector[apex]),
            "entry_straight_m": contiguous_straight_length(track, start, direction=-1),
            "exit_straight_m": contiguous_straight_length(track, end, direction=1),
        })
    return rows


def validate_complex_rows(track: CanonicalTrack, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"{track.circuit_id} has no derived complexes")
    ordered = sorted(rows, key=lambda row: row["start_distance_m"])
    for previous, current in zip(ordered, ordered[1:]):
        if previous["end_distance_m"] > current["start_distance_m"]:
            raise ValueError(f"overlapping complexes: {previous['id']} and {current['id']}")
    for row in ordered:
        if not row["start_distance_m"] <= row["apex_hint_m"] <= row["end_distance_m"]:
            raise ValueError(f"apex outside complex: {row['id']}")
        if row["end_distance_m"] > track.length_m:
            raise ValueError(f"complex exceeds circuit length: {row['id']}")
```

Run the generator for every configured geometry and commit the resulting `config/complexes.yaml`:

```bash
spa-calibration geometry derive-complexes --circuits config/circuits.yaml --output config/complexes.yaml
spa-calibration geometry validate-complexes --circuits config/circuits.yaml --complexes config/complexes.yaml
```

Expected: Melbourne, Shanghai, Suzuka, Miami, Montreal, Monaco, Barcelona, Spielberg, Silverstone, and Spa each report at least one validated complex; the command exits non-zero on overlap or an out-of-range apex.

Add CLI:

```python
@corpus_app.command("refresh")
def refresh(
    events: Path = typer.Option(Path("config/events.yaml")),
    circuits: Path = typer.Option(Path("config/circuits.yaml")),
    raw_cache: Path = typer.Option(Path("data/raw/openf1")),
    output: Path = typer.Option(Path("data/processed")),
    generated_at: str = typer.Option(..., help="Required ISO timestamp for reproducibility"),
) -> None:
    manifest = asyncio.run(build_live_corpus(events, circuits, raw_cache, output, datetime.fromisoformat(generated_at.replace("Z", "+00:00"))))
    typer.echo(manifest.model_dump_json(indent=2))
```

- [ ] **Step 4: Verify fixture orchestration and explicit live command help**

```bash
cd calibration
python -m pytest tests/test_pipeline.py -q
spa-calibration corpus refresh --help
```

Expected: test passes; help lists required `--generated-at`.

- [ ] **Step 5: Commit live pipeline orchestration**

```bash
git add calibration/src/spa_calibration/pipeline.py calibration/src/spa_calibration/cli.py calibration/tests/test_pipeline.py calibration/data/fixtures/pipeline-openf1-bundle.json calibration/config/complexes.yaml
git commit -m "feat(calibration-data): orchestrate paired-season corpus refresh"
```

---

## Plan A Completion Gate

Run:

```bash
cd calibration
python -m pytest -q
spa-calibration corpus verify --output data/processed
```

The plan is complete when the corpus verification succeeds, all Parquet files have checksums recorded in `provenance.json`, and no test makes a network request.
