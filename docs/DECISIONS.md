# Decisions

One dated line per irreversible or debatable choice. Append to this file in any
pull request that makes one. Do not rewrite past entries: if a decision is
reversed, add a new line saying so and why.

- 2026-09-02: anchor ids `start`, `connect`, `build`, `skills`, `samples` on the home page, permanent. External links, documentation, and agents point at these, so they are chosen once and never renamed.
- 2026-09-02: static Jekyll on GitHub Pages over Docusaurus or any JavaScript framework. Agent readability is the point of this site, and a markdown source that renders itself keeps the page and the machine-readable version from drifting.
- 2026-09-02: every page is a `.md` file published twice, once as HTML and once as its own source at `<page>.md`. One source file, two outputs, so the twin cannot go stale.
- 2026-09-02: home page hero and path-card copy live in `index.md` front matter rather than the body, because the layout needs it as structured data. `scripts/build-agent-files.mjs` renders it back into markdown for the `.md` twin so the twin stays complete.
- 2026-09-02: tabs and copy buttons are progressive enhancement. Panels render as stacked headings with no JavaScript, so no content depends on a script running.
- 2026-09-02: design tokens copied verbatim from the Azure SQL Database container site rather than reinterpreted, so the two properties read as one family. One deliberate difference: azure blue is reserved for interactive elements here, and labels and accents use the cyan or muted ink instead.
- 2026-09-02: the nav renders only anchors whose sections exist. The full permanent id list lives in `_config.yml` as `nav_anchors` with a `live` flag. Shipping a nav link that scrolls nowhere was judged worse than a nav that grows in a later pull request.
- 2026-09-02: the home page describes the Azure SQL Database free offer as needing an Azure account and subscription, and does not say "no credit card". The offer documentation lists an Azure account and subscription as prerequisites and makes no claim about payment methods.
- 2026-09-02: Application Insights is wired but disabled, with no connection string. The container site's connection string is public and reusable, but sending this site's traffic to that resource would mix two properties' telemetry with no clean way to separate it later. This hub gets its own resource before analytics is switched on.
- 2026-09-02: the house-rules check is a script run by both CI and `npm test`, not inline workflow YAML, so a local green run and a CI green run mean the same thing.
- 2026-09-02: the deploy workflow derives `url` and `baseurl` from the Pages API at build time rather than reading them from `_config.yml`. This repository is private, so Pages publishes to a generated `*.pages.github.io` domain at the root instead of `microsoft.github.io/azure-sql-dev-hub`. Hardcoding either value would break `absolute_url`, which is what `llms.txt` and the `og:url` tag are built from, and would need another edit if the repository is made public.
