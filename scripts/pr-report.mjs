#!/usr/bin/env node
// Writes the PR comment, as markdown on stdout, from what the PR workflow left
// in one folder: outcomes.json (each step's outcome), the checks' logs and JSON.
// The first line is a marker the workflow finds to update the same comment.
//
//   node scripts/pr-report.mjs <report-dir>
//
// Environment: PREVIEW_URL, PREVIEW_STATE (live, pending, failed, skipped),
// HEAD_SHA, RUN_URL. Every input is optional, so a run that stopped early still
// reports what it got.

import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2] || 'report';
const json = (f) => { try { return JSON.parse(readFileSync(join(dir, f), 'utf8')); } catch { return null; } };
const text = (f) => (existsSync(join(dir, f)) ? readFileSync(join(dir, f), 'utf8') : '');
const env = process.env;
const out = json('outcomes.json') || {};
const icon = (o) => (o === 'success' ? '✅' : o === 'failure' ? '❌' : '⏭️');
const tail = (s, n = 15) => s.trim().split('\n').slice(-n).join('\n');
// Details quote markup ("no <link rel=canonical>"), which GitHub would drop.
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const rows = [];
rows.push(['House rules and telemetry', icon(out.tests), out.tests === 'failure' ? 'see Failures' : '']);
rows.push(['Build', icon(out.build), '']);
const linksOk = /links OK, (\d+)/.exec(text('links.log'));
rows.push(['Internal links', icon(out.links), linksOk ? `${linksOk[1]} checked` : out.links === 'failure' ? 'see Failures' : '']);

const pages = json('pages.json');
if (pages) {
  const base = pages.baseline;
  const delta = base === null || base === undefined ? '' : ` (main ${base}, ${pages.score - base >= 0 ? '+' : ''}${pages.score - base})`;
  rows.push(['Page checks', icon(out.pages), `score **${pages.score}/100**${delta}, ${pages.pages} pages`]);
} else rows.push(['Page checks', icon(out.pages), '']);

const lumar = json('lumar.json');
if (lumar && lumar.reach) {
  rows.push(['Agent files (Lumar)', icon(out.agentfiles), `${lumar.adopted} of ${lumar.checked} published, ${lumar.broken} broken`]);
} else rows.push(['Agent files (Lumar)', icon(out.agentfiles), out.agentfiles === 'failure' ? 'see Failures' : '']);

const ext = json('external.json');
if (ext) {
  const n = ext.broken.length;
  rows.push(['External links', n ? '⚠️' : '✅', `${ext.checked} checked, ${n} broken${ext.blocked.length ? `, ${ext.blocked.length} blocked bots` : ''} (report only)`]);
} else rows.push(['External links', '⏭️', '']);

const preview = {
  live: `**Preview:** ${env.PREVIEW_URL}`,
  pending: `**Preview:** ${env.PREVIEW_URL} (saved but not live yet: it appears once the Pages deploy on the default branch publishes previews; see the workflow run)`,
  failed: '**Preview:** ❌ the preview did not build or publish; see the workflow run',
  skipped: '**Preview:** none for pull requests from forks',
  removed: '**Preview:** removed when the pull request closed',
}[env.PREVIEW_STATE || 'skipped'];

const sha = (env.HEAD_SHA || '').slice(0, 7);
const lines = [
  '<!-- hub-pr-report -->',
  `### PR checks${sha ? ` for \`${sha}\`` : ''}`,
  '',
  preview,
  '',
  '| Check | Result | |',
  '|---|:-:|---|',
  ...rows.map((r) => `| ${r.join(' | ')} |`),
  '',
];

if (pages) {
  const lost = [
    ...pages.site.filter((c) => !c.pass).map((c) => `- ${c.label}: ${esc(c.detail)} (-${c.points})`),
    ...pages.checks.filter((c) => c.passing < c.total).map((c) =>
      `- ${c.label}: fails on ${c.total - c.passing} of ${c.total} pages (-${Math.round((c.points - c.earned) * 10) / 10}), e.g. \`${c.failing[0].path}\`: ${esc(c.failing[0].detail)}`),
  ];
  if (lost.length) lines.push(`<details><summary>Where the other ${100 - pages.score} points went</summary>`, '', ...lost, '', '</details>', '');
}
if (ext && ext.broken.length) {
  lines.push('<details><summary>Broken external links</summary>', '',
    ...ext.broken.map((b) => `- ${b.url}: ${b.status || b.error}, on \`${b.pages.join('`, `')}\``), '', '</details>', '');
}
if (lumar && lumar.broken) {
  const bad = (lumar.signals || []).filter((s) => s.defects && s.defects.length);
  lines.push('<details><summary>Agent file defects</summary>', '',
    ...bad.flatMap((s) => s.defects.map((d) => `- ${s.label}: ${typeof d === 'string' ? d : JSON.stringify(d)}`)), '', '</details>', '');
}
const failed = [['tests', 'House rules and telemetry', 'tests.log'], ['build', 'Build', 'build.log'], ['links', 'Internal links', 'links.log'],
  ['pages', 'Page checks', 'pages.log'], ['agentfiles', 'Agent files', 'lumar.log']].filter(([k]) => out[k] === 'failure');
if (failed.length) {
  lines.push('<details open><summary>Failures</summary>', '');
  for (const [, label, log] of failed) lines.push(`**${label}**`, '```', tail(text(log)) || '(no output)', '```', '');
  lines.push('</details>', '');
}
if (env.RUN_URL) lines.push(`<sub>[Workflow run](${env.RUN_URL}). This comment updates on every push.</sub>`);
console.log(lines.join('\n'));
