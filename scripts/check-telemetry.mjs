#!/usr/bin/env node

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const mainScript = readFileSync('assets/js/main.js', 'utf8');
const homeLayout = readFileSync('_layouts/home.html', 'utf8');
const scenarioLayout = readFileSync('_layouts/scenario.html', 'utf8');
const homeContent = readFileSync('index.md', 'utf8');

const clarityCalls = [];
const appInsightsCalls = [];
const context = {
  console: { log() {} },
  document: {
    documentElement: { classList: { add() {} } },
    querySelectorAll() { return []; },
  },
  location: { pathname: '/build/javascript-app.html' },
  navigator: {},
  setTimeout,
  window: {
    clarity(...args) { clarityCalls.push(args); },
    appInsights: {
      trackEvent(event, properties) {
        appInsightsCalls.push({ event, properties });
      },
    },
  },
};

vm.runInNewContext(mainScript, context);
context.window.trackHubEvent(
  'copy_prompt',
  { scenario_id: 'javascript-app', source: 'home' },
  { clarityEvent: 'copy_prompt_javascript-app' },
);

assert.deepEqual(
  clarityCalls.filter(([operation]) => operation === 'event'),
  [
    ['event', 'copy_prompt'],
    ['event', 'copy_prompt_javascript-app'],
  ],
  'Clarity must receive aggregate and item-level custom events',
);
assert.deepEqual(
  appInsightsCalls.map(({ event }) => event.name),
  ['copy_prompt'],
  'Application Insights must preserve the existing aggregate event name',
);
assert.equal(
  appInsightsCalls[0].properties.scenario_id,
  'javascript-app',
  'Application Insights must retain event properties',
);

const requiredWiring = [
  [homeLayout, 'data-clarity-event="copy_prompt_{{ s.slug }}"', 'prompt copy'],
  [homeLayout, 'data-clarity-event="view_prompt_{{ s.slug }}"', 'prompt view'],
  [homeLayout, 'data-clarity-event="copy_skill_install_{{ a0.key }}"', 'initial harness install'],
  [homeLayout, "copyEl.setAttribute('data-clarity-event','copy_skill_install_'+agent)", 'selected harness install'],
  [homeLayout, 'data-clarity-event="copy_ask_{{ c.key }}"', 'suggested ask'],
  [homeLayout, 'data-clarity-event="browse_skills"', 'skills catalog'],
  [scenarioLayout, "assign scenario_id = page.name | remove: '.md' | remove: '.html'", 'scenario identifier'],
  [scenarioLayout, 'data-clarity-event="copy_prompt_{{ scenario_id }}"', 'scenario prompt copy'],
  [scenarioLayout, 'data-clarity-event="view_prompt_{{ scenario_id }}"', 'scenario prompt view'],
  [homeContent, 'key: connect_node_passwordless', 'stable suggested ask keys'],
];

for (const [source, marker, interaction] of requiredWiring) {
  assert.ok(source.includes(marker), `Missing item-level Clarity event for ${interaction}`);
}

console.log('telemetry contract OK');
