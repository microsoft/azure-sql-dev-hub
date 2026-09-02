# Azure SQL Hub

The Azure SQL Dev Hub is one front door for developers and AI agents to start
building on Azure SQL. It points at three ways in: the Azure SQL Database engine
running locally in a container, a free database in the Microsoft Azure cloud, and
the agent skills that let an AI coding agent do the setup for you.

## Live site

Not deployed yet. Once GitHub Pages is enabled for this repository the site will
be at `https://microsoft.github.io/azure-sql-dev-hub/`. Enabling it is a one-time
setting: **Settings > Pages > Source > GitHub Actions**. The deploy workflow is
already in this repository and runs on every push to `main`.

## How it works

Static markdown and Jekyll, built and deployed by GitHub Actions. There is no
JavaScript framework, and no content on this site needs JavaScript to be read.

Every page is authored as a `.md` file, and the build publishes each one twice:
once as the HTML page and once as its markdown source at the same path with `.md`
appended. So `/index.html` has a twin at `/index.md`, and every page links to its
own source with `<link rel="alternate" type="text/markdown">`. Two more files
serve agents specifically: `/llms.txt` is a short description with a linked index
of the site, and `/llms-full.txt` is every page concatenated, generated at build
time by `scripts/build-agent-files.mjs`.

The tabs and copy buttons are progressive enhancement. With JavaScript blocked,
tab panels render as ordinary stacked headings and every command is still there
to select and copy by hand.

## How to contribute

Edit the `.md` file for the page, open a pull request, and let CI check it. House
rules run on every pull request and are the same command you can run locally:

```bash
npm install
npm test
```

To preview the site:

```bash
bundle install
bundle exec jekyll serve --baseurl ""
```

The house rules cover things a reviewer should not have to catch by eye: no
em-dashes, no absolute claims about what an AI agent will do, and no wording that
overstates a preview product's release status. See
`scripts/check-house-rules.mjs` for the current list and the reasoning.

Anchor ids on the home page (`start`, `connect`, `build`, `skills`, `samples`)
are permanent. Add sections, never rename these.

## Repo map

| Path | What it is |
| --- | --- |
| `index.md` | The home page. Hero and path-card copy live in its front matter; the rest is the body. |
| `llms.txt` | Short site description and linked index of every page, for agents. |
| `_config.yml` | Jekyll config, shared links, the permanent nav anchors, and the analytics switch. |
| `_layouts/` | `home.html` for the front page, `page.html` for everything else. |
| `_includes/` | Head, nav, footer, and the analytics loader. |
| `assets/css/main.scss` | Design tokens and all styling. Tokens are carried over from the container site. |
| `assets/js/main.js` | Copy buttons, tabs, and the analytics event helper. All optional to the reader. |
| `scripts/check-house-rules.mjs` | The CI house-rules check. Also `npm test`. |
| `scripts/build-agent-files.mjs` | Writes the `.md` twins and `llms-full.txt` into the built site. |
| `docs/DECISIONS.md` | One dated line per irreversible or debatable choice. |
| `.github/workflows/` | `ci.yml` checks pull requests, `pages.yml` builds and deploys. |

## Who owns it

The Azure SQL team. For anything about this site, including a broken link, wrong
copy, or a page you expected to find: [open an issue](https://github.com/microsoft/azure-sql-dev-hub/issues).
For the container itself, use the
[container repository](https://github.com/microsoft/azure-sql-database-container).
