# Website telemetry implementation

The Azure SQL Developer Hub sends normalized `mssql-agent-skills/` events to the existing
vscode-mssql 1DS/Aria tenant through OneCollector. Microsoft Clarity remains a separate provider
for behavioral analytics.

## Shared browser client

The source client and event contract live in the internal ADO `AgentSkills` repository under
`telemetry/`. This public repository consumes a generated, self-contained artifact at:

`assets/js/mssql-agent-skills-telemetry.js`

The bundle is checked in so GitHub Pages does not need access to the internal repository or its npm
feed. Do not edit the generated file directly.

From a workspace containing both repositories, regenerate it with:

```bash
cd /path/to/AgentSkills
npm ci
npm run telemetry:bundle:browser -- \
  --out /path/to/azure-sql-dev-hub/assets/js/mssql-agent-skills-telemetry.js
```

`_includes/analytics/one-ds.html` loads the bundle and creates
`window.mssqlAgentSkillsTelemetry`. `assets/js/main.js` supplies the page and interaction context,
then calls that client's validated `track()` method. Local Jekyll builds use the client's disabled
mode and do not send production events.

## Event markers

Declarative interactions use:

- `data-event="site/action"` for site interactions;
- `data-event-action="<action>"` for the action discriminator;
- `data-event-<property-name>` for allowlisted event properties;
- stable content, harness, path, and destination IDs rather than display text.

The browser client adds `sourceId=azure-sql-dev-hub`. The page layout supplies `view=mainPage` for
the home page. Dedicated scenario pages use `view=scenarioPage`; the scenario slug is sent separately as
`scenario`, for example `scenario=javascript-app`. Prompt interactions use `action=copyPrompt` or
`action=viewPrompt`.

Copy events are emitted only after the clipboard operation succeeds. Copied text, commands, code,
prompts, URLs, and connection strings are never sent.

## Test

```bash
npm test
```

The telemetry check verifies the generated bundle, 1DS initialization, page/context routing,
Clarity fan-out, normalized template markers, required marker properties, and removal of the
inactive conventional Application Insights integration.

## Local preview

Prompt-copy buttons fetch the generated Markdown twin from `_site/build/*.md`. Always use the
combined build so those twins exist:

```bash
npm run build:site
```

That command builds the HTML and then generates the Markdown twins. Serving the output of
`bundle exec jekyll build` alone leaves the HTML pages present but makes prompt-copy requests
return 404.

To intentionally send a local preview to the production 1DS tenant for telemetry validation, use:

```bash
npm run build:site:telemetry
```

The normal `build:site` command uses disabled local telemetry.
