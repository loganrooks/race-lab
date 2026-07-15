# Spa 2026 Calibration Plan Reconciliation

**Date:** 2026-07-15  
**Repository:** `loganrooks/race-lab`  
**Pull request:** `#1`  
**Branch:** `chore/establish-race-lab-structure`  
**Scope:** implementation-planning reconciliation only; no production calibration implementation.

## Decision summary

The four-plan package has been revised as one programme. The independent review and defence are authoritative: their six mandatory resolutions were operationalized first. Codex findings were then evaluated against that revised architecture rather than applied mechanically. The provisional `1:40.4` estimate remains suppressed. No impossible composite car, temporal leakage, uncoupled trace, or blurred observed/inferred/simulated claim is permitted.

The primary estimand is now the distribution of the best clean dry qualifying lap achievable by each supported 2026 car-driver profile under the versioned `spa-2026-dry-qualifying-reference/v1` condition scenario. It represents the best of two representative push attempts after preparation; the field-best distribution is the draw-wise minimum across complete coherent profiles. It is not an expected actual pole or an unconstrained theoretical minimum.

## A. Independent review requirements

### A1. Define the prediction estimand

**Technical meaning**

Training targets, profile draws, field aggregation, validation, artifact labels, and UI copy must refer to one quantity. The v1 target is conditional clean-lap performance, not session operations. Each prediction belongs to a coherent car-driver profile; two representative attempts are simulated per profile. Shared condition uncertainty is retained across profiles before computing the field minimum.

The declared Spa scenario fixes new soft tyres, qualifying fuel and legal operating state, dry running, no traffic/tow/yellow interruption, and legal active-aero/ERS use. Track/ambient temperature, pressure/air density, wind, and grip evolution are sampled from versioned pre-event distributions.

**Operationalized in**

- `2026-07-14-spa-calibration-program.md`: normative programme estimand and condition contract.
- `2026-07-14-spa-calibration-model-prediction.md`: profile/attempt sampling and coherent field-best composition.
- `2026-07-14-spa-calibration-app-integration.md`: estimand and scenario disclosure in released UI.

**Changed interfaces, schemas, tests, or gates**

- Prediction provenance requires a scenario identifier/checksum and attempt count.
- `FieldBestSample` is computed from complete profile-attempt draws only.
- Artifact validation rejects missing or mismatched scenario metadata.
- UI must label the result as a clean dry qualifying-performance distribution.

**Remaining implementation-time decision**

The exact numerical distributions for temperature, wind, pressure, and grip evolution must be frozen immediately before the forecast cutoff using admissible pre-event evidence. They cannot be replaced by realized Spa qualifying conditions.

**Evidence required before release**

- Versioned scenario manifest and checksum.
- Traceable pre-event sources for all sampled condition distributions.
- Tests proving field-best samples never combine sectors or outcomes across profiles.
- Artifact/UI parity tests for estimand wording and scenario identity.

### A2. Add rolling-origin temporal validation

**Technical meaning**

Leave-one-circuit-out validation tests geometric transfer but may train on future events. Rolling-origin validation must recreate prospective forecasts using only rows whose source timestamps precede each held-out event cutoff. Realized held-out weather, track state, telemetry, setup clues, upgrades, and post-event information are unavailable to the fold.

**Operationalized in**

- Programme release contract requires both validation axes.
- Model plan adds `run_rolling_origin_validation()` and a single `combine_release_evidence()` authority.
- Data manifests retain session timestamps, retrieval provenance, and cutoff eligibility.

**Changed interfaces, schemas, tests, or gates**

- Validation reports are split into `loco-results.json` and `rolling-origin-results.json`.
- Every rolling-origin fold records cutoff, eligible training events, excluded future rows, scenario inputs, and held-out result.
- `release_gates.passed` requires a passing temporal report; LOCO cannot release alone.
- Regression fixtures deliberately include post-cutoff rows and assert exclusion.

**Remaining implementation-time decision**

Select the minimum set of informative rolling origins supported by the pre-Spa 2026 calendar and define explicit upgrade/directive regime stress windows.

**Evidence required before release**

- Reproducible fold manifests and source cutoffs.
- Negative leakage tests.
- Separate temporal and cross-circuit scores.
- Regime-stress report for material season changes.

### A3. Make uncertainty calibration a release gate

**Technical meaning**

Nominal intervals must achieve defensible held-out coverage and useful sharpness. Outcome, phase, team, driver, circuit, regulation, and condition uncertainties are correlated. Field-best draws must share common uncertainties while preserving profile-specific variation.

**Operationalized in**

- Model plan requires 80% and 95% coverage, weighted interval score, CRPS, archetype/speed-regime calibration, and scarcity behavior.
- Outcome marginals are coupled by an explicitly estimated residual/posterior copula and covariance matrix; unrelated same-index draws are prohibited.
- Programme and app plans require uncertainty-calibration evidence before release/rendering.

**Changed interfaces, schemas, tests, or gates**

- `CalibrationFit` records outcome order, covariance, and copula version.
- `sample_covariance_coupled_outcome_draws()` replaces unrelated marginal-index reuse.
- Release-gate configuration adds empirical coverage bands, WIS, and CRPS thresholds.
- Unsupported corner-level intervals are suppressed or widened rather than cosmetically shown.

**Remaining implementation-time decision**

Finalize coverage tolerances with finite-sample confidence intervals after the feasibility corpus size is known. The gate may become coarser, but not weaker.

**Evidence required before release**

- Held-out empirical coverage at supported granularities.
- WIS/CRPS comparisons against baselines.
- Covariance-recovery fixtures and posterior predictive checks.
- Scarcity/suppression report for unsupported Spa sections.

### A4. Establish a source-feasibility and eligibility contract

**Technical meaning**

Each source/circuit/year/session must declare what it actually supports. Eligibility is executable and fail-closed: a downstream phase or model outcome cannot depend on a channel or semantic claim that is absent, too sparse, delayed beyond tolerance, non-redistributable, or only illustrative.

**Operationalized in**

- Data plan adds Task 0, `source-eligibility.yaml`, `feature-requirements.yaml`, and evaluated source/circuit-year manifests.
- Circuit configuration owns geometry paths and source/license metadata.
- Raw source coverage is measured before resampling.
- Selection manifests record Q3/SQ3 preference and fallback provenance.

**Changed interfaces, schemas, tests, or gates**

- Eligibility levels: `excluded`, `sector-only`, `phase`, and `corner`.
- Manifests record channel semantics/units, nominal and observed resolution, gaps, quantization, delays, adapter version, derivable features, prohibited claims, quality flags, and redistribution policy.
- `LapQuality` records raw start/end/coverage and per-channel coverage.
- Corpus manifest checksums source eligibility, circuit-year eligibility, and lap selection.

**Remaining implementation-time decision**

Populate and adjudicate the first varied-circuit feasibility spike. Manual annotations require reviewer identity and versioned diffs.

**Evidence required before release**

- Passing representative feasibility spike.
- Complete eligibility rows for every training and Spa input.
- Source checksums, query identities, and licensing records.
- Exclusion/degradation tests for missing channels.

### A5. Define empirical-to-physics coupling

**Technical meaning**

Learned effects must enter the coupled dynamics solver exactly once. Effective physical envelopes, control landmarks, and diagnostics have distinct owners. Direct post-hoc trace corrections are not allowed in a released coupled solution. Optimized geometry must recompute path distance before dynamics are solved.

**Operationalized in**

- Programme plan defines correction-family ownership and a correction ledger.
- Model plan maps effective-envelope draws to bounded parameters; braking/throttle/exit effects to constraints/objectives; phase-time residuals to diagnostics only in v1.
- Line optimizer recomputes cumulative optimized-path distance, progress, heading, and curvature.
- ERS integration reduces deployment before reserve violation instead of clipping state and borrowing future regeneration.

**Changed interfaces, schemas, tests, or gates**

- Correction rows contain family and application count.
- `validate_correction_ledger()` rejects duplicate application or unsupported outcomes.
- Every uncertainty draw is re-optimized and re-solved.
- Lap summary time equals the final emitted trace time.
- Physical-feasibility and convergence reports participate in release eligibility.

**Remaining implementation-time decision**

Choose bounded effective parameter ranges and objective weights from the feasibility spike. No range may be described as a recovered proprietary coefficient.

**Evidence required before release**

- Synthetic no-double-counting tests.
- Line/speed/control/energy consistency tests.
- ERS reserve and energy-conservation traces.
- Solver convergence/failure report for every released draw.

### A6. Strengthen baselines, ablations, and identifiability rules

**Technical meaning**

The full hierarchy must earn its complexity. Profile-specific effects are omitted or pooled when public data cannot identify them. Performance is compared with multiple credible alternatives, not just whole-lap scaling.

**Operationalized in**

- Model plan adds a baseline/ablation/identifiability task.
- Programme release contract requires baseline improvement and support decisions.
- App displays team-specific results only when the identifiability report marks them supported.

**Changed interfaces, schemas, tests, or gates**

Required models: unchanged 2025 Spa, global lap scaling, sector scaling, physics-only, pooled empirical, simple mixed effects, nearest-analogue/continuous regression, and full coupled hierarchy. Required ablations remove continuous features, archetypes, team, driver, conditions, regime, physics, re-optimization, and 2024 controls. `IdentifiabilityDecision` records ESS, shrinkage, prior sensitivity, resample stability, predictive contribution, interval usefulness, and `supported | pooled | omitted`.

**Remaining implementation-time decision**

Set practical-improvement margins after baseline score variance is measured. Complexity is not retained on a statistically trivial win.

**Evidence required before release**

- Complete baseline and ablation report.
- Stability diagnostics per retained profile/effect.
- Evidence that the released model improves point and proper distributional scores.
- Omission/pooling decisions visible in provenance and UI.

## B. Codex review findings

Repeated review runs are deduplicated by technical issue. Thread identifiers are the GitHub GraphQL review-thread IDs from PR #1; line numbers refer to the reviewed revision and may become outdated after reconciliation.

### B1. Moved plan paths

- **Source:** top-level Codex review `PRR_kwDOTZdGvM8AAAABGHuhEg`, program plan execution-order paths.
- **Still valid after independent-review revisions:** yes.
- **Disposition:** accepted.
- **Technical justification:** the former `docs/superpowers/plans` references were deleted and could not be executed.
- **Affected files/interfaces:** programme plan execution order.
- **Revision:** all references now use `circuits/spa-francorchamps/seasons/2026/plans/...`.
- **Verification:** canonical-path existence check in `scripts/verify.sh`.

### B2. Resampling grid can exceed track length

- **Source:** `PRRT_kwDOTZdGvM6RJ-fK`, data plan reviewed line 975.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** `np.arange(stop + spacing/2)` can emit progress above one.
- **Affected interfaces:** `resample_aligned_trace()`.
- **Revision:** generate interior points strictly below length, append exact endpoint, deduplicate, clip progress, assert monotonic exact endpoints.
- **Verification:** non-divisible-length tests and bounded-progress property tests.

### B3. Positional construction of Pydantic `EventSpec`

- **Source:** `PRRT_kwDOTZdGvM6RJ-fO`, data plan line 1827.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** Pydantic models reject positional field construction.
- **Affected interfaces:** retrieval tests and live corpus orchestration.
- **Revision:** all examples use keyword arguments and include circuit-unique discriminators.
- **Verification:** fixture and live-orchestration unit tests instantiate the exact schema.

### B4. Incomplete-lap classification after full-grid resampling

- **Source:** `PRRT_kwDOTZdGvM6RJ-fR`, data plan line 1703.
- **Still valid:** yes and broadened by source-feasibility requirements.
- **Disposition:** accepted with modification.
- **Technical justification:** a canonical full grid falsely implies complete source coverage.
- **Affected interfaces:** `LapQuality`, `RawCoverage`, corpus acceptance.
- **Revision:** coverage/gaps/reversals/channel presence are computed from coupled/aligned source rows before resampling; accepted laps alone are resampled.
- **Verification:** truncated-source fixture remains rejected despite full-grid interpolation capability.

### B5. Canonical geometry lost during resampling

- **Source:** `PRRT_kwDOTZdGvM6RJ-fW`, data plan line 1696.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** phase and feature extraction require curvature/gradient and must not derive them from approximate telemetry coordinates.
- **Affected interfaces:** `resample_aligned_trace(trace, track)`.
- **Revision:** geometry columns are interpolated from immutable configured `CanonicalTrack` onto the telemetry grid.
- **Verification:** equality/provenance tests against canonical geometry fixtures.

### B6. Lap summary and emitted trace timeline disagree

- **Source:** `PRRT_kwDOTZdGvM6RJ-fa`, model plan line 898.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** `dt.sum()` included a segment excluded from zero-origin elapsed time.
- **Affected interfaces:** `LapSolution.lap_time_s`, timing table, browser playback.
- **Revision:** summary time is exactly `trace.elapsed_s.iloc[-1]`.
- **Verification:** invariant test asserts summary, final trace time, timing table, and serialized artifact agree.

### B7. ERS deployment borrows future regeneration

- **Source:** `PRRT_kwDOTZdGvM6RJ-fd`, model plan lines 848–852.
- **Still valid:** yes and release-blocking under the physical-feasibility resolution.
- **Disposition:** accepted.
- **Technical justification:** clipping battery state while retaining requested deployment hides infeasible energy use.
- **Affected interfaces:** `_integrate_battery()`, deploy trace, physical-feasibility gate.
- **Revision:** deployment is curtailed before reserve crossing; reserve violation raises an explicit solver error.
- **Verification:** early-deployment/late-regen fixture proves no future-energy borrowing.

### B8. Phase distances absent from feature rows

- **Source:** `PRRT_kwDOTZdGvM6RJ-fi`, model plan line 1361.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** Spa correction and corner cards require canonical phase/apex distances.
- **Affected interfaces:** `FeatureRecord`, feature extraction, correction construction.
- **Revision:** track, complex, phase, and apex distance fields are explicit schema outputs.
- **Verification:** schema and round-trip artifact tests.

### B9. CLI release validation is incomplete

- **Source:** `PRRT_kwDOTZdGvM6RJ-fk`, model plan lines 1702–1703.
- **Still valid:** yes; broadened by independent review.
- **Disposition:** accepted with modification.
- **Technical justification:** checksum validity does not imply release eligibility.
- **Affected interfaces:** shared artifact validator and CLI.
- **Revision:** released artifacts require field best, all release reports/gates, ordered intervals, scenario/cutoff freshness, and complete provenance.
- **Verification:** validator-parity fixture suite across model, CLI, generator, and browser.

### B10. Zero-length full-power phase

- **Source:** `PRRT_kwDOTZdGvM6RJ-fo`, data plan line 1141.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** full-power start and end were both the final sample.
- **Affected interfaces:** phase detector and `PhaseRecord` validation.
- **Revision:** full-power starts at detected onset no later than the penultimate sample and ends at the window end; cross-field schema validation rejects zero length.
- **Verification:** absent/late full-power fixtures and phase-duration property tests.

### B11. Braking onset measured relative to its own phase

- **Source:** `PRRT_kwDOTZdGvM6RJ-fs`, data plan line 1301.
- **Still valid:** yes.
- **Disposition:** accepted with modification.
- **Technical justification:** onset-phase start makes the value zero and destroys the calibration outcome.
- **Affected interfaces:** `FeatureRecord`, paired deltas, braking validation.
- **Revision:** store absolute canonical onset and offset from complex start; missing onset is `None`, never artificial zero.
- **Verification:** known-onset and no-braking fixtures.

### B12. Fleet-wide phase sums used as a lap

- **Source:** `PRRT_kwDOTZdGvM6RJ-fw`, model plan lines 1124–1126.
- **Still valid:** yes and conflicts with the estimand.
- **Disposition:** accepted.
- **Technical justification:** phases from multiple cars are not one coherent lap.
- **Affected interfaces:** fold scoring and release metrics.
- **Revision:** aggregate phase predictions by `lap_slug`/profile first, then score and aggregate laps.
- **Verification:** multi-profile fixture whose fleet sum differs from every coherent lap.

### B13. Learned non-speed corrections do not enter dynamics

- **Source:** `PRRT_kwDOTZdGvM6RJ-fy`, model plan lines 860–862.
- **Still valid:** yes; superseded in scope by the empirical-to-physics resolution.
- **Disposition:** accepted with modification.
- **Technical justification:** unused fitted outcomes cannot calibrate the released trace; naïve direct additions would double-count.
- **Affected interfaces:** correction ledger, solver constraints, release model outcome set.
- **Revision:** effective envelope, braking onset, throttle pickup, and exit-speed corrections have explicit solver owners; phase-time is diagnostic-only in v1. An outcome that has no solver owner is excluded from release fitting.
- **Verification:** single-owner, no-double-counting, and outcome-perturbation tests.

### B14. Browser generator can bundle an invalid released artifact

- **Source:** `PRRT_kwDOTZdGvM6RKgmD`, app plan line 222.
- **Still valid:** yes.
- **Disposition:** accepted with modification.
- **Technical justification:** build-time checksum-only validation bypasses the browser contract.
- **Affected interfaces:** `scripts-build-calibration-data.mjs` and shared validator.
- **Revision:** generator invokes full release validation after checksum and emits pending on any failure.
- **Verification:** shared parity fixtures.

### B15. Session lookup is not circuit-unique

- **Source:** `PRRT_kwDOTZdGvM6RKgmJ`, data plan lines 570–574.
- **Still valid:** yes and covered by source eligibility.
- **Disposition:** accepted.
- **Technical justification:** country/year/session can match multiple U.S. meetings and corrupt geometry/provenance.
- **Affected interfaces:** `EventSpec`, events manifest, `resolve_session()`.
- **Revision:** meeting key when frozen; otherwise meeting name, circuit short name, and date window; exactly one result or failure.
- **Verification:** Miami/other-U.S.-meeting ambiguity fixture.

### B16. Optimized line retains centreline distance

- **Source:** `PRRT_kwDOTZdGvM6RKgmM`, model plan line 940.
- **Still valid:** yes and violates physical coupling.
- **Disposition:** accepted.
- **Technical justification:** speed/time integration used wrong path length after lateral movement.
- **Affected interfaces:** line materialization and solver input.
- **Revision:** recompute segment/cumulative distance, progress, heading, and curvature from optimized coordinates before solving.
- **Verification:** nonzero-offset path-length and lap-time coupling tests.

### B17. Analogue provenance hard-codes 2026

- **Source:** `PRRT_kwDOTZdGvM6RKgmP`, model plan line 1538.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** evidence may come from 2024/2025 and must not be presented as 2026 observation.
- **Affected interfaces:** analogue serialization and UI.
- **Revision:** carry source `season` from training feature row.
- **Verification:** mixed-season analogue fixture.

### B18. Legacy OpenF1 channel names are not normalized

- **Source:** `PRRT_kwDOTZdGvM6RKgmS`, app plan line 372.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** historical traces use `speed/throttle/brake`, while browser consumers require normalized names.
- **Affected interfaces:** trace-source adapter.
- **Revision:** normalize at adapter boundary to `speedKph/throttlePct/brakePct`.
- **Verification:** legacy and modern trace fixtures produce identical sampled telemetry.

### B19. Temporal validation does not gate release

- **Source:** `PRRT_kwDOTZdGvM6RKgmV`, model plan line 1186.
- **Still valid after revisions:** its original observation is valid, but the requirement is now fully governed by mandatory recommendation A2.
- **Disposition:** superseded.
- **Technical justification:** the broader review resolution defines temporal fold construction and mandatory gate conjunction, beyond adding one Boolean.
- **Affected interfaces:** rolling-origin report and `combine_release_evidence()`.
- **Verification:** missing/failing temporal report prevents release.

### B20. Marginal outcome draws do not preserve covariance

- **Source:** `PRRT_kwDOTZdGvM6RKgmb`, model plan lines 1353–1354.
- **Still valid:** yes and covered by A3.
- **Disposition:** accepted with modification.
- **Technical justification:** equal integer indices in separate posterior objects have no joint meaning.
- **Affected interfaces:** `CalibrationFit`, posterior sampling, profile and field draws.
- **Revision:** explicit cross-outcome residual/posterior copula and covariance-coupled ranks. A future truly joint likelihood may replace it if it materially improves validation.
- **Verification:** known-covariance recovery and independence-substitution failure test.

### B21. Geometry loader ignores configured paths

- **Source:** `PRRT_kwDOTZdGvM6RKgmg`, data plan line 1687.
- **Still valid:** yes.
- **Disposition:** accepted.
- **Technical justification:** hard-coded filenames bypass provenance and fail for Spa's adapter geometry.
- **Affected interfaces:** corpus builder and circuits manifest.
- **Revision:** load the declared `geometry` path and metadata from `circuits.yaml`.
- **Verification:** CSV and Spa JSON-adapter fixture paths.

### B22. Canonical Ruff verification fails on inherited files

- **Source:** `PRRT_kwDOTZdGvM6RKgmm`, `scripts/verify.sh` line 62.
- **Still valid:** yes.
- **Disposition:** accepted with modification.
- **Technical justification:** a new canonical command must pass in the declared environment without hiding new lint defects; inherited unrelated lint debt should not make every planning PR unverifiable.
- **Affected interfaces:** `scripts/verify.sh`.
- **Revision:** compile all tracked Python; Ruff all calibration/tests/scripts Python plus every Python file changed against the merge base. `RACE_LAB_FULL_LINT=1` runs repository-wide Ruff and exposes legacy debt explicitly. No changed Python file can bypass lint.
- **Verification:** synthetic unchanged-legacy fixture passes; modifying that legacy file makes Ruff blocking; full-lint mode reports its debt.

### B23. Candidate selection ignores Q3/SQ3 priority

- **Source:** `PRRT_kwDOTZdGvM6RKgmq`, data plan lines 1803–1804.
- **Still valid:** yes and covered by A4.
- **Disposition:** accepted.
- **Technical justification:** globally fastest laps can silently substitute earlier qualifying segments.
- **Affected interfaces:** `select_candidate_laps()`, `LapRecord`, selection manifest.
- **Revision:** Q3/SQ3 first; ordered fallback with explicit Boolean and reason per lap/profile.
- **Verification:** missing/deleted/traffic Q3 fixtures and manifest assertions.

### B24. Released provenance is incomplete

- **Source:** `PRRT_kwDOTZdGvM6RKgmu`, model plan line 1690.
- **Still valid:** yes and broadened by the review resolutions.
- **Disposition:** accepted with modification.
- **Technical justification:** checksums cannot make an irreproducible artifact reproducible.
- **Affected interfaces:** artifact builder, shared validator, browser details.
- **Revision:** required provenance includes corpus/training/eligibility/scenario/report checksums, random seed, regulation identifiers, hyperparameters, training/held-out circuits, code commit, source cutoff, model version, and generation time before checksum.
- **Verification:** omission of any required field prevents checksum finalization/release in all validation paths.

## Cross-plan consistency and implementation-time boundary

The plans deliberately do not create production calibration modules. Illustrative snippets define contracts and tests for future implementation. Where the public data cannot support a requested granularity, eligibility and identifiability rules reduce or suppress the claim rather than substituting synthetic observations. Model-release validation is separate from ordinary software CI but is mandatory before a prediction artifact can become `released`.

## PR thread handling

After the consolidated plan commit:

1. all technically accepted inline comments receive a positive rating when the GitHub API exposes a numeric review-comment identifier;
2. each addressed inline thread is resolved using its thread identifier;
3. the temporal-gate thread is resolved as superseded by the broader mandatory-review implementation, not dismissed as incorrect;
4. a top-level PR comment links this reconciliation and requests one fresh Codex review;
5. any new finding is reassessed against the revised architecture before further changes.

## C. Fresh Codex review of `1ffaf2d`

All twelve findings were verified against the reviewed snippets and accepted. They expose concrete internal contradictions rather than requests to reopen the approved architecture. Reactions, replies, and thread resolution are recorded separately after publication of the corrected head.

| Task | Thread | Severity | Disposition | Corrective contract and regression evidence |
|---|---|---:|---|---|
| DATA-01 | `PRRT_kwDOTZdGvM6RO8R2` | P2 | accepted | Event rows now validate as either `meeting_key`-identified or complete fallback-discriminator records; every shown event has per-season windows; missing metadata fails before retrieval. |
| DATA-02 | `PRRT_kwDOTZdGvM6RO8R-` | P2 | accepted | `GeometrySource` owns path, format, checksum, source, and licence; loader declaration and pipeline call use the same interface, including the Spa JSON adapter. |
| DATA-03 | `PRRT_kwDOTZdGvM6RO8SK` | P1 | accepted | Observed progress is unwrapped but never divided by its observed span; a middle-60% fixture remains 60% and is rejected before resampling. |
| MODEL-01 | `PRRT_kwDOTZdGvM6RO8Rw` | P1 | accepted | `lap_slug` remains in model and baseline joins before coherent-lap aggregation. |
| MODEL-02 | `PRRT_kwDOTZdGvM6RO8R8` | P1 | accepted | `ReleaseGates` represents every YAML key, rejects unknown/missing keys, and the final conjunction retains temporal, uncertainty, baseline, feasibility, and identifiability evidence. |
| MODEL-03 | `PRRT_kwDOTZdGvM6RO8SA` | P2 | accepted | `_solve_speed_envelope()` and `simulate_lap()` share an explicit `ControlConstraints` interface with length validation. |
| MODEL-04 | `PRRT_kwDOTZdGvM6RO8SN` | P1 | accepted | `n` samples produce `n-1` real segments; elapsed time begins at zero and ends after cumulative segment times, without a post-finish segment. |
| MODEL-05 | `PRRT_kwDOTZdGvM6RO8SR` | P1 | accepted | Field draws require the exact frozen profile-attempt set, reject duplicates/missing solver results, and take best attempt per profile before field minimum. |
| MODEL-06 | `PRRT_kwDOTZdGvM6RO8Ry` | P1 | accepted | Complete semantic validation precedes hashing; checksum and full validation run again before serialization. |
| APP-01 | `PRRT_kwDOTZdGvM6RO8SC` | P1 | accepted | Pending, failed, and released artifacts all pass the semantic validator; any failure emits frozen pending, and unreleased estimates are suppressed. |
| APP-02 | `PRRT_kwDOTZdGvM6RO8SI` | P2 | accepted | Legacy telemetry keys are destructured away at the adapter boundary; only normalized channels remain. |
| APP-03 | `PRRT_kwDOTZdGvM6RO8SV` | P2 | accepted | One complete released fixture satisfies all reports, provenance, scenario, timestamps, and intervals; each negative test mutates one property. |

**Horizontal review:** Plan A fields consumed by Plan B, Plan B artifact fields consumed by Plan C, all release predicates, scenario identity, attempt count, complete-profile semantics, and fail-closed states were reviewed together. No production calibration functionality was implemented. The provisional `1:40.4` estimate remains suppressed.

**PR action state at publication:** reactions pending; inline replies pending; twelve fresh threads pending resolution until the corrected commit is pushed and verified.
