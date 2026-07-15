# Spa Calibration App Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Spa Race Lab consume the versioned calibrated prediction artifact, synchronize predicted and historical traces across the map and telemetry views, and expose uncertainty, analogues, validation, provenance, and a safe calibration-pending state.

**Architecture:** A build-time adapter converts `spa-2026-prediction-v1.json` into a small JavaScript module validated against an explicit browser schema. A trace-source adapter gives the existing `MapController` one contract for the uncalibrated educational simulation, released predictions, historical Spa references, and completed-circuit analogue traces. UI modules render prediction status, uncertainty bands, source selection, corner evidence, and calibration-report details. The client never fits or modifies the statistical model.

**Tech Stack:** Existing vanilla HTML/CSS/JavaScript, Node test runner, esbuild, Playwright; no new browser dependency.

## Global Constraints

- Browser schema version is exactly `spa-calibration-prediction/v1`.
- The browser displays `Calibration pending` whenever the artifact is absent, malformed, checksum-invalid, stale, `pending`, or `failed-validation`.
- The existing coupled lap remains selectable as `Uncalibrated educational simulation`; it must not be labelled a 2026 prediction.
- Historical OpenF1 traces remain named and attributed; progress is observed, lateral placement is illustrative.
- Prediction intervals must be shown as intervals, not decorative exact times.
- Team predictions appear only when present in the released artifact.
- Map, chart, telemetry numbers, corner phase, and playback position must all come from the selected trace source.
- The app must preserve zoom/pan/touch, reduced motion, keyboard access, mobile layout, offline standalone operation, and RawGitHack compatibility.
- No provisional 1:40.4 claim may remain in source, bundle, standalone HTML, screenshots, or copy.


## Mandatory Review Resolutions

- The browser, build generator, Python model, and CLI use the same release predicate and fixture corpus. A checksum is necessary but never sufficient.
- The build generator calls `validateCalibrationArtifact()` after checksum verification and emits a frozen pending artifact on any schema, gate, interval, provenance, scenario, cutoff, or freshness failure.
- Historical OpenF1 inputs are normalized at the adapter boundary from legacy `speed/throttle/brake` names to `speedKph/throttlePct/brakePct`; raw objects never enter `TraceSource`.
- The UI displays the estimand and `spa-2026-dry-qualifying-reference/v1` scenario, including the best-of-two-attempts meaning and condition distributions.
- Rolling-origin, uncertainty calibration, baseline/ablation, identifiability, physical feasibility, and eligibility summaries are required before a released state can render.

---

## File Map

```text
scripts-build-calibration-data.mjs
js/calibration-data.js                 # generated, committed
js/calibration-schema.js
js/trace-sources.js
js/calibration-ui.js
js/telemetry-chart.js
js/app.js
js/map-controller.js
index.html
css/styles.css
sw.js
scripts-generate-standalone.mjs
tests/calibration-schema.test.js
tests/trace-sources.test.js
tests/telemetry-chart.test.js
tests/app.spec.js
```

## Shared Interfaces

```typescript
type TraceSample = {
  progress: number;
  elapsedSeconds: number;
  speedKph: number;
  throttlePct: number;
  brakePct: number;
  gear: number;
  longitudinalG?: number;
  lateralG?: number;
  deployKw?: number;
  regenKw?: number;
  lower80SpeedKph?: number;
  upper80SpeedKph?: number;
};

type TraceSource = {
  id: string;
  label: string;
  kind: "educational-model" | "prediction" | "historical" | "analogue";
  spatialRoute: "model-racing-line" | "reference-racing-line";
  trace: TraceSample[];
  timingTable: { progress: number; time: number }[];
  lapTimeSeconds: number | null;
  interval?: { lower80: number; median: number; upper80: number };
  disclosure: string;
  provenance: Record<string, unknown>;
};
```

---

### Task 1: Generate and validate the browser prediction module

**Files:**
- Create: `scripts-build-calibration-data.mjs`
- Create: `js/calibration-schema.js`
- Create: `tests/calibration-schema.test.js`
- Generate: `js/calibration-data.js`
- Modify: `package.json`

**Interfaces:**
- Consumes: `calibration/artifacts/predictions/spa-2026-prediction-v1.json`.
- Produces: `CALIBRATION_ARTIFACT`, `validateCalibrationArtifact()`, and deterministic build command `npm run calibration:data`.

- [ ] **Step 1: Write failing schema and fallback tests**

```javascript
// tests/calibration-schema.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import { pendingCalibrationArtifact, validateCalibrationArtifact } from '../js/calibration-schema.js';

const NOW = new Date('2026-07-15T00:00:00Z');
const REPORT_NAMES = ['loco', 'rollingOrigin', 'uncertaintyCalibration', 'baselinesAblations', 'identifiability', 'physicalFeasibility', 'eligibility'];

function releasedFixture(overrides = {}) {
  const reports = Object.fromEntries(REPORT_NAMES.map((name) => [name, { passed: true, checks: { complete: true } }]));
  return {
    schemaVersion: 'spa-calibration-prediction/v1',
    status: 'released',
    modelVersion: 'spa-corner-transfer/0.1.0',
    generatedAt: '2026-07-14T00:00:00Z',
    sourceCutoff: '2026-07-13T23:59:59Z',
    fieldBest: { lapTimeSeconds: { lower95: 99, lower80: 100, median: 101, upper80: 102, upper95: 103 } },
    teams: [], historicalReferences: [], analogueTraces: [], corners: [],
    validation: { release_gates: { passed: true, checks: { all: true } }, reports },
    provenance: {
      trainingManifestChecksum: '1'.repeat(64), sourceEligibilityChecksum: '2'.repeat(64),
      circuitYearEligibilityChecksum: '3'.repeat(64), scenarioChecksum: '4'.repeat(64),
      randomSeed: 7, regulationIdentifiers: ['2026'], hyperparameters: {},
      trainingCircuits: ['silverstone'], heldOutCircuits: ['spa'],
      validationReportChecksums: {}, codeCommit: 'a'.repeat(40),
      scenario: { id: 'spa-2026-dry-qualifying-reference/v1', attempts: 2 }
    },
    checksum: 'a'.repeat(64),
    ...overrides,
  };
}

const released = releasedFixture();
const validate = (value) => validateCalibrationArtifact(value, { now: NOW });

test('released artifact requires ordered field-best interval', () => {
  assert.equal(validate(released).status, 'released');
  assert.throws(() => validate({
    ...released,
    fieldBest: { lapTimeSeconds: { lower80: 102, median: 101, upper80: 100 } }
  }), /interval/i);
});

test('non-released artifacts cannot expose field best', () => {
  assert.throws(() => validate({ ...released, status: 'failed-validation' }), /fieldBest/i);
  assert.equal(pendingCalibrationArtifact('missing').fieldBest, null);
  assert.throws(() => validate({ ...released, checksum: 'bad' }), /checksum/i);
});
```

- [ ] **Step 2: Run and verify RED**

```bash
node --test tests/calibration-schema.test.js
```

Expected: missing module.

- [ ] **Step 3: Implement schema guard and deterministic generator**

```javascript
// js/calibration-schema.js
const SCHEMA = 'spa-calibration-prediction/v1';
const STATUS = new Set(['pending', 'failed-validation', 'released']);
const REQUIRED_REPORTS = ['loco', 'rollingOrigin', 'uncertaintyCalibration', 'baselinesAblations', 'identifiability', 'physicalFeasibility', 'eligibility'];
const REQUIRED_PROVENANCE = ['trainingManifestChecksum', 'sourceEligibilityChecksum', 'circuitYearEligibilityChecksum', 'scenarioChecksum', 'randomSeed', 'regulationIdentifiers', 'hyperparameters', 'trainingCircuits', 'heldOutCircuits', 'validationReportChecksums', 'codeCommit'];

function validateRequiredReleaseReports(validation) {
  for (const name of REQUIRED_REPORTS) {
    if (validation?.reports?.[name]?.passed !== true) throw new TypeError(`Missing or failed release report: ${name}`);
  }
}

function validateRequiredProvenance(provenance) {
  for (const name of REQUIRED_PROVENANCE) {
    if (provenance?.[name] === undefined || provenance?.[name] === null) throw new TypeError(`Missing release provenance: ${name}`);
  }
}

function validateScenario(scenario) {
  if (scenario?.id !== 'spa-2026-dry-qualifying-reference/v1' || scenario?.attempts !== 2) {
    throw new TypeError('Unsupported Spa prediction scenario');
  }
}

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function pendingCalibrationArtifact(reason = 'missing') {
  return Object.freeze({
    schemaVersion: SCHEMA,
    status: 'pending',
    reason,
    modelVersion: null,
    generatedAt: null,
    sourceCutoff: null,
    fieldBest: null,
    teams: [],
    historicalReferences: [],
    analogueTraces: [],
    corners: [],
    validation: null,
    provenance: {},
    checksum: null
  });
}

export function validateCalibrationArtifact(value, { now = new Date(), maximumAgeHours = 24 * 7 } = {}) {
  if (!value || value.schemaVersion !== SCHEMA) throw new TypeError('Unsupported calibration schema');
  if (!STATUS.has(value.status)) throw new TypeError('Invalid calibration status');
  if (value.status !== 'pending' && !/^[0-9a-f]{64}$/.test(value.checksum || '')) throw new TypeError('Invalid calibration checksum');
  if (value.status !== 'released') {
    if (value.fieldBest !== null || value.teams?.length || value.corners?.length) {
      throw new TypeError('Non-released calibration artifact must suppress fieldBest, teams, and predicted corners');
    }
  }
  if (value.status === 'released') {
    if (value.validation?.release_gates?.passed !== true) throw new TypeError('Released artifact requires passing release gates');
    if (!value.fieldBest) throw new TypeError('Released artifact requires fieldBest');
    validateRequiredReleaseReports(value.validation);
    validateRequiredProvenance(value.provenance);
    validateScenario(value.provenance?.scenario);
    const generated = Date.parse(value.generatedAt);
    const sourceCutoff = Date.parse(value.sourceCutoff);
    if (!Number.isFinite(generated) || !Number.isFinite(sourceCutoff)) throw new TypeError('Released artifact requires valid timestamps');
    if (now.getTime() - generated > maximumAgeHours * 3600_000) throw new TypeError('Released artifact is stale');
    const interval = value.fieldBest?.lapTimeSeconds;
    if (!interval || !(interval.lower80 <= interval.median && interval.median <= interval.upper80)) {
      throw new TypeError('Calibration lap-time interval is not ordered');
    }
  }
  for (const key of ['teams', 'historicalReferences', 'analogueTraces', 'corners']) {
    if (!Array.isArray(value[key])) throw new TypeError(`${key} must be an array`);
  }
  return Object.freeze(value);
}
```

```javascript
// scripts-build-calibration-data.mjs
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { validateCalibrationArtifact } from './js/calibration-schema.js';

const input = new URL('./calibration/artifacts/predictions/spa-2026-prediction-v1.json', import.meta.url);
const output = new URL('./js/calibration-data.js', import.meta.url);

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function pending(reason) {
  return {
    schemaVersion: 'spa-calibration-prediction/v1', status: 'pending', reason,
    modelVersion: null, generatedAt: null, sourceCutoff: null, fieldBest: null,
    teams: [], historicalReferences: [], analogueTraces: [], corners: [],
    validation: null, provenance: {}, checksum: null
  };
}

const generatedAt = new Date();
let artifact;
try {
  artifact = JSON.parse(await readFile(input, 'utf8'));
  if (artifact.status !== 'pending') {
    const { checksum, ...unsigned } = artifact;
    const actual = createHash('sha256').update(canonicalJson(unsigned)).digest('hex');
    if (checksum !== actual) throw new Error(`checksum mismatch ${checksum} != ${actual}`);
  }
  artifact = validateCalibrationArtifact(artifact, { now: generatedAt, maximumAgeHours: 24 * 7 });
} catch (error) {
  artifact = pending(error.code === 'ENOENT' ? 'missing' : 'invalid-or-unverified');
}
const sourceHash = createHash('sha256').update(canonicalJson(artifact)).digest('hex');
const moduleText = `// Generated by scripts-build-calibration-data.mjs; source ${sourceHash}
export const CALIBRATION_ARTIFACT = Object.freeze(${JSON.stringify(artifact)});
`;
await writeFile(output, moduleText, 'utf8');
console.log(`wrote js/calibration-data.js status=${artifact.status}`);
```


Add scripts to `package.json`:

```json
{
  "calibration:data": "node scripts-build-calibration-data.mjs",
  "build": "npm run calibration:data && esbuild js/app.js --bundle --minify --format=iife --target=es2020 --outfile=dist/app.bundle.js"
}
```

- [ ] **Step 4: Verify GREEN and deterministic output**

```bash
node --test tests/calibration-schema.test.js
npm run calibration:data
cp js/calibration-data.js /tmp/calibration-data-a.js
npm run calibration:data
cmp /tmp/calibration-data-a.js js/calibration-data.js
```

Expected: tests pass; `cmp` exits 0.

- [ ] **Step 5: Commit artifact adapter**

```bash
git add scripts-build-calibration-data.mjs js/calibration-schema.js js/calibration-data.js tests/calibration-schema.test.js package.json
git commit -m "feat(app): load gated calibration artifact"
```

---

### Task 2: Normalize every lap source behind one trace-source contract

**Files:**
- Create: `js/trace-sources.js`
- Create: `tests/trace-sources.test.js`
- Modify: `js/app.js`
- Modify: `js/map-controller.js`

**Interfaces:**
- Consumes: educational simulation, `CALIBRATION_ARTIFACT`, bundled historical references.
- Produces: `buildTraceSources()`, `sampleTrace()`, and `state.activeTraceSourceId`.

- [ ] **Step 1: Write failing trace-source tests**

```javascript
// tests/trace-sources.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildTraceSources, sampleTrace } from '../js/trace-sources.js';

const simulation = {
  lapTimeSeconds: 105,
  timingTable: [{ progress: 0, time: 0 }, { progress: 1, time: 1 }],
  trace: [
    { progress: 0, elapsedSeconds: 0, speedKph: 300, throttlePct: 100, brakePct: 0, gear: 8 },
    { progress: 1, elapsedSeconds: 105, speedKph: 300, throttlePct: 100, brakePct: 0, gear: 8 }
  ]
};

test('uncalibrated simulation is never called a prediction', () => {
  const [source] = buildTraceSources({ simulation, calibration: { status: 'pending', teams: [], analogueTraces: [] }, references: [] });
  assert.equal(source.kind, 'educational-model');
  assert.match(source.label, /Uncalibrated/i);
  assert.equal(source.spatialRoute, 'model-racing-line');
});

test('historical trace uses reference trajectory and interpolates telemetry', () => {
  const [, historical] = buildTraceSources({
    simulation,
    calibration: { status: 'pending', teams: [], analogueTraces: [] },
    references: [{ id: 'real', driver: { name: 'Driver' }, lapTimeSeconds: 100, trace: simulation.trace, timingTable: simulation.timingTable }]
  });
  assert.equal(historical.spatialRoute, 'reference-racing-line');
  assert.equal(sampleTrace(historical, .5).speedKph, 300);
});
```

- [ ] **Step 2: Run and verify RED**

```bash
node --test tests/trace-sources.test.js
```

Expected: missing module.

- [ ] **Step 3: Implement source adapters and route-safe playback**

```javascript
// js/trace-sources.js
export function buildTraceSources({ simulation, calibration, references }) {
  const sources = [{
    id: 'educational-model',
    label: 'Uncalibrated educational simulation',
    kind: 'educational-model',
    spatialRoute: 'model-racing-line',
    trace: simulation.trace,
    timingTable: simulation.timingTable,
    lapTimeSeconds: simulation.lapTimeSeconds,
    interval: null,
    disclosure: 'Coupled vehicle model; not the calibrated 2026 Spa prediction.',
    provenance: { model: simulation.modelVersion || 'vehicle-model' }
  }];
  if (calibration.status === 'released') {
    sources.push({
      id: 'field-best-2026',
      label: '2026 predicted field best',
      kind: 'prediction',
      spatialRoute: 'model-racing-line',
      trace: calibration.fieldBest.trace,
      timingTable: calibration.fieldBest.timingTable,
      lapTimeSeconds: calibration.fieldBest.lapTimeSeconds.median,
      interval: calibration.fieldBest.lapTimeSeconds,
      disclosure: 'Backtested corner-transfer prediction with posterior uncertainty.',
      provenance: calibration.provenance
    });
    for (const team of calibration.teams) {
      sources.push({
        id: `team-${team.slug}`,
        label: `${team.teamName} 2026 prediction`,
        kind: 'prediction',
        spatialRoute: 'model-racing-line',
        trace: team.trace,
        timingTable: team.timingTable,
        lapTimeSeconds: team.lapTimeSeconds.median,
        interval: team.lapTimeSeconds,
        disclosure: team.disclosure,
        provenance: team.provenance
      });
    }
  }
  for (const reference of references) {
    sources.push({
      id: reference.id,
      label: `${reference.driver.name} · ${reference.year} ${reference.sessionName}`,
      kind: 'historical',
      spatialRoute: 'reference-racing-line',
      trace: reference.trace.map((sample) => {
        const { speed, throttle, brake, ...rest } = sample;
        return {
          ...rest,
          speedKph: sample.speedKph ?? speed,
          throttlePct: sample.throttlePct ?? throttle,
          brakePct: sample.brakePct ?? brake,
        };
      }),
      timingTable: reference.timingTable,
      lapTimeSeconds: reference.lapTimeSeconds,
      interval: null,
      disclosure: 'Observed OpenF1 telemetry synchronized by progress; lateral line placement is illustrative.',
      provenance: reference.source
    });
  }
  for (const analogue of calibration.analogueTraces || []) {
    sources.push({ ...analogue, kind: 'analogue', spatialRoute: 'reference-racing-line' });
  }
  return sources;
}

export function sampleTrace(source, progress) {
  const trace = source.trace;
  const p = Math.max(0, Math.min(1, progress));
  let right = trace.findIndex((row) => row.progress >= p);
  if (right <= 0) return { ...trace[0] };
  if (right < 0) return { ...trace.at(-1) };
  const left = trace[right - 1];
  const next = trace[right];
  const ratio = (p - left.progress) / Math.max(next.progress - left.progress, 1e-9);
  const interpolate = (key) => Number.isFinite(left[key]) && Number.isFinite(next[key])
    ? left[key] + (next[key] - left[key]) * ratio
    : left[key] ?? next[key];
  return {
    progress: p,
    elapsedSeconds: interpolate('elapsedSeconds'),
    speedKph: interpolate('speedKph'),
    throttlePct: interpolate('throttlePct'),
    brakePct: interpolate('brakePct'),
    gear: Math.round(interpolate('gear')),
    longitudinalG: interpolate('longitudinalG'),
    lateralG: interpolate('lateralG'),
    deployKw: interpolate('deployKw'),
    regenKw: interpolate('regenKw'),
    lower80SpeedKph: interpolate('lower80SpeedKph'),
    upper80SpeedKph: interpolate('upper80SpeedKph')
  };
}
```

Modify `MapController` to receive an explicit route and import the shared sampler:

```javascript
import { sampleTrace } from './trace-sources.js';

setTraceSource(source) {
  if (!source?.trace?.length || !source?.timingTable?.length) throw new TypeError('Trace source requires trace and timingTable');
  if (this.playbackState === 'playing') this.pause();
  this.traceSource = source;
  this.playbackRoute = source.spatialRoute === 'reference-racing-line' ? 'reference' : 'racing';
  this.playbackSourceId = source.id;
  this.timingTable = source.timingTable;
  this.duration = 20500;
  this.car.dataset.source = source.id;
  this.setTime(0);
}

setTime(time) {
  const boundedTime = clamp(time, 0, 1);
  this.playbackTime = boundedTime;
  const progress = progressAtTime(this.timingTable, boundedTime);
  const point = this.pointAt(progress, this.playbackRoute);
  const telemetry = sampleTrace(this.traceSource, progress);
  this.car.setAttribute('transform', `translate(${round(point.x)} ${round(point.y)}) rotate(${round(point.angle)})`);
  this.car.classList.toggle('positioned', boundedTime > 0);
  if (this.progressBar) this.progressBar.style.width = `${progress * 100}%`;
  if (this.scrubber && Number(this.scrubber.value) !== Math.round(progress * 1000)) {
    this.scrubber.value = String(Math.round(progress * 1000));
  }
  this.onProgress?.({ time: boundedTime, progress, telemetry, point, sourceId: this.playbackSourceId });
  if (this.followCar) this.followPoint(point);
}
```

- [ ] **Step 4: Verify GREEN**

```bash
node --test tests/trace-sources.test.js
npm test
```

Expected: trace-source tests and existing domain tests pass.

- [ ] **Step 5: Commit unified trace sources**

```bash
git add js/trace-sources.js js/app.js js/map-controller.js tests/trace-sources.test.js
git commit -m "feat(app): unify predicted and historical lap sources"
```

---

### Task 3: Add prediction status and source selection UI

**Files:**
- Create: `js/calibration-ui.js`
- Modify: `index.html`
- Modify: `css/styles.css`
- Modify: `js/app.js`
- Modify: `tests/app.spec.js`

**Interfaces:**
- Consumes: artifact status and trace sources.
- Produces: prediction status card, source selector, formatted interval, disclosure, and active source state.

- [ ] **Step 1: Add failing pending and released UI tests**

```javascript
// append to tests/app.spec.js
test('shows calibration pending and suppresses provisional pole value', async ({ page }) => {
  await expect(page.locator('#prediction-status')).toContainText(/Calibration pending|Failed validation/i);
  await expect(page.locator('body')).not.toContainText('1:40.4');
  await expect(page.getByRole('option', { name: /Uncalibrated educational simulation/i })).toHaveCount(1);
});

test('source selector changes disclosure and playback source', async ({ page }) => {
  const selector = page.locator('#trace-source-select');
  await expect(selector).toBeVisible();
  const options = await selector.locator('option').allTextContents();
  expect(options.some((value) => /OpenF1|2025|Qualifying/i.test(value))).toBeTruthy();
  await selector.selectOption({ index: 1 });
  await expect(page.locator('#trace-source-disclosure')).not.toBeEmpty();
});
```

- [ ] **Step 2: Run and verify RED**

```bash
npx playwright test tests/app.spec.js -g 'calibration pending|source selector'
```

Expected: selectors not found.

- [ ] **Step 3: Add semantic markup, renderer, and restrained racing-red styles**

```html
<!-- insert in index.html above the circuit map toolbar -->
<section class="prediction-strip" aria-labelledby="prediction-heading">
  <div>
    <p class="card-kicker">Spa 2026 calibration</p>
    <h3 id="prediction-heading">Prediction status</h3>
    <p id="prediction-status" aria-live="polite"></p>
  </div>
  <div class="prediction-time" id="prediction-time" hidden>
    <strong id="prediction-median"></strong>
    <span id="prediction-interval"></span>
  </div>
  <label class="trace-selector">
    <span>Lap source</span>
    <select id="trace-source-select" name="trace-source"></select>
  </label>
  <p id="trace-source-disclosure" class="source-disclosure"></p>
</section>
```

```javascript
// js/calibration-ui.js
export function formatLapTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${(seconds - minutes * 60).toFixed(2).padStart(5, '0')}`;
}

export function renderPredictionStatus(artifact, elements) {
  const released = artifact.status === 'released';
  elements.status.textContent = released
    ? `Released model ${artifact.modelVersion} · data through ${new Date(artifact.sourceCutoff).toLocaleDateString()}`
    : artifact.status === 'failed-validation'
      ? 'Calibration failed validation. The educational simulation remains available.'
      : 'Calibration pending. No 2026 pole estimate is displayed.';
  elements.time.hidden = !released;
  if (released) {
    const interval = artifact.fieldBest.lapTimeSeconds;
    elements.median.textContent = formatLapTime(interval.median);
    elements.interval.textContent = `80% interval ${formatLapTime(interval.lower80)}–${formatLapTime(interval.upper80)}`;
  }
}

export function renderTraceSelector(select, sources, activeId) {
  const options = sources.map((source) => {
    const option = document.createElement('option');
    option.value = source.id;
    option.textContent = source.label;
    option.selected = source.id === activeId;
    return option;
  });
  select.replaceChildren(...options);
}
```

```css
/* append to css/styles.css */
.prediction-strip { display:grid; grid-template-columns:minmax(230px,1fr) auto minmax(230px,.8fr); gap:22px; align-items:center; padding:18px 20px; border-bottom:1px solid var(--line); background:linear-gradient(90deg, rgba(225,6,0,.12), transparent 45%); }
.prediction-strip h3 { margin-bottom:4px; }
.prediction-strip p { margin-bottom:0; }
.prediction-time { padding-left:18px; border-left:3px solid var(--accent); }
.prediction-time strong { display:block; font:800 1.65rem/1 var(--mono); font-variant-numeric:tabular-nums; }
.prediction-time span, .source-disclosure, .trace-selector span { color:var(--muted); font-size:.72rem; }
.trace-selector { display:grid; gap:5px; }
.trace-selector select { width:100%; }
@media (max-width: 760px) { .prediction-strip { grid-template-columns:1fr; } .prediction-time { border-left:0; border-top:2px solid var(--accent); padding:12px 0 0; } }
```

- [ ] **Step 4: Verify GREEN**

```bash
npm run standalone
npx playwright test tests/app.spec.js -g 'calibration pending|source selector'
```

Expected: both tests pass.

- [ ] **Step 5: Commit prediction selector**

```bash
git add js/calibration-ui.js js/app.js index.html css/styles.css tests/app.spec.js
git commit -m "feat(app): show prediction status and lap selector"
```

---

### Task 4: Render telemetry comparisons and prediction uncertainty

**Files:**
- Create: `js/telemetry-chart.js`
- Create: `tests/telemetry-chart.test.js`
- Modify: `index.html`
- Modify: `css/styles.css`
- Modify: `js/app.js`
- Modify: `tests/app.spec.js`

**Interfaces:**
- Consumes: selected source and comparison sources.
- Produces: speed interval band, speed comparisons, throttle/brake controls, longitudinal/lateral-g dynamics, energy channels where available, cursor synchronization, and legend.

- [ ] **Step 1: Write failing chart geometry tests**

```javascript
// tests/telemetry-chart.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildBandPath, buildLinePath, chartY } from '../js/telemetry-chart.js';

test('higher speed maps upward on the chart', () => {
  assert.ok(chartY(320, 0, 350, 200) < chartY(80, 0, 350, 200));
});

test('uncertainty band closes upper and lower boundaries', () => {
  const rows = [
    { progress: 0, lower80SpeedKph: 90, upper80SpeedKph: 110 },
    { progress: 1, lower80SpeedKph: 290, upper80SpeedKph: 310 }
  ];
  const path = buildBandPath(rows, { width: 100, height: 100, min: 0, max: 350 });
  assert.match(path, /^M/);
  assert.match(path, /Z$/);
});

test('line path is monotonic in horizontal progress', () => {
  const path = buildLinePath([{ progress: 0, speedKph: 100 }, { progress: .5, speedKph: 200 }, { progress: 1, speedKph: 300 }], 'speedKph', { width: 100, height: 100, min: 0, max: 350 });
  assert.equal(path, 'M0 71.43 L50 42.86 L100 14.29');
});

test('control channels use the same progress x-axis', () => {
  const rows = [{ progress: 0, throttlePct: 0, brakePct: 100 }, { progress: 1, throttlePct: 100, brakePct: 0 }];
  assert.equal(buildLinePath(rows, 'throttlePct', { width: 100, height: 100, min: 0, max: 100 }), 'M0 100 L100 0');
  assert.equal(buildLinePath(rows, 'brakePct', { width: 100, height: 100, min: 0, max: 100 }), 'M0 0 L100 100');
});
```

- [ ] **Step 2: Run and verify RED**

```bash
node --test tests/telemetry-chart.test.js
```

Expected: missing module.

- [ ] **Step 3: Implement pure SVG chart builders and UI renderer**

```javascript
// js/telemetry-chart.js
const round = (value) => Math.round(value * 100) / 100;
export const chartY = (value, min, max, height) => round(height - ((value - min) / Math.max(max - min, 1e-9)) * height);
const chartX = (progress, width) => round(progress * width);

export function buildLinePath(rows, key, bounds) {
  return rows.map((row, index) => `${index ? 'L' : 'M'}${chartX(row.progress, bounds.width)} ${chartY(row[key], bounds.min, bounds.max, bounds.height)}`).join(' ');
}

export function buildBandPath(rows, bounds) {
  const upper = rows.map((row) => [chartX(row.progress, bounds.width), chartY(row.upper80SpeedKph, bounds.min, bounds.max, bounds.height)]);
  const lower = [...rows].reverse().map((row) => [chartX(row.progress, bounds.width), chartY(row.lower80SpeedKph, bounds.min, bounds.max, bounds.height)]);
  return [...upper, ...lower].map(([x, y], index) => `${index ? 'L' : 'M'}${x} ${y}`).join(' ') + ' Z';
}

export function renderTelemetryChart(root, selected, comparisons = []) {
  const speedBounds = { width: 1000, height: 210, min: 0, max: 360 };
  const controlBounds = { width: 1000, height: 100, min: 0, max: 100 };
  const dynamicsBounds = { width: 1000, height: 100, min: -5.5, max: 5.5 };
  const band = selected.kind === 'prediction' && selected.trace.some((row) => Number.isFinite(row.lower80SpeedKph))
    ? `<path class="telemetry-band" d="${buildBandPath(selected.trace, speedBounds)}"/>`
    : '';
  const comparisonLines = comparisons.map((source) => `<path class="telemetry-reference" data-source="${source.id}" d="${buildLinePath(source.trace, 'speedKph', speedBounds)}"/>`).join('');
  const longitudinal = selected.trace.some((row) => Number.isFinite(row.longitudinalG))
    ? `<path class="telemetry-longitudinal" d="${buildLinePath(selected.trace, 'longitudinalG', dynamicsBounds)}"/>`
    : '';
  const lateral = selected.trace.some((row) => Number.isFinite(row.lateralG))
    ? `<path class="telemetry-lateral" d="${buildLinePath(selected.trace, 'lateralG', dynamicsBounds)}"/>`
    : '';
  const deploy = selected.trace.some((row) => Number.isFinite(row.deployKw))
    ? `<path class="telemetry-deploy" d="${buildLinePath(selected.trace, 'deployKw', { width: 1000, height: 100, min: -350, max: 350 })}"/>`
    : '';
  const regen = selected.trace.some((row) => Number.isFinite(row.regenKw))
    ? `<path class="telemetry-regen" d="${buildLinePath(selected.trace, 'regenKw', { width: 1000, height: 100, min: -350, max: 350 })}"/>`
    : '';
  root.innerHTML = `
    <svg class="telemetry-speed-panel" viewBox="0 0 1000 210" role="img" aria-label="Speed comparison around Spa">${band}${comparisonLines}<path class="telemetry-selected" d="${buildLinePath(selected.trace, 'speedKph', speedBounds)}"/><line class="telemetry-cursor" data-chart-cursor x1="0" x2="0" y1="0" y2="210"/></svg>
    <svg class="telemetry-controls-panel" viewBox="0 0 1000 100" role="img" aria-label="Throttle and brake around Spa"><path class="telemetry-throttle" d="${buildLinePath(selected.trace, 'throttlePct', controlBounds)}"/><path class="telemetry-brake" d="${buildLinePath(selected.trace, 'brakePct', controlBounds)}"/><line class="telemetry-cursor" data-chart-cursor x1="0" x2="0" y1="0" y2="100"/></svg>
    <svg class="telemetry-dynamics-panel" viewBox="0 0 1000 100" role="img" aria-label="Dynamics and energy around Spa">${longitudinal}${lateral}${deploy}${regen}<line class="telemetry-cursor" data-chart-cursor x1="0" x2="0" y1="0" y2="100"/></svg>`;
}

export function updateTelemetryCursors(root, progress) {
  const x = Math.max(0, Math.min(1000, progress * 1000));
  root.querySelectorAll('[data-chart-cursor]').forEach((line) => {
    line.setAttribute('x1', String(x));
    line.setAttribute('x2', String(x));
  });
}
```

Add markup:

```html
<section class="telemetry-comparison" aria-labelledby="telemetry-comparison-title">
  <div class="telemetry-comparison-heading">
    <h3 id="telemetry-comparison-title">Lap telemetry</h3>
    <div id="telemetry-legend" class="telemetry-legend"></div>
  </div>
  <div id="telemetry-chart" class="telemetry-chart"></div>
</section>
```

```css
.telemetry-comparison { padding:20px; border-top:1px solid var(--line); }
.telemetry-comparison-heading { display:flex; align-items:end; justify-content:space-between; gap:18px; }
.telemetry-chart svg { display:block; width:100%; height:auto; overflow:visible; }
.telemetry-band { fill:rgba(225,6,0,.16); stroke:none; }
.telemetry-selected { fill:none; stroke:var(--accent); stroke-width:3; vector-effect:non-scaling-stroke; }
.telemetry-throttle { fill:none; stroke:#f6f2ec; stroke-width:2; }
.telemetry-brake { fill:none; stroke:var(--accent); stroke-width:2; }
.telemetry-longitudinal { fill:none; stroke:#ffb36b; stroke-width:1.6; }
.telemetry-lateral { fill:none; stroke:#7bb8ff; stroke-width:1.6; }
.telemetry-deploy { fill:none; stroke:#ff5a52; stroke-width:1.3; }
.telemetry-regen { fill:none; stroke:#f1bd4a; stroke-width:1.3; }
.telemetry-controls-panel, .telemetry-dynamics-panel { margin-top:8px; border-top:1px solid var(--line); }
.telemetry-reference { fill:none; stroke:rgba(255,255,255,.38); stroke-width:1.4; vector-effect:non-scaling-stroke; }
.telemetry-cursor { stroke:#fff; stroke-width:1; stroke-dasharray:3 4; vector-effect:non-scaling-stroke; }
```

- [ ] **Step 4: Verify chart and synchronized cursor**

```bash
node --test tests/telemetry-chart.test.js
npm run standalone
npx playwright test tests/app.spec.js -g 'telemetry|source selector'
```

Expected: chart tests pass; changing source changes selected path; moving scrubber moves `#telemetry-cursor`.

- [ ] **Step 5: Commit telemetry comparison**

```bash
git add js/telemetry-chart.js js/app.js index.html css/styles.css tests/telemetry-chart.test.js tests/app.spec.js
git commit -m "feat(app): visualize lap traces and uncertainty"
```

---

### Task 5: Add corner prediction evidence drawer

**Files:**
- Modify: `index.html`
- Modify: `css/styles.css`
- Modify: `js/calibration-ui.js`
- Modify: `js/app.js`
- Modify: `tests/app.spec.js`

**Interfaces:**
- Consumes: `artifact.corners` and selected turn/complex.
- Produces: `renderCornerPrediction()`, analogue table, observed/inferred/simulated labels, and confidence indicator.

- [ ] **Step 1: Add failing corner drawer test**

```javascript
// append to tests/app.spec.js
test('corner drawer distinguishes predicted deltas from observed analogues', async ({ page }) => {
  await page.locator('[data-corner-marker="10"]').click();
  const drawer = page.locator('#corner-prediction');
  await expect(drawer).toBeVisible();
  await expect(drawer).toContainText(/Predicted|Calibration pending/i);
  await expect(drawer).toContainText(/Observed|Inferred|Simulated|unavailable/i);
  await expect(page.locator('#layer-calibration-confidence')).toHaveCount(1);
});
```

- [ ] **Step 2: Run and verify RED**

```bash
npx playwright test tests/app.spec.js -g 'corner drawer'
```

Expected: `#corner-prediction` missing.

- [ ] **Step 3: Add accessible drawer markup and renderer**

```html
<!-- add inside the map viewport after the racing-line layer -->
<g id="layer-calibration-confidence" class="map-layer calibration-confidence-layer" aria-hidden="true"></g>

<!-- add inside the existing corner notebook -->
<section id="corner-prediction" class="corner-prediction" aria-labelledby="corner-prediction-title">
  <div class="corner-prediction-heading">
    <h4 id="corner-prediction-title">2026 calibration evidence</h4>
    <span id="corner-confidence" class="confidence-badge"></span>
  </div>
  <div id="corner-prediction-metrics" class="corner-prediction-metrics"></div>
  <div id="corner-analogues" class="corner-analogues"></div>
  <p id="corner-prediction-disclosure" class="source-disclosure"></p>
</section>
```

```javascript
// append to js/calibration-ui.js
export function renderCornerPrediction(artifact, complexId, elements) {
  const prediction = artifact.status === 'released'
    ? artifact.corners.find((row) => row.complexId === complexId)
    : null;
  if (!prediction) {
    elements.confidence.textContent = 'Unavailable';
    elements.metrics.innerHTML = '<p>Calibration pending; no 2026 corner delta is published.</p>';
    elements.analogues.innerHTML = '';
    elements.disclosure.textContent = 'The displayed driving notes remain educational, not calibrated predictions.';
    return;
  }
  elements.confidence.textContent = `${Math.round(prediction.confidence * 100)}% support`;
  elements.metrics.innerHTML = `
    <dl>
      <div><dt>Phase time</dt><dd>${signed(prediction.phaseTimeDeltaSeconds.median, 3)} s <span>Predicted</span></dd></div>
      <div><dt>Minimum speed</dt><dd>${signed(prediction.minimumSpeedDeltaKph.median, 1)} km/h <span>Inferred</span></dd></div>
      <div><dt>Brake onset</dt><dd>${signed(prediction.brakingOnsetDeltaM.median, 0)} m <span>Inferred</span></dd></div>
      <div><dt>Exit speed</dt><dd>${signed(prediction.exitSpeed100mDeltaKph.median, 1)} km/h <span>Predicted</span></dd></div>
    </dl>`;
  elements.analogues.innerHTML = `<h5>Closest observed phases</h5><ol>${prediction.analogues.map((row) => `<li><strong>${row.circuitLabel} · ${row.complexLabel}</strong><span>${Math.round(row.weight * 100)}% similarity weight · Observed ${row.year}</span></li>`).join('')}</ol>`;
  elements.disclosure.textContent = prediction.dominantUncertainty;
}

export function renderConfidenceLayer(root, cornerPredictions, pathSegmentBuilder) {
  root.innerHTML = cornerPredictions.map((corner) => {
    const opacity = Math.max(.12, Math.min(.72, corner.confidence));
    const dash = corner.confidence < .55 ? '8 7' : corner.confidence < .75 ? '3 5' : '';
    return `<path data-complex-confidence="${corner.complexId}" d="${pathSegmentBuilder(corner.startProgress, corner.endProgress)}" style="opacity:${opacity};stroke-dasharray:${dash}"/>`;
  }).join('');
}

function signed(value, digits) {
  const number = Number(value);
  return `${number > 0 ? '+' : ''}${number.toFixed(digits)}`;
}
```

```css
.calibration-confidence-layer path { fill:none; stroke:var(--accent); stroke-width:9; stroke-linecap:butt; pointer-events:none; }
.corner-prediction { margin-top:24px; padding-top:20px; border-top:1px solid var(--line); }
.corner-prediction-heading { display:flex; justify-content:space-between; align-items:center; gap:12px; }
.confidence-badge { padding:4px 8px; border:1px solid color-mix(in srgb,var(--accent) 55%,var(--line)); color:var(--accent-2); font:700 .65rem var(--mono); }
.corner-prediction-metrics dl { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1px; background:var(--line); }
.corner-prediction-metrics dl > div { padding:10px; background:var(--panel-solid); }
.corner-prediction-metrics dt { color:var(--muted); font-size:.68rem; }
.corner-prediction-metrics dd { margin:3px 0 0; font:700 .9rem var(--mono); }
.corner-prediction-metrics dd span { display:block; color:var(--faint); font:600 .58rem var(--sans); text-transform:uppercase; }
.corner-analogues ol { padding-left:20px; }
.corner-analogues li span { display:block; color:var(--muted); font-size:.7rem; }
```

- [ ] **Step 4: Verify GREEN**

```bash
npm run standalone
npx playwright test tests/app.spec.js -g 'corner drawer'
```

Expected: pass in pending fixture; released fixture test added later can assert analogue rows.

- [ ] **Step 5: Commit corner evidence**

```bash
git add js/calibration-ui.js js/app.js index.html css/styles.css tests/app.spec.js
git commit -m "feat(app): explain corner prediction evidence"
```

---

### Task 6: Add the calibration report and release-gate evidence

**Files:**
- Modify: `index.html`
- Modify: `css/styles.css`
- Modify: `js/calibration-ui.js`
- Modify: `js/app.js`
- Modify: `tests/app.spec.js`

**Interfaces:**
- Consumes: `artifact.validation` and `artifact.provenance`.
- Produces: collapsible training-data, exclusion, holdout, baseline, gate, version, cutoff, assumptions, and limitations report.

- [ ] **Step 1: Add failing calibration report test**

```javascript
// append to tests/app.spec.js
test('calibration report exposes cutoff, validation and limitations', async ({ page }) => {
  const details = page.locator('#calibration-report');
  await expect(details).toBeVisible();
  await details.locator('summary').click();
  await expect(details).toContainText(/data cutoff|source cutoff/i);
  await expect(details).toContainText(/held-out|validation/i);
  await expect(details).toContainText(/battery|lateral placement|limitations/i);
});
```

- [ ] **Step 2: Run and verify RED**

```bash
npx playwright test tests/app.spec.js -g 'calibration report'
```

Expected: selector missing.

- [ ] **Step 3: Add semantic details element and report renderer**

```html
<details id="calibration-report" class="calibration-report">
  <summary>How the 2026 prediction is calibrated</summary>
  <div id="calibration-report-body"></div>
</details>
```

```javascript
// append to js/calibration-ui.js
export function renderCalibrationReport(artifact, root) {
  const validation = artifact.validation;
  const provenance = artifact.provenance || {};
  root.innerHTML = `
    <div class="calibration-report-grid">
      <section><h4>Data cutoff</h4><p>${artifact.sourceCutoff ? new Date(artifact.sourceCutoff).toLocaleString() : 'No released calibration corpus'}</p></section>
      <section><h4>Training circuits</h4><p>${(provenance.trainingCircuits || []).join(', ') || 'Unavailable'}</p></section>
      <section><h4>Held-out validation</h4><p>${validation ? `${validation.folds?.length || 0} circuit folds` : 'Not run'}</p></section>
      <section><h4>Release gates</h4><ul>${Object.entries(validation?.release_gates?.checks || {}).map(([name, passed]) => `<li class="${passed ? 'pass' : 'fail'}">${name}: ${passed ? 'pass' : 'fail'}</li>`).join('') || '<li>Calibration pending</li>'}</ul></section>
      <section><h4>Baseline comparison</h4><p>${validation?.metrics ? `Model MAE ${validation.metrics.model_lap_mae_s.toFixed(2)} s; whole-circuit baseline ${validation.metrics.baseline_lap_mae_s.toFixed(2)} s.` : 'Unavailable'}</p></section>
      <section><h4>Limitations</h4><p>Battery state, electrical power, aerodynamic coefficients and historical lateral placement are inferred or illustrative, not proprietary measured telemetry.</p></section>
    </div>`;
}
```

```css
.calibration-report { margin:24px 20px 20px; border:1px solid var(--line); background:var(--panel-solid); }
.calibration-report summary { cursor:pointer; padding:14px 16px; font-weight:750; }
.calibration-report summary:focus-visible { outline:2px solid var(--accent); outline-offset:3px; }
.calibration-report-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px; background:var(--line); border-top:1px solid var(--line); }
.calibration-report-grid section { padding:14px; background:var(--panel-solid); }
.calibration-report-grid h4 { margin-bottom:6px; font-size:.75rem; text-transform:uppercase; }
.calibration-report-grid p, .calibration-report-grid li { color:var(--muted); font-size:.72rem; }
.calibration-report-grid .pass { color:#d8f5df; }
.calibration-report-grid .fail { color:var(--accent-2); }
@media (max-width:760px) { .calibration-report-grid { grid-template-columns:1fr; } }
```

- [ ] **Step 4: Verify GREEN**

```bash
npm run standalone
npx playwright test tests/app.spec.js -g 'calibration report'
```

Expected: pass.

- [ ] **Step 5: Commit calibration report**

```bash
git add js/calibration-ui.js js/app.js index.html css/styles.css tests/app.spec.js
git commit -m "feat(app): expose calibration and validation report"
```

---

### Task 7: Enforce pending migration, mobile accessibility, offline packaging, and release verification

**Files:**
- Modify: `js/app.js`
- Modify: `index.html`
- Modify: `css/styles.css`
- Modify: `sw.js`
- Modify: `scripts-generate-standalone.mjs`
- Modify: `tests/app.spec.js`
- Modify: `README.md`
- Modify: `ASSET-LICENSES.md`

**Interfaces:**
- Consumes: all previous tasks.
- Produces: no-provisional-value migration, accessible responsive app, standalone artifact, ZIP, and verified RawGitHack payload inputs.

- [ ] **Step 1: Add release-blocking E2E assertions**

```javascript
// append to tests/app.spec.js
test('release contains no provisional Spa pole claim', async ({ page }) => {
  const body = await page.locator('body').innerText();
  expect(body).not.toMatch(/1:40\.4/);
  expect(body).not.toMatch(/field-best.*uncalibrated/i);
});

test('calibration surfaces fit a 390px viewport and remain keyboard reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loadApp(page);
  const metrics = await page.evaluate(() => ({ width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.width);
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus-visible')).toBeVisible();
  await expect(page.locator('#trace-source-select')).toBeVisible();
});

test('reduced motion disables smooth playback presentation transitions', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await loadApp(page);
  const duration = await page.locator('#animated-car').evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(duration).toBe('0s');
});
```

- [ ] **Step 2: Run and verify RED where migration remains incomplete**

```bash
npm run standalone
npx playwright test tests/app.spec.js -g 'provisional|390px|reduced motion'
```

Expected: at least the source/copy scan fails before cleanup.

- [ ] **Step 3: Complete migration and package integration**

Add reduced-motion styles:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior:auto !important; animation-duration:.001ms !important; animation-iteration-count:1 !important; transition-duration:0s !important; }
}
```

Update `sw.js` cache revision and assets:

```javascript
const CACHE = 'spa-race-lab-v4-calibration';
const ASSETS = [
  './', './index.html', './css/styles.css', './dist/app.bundle.js',
  './manifest.webmanifest', './assets/icon.svg'
];
```

Add a build-time source scan to `scripts-generate-standalone.mjs`:

```javascript
const forbidden = [/1:40\.4/, /provisional field-best/i];
for (const pattern of forbidden) {
  if (pattern.test(html)) throw new Error(`standalone build contains forbidden calibration claim: ${pattern}`);
}
```

Document the distinction in `README.md`:

```markdown
## Calibration states

- **Uncalibrated educational simulation:** coupled racing line and vehicle model used for learning and fallback playback.
- **Released Spa 2026 prediction:** available only when the corner-transfer model passes all held-out release gates.
- **Historical references:** OpenF1 telemetry synchronized by lap progress; lateral line placement is illustrative.
```

- [ ] **Step 4: Run full app and artifact verification**

```bash
npm run verify
grep -R -nE '1:40\.4|provisional field-best' js index.html css README.md spa-race-lab-standalone.html && exit 1 || true
node -e "import('./js/calibration-data.js').then(({CALIBRATION_ARTIFACT}) => console.log(CALIBRATION_ARTIFACT.status))"
python -m zipfile -t /mnt/data/spa-race-lab.zip
```

Expected:

```text
all Node and Playwright tests pass
source scan prints nothing
artifact status prints pending, failed-validation, or released
Done testing of archive. No errors detected.
```

- [ ] **Step 5: Commit release migration and docs**

```bash
git add js/app.js index.html css/styles.css sw.js scripts-generate-standalone.mjs tests/app.spec.js README.md ASSET-LICENSES.md
git commit -m "feat(app): complete gated calibration integration"
```

## Plan C Completion Gate

The plan is complete when:

1. pending and failed-validation artifacts never show a pole estimate;
2. released prediction, team, historical, and analogue sources all replay through the same source contract;
3. map, chart, telemetry, corner and playback remain synchronized after seeking and source changes;
4. uncertainty, provenance and validation evidence are accessible on desktop and mobile;
5. `npm run verify` passes from a clean checkout;
6. standalone and ZIP builds contain no provisional 1:40.4 claim.
