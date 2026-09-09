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
// section data, a scenario page's prompt and starter) get that data rendered
// back into markdown here, because it is real page content, not metadata.

import { readdirSync, statSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import yaml from 'js-yaml';

const SITE = '_site';
const SKIP_FILES = new Set(['README.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md']);
const SKIP_DIRS = new Set(['_site', '_includes', '_layouts', 'docs', 'scripts', 'node_modules', '.github', '.git', 'assets', 'vendor', '.jekyll-cache']);

// Reading order for llms-full.txt. Anything discovered but not listed appends
// alphabetically, so a new page is never silently dropped.
const ORDER = [
  'index.md',
  'build/start-database.md',
  'build/connect-app.md',
  'build/rag.md',
  'build/multi-tenant.md',
  'build/query-performance.md',
  'build/local-to-cloud.md',
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

// Liquid the sources may contain. The twin resolves it the same way the page
// did instead of publishing raw template syntax. Handles {{ site.key }},
// {{ 'path' | relative_url }}, and {{ 'path' | absolute_url }}.
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

// Kramdown inline attribute lists mark up the HTML, not the prose.
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

// The home page's structured front matter, rendered back into markdown.
function homeToMarkdown(d) {
  const out = [];
  const h = d.hero || {};
  out.push(`# ${h.headline} ${h.headline_accent}`.trim(), '', h.subline, '');
  if (h.agents) out.push(`Works with ${h.agents.join(', ')}.`, '');

  out.push('## Get running {#get-running}', '',
    'Choose the path that matches your workflow.', '');
  for (const m of d.quickstart || []) {
    out.push(`### ${m.name}: ${m.title}`, '', m.desc, '', fence(m.code, 'bash'), '');
    if (m.prompt) out.push('Then ask:', '', fence(m.prompt, 'text'), '');
    out.push(`${m.link.label.replace(/\s*→\s*$/, '')}: ${m.link.href}`, '');
  }

  const c = d.continuity || {};
  out.push('## Local to cloud {#continuity}', '', c.heading, '', c.text, '',
    'Local environment:', '', fence(c.local_env, 'text'), '',
    'In Azure:', '', fence(c.azure_env, 'text'), '',
    'Same application code. Only the connection target changes.', '');

  out.push('## Build {#build}', '', 'Start with the job you need done:', '');
  for (const s of d.scenarios || []) {
    out.push(`- [${s.title}](build/${s.slug}.md): ${s.blurb}`);
  }
  out.push('');

  out.push('## Prompt library {#prompts}', '');
  for (const p of d.prompts_featured || []) {
    out.push(`### ${p.title} (${p.tag})`, '', p.blurb, '', fence(p.prompt, 'text'), '');
  }
  out.push('The full library is at [prompts.md](prompts.md).', '');

  const sk = d.skills || {};
  out.push('## Skills {#skills}', '', sk.heading, '', sk.text, '');
  for (const a of sk.agents || []) {
    out.push(`### ${a.name}`, '', a.blurb, '', fence(a.code, 'text'), '');
    if (a.alt_code) out.push(fence(a.alt_code, 'bash'), '');
  }
  if (sk.chips) out.push(`Skills include: ${sk.chips.map((x) => '`' + x + '`').join(' ')}`, '');
  if (sk.mcp_note) out.push(sk.mcp_note, '');

  const e = d.existing || {};
  out.push('## Already have Azure SQL data? {#existing}', '', e.heading, '', e.text, '',
    fence(e.sql, 'sql'), '');
  return out.join('\n');
}

// A scenario page's structured front matter, rendered ahead of its body.
function scenarioToMarkdown(d) {
  const out = [`# ${d.title}`, '', d.intro, '',
    '## Prompt', '', fence(d.prompt, 'text'), '',
    '## Starter', '', fence(d.starter.code, d.starter.language || ''), '',
    '## Skill', '', d.skill.note, ''];
  if (d.skill.install) out.push(fence(d.skill.install, 'bash'), '');
  out.push(`## Docs`, '', `${d.docs.label}: ${d.docs.href}`, '',
    '## Walkthrough', '', 'Video: coming soon.', '');
  return out.join('\n');
}

const config = yaml.load(readFileSync('_config.yml', 'utf8')) || {};
const found = findPages('.', '');
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
  else if (data.layout === 'scenario') head = scenarioToMarkdown(data);
  else if (data.title) head = `# ${data.title}\n`;

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
