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
const SKIP_DIRS = new Set(['_site', '_includes', '_layouts', '__pycache__', 'docs', 'runs', 'scripts', 'node_modules', '.github', '.git', 'assets', 'vendor', '.jekyll-cache', 'outputs']);

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

// The local container's setup guide, a dialog on the page: both routes, with
// every command, so an agent reading the twin can run them.
function containerSetup(cs) {
  if (!cs) return [];
  const out = [`#### ${cs.title}`, ''];
  const steps = (list) => {
    for (const [i, st] of (list || []).entries()) {
      out.push(`${i + 1}. ${st.title}. ${plain(st.text)}`, '');
      if (st.code) out.push(fence(st.code, 'bash'), '');
      if (st.prompt) out.push(`> ${st.prompt}`, '');
    }
  };
  out.push(`${cs.manual.tab}. ${plain(cs.manual.intro)}`, '');
  steps(cs.manual.steps);
  out.push(`${cs.agent.tab}. ${plain(cs.agent.intro)}`, '');
  steps(cs.agent.steps);
  for (const l of [cs.prerequisites, cs.limitations, cs.troubleshooting]) if (l) out.push(`- ${l.label}: ${twinHref(l.href)}`);
  out.push('');
  return out;
}

// The home page's structured front matter, rendered back into markdown.
function homeToMarkdown(d) {
  const out = [];
  const h = d.hero || {};
  out.push(`# ${[h.headline, h.headline_accent].filter(Boolean).join(' ')}`.trim(), '');
  if (h.tagline) out.push(h.tagline, '');
  out.push(h.subline, '');
  if (h.stacks) out.push(`Build with ${sentenceList(h.stacks)}.`, '');

  const v = d.demo || {};
  if (v.title) out.push(`## ${v.title}`, '', v.sub, '');

  out.push('## Get running {#get-running}', '', d.quickstart_text || '', '');
  for (const m of d.quickstart || []) {
    out.push(`### ${m.name}: ${m.title}`, '', m.desc, '');
    if (m.code) out.push(fence(m.code, 'bash'), '');
    for (const c of m.checks || []) out.push(`- ${c[0]}: ${c[1]}`);
    out.push('');
    if (m.button) out.push(`${m.button.label}: ${m.button.href}`, '');
    if (m.link) out.push(`${m.link.label}: ${m.link.href}`, '');
    if (m.key === 'local') out.push(...containerSetup(d.container_setup));
  }
  if (d.then) out.push(`Then: ${d.then.from} to ${d.then.to}. ${d.then.note}`, '');

  // The container section: its cards open the setup guide above, so the twin
  // names them and lists the resources, with the guide's own links.
  const ct = d.containers;
  if (ct) {
    const cs = d.container_setup || {};
    out.push(`## ${ct.heading} {#containers}`, '', `${ct.pill}. ${ct.text}`, '');
    for (const c of ct.cards || []) out.push(`- ${c.title}: ${c.text} The steps are in the setup guide under Get running.`);
    out.push('', `- ${ct.image.label}: ${ct.image.href}`);
    if (cs.prerequisites) out.push(`- ${ct.prerequisites}: ${twinHref(cs.prerequisites.href)}`);
    for (const l of [cs.limitations, cs.troubleshooting, cs.faq]) if (l) out.push(`- ${l.label}: ${twinHref(l.href)}`);
    out.push('');
  }

  out.push(`## ${d.build_heading || 'Build'} {#build}`, '', d.build_text || '', '');
  if (d.build_note) {
    const note = d.build_note_link && d.build_note_href
      ? d.build_note.replace(d.build_note_link, `[${d.build_note_link}](${d.build_note_href})`)
      : d.build_note;
    out.push(note, '');
  }
  for (const [i, step] of (d.build_steps || []).entries()) out.push(`${i + 1}. ${step}`);
  out.push('');
  // Two groups of templates, as the page's filter shows them: full apps, with
  // the details their dialogs show, then the building blocks.
  const groups = Object.fromEntries((d.template_groups || []).map((g) => [g.key, g.label]));
  const inside = d.template_inside || {};
  if (d.templates) {
    out.push(`### ${groups.apps || 'Apps'}`, '');
    for (const t of d.templates) {
      out.push(`#### [${t.title}](build/${t.slug}.md)`, '', `${t.tag}. ${t.blurb}`, '');
      out.push(`- Stack: ${d.template_stack}`, `- Covers: ${t.covers}`);
      if (d.template_runs_on) out.push(`- Runs on: ${d.template_runs_on.join(', ')}`);
      out.push('', `${inside.features || 'What it does'}:`, '', ...t.features.map((f) => `- ${f}`), '');
      out.push(`${inside.tables || 'Tables it creates'}:`, '', ...t.tables.map(([n, x]) => `- \`${n}\`: ${x}`), '');
      out.push(`${inside.sql || 'Azure SQL features it uses'}:`, '', ...t.sql.map(([n, x]) => `- ${n}: ${x}`), '');
      out.push(`${inside.try || 'Try it yourself'}:`, '', ...t.try.map(([n, x]) => `- ${n}. ${x}`), '');
      out.push(`Full prompt: build/${t.slug}.md`, '');
    }
    out.push(`### ${groups.blocks || 'Building blocks'}`, '');
  }
  for (const s of d.scenarios || []) {
    out.push(`#### [${s.title}](build/${s.slug}.md)`, '', `${s.tag}. ${s.blurb}`, '', `Full prompt: build/${s.slug}.md`, '');
  }

  out.push(`## ${d.workloads_heading} {#workloads}`, '', d.workloads_text || '', '');
  for (const t of d.workloads || []) {
    out.push(`- ${t.title}: ${plain(t.text)}${t.link && /^https?:/.test(t.link.href) ? ` (${t.link.href})` : ''}`);
  }
  out.push('');

  const sk = d.skills || {};
  out.push('## Skills {#skills}', '', sk.heading, '', sk.text, '');
  for (const a of sk.agents || []) {
    out.push(`### ${a.name}`, '', fence(a.code, 'bash'), '', plain(a.note), '');
  }
  if (sk.chips) out.push('Example prompts once the skills are installed:', '', ...sk.chips.map((c) => `- ${c.text || c}`), '');
  const skNote = [sk.catalog, sk.note].filter(Boolean).map(plain).join(' ');
  if (skNote) out.push(skNote, '');

  out.push('## Videos {#watch}', '', d.videos_text || '', '');
  for (const vv of d.videos || []) out.push(`- [${vv.title}](${vv.href}): ${vv.text}`);
  out.push('');

  out.push('## Before you build', '');
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
