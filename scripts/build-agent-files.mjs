#!/usr/bin/env node
// Generates the agent-facing half of the site:
//
//   1. A .md twin next to every .html page, so `curl <page>.md` returns the
//      source the page was built from.
//   2. llms-full.txt, the whole site concatenated into one document.
//   3. sitemap.md, every page with its title, description and twin, and a
//      sitemap.xml whose URLs drop .html and carry each page's last commit
//      date, so `<page URL>.md` finds the twin and agents know what is fresh.
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
import { execFileSync } from 'node:child_process';
import yaml from 'js-yaml';

const SITE = '_site';
// 404.md is the not-found page: no twin, and not part of the site's content.
const SKIP_FILES = new Set(['README.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md', '404.md']);
const SKIP_DIRS = new Set(['_site', '_includes', '_layouts', '__pycache__', 'docs', 'runs', 'scripts', 'node_modules', '.github', '.git', 'assets', 'vendor', '.jekyll-cache', 'outputs', 'eval']);

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

// One way to get a database (Get a database running): its setup dialog, every
// route, with every command and the agent prompt, so an agent reading the twin
// can follow either.
function setupOption(o, labels, skills) {
  const out = [`### ${o.title}${o.pill ? ` (${o.pill})` : ''}`, '', o.card, '', o.summary, ''];
  if (o.vscode) {
    out.push(`${labels.vscode || 'Set it up in VS Code'}. ${plain(o.vscode.text)} ${labels.vscode_need || ''}`.trim(), '');
    out.push(`- ${labels.vscode_open || 'Open in VS Code'}: vscode://ms-mssql.mssql/deploy?type=${o.vscode.type}&source=azure-sql-dev-hub`);
    if (labels.vscode_get_href) out.push(`- ${labels.vscode_get || 'Get the extension'}: ${labels.vscode_get_href}`);
    out.push('');
  }
  out.push(`${labels.manual || 'Set it up yourself'}:`, '');
  if (o.engines && o.engines.length) {
    const [first, ...rest] = o.engines;
    out.push(`The commands use ${plain(first.use)}. Other engines' full commands follow the steps.`, '');
    for (const e of o.engines) out.push(`- ${e.name}: ${plain(e.note)}`);
    out.push('');
  }
  for (const [i, st] of (o.steps || []).entries()) {
    out.push(`${i + 1}. ${st.title}. ${plain(st.text)}`, '');
    if (st.link) out.push(`${st.link.label}: ${st.link.href}`, '');
    if (st.code) out.push(fence(st.code, /^SELECT/.test(st.code) ? 'sql' : 'bash'), '');
  }
  if (o.engines) {
    const all = (o.steps || []).map((st) => st.code).filter(Boolean).join('\n\n');
    for (const e of o.engines.slice(1)) {
      const code = (e.swap || []).reduce((c, [from, to]) => c.split(from).join(to), all);
      out.push(`With ${e.name}:`, '', fence(code, 'bash'), '');
    }
  }
  if (o.free) {
    out.push(`${o.free.title}:`, '', ...o.free.tiles.map(([k, v, u]) => `- ${k}: ${v}${u ? ` ${u}` : ''}`), ...(o.free.notes || []).map((n) => `- ${n}`), '');
  }
  if (o.agent) {
    out.push(`${labels.agent || 'Set it up with your coding agent'}.${o.agent.text ? ` ${plain(o.agent.text)}` : ''}`, '');
    if (skills && skills.skills_code) out.push(`${skills.skills_title}: ${skills.skills_text}`, '', fence(skills.skills_code, 'bash'), '');
    out.push(`> ${o.agent.prompt}`, '');
    if (o.agent.check) out.push(plain(o.agent.check), '');
  }
  for (const l of o.links || []) out.push(`- ${l.label}: ${twinHref(l.href)}`);
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
  if (h.agents) out.push(`Works with ${sentenceList(h.agents)}.`, '');

  const v = d.demo || {};
  if (v.title) out.push(`## ${v.title}`, '', v.sub, '');

  out.push(`## ${d.setup_heading || 'Get a database running'} {#get-running}`, '', d.setup_text || '', '');
  for (const o of d.setup || []) out.push(...setupOption(o, d.setup_labels || {}, d.template_inside));
  if (d.then) out.push(`Then: ${d.then.from} to ${d.then.to}. ${d.then.note}`, '');

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
      for (const para of t.description || []) out.push(para, '');
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

  if (d.tools && d.tools.length) {
    out.push(`## ${d.tools_heading} {#tools}`, '');
    for (const tool of d.tools) {
      out.push(`### ${tool.title}`, '', plain(tool.text), '', `[${tool.label}](${tool.href})`, '');
    }
  }

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

// sitemap.md: the pages an agent can read, each with its Markdown twin. Links
// are relative to this file at the site root, so they hold under any baseurl.
const mapLines = [
  `# ${config.title}: sitemap`,
  '',
  `> ${String(config.description || '').trim().replace(/\s+/g, ' ')}`,
  '',
  'Every page on this site, linked to its Markdown version. The whole site in one file is at llms-full.txt.',
  '',
];
for (const file of pages) {
  const { data } = splitFrontMatter(readFileSync(file, 'utf8'));
  const title = file === 'index.md' ? `${config.title} (home page)` : data.head_title || data.title || file;
  mapLines.push(`- [${title}](${file})${data.description ? `: ${String(data.description).trim()}` : ''}`);
}
writeFileSync(join(SITE, 'sitemap.md'), mapLines.join('\n') + '\n', 'utf8');
console.log(`  sitemap.md     ${pages.length} page(s)`);

// sitemap.xml, from jekyll-sitemap: drop .html from each URL and add the date
// of the last commit that touched the page's source. GitHub Pages serves
// /build/x from build/x.html, and the twin sits at /build/x.md, so a client
// that appends .md to a sitemap URL finds it. Without git history (a shallow
// clone, or no git), a page gets today's date.
const sitemapFile = join(SITE, 'sitemap.xml');
if (existsSync(sitemapFile)) {
  const today = new Date().toISOString().slice(0, 10);
  const lastCommit = (src) => {
    try {
      return execFileSync('git', ['log', '-1', '--format=%cs', '--', src], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim() || null;
    } catch { return null; }
  };
  // The loc carries the site's url and baseurl; drop leading segments until
  // the rest names a source file in this repository.
  const sourceFor = (loc) => {
    const segments = new URL(loc).pathname.split('/').filter(Boolean);
    const trailing = loc.endsWith('/');
    for (let i = 0; i <= segments.length; i++) {
      const rest = segments.slice(i).join('/');
      const candidates = rest === '' || trailing ? [join(rest, 'index.md'), join(rest, 'index.html')] : [rest.replace(/\.html$/, '.md'), rest];
      const hit = candidates.find((c) => existsSync(c) && statSync(c).isFile());
      if (hit) return hit;
    }
    return null;
  };
  let dated = 0;
  const xml = readFileSync(sitemapFile, 'utf8').replace(/<url>([\s\S]*?)<\/url>/g, (block, inner) => {
    const loc = (/<loc>([^<]+)<\/loc>/.exec(inner) || [])[1];
    if (!loc) return block;
    const src = sourceFor(loc);
    const date = (src && lastCommit(src)) || today;
    if (src && date !== today) dated++;
    let next = inner.replace(`<loc>${loc}</loc>`, `<loc>${loc.replace(/\.html$/, '')}</loc>`);
    if (!/<lastmod>/.test(next)) next = next.replace('</loc>', `</loc>\n<lastmod>${date}</lastmod>`);
    return `<url>${next}</url>`;
  });
  writeFileSync(sitemapFile, xml, 'utf8');
  console.log(`  sitemap.xml    URLs without .html, ${dated} dated from git`);
}
