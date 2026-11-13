# Azure SQL Developer Hub

**https://aka.ms/azuresql-hub**

The front door for building applications on Azure SQL Database with an AI coding agent. Start free in the cloud, hand your agent a build prompt, and verify a working app.

Curated by the Azure SQL Database product team.

## What is here

- **Build prompts.** Fourteen prompts in [`build/`](build/): six apps and eight building blocks.
- **Two ways to get a database.** The free cloud tier, or the local container (public preview).
- **Agent skills.** Install the plugin for your agent from [aka.ms/azuresql-skills](https://aka.ms/azuresql-skills); the skills load themselves when the work matches.
- **An agent-readable layer.** Every page has a markdown twin at `<page>.md`, an index at [`llms.txt`](llms.txt), and an alternate link in its head.

## Build prompts

Apps are specifications: rules, sample data, a database design, and checks. The agent designs and builds the rest. They run on Azure SQL Database or the local container.

| App | Azure SQL features | Prompt |
|---|---|---|
| Team board | Temporal tables, version check in the `UPDATE` | [team-board.md](build/team-board.md) |
| Inventory reservations | Transactions and row locks, idempotency key | [inventory-reservations.md](build/inventory-reservations.md) |
| Knowledge base search | `VECTOR`, `AI_GENERATE_EMBEDDINGS`, JSON | [knowledge-base.md](build/knowledge-base.md) |
| Revenue reporting | `bigint` cents, `GENERATE_SERIES`, columnstore | [revenue-reporting.md](build/revenue-reporting.md) |
| Shipment tracker | `OPENJSON`, composite key, binary collation | [shipment-tracker.md](build/shipment-tracker.md) |
| Multi-tenant helpdesk | Row-level security, `SESSION_CONTEXT` | [multi-tenant-helpdesk.md](build/multi-tenant-helpdesk.md) |

Building blocks are short, with the code included: role, scope, numbered steps, validation rules, and what not to do.

| Building block | Stack | Prompt |
|---|---|---|
| Start a Next.js app | JavaScript, Next.js | [javascript-app.md](build/javascript-app.md) |
| Add a Python API | Python, FastAPI | [python-api.md](build/python-api.md) |
| Search text by meaning | Python, native `VECTOR` | [rag-app.md](build/rag-app.md) |
| Add a serverless API | .NET, Azure Functions SQL bindings | [serverless-api.md](build/serverless-api.md) |
| React to data changes | .NET, SQL trigger with Change Tracking | [event-driven-app.md](build/event-driven-app.md) |
| Isolate each tenant's rows | JavaScript, row-level security | [multi-tenant.md](build/multi-tenant.md) |
| Get a REST and GraphQL API | Data API builder | [data-api.md](build/data-api.md) |
| Move from the container to the cloud | Any stack | [local-to-cloud.md](build/local-to-cloud.md) |

The first six building blocks passed the evaluation harness in [`eval/`](eval/) on 2026-09-29 and have been edited since. The apps and the last two building blocks have not been run through it. Every prompt carries `validated: false` until it is rerun.

Five earlier pages (`build/connect-app`, `build/query-performance`, `build/rag`, `build/start-database`, and `prompts`) are kept as redirects so old links land.

## Install the skills

Claude Code:

```bash
claude plugin marketplace add microsoft/microsoft-sql
claude plugin install microsoft-sql@microsoft-sql
```

GitHub Copilot CLI, Codex, and Cursor commands are on the site and at [aka.ms/azuresql-skills](https://aka.ms/azuresql-skills).
## Scope

Cloud means Azure SQL Database. Not Managed Instance, not Fabric SQL, not SQL Server on virtual machines. Local means the Azure SQL Database container.

## Run the site locally

The site is Jekyll, served from the repository root. Prompt pages live in `build/`, the home page content in `index.md` front matter.

```bash
bundle install
npm install
npm run build:site             # HTML, then markdown twins and llms-full.txt into _site
npm test                       # house rules and the telemetry contract
npm run check:links            # internal links in the built site
```

The Copy prompt buttons fetch the page's markdown twin over HTTP, so use a served build rather than opening files from disk. `jekyll serve` removes the twins on every rebuild; run `npm run build:agent-files` again after it regenerates.
## Contributing

Pull requests are welcome. Read [`docs/DECISIONS.md`](docs/DECISIONS.md) first for why the site is shaped the way it is. House rules run in CI on every pull request: no em dashes in copy, and the agent layer (`llms.txt`, markdown twins, alternate links) must be present on every build.

A prompt is ready to merge when it has been run once, end to end, against a fresh Azure SQL Database and its validation rules held. Keep the home page copy short: a card is a title and one line.

## Feedback

- A prompt or the site said something wrong, stale, or unhelpful: [open an issue](https://github.com/microsoft/azure-sql-dev-hub/issues).
- A skill said something wrong: [skill feedback](https://aka.ms/sql-agent-skills-feedback).
- The product misbehaved rather than the prompt: the Azure SQL Database feedback channels.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.
