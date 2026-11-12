#!/usr/bin/env node
// External link check over the built site. Report only: it exits 0 whatever it
// finds, because CI must not fail on someone else's outage (see check-links.mjs
// for the internal links, which do fail). The PR report lists what it found.
//
//   node scripts/check-external-links.mjs [--site _site] [--json out.json]
//
// Every <a href> to http(s) is requested once: HEAD first, then GET when a
// server refuses HEAD. 2xx and 3xx pass. 401, 403 and 429 are "blocked": the
// site turned away an automated client, which says nothing about the link.
// 404, 410, 5xx, timeouts and DNS failures are "broken".

import { readdirSync, statSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';

const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : fallback;
};
const SITE = arg('--site', '_site');
const JSON_OUT = arg('--json');
const TIMEOUT_MS = 15000;
const CONCURRENCY = 8;
// Hosts that only make sense in a browser session, or never answer bots.
const SKIP = [/^https?:\/\/localhost\b/, /^https?:\/\/127\./, /^https?:\/\/(www\.)?linkedin\.com\//];

if (!existsSync(SITE)) {
  console.error(`x ${SITE} does not exist. Run "bundle exec jekyll build" first.`);
  process.exit(1);
}

function* htmlFiles(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* htmlFiles(p);
    else if (name.endsWith('.html')) yield p;
  }
}

const decode = (s) => s.replace(/&amp;/g, '&').replace(/&#39;/g, "'").replace(/&quot;/g, '"');
const links = new Map(); // url -> pages it appears on
for (const file of htmlFiles(SITE)) {
  const page = relative(SITE, file).replace(/\\/g, '/');
  const html = readFileSync(file, 'utf8');
  for (const m of html.matchAll(/<a\b[^>]*\shref="(https?:\/\/[^"]+)"/gi)) {
    const url = decode(m[1]).split('#')[0];
    if (SKIP.some((re) => re.test(url))) continue;
    if (!links.has(url)) links.set(url, new Set());
    links.get(url).add(page);
  }
}

async function request(url, method) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method,
      redirect: 'follow',
      signal: ctrl.signal,
      headers: { 'user-agent': 'azure-sql-dev-hub-link-check', accept: 'text/html,*/*' },
    });
    res.body?.cancel?.().catch(() => {});
    return { status: res.status };
  } catch (e) {
    return { status: 0, error: e.name === 'AbortError' ? 'timeout' : (e.cause?.code || e.message) };
  } finally {
    clearTimeout(timer);
  }
}

async function check(url) {
  let r = await request(url, 'HEAD');
  if (r.status === 0 || r.status === 405 || r.status === 403 || r.status === 404 || r.status >= 500) {
    r = await request(url, 'GET');
  }
  const state = r.status >= 200 && r.status < 400 ? 'ok'
    : [401, 403, 429].includes(r.status) ? 'blocked'
    : 'broken';
  return { url, state, status: r.status, error: r.error, pages: [...links.get(url)].sort() };
}

const queue = [...links.keys()];
const results = [];
await Promise.all(Array.from({ length: CONCURRENCY }, async () => {
  while (queue.length) results.push(await check(queue.shift()));
}));
results.sort((a, b) => a.url.localeCompare(b.url));

const broken = results.filter((r) => r.state === 'broken');
const blocked = results.filter((r) => r.state === 'blocked');
const summary = { checked: results.length, broken, blocked: blocked.map(({ url, status }) => ({ url, status })) };
if (JSON_OUT) writeFileSync(JSON_OUT, JSON.stringify(summary, null, 2));

console.log(`external links: ${results.length} checked, ${broken.length} broken, ${blocked.length} blocked by the server`);
for (const r of broken) console.log(`  x ${r.url} -> ${r.status || r.error} (on ${r.pages.join(', ')})`);
