import { writeFile } from 'node:fs/promises';

const API = 'https://api.openf1.org/v1';
const DRIVERS = [
  { number: 4, acronym: 'NOR', name: 'Lando Norris', team: 'McLaren', colour: '#ff8700' },
  { number: 81, acronym: 'PIA', name: 'Oscar Piastri', team: 'McLaren', colour: '#ffd1a3' },
  { number: 1, acronym: 'VER', name: 'Max Verstappen', team: 'Red Bull Racing', colour: '#3671c6' }
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
const sessions = await request('sessions', { year: 2025, country_name: 'Belgium', session_name: 'Qualifying' });
const session = sessions.filter((row) => row.session_name === 'Qualifying').sort((a, b) => Date.parse(b.date_start) - Date.parse(a.date_start))[0];
if (!session?.session_key) throw new Error('2025 Belgian qualifying session not found');
const traces = [];
for (const driver of DRIVERS) {
  const laps = await request('laps', { session_key: session.session_key, driver_number: driver.number });
  const lap = laps.filter((row) => Number.isFinite(row.lap_duration) && row.lap_duration > 70 && row.lap_duration < 160 && !row.is_pit_out_lap && row.date_start).sort((a, b) => a.lap_duration - b.lap_duration)[0];
  if (!lap) throw new Error(`No complete lap for ${driver.acronym}`);
  const startMs = Date.parse(lap.date_start);
  const endMs = startMs + lap.lap_duration * 1000 + 700;
  const range = { session_key: session.session_key, driver_number: driver.number, 'date>=': new Date(startMs - 500).toISOString(), 'date<=': new Date(endMs).toISOString() };
  const car = await request('car_data', range);
  const location = await request('location', range);
  const trace = couple(car, location, startMs, lap.lap_duration);
  if (trace.length < 8) throw new Error(`Incomplete trace for ${driver.acronym}`);
  traces.push({
    id: `2025-${driver.acronym.toLowerCase()}-q`, driver, sessionKey: session.session_key, meetingKey: session.meeting_key,
    year: 2025, sessionName: 'Qualifying', lapNumber: lap.lap_number, lapTimeSeconds: lap.lap_duration, trace,
    timingTable: trace.map((row) => ({ progress: row.progress, time: clamp(row.elapsedSeconds / lap.lap_duration, 0, 1) })),
    spatialRoute: 'reference',
    source: { name: 'OpenF1', url: 'https://openf1.org/', license: 'CC BY-NC-SA 4.0', sampling: 'about 3.7 Hz' },
    limitations: 'OpenF1 location is approximate and does not preserve left-right placement on the road.'
  });
}
const generatedAt = new Date().toISOString();
const content = `// Generated from OpenF1 historical data by scripts-fetch-openf1.mjs.\n// Source license: CC BY-NC-SA 4.0. Do not edit by hand.\nexport const BUNDLED_SPA_REFERENCES = Object.freeze(${JSON.stringify(traces)});\nexport const BUNDLED_SPA_REFERENCE_META = Object.freeze(${JSON.stringify({ generatedAt, source: 'OpenF1', session: '2025 Belgian Grand Prix qualifying', sessionKey: session.session_key })});\n`;
await writeFile(new URL('./js/reference-data.js', import.meta.url), content, 'utf8');
console.log(`Wrote ${traces.length} traces for session ${session.session_key}`);

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
