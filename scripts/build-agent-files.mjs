#!/usr/bin/env node
// Generates the agent-facing half of the site:
//
//   1. A .md twin next to every .html page, so `curl <page>.md` returns the
//      source the page was built from.
//   2. llms-full.txt, the whole site concatenated into one document.
//
// Runs after `jekyll build`, writing into _site. It reads the same .md sources
// Jekyll just consumed, so the twin cannot drift from the page: there is one
// source file, published twice.
//
// Pages that keep structured copy in front matter (the home page's hero and
// section data) get that data rendered back into markdown here, because it is
// real page content, not metadata. Scenario pages carry the prompt in the body,
// so the twin is the body itself.

import { readdirSync, statSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import yaml from 'js-yaml';

const SITE = '_site';
const SKIP_FILES = new Set(['README.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md']);
const SKIP_DIRS = new Set(['_site', '_includes', '_layouts', '__pycache__', 'docs', 'eval', 'redesign', 'runs', 'scripts', 'node_modules', '.github', '.git', 'assets', 'vendor', '.jekyll-cache', 'outputs']);

// Reading order for llms-full.txt. Anything discovered but not listed appends
// alphabetically, so a new page is never silently dropped.
const ORDER = [
  'index.md',
  'build/team-board.md',
  'build/inventory-reservations.md',
  'build/knowledge-base.md',
  'build/revenue-reporting.md',
  'build/shipment-tracker.md',
  'build/multi-tenant-helpdesk.md',
  'build/javascript-app.md',
  'build/python-api.md',
  'build/rag-app.md',
  'build/serverless-api.md',
  'build/event-driven-app.md',
  'build/multi-tenant.md',
  'build/data-api.md',
  'build/local-to-cloud.md',
  'container/get-started.md',
  'container/faq.md',
];

if (!existsSync(SITE)) {
  console.error(`x ${SITE} does not exist. Run "bundle exec jekyll build" first.`);
  process.exit(1);
}

function findPages(dir, prefix) {
  const out = [];
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name) || name.startsWith('.')) continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      out.push(...findPages(p, prefix ? `${prefix}/${name}` : name));
    } else if (name.endsWith('.md') && !SKIP_FILES.has(name)) {
      out.push(prefix ? `${prefix}/${name}` : name);
    }
  }
  return out;
}

function splitFrontMatter(raw) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(raw);
  if (!m) return { data: {}, body: raw };
  return { data: yaml.load(m[1]) || {}, body: raw.slice(m[0].length) };
}

// A {% raw %} ... {% endraw %} block, each tag on its own line, keeps Jekyll
// from reading code as Liquid (JSX `style={{ ... }}` otherwise vanishes from
// the HTML page). The twin drops the two tag lines and leaves the code between
// them untouched, so it matches what the page shows.
const RAW_BLOCK = /^[ \t]*\{%-?\s*raw\s*-?%\}[ \t]*\r?\n([\s\S]*?)^[ \t]*\{%-?\s*endraw\s*-?%\}[ \t]*(?:\r?\n|$)/m;

function resolveLiquid(text, config) {
  const siteUrl = String(config.url || '').replace(/\/$/, '');
  const base = String(config.baseurl || '');
  const resolve = (s) => s
    .replace(/\{\{\s*'([^']*)'\s*\|\s*absolute_url\s*\}\}/g, (w, p) => siteUrl + base + p)
    .replace(/\{\{\s*'([^']*)'\s*\|\s*relative_url\s*\}\}/g, (w, p) => base + p)
    .replace(/\{\{\s*site\.([a-z0-9_]+)\s*\}\}/gi, (w, key) =>
      Object.prototype.hasOwnProperty.call(config, key) ? String(config[key]) : w
    );
  // split() with a capture group alternates outside, inside, outside, ...
  return text
    .split(RAW_BLOCK)
    .map((part, i) => (i % 2 ? part : resolve(part)))
    .join('');
}

function stripAttributeLists(body) {
  return body
    .split('\n')
    .filter((line) => !/^\{:[^}]*\}\s*$/.test(line))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n');
}

function fence(code, lang) {
  return '```' + (lang || '') + '\n' + String(code).replace(/\s+$/, '') + '\n```';
}

// Strip inline HTML the front matter carries for the page (icons, logos, <code>).
function plain(s) {
  return String(s || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}

// Oxford list, matching the sentence the layout renders in the hero.
function sentenceList(items) {
  if (items.length < 2) return items.join('');
  return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
}

// A link to a page on this site points at that page's markdown twin, so an
// agent reading a twin stays in markdown. Links elsewhere pass through.
function twinHref(href) {
  return /^\//.test(href) ? href.replace(/\.html(?=#|$)/, '.md') : href;
}

// A link in the home page's data. One that starts with `/` is a page on this
// site and points at its markdown twin; one that starts with `#` stays on the
// page and is left out, since the twin has no anchors to land on.
function linkLine(l) {
  if (!l || !l.href || l.href.startsWith('#')) return null;
  return `- ${l.label}: ${twinHref(l.href)}`;
}

// The home page's structured front matter, rendered back into markdown.
function homeToMarkdown(d) {
  const out = [];
  const h = d.hero || {};
  out.push(`# ${[h.headline, h.headline_accent].filter(Boolean).join(' ')}`.trim(), '');
  if (h.tagline) out.push(h.tagline, '');
  out.push(h.subline, '');
  if (h.agents) out.push(`Works with ${sentenceList(h.agents)}.`, '');

  // Get a database: each tab with its steps and every command, so an agent
  // reading the twin can run them.
  out.push(`## ${d.quickstart_heading || 'Get a database'} {#get-running}`, '', d.quickstart_text || '', '');
  for (const m of d.quickstart || []) {
    out.push(`### ${m.name}: ${m.title}`, '', m.pill ? `${m.pill}. ${m.desc}` : m.desc, '');
    if (m.button) out.push(`${m.button.label}: ${m.button.href}`, '');
    for (const [i, st] of (m.steps || []).entries()) {
      out.push(`${i + 1}. ${st.title}.${st.text ? ` ${plain(st.text)}` : ''}`, '');
      if (st.code) out.push(fence(st.code, /^SELECT/i.test(st.code) ? 'sql' : 'bash'), '');
    }
    if (m.extra) {
      out.push(m.extra.label, '', fence(m.extra.code, 'bash'), '');
      if (m.extra.note) out.push(m.extra.note, '');
    }
    if (m.agent) out.push(m.agent.label, '', `> ${m.agent.prompt}`, '');
    if (m.note) out.push(m.note, '');
    const links = (m.links || []).map(linkLine).filter(Boolean);
    if (links.length) out.push(...links, '');
  }

  const sk = d.skills || {};
  out.push(`## ${sk.heading || 'Skills'} {#skills}`, '', sk.text || '', '');
  for (const a of sk.agents || []) {
    out.push(`### ${a.name}`, '', fence(a.code, 'bash'), '', plain(a.note), '');
  }
  if (sk.chips) out.push(`${sk.asks_label || 'Then ask:'}`, '', ...sk.chips.map((c) => `- ${c.text || c}`), '');
  if (sk.catalog && sk.catalog.text) out.push(plain(sk.catalog.text), '');

  out.push(`## ${d.build_heading || 'Build'} {#build}`, '', d.build_text || '', '');
  if (d.build_note) out.push(d.build_note, '');
  for (const [i, step] of (d.build_steps || []).entries()) out.push(`${i + 1}. ${step}`);
  out.push('');
  // Two groups of prompts, as the page's filter shows them: full apps, with
  // the details their dialogs show, then the building blocks.
  const groups = Object.fromEntries((d.template_groups || []).map((g) => [g.key, g.label]));
  const inside = d.template_inside || {};
  if (d.templates) {
    out.push(`### ${groups.apps || 'Apps'}`, '');
    for (const t of d.templates) {
      out.push(`#### [${t.title}](build/${t.slug}.md)`, '', `${t.tag}. ${t.blurb}`, '');
      if (d.template_runs_on) out.push(`- Runs on: ${d.template_runs_on.join(', ')}`);
      if (t.needs) out.push(`- Needs: ${t.needs}`);
      out.push(`- ${inside.tables || 'Tables'}: ${t.tables.map((n) => `\`${n}\``).join(', ')}`);
      out.push(`- ${inside.sql || 'Azure SQL features'}: ${t.sql.map(([n, x]) => `${n} (${String(x).replace(/\.$/, '')})`).join('; ')}`, '');
      out.push(`Full prompt: build/${t.slug}.md`, '');
    }
    out.push(`### ${groups.blocks || 'Building blocks'}`, '');
  }
  const titles = Object.fromEntries((d.scenarios || []).map((s) => [s.slug, s.title]));
  for (const s of d.scenarios || []) {
    out.push(`#### [${s.title}](build/${s.slug}.md)`, '', `${s.tag}. ${s.blurb}`, '');
    if (s.after) out.push(`- Builds on: [${titles[s.after] || s.after_title}](build/${s.after}.md)`);
    if (s.needs) out.push(`- Needs: ${s.needs}`);
    out.push(`- Database: ${s.cloud ? 'Azure SQL Database in the cloud' : 'Azure SQL Database in the cloud, or the local container'}`);
    out.push('', `Full prompt: build/${s.slug}.md`, '');
  }

  out.push(`## ${d.workloads_heading || 'Built for AI workloads'} {#workloads}`, '', d.workloads_text || '', '');
  for (const t of d.workloads || []) {
    out.push(`- ${t.title}: ${plain(t.text)}${t.link && /^https?:/.test(t.link.href) ? ` (${t.link.href})` : ''}`);
  }
  out.push('');

  out.push(`## ${d.videos_heading || 'Videos'} {#watch}`, '', d.videos_text || '', '');
  for (const vv of d.videos || []) out.push(`- [${vv.title}](${vv.href}): ${vv.text}`);
  out.push('');

  out.push(`## ${d.faq_heading || 'Frequently asked questions'} {#faq}`, '');
  for (const f of d.faqs || []) out.push(`### ${f.question}`, '', f.answer, '');
  return out.join('\n');
}

const config = yaml.load(readFileSync('_config.yml', 'utf8')) || {};
const found = findPages('.', '').filter(f => splitFrontMatter(readFileSync(f, 'utf8')).data.published !== false);
const pages = [
  ...ORDER.filter((f) => found.includes(f)),
  ...found.filter((f) => !ORDER.includes(f)).sort(),
];

if (pages.length === 0) {
  console.error('x found no page sources to publish. That is a broken build, not an empty site.');
  process.exit(1);
}

const parts = [];

for (const file of pages) {
  const raw = readFileSync(file, 'utf8');
  const { data, body } = splitFrontMatter(raw);

  let head = '';
  if (data.layout === 'home') head = homeToMarkdown(data);
  // Scenario pages: the body is the prompt and already carries its own H1.
  // Other pages print their title from front matter, so the twin adds it,
  // with the page's status pill when it has one.
  else if (data.title && !/^#\s/m.test(body.replace(/^```[\s\S]*?^```/gm, ''))) {
    head = [`# ${data.head_title || data.title}`, data.pill ? `${data.pill}.` : ''].filter(Boolean).join('\n\n');
  }

  const markdown = [head, stripAttributeLists(resolveLiquid(body, config))]
    .filter(Boolean)
    .join('\n')
    .trim() + '\n';

  const dest = join(SITE, file);
  mkdirSync(dirname(dest), { recursive: true });
  writeFileSync(dest, markdown, 'utf8');
  console.log(`  markdown twin  ${dest}`);

  // A page that has moved keeps a twin that says where it went, and stays out
  // of the one-file corpus.
  if (data.redirect_to) continue;

  const url = file === 'index.md' ? '/' :`/${file.replace(/\.md$/, '.html')}`;
  parts.push(`<!-- source: ${file} | page: ${url} -->\n\n${markdown}`);
}

const header = [
  `# ${config.title}`,
  '',
  `> ${String(config.description || '').trim().replace(/\s+/g, ' ')}`,
  '',
  'This file is every page of this site concatenated in full, generated at build',
  'time. For a linked index of the site instead, see /llms.txt.',
  '',
  '',
].join('\n');

writeFileSync(join(SITE, 'llms-full.txt'), header + parts.join('\n\n---\n\n'), 'utf8');
console.log(`  llms-full.txt  ${pages.length} page(s)`);
