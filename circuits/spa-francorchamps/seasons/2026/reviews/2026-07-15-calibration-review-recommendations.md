---
title: "Spa 2026 Calibration Specification — Implementation-Planning Recommendations"
document_type: "Independent specification review and implementation-planning guidance"
status: "Approved for implementation planning with mandatory planning resolutions"
commissioned_by: "Logan Rooks, project owner"
prepared_by: "GPT-5.6 Thinking, acting as independent F1 simulation and software-systems reviewer"
prepared_on: "2026-07-15"
project: "Paddock / Spa Race Lab"
target_document: "spa-race-lab/docs/superpowers/specs/2026-07-14-spa-2026-calibration-design.md"
target_repository: "loganrooks/paddock"
target_branch: "spa-race-lab-pages"
target_commit: "9acac706e977a7a7ad5742f210d92132b7631908"
target_commit_message: "docs: specify Spa 2026 corner-transfer calibration"
review_purpose:
  - "Determine whether the written calibration specification is ready for implementation planning"
  - "Identify unresolved matters that must be operationalized before full model construction"
  - "Protect the project against scientifically misleading or architecturally unstable implementation"
intended_audience:
  - "F1 vehicle-dynamics and performance engineers"
  - "Race simulation and telemetry specialists"
  - "Statistical and machine-learning engineers"
  - "Senior software engineers and technical leads"
  - "Future implementation-planning and implementation agents"
approval_boundary: "The specification is approved for implementation planning, not for immediate unconstrained construction of the complete calibration model."
---

# Spa 2026 Calibration Specification — Implementation-Planning Recommendations

## Executive decision

The **Spa 2026 Corner-Transfer Calibration Design** at commit
`9acac706e977a7a7ad5742f210d92132b7631908` is **approved for implementation
planning**.

The specification successfully incorporates its principal requirements:

- paired 2025–2026 qualifying telemetry across mutually completed circuits;
- phase-level telemetry analysis and continuous corner-feature transfer;
- a coupled racing-line and vehicle-dynamics model;
- hierarchical team, driver, circuit, condition, and archetype effects;
- leave-one-circuit-out backtesting;
- uncertainty reporting by sector and corner;
- suppression of the provisional **1:40.4** estimate until validation passes.

It also establishes appropriate product and scientific boundaries:

- observed, inferred, and simulated quantities must remain distinguishable;
- public location data must not be represented as a measured racing line;
- the field-best result must not be assembled from incompatible best sectors
  belonging to different cars;
- the browser consumes versioned artifacts rather than fitting the full model;
- unstable team-specific predictions must be omitted;
- failed release gates leave the calibrated Spa estimate unavailable.

No load-bearing conceptual defect requires returning to specification drafting
before planning begins.

However, the implementation plan must explicitly resolve the six matters below.
They are conditions of a defensible implementation, not optional enhancements.

## 1. Define the prediction estimand

### Problem

“Fastest achievable dry qualifying performance” can denote several different
quantities:

1. the expected actual pole time in the real qualifying session;
2. the expected best lap among a specified number of representative attempts;
3. a latent clean-session optimum for a given car-driver profile;
4. a theoretical minimum-time lap under idealized model conditions;
5. a selected high quantile of an achievable-lap distribution.

These targets differ materially. An actual pole includes track evolution,
tyre preparation, traffic, towing, yellow flags, wind variation, driver
execution, run sequencing, and the number of available attempts. A theoretical
minimum normally removes many of those effects.

### Required planning decision

The implementation plan must declare:

- the primary statistical target;
- the unit of prediction: car, driver, team, field, or session;
- the number and meaning of hypothetical qualifying attempts, if relevant;
- whether the output is a theoretical optimum, a conditional performance
  distribution, or an actual-session forecast;
- how the field-best distribution is derived from coherent profile
  distributions;
- which Spa conditions are fixed, estimated, or sampled.

The target-condition contract should address at least:

- tyre compound and tyre state;
- track temperature and ambient temperature;
- wind and air density;
- track evolution and grip state;
- DRS and relevant aero-state assumptions;
- fuel and qualifying operating assumptions.

### Recommended primary formulation

> The predicted distribution of the best clean dry qualifying lap achievable by
> each supported 2026 car-driver profile under a declared Spa condition
> scenario, with the field-best distribution derived from those coherent
> profile distributions.

A separate model of expected actual pole may be added later.

### Acceptance criterion

Every training target, validation metric, prediction artifact, and user-facing
label must map unambiguously to the chosen estimand.

## 2. Add leakage-safe temporal validation

### Problem

Leave-one-circuit-out validation measures cross-circuit transfer, but it can
still use data from events that occurred after the held-out race. In a
developing F1 season, later events may contain information about upgrades,
operating knowledge, technical directives, setup evolution, and changing
competitive order.

A retrospective reconstruction trained on later events may therefore overstate
what could have been forecast at the time.

### Required planning decision

Retain leave-one-circuit-out backtesting, but supplement it with
**rolling-origin validation**:

1. choose a historical 2026 event;
2. freeze the information cutoff immediately before that event;
3. train only on data available before the cutoff;
4. predict the event as though it had not occurred;
5. compare against the actual qualifying traces and outcomes.

The held-out event's realized weather, track state, session telemetry, setup
clues, and post-event information must not enter a pre-event forecast.

### Validation roles

- **Leave-one-circuit-out:** tests geometric and archetype transfer.
- **Rolling-origin:** tests genuine forecasting under season-time constraints.
- **Regime stress tests:** assess robustness to upgrades, directives, or
  material changes in competitive state.

### Acceptance criterion

The model-release report must contain both cross-circuit and temporal
validation results, clearly separated.

## 3. Make uncertainty calibration a release gate

### Problem

The specification promises central estimates, 80% and optionally 95%
intervals, confidence by corner and sector, analogue coverage, and dominant
uncertainty sources.

Those intervals must be empirically evaluated. A nominal 80% interval that
contains only 45% of held-out observations is not a defensible uncertainty
estimate.

Corner, sector, team, and driver errors are correlated. Field-best uncertainty
must not be produced by independently sampling quantities that share common
regulation, circuit, tyre, and condition uncertainty.

### Required planning decision

The model-release process must evaluate:

- empirical coverage of declared lap-time intervals;
- sector-level interval coverage;
- corner- or phase-level coverage where source resolution permits;
- interval width and sharpness;
- calibration by speed regime and corner archetype;
- a proper scoring rule such as CRPS, weighted interval score, or an equivalent;
- correlation-aware sampling of common and profile-specific uncertainty;
- failure behavior when analogue support is weak.

### Required uncertainty components

At minimum, preserve distinctions among:

- telemetry and alignment uncertainty;
- lap-quality and condition uncertainty;
- driver variation;
- team/car variation;
- model-parameter uncertainty;
- residual uncertainty;
- analogue scarcity;
- shared season- or regulation-level uncertainty.

### Release behavior

If interval calibration fails:

- widen intervals when justified;
- suppress unsupported corner-level confidence;
- show analogue scarcity explicitly;
- or fail the calibrated-model release.

### Acceptance criterion

Passing point-estimate error thresholds is insufficient. Declared intervals
must also achieve documented and reasonably calibrated held-out coverage.

## 4. Establish a source-feasibility and eligibility contract

### Problem

The specification depends on heterogeneous inputs whose availability,
semantics, resolution, and licensing may vary by source, circuit, season, and
session.

Potentially fragile quantities include:

- canonical centreline and elevation;
- road width and circuit-version differences;
- sufficiently resolved speed, throttle, brake, gear, and location channels;
- weather and track-state information;
- tyre and session-condition metadata;
- braking-onset location;
- energy-deployment proxies;
- lateral placement;
- source redistribution rights.

An implementation can become structurally invalid if it assumes uniform
availability where none exists.

### Required planning artifact

Create a versioned, preferably machine-readable, **source and eligibility
manifest** containing, per source and circuit-year:

- available channels;
- units and channel semantics;
- nominal and observed sample resolution;
- known delays, quantization, gaps, and anomalies;
- licensing and redistribution constraints;
- adapter and retrieval version;
- derivable features;
- prohibited claims;
- quality flags;
- downstream eligibility.

### Required eligibility outputs

The plan must define:

- a circuit-year eligibility matrix;
- minimum requirements for inclusion in the paired calibration corpus;
- degradation paths when a channel is missing;
- criteria for sector-only versus corner-level use;
- criteria for excluding a trace, session, circuit, or season;
- how manual annotations are versioned and audited.

### First implementation stage

Run a source-feasibility spike across a deliberately varied circuit sample,
including examples with:

- high-speed aero loading;
- heavy braking;
- elevation;
- rapid direction changes;
- traction-limited exits;
- long full-throttle sections.

### Acceptance criterion

No model component may depend on an input until the eligibility manifest shows
that the input can be produced consistently enough for that component's claim.

## 5. Specify the empirical-to-physics coupling

### Problem

The design correctly requires empirical 2026 corrections to be followed by
re-optimization of line and controls. The implementation plan must now define
how those corrections enter the coupled solver.

A learned improvement might be represented as:

- an effective change to tyre or friction capacity;
- an aero or drag envelope adjustment;
- an acceleration-capacity change;
- a braking-capacity or braking-onset adjustment;
- a phase-time residual;
- a control constraint;
- or a direct correction to an output channel.

Applying the same effect at multiple levels risks double-counting. A correction
to both effective grip and minimum speed, for example, may represent the same
observed change twice.

### Required planning decision

Define the empirical-physics interface:

1. quantities exchanged between the hierarchical model and the solver;
2. units and coordinate systems;
3. whether each quantity is a prior, latent parameter, bound, constraint,
   objective term, or residual;
4. which corrections are physically parameterized and which are
   phenomenological;
5. how double-counting is detected and prevented;
6. how re-optimization and convergence are determined;
7. how uncertainty samples propagate through the solver;
8. fallback behavior when convergence or feasibility fails;
9. provenance showing which output channels were observed, inferred, and
   simulated.

### Modelling caution

Public data is unlikely to identify proprietary downforce, drag, tyre, mass
distribution, and power parameters uniquely. The plan should therefore prefer
bounded effective parameters or constrained phenomenological corrections over
false claims of recovering true team parameters.

### Acceptance criterion

Synthetic and fixture tests must demonstrate:

- no correction is applied twice;
- line, speed, and controls remain mutually consistent;
- corrected traces satisfy declared physical constraints;
- uncertainty propagation preserves valid trajectories;
- solver failures are explicit rather than silently repaired by presentation
  code.

## 6. Strengthen baselines, ablations, and identifiability rules

### Problem

A whole-circuit scaling baseline is necessary but not sufficient. A complex
hybrid architecture should demonstrate that each major layer earns its
complexity.

Hierarchical team-by-archetype effects may be physically real while remaining
weakly identifiable from the available public pre-Spa sample. Partial pooling
reduces variance but does not create information.

### Required baseline suite

At minimum compare against:

1. unadjusted 2025 same-circuit performance;
2. global 2025-to-2026 whole-lap scaling;
3. sector-level scaling;
4. physics-only prediction;
5. a pooled empirical model without team-archetype interactions;
6. a simpler mixed-effects model;
7. nearest-analogue or continuous-feature regression;
8. the full coupled hierarchical model.

### Required ablations

Evaluate the contribution of:

- continuous corner features;
- named archetypes;
- team effects;
- driver effects;
- condition covariates;
- season-regime structure;
- the physics layer;
- iterative re-optimization;
- 2024 control-season information.

### Required stability diagnostics

Use a combination of:

- effective sample size;
- posterior or bootstrap uncertainty;
- shrinkage toward global effects;
- prior sensitivity;
- stability across resamples;
- held-out predictive contribution;
- comparison against a model omitting the effect;
- interval width and practical usefulness.

### Operational definition of instability

A team-, driver-, or archetype-specific estimate should be omitted when it is:

- weakly identified;
- strongly prior-sensitive;
- unstable across resamples;
- unsupported by effective sample size;
- unable to improve held-out prediction;
- or too uncertain to sustain a distinct product claim.

### Acceptance criterion

The full model must outperform relevant simpler alternatives on declared
held-out metrics without introducing unacceptable physical infeasibility,
systematic bias, or uncertainty miscalibration.

## Recommended implementation-planning sequence

The planning package should organize implementation around staged evidence
gates rather than beginning with the full hierarchy.

### Stage 0 — Project and claim contract

- freeze the prediction estimand;
- define target conditions;
- define terminology and observed/inferred/simulated labels;
- record the approval boundary.

### Stage 1 — Data feasibility

- create the source and eligibility manifest;
- test representative circuit-year samples;
- freeze raw-source provenance;
- identify unsupported channels and claims.

### Stage 2 — Canonical data pipeline

- ingestion;
- trace quality;
- lap-window clipping;
- circuit representation;
- progress alignment;
- phase segmentation;
- continuous feature extraction;
- small frozen fixtures.

### Stage 3 — Simple baselines

- unchanged-2025 baseline;
- year-scaling baselines;
- nearest-analogue and pooled statistical baselines;
- cross-circuit and rolling-origin evaluation harnesses.

### Stage 4 — Minimal coupled physics model

- define effective parameters;
- jointly solve line, speed, and controls;
- verify feasibility, convergence, and reproducibility;
- maintain explicit educational-simulation labeling.

### Stage 5 — Empirical correction

- introduce the smallest defensible correction interface;
- test synthetic recovery;
- compare alternative coupling formulations;
- prevent double-counting.

### Stage 6 — Hierarchy and uncertainty

- add global and phase effects first;
- add team, driver, and archetype effects only when identified;
- propagate shared and profile-specific uncertainty;
- evaluate coverage and proper scoring rules.

### Stage 7 — Spa composition and release artifact

- generate coherent profile distributions;
- derive the field-best distribution;
- produce sector- and corner-level explanations;
- emit a versioned browser artifact with complete provenance.

### Stage 8 — Release decision

Release the calibrated Spa estimate only when:

- the selected model beats relevant baselines;
- temporal and cross-circuit validation pass;
- traces are physically feasible;
- systematic regime bias is absent or declared;
- uncertainty is acceptably calibrated;
- the artifact is reproducible;
- unsupported detail is suppressed.

Otherwise retain:

- the educational coupled simulation;
- historical references;
- calibration evidence;
- the “calibration pending” state;
- suppression of the provisional **1:40.4** estimate.

## Final approval statement

The specification is ready to serve as the authoritative input to
implementation planning.

The six recommendations in this document are mandatory planning resolutions.
They do not reopen the product concept. They operationalize the scientific,
statistical, numerical, and software obligations already created by the
specification's intended outputs.
