# AGENTS.md

## Project purpose

Race Lab is a public F1 circuit-analysis, telemetry, simulation, calibration,
and visualization project.

Race Lab distinguishes observed source data, derived measurements, inferred
quantities, simulated quantities, provisional predictions, and validated
release artifacts. Do not blur these categories.

## Review guidelines

Report only defects with a concrete correctness, scientific-validity,
security, reproducibility, licensing, or release-integrity consequence.

Treat the following as P1 issues:

- publishing a calibrated prediction before its declared release gates pass;
- reintroducing the provisional Spa 2026 `1:40.4` estimate as a prediction;
- presenting inferred or simulated quantities as observed telemetry;
- presenting approximate public coordinates as a measured racing line;
- combining incompatible teams or drivers into an impossible composite lap;
- temporal leakage from post-event data into a purported pre-event forecast;
- bypassing data-quality, provenance, eligibility, or uncertainty checks;
- silently substituting synthetic data for missing observations;
- committing credentials, restricted source data, or data without documented
  redistribution rights;
- allowing generated browser artifacts to disagree with their model version,
  cutoff, validation report, or checksum;
- numerical changes that break monotonic lap progress, physical feasibility,
  unit consistency, or line/speed/control coupling.

For model and statistical changes, check:

- whether the target estimand is unchanged or explicitly migrated;
- whether simpler baselines and required backtests remain available;
- whether uncertainty is propagated rather than appended cosmetically;
- whether shared and profile-specific uncertainty remain correlated;
- whether team, driver, circuit, and archetype effects are identifiable;
- whether the implementation double-counts an empirical correction through
  both physical parameters and residual adjustments.

For circuit-specific changes, check:

- layout and season applicability;
- source provenance;
- units and coordinate systems;
- circuit-version assumptions;
- analogue support and scarcity disclosures.

## Verification

Run the repository's canonical verification command:

```bash
bash scripts/verify.sh
```

Also observe these rules:

- inspect changed scripts for syntax and failure handling;
- run directly relevant tests and validation fixtures;
- verify Markdown links for moved documents;
- verify JSON, YAML, and generated-artifact schemas where applicable;
- do not claim that a numerical model is validated merely because software
  tests pass.

Do not make unrelated style comments unless they obscure meaning or create a
substantive maintenance risk.
