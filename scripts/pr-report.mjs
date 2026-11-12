#!/usr/bin/env node
// The PR checks comment, as markdown on stdout, from what the Checks job left
// in its report folder: outcomes.json (each step's outcome) and the checks'
// logs and JSON. The first line is a marker the workflow finds to update the
// same comment. Every input is optional, so a run that stopped early still
// reports what it got.
//
//   node scripts/pr-report.mjs <report-dir>            the comment
//   node scripts/pr-report.mjs --images <report-dir>   "<source>\t<name>" per changed screenshot
//
// Environment: HEAD_SHA, RUN_URL, IMAGE_BASE (where --images files were
// published; without it the comment points at the run's artifact instead).
//
// Layout: a one-line verdict, the blocking checks on one line, the scores in a
// table against main, one line each for links and screenshots, then one
// merged list of what would raise the scores, so the three scorers' overlapping
// findings read as a to-do list rather than three reports.

import { readFileSync, existsSync } from 'node:fs';
import { join, posix } from 'node:path';

const listImages = process.argv[2] === '--images';
const dir = process.argv[listImages ? 3 : 2] || 'report';
const json = (f) => { try { return JSON.parse(readFileSync(join(dir, f), 'utf8')); } catch { return null; } };
const text = (f) => (existsSync(join(dir, f)) ? readFileSync(join(dir, f), 'utf8') : '');
const env = process.env;
const MAX_SHOTS = 8;

// Visual diff: BackstopJS's JSON report, with image paths relative to its
// json folder. Each changed pair publishes as <slug>-main/pr/diff.png.
const visual = json('visual/json/jsonReport.json');
const visualPages = json('visual-pages.json');
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const pairs = (visual?.tests || []).map((t) => {
  const p = t.pair || {};
  const from = (f) => (f ? posix.join('visual/json', f.replace(/\\/g, '/')) : null);
  return {
    label: p.label, viewport: p.viewportLabel, status: t.status,
    mismatch: Number(p.diff?.misMatchPercentage ?? 0),
    files: { main: from(p.reference), pr: from(p.test), diff: from(p.diffImage) },
    name: slug(`${p.label} ${p.viewportLabel}`),
  };
});
const changed = pairs.filter((p) => p.status === 'fail');

if (listImages) {
  for (const p of changed.slice(0, MAX_SHOTS)) {
    for (const [k, f] of Object.entries(p.files)) if (f && existsSync(join(dir, f))) console.log(`${f}\t${p.name}-${k}.png`);
  }
  process.exit(0);
}

const out = json('outcomes.json') || {};
const tail = (s, n = 15) => s.trim().split('\n').slice(-n).join('\n');
// Details quote markup ("no <link rel=canonical>"), which GitHub would drop.
const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

// ---------- inputs ----------

const pages = json('pages.json');
const lumar = json('lumar.json');
const linksOk = /links OK, (\d+)/.exec(text('links.log'));

// open-agent-readiness: its own total_score. It grades through the Cloudflare
// quick tunnel, whose edge on trycloudflare.com rewrites robots.txt with
// Cloudflare's AI-crawler rules and answers AI crawlers with 403; the checks
// below grade that edge, not this site. PR and base go through the same edge.
const TUNNEL_CHECKS = new Set(['ai_bot_rules', 'content_signals', 'browse_bot_access', 'multi_bot_fetch']);
const oar = (o) => (o && typeof o.total_score === 'number'
  ? { score: o.total_score, label: o.grade, open: (o.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn') }
  : null);
const vercel = (o) => {
  if (!o || typeof o.score !== 'number') return null;
  const failed = [];
  for (const cat of Object.values(o.categories || {})) for (const c of cat.checks || []) if (!c.passed && !c.skipped) failed.push(c);
  return { score: o.score, label: o.rating, failed };
};
// Vercel's audit samples 5 random pages from the sitemap, so the workflow runs
// it three times per side; the run with the middle score is reported, and a
// difference under VERCEL_NOISE points reads as unchanged.
const VERCEL_NOISE = 5;
const middle = (prefix) => {
  const runs = [1, 2, 3].map((i) => vercel(json(`${prefix}-${i}.json`))).filter(Boolean);
  if (!runs.length) return vercel(json(`${prefix}.json`));
  runs.sort((a, b) => a.score - b.score);
  return { ...runs[Math.floor((runs.length - 1) / 2)], runs: runs.map((r) => r.score) };
};
const oarPr = oar(json('oar-pr.json')), oarBase = oar(json('oar-base.json'));
const vcPr = middle('vercel-pr'), vcBase = middle('vercel-base');

const lk = json('linkinator.json');
const lkLinks = lk?.links || [];
const broken = lkLinks.filter((l) => l.state === 'BROKEN');
// The workflow passes 401/403/429 as warnings: the site turned a bot away.
const blocked = lkLinks.filter((l) => l.state !== 'BROKEN' && [401, 403, 429].includes(l.status));

// ---------- verdict and blocking checks ----------

const BLOCKING = [
  ['tests', 'House rules', 'tests.log'],
  ['build', 'Build', 'build.log'],
  ['links', linksOk ? `Internal links (${linksOk[1]})` : 'Internal links', 'links.log'],
  ['pages', 'Page checks', 'pages.log'],
  ['agentfiles', 'Agent files (Lumar)', 'lumar.log'],
];
const mark = (o) => (o === 'success' ? '✅' : o === 'failure' ? '❌' : '⏭️');
const failedChecks = BLOCKING.filter(([k]) => out[k] === 'failure');

// [name, PR result, main result, points of difference that count as noise]
const lumarBase = json('lumar-base.json');
const lumarRow = (l) => (l && l.reach ? { score: l.adopted, text: `${l.adopted} of ${l.checked} published, ${l.broken} broken` } : null);
const scores = [
  ['[Lumar agentic-readiness](https://agentic-readiness.lumar.io/cli)', lumarRow(lumar), lumarRow(lumarBase), 0],
  ['[open-agent-readiness](https://gitlab.com/startuphub-ai/open-agent-readiness)', oarPr, oarBase, 0],
  ['[Vercel agent readability](https://vercel.com/kb/guide/agent-readability-spec)', vcPr, vcBase, VERCEL_NOISE],
  ['Page checks (ours)', pages && { score: pages.score }, pages && typeof pages.baseline === 'number' ? { score: pages.baseline } : null, 0],
];
const diff = (pr, base) => Math.round((pr.score - base.score) * 10) / 10;
const moved = scores.filter(([, pr, base, noise]) => pr && base && Math.abs(diff(pr, base)) > noise);
const change = (pr, base, noise = 0) => {
  if (!pr || !base) return '';
  const d = diff(pr, base);
  return Math.abs(d) <= noise ? '–' : d > 0 ? `▲ +${d}` : `▼ ${d}`;
};
const plainName = (name) => name.replace(/\[([^\]]+)\]\([^)]+\)/, '$1');

const sha = (env.HEAD_SHA || '').slice(0, 7);
const lines = ['<!-- hub-pr-report -->', `### PR checks${sha ? ` for \`${sha}\`` : ''}`, ''];

const verdict = failedChecks.length
  ? `❌ **${plural(failedChecks.length, 'blocking check')} failed:** ${failedChecks.map(([, label]) => label).join(', ')}.`
  : `✅ **All ${BLOCKING.length} blocking checks pass.**`;
const scoreNote = moved.length
  ? ` Scores changed: ${moved.map(([name, pr, base, noise]) => `${plainName(name)} ${change(pr, base, noise)}`).join(', ')}.`
  : scores.some(([, pr, base]) => pr && base) ? ' Scores unchanged from main.' : '';
lines.push(verdict + scoreNote, '', BLOCKING.map(([k, label]) => `${mark(out[k])} ${label}`).join(' · '), '');

// ---------- scores ----------

lines.push('**Agent checks**', '', '| | This PR | main | Change |', '|---|--:|--:|:-:|');
for (const [name, pr, base, noise] of scores) {
  const fmt = (s) => (!s ? '' : s.text ? esc(s.text) : `${s.score}${s.label ? ` (${esc(s.label)})` : ''}`);
  lines.push(`| ${name} | ${pr ? fmt(pr) : 'unavailable'} | ${fmt(base) || '–'} | ${change(pr, base, noise)} |`);
}
lines.push('');

// ---------- links and screenshots ----------

// Each on its own paragraph: consecutive lines would run together on GitHub.
if (lk) {
  const extra = blocked.length ? ` (${plural(blocked.length, 'site blocks', 'sites block')} bots)` : '';
  lines.push(broken.length
    ? `🔗 ${lkLinks.length} links checked, **${broken.length} broken**${extra}`
    : `🔗 ${lkLinks.length} links checked, none broken${extra}`, '');
}
if (visual) lines.push(changed.length ? `🖼️ **${plural(changed.length, 'screenshot')} changed** of ${pairs.length}, on the pages this PR changed` : `🖼️ ${pairs.length} screenshots of changed pages, none look different`, '');
else if (visualPages) lines.push('🖼️ No page changed, so no screenshots', '');

lines.push('<!-- visual -->');
if (changed.length) {
  const img = (p, k) => (env.IMAGE_BASE && p.files[k] ? `<img src="${env.IMAGE_BASE}/${p.name}-${k}.png" width="260" alt="${esc(p.label)}, ${p.viewport}, ${k}">` : '');
  lines.push(`<details open><summary>Changed screenshots</summary>`, '');
  if (env.IMAGE_BASE) {
    lines.push('| Page | main | This PR | Difference |', '|---|---|---|---|');
    for (const p of changed.slice(0, MAX_SHOTS)) {
      lines.push(`| ${esc(p.label)}, ${p.viewport} (${p.mismatch}%) | ${img(p, 'main')} | ${img(p, 'pr')} | ${img(p, 'diff')} |`);
    }
    if (changed.length > MAX_SHOTS) lines.push('', `${changed.length - MAX_SHOTS} more in the run's \`pr-report\` artifact.`);
  } else {
    for (const p of changed) lines.push(`- ${esc(p.label)}, ${p.viewport}: ${p.mismatch}% different`);
    lines.push('', 'The images are in the run\'s `pr-report` artifact.');
  }
  lines.push('', '</details>');
}
lines.push('<!-- /visual -->', '');

// ---------- how to improve the scores ----------
//
// The three scorers overlap: a missing canonical link costs points in all of
// them. Each finding is mapped to one issue, so the list reads once.
// `page` ids are check-pages.mjs ids, `oar` ids are open-agent-readiness ids,
// `vercel` entries are Vercel audit check names.

const ISSUES = [
  { group: 'fix', title: 'Fix broken links in llms.txt', oar: ['llms_links_live'], vercel: ['llms.txt links resolve'] },
  { group: 'fix', title: 'Add a canonical link to every page', page: ['canonical'], oar: ['canonical_url'], vercel: ['Canonical URL'] },
  { group: 'fix', title: 'Add JSON-LD to every page, inside `<head>`', page: ['json-ld'], oar: ['json_ld', 'jsonld_in_head', 'org_schema'], vercel: ['Structured data'] },
  { group: 'fix', title: 'Add a 404 page', page: ['404'], vercel: ['Soft 404 detection'] },
  { group: 'fix', title: 'Add `lastmod` dates to the sitemap, and a `sitemap.md`', page: ['sitemap'], oar: ['sitemap'], vercel: ['sitemap.xml', 'sitemap.md'] },
  { group: 'fix', title: 'Use one h1 per page, with headings in order', page: ['h1', 'headings'], oar: ['h1_singular'], vercel: ['Heading structure'] },
  { group: 'fix', title: 'Give images meaningful alt text', page: ['alt'], oar: ['img_alt_coverage'] },
  { group: 'fix', title: 'Write meta descriptions of 50 to 320 characters', page: ['description'], oar: ['meta_description'], vercel: ['Meta description'] },
  { group: 'fix', title: 'Complete the Open Graph tags', page: ['og'], oar: ['open_graph'] },
  { group: 'fix', title: 'Put more of each page in plain HTML', page: ['text'], oar: ['readable_html', 'early_facts', 'html_payload_size'], vercel: ['Server-rendered content', 'Page size (HTML text)'] },
  { group: 'fix', title: 'Keep every page reachable without redirects or sign-in', vercel: ['Redirect behavior', 'Auth gate detection'] },
  { group: 'fix', title: 'Link and publish a Markdown twin for every page', page: ['twin'] },
  // Vercel requests <page URL>.md. Twins sit at /build/x.md, so the sitemap's
  // /build/x.html sends it to /build/x.html.md, a 404. Listing pages without
  // .html (GitHub Pages serves /build/x from x.html) would make it find them.
  { group: 'fix', title: 'List pages in the sitemap without `.html`, so `<page>.md` finds the Markdown twin', vercel: ['.md URL → markdown'] },
  { group: 'fix', title: 'Fix llms.txt and llms-full.txt', page: ['llms-txt', 'llms-full'], oar: ['llms_txt', 'llms_full_txt', 'llms_link_notes', 'llms_describedby'], vercel: ['llms.txt', 'llms.txt size', 'llms.txt valid'] },
  { group: 'host', title: 'Serve Markdown to agents that ask for it', oar: ['markdown_negotiation', 'json_negotiation'], vercel: ['Agent UA → markdown', 'Accept header → markdown', 'Missing page → markdown', 'Vary: Accept'] },
  { group: 'host', title: 'robots.txt rules for AI crawlers (read only at the root of the host)', page: ['robots'], oar: ['robots_txt'], vercel: ['robots.txt'] },
  { group: 'host', title: 'HTTP response headers (Link, rate limits)', oar: ['link_header', 'rate_limit_headers'] },
  { group: 'na', title: 'APIs, MCP, OAuth, commerce and site search', oar: ['mcp_server_card', 'openapi_spec', 'oauth_discovery', 'offer_structured_data', 'payment_link_surface', 'commerce_surface', 'agentic_registration', 'site_search_action', 'a2a_agent_card', 'agent_skills', 'api_catalog', 'web_bot_auth', 'security_txt'] },
];

const pageFails = new Map();
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
for (const c of pages?.site || []) if (!c.pass) pageFails.set(c.id, { lost: c.points, detail: esc(cap(c.detail)) });
for (const c of pages?.checks || []) {
  if (c.passing < c.total) {
    pageFails.set(c.id, {
      lost: Math.round((c.points - c.earned) * 10) / 10,
      detail: `Fails on ${c.total - c.passing} of ${c.total} pages, e.g. \`${c.failing[0].path}\`: ${esc(c.failing[0].detail)}`,
    });
  }
}
const oarOpen = new Map((oarPr?.open || []).map((c) => [c.id, c]));
const vcFailed = new Map((vcPr?.failed || []).map((c) => [c.name, c]));
const used = { oar: new Set(), vercel: new Set() };

// One tag per scorer, however many of its checks an issue covers: page checks
// with the points lost, agent readiness with its worst status, Vercel with
// whether any failed check is required.
const found = [];
for (const issue of ISSUES) {
  let detail = '', weight = 0, lost = 0, oarWorst = null, vcWorst = null;
  for (const id of issue.page || []) {
    const f = pageFails.get(id);
    if (f) { lost += f.lost; detail ||= f.detail; }
  }
  for (const id of issue.oar || []) {
    const c = oarOpen.get(id);
    used.oar.add(id);
    if (c) { oarWorst = oarWorst === 'fail' ? 'fail' : c.status; detail ||= esc(cap(c.detail)); weight += c.weight || 1; }
  }
  for (const name of issue.vercel || []) {
    const c = vcFailed.get(name);
    used.vercel.add(name);
    if (c) {
      vcWorst = vcWorst === 'required' ? 'required' : c.tier;
      detail ||= esc(cap(`${c.detail ? `${c.detail}. ` : ''}${c.hint || ''}`));
      weight += c.tier === 'required' ? 3 : 1;
    }
  }
  const hits = [
    lost && `page checks −${Math.round(lost * 10) / 10}`,
    oarWorst && `agent readiness ${oarWorst === 'fail' ? '❌' : '⚠️'}`,
    vcWorst && `Vercel ❌ ${vcWorst}`,
  ].filter(Boolean);
  if (hits.length) found.push({ ...issue, hits, detail, weight: weight + lost });
}
// Anything a scorer reports that the map above does not know yet.
for (const [id, c] of oarOpen) {
  if (!used.oar.has(id) && !TUNNEL_CHECKS.has(id)) found.push({ group: 'other', title: esc(c.title || id), hits: ['agent readiness'], detail: esc(c.detail), weight: c.weight || 1 });
}
for (const [name, c] of vcFailed) {
  if (!used.vercel.has(name)) found.push({ group: 'other', title: esc(name), hits: [`Vercel ${c.tier}`], detail: esc(c.detail || c.hint), weight: 1 });
}
const tunnel = [...oarOpen.values()].filter((c) => TUNNEL_CHECKS.has(c.id));

const fix = found.filter((f) => f.group === 'fix' || f.group === 'other').sort((a, b) => b.weight - a.weight);
const host = found.filter((f) => f.group === 'host');
const na = found.filter((f) => f.group === 'na');
if (fix.length || host.length || na.length || tunnel.length) {
  lines.push(`<details><summary><b>How to improve the scores</b> (${plural(fix.length, 'fix', 'fixes')} possible here)</summary>`, '');
  if (fix.length) {
    lines.push('**Fixable in this repository**, most points first:', '');
    for (const f of fix) lines.push(`- **${f.title}.** ${f.detail} <sub>(${f.hits.join(' · ')})</sub>`);
    lines.push('');
  }
  if (host.length) {
    lines.push('**Needs a different host.** GitHub Pages cannot set response headers or vary what it serves, and crawlers read robots.txt only at the root of `microsoft.github.io`:', '');
    for (const f of host) lines.push(`- ${f.title} <sub>(${f.hits.join(' · ')})</sub>`);
    lines.push('');
  }
  if (na.length) lines.push(`**Not relevant to this site:** ${na.map((f) => f.title).join('; ')}.`, '');
  if (tunnel.length) {
    lines.push(`**Graded the tunnel, not this site:** ${tunnel.map((c) => esc(c.title || c.id)).join('; ')}. Cloudflare's edge in front of the scan rewrites robots.txt and refuses AI crawlers. These cost points for the PR and main alike.`, '');
  }
  lines.push('</details>', '');
}

// ---------- problems ----------

if (broken.length) {
  lines.push('<details><summary>Broken links</summary>', '',
    ...broken.slice(0, 30).map((l) => `- ${esc(l.url.replace('http://localhost:8080', ''))}: ${l.status || 'no response'}`), '', '</details>', '');
}
if (lumar && lumar.broken) {
  const bad = (lumar.signals || []).filter((s) => s.defects && s.defects.length);
  lines.push('<details><summary>Agent file defects</summary>', '',
    ...bad.flatMap((s) => s.defects.map((d) => `- ${s.label}: ${esc(typeof d === 'string' ? d : JSON.stringify(d))}`)), '', '</details>', '');
}
if (failedChecks.length) {
  lines.push('<details open><summary>Failures</summary>', '');
  for (const [, label, log] of failedChecks) lines.push(`**${label}**`, '```', tail(text(log)) || '(no output)', '```', '');
  lines.push('</details>', '');
}

// ---------- footer ----------

const foot = [sha && `\`${sha}\``, env.RUN_URL && `[Run and full reports](${env.RUN_URL})`, 'updates on every push'].filter(Boolean).join(' · ');
const vercelRuns = vcPr?.runs ? ` (this PR scored ${vcPr.runs.join(', ')})` : '';
lines.push(`<sub>${foot}<br>open-agent-readiness scans through a temporary Cloudflare tunnel. Vercel's audit grades 5 pages picked at random, so it runs 3 times and reports the middle score${vercelRuns}; a difference under ${VERCEL_NOISE} points counts as unchanged. Links: linkinator. Screenshots: BackstopJS. Page checks: \`scripts/check-pages.mjs\`.</sub>`);
console.log(lines.join('\n'));
