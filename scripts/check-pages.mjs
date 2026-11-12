#!/usr/bin/env node
// Page checks over the built site, with an agent-readiness score out of 100.
// Runs after `jekyll build` and the agent-files generator, on what will deploy.
//
// The checklist follows the public agent-readiness scanners (is-agentic.com,
// open-agent-readiness, Cloudflare's isitagentready.com) for everything this
// site controls from its own files. Those scanners grade a whole host, and this
// site lives on a subpath of microsoft.github.io, so they cannot score it; this
// does, offline, and the same way every time.
//
//   node scripts/check-pages.mjs [--site _site] [--json out.json] [--baseline base.json]
//
// Errors fail the run. Warnings only cost points. With --baseline (this
// script's JSON from the base branch), the run also fails if the score drops.

import { readdirSync, statSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';

const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : fallback;
};
const SITE = arg('--site', '_site');
const JSON_OUT = arg('--json');
const BASELINE = arg('--baseline');

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
const read = (p) => (existsSync(join(SITE, p)) ? readFileSync(join(SITE, p), 'utf8') : null);
const attr = (tag, name) => {
  const m = new RegExp(`\\s${name}\\s*=\\s*("([^"]*)"|'([^']*)')`, 'i').exec(tag);
  return m ? (m[2] ?? m[3]) : null;
};
const tags = (html, name) => html.match(new RegExp(`<${name}\\b[^>]*>`, 'gi')) || [];
const meta = (html, key) => {
  for (const t of tags(html, 'meta')) {
    if (attr(t, 'name') === key || attr(t, 'property') === key) return attr(t, 'content');
  }
  return null;
};
const link = (html, rel, type) =>
  tags(html, 'link').find((t) => attr(t, 'rel') === rel && (!type || attr(t, 'type') === type));

// Text an agent sees without running scripts: no script, style, svg or template
// bodies, no tags, entities folded, whitespace collapsed.
function visibleText(html) {
  const body = (/<body\b[^>]*>([\s\S]*)<\/body>/i.exec(html) || [, html])[1];
  return body
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<(script|style|svg|template|noscript)\b[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;|&#160;/g, ' ')
    .replace(/&[a-z]+;|&#\d+;/gi, 'x')
    .replace(/\s+/g, ' ')
    .trim();
}

// Site-level checks: [id, label, points, pass, detail]. A failing check marked
// as an error fails the run as well as costing its points.
const site = [];
const errors = [];
const siteCheck = (id, label, points, pass, detail, isError = false) => {
  site.push({ id, label, points, earned: pass ? points : 0, pass, detail });
  if (!pass && isError) errors.push(`${label}: ${detail}`);
};

const llms = read('llms.txt');
siteCheck('llms-txt', 'llms.txt', 10,
  !!llms && /^# \S/m.test(llms) && /\]\(https?:\/\//.test(llms),
  llms ? 'needs an H1 and at least one absolute link' : 'missing', !llms);
siteCheck('llms-full', 'llms-full.txt', 5, !!read('llms-full.txt'), 'missing');
const sitemap = read('sitemap.xml');
siteCheck('sitemap', 'Sitemap', 5, !!sitemap && /<loc>/.test(sitemap), sitemap ? 'no <loc> entries' : 'missing');
siteCheck('robots', 'robots.txt', 5, !!read('robots.txt'), 'missing');
const notFound = read('404.html');
siteCheck('404', 'Helpful 404 page', 5,
  !!notFound && /<a\b[^>]*href=/i.test(notFound) && visibleText(notFound).length >= 40,
  notFound ? 'needs a sentence and a link back' : 'missing 404.html');

// Page-level checks, each worth its points times the share of pages passing.
const PAGE_CHECKS = [
  ['lang', 'html lang', 5, true],
  ['title', 'Title', 5, true],
  ['description', 'Meta description, 50 to 320 characters', 5],
  ['canonical', 'Canonical link', 5],
  ['og', 'Open Graph tags', 5],
  ['json-ld', 'JSON-LD structured data', 10],
  ['h1', 'Exactly one h1', 5],
  ['headings', 'Heading levels in order', 5],
  ['text', '500+ characters of text without JavaScript', 10],
  ['alt', 'Images have alt text', 5],
  ['twin', 'Markdown twin linked and present', 10],
  ['no-refresh', 'No meta refresh redirect', 0, true],
];
const pages = [];
for (const file of htmlFiles(SITE)) {
  const path = relative(SITE, file).replace(/\\/g, '/');
  if (path === '404.html') continue;
  const html = readFileSync(file, 'utf8');
  const fails = {};
  const fail = (id, detail) => (fails[id] = detail);

  if (!attr(tags(html, 'html')[0] || '', 'lang')) fail('lang', 'no lang on <html>');
  const title = (/<title>([\s\S]*?)<\/title>/i.exec(html) || [])[1];
  if (!title || !title.trim()) fail('title', 'empty or missing <title>');
  const desc = meta(html, 'description');
  if (!desc || desc.length < 50 || desc.length > 320) fail('description', desc ? `${desc.length} characters` : 'missing');
  if (!link(html, 'canonical')) fail('canonical', 'no <link rel="canonical">');
  const og = ['og:title', 'og:description', 'og:type', 'og:url', 'og:image'].filter((k) => !meta(html, k));
  if (og.length) fail('og', `missing ${og.join(', ')}`);

  const ld = [...html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi)];
  if (!ld.length) fail('json-ld', 'none');
  for (const [, body] of ld) {
    try { JSON.parse(body); } catch (e) { fail('json-ld', `does not parse: ${e.message}`); errors.push(`${path}: JSON-LD does not parse`); }
  }

  const heads = [...html.matchAll(/<h([1-6])\b/gi)].map((m) => Number(m[1]));
  const h1s = heads.filter((h) => h === 1).length;
  if (h1s !== 1) fail('h1', `${h1s} h1 elements`);
  const skip = heads.findIndex((h, i) => i > 0 && h > heads[i - 1] + 1);
  if (skip > 0) fail('headings', `h${heads[skip - 1]} then h${heads[skip]}`);

  const text = visibleText(html).length;
  if (text < 500) fail('text', `${text} characters`);
  const noAlt = tags(html, 'img').filter((t) => attr(t, 'alt') === null).length;
  if (noAlt) fail('alt', `${noAlt} image(s) without alt`);

  const twinTag = link(html, 'alternate', 'text/markdown');
  if (!twinTag) fail('twin', 'no markdown alternate link');
  else {
    // The href carries the baseurl; the twin sits at the same path in _site.
    const expected = path === 'index.html' ? 'index.md' : path.replace(/\.html$/, '.md');
    const href = attr(twinTag, 'href') || '';
    if (!href.endsWith('/' + expected) && href !== expected) fail('twin', `links ${href}, expected …/${expected}`);
    else if (!read(expected)) fail('twin', `${expected} is missing`);
  }
  if (tags(html, 'meta').some((t) => /refresh/i.test(attr(t, 'http-equiv') || ''))) fail('no-refresh', 'meta refresh found');

  for (const [id, label, , isError] of PAGE_CHECKS) {
    if (isError && fails[id]) errors.push(`${path}: ${label}: ${fails[id]}`);
  }
  pages.push({ path, fails });
}

if (!pages.length) {
  console.error('x page check found 0 pages. That is a broken check, not a clean site.');
  process.exit(1);
}

const pageScores = PAGE_CHECKS.map(([id, label, points]) => {
  const failing = pages.filter((p) => p.fails[id]);
  const passing = pages.length - failing.length;
  return {
    id, label, points,
    earned: Math.round((points * passing / pages.length) * 10) / 10,
    passing, total: pages.length,
    failing: failing.map((p) => ({ path: p.path, detail: p.fails[id] })),
  };
});
const score = Math.round([...site, ...pageScores].reduce((s, c) => s + c.earned, 0));

let baseline = null;
if (BASELINE && existsSync(BASELINE)) {
  try { baseline = JSON.parse(readFileSync(BASELINE, 'utf8')).score; } catch { baseline = null; }
}
const regressed = baseline !== null && score < baseline;
if (regressed) errors.push(`score dropped from ${baseline} to ${score}`);

const result = { score, baseline, pages: pages.length, site, checks: pageScores, errors };
if (JSON_OUT) writeFileSync(JSON_OUT, JSON.stringify(result, null, 2));

console.log(`agent-readiness score ${score}/100${baseline !== null ? ` (base ${baseline})` : ''}, ${pages.length} pages`);
for (const c of site) if (!c.pass) console.log(`  - ${c.label}: ${c.detail} (-${c.points})`);
for (const c of pageScores) if (c.passing < c.total) console.log(`  - ${c.label}: fails on ${c.total - c.passing} of ${c.total} pages (-${Math.round((c.points - c.earned) * 10) / 10})`);
if (errors.length) {
  console.error(`${errors.length} error(s):`);
  for (const e of errors) console.error(`  x ${e}`);
  process.exit(1);
}
console.log('page checks OK');
