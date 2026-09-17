# Decisions

- 2026-09-16: Keep validation tracking and agent-file documentation in repository docs; remove the For agents page from publishing and human navigation while retaining machine-readable files and alternate links.
- 2026-09-16: Use visual links to existing SQL videos without auto-playing or embedding a player; retain a complete hero without a demo placeholder.

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
- 2026-09-08: the V8 mockup's visual language supersedes the container-inherited tokens from PR 1. Light page, Microsoft blue, Inter, dark surfaces only for code. The owner approved V8 as the design of record; this line supersedes the 2026-09-02 token decision.
- 2026-09-08: the V8 information architecture supersedes the original anchor set. `build` and `skills` remain; `get-running` replaces `start`, which stays as an invisible alias anchor so old links still land; `connect` and `samples` were retired before any nav ever rendered them; `prompts`, `continuity`, and `existing` are new sections. This line supersedes the 2026-09-02 anchor decision.
- 2026-09-08: scenarios are real pages under /build/<slug>.html with .md twins, not modals. A URL an agent can fetch and a person can share is the product thesis; the mockup's modal was a preview stand-in.
- 2026-09-08: the cloud quickstart uses the Azure CLI free-offer command. It is verbatim a documented example in the az sql db create reference, so it is canonical, not invented.
- 2026-09-08: the multi-tenant starter uses the SESSION_CONTEXT predicate pattern from the Row-Level Security documentation rather than the mockup's fragment, which referenced a predicate function it never defined.
- 2026-09-08: no .well-known discovery files. No current artifact defines one: there is no Azure SQL MCP endpoint yet, and llms.txt lives at the site root by convention. Inventing a discovery surface that points at nothing would be worse than absence; /for-agents documents what exists.
- 2026-09-08: telemetry stays behind one track() that logs to the console for the demo and fans out to App Insights when configured. quickstart_start fires only on user interaction, not on page load as in the mockup, so the metric means a person chose a path.
- 2026-09-08: repository visibility changed from private to internal, on the owner's decision, so everyone in the Microsoft enterprise can view the demo site after signing in. The Pages site stays privately published on the same generated domain; nothing is exposed to the public internet. Public visibility was considered and rejected for a pre-release demo.

- 2026-09-11: propose six cloud-first application prompts across JavaScript, Python, and .NET before engineering handoff. Preserve existing scenario URLs. Container setup becomes an optional signup path; new prompts remain explicitly draft until reproduced and validated.
# Decisions for the SQLCon review

2026-09-16: Feature three cloud-first draft prompts for a focused review; retain earlier URLs, and require engineering execution evidence before launch claims.
2026-09-16: Engineering owns both Clarity telemetry implementation and prompt validation; PM owns content, mockup approval and launch messaging.
2026-09-16: Exclude local output packages from site publishing and agent indexes; omit unavailable video placeholders.
