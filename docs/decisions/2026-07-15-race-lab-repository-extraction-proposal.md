---
title: "Race Lab Repository Extraction and Multi-Circuit Structure Proposal"
document_type: "Repository-boundary and information-architecture proposal"
status: "Proposed for approval"
commissioned_by: "Logan Rooks, project owner"
prepared_by: "GPT-5.6 Thinking, acting as independent product architect and software-systems reviewer"
prepared_on: "2026-07-15"
current_repository: "loganrooks/paddock"
current_product_identity: "Prix Guesser"
source_branch: "spa-race-lab-pages"
source_commit: "9acac706e977a7a7ad5742f210d92132b7631908"
proposed_repository: "loganrooks/race-lab"
proposed_visibility: "public"
proposal_scope:
  - "Separate Race Lab from the unrelated Paddock / Prix Guesser product boundary"
  - "Define a durable multi-circuit and multi-season repository structure"
  - "Place specifications, reviews, plans, manifests, reports, code, and generated artifacts according to their domain role"
  - "Preserve relevant Git history during extraction"
  - "Define public-data, licensing, and publication boundaries"
related_documents:
  - "Spa 2026 Corner-Transfer Calibration Design"
  - "Spa 2026 Calibration Specification — Implementation-Planning Recommendations"
  - "Defence of the Spa 2026 Calibration Review Recommendations"
decision_requested: "Approve creation of a standalone public Race Lab repository and migration of the current Spa Race Lab work into the structure defined here."
---

# Race Lab Repository Extraction and Multi-Circuit Structure Proposal

## 1. Executive recommendation

Create a standalone public repository:

```text
loganrooks/race-lab
```

Race Lab should not remain a permanent subtree or long-lived feature branch of
`loganrooks/paddock`.

`paddock` currently identifies itself as Prix Guesser: an F1-themed geography
and party-game project. Race Lab is a materially different product and
technical programme. It concerns telemetry ingestion, circuit representation,
vehicle dynamics, cross-circuit calibration, probabilistic prediction,
validation, and scientific presentation.

Keeping both projects in one repository would create misleading ownership
boundaries, unrelated build and dependency surfaces, confused issue tracking,
and an increasingly artificial directory hierarchy.

The new repository should be organized around:

- shared Race Lab software and methodology;
- one durable directory per circuit;
- season-specific work within each circuit;
- versioned evidence and generated prediction artifacts;
- explicit separation of observed, inferred, and simulated data.

The current Spa work should become the founding circuit programme of the new
repository, not a special-purpose project that later circuits must imitate by
copying.

## 2. Decision summary

### Adopt

- a standalone public `loganrooks/race-lab` repository;
- `circuits/<circuit-slug>/` as the durable circuit boundary;
- `seasons/<year>/` beneath each circuit for event-specific work;
- shared source code under `src/race_lab/`;
- a separate web application under `apps/web/`;
- domain-based locations for specs, reviews, plans, manifests, and reports;
- history-preserving extraction from the current Paddock branch;
- GitHub Pages deployment from the new repository;
- an explicit third-party data and licensing policy.

### Reject

- keeping Race Lab permanently under `paddock/`;
- placing durable project documents under `docs/superpowers/`;
- creating one repository per circuit;
- creating separate model and pipeline implementations inside every circuit
  directory;
- committing unrestricted copies of third-party telemetry merely because the
  repository is public;
- publishing provisional predictions before their release gates pass.

## 3. Why Race Lab is a separate repository

## 3.1 Different product identity

Paddock / Prix Guesser is a game-oriented product centered on authored
geography, circuit recognition, social play, and reveal design.

Race Lab is an engineering and analysis product centered on:

- circuit geometry;
- telemetry and provenance;
- phase and corner features;
- racing-line and vehicle-dynamics simulation;
- cross-season and cross-circuit calibration;
- uncertainty;
- validation;
- explanatory technical visualization.

These products may eventually exchange data or experiences, but they do not
share a coherent primary purpose.

A repository should communicate what the project is. A visitor should not need
to infer that a vehicle-dynamics and telemetry laboratory is hidden inside a
party-game repository.

## 3.2 Different technical architecture

Race Lab is likely to require:

- Python or equivalent scientific-computing infrastructure;
- numerical optimization;
- statistical modelling;
- source adapters and data-quality pipelines;
- immutable schemas and generated artifacts;
- larger tests and model-release workflows;
- a static or client-side visualization application;
- explicit data licensing and reproducibility controls.

Prix Guesser has a different application architecture, release cadence,
content model, and user workflow.

Combining them would couple unrelated dependencies and make CI, issues,
releases, and contributor expectations harder to understand.

## 3.3 Different publication and evidence model

Race Lab makes claims whose provenance and uncertainty must be auditable.
Its releases should identify:

- data cutoff;
- model version;
- source eligibility;
- validation results;
- uncertainty calibration;
- assumptions and limitations;
- artifact checksum.

That is closer to a public technical laboratory than to an ordinary feature of
a game.

## 3.4 Independent future value

Race Lab can support:

- pre-race technical exploration;
- historical trace comparison;
- regulation-era analysis;
- educational vehicle-dynamics demonstrations;
- reusable telemetry and circuit tooling;
- open methodological discussion;
- future integration into other F1 projects.

Its value is not contingent on Prix Guesser shipping or adopting its outputs.

## 4. Alternatives considered

## 4.1 Option A — Keep Race Lab inside Paddock

Example:

```text
paddock/
├── prix-guesser/
└── race-lab/
```

### Advantages

- no repository migration;
- one place for all current F1 work;
- easy local sharing of unversioned code.

### Disadvantages

- conflicts with Paddock's declared Prix Guesser identity;
- unrelated dependency and build surfaces;
- unclear issue and release ownership;
- poor public discoverability for Race Lab;
- encourages direct internal coupling instead of stable interfaces;
- makes future extraction harder after more history accumulates.

### Decision

Reject as the durable architecture.

It may be acceptable only as a temporary staging state while the new repository
is created and verified.

## 4.2 Option B — Create one Race Lab repository

Example:

```text
loganrooks/race-lab
```

All circuits share one model and data architecture while retaining independent
circuit and season records.

### Advantages

- clear public identity;
- shared pipeline and model implementation;
- consistent methodology across circuits;
- one validation framework;
- coherent documentation and issue tracker;
- circuit-specific work remains locally discoverable;
- straightforward Pages deployment;
- avoids cross-repository duplication.

### Disadvantages

- requires a deliberate migration;
- shared and circuit-specific boundaries must be enforced;
- repository size must be managed if generated data grows.

### Decision

Adopt.

This is the best fit for a reusable multi-circuit technical laboratory.

## 4.3 Option C — Create a repository per circuit

Examples:

```text
race-lab-spa
race-lab-monza
race-lab-suzuka
```

### Advantages

- complete circuit isolation;
- independent release histories;
- smaller individual repositories.

### Disadvantages

- duplicated ingestion, feature, model, and validation code;
- methodological drift;
- difficult cross-circuit training;
- fragmented issues and documentation;
- poor fit for leave-one-circuit-out calibration;
- package-version coordination overhead.

### Decision

Reject for the foreseeable future.

Separate repositories should be considered only if a component becomes an
independently reusable package with a genuinely separate lifecycle—not merely
because it serves another circuit.

## 5. Proposed repository structure

Use `circuits/` rather than `tracks/` as the durable directory name. “Circuit”
is more precise in this domain and leaves “track” available for geometry,
progress, and telemetry concepts inside the code.

```text
race-lab/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CITATION.cff
├── AGENTS.md
├── pyproject.toml
├── package.json
│
├── docs/
│   ├── architecture/
│   │   ├── system-overview.md
│   │   ├── calibration-pipeline.md
│   │   ├── vehicle-dynamics-model.md
│   │   ├── artifact-architecture.md
│   │   └── web-application.md
│   │
│   ├── methodology/
│   │   ├── data-eligibility.md
│   │   ├── telemetry-quality.md
│   │   ├── circuit-alignment.md
│   │   ├── phase-segmentation.md
│   │   ├── feature-representation.md
│   │   ├── validation.md
│   │   └── uncertainty.md
│   │
│   ├── decisions/
│   │   └── YYYY-MM-DD-<decision>.md
│   │
│   └── governance/
│       ├── data-and-licensing-policy.md
│       ├── publication-policy.md
│       └── model-release-policy.md
│
├── schemas/
│   ├── source-manifest.schema.json
│   ├── circuit.schema.json
│   ├── lap-trace.schema.json
│   ├── calibration-report.schema.json
│   └── prediction-artifact.schema.json
│
├── src/
│   └── race_lab/
│       ├── ingestion/
│       ├── quality/
│       ├── circuits/
│       ├── alignment/
│       ├── segmentation/
│       ├── features/
│       ├── dynamics/
│       ├── calibration/
│       ├── validation/
│       ├── prediction/
│       └── artifacts/
│
├── apps/
│   └── web/
│       ├── src/
│       ├── public/
│       └── tests/
│
├── circuits/
│   ├── spa-francorchamps/
│   │   ├── README.md
│   │   ├── circuit/
│   │   │   ├── circuit.yaml
│   │   │   ├── layouts/
│   │   │   ├── corners/
│   │   │   ├── references/
│   │   │   └── limitations.md
│   │   │
│   │   └── seasons/
│   │       └── 2026/
│   │           ├── README.md
│   │           ├── specs/
│   │           ├── reviews/
│   │           ├── plans/
│   │           ├── manifests/
│   │           ├── reports/
│   │           └── artifacts/
│   │
│   ├── monza/
│   │   └── ...
│   └── suzuka/
│       └── ...
│
├── data/
│   ├── README.md
│   ├── source-manifests/
│   ├── fixtures/
│   └── .gitignore
│
├── generated/
│   ├── README.md
│   └── .gitignore
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── model_release/
│
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── pull_request_template.md
    └── workflows/
        ├── ci.yml
        ├── model-release.yml
        └── pages.yml
```

The initial repository need not create every empty directory. This tree defines
the intended boundaries; directories should appear as their first real artifact
is added.

## 6. Circuit and season organization

## 6.1 Circuit-stable material

Place material expected to survive across seasons under:

```text
circuits/spa-francorchamps/circuit/
```

Examples:

- canonical circuit identity;
- layout versions;
- centreline and elevation sources;
- corner and complex definitions;
- known source limitations;
- reusable historical references;
- aliases and naming conventions.

Circuit material should still be versioned where the physical venue changes.
A resurfacing, layout adjustment, DRS-zone change, kerb change, or materially
different reference geometry should not be silently treated as identical.

## 6.2 Season-specific material

Place work tied to a regulation year, data cutoff, event, or prediction under:

```text
circuits/spa-francorchamps/seasons/2026/
```

Examples:

- the Spa 2026 calibration specification;
- its review and defence;
- implementation plans;
- source-eligibility manifests;
- held-out validation reports;
- prediction artifacts;
- release decisions;
- event-specific assumptions.

This gives a future reader a coherent local chain:

```text
specs/       What was proposed and approved
reviews/     What planning had to resolve and why
plans/       How the work was decomposed
manifests/   Which evidence was eligible
reports/     What validation found
artifacts/   What was released
```

## 6.3 Shared implementation

Do not create:

```text
circuits/spa-francorchamps/src/
circuits/monza/src/
circuits/suzuka/src/
```

The ingestion, alignment, features, vehicle model, hierarchy, validation, and
artifact generation belong under `src/race_lab/`.

Circuit directories contain domain data, configuration, evidence, decisions,
and outputs. They should not fork the software architecture.

## 7. Placement of the current Spa documents

Move the existing calibration design to:

```text
circuits/spa-francorchamps/seasons/2026/specs/
  2026-07-14-calibration-design.md
```

Add the two review records to:

```text
circuits/spa-francorchamps/seasons/2026/reviews/
  2026-07-15-calibration-review-recommendations.md
  2026-07-15-calibration-review-defence.md
```

Move the current implementation plans to:

```text
circuits/spa-francorchamps/seasons/2026/plans/
  2026-07-14-calibration-program.md
  2026-07-14-calibration-data-pipeline.md
  2026-07-14-calibration-model-prediction.md
  2026-07-14-calibration-app-integration.md
```

The path already establishes “Spa 2026,” so future filenames may omit repeated
`spa-2026` wording. Existing names may be retained during migration if renaming
would make commit history harder to follow.

## 8. Why durable documents should not live under `docs/superpowers`

Superpowers is a process used to produce or review an artifact. It is not the
artifact's domain.

A specification remains a Spa 2026 calibration specification regardless of
whether it was developed through Superpowers, another planning workflow, or
manual engineering review.

Organizing canonical documents under `docs/superpowers/` causes several
problems:

- the filesystem records tool provenance instead of product meaning;
- related specs, reviews, plans, and reports become separated;
- future contributors may treat process directories as authority boundaries;
- changing planning methods would imply changing domain paths.

The repository may record process provenance in:

- YAML metadata;
- commit messages;
- an optional `process:` field;
- `AGENTS.md`;
- a workflow note under `docs/governance/`.

Repository instructions should explicitly override the default Superpowers
document path and direct circuit-specific artifacts to their domain directory.

## 9. Public repository and data policy

A public code repository does not imply that all acquired source data can be
redistributed.

The repository should distinguish:

### Safe to commit by default

- source adapters;
- schemas;
- methodology;
- manually authored specifications and reviews;
- small synthetic or expressly redistributable fixtures;
- source manifests and identifiers;
- generated results that are legally and methodologically publishable;
- checksums and reproducibility metadata.

### Commit only after rights and size review

- downloaded telemetry;
- derived traces that may reproduce protected source data;
- circuit geometry from third-party providers;
- images, maps, and logos;
- large generated artifacts;
- cached API responses.

### Do not commit by default

- credentials or session material;
- undocumented scraped payload dumps;
- data whose terms prohibit redistribution;
- proprietary or confidential data;
- provisional artifacts that the release policy suppresses.

Use manifests to record how eligible data can be retrieved rather than assuming
the repository must contain every raw byte.

## 10. Licensing recommendation

Do not copy Paddock's current “no license” state into Race Lab.

Before the first public release, choose explicit licensing for each category:

- **code:** Apache-2.0 is recommended because it is permissive and includes an
  express patent grant;
- **original documentation:** CC BY 4.0 or inclusion under the code license,
  depending on the desired contribution model;
- **third-party data:** retain its original terms and do not relicense it;
- **generated artifacts:** declare licensing per artifact where source rights
  allow.

This is a project-governance recommendation, not a conclusion that every
current input is redistributable.

The initial repository can be created public before all data licensing is
resolved, provided restricted data is excluded and the README clearly labels
the project as pre-release.

## 11. GitHub Pages and publication

Deploy the web application from the standalone repository, targeting a stable
project URL such as:

```text
https://loganrooks.github.io/race-lab/
```

Recommended route structure:

```text
/spa-francorchamps/2026/
/monza/2026/
/suzuka/2026/
```

Use a GitHub Actions Pages workflow rather than a long-lived hand-managed
publication branch.

The deployment workflow must distinguish:

- ordinary application builds;
- historical and educational simulations;
- validated prediction artifacts;
- suppressed or calibration-pending products.

A successful web build must not automatically imply that an unvalidated model
artifact is eligible for publication.

## 12. Integration with Paddock and other projects

The repository split should not prohibit later integration.

Race Lab may expose versioned outputs through:

- published JSON artifacts;
- a versioned package;
- release assets;
- a documented static endpoint;
- an exported visualization component.

Paddock or Prix Guesser may consume those outputs later without importing Race
Lab's internal source tree.

The integration rule should be:

> Share stable artifacts and interfaces across repositories; do not create
> hidden source-level coupling merely because both projects concern Formula 1.

## 13. History-preserving migration

## 13.1 Preferred extraction method

Create `loganrooks/race-lab` as an empty public repository—without an
automatically generated README or license commit—then extract the existing
`spa-race-lab` subtree from the source branch.

A suitable local sequence is:

```bash
git clone git@github.com:loganrooks/paddock.git
cd paddock
git fetch --all

git checkout spa-race-lab-pages
git subtree split \
  --prefix=spa-race-lab \
  -b race-lab-extract

git remote add race-lab git@github.com:loganrooks/race-lab.git
git push race-lab race-lab-extract:main
```

This preserves commits that affected the extracted subtree while removing the
unrelated Paddock tree from the new repository.

If the current Race Lab material spans paths outside `spa-race-lab/`, use
`git filter-repo` with an explicit reviewed path map instead.

## 13.2 Reorganization commit

After extraction, make one dedicated repository-layout commit that:

- moves the Spa specification;
- adds the review and defence;
- moves the four implementation plans;
- establishes the initial shared directories;
- adds the root README and public-data policy;
- configures repository-local planning paths;
- removes obsolete `docs/superpowers` paths.

Suggested commit:

```text
chore: establish Race Lab repository structure
```

Keep content changes separate from path changes wherever practical so reviewers
can distinguish migration from substantive revision.

## 13.3 Paddock cleanup

After verifying the new repository:

- stop new Race Lab work on the Paddock branch;
- add a concise pointer in Paddock only if a merged branch or public history
  would otherwise leave confusing references;
- update links in commits, documents, or issues that are still actively used;
- archive or delete the temporary branch only after the extraction has been
  verified;
- do not retain a second live copy of the Race Lab source.

The Paddock repository should remain focused on Prix Guesser and its own
long-arc product material.

## 14. Migration verification

The migration is complete only when all of the following are true:

- the new repository is public and accessible;
- the relevant source commits are present in its history;
- the Spa specification content matches the approved commit;
- both review documents are present;
- all four implementation plans are present;
- internal links resolve;
- no credentials or restricted raw data were migrated;
- the default branch builds and tests successfully;
- Pages deployment uses the new repository;
- the provisional **1:40.4** estimate remains suppressed;
- Paddock is no longer the active home of Race Lab work;
- README and metadata consistently identify the new repository.

## 15. Initial repository README contract

The new README should state, near the top:

1. Race Lab is an independent, public F1 circuit-analysis and simulation
   project.
2. It is not affiliated with Formula 1, the FIA, teams, drivers, circuits, or
   data providers.
3. Observed, inferred, and simulated quantities are distinguished.
4. Public data does not imply team-grade telemetry or proprietary parameter
   recovery.
5. Predictions are withheld when validation gates fail.
6. Raw third-party data is included only when redistribution is permitted.
7. Spa 2026 is the founding programme, not the permanent limit of the project.

## 16. Scaling to additional circuits

Adding a circuit should require:

- a canonical circuit identity and slug;
- geometry and provenance;
- source-eligibility assessment;
- corner and complex definitions;
- declared layout version;
- circuit-specific limitations;
- a season/event directory when predictions or reports are added.

Adding another circuit must not require copying the Spa code.

The second circuit should be used as an architectural test. Any “shared”
abstraction that only works for Spa should be revised before a large catalogue
of circuits is created.

Use a practical rule:

> Generalize shared code where the cross-circuit method already requires it,
> but defer speculative document and configuration abstractions until Spa and
> at least one materially different second circuit exercise them.

A good second circuit should stress different characteristics—for example,
Monza for long-straight and braking transfer, or Suzuka for sustained load and
direction-change behavior.

## 17. Risks and mitigations

### Risk: premature generalization

**Mitigation:** keep the approved Spa specification intact during migration;
extract shared doctrine incrementally.

### Risk: repository bloat

**Mitigation:** exclude bulk raw data, use manifests, keep only small fixtures,
and publish larger validated artifacts as releases or external storage where
appropriate.

### Risk: licensing confusion

**Mitigation:** create a data-and-licensing policy before importing new sources;
record source terms in every manifest.

### Risk: model and web releases become conflated

**Mitigation:** separate application CI from model-release eligibility and
artifact publication.

### Risk: duplicated active copies

**Mitigation:** declare the new repository authoritative immediately after
verification and retire the Paddock branch as a working location.

### Risk: circuit directories fork the implementation

**Mitigation:** prohibit circuit-local model source and require shared,
schema-driven interfaces.

## 18. Proposed execution sequence

### Phase 1 — Approve repository boundary

Approve:

- standalone public repository;
- repository name;
- circuit-first structure;
- migration method;
- data and publication boundaries.

### Phase 2 — Create and extract

- create the empty repository;
- split and push relevant history;
- verify source content;
- tag the imported baseline if useful.

### Phase 3 — Establish structure

- add root governance and build files;
- move Spa documents;
- add review artifacts;
- add implementation plans;
- establish initial schemas and source layout.

### Phase 4 — Repair references and deployment

- update internal links and metadata;
- update Pages deployment;
- remove RawGitHack or Paddock-specific publication assumptions;
- verify calibration-pending behavior.

### Phase 5 — Retire the old location

- mark the new repository authoritative;
- stop changes to the Paddock branch;
- retain only a pointer or archival reference where necessary.

### Phase 6 — Continue Spa implementation planning

Proceed from the approved Spa design, review recommendations, defence, and
implementation plans inside the new repository.

## 19. Approval criteria

Approve this proposal if the following statements are accepted:

1. Race Lab is an independent product and technical programme, not a Prix
   Guesser subsystem.
2. Its authoritative home should be `loganrooks/race-lab`.
3. The repository should be public, while third-party data remains subject to
   separate eligibility and licensing rules.
4. Circuits should have durable directories with season-specific work beneath
   them.
5. Shared software must remain outside circuit directories.
6. Specifications and reviews should be organized by domain, not under
   `docs/superpowers`.
7. The current Spa history should be extracted rather than copied without
   provenance.
8. Model release and web deployment must remain separate gates.

## 20. Proposed decision

> **Create `loganrooks/race-lab` as a standalone public repository. Extract the
> current `spa-race-lab` history from Paddock, establish a circuit-first
> multi-season structure, migrate the Spa specification, reviews, and plans,
> and make the new repository the sole active home of Race Lab work.**

This decision should be made before further calibration implementation creates
additional history, dependencies, and publication assumptions inside Paddock.
