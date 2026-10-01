#!/usr/bin/env node

import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import vm from "node:vm";

const mainScript = readFileSync("assets/js/main.js", "utf8");
const telemetryBundle = readFileSync("assets/js/mssql-agent-skills-telemetry.js", "utf8");
const analyticsRouter = readFileSync("_includes/analytics.html", "utf8");
const oneDsInclude = readFileSync("_includes/analytics/one-ds.html", "utf8");
const homeLayout = readFileSync("_layouts/home.html", "utf8");
const pageLayout = readFileSync("_layouts/page.html", "utf8");
const scenarioLayout = readFileSync("_layouts/scenario.html", "utf8");
const navInclude = readFileSync("_includes/nav.html", "utf8");
const footerInclude = readFileSync("_includes/footer.html", "utf8");
const homeContent = readFileSync("index.md", "utf8");
const config = readFileSync("_config.yml", "utf8");

assert.equal(
  existsSync("_includes/analytics/app-insights.html"),
  false,
  "The inactive App Insights include must be removed",
);
assert.ok(
  config.includes("one_ds_instrumentation_key:"),
  "The 1DS key must be configured",
);
assert.ok(
  !config.includes("app_insights_connection_string:"),
  "The inactive App Insights configuration must be removed",
);
assert.ok(
  analyticsRouter.includes("analytics/one-ds.html"),
  "The analytics router must include 1DS",
);
assert.ok(
  !analyticsRouter.includes("analytics/app-insights.html"),
  "The analytics router must not include App Insights",
);
assert.ok(
  oneDsInclude.includes("MssqlAgentSkillsTelemetry"),
  "The 1DS include must initialize the shared browser bundle",
);
assert.ok(
  oneDsInclude.includes("mssqlAgentSkillsTelemetry"),
  "The initialized client must be available to the site router",
);
assert.ok(
  telemetryBundle.includes("Generated from AgentSkills telemetry/browser-global.mjs"),
  "The browser telemetry asset must be generated from AgentSkills",
);
assert.ok(
  telemetryBundle.includes("mobile.events.data.microsoft.com/OneCollector/1.0"),
  "The browser bundle must target OneCollector",
);

const clarityCalls = [];
const oneDsCalls = [];
const context = {
  URL,
  console: { log() {}, warn() {} },
  document: {
    body: {
      getAttribute(name) {
        return name === "data-view" ? "mainPage" : null;
      },
    },
    documentElement: { classList: { add() {} } },
    querySelectorAll() {
      return [];
    },
    referrer: "",
  },
  location: {
    origin: "https://microsoft.github.io",
    pathname: "/azure-sql-dev-hub/",
  },
  navigator: {
    language: "en-US",
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
  },
  setTimeout,
  window: {
    clarity(...args) {
      clarityCalls.push(args);
    },
    mssqlAgentSkillsTelemetry: {
      track(name, properties, measurements) {
        oneDsCalls.push({ name, properties, measurements });
      },
    },
  },
};

vm.runInNewContext(mainScript, context);
context.window.trackHubEvent(
  "site/action",
  {
    action: "contentCopied",
    actionLocation: "skill-card",
    contentId: "javascript-app",
    contentType: "prompt",
  },
  { clarityEvent: "copy_prompt_javascript-app" },
);

assert.deepEqual(
  oneDsCalls.map(({ name }) => name),
  ["site/action", "site/action"],
  "1DS must receive the normalized page-view and interaction events",
);
assert.equal(
  oneDsCalls[0].properties.view,
  "mainPage",
  "1DS events must include the stable view",
);
assert.equal(
  oneDsCalls[0].properties.pagePath,
  "/azure-sql-dev-hub/",
  "1DS events must include the path without query or fragment",
);
assert.equal(
  oneDsCalls[0].properties.browserFamily,
  "edge",
  "1DS events must use coarse browser classification",
);
assert.equal(
  oneDsCalls[1].measurements.count,
  1,
  "Interaction events must carry the required count measurement",
);
assert.deepEqual(
  clarityCalls.filter(([operation]) => operation === "event"),
  [
    ["event", "site/action"],
    ["event", "site/action"],
    ["event", "copy_prompt_javascript-app"],
  ],
  "Clarity must receive normalized events and retained item-level aliases",
);

const templateSources = [
  ["home layout", homeLayout],
  ["scenario layout", scenarioLayout],
  ["navigation", navInclude],
  ["footer", footerInclude],
];
const requiredActionProperties = {
  contentCopied: ["action-location", "content-id", "content-type"],
  contentOpened: ["action-location", "content-id", "content-type"],
  copyPrompt: ["action-location", "scenario"],
  harnessSelected: ["action-location", "harness-id"],
  mediaEngaged: ["content-id", "media-action"],
  outboundClicked: ["destination-type"],
  pathSelected: ["path-id"],
  viewPrompt: ["action-location", "scenario"],
};
for (const [sourceName, source] of templateSources) {
  const eventElements = [...source.matchAll(/<[^>]*data-event="([^"]+)"[^>]*>/gs)];
  assert.ok(eventElements.length > 0, `${sourceName} must contain telemetry events`);
  for (const [, eventName] of eventElements) {
    assert.ok(
      eventName === "site/action",
      `${sourceName} contains non-normalized event ${eventName}`,
    );
  }
  for (const [element, eventName] of eventElements) {
    const action = /data-event-action="([^"]+)"/.exec(element)?.[1];
    assert.ok(action, `${sourceName} ${eventName} is missing action`);
    for (const property of requiredActionProperties[action] ?? []) {
      assert.ok(
        element.includes(`data-event-${property}=`),
        `${sourceName} ${eventName} is missing ${property}`,
      );
    }
  }
}

const requiredWiring = [
  [homeLayout, 'data-event-action="contentCopied"', "home copy actions"],
  [homeLayout, 'data-event-harness-id="{{ a.key }}"', "harness identifiers"],
  [homeLayout, 'data-event-scenario="{{ s.slug }}"', "scenario identifiers"],
  [scenarioLayout, 'data-event-scenario="{{ scenario_id }}"', "scenario prompt"],
  [scenarioLayout, 'data-event-content-type="skill-install"', "scenario skill install"],
  [navInclude, 'data-event-destination-type="feedback"', "feedback destination"],
  [footerInclude, 'data-event-destination-type="github"', "repository destination"],
  [homeContent, "key: connect_node_passwordless", "stable suggested ask keys"],
  [homeContent, "key: vscode-copilot", "normalized Copilot harness ID"],
  [homeContent, "event:", "obsolete front-matter event names", true],
  [pageLayout, 'data-view="scenarioPage"', "scenario page view"],
  [pageLayout, 'data-scenario="{{ page.name', "scenario page identity"],
  [pageLayout, 'data-view="{{ page.name', "content page views"],
  [homeLayout, 'data-view="mainPage"', "main page view"],
  [scenarioLayout, 'data-view="scenarioPage"', "scenario page view"],
];

for (const [source, marker, interaction, mustBeAbsent] of requiredWiring) {
  assert.equal(
    source.includes(marker),
    !mustBeAbsent,
    `${mustBeAbsent ? "Found" : "Missing"} telemetry wiring for ${interaction}`,
  );
}

console.log("telemetry contract OK");
