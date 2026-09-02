#!/usr/bin/env node
// Generates the two things this site owes a reader that is not a browser:
//
//   1. A .md twin next to every .html page, so `curl <page>.md` returns the
//      source the page was built from.
//   2. llms-full.txt, the whole site concatenated into one document.
//
// Runs after `jekyll build`, writing into _site. It reads the same .md sources
// Jekyll just consumed, so the twin cannot drift from the page: there is one
// source file, published twice.
//
// The home page keeps its hero and path-card copy in front matter, because the
// layout needs it as structured data. That copy is real page content, so it is
// rendered back into markdown here rather than dropped. Everything else is the
// body, verbatim.

import { readdirSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import yaml from 'js-yaml';

const SITE = '_site';
const SKIP = new Set(['README.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md']);

if (!existsSync(SITE)) {
  console.error(`x ${SITE} does not exist. Run "bundle exec jekyll build" first.`);
  process.exit(1);
}

function splitFrontMatter(raw) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(raw);
  if (!m) return { data: {}, body: raw };
  return { data: yaml.load(m[1]) || {}, body: raw.slice(m[0].length) };
}

// Front-matter copy, rendered as the markdown it would have been if the layout
// had not needed it as data.
function heroToMarkdown(data) {
  const out = [];
  if (data.hero) {
    out.push(`# ${data.hero.headline}`, '', data.hero.subline, '');
    if (data.hero.command) {
      out.push('Quickstart:', '', '```bash', data.hero.command, '```', '');
    }
    if (data.hero.trust) out.push(data.hero.trust, '');
  }
  if (Array.isArray(data.paths) && data.paths.length) {
    out.push('## Ways to start', '');
    for (const p of data.paths) {
      out.push(`### ${p.title}${p.badge ? ` (${p.badge})` : ''}`, '', p.what, '');
      for (const f of p.facts || []) out.push(`- ${f}`);
      out.push('');
    }
  }
  return out.join('\n');
}

// Liquid the body may contain. These are site-config links, so the twin resolves
// them the same way the page did instead of publishing raw template syntax.
function resolveLiquid(body, config) {
  return body.replace(/\{\{\s*site\.([a-z0-9_]+)\s*\}\}/gi, (whole, key) =>
    Object.prototype.hasOwnProperty.call(config, key) ? String(config[key]) : whole
  );
}

// Kramdown inline attribute lists mark up the HTML. They are not prose, and a
// reader of the markdown has no use for them.
function stripAttributeLists(body) {
  return body
    .split('\n')
    .filter((line) => !/^\{:\s*\.[a-z0-9-\s.]+\}\s*$/i.test(line))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n');
}

const config = yaml.load(readFileSync('_config.yml', 'utf8')) || {};
const pages = readdirSync('.').filter((f) => f.endsWith('.md') && !SKIP.has(f));

if (pages.length === 0) {
  console.error('x found no page sources to publish. That is a broken build, not an empty site.');
  process.exit(1);
}

const parts = [];

for (const file of pages) {
  const raw = readFileSync(file, 'utf8');
  const { data, body } = splitFrontMatter(raw);
  const markdown = [heroToMarkdown(data), stripAttributeLists(resolveLiquid(body, config))]
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
