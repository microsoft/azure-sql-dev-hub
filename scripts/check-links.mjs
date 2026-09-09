#!/usr/bin/env node
// Internal link check over the built site. Runs after `jekyll build` and the
// agent-files generator, so it validates what will actually deploy: every
// internal href and src in the HTML resolves to a real file, and every
// same-page anchor points at an id that exists.
//
// External links are deliberately out of scope here: CI must not fail on
// someone else's outage. They are verified by hand when added.

import { readdirSync, statSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';

const SITE = '_site';

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

function idsIn(html) {
  const ids = new Set();
  const re = /\sid="([^"]+)"/g;
  let m;
  while ((m = re.exec(html))) ids.add(m[1]);
  return ids;
}

// GitHub Pages serves /foo from foo.html, /dir/ from dir/index.html.
function targetExists(path) {
  const clean = path.replace(/^\//, '');
  if (clean === '') return existsSync(join(SITE, 'index.html'));
  return (
    existsSync(join(SITE, clean)) ||
    existsSync(join(SITE, clean + '.html')) ||
    existsSync(join(SITE, clean, 'index.html'))
  );
}

const idCache = new Map();
function idsOf(sitePath) {
  if (!idCache.has(sitePath)) {
    idCache.set(sitePath, existsSync(sitePath) ? idsIn(readFileSync(sitePath, 'utf8')) : new Set());
  }
  return idCache.get(sitePath);
}

const problems = [];
let checked = 0;

for (const file of htmlFiles(SITE)) {
  const html = readFileSync(file, 'utf8');
  const ownIds = idsIn(html);
  const re = /\s(?:href|src)="([^"]+)"/g;
  let m;
  while ((m = re.exec(html))) {
    const url = m[1];
    if (/^(?:https?:|mailto:|data:|javascript:)/.test(url)) continue;
    checked++;

    const [pathPart, hash] = url.split('#');

    if (pathPart === '') {
      // same-page anchor
      if (hash && !ownIds.has(hash)) {
        problems.push(`${file}: anchor #${hash} has no matching id on the page`);
      }
      continue;
    }

    const path = pathPart.split('?')[0];
    let resolved;
    if (path.startsWith('/')) {
      resolved = path;
    } else {
      const dir = dirname(file).slice(SITE.length).replace(/\\/g, '/');
      resolved = (dir + '/' + path).replace(/\/{2,}/g, '/');
    }

    if (!targetExists(resolved)) {
      problems.push(`${file}: broken link ${url}`);
      continue;
    }
    if (hash) {
      const clean = resolved.replace(/^\//, '');
      const candidates = [join(SITE, clean), join(SITE, clean + '.html'), join(SITE, clean, 'index.html'), join(SITE, clean === '' ? 'index.html' : clean)];
      const target = candidates.find((c) => existsSync(c) && statSync(c).isFile());
      if (target && target.endsWith('.html') && !idsOf(target).has(hash)) {
        problems.push(`${file}: link ${url} points at an id that does not exist on the target`);
      }
    }
  }
}

if (checked === 0) {
  console.error('x link check examined 0 links. That is a broken check, not a clean site.');
  process.exit(1);
}
if (problems.length) {
  console.error(`${problems.length} broken internal link(s):`);
  for (const p of problems) console.error(`  x ${p}`);
  process.exit(1);
}
console.log(`links OK, ${checked} internal references checked`);
