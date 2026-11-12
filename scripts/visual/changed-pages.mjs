#!/usr/bin/env node
// Which pages the visual diff should capture: only what this PR changed.
// Compares the base build with the PR build, file by file, and prints a JSON
// list of page paths.
//
// - A page whose HTML differs is captured.
// - If a shared file changed (CSS, JS, images, fonts), every page could look
//   different, so the key pages are captured too.
// - Nothing changed, nothing captured: a PR that leaves the site alone gets no
//   screenshots, so it cannot report differences it did not make.
//
//   node scripts/visual/changed-pages.mjs <base-site> <pr-site>

import { readdirSync, statSync, readFileSync, existsSync } from 'node:fs';
import { join, relative, extname } from 'node:path';

const [baseDir, prDir] = process.argv.slice(2);
const KEY_PAGES = ['/', '/build/javascript-app.html', '/prompts.html', '/privacy.html'];
const MAX_PAGES = 10;
// Not rendered in a browser, so a change here cannot change a screenshot.
const NOT_VISUAL = new Set(['.md', '.txt', '.xml', '.json', '.map']);

function* files(dir, root = dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* files(p, root);
    else yield relative(root, p).replace(/\\/g, '/');
  }
}
// Each build carries the address it is served at (base on 8081, PR on 8080)
// in absolute URLs such as og:url, which says nothing about the page itself.
const TEXT = new Set(['.html', '.css', '.js', '.svg']);
const BASE_ORIGIN = process.env.BASE_ORIGIN || 'http://localhost:8081';
const PR_ORIGIN = process.env.PR_ORIGIN || 'http://localhost:8080';
function same(rel) {
  if (!existsSync(join(baseDir, rel))) return false;
  const a = readFileSync(join(baseDir, rel));
  const b = readFileSync(join(prDir, rel));
  if (!TEXT.has(extname(rel))) return a.equals(b);
  return a.toString('utf8').split(BASE_ORIGIN).join(PR_ORIGIN) === b.toString('utf8');
}

const pages = [];
let shared = false;
for (const rel of files(prDir)) {
  if (NOT_VISUAL.has(extname(rel)) || same(rel)) continue;
  if (extname(rel) === '.html') pages.push('/' + rel.replace(/(^|\/)index\.html$/, '$1'));
  else shared = true;
  console.error(`changed: ${rel}`);
}
const list = [...new Set([...(shared ? KEY_PAGES : []), ...pages.sort()])].slice(0, MAX_PAGES);
console.log(JSON.stringify(list));
