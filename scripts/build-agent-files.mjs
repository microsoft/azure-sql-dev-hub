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
const SKIP_DIRS = new Set(['_site', '_includes', '_layouts', 'docs', 'scripts', 'node_modules', '.github', '.git', 'assets', 'vendor', '.jekyll-cache', 'outputs']);

// Reading order for llms-full.txt. Anything discovered but not listed appends
// alphabetically, so a new page is never silently dropped.
const ORDER = [
  'index.md',
  'build/javascript-app.md',
  'build/python-api.md',
  'build/rag-app.md',
  'build/serverless-api.md',
  'build/event-driven-app.md',
  'build/multi-tenant.md',
  'prompts.md',
  'for-agents.md',
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

function resolveLiquid(text, config) {
  const siteUrl = String(config.url || '').replace(/\/$/, '');
  const base = String(config.baseurl || '');
  return text
    .replace(/\{\{\s*'([^']*)'\s*\|\s*absolute_url\s*\}\}/g, (w, p) => siteUrl + base + p)
    .replace(/\{\{\s*'([^']*)'\s*\|\s*relative_url\s*\}\}/g, (w, p) => base + p)
    .replace(/\{\{\s*site\.([a-z0-9_]+)\s*\}\}/gi, (w, key) =>
      Object.prototype.hasOwnProperty.call(config, key) ? String(config[key]) : w
    );
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

// The home page's structured front matter, rendered back into markdown.
function homeToMarkdown(d) {
  const out = [];
  const h = d.hero || {};
  out.push(`# ${h.headline} ${h.headline_accent}`.trim(), '', h.subline, '');
  if (h.agents) out.push(`Works with ${h.agents.join(', ')}.`, '');

  const v = d.video || {};
  if (v.id) {
    out.push('## Demo video', '', `${v.title}. ${v.sub}`, '', `https://www.youtube.com/watch?v=${v.id}`, '');
    if (v.chapters) out.push(v.chapters.map((c) => `${c.stamp} ${c.label}`).join(' · '), '');
  }

  out.push('## Get running {#get-running}', '', d.quickstart_text || '', '');
  for (const m of d.quickstart || []) {
    out.push(`### ${m.name}: ${m.title}`, '', m.desc, '');
    if (m.code) out.push(fence(m.code, 'bash'), '');
    for (const c of m.checks || []) out.push(`- ${c[0]}: ${c[1]}`);
    out.push('');
    if (m.button) out.push(`${m.button.label}: ${m.button.href}`, '');
    if (m.link) out.push(`${m.link.label}: ${m.link.href}`, '');
  }
  if (d.then) out.push(`Then: ${d.then.from} to ${d.then.to}. ${d.then.note}`, '');

  out.push('## Build {#build}', '', d.build_text || '', '');
  for (const s of d.scenarios || []) {
    out.push(`### [${s.title}](build/${s.slug}.md)`, '', `${s.tag}. ${s.blurb}`, '', `Full prompt: build/${s.slug}.md`, '');
  }

  out.push('## Built for AI workloads {#workloads}', '', d.workloads_text || '', '');
  for (const t of d.workloads || []) {
    out.push(`- ${t.title}: ${plain(t.text)}${t.link && /^https?:/.test(t.link.href) ? ` (${t.link.href})` : ''}`);
  }
  out.push('');

  const sk = d.skills || {};
  out.push('## Skills {#skills}', '', sk.heading, '', sk.text, '');
  for (const a of sk.agents || []) {
    out.push(`### ${a.name}`, '', fence(a.code, 'bash'), '', plain(a.note), '');
  }
  if (sk.chips) out.push('Example prompts once the skills are installed:', '', ...sk.chips.map((c) => `- ${c}`), '');
  if (sk.note) out.push(plain(sk.note), '');

  out.push('## Videos {#watch}', '', d.videos_text || '', '');
  for (const vv of d.videos || []) out.push(`- [${vv.title}](${vv.href}): ${vv.text}`);
  out.push('');

  if (d.existing) out.push('## Existing data {#existing}', '', d.existing.text, '');
  if (d.continuity) out.push('## Local development {#continuity}', '', d.continuity.heading, '', d.continuity.text, '');
  out.push('## Before you build', '');
  for (const f of d.faqs || []) out.push(`### ${f.question}`, '', f.answer, '');
  if (d.close) out.push('## Get started', '', d.close.heading, '', fence(d.close.code, 'bash'), '');
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

  const markdown = [head, stripAttributeLists(resolveLiquid(body, config))]
    .filter(Boolean)
    .join('\n')
    .trim() + '\n';

  const dest = join(SITE, file);
  mkdirSync(dirname(dest), { recursive: true });
  writeFileSync(dest, markdown, 'utf8');
  console.log(`  markdown twin  ${dest}`);

  const url = file === 'index.md' ? '/' : `/${file.replace(/\.md$/, '.html')}`;
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
