#!/usr/bin/env node
// House rules for the site copy and the files around it.
//
// Adapted from microsoft/microsoft-sql scripts/check-house-rules.mjs. It is a
// script rather than inline workflow YAML so that `npm test` and CI run THE SAME
// CHECK. When a gate lives only in the workflow, a contributor can run the local
// test, see green, push, and fail CI on a rule their local run never applied.
// Two definitions of "clean" is one too many.
//
// Several patterns below are assembled from pieces rather than written out. A
// checker that names the thing it bans fails on itself, and an exemption for
// this file would be a hole big enough to drive the next violation through.

import { readdirSync, statSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const EM_DASH = String.fromCharCode(0x2014);

// Internal shorthand that means nothing to a reader here. The rule ids and
// section numbers live in documents in other repositories, so the reference is
// not merely terse, it is unresolvable. Say the rule in words instead.
const SHORTHAND = [
  { re: /\b(?:VAL|BD|SEC|ST|FM|SCP|LAY|XR)\d{3}\b/, what: 'an internal rule id' },
  { re: /\bSection \d+(?:\.\d+)* of the PRD\b/i, what: 'a section number in a document readers here do not have' },
  { re: /\bADR-\d+\b/, what: 'an internal decision id' },
];

// Absolute claims about what an agent will do. Agents are probabilistic, so a
// promise of certainty is a promise this site cannot keep. Say what the skills
// know and what they are for, not what the agent will invariably do.
//
// Narrowed to lines that also mention an agent or a skill, because these words
// are ordinary English elsewhere ("the free amount always renews monthly" is a
// billing fact, not a claim about a model).
const ABSOLUTE = ['alw' + 'ays', 'guarant' + 'eed', 'guarant' + 'ees', 'never fa' + 'ils', '100% of the ti' + 'me'];
const AGENT_CONTEXT = /\b(agent|agents|skill|skills|Claude|Copilot|Codex|Cursor)\b/i;

// Preview accuracy. This product line is in preview, so a word that implies
// general availability is a factual error, not a style choice.
const GA_CLAIMS = [
  { re: new RegExp('\\bgener' + 'ally avail' + 'able\\b', 'i'), what: 'implies general availability' },
  { re: new RegExp('\\b(?:now|is) ' + 'GA\\b', 'i'), what: 'implies general availability' },
];

// What this repository authors. Naming ours rather than excluding theirs means a
// vendored tree added later does not silently start being linted, and an
// exclusion list cannot go stale without anyone noticing.
const ROOTS = [
  'index.md', 'llms.txt', 'prompts.md', 'for-agents.md', 'build',
  'README.md', '_config.yml',
  '_includes', '_layouts', 'assets', 'scripts', 'docs',
  '.github/workflows',
];

const SKIP_DIRS = new Set(['node_modules', '.git', '_site', 'vendor']);

function* walk(p) {
  if (!existsSync(p)) return;
  if (statSync(p).isFile()) { yield p; return; }
  for (const name of readdirSync(p)) {
    if (SKIP_DIRS.has(name)) continue;
    yield* walk(join(p, name));
  }
}

const findings = [];
let scanned = 0;

for (const root of ROOTS) {
  for (const file of walk(root)) {
    if (/\.(png|jpg|jpeg|gif|svg|ico|woff2?|pdf)$/i.test(file)) continue;
    scanned++;
    const text = readFileSync(file, 'utf8');
    text.split('\n').forEach((line, i) => {
      const at = { file, line: i + 1 };

      if (line.includes(EM_DASH)) {
        findings.push({ ...at, why: 'em-dash character' });
      }
      for (const s of SHORTHAND) {
        const m = s.re.exec(line);
        if (m) findings.push({ ...at, why: `"${m[0]}" is ${s.what}` });
      }
      if (AGENT_CONTEXT.test(line)) {
        for (const word of ABSOLUTE) {
          if (new RegExp(`\\b${word}\\b`, 'i').test(line)) {
            findings.push({ ...at, why: `"${word}" is an absolute claim about agent behavior` });
          }
        }
      }
      for (const g of GA_CLAIMS) {
        const m = g.re.exec(line);
        if (m) findings.push({ ...at, why: `"${m[0]}" ${g.what}` });
      }
    });
  }
}

// A scan that examines nothing must not report success. This exact failure has
// happened in the repository this check came from: an unquoted shell variable
// meant the gate scanned a single nonexistent path and passed.
if (scanned === 0) {
  console.error('x house rules scanned 0 files. That is a broken check, not a clean tree.');
  process.exit(1);
}

if (findings.length) {
  console.error(`${findings.length} house rule violation(s):`);
  for (const f of findings) console.error(`  x ${f.file}:${f.line}  ${f.why}`);
  console.error('');
  console.error('Em-dashes: use a comma, a colon, or a full stop.');
  console.error('Absolute claims: say what the skills know, not what the agent will invariably do.');
  console.error('Preview wording: this product line is in preview. Do not imply general availability.');
  console.error('Internal ids: say the rule in words. The document that defines the id lives in');
  console.error('another repository, so a reader here has nothing to look it up in.');
  process.exit(1);
}
console.log(`house rules OK, ${scanned} files scanned`);
