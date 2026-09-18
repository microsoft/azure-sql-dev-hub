# Azure SQL Developer Hub

**https://aka.ms/azuresql-hub**

The front door for building applications on Azure SQL Database with an AI coding agent. Start free in the cloud, hand your agent a build prompt, and verify a working app.

Curated by the Azure SQL Database product team.

## What is here

- **Build prompts.** Six copy-and-run prompts, each targeting Azure SQL Database in the cloud and ending in a working app with validation rules at the end. They live in [`build/`](build/).
- **Setup paths.** Free cloud tier, the local container (Preview), or let your agent do it.
- **Agent skills.** Install once from [aka.ms/azuresql-skills](https://aka.ms/azuresql-skills); the skills load themselves when the work matches.
- **An agent-readable layer.** Every page has a markdown twin at `<page>.md`, an index at [`llms.txt`](llms.txt), and an alternate link in its head. Agents read that; people read the page.

## Build prompts

| Scenario | Framework | Prompt |
|---|---|---|
| Scaffold a new app | JavaScript, Next.js | [javascript-app.md](build/javascript-app.md) |
| Build a Python API | Python, FastAPI | [python-api.md](build/python-api.md) |
| Build a RAG workflow | Python, native `VECTOR` | [rag-app.md](build/rag-app.md) |
| Go serverless | .NET, Azure Functions SQL bindings | [serverless-api.md](build/serverless-api.md) |
| React to row changes | .NET, SQL trigger with Change Tracking | [event-driven-app.md](build/event-driven-app.md) |
| Make it multi-tenant | JavaScript, row-level security | [multi-tenant.md](build/multi-tenant.md) |

Each prompt is the whole instruction set: role, scope, numbered steps with code, validation rules, and what not to do. Copy it from the site or from the file, paste it into your agent, check the result against the rules.

Prompts here target the cloud. Prompts that target the local container live with the [Azure SQL Database container](https://microsoft.github.io/azure-sql-database-container/).

## Install the skills

```bash
npx skills add microsoft/azure-sql-skills
```

Claude Code plugin:

```bash
claude plugin marketplace add microsoft/azure-sql-skills
claude plugin install azure-sql-skills@azure-sql-skills
```

Full catalog, per-tool install, and feedback at [aka.ms/azuresql-skills](https://aka.ms/azuresql-skills).

## Scope

Cloud means Azure SQL Database. Not Managed Instance, not Fabric SQL, not SQL Server on virtual machines. Local means the Azure SQL Database container.

## Run the site locally

The site is Jekyll, served from the repository root. Scenario pages live in `build/`, the homepage content in `index.md` front matter.

```bash
bundle install
bundle exec jekyll build --baseurl ""
npm install
npm run build:agent-files      # markdown twins and llms-full.txt into _site
npm test                       # house rules
```

The prompt Copy buttons fetch the page's markdown twin over HTTP, so use a served build rather than opening files from disk.

## Contributing

Pull requests are welcome. Read [`docs/DECISIONS.md`](docs/DECISIONS.md) first for why the site is shaped the way it is. House rules run in CI on every pull request: no em dashes in copy, and the agent layer (`llms.txt`, markdown twins, alternate links) must be present on every build.

A prompt is ready to merge when it has been run once, end to end, against a fresh Azure SQL Database and its validation rules held.

## Feedback

- A prompt or the site said something wrong, stale, or unhelpful: [open an issue](https://github.com/microsoft/azure-sql-dev-hub/issues).
- A skill said something wrong: [skill feedback](https://aka.ms/sql-agent-skills-feedback).
- The product misbehaved rather than the prompt: the Azure SQL Database feedback channels.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.
