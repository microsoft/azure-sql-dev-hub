# Azure SQL Developer Hub

The Azure SQL Dev Hub is one front door for developers and AI agents to start
building on Azure SQL. It gives a person the shortest useful action (a
quickstart command, a scenario page, a prompt) and gives an agent the current
machine-readable context behind it, generated from the same content.

## Live site

<https://didactic-adventure-jgqz4oz.pages.github.io/>

The repository is internal, so anyone in the Microsoft enterprise can view the
site after signing in to GitHub; the generated domain is what GitHub assigns to
a privately published Pages site. If this repository is ever made public the
site moves to `https://microsoft.github.io/azure-sql-dev-hub/`, and the deploy
workflow picks that up on its own without a config edit.

Deploys run on every push to `main`.

## How it works

Static markdown and Jekyll, built and deployed by GitHub Actions. There is no
JavaScript framework, and no content on this site needs JavaScript to be read:
tabs render stacked and copy buttons disappear, but every command stays on the
page.

Every page is authored as a `.md` file and published twice: once as HTML and
once as its own source at the same path with `.md` appended. So `/build/rag.html`
has a twin at `/build/rag.md`, and every page links to its source with
`<link rel="alternate" type="text/markdown">`. Two more files serve agents:
`/llms.txt` indexes the site, and `/llms-full.txt` concatenates it, both
generated at build time by `scripts/build-agent-files.mjs`. The `/for-agents`
page documents all of it.

Telemetry goes through one `track()` function in `assets/js/main.js`. For the
demo it logs to the console; it fans out to Application Insights the moment
`_config.yml` carries a connection string.

## How to contribute

Edit the `.md` file for the page, open a pull request, and let CI check it:

```bash
npm install
npm test
```

To preview the site: `bundle install && bundle exec jekyll serve --baseurl ""`.

House rules run on every pull request and locally as `npm test`: no em-dashes,
no absolute claims about what an AI agent will do, and no wording that
overstates a preview product's release status. CI also builds the site, checks
every internal link, and fails if the agent-facing files went missing.

## Repo map

| Path | What it is |
| --- | --- |
| `index.md` | The home page. Section copy lives in its front matter as structured data. |
| `build/*.md` | The six scenario pages: prompt, starter, skill, docs, walkthrough slot. |
| `prompts.md` | The prompt library. |
| `for-agents.md` | Documents every machine-readable surface. |
| `llms.txt` | Site description and linked index of every page, for agents. |
| `_config.yml` | Jekyll config, shared links, and the analytics switch. |
| `_layouts/` | `home`, `scenario`, and `page` layouts. |
| `_includes/` | Head, nav, footer, and the analytics loader. |
| `assets/` | Stylesheet (V8 design system) and the JS for tabs, copy, telemetry. |
| `scripts/` | House rules, agent-files generator, internal link check. |
| `docs/DECISIONS.md` | One dated line per irreversible or debatable choice. |
| `.github/workflows/` | `ci.yml` checks pull requests, `pages.yml` builds and deploys. |

## Who owns it

The Azure SQL team. For anything about this site, including a broken link,
wrong copy, or a page you expected to find:
[open an issue](https://github.com/microsoft/azure-sql-dev-hub/issues). For the
container itself, use the
[container repository](https://github.com/microsoft/azure-sql-database-container).
