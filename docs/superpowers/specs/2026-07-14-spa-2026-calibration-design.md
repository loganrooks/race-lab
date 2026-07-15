# Spa 2026 Corner-Transfer Calibration Design

## Status

Approved design for review. This specification replaces direct tuning of the Spa simulation to a remembered or historical pole time. The displayed 2026 Spa prediction must be generated only after the calibration and validation pipeline defined here passes its release gates.

## Goal

Predict the fastest achievable dry qualifying performance at Spa in 2026 by learning how 2026 cars differ from 2025 cars at the level of driving phases and corner characteristics across completed 2026 circuits.

The output is not only a lap-time estimate. It is a self-consistent predicted lap containing:

- racing trajectory;
- speed;
- throttle;
- brake;
- gear;
- longitudinal and lateral acceleration;
- estimated electrical deployment and recovery;
- aero-state assumptions;
- sector and corner times;
- uncertainty and provenance.

The prediction must remain comparable with named historical Spa traces without presenting historical approximate location data as a measured racing line.

## Product outputs

The app will expose four related products:

1. **Field-best Spa 2026 prediction** — the estimated best dry qualifying lap from the competitive field, with an uncertainty interval.
2. **Team- or car-specific predictions** — only where the completed-season data supports stable team-level archetype estimates.
3. **Historical Spa references** — named real laps with driver, team, session, year, lap number, lap time, channels, source and limitations.
4. **Calibration evidence** — completed-circuit backtests and the corner analogues that support each Spa prediction.

The primary prediction card must show a central estimate and interval, not false precision to one millisecond.

## Non-goals

The first calibrated version will not claim to reconstruct proprietary team telemetry, exact battery state, exact electrical power flow, measured downforce or drag coefficients, exact aero commands where the public feed does not expose them, exact lateral placement from OpenF1 location data, wet qualifying performance, or race-fuel strategy.

These quantities may exist as latent variables or bounded assumptions, but the UI must label them as inferred or simulated.

## Data corpus

For every circuit completed in both 2025 and 2026 before Spa, build paired qualifying datasets. Use 2024 as a control season where useful to estimate ordinary year-to-year variability independent of the 2026 regulation change.

Prefer clean dry Q3 laps from multiple competitive cars. When Q3 is unavailable or unrepresentative, use the fastest clean qualifying segment with an explicit quality flag. Do not select only the pole lap: include enough leading cars to estimate field-wide effects, team × corner-archetype interactions, driver variance, and circuit/session noise.

Exclude or down-weight pit-out laps, aborted laps, traffic- or yellow-affected laps where detectable, materially wet laps, samples outside the official lap window, and traces with feed gaps or non-monotonic progress.

Store provenance for every trace: source, session key, driver, team, year, session, lap number, retrieval date, source license, original query or identifier, sample count and limitations.

## Canonical circuit representation

Every circuit is represented as a distance-indexed canonical path with centreline distance, heading, signed curvature, local radius, elevation, gradient, corner identity, road-width estimate where available, sector identity, and distances to surrounding full-throttle regions.

Public location samples are aligned to this representation by lap progress. They are not used to infer precise lateral road placement unless a source explicitly supports that claim.

## Driving-phase segmentation

Each sequence is segmented into approach, braking onset, peak braking, brake release or trail phase, turn-in, apex region, throttle pickup, exit acceleration, and full-power continuation.

Phase detection combines telemetry thresholds, change-point detection and geometry. Manual annotations may constrain ambiguous sequences, but the process must remain reproducible.

Each phase produces entry speed, minimum speed, fixed-distance exit speeds, braking onset and length, deceleration proxies, throttle pickup, time below full throttle, gear, sustained lateral-load duration, curvature-change rate, surrounding straight lengths, elevation change, and acceleration taper.

## Corner representation

Human-readable archetypes remain useful for explanation, but prediction uses continuous features. Labels may include slow hairpin, traction corner, medium-speed single-apex, direction change, sustained high-speed corner, compression, crest, long straight into heavy braking, and exit-dominated corner.

Each phase receives a feature vector describing geometry, speed regime, braking severity, sustained load, gradient and energy demand. Similarity between Spa and completed-circuit segments is computed from these features rather than assigned by circuit name alone.

## Model architecture

### Physics prior

A simplified minimum-time vehicle model generates an internally consistent lap from candidate racing line, curvature, mass, tyre-friction envelope, speed-dependent downforce, drag, power limits, braking capacity, bounded electrical deployment and recovery, and circuit-specific constraints.

The model jointly determines line, speed and controls. The racing line is not drawn independently and assigned telemetry later.

### Empirical 2026 correction

A hierarchical model learns residual 2025→2026 changes after accounting for geometry and conditions. It estimates effects on minimum speed, braking onset and duration, exit acceleration, terminal speed, phase time, full-throttle fraction and long-straight acceleration taper.

The hierarchy includes global 2026 effects, phase and speed-regime effects, continuous geometry interactions, team × archetype effects, driver random effects, circuit/session effects, condition covariates, and optional season-regime effects when supported by evidence. Partial pooling prevents one exceptional lap from defining an archetype.

### Spa composition

For each candidate 2026 car profile:

1. initialize Spa from a validated reference or minimum-curvature trajectory;
2. solve the physics model;
3. apply learned empirical corrections according to local features;
4. re-optimize line and controls because speed changes alter the best trajectory;
5. iterate until lap time and trajectory converge;
6. sample parameter and residual uncertainty to produce a lap distribution.

The field-best distribution is computed from coherent team/driver lap distributions. It must not combine unrelated teams' best segments into an impossible composite car.

## Regulation and season regimes

Preserve the regulation issue and event date associated with every session. If rules changed materially during the observed season, compare a pooled model, a piecewise regime model and a continuous development model. Choose the least complex model that improves held-out prediction. Publication date alone is not proof of an on-track regime change.

## Validation

### Leave-one-circuit-out backtesting

For every completed 2026 circuit:

1. remove that circuit's 2026 data;
2. train on the remaining paired circuits;
3. use the held-out circuit's 2025 traces and geometry to predict 2026;
4. compare against actual 2026 laps and telemetry.

Evaluate lap, sector and phase-time error; minimum-speed error; braking-onset error; exit-speed and maximum-speed error; full-throttle-fraction error; speed-profile shape; and errors by archetype.

Report separate stress tests for high-speed aero, rapid direction changes, long straights and heavy braking, elevation and traction, and low-speed rotation.

### Release gates

Before the app displays a calibrated Spa estimate, the model must outperform a whole-circuit scaling baseline, avoid systematic bias by speed regime, produce physically feasible traces, preserve monotonic progress, remain within declared bounds, and report calibration coverage honestly.

Initial quality targets are:

- held-out lap-time MAE no worse than 0.7 seconds;
- sector MAE no worse than 0.25 seconds;
- minimum-speed MAE no worse than 8 km/h;
- braking-onset MAE no worse than 25 metres or the source-supported equivalent;
- no persistent signed error across principal Spa archetypes.

Thresholds may change only with documented evidence about source resolution or baseline performance.

## Uncertainty

Uncertainty is decomposed into telemetry and alignment uncertainty, lap-quality and condition uncertainty, driver variance, team/car uncertainty, model-parameter uncertainty, residual uncertainty, and analogue scarcity.

The UI displays a central estimate, 80% and optionally 95% intervals, confidence by sector and corner, analogue coverage, and dominant uncertainty sources. Eau Rouge–Raidillon and other uniquely Spa-specific combinations receive wider intervals when analogues are weak.

## App presentation

Users can select the 2026 predicted field best, supported team predictions, 2025 Spa reference laps, and completed 2026 analogue laps.

The selected lap controls synchronized map playback, speed, throttle, brake, gear, acceleration, energy estimate where simulated, and current corner/phase.

Historical OpenF1 laps replay along a validated reference trajectory unless measured lateral placement is supported. The UI states that progress synchronization is real while lateral line placement is illustrative.

For each Spa complex, a comparison drawer displays predicted time, speed, braking and exit changes; analogue phases and similarity weights; supported team strengths; confidence; provenance; and observed/inferred/simulated labels.

A collapsible calibration report contains training circuits, exclusions, held-out results, simple-baseline comparisons, model version, cutoff, assumptions and limitations.

## Software boundaries

Separate data ingestion, lap quality, circuit alignment, phase segmentation, feature extraction, calibration fitting, vehicle dynamics, Spa prediction, validation, browser-artifact generation and visualization.

The browser consumes versioned generated artifacts. It does not fit the full calibration model in the client.

## Failure handling

If current-season data is missing, retain the last valid artifact, mark the cutoff, widen uncertainty, and never silently substitute synthetic telemetry for observed data.

If team-specific estimates are unstable, omit them. If release gates fail, the app may show the coupled educational simulation and historical references, but the calibrated 2026 prediction remains unavailable.

## Reproducibility

Every prediction artifact includes model version, data cutoff, training and held-out circuits, regulation identifiers, hyperparameters and priors, random seed, validation metrics, checksum and timestamp. Source data, generated features and model outputs remain logically distinct.

## Testing strategy

Tests cover ingestion and provenance, lap-window clipping, monotonic alignment, phase segmentation fixtures, feature invariants, physics feasibility, line/speed/control coupling, hierarchical-model recovery on synthetic data, leave-one-circuit-out orchestration, interval ordering, browser artifact schemas, synchronized playback, historical-route disclosure, mobile and accessibility behaviour.

Golden calibration fixtures must be small, auditable and frozen. Full source refreshes are separate explicit operations.

## Migration from the current app

Until the calibrated artifact passes release gates:

- preserve the current coupled dynamics model as an explicitly uncalibrated educational simulation;
- preserve historical reference traces;
- remove or suppress the provisional 1:40.4 field-best prediction;
- display “calibration pending” where a 2026 pole estimate would otherwise appear;
- do not publish the staged RawGitHack release that embeds the provisional value.
