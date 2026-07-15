# Spa Calibration Model and Prediction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Learn a backtested 2025→2026 phase-level performance correction, compose it with a minimum-time vehicle prior, and emit a gated Spa 2026 prediction with coherent team distributions and honest uncertainty.

**Architecture:** Separate baseline, statistical calibration, physics prior, validation, and prediction modules. A set of partially pooled Student-t outcome models estimates phase-level residual changes from continuous geometry, phase, team, driver, circuit, and season-regime effects. Leave-one-circuit-out validation compares the hierarchy against whole-circuit and archetype baselines. Spa prediction applies posterior corrections to team-specific vehicle priors, iterates line/control optimization, samples coherent laps, and serializes a checksum-protected browser artifact only when release gates pass.

**Tech Stack:** Python 3.11+, NumPy, pandas, SciPy, scikit-learn, PyMC 5, ArviZ, Pydantic, PyArrow, pytest.

## Global Constraints

- Consume only a verified `spa-calibration-corpus/v1` corpus.
- The release model must outperform whole-circuit scaling on held-out lap time and telemetry shape.
- Do not create a “best-of-every-team” composite car; each sampled lap belongs to one coherent team/driver profile.
- The physics prior and empirical correction must remain separately inspectable.
- Posterior uncertainty must include global, team, circuit, driver, residual, and analogue-scarcity contributions.
- The artifact is `released` only when all declared gates pass; otherwise it is `failed-validation` or `pending` and contains no field-best central estimate.
- Fix every random seed in configuration and record it in the artifact.
- Never claim exact battery state, electrical power, downforce, drag, or active-aero command as observed.

---

## File Map

```text
calibration/
├── config/
│   ├── model.yaml
│   ├── release-gates.yaml
│   ├── regulation-regimes.yaml
│   └── spa-analogues.yaml
├── src/spa_calibration/
│   ├── baselines.py
│   ├── design_matrix.py
│   ├── hierarchical.py
│   ├── model_io.py
│   ├── vehicle_prior.py
│   ├── line_optimizer.py
│   ├── validation.py
│   ├── regimes.py
│   ├── analogues.py
│   ├── spa_predictor.py
│   ├── artifact.py
│   └── cli.py
├── tests/
│   ├── test_baselines.py
│   ├── test_design_matrix.py
│   ├── test_hierarchical_recovery.py
│   ├── test_vehicle_prior.py
│   ├── test_line_optimizer.py
│   ├── test_validation.py
│   ├── test_regimes.py
│   ├── test_analogues.py
│   ├── test_spa_predictor.py
│   └── test_prediction_artifact.py
└── artifacts/
    ├── model/
    ├── validation/
    └── predictions/
```

## Shared Interfaces

```python
OUTCOMES = (
    "delta_phase_time_s",
    "delta_minimum_speed_kph",
    "delta_exit_speed_100m_kph",
    "delta_braking_onset_m",
    "delta_full_throttle_fraction",
)

@dataclass(frozen=True)
class CalibrationFit:
    model_version: str
    outcomes: dict[str, az.InferenceData]
    encoder: FeatureEncoder
    training_manifest_checksum: str
    random_seed: int

@dataclass(frozen=True)
class LapSolution:
    team_name: str
    driver_acronym: str
    lap_time_s: float
    sectors_s: tuple[float, float, float]
    trace: pd.DataFrame
    line: pd.DataFrame
    assumptions: dict[str, float | str]
```

---

### Task 1: Implement simple baselines and deterministic fold definitions

**Files:**
- Create: `calibration/src/spa_calibration/baselines.py`
- Create: `calibration/tests/test_baselines.py`
- Create: `calibration/config/release-gates.yaml`

**Interfaces:**
- Consumes: Plan A paired delta frame.
- Produces: `whole_circuit_baseline()`, `archetype_baseline()`, `circuit_folds()`, and `ReleaseGates`.

- [ ] **Step 1: Write failing baseline tests**

```python
# calibration/tests/test_baselines.py
import pandas as pd
from spa_calibration.baselines import archetype_baseline, circuit_folds, whole_circuit_baseline


def frame() -> pd.DataFrame:
    return pd.DataFrame({
        "circuit_id": ["a", "a", "b", "b", "c", "c"],
        "archetype": ["slow", "fast", "slow", "fast", "slow", "fast"],
        "reference_phase_time_s": [10, 20, 10, 20, 10, 20],
        "delta_phase_time_s": [-2, -.5, -1, -.25, -3, 0],
        "quality_weight": [1, 1, 1, 1, 1, 1],
    })


def test_whole_circuit_baseline_excludes_held_out_circuit() -> None:
    predicted = whole_circuit_baseline(frame(), held_out="c")
    assert predicted.loc[predicted.circuit_id == "c", "predicted_delta_phase_time_s"].round(3).tolist() == [-0.938, -0.938]


def test_archetype_baseline_preserves_slow_fast_difference() -> None:
    predicted = archetype_baseline(frame(), held_out="c")
    assert predicted.loc[predicted.archetype == "slow", "predicted_delta_phase_time_s"].item() == -1.5
    assert predicted.loc[predicted.archetype == "fast", "predicted_delta_phase_time_s"].item() == -.375


def test_circuit_folds_are_sorted_and_complete() -> None:
    assert [fold.held_out for fold in circuit_folds(frame())] == ["a", "b", "c"]
```

- [ ] **Step 2: Run tests and verify RED**

```bash
cd calibration
python -m pytest tests/test_baselines.py -q
```

Expected: `ModuleNotFoundError: No module named 'spa_calibration.baselines'`.

- [ ] **Step 3: Implement weighted baselines and gates**

```python
# calibration/src/spa_calibration/baselines.py
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CircuitFold:
    held_out: str
    training: tuple[str, ...]


def circuit_folds(frame: pd.DataFrame) -> list[CircuitFold]:
    circuits = sorted(frame.circuit_id.unique())
    return [CircuitFold(held_out=circuit, training=tuple(item for item in circuits if item != circuit)) for circuit in circuits]


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    return float(np.average(values.to_numpy(float), weights=weights.to_numpy(float)))


def whole_circuit_baseline(frame: pd.DataFrame, held_out: str) -> pd.DataFrame:
    train = frame[frame.circuit_id != held_out]
    mean = _weighted_mean(train.delta_phase_time_s, train.quality_weight)
    result = frame[frame.circuit_id == held_out].copy()
    result["predicted_delta_phase_time_s"] = mean
    return result


def archetype_baseline(frame: pd.DataFrame, held_out: str) -> pd.DataFrame:
    train = frame[frame.circuit_id != held_out]
    means = train.groupby("archetype").apply(
        lambda group: _weighted_mean(group.delta_phase_time_s, group.quality_weight),
        include_groups=False,
    )
    global_mean = _weighted_mean(train.delta_phase_time_s, train.quality_weight)
    result = frame[frame.circuit_id == held_out].copy()
    result["predicted_delta_phase_time_s"] = result.archetype.map(means).fillna(global_mean)
    return result
```

```yaml
# calibration/config/release-gates.yaml
schema_version: spa-calibration-release-gates/v1
lap_time_mae_s: 0.70
sector_mae_s: 0.25
minimum_speed_mae_kph: 8.0
braking_onset_mae_m: 25.0
maximum_signed_archetype_bias_s: 0.15
minimum_interval_coverage_80: 0.70
requires_baseline_improvement: true
```

- [ ] **Step 4: Verify GREEN**

```bash
cd calibration
python -m pytest tests/test_baselines.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit baselines**

```bash
git add calibration/src/spa_calibration/baselines.py calibration/tests/test_baselines.py calibration/config/release-gates.yaml
git commit -m "feat(calibration-model): add held-out baselines"
```

---

### Task 2: Build a stable encoded design matrix

**Files:**
- Create: `calibration/src/spa_calibration/design_matrix.py`
- Create: `calibration/tests/test_design_matrix.py`
- Create: `calibration/config/model.yaml`
- Modify: `calibration/pyproject.toml`

**Interfaces:**
- Consumes: paired feature frame.
- Produces: `FeatureEncoder.fit()`, `FeatureEncoder.transform()`, `EncodedData`, and `ModelConfig`.

- [ ] **Step 1: Write failing encoder tests**

```python
# calibration/tests/test_design_matrix.py
import pandas as pd
from spa_calibration.design_matrix import FeatureEncoder


def test_encoder_is_stable_under_row_reordering() -> None:
    frame = pd.DataFrame({
        "team_name": ["B", "A", "B"],
        "driver_acronym": ["BB", "AA", "BC"],
        "circuit_id": ["x", "y", "z"],
        "archetype": ["fast", "slow", "fast"],
        "phase_type": ["apex", "braking-onset", "full-power"],
        "mean_curvature_per_m": [.01, .02, .005],
        "peak_curvature_per_m": [.02, .03, .008],
        "gradient_mean": [0, .02, -.01],
        "entry_straight_m": [100, 50, 500],
        "exit_straight_m": [200, 300, 600],
        "sustained_load_s": [2, 1, 4],
        "quality_weight": [.9, 1, .8],
    })
    first = FeatureEncoder.fit(frame)
    second = FeatureEncoder.fit(frame.sample(frac=1, random_state=1))
    assert first.to_dict() == second.to_dict()
    assert first.transform(frame).x.shape[0] == 3


def test_unknown_category_maps_to_explicit_unknown_index() -> None:
    train = pd.DataFrame({
        "team_name": ["A"], "driver_acronym": ["AA"], "circuit_id": ["x"],
        "archetype": ["slow"], "phase_type": ["apex"],
        "mean_curvature_per_m": [.01], "peak_curvature_per_m": [.02], "gradient_mean": [0],
        "entry_straight_m": [100], "exit_straight_m": [200], "sustained_load_s": [1],
        "quality_weight": [1],
    })
    encoded = FeatureEncoder.fit(train).transform(train.assign(team_name="NEW"))
    assert encoded.team_index.tolist() == [0]
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_design_matrix.py -q
```

Expected: missing module.

- [ ] **Step 3: Implement encoder and pin modelling dependencies**

```python
# calibration/src/spa_calibration/design_matrix.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

CONTINUOUS = (
    "mean_curvature_per_m", "peak_curvature_per_m", "gradient_mean",
    "entry_straight_m", "exit_straight_m", "sustained_load_s"
)
CATEGORICAL = ("team_name", "driver_acronym", "circuit_id", "archetype", "phase_type")


@dataclass(frozen=True)
class EncodedData:
    x: np.ndarray
    team_index: np.ndarray
    driver_index: np.ndarray
    circuit_index: np.ndarray
    archetype_index: np.ndarray
    phase_index: np.ndarray
    weights: np.ndarray


@dataclass(frozen=True)
class FeatureEncoder:
    means: dict[str, float]
    scales: dict[str, float]
    categories: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, frame: pd.DataFrame) -> "FeatureEncoder":
        means = {column: float(frame[column].mean()) for column in CONTINUOUS}
        scales = {column: max(float(frame[column].std(ddof=0)), 1e-9) for column in CONTINUOUS}
        categories = {
            column: tuple(["__UNKNOWN__"] + sorted(str(value) for value in frame[column].dropna().unique()))
            for column in CATEGORICAL
        }
        return cls(means=means, scales=scales, categories=categories)

    def _indices(self, frame: pd.DataFrame, column: str) -> np.ndarray:
        mapping = {value: index for index, value in enumerate(self.categories[column])}
        return frame[column].astype(str).map(mapping).fillna(0).to_numpy(np.int32)

    def transform(self, frame: pd.DataFrame) -> EncodedData:
        x = np.column_stack([(frame[column].to_numpy(float) - self.means[column]) / self.scales[column] for column in CONTINUOUS])
        return EncodedData(
            x=x,
            team_index=self._indices(frame, "team_name"),
            driver_index=self._indices(frame, "driver_acronym"),
            circuit_index=self._indices(frame, "circuit_id"),
            archetype_index=self._indices(frame, "archetype"),
            phase_index=self._indices(frame, "phase_type"),
            weights=frame.quality_weight.to_numpy(float),
        )

    def to_dict(self) -> dict[str, object]:
        return {"means": self.means, "scales": self.scales, "categories": {key: list(value) for key, value in self.categories.items()}}
```

Add to `calibration/pyproject.toml`:

```toml
"arviz>=0.20,<1",
"pymc>=5.18,<6",
```

```yaml
# calibration/config/model.yaml
schema_version: spa-calibration-model-config/v1
model_version: spa-corner-transfer/0.1.0
random_seed: 560714
chains: 4
cores: 4
draws: 1000
tune: 1000
target_accept: 0.92
outcomes:
  - delta_phase_time_s
  - delta_minimum_speed_kph
  - delta_exit_speed_100m_kph
  - delta_braking_onset_m
  - delta_full_throttle_fraction
student_t_nu_prior_rate: 0.10
```

- [ ] **Step 4: Verify GREEN**

```bash
cd calibration
python -m pip install -e '.[dev]'
python -m pytest tests/test_design_matrix.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit design matrix**

```bash
git add calibration/src/spa_calibration/design_matrix.py calibration/tests/test_design_matrix.py calibration/config/model.yaml calibration/pyproject.toml
git commit -m "feat(calibration-model): encode phase-level predictors"
```

---

### Task 3: Fit partially pooled outcome models and verify synthetic recovery

**Files:**
- Create: `calibration/src/spa_calibration/hierarchical.py`
- Create: `calibration/src/spa_calibration/model_io.py`
- Create: `calibration/tests/test_hierarchical_recovery.py`
- Create: `calibration/data/fixtures/synthetic-hierarchy.parquet`

**Interfaces:**
- Consumes: `EncodedData`, one outcome vector, and encoder category counts.
- Produces: `fit_outcome_model() -> az.InferenceData`, `posterior_mean_prediction()`, `posterior_draw_predictions()`, `CalibrationFit`, `save_fit()`, and `load_fit()`.

- [ ] **Step 1: Write failing synthetic recovery test**

```python
# calibration/tests/test_hierarchical_recovery.py
import pandas as pd
from spa_calibration.design_matrix import FeatureEncoder
from spa_calibration.hierarchical import FitConfig, fit_outcome_model, posterior_mean_prediction


def test_hierarchy_recovers_global_curvature_and_team_direction() -> None:
    frame = pd.read_parquet("data/fixtures/synthetic-hierarchy.parquet")
    encoder = FeatureEncoder.fit(frame)
    fit = fit_outcome_model(
        frame,
        outcome="delta_phase_time_s",
        encoder=encoder,
        config=FitConfig(draws=250, tune=250, chains=2, cores=1, random_seed=17, target_accept=.9),
    )
    predicted = posterior_mean_prediction(fit, frame, encoder)
    correlation = predicted.corr(frame.delta_phase_time_s)
    assert correlation > .8
    team_means = predicted.groupby(frame.team_name).mean()
    assert team_means["Fast Team"] < team_means["Slow Team"]
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_hierarchical_recovery.py -q
```

Expected: missing module.

- [ ] **Step 3: Implement the Student-t hierarchical model**

```python
# calibration/src/spa_calibration/hierarchical.py
from __future__ import annotations
from dataclasses import dataclass
import arviz as az
import numpy as np
import pandas as pd
import pymc as pm
from .design_matrix import FeatureEncoder


@dataclass(frozen=True)
class FitConfig:
    draws: int = 1000
    tune: int = 1000
    chains: int = 4
    cores: int = 4
    random_seed: int = 560714
    target_accept: float = .92


def fit_outcome_model(frame: pd.DataFrame, outcome: str, encoder: FeatureEncoder, config: FitConfig) -> az.InferenceData:
    encoded = encoder.transform(frame)
    y = frame[outcome].to_numpy(float)
    outcome_mean = float(y.mean())
    outcome_scale = max(float(y.std(ddof=0)), 1e-6)
    y_standardized = (y - outcome_mean) / outcome_scale
    with pm.Model(coords={
        "feature": range(encoded.x.shape[1]),
        "team": range(len(encoder.categories["team_name"])),
        "driver": range(len(encoder.categories["driver_acronym"])),
        "circuit": range(len(encoder.categories["circuit_id"])),
        "archetype": range(len(encoder.categories["archetype"])),
        "phase": range(len(encoder.categories["phase_type"])),
        "observation": range(len(frame)),
    }) as model:
        x = pm.Data("x", encoded.x, dims=("observation", "feature"))
        alpha = pm.Normal("alpha", 0, 1)
        beta = pm.Normal("beta", 0, .5, dims="feature")

        sigma_team = pm.HalfNormal("sigma_team", .5)
        sigma_driver = pm.HalfNormal("sigma_driver", .35)
        sigma_circuit = pm.HalfNormal("sigma_circuit", .5)
        sigma_arch = pm.HalfNormal("sigma_archetype", .4)
        sigma_phase = pm.HalfNormal("sigma_phase", .4)
        team = pm.Normal("team_effect", 0, sigma_team, dims="team")
        driver = pm.Normal("driver_effect", 0, sigma_driver, dims="driver")
        circuit = pm.Normal("circuit_effect", 0, sigma_circuit, dims="circuit")
        archetype = pm.Normal("archetype_effect", 0, sigma_arch, dims="archetype")
        phase = pm.Normal("phase_effect", 0, sigma_phase, dims="phase")

        sigma_team_arch = pm.HalfNormal("sigma_team_archetype", .25)
        team_arch = pm.Normal(
            "team_archetype_effect", 0, sigma_team_arch,
            dims=("team", "archetype")
        )
        mu = (
            alpha + pm.math.dot(x, beta)
            + team[encoded.team_index]
            + driver[encoded.driver_index]
            + circuit[encoded.circuit_index]
            + archetype[encoded.archetype_index]
            + phase[encoded.phase_index]
            + team_arch[encoded.team_index, encoded.archetype_index]
        )
        sigma = pm.HalfNormal("sigma", 1)
        nu = pm.Exponential("nu_minus_two", .1) + 2
        pm.StudentT(
            "observed",
            nu=nu,
            mu=mu,
            sigma=sigma / np.sqrt(np.clip(encoded.weights, .05, 1)),
            observed=y_standardized,
            dims="observation",
        )
        inference = pm.sample(
            draws=config.draws,
            tune=config.tune,
            chains=config.chains,
            cores=config.cores,
            random_seed=config.random_seed,
            target_accept=config.target_accept,
            progressbar=False,
            return_inferencedata=True,
        )
        inference.posterior.attrs["outcome_mean"] = outcome_mean
        inference.posterior.attrs["outcome_scale"] = outcome_scale
        return inference


def posterior_mean_prediction(fit: az.InferenceData, frame: pd.DataFrame, encoder: FeatureEncoder) -> pd.Series:
    encoded = encoder.transform(frame)
    posterior = fit.posterior
    alpha = float(posterior.alpha.mean())
    beta = posterior.beta.mean(("chain", "draw")).to_numpy()
    team = posterior.team_effect.mean(("chain", "draw")).to_numpy()
    driver = posterior.driver_effect.mean(("chain", "draw")).to_numpy()
    circuit = posterior.circuit_effect.mean(("chain", "draw")).to_numpy()
    archetype = posterior.archetype_effect.mean(("chain", "draw")).to_numpy()
    phase = posterior.phase_effect.mean(("chain", "draw")).to_numpy()
    team_arch = posterior.team_archetype_effect.mean(("chain", "draw")).to_numpy()
    values = (
        alpha + encoded.x @ beta
        + team[encoded.team_index]
        + driver[encoded.driver_index]
        + circuit[encoded.circuit_index]
        + archetype[encoded.archetype_index]
        + phase[encoded.phase_index]
        + team_arch[encoded.team_index, encoded.archetype_index]
    )
    mean = float(posterior.attrs["outcome_mean"])
    scale = float(posterior.attrs["outcome_scale"])
    return pd.Series(values * scale + mean, index=frame.index, name="prediction")


def posterior_draw_predictions(
    fit: az.InferenceData,
    frame: pd.DataFrame,
    encoder: FeatureEncoder,
    draw_indices: np.ndarray,
) -> np.ndarray:
    encoded = encoder.transform(frame)
    posterior = fit.posterior.stack(sample=("chain", "draw"))
    alpha = posterior.alpha.to_numpy()[draw_indices]
    beta = posterior.beta.transpose("sample", "feature").to_numpy()[draw_indices]
    team = posterior.team_effect.transpose("sample", "team").to_numpy()[draw_indices]
    driver = posterior.driver_effect.transpose("sample", "driver").to_numpy()[draw_indices]
    circuit = posterior.circuit_effect.transpose("sample", "circuit").to_numpy()[draw_indices]
    archetype = posterior.archetype_effect.transpose("sample", "archetype").to_numpy()[draw_indices]
    phase = posterior.phase_effect.transpose("sample", "phase").to_numpy()[draw_indices]
    team_arch = posterior.team_archetype_effect.transpose("sample", "team", "archetype").to_numpy()[draw_indices]
    values = (
        alpha[:, None]
        + beta @ encoded.x.T
        + team[:, encoded.team_index]
        + driver[:, encoded.driver_index]
        + circuit[:, encoded.circuit_index]
        + archetype[:, encoded.archetype_index]
        + phase[:, encoded.phase_index]
        + team_arch[:, encoded.team_index, encoded.archetype_index]
    )
    mean = float(fit.posterior.attrs["outcome_mean"])
    scale = float(fit.posterior.attrs["outcome_scale"])
    return values * scale + mean
```

```python
# calibration/src/spa_calibration/model_io.py
from dataclasses import dataclass
from pathlib import Path
import arviz as az
import orjson
from .design_matrix import FeatureEncoder


@dataclass(frozen=True)
class CalibrationFit:
    model_version: str
    outcomes: dict[str, az.InferenceData]
    encoder: FeatureEncoder
    training_manifest_checksum: str
    random_seed: int


def save_fit(fit: CalibrationFit, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    metadata = {
        "modelVersion": fit.model_version,
        "encoder": fit.encoder.to_dict(),
        "trainingManifestChecksum": fit.training_manifest_checksum,
        "randomSeed": fit.random_seed,
        "outcomes": sorted(fit.outcomes),
    }
    (directory / "model-summary.json").write_bytes(orjson.dumps(metadata, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2))
    for outcome, inference in fit.outcomes.items():
        inference.to_netcdf(directory / f"{outcome}.nc")


def load_fit(directory: Path) -> CalibrationFit:
    metadata = orjson.loads((directory / "model-summary.json").read_bytes())
    encoder = FeatureEncoder(
        means={key: float(value) for key, value in metadata["encoder"]["means"].items()},
        scales={key: float(value) for key, value in metadata["encoder"]["scales"].items()},
        categories={key: tuple(value) for key, value in metadata["encoder"]["categories"].items()},
    )
    outcomes = {outcome: az.from_netcdf(directory / f"{outcome}.nc") for outcome in metadata["outcomes"]}
    return CalibrationFit(
        model_version=metadata["modelVersion"],
        outcomes=outcomes,
        encoder=encoder,
        training_manifest_checksum=metadata["trainingManifestChecksum"],
        random_seed=int(metadata["randomSeed"]),
    )
```

- [ ] **Step 4: Verify GREEN and diagnostics**

```bash
cd calibration
python -m pytest tests/test_hierarchical_recovery.py -q
```

Expected: test passes; no divergent-transition warning in captured output.

- [ ] **Step 5: Commit hierarchy**

```bash
git add calibration/src/spa_calibration/{hierarchical,model_io}.py calibration/tests/test_hierarchical_recovery.py calibration/data/fixtures/synthetic-hierarchy.parquet
git commit -m "feat(calibration-model): fit partially pooled phase deltas"
```

---

### Task 4: Port the physics prior and optimize a bounded racing line

**Files:**
- Create: `calibration/src/spa_calibration/vehicle_prior.py`
- Create: `calibration/src/spa_calibration/line_optimizer.py`
- Create: `calibration/tests/test_vehicle_prior.py`
- Create: `calibration/tests/test_line_optimizer.py`
- Create: `calibration/data/fixtures/spa-line-small.parquet`

**Interfaces:**
- Consumes: canonical line, road boundaries, vehicle parameters, phase corrections.
- Produces: `simulate_lap() -> LapSolution`, `optimize_line() -> OptimizedLine`, and trace channels derived from one dynamics pass.

- [ ] **Step 1: Write failing feasibility and coupling tests**

```python
# calibration/tests/test_vehicle_prior.py
import pandas as pd
from spa_calibration.vehicle_prior import VehicleParameters, simulate_lap


def test_speed_controls_energy_and_time_come_from_same_solution() -> None:
    line = pd.read_parquet("data/fixtures/spa-line-small.parquet")
    solution = simulate_lap(line, VehicleParameters.default_2026())
    trace = solution.trace
    assert (trace.speed_kph >= 0).all()
    assert trace.elapsed_s.is_monotonic_increasing
    assert ((trace.throttle_pct == 0) | (trace.brake_pct < 5)).mean() > .95
    assert trace.battery_kj.between(0, solution.parameters.energy_window_kj).all()
    assert abs(solution.lap_time_s - trace.elapsed_s.iloc[-1]) < 1e-6


def test_smaller_energy_window_reduces_deployment_and_does_not_break_battery_bounds() -> None:
    line = pd.read_parquet("data/fixtures/spa-line-small.parquet")
    baseline = VehicleParameters.default_2026()
    constrained = baseline.__class__(**{**baseline.__dict__, "initial_battery_kj": 900, "energy_window_kj": 1200, "battery_reserve_kj": 300})
    full = simulate_lap(line, baseline)
    limited = simulate_lap(line, constrained)
    assert limited.ers_scale < full.ers_scale
    assert limited.lap_time_s > full.lap_time_s
    assert limited.trace.battery_kj.min() >= constrained.battery_reserve_kj
```

```python
# calibration/tests/test_line_optimizer.py
import pandas as pd
from spa_calibration.line_optimizer import LineOptimizationConfig, optimize_line
from spa_calibration.vehicle_prior import VehicleParameters


def test_optimizer_stays_inside_boundaries_and_does_not_slow_reference() -> None:
    track = pd.read_parquet("data/fixtures/spa-line-small.parquet")
    result = optimize_line(track, VehicleParameters.default_2026(), LineOptimizationConfig(max_iterations=15))
    assert result.line.lateral_fraction.between(-1, 1).all()
    assert result.optimized_lap_time_s <= result.reference_lap_time_s + 1e-6
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_vehicle_prior.py tests/test_line_optimizer.py -q
```

Expected: missing modules.

- [ ] **Step 3: Implement the point-mass prior and bounded offset optimization**

```python
# calibration/src/spa_calibration/vehicle_prior.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

G = 9.81


@dataclass(frozen=True)
class VehicleParameters:
    mass_kg: float
    ice_power_kw: float
    ers_power_kw: float
    energy_window_kj: float
    initial_battery_kj: float
    battery_reserve_kj: float
    regen_efficiency: float
    drive_efficiency: float
    drag_corner: float
    drag_straight: float
    downforce_corner: float
    downforce_straight: float
    mu_lateral: float
    mu_brake: float
    rolling_resistance_n: float
    top_speed_kph: float

    @classmethod
    def default_2026(cls) -> "VehicleParameters":
        return cls(
            mass_kg=800,
            ice_power_kw=440,
            ers_power_kw=350,
            energy_window_kj=4000,
            initial_battery_kj=3350,
            battery_reserve_kj=350,
            regen_efficiency=.78,
            drive_efficiency=.93,
            drag_corner=.92,
            drag_straight=.45,
            downforce_corner=3.55,
            downforce_straight=2.35,
            mu_lateral=1.68,
            mu_brake=1.92,
            rolling_resistance_n=190,
            top_speed_kph=345,
        )


@dataclass(frozen=True)
class LapSolution:
    lap_time_s: float
    trace: pd.DataFrame
    parameters: VehicleParameters
    ers_scale: float


def _lateral_speed_limit(frame: pd.DataFrame, parameters: VehicleParameters) -> np.ndarray:
    curvature = np.maximum(np.abs(frame.curvature_per_m.to_numpy(float)), 1e-7)
    straight_mode = curvature < .0018
    downforce = np.where(straight_mode, parameters.downforce_straight, parameters.downforce_corner)
    denominator = np.maximum(curvature - parameters.mu_lateral * downforce / parameters.mass_kg, 1e-6)
    limit = np.sqrt(parameters.mu_lateral * G / denominator)
    return np.minimum(limit, parameters.top_speed_kph / 3.6)


def _deployment_priority(frame: pd.DataFrame, lateral_limit: np.ndarray) -> np.ndarray:
    curvature = np.abs(frame.curvature_per_m.to_numpy(float))
    curvature_score = 1 - np.clip(curvature / .01, 0, 1)
    speed_score = np.clip(lateral_limit / (300 / 3.6), 0, 1)
    exit_score = np.clip(frame.get("exit_straight_m", pd.Series(0, index=frame.index)).to_numpy(float) / 700, 0, 1)
    return np.clip(.15 + .45 * curvature_score + .25 * speed_score + .15 * exit_score, 0, 1)


def _solve_speed_envelope(
    frame: pd.DataFrame,
    parameters: VehicleParameters,
    lateral_limit: np.ndarray,
    deploy_fraction: np.ndarray,
) -> np.ndarray:
    distance = frame.distance_m.to_numpy(float)
    ds = np.diff(distance, append=distance[-1] + np.median(np.diff(distance)))
    speed = lateral_limit.copy()
    curvature = np.abs(frame.curvature_per_m.to_numpy(float))
    for _ in range(6):
        for index in range(1, len(speed)):
            prior = max(speed[index - 1], 5)
            straight_mode = curvature[index - 1] < .0018 and prior > 45
            drag = parameters.drag_straight if straight_mode else parameters.drag_corner
            wheel_power_w = (
                parameters.ice_power_kw
                + parameters.ers_power_kw * deploy_fraction[index - 1]
            ) * 1000 * parameters.drive_efficiency
            drag_force = drag * prior * prior + parameters.rolling_resistance_n
            drive_accel = max(0, wheel_power_w / (parameters.mass_kg * prior) - drag_force / parameters.mass_kg)
            speed[index] = min(speed[index], np.sqrt(prior * prior + 2 * drive_accel * ds[index - 1]))
        for index in range(len(speed) - 2, -1, -1):
            downforce_brake = parameters.downforce_corner * speed[index + 1] ** 2 / parameters.mass_kg
            braking = parameters.mu_brake * (G + downforce_brake)
            speed[index] = min(speed[index], np.sqrt(speed[index + 1] ** 2 + 2 * braking * ds[index]))
    return speed


def _derive_controls(speed: np.ndarray, distance: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ds = np.diff(distance, append=distance[-1] + np.median(np.diff(distance)))
    dt = ds / np.maximum(speed, 1)
    elapsed = np.cumsum(dt) - dt[0]
    acceleration = np.gradient(speed, np.maximum(elapsed, 1e-6))
    positive = np.maximum(acceleration, 0)
    negative = np.maximum(-acceleration, 0)
    throttle = np.clip(positive / max(np.quantile(positive, .95), 1e-6) * 100, 0, 100)
    brake = np.clip(negative / max(np.quantile(negative, .95), 1e-6) * 100, 0, 100)
    throttle[brake > 5] = 0
    return dt, elapsed, throttle, brake


def _integrate_battery(
    dt: np.ndarray,
    deploy_kw: np.ndarray,
    regen_kw: np.ndarray,
    parameters: VehicleParameters,
) -> np.ndarray:
    battery = np.empty(len(dt))
    battery[0] = parameters.initial_battery_kj
    for index in range(1, len(dt)):
        battery[index] = np.clip(
            battery[index - 1] + (regen_kw[index] - deploy_kw[index]) * dt[index],
            parameters.battery_reserve_kj,
            parameters.energy_window_kj,
        )
    return battery


def simulate_lap(line: pd.DataFrame, parameters: VehicleParameters, corrections: pd.DataFrame | None = None) -> LapSolution:
    frame = line.sort_values("distance_m").reset_index(drop=True).copy()
    distance = frame.distance_m.to_numpy(float)
    lateral_limit = _lateral_speed_limit(frame, parameters)
    if corrections is not None and "speed_correction_ms" in corrections:
        correction = np.interp(distance, corrections.distance_m, corrections.speed_correction_ms)
        lateral_limit = np.maximum(10, lateral_limit + correction)

    priority = _deployment_priority(frame, lateral_limit)
    ers_scale = 1.0
    for _ in range(5):
        deploy_fraction = priority * ers_scale
        speed = _solve_speed_envelope(frame, parameters, lateral_limit, deploy_fraction)
        dt, elapsed, throttle, brake = _derive_controls(speed, distance)
        deploy_kw = parameters.ers_power_kw * deploy_fraction * (throttle / 100)
        regen_kw = parameters.ers_power_kw * parameters.regen_efficiency * (brake / 100)
        deploy_energy_kj = float(np.sum(deploy_kw * dt))
        recoverable_kj = float(np.sum(regen_kw * dt))
        available_kj = max(
            0,
            parameters.initial_battery_kj - parameters.battery_reserve_kj + recoverable_kj,
        )
        if deploy_energy_kj <= available_kj + 1e-6:
            break
        ers_scale *= max(.05, available_kj / max(deploy_energy_kj, 1e-6))

    battery = _integrate_battery(dt, deploy_kw, regen_kw, parameters)
    gear = np.clip(np.searchsorted(np.array([90, 125, 160, 195, 230, 270, 310]), speed * 3.6) + 1, 1, 8)
    acceleration = np.gradient(speed, np.maximum(elapsed, 1e-6))
    trace = frame.assign(
        progress=distance / distance[-1],
        speed_kph=speed * 3.6,
        throttle_pct=throttle,
        brake_pct=brake,
        gear=gear,
        longitudinal_g=acceleration / G,
        lateral_g=speed * speed * frame.curvature_per_m.to_numpy(float) / G,
        deploy_kw=deploy_kw,
        regen_kw=regen_kw,
        battery_kj=battery,
        elapsed_s=elapsed,
    )
    return LapSolution(float(dt.sum()), trace, parameters, ers_scale)
```


```python
# calibration/src/spa_calibration/line_optimizer.py
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from .vehicle_prior import LapSolution, VehicleParameters, simulate_lap


@dataclass(frozen=True)
class LineOptimizationConfig:
    control_points: int = 48
    max_iterations: int = 80
    smoothness_weight: float = .08


@dataclass(frozen=True)
class OptimizedLine:
    line: pd.DataFrame
    reference_lap_time_s: float
    optimized_lap_time_s: float
    solution: LapSolution


def optimize_line(track: pd.DataFrame, parameters: VehicleParameters, config: LineOptimizationConfig, corrections: pd.DataFrame | None = None) -> OptimizedLine:
    reference = simulate_lap(track.assign(lateral_fraction=0.0), parameters, corrections)
    grid = np.linspace(0, 1, config.control_points, endpoint=False)

    def materialize(values: np.ndarray) -> pd.DataFrame:
        progress = track.distance_m.to_numpy(float) / track.distance_m.iloc[-1]
        extended_x = np.r_[grid, 1]
        extended_y = np.r_[values, values[0]]
        lateral = np.interp(progress, extended_x, extended_y)
        width = np.minimum(track.left_width_m.to_numpy(float), track.right_width_m.to_numpy(float))
        x = track.center_x_m + track.normal_x * lateral * width
        y = track.center_y_m + track.normal_y * lateral * width
        heading = np.unwrap(np.arctan2(np.gradient(y), np.gradient(x)))
        curvature = np.gradient(heading, track.distance_m.to_numpy(float))
        return track.assign(x_m=x, y_m=y, curvature_per_m=curvature, lateral_fraction=lateral)

    def objective(values: np.ndarray) -> float:
        line = materialize(values)
        lap = simulate_lap(line, parameters, corrections).lap_time_s
        smoothness = np.mean(np.diff(np.r_[values, values[:2]], n=2) ** 2)
        return lap + config.smoothness_weight * smoothness

    result = minimize(
        objective,
        np.zeros(config.control_points),
        bounds=[(-.96, .96)] * config.control_points,
        method="L-BFGS-B",
        options={"maxiter": config.max_iterations, "ftol": 1e-6},
    )
    line = materialize(result.x)
    solution = simulate_lap(line, parameters, corrections)
    return OptimizedLine(line, reference.lap_time_s, solution.lap_time_s, solution)
```

- [ ] **Step 4: Verify GREEN**

```bash
cd calibration
python -m pytest tests/test_vehicle_prior.py tests/test_line_optimizer.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit physics prior**

```bash
git add calibration/src/spa_calibration/{vehicle_prior,line_optimizer}.py calibration/tests/test_vehicle_prior.py calibration/tests/test_line_optimizer.py calibration/data/fixtures/spa-line-small.parquet
git commit -m "feat(spa-prediction): add coupled minimum-time prior"
```

---

### Task 5: Add regime comparison and leave-one-circuit-out validation

**Files:**
- Create: `calibration/src/spa_calibration/regimes.py`
- Create: `calibration/src/spa_calibration/validation.py`
- Create: `calibration/tests/test_regimes.py`
- Create: `calibration/tests/test_validation.py`
- Create: `calibration/config/regulation-regimes.yaml`

**Interfaces:**
- Consumes: corpus, baselines, fit function.
- Produces: `choose_regime_model()`, `run_loco_validation() -> ValidationReport`, and release gate status.

- [ ] **Step 1: Write failing regime and validation tests**

```python
# calibration/tests/test_regimes.py
import pandas as pd
from spa_calibration.regimes import choose_regime_model


def test_piecewise_model_is_rejected_without_held_out_gain() -> None:
    scores = pd.DataFrame({
        "model": ["pooled", "piecewise", "continuous"],
        "mean_lap_mae_s": [.52, .51, .55],
        "standard_error_s": [.03, .04, .03],
        "parameter_count": [20, 32, 24],
    })
    assert choose_regime_model(scores) == "pooled"
```

```python
# calibration/tests/test_validation.py
from spa_calibration.validation import ReleaseGates, ValidationMetrics, evaluate_release_gates


def test_release_requires_every_metric_and_baseline_improvement() -> None:
    gates = ReleaseGates(.7, .25, 8, 25, .15, .7, True)
    metrics = ValidationMetrics(
        lap_time_mae_s=.55,
        sector_mae_s=.2,
        minimum_speed_mae_kph=6,
        braking_onset_mae_m=18,
        maximum_signed_archetype_bias_s=.08,
        interval_coverage_80=.76,
        model_lap_mae_s=.55,
        baseline_lap_mae_s=.72,
    )
    assert evaluate_release_gates(metrics, gates).passed
    assert not evaluate_release_gates(metrics.__class__(**{**metrics.__dict__, "model_lap_mae_s": .75}), gates).passed
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_regimes.py tests/test_validation.py -q
```

Expected: missing modules.

- [ ] **Step 3: Implement parsimonious regime selection and gate evaluation**

```python
# calibration/src/spa_calibration/regimes.py
import pandas as pd


def choose_regime_model(scores: pd.DataFrame) -> str:
    ordered = scores.sort_values(["mean_lap_mae_s", "parameter_count"]).reset_index(drop=True)
    best = ordered.iloc[0]
    pooled = ordered[ordered.model == "pooled"].iloc[0]
    improvement = pooled.mean_lap_mae_s - best.mean_lap_mae_s
    combined_error = (pooled.standard_error_s ** 2 + best.standard_error_s ** 2) ** .5
    if best.model != "pooled" and improvement <= combined_error:
        return "pooled"
    return str(best.model)
```

```python
# calibration/src/spa_calibration/validation.py
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class ReleaseGates:
    lap_time_mae_s: float
    sector_mae_s: float
    minimum_speed_mae_kph: float
    braking_onset_mae_m: float
    maximum_signed_archetype_bias_s: float
    minimum_interval_coverage_80: float
    requires_baseline_improvement: bool


@dataclass(frozen=True)
class ValidationMetrics:
    lap_time_mae_s: float
    sector_mae_s: float
    minimum_speed_mae_kph: float
    braking_onset_mae_m: float
    maximum_signed_archetype_bias_s: float
    interval_coverage_80: float
    model_lap_mae_s: float
    baseline_lap_mae_s: float


@dataclass(frozen=True)
class GateEvaluation:
    passed: bool
    checks: dict[str, bool]


def evaluate_release_gates(metrics: ValidationMetrics, gates: ReleaseGates) -> GateEvaluation:
    checks = {
        "lap_time_mae": metrics.lap_time_mae_s <= gates.lap_time_mae_s,
        "sector_mae": metrics.sector_mae_s <= gates.sector_mae_s,
        "minimum_speed_mae": metrics.minimum_speed_mae_kph <= gates.minimum_speed_mae_kph,
        "braking_onset_mae": metrics.braking_onset_mae_m <= gates.braking_onset_mae_m,
        "archetype_bias": abs(metrics.maximum_signed_archetype_bias_s) <= gates.maximum_signed_archetype_bias_s,
        "interval_coverage": metrics.interval_coverage_80 >= gates.minimum_interval_coverage_80,
        "baseline_improvement": (not gates.requires_baseline_improvement) or metrics.model_lap_mae_s < metrics.baseline_lap_mae_s,
    }
    return GateEvaluation(all(checks.values()), checks)
```

Add scoring and orchestration in the same file:

```python
import numpy as np
import pandas as pd
from .baselines import circuit_folds


def score_fold(test: pd.DataFrame, prediction: pd.DataFrame, baseline: pd.DataFrame, held_out: str) -> dict[str, object]:
    joined = test[[
        "pair_id", "archetype", "sector", "delta_phase_time_s", "delta_minimum_speed_kph",
        "delta_braking_onset_m"
    ]].merge(prediction, on="pair_id", validate="one_to_one")
    baseline_joined = test[["pair_id", "delta_phase_time_s"]].merge(
        baseline[["pair_id", "predicted_delta_phase_time_s"]], on="pair_id", validate="one_to_one"
    )
    phase_error = joined.predicted_delta_phase_time_s - joined.delta_phase_time_s
    speed_error = joined.predicted_delta_minimum_speed_kph - joined.delta_minimum_speed_kph
    brake_error = joined.predicted_delta_braking_onset_m - joined.delta_braking_onset_m
    lap_actual = float(test.delta_phase_time_s.sum())
    lap_predicted = float(joined.predicted_delta_phase_time_s.sum())
    lap_baseline = float(baseline_joined.predicted_delta_phase_time_s.sum())
    sector_errors = joined.groupby("sector").apply(
        lambda group: float(group.predicted_delta_phase_time_s.sum() - group.delta_phase_time_s.sum()),
        include_groups=False,
    ) if "sector" in joined else pd.Series([lap_predicted - lap_actual])
    archetype_bias = joined.assign(error=phase_error).groupby("archetype").error.mean()
    covered = (
        (joined.delta_phase_time_s >= joined.lower80_delta_phase_time_s)
        & (joined.delta_phase_time_s <= joined.upper80_delta_phase_time_s)
    ).mean()
    return {
        "held_out": held_out,
        "lap_error_s": lap_predicted - lap_actual,
        "baseline_lap_error_s": lap_baseline - lap_actual,
        "sector_absolute_errors_s": [abs(float(value)) for value in sector_errors],
        "minimum_speed_absolute_errors_kph": np.abs(speed_error).tolist(),
        "braking_onset_absolute_errors_m": np.abs(brake_error).tolist(),
        "archetype_bias_s": {str(key): float(value) for key, value in archetype_bias.items()},
        "interval_coverage_80": float(covered),
    }


def aggregate_fold_metrics(rows: list[dict[str, object]]) -> ValidationMetrics:
    lap_errors = np.asarray([abs(row["lap_error_s"]) for row in rows], dtype=float)
    baseline_errors = np.asarray([abs(row["baseline_lap_error_s"]) for row in rows], dtype=float)
    sector_errors = np.concatenate([np.asarray(row["sector_absolute_errors_s"], dtype=float) for row in rows])
    speed_errors = np.concatenate([np.asarray(row["minimum_speed_absolute_errors_kph"], dtype=float) for row in rows])
    brake_errors = np.concatenate([np.asarray(row["braking_onset_absolute_errors_m"], dtype=float) for row in rows])
    biases = [abs(value) for row in rows for value in row["archetype_bias_s"].values()]
    return ValidationMetrics(
        lap_time_mae_s=float(lap_errors.mean()),
        sector_mae_s=float(sector_errors.mean()),
        minimum_speed_mae_kph=float(speed_errors.mean()),
        braking_onset_mae_m=float(brake_errors.mean()),
        maximum_signed_archetype_bias_s=float(max(biases, default=0)),
        interval_coverage_80=float(np.mean([row["interval_coverage_80"] for row in rows])),
        model_lap_mae_s=float(lap_errors.mean()),
        baseline_lap_mae_s=float(baseline_errors.mean()),
    )


def run_loco_validation(
    paired_features: pd.DataFrame,
    *,
    fit_fold: Callable[[pd.DataFrame, pd.DataFrame, str], pd.DataFrame],
    baseline_fold: Callable[[pd.DataFrame, str], pd.DataFrame],
    gates: ReleaseGates,
) -> dict[str, object]:
    fold_rows: list[dict[str, object]] = []
    for fold in circuit_folds(paired_features):
        train = paired_features[paired_features.circuit_id != fold.held_out]
        test = paired_features[paired_features.circuit_id == fold.held_out]
        prediction = fit_fold(train, test, fold.held_out)
        baseline = baseline_fold(paired_features, fold.held_out)
        fold_rows.append(score_fold(test, prediction, baseline, fold.held_out))
    metrics = aggregate_fold_metrics(fold_rows)
    evaluation = evaluate_release_gates(metrics, gates)
    return {
        "folds": fold_rows,
        "metrics": asdict(metrics),
        "release_gates": {"passed": evaluation.passed, "checks": evaluation.checks},
    }
```

- [ ] **Step 4: Verify GREEN**

```bash
cd calibration
python -m pytest tests/test_regimes.py tests/test_validation.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit validation**

```bash
git add calibration/src/spa_calibration/{regimes,validation}.py calibration/tests/test_regimes.py calibration/tests/test_validation.py calibration/config/regulation-regimes.yaml
git commit -m "feat(calibration-model): validate with circuit holdouts"
```

---

### Task 6: Compute Spa analogue weights and coherent posterior lap samples

**Files:**
- Create: `calibration/src/spa_calibration/analogues.py`
- Create: `calibration/src/spa_calibration/spa_predictor.py`
- Create: `calibration/tests/test_analogues.py`
- Create: `calibration/tests/test_spa_predictor.py`
- Create: `calibration/config/spa-analogues.yaml`

**Interfaces:**
- Consumes: Spa phase features, training phase features, `CalibrationFit`, team priors, and road geometry.
- Produces: `nearest_analogues()`, `predict_spa_team()`, and `predict_field_best()`.

- [ ] **Step 1: Write failing analogue and coherence tests**

```python
# calibration/tests/test_analogues.py
import pandas as pd
from spa_calibration.analogues import nearest_analogues


def test_weights_sum_to_one_and_prefer_feature_match() -> None:
    spa = pd.Series({"mean_curvature_per_m": .01, "entry_straight_m": 500, "exit_straight_m": 100})
    candidates = pd.DataFrame({
        "phase_id": ["close", "far"],
        "mean_curvature_per_m": [.011, .001],
        "entry_straight_m": [480, 50],
        "exit_straight_m": [110, 600],
    })
    result = nearest_analogues(spa, candidates, k=2)
    assert abs(result.weight.sum() - 1) < 1e-9
    assert result.iloc[0].phase_id == "close"
```

```python
# calibration/tests/test_spa_predictor.py
from spa_calibration.spa_predictor import TeamLapSample, predict_field_best


def test_field_best_uses_one_complete_team_per_draw() -> None:
    samples = [
        TeamLapSample("A", 0, 100.0, (30, 40, 30)),
        TeamLapSample("B", 0, 99.5, (35, 34.5, 30)),
        TeamLapSample("A", 1, 98.0, (30, 38, 30)),
        TeamLapSample("B", 1, 98.5, (32, 36.5, 30)),
    ]
    field = predict_field_best(samples)
    assert [(row.draw, row.team_name, row.lap_time_s) for row in field] == [(0, "B", 99.5), (1, "A", 98.0)]
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_analogues.py tests/test_spa_predictor.py -q
```

Expected: missing modules.

- [ ] **Step 3: Implement standardized similarity and coherent field minimum**

```python
# calibration/src/spa_calibration/analogues.py
import numpy as np
import pandas as pd

SIMILARITY_FEATURES = (
    "mean_curvature_per_m", "peak_curvature_per_m", "gradient_mean",
    "entry_straight_m", "exit_straight_m", "sustained_load_s"
)


def nearest_analogues(spa_phase: pd.Series, candidates: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    scales = candidates[list(SIMILARITY_FEATURES)].std(ddof=0).replace(0, 1)
    delta = (candidates[list(SIMILARITY_FEATURES)] - spa_phase[list(SIMILARITY_FEATURES)]) / scales
    distance = np.sqrt((delta * delta).sum(axis=1))
    selected = candidates.assign(distance=distance).nsmallest(k, "distance").copy()
    raw = np.exp(-selected.distance.to_numpy(float) ** 2 / 2)
    selected["weight"] = raw / raw.sum()
    return selected.sort_values(["distance", "phase_id"]).reset_index(drop=True)
```

```python
# calibration/src/spa_calibration/spa_predictor.py
from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class TeamLapSample:
    team_name: str
    draw: int
    lap_time_s: float
    sectors_s: tuple[float, float, float]


@dataclass(frozen=True)
class FieldBestSample:
    draw: int
    team_name: str
    lap_time_s: float
    sectors_s: tuple[float, float, float]


def predict_field_best(samples: list[TeamLapSample]) -> list[FieldBestSample]:
    by_draw: dict[int, list[TeamLapSample]] = defaultdict(list)
    for sample in samples:
        by_draw[sample.draw].append(sample)
    result: list[FieldBestSample] = []
    for draw in sorted(by_draw):
        winner = min(by_draw[draw], key=lambda row: row.lap_time_s)
        result.append(FieldBestSample(draw, winner.team_name, winner.lap_time_s, winner.sectors_s))
    return result
```

Add correction transfer, iteration, team support, and trace summarization:

```python
import numpy as np
import pandas as pd
from .analogues import nearest_analogues
from .hierarchical import posterior_draw_predictions
from .model_io import CalibrationFit
from .line_optimizer import LineOptimizationConfig, optimize_line
from .vehicle_prior import VehicleParameters, simulate_lap


def build_spa_correction_draws(
    fit: CalibrationFit,
    spa_features: pd.DataFrame,
    team_name: str,
    driver_acronym: str,
    draw_count: int,
    random_seed: int,
) -> list[pd.DataFrame]:
    frame = spa_features.assign(
        team_name=team_name,
        driver_acronym=driver_acronym,
        circuit_id="__UNKNOWN__",
        quality_weight=1.0,
    )
    available = fit.outcomes["delta_phase_time_s"].posterior.sizes["chain"] * fit.outcomes["delta_phase_time_s"].posterior.sizes["draw"]
    rng = np.random.default_rng(random_seed)
    indices = rng.choice(available, size=min(draw_count, available), replace=False)
    predictions = {
        outcome: posterior_draw_predictions(inference, frame, fit.encoder, indices)
        for outcome, inference in fit.outcomes.items()
    }
    draws: list[pd.DataFrame] = []
    for draw_index in range(len(indices)):
        draws.append(pd.DataFrame({
            "complex_id": frame.complex_id,
            "phase_type": frame.phase_type,
            "distance_m": frame.apex_distance_m,
            "speed_correction_ms": predictions["delta_minimum_speed_kph"][draw_index] / 3.6,
            "phase_time_correction_s": predictions["delta_phase_time_s"][draw_index],
            "braking_onset_correction_m": predictions["delta_braking_onset_m"][draw_index],
            "exit_speed_correction_ms": predictions["delta_exit_speed_100m_kph"][draw_index] / 3.6,
            "full_throttle_fraction_correction": predictions["delta_full_throttle_fraction"][draw_index],
        }))
    return draws


def build_analogue_evidence(spa_features: pd.DataFrame, training_features: pd.DataFrame, k: int = 7) -> dict[str, pd.DataFrame]:
    evidence: dict[str, pd.DataFrame] = {}
    for row in spa_features.itertuples(index=False):
        candidates = training_features[
            (training_features.phase_type == row.phase_type)
            & (training_features.archetype == row.archetype)
        ].copy()
        candidates["phase_id"] = candidates.pair_id
        evidence[f"{row.complex_id}|{row.phase_type}"] = nearest_analogues(
            pd.Series(row._asdict()), candidates, k=min(k, len(candidates))
        ) if len(candidates) else candidates.assign(distance=[], weight=[])
    return evidence

def sector_times(trace: pd.DataFrame) -> tuple[float, float, float]:
    values = []
    for sector in (1, 2, 3):
        rows = trace[trace.sector == sector]
        values.append(float(rows.elapsed_s.iloc[-1] - rows.elapsed_s.iloc[0]))
    return tuple(values)


def line_change_m(previous: pd.DataFrame, current: pd.DataFrame) -> float:
    return float(np.max(np.hypot(current.x_m.to_numpy() - previous.x_m.to_numpy(), current.y_m.to_numpy() - previous.y_m.to_numpy())))


def predict_spa_team(
    team_name: str,
    driver_acronym: str,
    posterior_draws: list[pd.DataFrame],
    spa_track: pd.DataFrame,
    spa_features: pd.DataFrame,
    parameters: VehicleParameters,
) -> tuple[list[TeamLapSample], dict[int, pd.DataFrame]]:
    samples: list[TeamLapSample] = []
    traces: dict[int, pd.DataFrame] = {}
    for draw_index, corrections in enumerate(posterior_draws):
        required = {"distance_m", "speed_correction_ms", "phase_time_correction_s", "braking_onset_correction_m", "exit_speed_correction_ms"}
        missing = required - set(corrections.columns)
        if missing:
            raise ValueError(f"Spa correction draw missing columns: {sorted(missing)}")
        line = spa_track.copy()
        prior_lap_time = float("inf")
        for _ in range(6):
            optimized = optimize_line(line, parameters, LineOptimizationConfig(), corrections)
            solution = simulate_lap(optimized.line, parameters, corrections)
            if abs(prior_lap_time - solution.lap_time_s) < .01 and line_change_m(line, optimized.line) < .05:
                break
            prior_lap_time = solution.lap_time_s
            line = optimized.line
        samples.append(TeamLapSample(team_name, draw_index, solution.lap_time_s, sector_times(solution.trace)))
        traces[draw_index] = solution.trace
    return samples, traces


def team_is_supported(samples: list[TeamLapSample], minimum_draws: int = 200) -> bool:
    if len(samples) < minimum_draws:
        return False
    lap_times = np.asarray([row.lap_time_s for row in samples], dtype=float)
    interval_width = float(np.quantile(lap_times, .9) - np.quantile(lap_times, .1))
    return np.isfinite(lap_times).all() and interval_width <= 1.8


def browser_trace_rows(trace: pd.DataFrame) -> list[dict[str, object]]:
    mapping = {
        "elapsed_s": "elapsedSeconds",
        "speed_kph": "speedKph",
        "throttle_pct": "throttlePct",
        "brake_pct": "brakePct",
        "longitudinal_g": "longitudinalG",
        "lateral_g": "lateralG",
        "deploy_kw": "deployKw",
        "regen_kw": "regenKw",
        "battery_kj": "batteryKj",
    }
    columns = [
        "progress", "elapsed_s", "speed_kph", "throttle_pct", "brake_pct", "gear",
        "longitudinal_g", "lateral_g", "deploy_kw", "regen_kw", "battery_kj",
        "lower80SpeedKph", "upper80SpeedKph"
    ]
    available = [column for column in columns if column in trace]
    renamed = trace[available].rename(columns=mapping)
    return renamed.where(pd.notna(renamed), None).to_dict(orient="records")


def summarize_team_prediction(
    team_name: str,
    samples: list[TeamLapSample],
    traces: dict[int, pd.DataFrame],
) -> dict[str, object]:
    lap_times = np.asarray([row.lap_time_s for row in samples], dtype=float)
    representative = samples[int(np.argmin(np.abs(lap_times - np.median(lap_times))))]
    trace = traces[representative.draw]
    return {
        "slug": team_name.lower().replace(" ", "-"),
        "teamName": team_name,
        "supported": team_is_supported(samples),
        "lapTimeSeconds": {
            "lower80": float(np.quantile(lap_times, .1)),
            "median": float(np.quantile(lap_times, .5)),
            "upper80": float(np.quantile(lap_times, .9)),
        },
        "trace": browser_trace_rows(trace),
        "timingTable": trace[["progress", "elapsed_s"]].assign(time=lambda frame: frame.elapsed_s / frame.elapsed_s.iloc[-1])[["progress", "time"]].to_dict(orient="records"),
        "disclosure": "Team-level prediction is shown only when posterior support and interval width pass stability checks.",
        "provenance": {"representativeDraw": representative.draw},
    }


def summarize_field_best(field_samples: list[FieldBestSample], traces_by_team_draw: dict[tuple[str, int], pd.DataFrame]) -> dict[str, object]:
    lap_times = np.asarray([row.lap_time_s for row in field_samples], dtype=float)
    median_index = int(np.argmin(np.abs(lap_times - np.median(lap_times))))
    representative = field_samples[median_index]
    grid = traces_by_team_draw[(representative.team_name, representative.draw)].progress.to_numpy(float)
    stacked_speed = np.vstack([
        np.interp(grid, traces_by_team_draw[(row.team_name, row.draw)].progress, traces_by_team_draw[(row.team_name, row.draw)].speed_kph)
        for row in field_samples
    ])
    trace = traces_by_team_draw[(representative.team_name, representative.draw)].copy()
    trace["lower80SpeedKph"] = np.quantile(stacked_speed, .1, axis=0)
    trace["upper80SpeedKph"] = np.quantile(stacked_speed, .9, axis=0)
    return {
        "lapTimeSeconds": {
            "lower80": float(np.quantile(lap_times, .1)),
            "median": float(np.quantile(lap_times, .5)),
            "upper80": float(np.quantile(lap_times, .9)),
            "lower95": float(np.quantile(lap_times, .025)),
            "upper95": float(np.quantile(lap_times, .975)),
        },
        "winnerProbabilities": {
            team: float(np.mean([row.team_name == team for row in field_samples]))
            for team in sorted({row.team_name for row in field_samples})
        },
        "trace": browser_trace_rows(trace),
        "timingTable": trace[["progress", "elapsed_s"]].assign(time=lambda frame: frame.elapsed_s / frame.elapsed_s.iloc[-1])[["progress", "time"]].to_dict(orient="records"),
        "representativeTeam": representative.team_name,
    }


def build_corner_predictions(
    spa_features: pd.DataFrame,
    correction_draws: list[pd.DataFrame],
    analogue_evidence: dict[str, pd.DataFrame],
) -> list[dict[str, object]]:
    results = []
    for feature in spa_features.itertuples(index=False):
        key = f"{feature.complex_id}|{feature.phase_type}"
        phase_draws = [draw[(draw.complex_id == feature.complex_id) & (draw.phase_type == feature.phase_type)].iloc[0] for draw in correction_draws]
        phase_time = np.asarray([row.phase_time_correction_s for row in phase_draws], dtype=float)
        minimum_speed = np.asarray([row.speed_correction_ms * 3.6 for row in phase_draws], dtype=float)
        braking = np.asarray([row.braking_onset_correction_m for row in phase_draws], dtype=float)
        exit_speed = np.asarray([row.exit_speed_correction_ms * 3.6 for row in phase_draws], dtype=float)
        analogues = analogue_evidence.get(key, pd.DataFrame())
        effective_neighbors = float(1 / np.sum(np.square(analogues.weight))) if len(analogues) else 0
        confidence = float(np.clip(effective_neighbors / 7, 0, 1))
        results.append({
            "complexId": feature.complex_id,
            "phaseType": feature.phase_type,
            "startProgress": float(feature.start_distance_m / feature.track_length_m),
            "endProgress": float(feature.end_distance_m / feature.track_length_m),
            "confidence": confidence,
            "phaseTimeDeltaSeconds": interval_dict(phase_time),
            "minimumSpeedDeltaKph": interval_dict(minimum_speed),
            "brakingOnsetDeltaM": interval_dict(braking),
            "exitSpeed100mDeltaKph": interval_dict(exit_speed),
            "analogues": [{
                "circuitLabel": row.circuit_id,
                "complexLabel": row.complex_id,
                "year": 2026,
                "weight": float(row.weight),
                "phaseId": row.phase_id,
            } for row in analogues.itertuples(index=False)],
            "dominantUncertainty": "Analogue scarcity" if confidence < .55 else "Team and residual variation",
        })
    return results


def interval_dict(values: np.ndarray) -> dict[str, float]:
    return {
        "lower80": float(np.quantile(values, .1)),
        "median": float(np.quantile(values, .5)),
        "upper80": float(np.quantile(values, .9)),
        "lower95": float(np.quantile(values, .025)),
        "upper95": float(np.quantile(values, .975)),
    }
```

```yaml
# calibration/config/spa-analogues.yaml
schema_version: spa-analogue-policy/v1
features:
  - mean_curvature_per_m
  - peak_curvature_per_m
  - gradient_mean
  - entry_straight_m
  - exit_straight_m
  - sustained_load_s
neighbors: 7
minimum_effective_neighbors: 3
scarcity_interval_inflation_per_missing_neighbor: 0.08
```

- [ ] **Step 4: Verify GREEN**

```bash
cd calibration
python -m pytest tests/test_analogues.py tests/test_spa_predictor.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Spa composition**

```bash
git add calibration/src/spa_calibration/{analogues,spa_predictor}.py calibration/tests/test_analogues.py calibration/tests/test_spa_predictor.py calibration/config/spa-analogues.yaml
git commit -m "feat(spa-prediction): compose coherent team lap distributions"
```

---

### Task 7: Serialize a gated, checksum-protected prediction artifact and CLI

**Files:**
- Create: `calibration/src/spa_calibration/artifact.py`
- Create: `calibration/tests/test_prediction_artifact.py`
- Modify: `calibration/src/spa_calibration/cli.py`
- Create: `calibration/artifacts/predictions/.gitkeep`

**Interfaces:**
- Consumes: validation report, field/team predictions, corner analogues, provenance.
- Produces: `spa-2026-prediction-v1.json`, `build_prediction_artifact()`, `validate_prediction_artifact()`, and the `spa-calibration validate` command. Model fitting and Spa composition remain explicit Python module calls covered by Tasks 3 and 6 rather than being hidden behind an untested orchestration command.

- [ ] **Step 1: Write failing artifact gate and checksum tests**

```python
# calibration/tests/test_prediction_artifact.py
from datetime import UTC, datetime
from spa_calibration.artifact import build_prediction_artifact, validate_prediction_artifact


def test_failed_validation_suppresses_field_best() -> None:
    artifact = build_prediction_artifact(
        validation={"release_gates": {"passed": False, "checks": {"lap_time_mae": False}}},
        field_summary={"lapTimeSeconds": {"lower80": 98.5, "median": 99.0, "upper80": 99.5}, "trace": [], "timingTable": []},
        team_predictions=[],
        corner_predictions=[],
        provenance={"modelVersion": "x", "sourceCutoff": "2026-07-13T00:00:00Z"},
        generated_at=datetime(2026, 7, 14, tzinfo=UTC),
    )
    assert artifact["status"] == "failed-validation"
    assert artifact["fieldBest"] is None
    assert validate_prediction_artifact(artifact)["checksum"] == artifact["checksum"]


def test_released_artifact_has_ordered_intervals() -> None:
    artifact = build_prediction_artifact(
        validation={"release_gates": {"passed": True, "checks": {"all": True}}},
        field_summary={"lapTimeSeconds": {"lower80": 100, "median": 101, "upper80": 102}, "trace": [], "timingTable": []},
        team_predictions=[],
        corner_predictions=[],
        provenance={"modelVersion": "x", "sourceCutoff": "2026-07-13T00:00:00Z"},
        generated_at=datetime(2026, 7, 14, tzinfo=UTC),
    )
    interval = artifact["fieldBest"]["lapTimeSeconds"]
    assert interval["lower80"] <= interval["median"] <= interval["upper80"]
```

- [ ] **Step 2: Run and verify RED**

```bash
cd calibration
python -m pytest tests/test_prediction_artifact.py -q
```

Expected: missing module.

- [ ] **Step 3: Implement artifact builder and validation command**

```python
# calibration/src/spa_calibration/artifact.py
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
import numpy as np
import orjson

SCHEMA_VERSION = "spa-calibration-prediction/v1"


def _interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "lower95": float(np.quantile(array, .025)),
        "lower80": float(np.quantile(array, .10)),
        "median": float(np.quantile(array, .50)),
        "upper80": float(np.quantile(array, .90)),
        "upper95": float(np.quantile(array, .975)),
    }


def _checksum(payload: dict[str, object]) -> str:
    clean = {key: value for key, value in payload.items() if key != "checksum"}
    return sha256(orjson.dumps(clean, option=orjson.OPT_SORT_KEYS)).hexdigest()


def build_prediction_artifact(*, validation, field_summary, team_predictions, corner_predictions, provenance, generated_at: datetime) -> dict[str, object]:
    passed = bool(validation["release_gates"]["passed"])
    released_teams = [row for row in team_predictions if row.get("supported") is True]
    artifact: dict[str, object] = {
        "schemaVersion": SCHEMA_VERSION,
        "status": "released" if passed else "failed-validation",
        "generatedAt": generated_at.isoformat(),
        "sourceCutoff": provenance["sourceCutoff"],
        "modelVersion": provenance["modelVersion"],
        "fieldBest": field_summary if passed else None,
        "teams": released_teams if passed else [],
        "historicalReferences": provenance.get("historicalReferences", []),
        "analogueTraces": provenance.get("analogueTraces", []),
        "corners": corner_predictions if passed else [],
        "validation": validation,
        "provenance": provenance,
    }
    artifact["checksum"] = _checksum(artifact)
    return artifact


def validate_prediction_artifact(artifact: dict[str, object]) -> dict[str, object]:
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unsupported prediction schema")
    actual = _checksum(artifact)
    if artifact.get("checksum") != actual:
        raise ValueError("prediction checksum mismatch")
    if artifact.get("status") != "released" and artifact.get("fieldBest") is not None:
        raise ValueError("non-released artifact must suppress fieldBest")
    return artifact
```

Add to `calibration/src/spa_calibration/cli.py`:

```python
from pathlib import Path
import json
from .artifact import validate_prediction_artifact


@app.command("validate")
def validate_artifact(artifact: Path) -> None:
    payload = json.loads(artifact.read_text())
    validated = validate_prediction_artifact(payload)
    typer.echo(f"valid {validated['schemaVersion']} status={validated['status']}")
```

- [ ] **Step 4: Run full Plan B verification**

```bash
cd calibration
python -m pytest -q tests/test_baselines.py tests/test_design_matrix.py tests/test_hierarchical_recovery.py tests/test_vehicle_prior.py tests/test_line_optimizer.py tests/test_regimes.py tests/test_validation.py tests/test_analogues.py tests/test_spa_predictor.py tests/test_prediction_artifact.py
spa-calibration validate --artifact artifacts/predictions/spa-2026-prediction-v1.json
```

Expected:

```text
all tests passed
valid spa-calibration-prediction/v1 status=<released|failed-validation>
```

- [ ] **Step 5: Commit artifact and CLI**

```bash
git add calibration/src/spa_calibration/{artifact,cli}.py calibration/tests/test_prediction_artifact.py calibration/artifacts/predictions/.gitkeep
git commit -m "feat(spa-prediction): gate and serialize prediction artifact"
```

## Plan B Completion Gate

The plan is complete when:

1. LOCO validation writes `calibration/artifacts/validation/loco-results.json`;
2. a prediction artifact validates against its checksum;
3. a failed gate produces no `fieldBest` or team predictions;
4. a released artifact records every fold, baseline comparison, posterior seed, corpus checksum, and uncertainty interval;
5. the full test suite succeeds without live API access.
