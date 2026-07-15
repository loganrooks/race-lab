# AGENTS.md

## Project purpose

Race Lab is a public F1 circuit-analysis, telemetry, simulation, calibration,
and visualization project.

Race Lab distinguishes observed source data, derived measurements, inferred
quantities, simulated quantities, provisional predictions, and validated
release artifacts. Do not blur these categories.

## Initiative continuity

For substantial initiatives, use repository-backed living records rather than
conversation memory alone. For Spa 2026, the control records are under:

`circuits/spa-francorchamps/seasons/2026/project/`

Before substantive Spa 2026 work:

1. read `project/README.md` and `project/STATUS.md`;
2. read the latest relevant entries in `ACTIVITY.md`, `DECISIONS.md`, and
   `LESSONS.md`;
3. inspect the actual branch, PR head, review threads, and verification state;
4. reconcile stale records before relying on them;
5. state the current objective and next exact action.

Before completion, publication, or handoff:

1. update `STATUS.md`;
2. append `ACTIVITY.md`;
3. update `DECISIONS.md` if a load-bearing decision changed;
4. update `LESSONS.md`, or record `lessons_reviewed: no-new-lesson` in the
   activity entry;
5. run the canonical verifier and read its complete output;
6. record what remains incomplete and one precise next action.

Do not rewrite historical activity entries. Append correction entries instead.
If a procedural sweep is interrupted, record its exact partial count.

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

When receiving external review, separately track:

- finding evaluated;
- artifact changed;
- reaction applied;
- inline reply posted;
- thread resolved;
- fresh review requested.

Do not use “addressed” as a substitute for those six states. Verify feedback
against the actual artifact before accepting, modifying, superseding, or
rejecting it.

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
  tests pass;
- do not claim CI success without a retrievable workflow or check result;
- distinguish locally verified, committed, pushed, remotely observed,
  reviewed, CI-confirmed, and reported-but-unverified states.

Do not make unrelated style comments unless they obscure meaning or create a
substantive maintenance risk.
