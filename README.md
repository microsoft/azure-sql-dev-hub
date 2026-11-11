# Azure SQL Developer Hub

**https://aka.ms/azuresql-hub**

App templates and practical patterns for Azure SQL Database. Explore dashboards, APIs, search, and multi-tenant applications, then adapt a starting point to your project.

Curated by the Azure SQL Database product team.

## What is here

- **App templates and building blocks.** Five full-app briefs and six focused build prompts for Azure SQL Database, with requirements and validation checks. These are instructions for building an app, not prebuilt codebases. They live in [`build/`](build/).
- **Setup paths.** Free cloud tier, the local container (public preview), or with your coding agent.
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

Prompts here target the cloud. Prompts that target the local container live in the [Azure SQL Database container repository](https://github.com/microsoft/azure-sql-database-container/tree/main/docs/prompts).

## Install the skills

```bash
npx skills add microsoft/microsoft-sql
```

Claude Code plugin:

```bash
claude plugin marketplace add microsoft/microsoft-sql
claude plugin install microsoft-sql@microsoft-sql
```

Full catalog, per-tool install, and feedback at [aka.ms/azuresql-skills](https://aka.ms/azuresql-skills).

## Scope

Cloud means Azure SQL Database. Not Managed Instance, not Fabric SQL, not SQL Server on virtual machines. Local means the Azure SQL Database container.

## Run the site locally

The site is Jekyll, served from the repository root. Scenario pages live in `build/`, the homepage content in `index.md` front matter.

Start Docker Desktop with Linux containers enabled. No local Ruby or Node.js
installation is required.

In VS Code, select **Website: launch with live reload** in Run and Debug and
press **F5**. Its **Website: serve** task builds the development image, starts
the preview at http://localhost:4000, and opens Edge after the server is ready.
The first build downloads Ruby, Node.js, and the project dependencies.
Stopping the debugger runs **Website: stop** to shut down the container.
If your network requires an npm mirror, set `NPM_CONFIG_REGISTRY` in a local
`.env` file before building. The file is ignored by Git and the Docker build.

To run the same preview without VS Code:

```bash
docker compose up --build --renew-anon-volumes
```

Saving pages, layouts, includes, or assets rebuilds the site and reloads the
browser. Markdown twins and `llms-full.txt` are regenerated on every build, so
the prompt Copy buttons stay current too. Restart the task after changing
`_config.yml`. Run `docker compose down` to stop a manually started preview.

For a one-off build and checks using the development image:

```bash
docker compose run --rm website npm run build:site
docker compose run --rm website npm test
```

Alternatively, with Ruby, Bundler, Node.js, and npm on your PATH:

```bash
bundle install
npm ci
npm start                      # watch, serve, and live reload at http://localhost:4000
npm run build:site             # Jekyll plus markdown twins and llms-full.txt into _site
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
