#!/usr/bin/env node
// OpsLab local LLM proxy (optional).
// Some providers (e.g. NVIDIA NIM at integrate.api.nvidia.com) block direct calls from a
// web page (CORS). This tiny proxy runs on your own computer, forwards OpsLab's requests
// to the provider, and adds the CORS headers the browser needs. No dependencies; Node 18+.
//
//   node tools/llm-proxy.mjs            # listens on http://localhost:8787
//   PORT=9000 node tools/llm-proxy.mjs
//   EXTRA_HOSTS=my-nim.example.com node tools/llm-proxy.mjs   # allow another host
//
// OpsLab calls  http://localhost:8787/https/<host>/<path>  ->  https://<host>/<path>
// Only hosts in the allowlist are forwarded, and it listens on 127.0.0.1 only.
import http from 'node:http';

const PORT = Number(process.env.PORT) || 8787;
const ALLOWED = new Set([
  'integrate.api.nvidia.com', 'api.openai.com', 'api.groq.com', 'openrouter.ai',
  'generativelanguage.googleapis.com', 'api.anthropic.com', 'api.mistral.ai',
  'api.together.xyz', 'api.deepseek.com', 'api.fireworks.ai', 'localhost:11434', '127.0.0.1:11434',
  ...(process.env.EXTRA_HOSTS || '').split(',').map(s => s.trim()).filter(Boolean)
]);
const FORWARD_HEADERS = ['content-type', 'authorization', 'x-api-key', 'anthropic-version', 'anthropic-beta', 'http-referer', 'x-title', 'accept'];
const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET, POST, OPTIONS',
  'access-control-allow-headers': FORWARD_HEADERS.join(', ') + ', anthropic-dangerous-direct-browser-access',
  'access-control-max-age': '600'
};

http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') { res.writeHead(204, cors); return res.end(); }
  const m = req.url.match(/^\/(https?)\/([^/]+)(\/.*)$/);
  if (!['GET', 'POST'].includes(req.method) || !m) { res.writeHead(404, {...cors, 'content-type': 'application/json'}); return res.end(JSON.stringify({error: {message: 'Use GET or POST /https/<host>/<path>'}})); }
  const [, scheme, host, path] = m;
  if (!ALLOWED.has(host)) { res.writeHead(403, {...cors, 'content-type': 'application/json'}); return res.end(JSON.stringify({error: {message: `Host ${host} is not in the proxy allowlist. Start the proxy with EXTRA_HOSTS=${host}`}})); }
  const chunks = []; for await (const c of req) chunks.push(c);
  const headers = {}; for (const h of FORWARD_HEADERS) if (req.headers[h]) headers[h] = req.headers[h];
  try {
    const up = await fetch(`${scheme}://${host}${path}`, req.method === 'GET' ? {method: 'GET', headers} : {method: 'POST', headers, body: Buffer.concat(chunks)});
    const body = Buffer.from(await up.arrayBuffer());
    res.writeHead(up.status, {...cors, 'content-type': up.headers.get('content-type') || 'application/json'});
    res.end(body);
    console.log(`${new Date().toLocaleTimeString()}  ${up.status}  ${host}${path}`);
  } catch (e) {
    res.writeHead(502, {...cors, 'content-type': 'application/json'});
    res.end(JSON.stringify({error: {message: `Proxy could not reach ${host}: ${e.message}`}}));
  }
}).listen(PORT, '127.0.0.1', () => console.log(`OpsLab LLM proxy on http://localhost:${PORT}  (allowed: ${[...ALLOWED].join(', ')})`));
