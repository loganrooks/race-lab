import { writeFile } from 'node:fs/promises';

const API = 'https://api.openf1.org/v1';
const SPECS = [
  { year: 2025, countryName: 'Belgium', sessionName: 'Qualifying', shortLabel: '2025 Q', limit: 4 },
  { year: 2025, countryName: 'Belgium', sessionName: 'Sprint Qualifying', shortLabel: '2025 SQ', limit: 3 }
];
let lastRequestAt = 0;
async function request(endpoint, params) {
  const wait = Math.max(0, 1100 - (Date.now() - lastRequestAt));
  if (wait) await new Promise((resolve) => setTimeout(resolve, wait));
  lastRequestAt = Date.now();
  const query = Object.entries(params).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&');
  const response = await fetch(`${API}/${endpoint}?${query}`, { headers: { accept: 'application/json' } });
  if (!response.ok) throw new Error(`${endpoint} failed (${response.status})`);
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error(`${endpoint} returned non-array JSON`);
  return data;
}
const traces = [];
const sessionKeys = [];
for (const spec of SPECS) {
  const sessions = await request('sessions', { year: spec.year, country_name: spec.countryName, session_name: spec.sessionName });
  const session = sessions.filter((row) => row.session_name === spec.sessionName).sort((a, b) => Date.parse(b.date_start) - Date.parse(a.date_start))[0];
  if (!session?.session_key) throw new Error(`${spec.sessionName} session not found`);
  sessionKeys.push(session.session_key);
  const [laps, driverRows] = await Promise.all([
    request('laps', { session_key: session.session_key }),
    request('drivers', { session_key: session.session_key })
  ]);
  const driverMap = new Map(driverRows.map((row) => [Number(row.driver_number), driverFromRow(row)]));
  const fastestByDriver = new Map();
  for (const lap of laps) {
    if (!validLap(lap)) continue;
    const number = Number(lap.driver_number);
    const current = fastestByDriver.get(number);
    if (!current || lap.lap_duration < current.lap_duration) fastestByDriver.set(number, lap);
  }
  const selected = [...fastestByDriver.values()].sort((a, b) => a.lap_duration - b.lap_duration).slice(0, spec.limit);
  for (const lap of selected) {
    const driver = driverMap.get(Number(lap.driver_number)) || genericDriver(lap.driver_number);
    const startMs = Date.parse(lap.date_start);
    const endMs = startMs + lap.lap_duration * 1000;
    const range = { session_key: session.session_key, driver_number: driver.number, 'date>=': new Date(startMs - 1200).toISOString(), 'date<=': new Date(endMs + 1600).toISOString() };
    const carQuery = url('car_data', range);
    const locationQuery = url('location', range);
    const [car, location] = await Promise.all([requestUrl(carQuery), requestUrl(locationQuery)]);
    const trace = couple(car, location, startMs, lap.lap_duration);
    if (trace.length < 8) throw new Error(`Incomplete trace for ${driver.acronym} ${spec.shortLabel}`);
    const abbreviation = spec.sessionName === 'Sprint Qualifying' ? 'sq' : 'q';
    traces.push({
      id: `${spec.year}-${abbreviation}-${driver.acronym.toLowerCase()}-l${lap.lap_number}`,
      driver, sessionKey: session.session_key, meetingKey: session.meeting_key, year: spec.year,
      sessionName: spec.sessionName, sessionLabel: spec.shortLabel, lapNumber: lap.lap_number,
      lapTimeSeconds: lap.lap_duration, sectorTimes: [lap.duration_sector_1, lap.duration_sector_2, lap.duration_sector_3],
      speedTrapKph: lap.st_speed ?? null, trace,
      timingTable: trace.map((row) => ({ progress: row.progress, time: clamp(row.elapsedSeconds / lap.lap_duration, 0, 1) })),
      source: { name: 'OpenF1', url: 'https://openf1.org/', license: 'CC BY-NC-SA 4.0', sampling: 'about 3.7 Hz', sessionKey: session.session_key, carDataQuery: carQuery, locationQuery },
      channels: ['speed', 'throttle', 'brake', 'gear', 'rpm', 'drs', 'time'], spatialRoute: 'reference-raceline', spatialConfidence: 'progress-only',
      sampleCount: trace.length, rawSampleCount: { carData: car.length, location: location.length },
      limitations: 'OpenF1 location is approximate and does not preserve left-right placement on the road. Replay position is synchronized to the validated TUM reference raceline.'
    });
  }
}
traces.sort((a, b) => a.sessionName.localeCompare(b.sessionName) || a.lapTimeSeconds - b.lapTimeSeconds);
const generatedAt = new Date().toISOString();
const content = `// Generated from OpenF1 historical data by scripts-fetch-openf1.mjs.\n// Source license: CC BY-NC-SA 4.0. Do not edit by hand.\nexport const BUNDLED_SPA_REFERENCES = Object.freeze(${JSON.stringify(traces)});\nexport const BUNDLED_SPA_REFERENCE_META = Object.freeze(${JSON.stringify({ generatedAt, source: 'OpenF1', session: '2025 Belgian Grand Prix qualifying and sprint qualifying', sessionKeys })});\n`;
await writeFile(new URL('./js/reference-data.js', import.meta.url), content, 'utf8');
console.log(`Wrote ${traces.length} traces from sessions ${sessionKeys.join(', ')}`);

async function requestUrl(target) {
  const wait = Math.max(0, 1100 - (Date.now() - lastRequestAt));
  if (wait) await new Promise((resolve) => setTimeout(resolve, wait));
  lastRequestAt = Date.now();
  const response = await fetch(target, { headers: { accept: 'application/json' } });
  if (!response.ok) throw new Error(`OpenF1 request failed (${response.status})`);
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error('OpenF1 returned non-array JSON');
  return data;
}
function url(endpoint, params) { return `${API}/${endpoint}?${Object.entries(params).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&')}`; }
function validLap(lap) { return Number.isFinite(lap?.lap_duration) && lap.lap_duration > 70 && lap.lap_duration < 180 && !lap.is_pit_out_lap && Boolean(lap.date_start); }
function driverFromRow(row) {
  const colour = String(row.team_colour || '').replace(/^#/, '');
  return { number: Number(row.driver_number), acronym: row.name_acronym || String(row.driver_number), name: titleCase(row.full_name || row.broadcast_name || String(row.driver_number)), team: row.team_name || 'Unknown team', colour: colour ? `#${colour}` : '#d8d4cc' };
}
function genericDriver(number) { return { number: Number(number), acronym: String(number), name: `Car ${number}`, team: 'Unknown team', colour: '#d8d4cc' }; }
function titleCase(value) { return String(value).toLowerCase().replace(/\b\p{L}/gu, (letter) => letter.toUpperCase()); }
function couple(carRows, locationRows, startMs, duration) {
  const locations = locationProgress(locationRows);
  let rows = carRows.filter((row) => row.date && Number.isFinite(row.speed)).sort((a, b) => Date.parse(a.date) - Date.parse(b.date)).map((row) => {
    const timestamp = Date.parse(row.date);
    return { progress: locations.length > 1 ? locationAt(locations, timestamp) : clamp((timestamp - startMs) / (duration * 1000), 0, 1), elapsedSeconds: clamp((timestamp - startMs) / 1000, 0, duration), speed: Number(row.speed) || 0, throttle: clamp(Number(row.throttle) || 0, 0, 100), brake: clamp(Number(row.brake) || 0, 0, 100), gear: clamp(Math.round(Number(row.n_gear) || 1), 0, 8), rpm: Math.max(0, Number(row.rpm) || 0), drs: Number(row.drs) || 0, lateralG: 0, longitudinalG: 0, ersPowerKw: 0, batteryPct: 0, aeroMode: Number(row.drs) >= 10 ? 'drs-open' : 'legacy-closed' };
  });
  let previous = 0;
  rows = rows.map((row, index) => ({ ...row, progress: previous = index ? Math.max(previous, row.progress) : Math.max(0, row.progress) }));
  if (!rows.length) return [];
  const first = rows[0].progress;
  const span = Math.max(rows.at(-1).progress - first, .0001);
  rows = rows.map((row) => ({ ...row, progress: clamp((row.progress - first) / span, 0, 1) }));
  rows[0] = { ...rows[0], progress: 0, elapsedSeconds: 0 };
  rows[rows.length - 1] = { ...rows.at(-1), progress: 1, elapsedSeconds: duration };
  if (rows.length <= 420) return rows;
  return Array.from({ length: 420 }, (_, index) => rows[Math.round(index * (rows.length - 1) / 419)]);
}
function locationProgress(rows) {
  const sorted = rows.filter((row) => Number.isFinite(row.x) && Number.isFinite(row.y) && row.date).sort((a, b) => Date.parse(a.date) - Date.parse(b.date));
  if (sorted.length < 2) return [];
  const segments = sorted.slice(1).map((row, index) => Math.hypot(row.x - sorted[index].x, row.y - sorted[index].y));
  const positives = segments.filter((value) => value > 0).sort((a, b) => a - b);
  const cap = (positives[Math.floor(positives.length / 2)] || 1) * 5;
  let distance = 0;
  const result = sorted.map((row, index) => { if (index) distance += Math.min(segments[index - 1], cap); return { timestamp: Date.parse(row.date), distance }; });
  const total = distance || 1;
  return result.map((row, index) => ({ ...row, progress: index === result.length - 1 ? 1 : row.distance / total }));
}
function locationAt(rows, timestamp) {
  if (timestamp <= rows[0].timestamp) return 0;
  if (timestamp >= rows.at(-1).timestamp) return 1;
  let low = 0, high = rows.length - 1;
  while (low + 1 < high) { const middle = Math.floor((low + high) / 2); if (rows[middle].timestamp < timestamp) low = middle; else high = middle; }
  const a = rows[low], b = rows[high];
  return a.progress + (b.progress - a.progress) * ((timestamp - a.timestamp) / Math.max(b.timestamp - a.timestamp, 1));
}
function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
