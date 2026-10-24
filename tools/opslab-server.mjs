#!/usr/bin/env node
// OpsLab class-room server (optional). Node 18+, no dependencies.
//
//   node tools/opslab-server.mjs          # http://<this-computer>:8787
//   PORT=9000 node tools/opslab-server.mjs
//
// What it does:
//   * serves opslab.html to every device on the network (students open the printed address)
//   * hosts class rooms: the professor creates a room, students join with a room code + roll number
//   * receives every student run, RE-COMPUTES it with the same simulation engine (so scores
//     cannot be faked), and gives the professor a live dashboard and CSV export
//   * includes the LLM proxy (/https/<host>/...) used by the live AI agent chat
//
// Data is kept in opslab-rooms.json next to opslab.html (set DATA_FILE to change).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {handleProxy} from './llm-proxy.mjs';

const VERSION = 'room-v1';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const HTML_FILE = path.join(HERE, '..', 'opslab.html');
const DATA_FILE = process.env.DATA_FILE || path.join(HERE, '..', 'opslab-rooms.json');
const PORT = Number(process.env.PORT) || 8787;
const MAX_RUNS_PER_TOPIC = 60;

// ---------- simulation engine, loaded from opslab.html itself ----------
function loadEngine() {
  const html = fs.readFileSync(HTML_FILE, 'utf8');
  const a = html.indexOf('/* ---------------- 1. Utilities'), b = html.indexOf('/* ---------------- 4. Charts');
  if (a < 0 || b < 0) throw new Error('Could not find the simulation engine inside opslab.html');
  const ctx = vm.createContext({performance, console});
  vm.runInContext(html.slice(a, b) + '\nglobalThis.__ops = {TOPICS, TOPIC, Agent, fmtV, campaignRound, CAMPAIGN, PERIODS};', ctx, {filename: 'opslab-engine.js'});
  return ctx.__ops;
}
const ENGINE = loadEngine();
const defaultsOf = t => Object.fromEntries(t.params.map(x => [x.id, JSON.parse(JSON.stringify(x.def))]));

// Validate a full parameter set sent by a browser. Returns {p} or {error}.
function sanitize(t, raw) {
  if (!raw || typeof raw !== 'object') return {error: 'Missing inputs'};
  const p = defaultsOf(t);
  for (const x of t.params) {
    if (!(x.id in raw)) continue;
    const v = raw[x.id];
    if (x.type === 'checkbox') p[x.id] = v === true;
    else if (x.type === 'text') p[x.id] = String(v).slice(0, 100);
    else if (x.type === 'select') { const o = x.options.find(o => String(o[0]) === String(v)); if (!o) return {error: `Invalid ${x.id}`}; p[x.id] = o[0]; }
    else if (x.type === 'jobs') {
      if (!Array.isArray(v) || v.length !== p.jobs.length) return {error: 'Invalid jobs'};
      for (let i = 0; i < v.length; i++) {
        const j = v[i]; if (!j || j.id !== p.jobs[i].id) return {error: 'Invalid jobs'};
        const pp = Math.round(+j.p), dd = Math.round(+j.d);
        if (!(pp >= 1 && pp <= 30 && dd >= 1 && dd <= 120)) return {error: 'Invalid jobs'};
        p.jobs[i] = {id: j.id, p: pp, d: dd};
      }
    } else {
      const n = +v; if (!isFinite(n) || n < x.min - 1e-9 || n > x.max + 1e-9) return {error: `${x.id} out of range`};
      p[x.id] = n;
    }
  }
  if (t.validate) { const e = t.validate(p); if (e) return {error: e}; }
  return {p};
}
// A campaign round is fair when its scenario matches that round's official conditions.
function fairRound(t, p, rd) {
  if (!rd || !ENGINE.CAMPAIGN[t.id] || !ENGINE.PERIODS[rd.period]) return false;
  const k = Math.round(+rd.k), n = Math.max(...ENGINE.PERIODS[rd.period].rounds);
  if (!(k >= 0 && k < n)) return false;
  const sc = ENGINE.campaignRound(t, rd.period, k).scenario;
  return t.params.filter(x => x.role === 'scenario').every(x => JSON.stringify(p[x.id]) === JSON.stringify(sc[x.id]));
}
const sameScenario = (t, p) => { const d = defaultsOf(t); return t.params.filter(x => x.role === 'scenario').every(x => JSON.stringify(p[x.id]) === JSON.stringify(d[x.id])); };

// Stable labels for the agent's diagnosis codes, so the dashboard can count the same mistake across students.
const ISSUE_LABELS = {
  bottleneck: 'Bottleneck not relieved', overcap: 'Excess capacity at a non-bottleneck', balance: 'Poorly balanced line', loss: 'Shift loses money',
  lowrop: 'Reorder point below lead-time demand', lowss: 'Safety stock too thin', highrop: 'Excess safety stock', smallq: 'Orders too small', bigq: 'Orders too large', shortshare: 'Stockouts dominate cost',
  late: 'Jobs finish late', fcfs: 'Used FCFS sequencing', lpt: 'Used LPT sequencing', flow: 'Flow time above SPT', swap: 'Long job blocks an urgent job',
  escape: 'Defects reach customers', noprev: 'No prevention spend', overinspect: 'Inspection costs more than it saves', appraisal: 'Appraisal-heavy quality system', overprev: 'Prevention past its useful limit',
  unstable: 'Unstable queue (too few servers)', sl: 'Service-level target missed', highutil: 'Servers run too hot', overstaff: 'Overstaffed', waitcost: 'Waiting cost exceeds wages',
  stockout: 'Stockouts during the disruption', nocont: 'No contingency plan', slow: 'Contingency response too slow', capacity: 'Backup capacity too small', premium: 'Dual-sourcing premium too large', overbuffer: 'Buffer larger than needed', overhang: 'Post-disruption inventory overhang',
  overload: 'Batches too small: capacity below demand', bigbatch: 'Large batches inflate lead time', queue: 'Queueing at the bottleneck dominates', setup: 'Long setups force big batches', transport: 'Transport and admin delays', pce: 'Very low process cycle efficiency'
};
const IGNORE_ISSUES = new Set(['shift', 'timestudy']); // informational only

// ---------- storage ----------
let DB = {rooms: {}};
try { DB = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); } catch (e) {}
let saveTimer = null;
function save() { clearTimeout(saveTimer); saveTimer = setTimeout(() => { fs.writeFile(DATA_FILE, JSON.stringify(DB), () => {}); }, 300); }
const sha = s => crypto.createHash('sha256').update(String(s)).digest('hex');
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function newCode() { let c; do { c = Array.from(crypto.randomBytes(6), b => CODE_CHARS[b % CODE_CHARS.length]).join(''); } while (DB.rooms[c]); return c; }
const normRoll = r => String(r || '').trim().toUpperCase().replace(/\s+/g, '');
const ROLL_RE = /^[A-Z0-9][A-Z0-9/_.-]{1,29}$/;

// ---------- scoring ----------
function topicSummary(t, runs) {
  const fair = runs.filter(r => r.fair);
  const best = fair.reduce((m, r) => Math.max(m, r.eff), 0);
  const bestRun = fair.find(r => r.eff === best);
  return {runs: runs.length, fairRuns: fair.length, best: fair.length ? best : null, bestValue: bestRun ? bestRun.valueText : null,
    first: fair.length ? fair[0].eff : null, last: runs.length ? runs[runs.length - 1].eff : null};
}
function studentScore(s) { return ENGINE.TOPICS.reduce((sum, t) => sum + (topicSummary(t, s.runs[t.id] || []).best || 0), 0); }
function ranking(room) {
  return Object.values(room.students).map(s => ({roll: s.roll, score: studentScore(s)})).sort((a, b) => b.score - a.score || a.roll.localeCompare(b.roll));
}
function dashboard(room) {
  const students = Object.values(room.students).map(s => {
    const perTopic = {}; let runs = 0;
    ENGINE.TOPICS.forEach(t => { const sm = topicSummary(t, s.runs[t.id] || []); perTopic[t.id] = sm; runs += sm.runs; });
    return {roll: s.roll, name: s.name, joined: s.joined, lastSeen: s.lastSeen, runs, score: studentScore(s), perTopic};
  }).sort((a, b) => b.score - a.score || a.roll.localeCompare(b.roll));
  students.forEach((s, i) => { s.rank = i + 1; });
  const topicStats = ENGINE.TOPICS.map(t => {
    const sums = students.map(s => s.perTopic[t.id]).filter(x => x.best !== null);
    const issues = {};
    Object.values(room.students).forEach(s => {
      const seen = new Set(); (s.runs[t.id] || []).forEach(r => (r.issues || []).forEach(i => seen.add(i)));
      seen.forEach(i => { issues[i] = (issues[i] || 0) + 1; });
    });
    return {id: t.id, name: t.name, attempted: sums.length, avgBest: sums.length ? sums.reduce((a, x) => a + x.best, 0) / sums.length : null,
      avgFirst: sums.length ? sums.reduce((a, x) => a + (x.first || 0), 0) / sums.length : null,
      topIssues: Object.entries(issues).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([code, students]) => ({title: ISSUE_LABELS[code] || code, students}))};
  });
  const missing = room.roster ? room.roster.filter(r => !room.students[r]) : [];
  return {room: {code: room.code, name: room.name, closed: !!room.closed, created: room.created, roster: room.roster ? room.roster.length : null, missing},
    topics: ENGINE.TOPICS.map(t => ({id: t.id, name: t.name, short: t.short})), students, topicStats, generated: Date.now()};
}
function csv(room) {
  const d = dashboard(room), head = ['Rank', 'Roll', 'Name', `Score (of ${d.topics.length})`, 'Runs', ...d.topics.flatMap(t => [`${t.short} best %`, `${t.short} runs`]), 'Last seen'];
  const q = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const rows = d.students.map(s => [s.rank, s.roll, s.name, s.score.toFixed(3), s.runs, ...d.topics.flatMap(t => [s.perTopic[t.id].best === null ? '' : (s.perTopic[t.id].best * 100).toFixed(1), s.perTopic[t.id].runs]), new Date(s.lastSeen).toISOString()]);
  (d.room.missing || []).forEach(r => rows.push(['', r, '(not joined)', 0, 0, ...d.topics.flatMap(() => ['', 0]), '']));
  return [head, ...rows].map(r => r.map(q).join(',')).join('\r\n');
}

// ---------- HTTP ----------
const CORS = {'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET, POST, OPTIONS', 'access-control-allow-headers': 'content-type, x-admin-key'};
const send = (res, status, obj) => { res.writeHead(status, {...CORS, 'content-type': 'application/json', 'cache-control': 'no-store'}); res.end(JSON.stringify(obj)); };
async function readBody(req) {
  const chunks = []; let n = 0;
  for await (const c of req) { n += c.length; if (n > 200_000) throw new Error('Request too large'); chunks.push(c); }
  try { return JSON.parse(Buffer.concat(chunks).toString() || '{}'); } catch (e) { throw new Error('Invalid JSON'); }
}
function admin(req, room, url) { const k = req.headers['x-admin-key'] || url.searchParams.get('key'); return k && sha(k) === room.adminHash; }

async function api(req, res, url) {
  const parts = url.pathname.split('/').filter(Boolean); // api, rooms, CODE, action
  if (parts[1] === 'health') return send(res, 200, {ok: true, version: VERSION, studentUrls: lanUrls()});
  if (parts[1] !== 'rooms') return send(res, 404, {error: 'Not found'});
  if (parts.length === 2 && req.method === 'POST') {
    const b = await readBody(req);
    const name = String(b.name || 'OpsLab class').trim().slice(0, 80) || 'OpsLab class';
    let roster = null;
    if (b.roster && String(b.roster).trim()) {
      roster = [...new Set(String(b.roster).split(/[\s,;]+/).map(normRoll).filter(Boolean))];
      const bad = roster.filter(r => !ROLL_RE.test(r));
      if (bad.length) return send(res, 400, {error: `Invalid roll numbers in class list: ${bad.slice(0, 5).join(', ')}`});
    }
    const code = newCode(), adminKey = crypto.randomBytes(12).toString('hex');
    DB.rooms[code] = {code, name, adminHash: sha(adminKey), created: Date.now(), closed: false, roster, students: {}};
    save(); console.log(`${new Date().toLocaleTimeString()}  room ${code} created: ${name}${roster ? ` (${roster.length} on class list)` : ''}`);
    return send(res, 200, {code, adminKey, name});
  }
  const room = DB.rooms[String(parts[2] || '').toUpperCase()];
  if (!room) return send(res, 404, {error: 'Room not found. Check the room code.'});
  const action = parts[3] || '';
  if (!action && req.method === 'GET') return send(res, 200, {code: room.code, name: room.name, closed: !!room.closed, classList: !!room.roster, students: Object.keys(room.students).length});

  if (action === 'join' && req.method === 'POST') {
    const b = await readBody(req), roll = normRoll(b.roll), name = String(b.name || '').trim().slice(0, 60);
    if (!ROLL_RE.test(roll)) return send(res, 400, {error: 'Enter a valid roll number (letters, digits, / _ . -).'});
    const s = room.students[roll];
    if (s) {
      if (s.tokenHash && b.token && sha(b.token) === s.tokenHash) { s.lastSeen = Date.now(); if (name) s.name = name; save(); return send(res, 200, {ok: true, token: b.token, room: room.name, roll, rejoined: true}); }
      if (s.tokenHash) return send(res, 409, {error: 'This roll number has already joined from another device. Ask your professor to reset it.'});
      const token = crypto.randomBytes(16).toString('hex'); s.tokenHash = sha(token); s.lastSeen = Date.now(); if (name) s.name = name; save();
      return send(res, 200, {ok: true, token, room: room.name, roll, rejoined: true});
    }
    if (room.closed) return send(res, 403, {error: 'This room is closed.'});
    if (room.roster && !room.roster.includes(roll)) return send(res, 403, {error: 'Roll number not on the class list for this room. Check it, or ask your professor.'});
    const token = crypto.randomBytes(16).toString('hex');
    room.students[roll] = {roll, name, tokenHash: sha(token), joined: Date.now(), lastSeen: Date.now(), runs: {}};
    save(); console.log(`${new Date().toLocaleTimeString()}  ${roll} joined ${room.code}`);
    return send(res, 200, {ok: true, token, room: room.name, roll});
  }

  if ((action === 'runs' || action === 'me') && (req.method === 'POST' || req.method === 'GET')) {
    const b = req.method === 'POST' ? await readBody(req) : {roll: url.searchParams.get('roll'), token: url.searchParams.get('token')};
    const s = room.students[normRoll(b.roll)];
    if (!s || !s.tokenHash || !b.token || sha(b.token) !== s.tokenHash) return send(res, 401, {error: 'Not joined to this room on this device. Join again.'});
    if (action === 'runs') {
      if (room.closed) return send(res, 403, {error: 'This room is closed. New runs are not recorded.'});
      const t = ENGINE.TOPIC[b.topic]; if (!t) return send(res, 400, {error: 'Unknown topic'});
      const v = sanitize(t, b.p); if (v.error) return send(res, 400, {error: v.error});
      const r = t.simulate(v.p), a = ENGINE.Agent.analyze(t, v.p, r), k = t.kpis.find(k => k.key === t.objective.key);
      const list = s.runs[t.id] = s.runs[t.id] || [];
      const rdOk = fairRound(t, v.p, b.round), rdLabel = rdOk ? (b.round.period === 'quarter' ? `Q${b.round.k % 4 + 1} Y${Math.floor(b.round.k / 4) + 1}` : `Year ${+b.round.k + 1}`) : '';
      list.push({n: +b.n || list.length + 1, at: Date.now(), round: rdLabel || undefined, decisions: (rdLabel ? rdLabel + ': ' : '') + t.describe(v.p), value: r[k.key], valueText: ENGINE.fmtV(k.fmt, r[k.key]),
        eff: a.eff, fair: sameScenario(t, v.p) || rdOk, issues: a.issues.filter(i => i.sev !== 'ok' && !IGNORE_ISSUES.has(i.code)).map(i => i.code)});
      if (list.length > MAX_RUNS_PER_TOPIC) list.splice(0, list.length - MAX_RUNS_PER_TOPIC);
      s.lastSeen = Date.now(); save();
    } else s.lastSeen = Date.now();
    const rk = ranking(room), rank = rk.findIndex(x => x.roll === s.roll) + 1;
    const perTopic = {}; ENGINE.TOPICS.forEach(t => { perTopic[t.id] = topicSummary(t, s.runs[t.id] || []); });
    const last = action === 'runs' ? s.runs[b.topic][s.runs[b.topic].length - 1] : null;
    return send(res, 200, {ok: true, rank, of: rk.length, score: studentScore(s), perTopic, recorded: last ? {eff: last.eff, valueText: last.valueText, fair: last.fair} : null});
  }

  if (!admin(req, room, url)) return send(res, 401, {error: 'Professor key required.'});
  if (action === 'dashboard' && req.method === 'GET') return send(res, 200, dashboard(room));
  if (action === 'export.csv' && req.method === 'GET') {
    res.writeHead(200, {...CORS, 'content-type': 'text/csv; charset=utf-8', 'content-disposition': `attachment; filename="opslab-${room.code}.csv"`});
    return res.end('﻿' + csv(room));
  }
  if (action === 'reset-student' && req.method === 'POST') {
    const b = await readBody(req), s = room.students[normRoll(b.roll)];
    if (!s) return send(res, 404, {error: 'No such student in this room.'});
    if (b.remove) delete room.students[s.roll]; else s.tokenHash = null;
    save(); return send(res, 200, {ok: true});
  }
  if (action === 'close' && req.method === 'POST') { const b = await readBody(req); room.closed = !!b.closed; save(); return send(res, 200, {ok: true, closed: room.closed}); }
  return send(res, 404, {error: 'Not found'});
}

const lanUrls = () => Object.values(os.networkInterfaces()).flat().filter(i => i && i.family === 'IPv4' && !i.internal).map(i => `http://${i.address}:${PORT}`);
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://x');
    if (url.pathname.startsWith('/api/')) {
      if (req.method === 'OPTIONS') { res.writeHead(204, CORS); return res.end(); }
      return await api(req, res, url);
    }
    if (await handleProxy(req, res)) return;
    if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/opslab.html')) {
      res.writeHead(200, {'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store'});
      return res.end(fs.readFileSync(HTML_FILE));
    }
    res.writeHead(404, {'content-type': 'text/plain'}); res.end('Not found');
  } catch (e) { send(res, 400, {error: e.message}); }
});
server.on('error', e => {
  if (e.code === 'EADDRINUSE') console.error(`Port ${PORT} is already in use. Is the OpsLab server (or llm-proxy) already running in another window? Close it, or start this one on another port, e.g. PORT=8788 (Windows PowerShell: $env:PORT=8788; node tools/opslab-server.mjs).`);
  else console.error('Server error: ' + e.message);
  process.exit(1);
});
server.listen(PORT, '0.0.0.0', () => {
  const ips = Object.values(os.networkInterfaces()).flat().filter(i => i && i.family === 'IPv4' && !i.internal).map(i => i.address);
  console.log(`OpsLab class-room server ${VERSION} (includes LLM proxy)`);
  console.log(`  On this computer:  http://localhost:${PORT}`);
  ips.forEach(ip => console.log(`  Students open:     http://${ip}:${PORT}`));
  if (!ips.length) console.log('  (No network address found: connect to Wi-Fi or a hotspot.)');
  console.log(`  Data file: ${DATA_FILE}`);
});
