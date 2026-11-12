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
// published; without it the comment links the run's artifact instead).

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
const icon = (o) => (o === 'success' ? '✅' : o === 'failure' ? '❌' : '⏭️');
const tail = (s, n = 15) => s.trim().split('\n').slice(-n).join('\n');
// Details quote markup ("no <link rel=canonical>"), which GitHub would drop.
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const delta = (now, base) => (typeof base === 'number' ? ` (main ${base}, ${now - base >= 0 ? '+' : ''}${Math.round((now - base) * 10) / 10})` : '');

// open-agent-readiness: its own total_score is the number reported. It grades
// through the Cloudflare quick tunnel, whose edge on trycloudflare.com rewrites
// robots.txt with Cloudflare's AI-crawler rules and answers AI crawlers with
// 403. The checks below grade that edge, not this site; they are listed apart
// so nobody tries to fix them here. Both PR and base go through the same edge,
// so the difference between them is still fair.
const TUNNEL_CHECKS = new Set(['ai_bot_rules', 'content_signals', 'browse_bot_access', 'multi_bot_fetch']);
function agentScore(o) {
  if (!o || typeof o.total_score !== 'number') return null;
  const open = (o.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn');
  return {
    score: o.total_score,
    grade: o.grade,
    site: open.filter((c) => !TUNNEL_CHECKS.has(c.id)),
    tunnel: open.filter((c) => TUNNEL_CHECKS.has(c.id)),
  };
}

// Vercel's Agent Readability audit: score, rating, and checks by category.
function vercelAudit(o) {
  if (!o || typeof o.score !== 'number') return null;
  const failed = [];
  for (const [, cat] of Object.entries(o.categories || {})) {
    for (const c of cat.checks || []) if (!c.passed && !c.skipped) failed.push(c);
  }
  return { score: o.score, rating: o.rating, failed };
}

const rows = [];
rows.push(['House rules and telemetry', icon(out.tests), out.tests === 'failure' ? 'see Failures' : '']);
rows.push(['Build', icon(out.build), '']);
const linksOk = /links OK, (\d+)/.exec(text('links.log'));
rows.push(['Internal links and anchors', icon(out.links), linksOk ? `${linksOk[1]} checked` : out.links === 'failure' ? 'see Failures' : '']);

const pages = json('pages.json');
rows.push(['Page checks', icon(out.pages), pages ? `score **${pages.score}/100**${delta(pages.score, pages.baseline)}, ${pages.pages} pages` : '']);

const oarPr = agentScore(json('oar-pr.json'));
const oarBase = agentScore(json('oar-base.json'));
rows.push(['Agent readiness (open-agent-readiness)', oarPr ? '📊' : '⚠️',
  oarPr ? `score **${oarPr.score}/100**, grade ${oarPr.grade}${delta(oarPr.score, oarBase?.score)} · report only`
    : 'unavailable this run (the tunnel or scan did not finish); not blocking']);

const vcPr = vercelAudit(json('vercel-pr.json'));
const vcBase = vercelAudit(json('vercel-base.json'));
rows.push(['Agent readability (Vercel)', vcPr ? '📊' : '⏭️',
  vcPr ? `score **${vcPr.score}/100**, ${vcPr.rating}${delta(vcPr.score, vcBase?.score)} · report only` : 'did not run']);

const lumar = json('lumar.json');
rows.push(['Agent files (Lumar)', icon(out.agentfiles),
  lumar && lumar.reach ? `${lumar.adopted} of ${lumar.checked} published, ${lumar.broken} broken` : out.agentfiles === 'failure' ? 'see Failures' : '']);

const lk = json('linkinator.json');
const lkLinks = lk?.links || [];
const isLocal = (u) => /^http:\/\/localhost:8080\b/.test(u);
const broken = lkLinks.filter((l) => l.state === 'BROKEN');
const brokenExt = broken.filter((l) => !isLocal(l.url));
const brokenInt = broken.filter((l) => isLocal(l.url));
// The workflow passes 401/403/429 as warnings: the site turned a bot away.
const blocked = lkLinks.filter((l) => l.state !== 'BROKEN' && [401, 403, 429].includes(l.status));
rows.push(['Links (linkinator)', lk ? (broken.length ? '⚠️' : '✅') : '⏭️',
  lk ? `${lkLinks.length} checked, ${brokenInt.length} internal and ${brokenExt.length} external broken${blocked.length ? `, ${blocked.length} blocked bots` : ''} · report only` : '']);

const visualPages = json('visual-pages.json');
rows.push(['Visual diff (BackstopJS)', visual ? (changed.length ? '🖼️' : '✅') : visualPages ? '✅' : '⏭️',
  visual ? `${changed.length} of ${pairs.length} screenshots changed, on ${visualPages?.length ?? '?'} page(s) whose output changed`
    : visualPages ? 'no page changed from main, so nothing to capture' : 'no base build to compare']);

const sha = (env.HEAD_SHA || '').slice(0, 7);
const lines = [
  '<!-- hub-pr-report -->',
  `### PR checks${sha ? ` for \`${sha}\`` : ''}`,
  '',
  '| Check | | Result |',
  '|---|:-:|---|',
  ...rows.map((r) => `| ${r.join(' | ')} |`),
  '',
];

lines.push('<!-- visual -->');
if (changed.length) {
  const img = (p, k) => (env.IMAGE_BASE && p.files[k] ? `<img src="${env.IMAGE_BASE}/${p.name}-${k}.png" width="260" alt="${esc(p.label)}, ${p.viewport}, ${k}">` : '');
  lines.push(`<details><summary><b>${changed.length} changed screenshot${changed.length > 1 ? 's' : ''}</b></summary>`, '');
  if (env.IMAGE_BASE) {
    lines.push('| Page | main | this PR | difference |', '|---|---|---|---|');
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

if (pages) {
  const lost = [
    ...pages.site.filter((c) => !c.pass).map((c) => `- ${c.label}: ${esc(c.detail)} (-${c.points})`),
    ...pages.checks.filter((c) => c.passing < c.total).map((c) =>
      `- ${c.label}: fails on ${c.total - c.passing} of ${c.total} pages (-${Math.round((c.points - c.earned) * 10) / 10}), e.g. \`${c.failing[0].path}\`: ${esc(c.failing[0].detail)}`),
  ];
  if (lost.length) lines.push(`<details><summary>Page checks: where the other ${100 - pages.score} points went</summary>`, '', ...lost, '', '</details>', '');
}
if (oarPr) {
  const mark = { fail: '❌', warn: '⚠️' };
  const item = (c) => `- ${mark[c.status]} ${esc(c.title || c.id)} (${c.category}, weight ${c.weight}): ${esc(c.detail || '')}`;
  lines.push(`<details><summary>Agent readiness (open-agent-readiness): ${oarPr.site.length + oarPr.tunnel.length} checks failed or warned</summary>`, '',
    ...oarPr.site.map(item));
  if (oarPr.tunnel.length) {
    lines.push('', '**Graded the tunnel, not this site.** Cloudflare\'s edge in front of the scan rewrites robots.txt and refuses AI crawlers; GitHub Pages does neither. These count in the score above, for the PR and main alike:', '', ...oarPr.tunnel.map(item));
  }
  lines.push('', '</details>', '');
}
if (vcPr && vcPr.failed.length) {
  lines.push(`<details><summary>Agent readability (Vercel): ${vcPr.failed.length} checks failed</summary>`, '',
    ...vcPr.failed.map((c) => `- ❌ ${esc(c.name)} (${c.tier})${c.detail ? `: ${esc(c.detail)}` : ''}. ${esc(c.hint || '')}`),
    '', 'Spec: [Agent Readability Spec](https://vercel.com/kb/guide/agent-readability-spec).', '', '</details>', '');
}
if (broken.length) {
  lines.push('<details><summary>Broken links</summary>', '',
    ...broken.slice(0, 30).map((l) => `- ${esc(l.url.replace('http://localhost:8080', ''))}: ${l.status || 'no response'}`), '', '</details>', '');
}
if (lumar && lumar.broken) {
  const bad = (lumar.signals || []).filter((s) => s.defects && s.defects.length);
  lines.push('<details><summary>Agent file defects</summary>', '',
    ...bad.flatMap((s) => s.defects.map((d) => `- ${s.label}: ${esc(typeof d === 'string' ? d : JSON.stringify(d))}`)), '', '</details>', '');
}
const failed = [['tests', 'House rules and telemetry', 'tests.log'], ['build', 'Build', 'build.log'], ['links', 'Internal links', 'links.log'],
  ['pages', 'Page checks', 'pages.log'], ['agentfiles', 'Agent files', 'lumar.log']].filter(([k]) => out[k] === 'failure');
if (failed.length) {
  lines.push('<details open><summary>Failures</summary>', '');
  for (const [, label, log] of failed) lines.push(`**${label}**`, '```', tail(text(log)) || '(no output)', '```', '');
  lines.push('</details>', '');
}
if (env.RUN_URL) lines.push(`<sub>[Workflow run and full reports](${env.RUN_URL}). This comment updates on every push.</sub>`);
console.log(lines.join('\n'));
