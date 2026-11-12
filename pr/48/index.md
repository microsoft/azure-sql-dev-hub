# Azure SQL, built for AI workloads

Bring the idea. Build with Azure SQL.

Start with a prompt. Give your AI coding agent SQL skills, and make your next app yours.

Works with Claude Code, GitHub Copilot, Codex, and Cursor.

## From idea to app

Azure SQL for the agent era.

## Get running {#get-running}

Choose your starting point: the cloud, local development, or your coding agent.

### Cloud, free tier: Create a free Azure SQL database.

Create it in the Azure portal with the free tier, then verify from any SQL editor. Prerequisites and tier limits are in the setup guide.

```bash
SELECT 1 AS connected;
```

- Create the database: You need an Azure subscription with permission to create resources. Follow the free-tier guide and pick the free tier when prompted.
- Open access: Add your IP to the firewall and sign in with Microsoft Entra.
- Verify: Run SELECT 1. A result of 1 means your connection works and you are ready for a build prompt.

Free tier: setup guide, prerequisites, and limits: https://learn.microsoft.com/azure/azure-sql/database/free-tier

### Local container: Run the Azure SQL Database engine on your laptop.

Same engine as the cloud, in a container, offline. Preview today. Sign up and we send registry access.

- One docker run: Sign in to the preview registry, pull the image, start the engine.
- Agent skills included: Skills teach your agent to provision, connect, migrate, seed, and ship, with you reviewing each step.
- Ship to Azure unchanged: Only the connection string changes.

Sign up for the Preview: https://aka.ms/sqldbcontainerpreview-signup

Container quickstart: https://microsoft.github.io/azure-sql-database-container/getting-started.html

### With your coding agent: Install the skills, then ask in plain English.

One command teaches Claude Code, Copilot, Codex, or Cursor how Azure SQL works. You stay in the loop on every step.

```bash
npx skills add microsoft/microsoft-sql
```

- Create a free database first: Provisioning is still your step today. The agent takes it from there.
- Prompt your agent: "Connect to my Azure SQL database and scaffold the schema, migrations, and data layer for my stack."
- Verify: The agent runs the first query and shows you the result.

What the skills teach, per agent: https://aka.ms/azuresql-skills

Then: Local or free tier to Azure SQL Database. Same code, connection string changes, app goes live.

## Bring your app idea to life {#build}

Start with a task app, an API, or search over your content. Choose a scenario and use its prompt with your coding agent to build on Azure SQL.

Each prompt works against a database you already have. No database yet? [Get a database running](#get-running) takes three steps.

1. Choose a scenario
2. Copy the prompt
3. Build and verify

### [Build a task-tracking app](build/javascript-app.md)

JavaScript. Build a web app that displays tasks stored in Azure SQL. Start with sample data and make it your own.

Full prompt: build/javascript-app.md

### [Build an API for your app](build/python-api.md)

Python. Give your app a way to create, complete, and retrieve tasks. Build a Python API that connects to Azure SQL with Microsoft Entra, no passwords.

Full prompt: build/python-api.md

### [Search your content by meaning](build/rag-app.md)

Python / AI. Find relevant text with vector search in Azure SQL. Build the retrieval layer for a RAG app using sample text and an embedding model you provide.

Full prompt: build/rag-app.md

### [Create a serverless task API](build/serverless-api.md)

.NET. Read and save tasks through an Azure Functions API backed by Azure SQL. Build and test the functions locally.

Full prompt: build/serverless-api.md

### [Respond to data changes](build/event-driven-app.md)

.NET. Extend the serverless API with a function that reacts when tasks change in Azure SQL. Log inserts, updates, and deletes as a starting point for automation.

Full prompt: build/event-driven-app.md

### [Separate each customer's data](build/multi-tenant.md)

JavaScript. Extend a task app for multiple customers. Add row-level security and test that one tenant cannot read another tenant's tasks.

Full prompt: build/multi-tenant.md

## Built for AI workloads {#workloads}

The pieces an AI app needs, inside the engine.

- Vector search: A native VECTOR type and VECTOR_DISTANCE. Store embeddings next to the rows they describe. (https://learn.microsoft.com/sql/relational-databases/vectors/vectors-sql-server)
- Embeddings in T-SQL: Generate and chunk from inside the database with external model calls. No separate pipeline. (https://learn.microsoft.com/sql/t-sql/functions/ai-generate-embeddings-transact-sql)
- RAG, end to end: Chunk, embed, store, retrieve, ground. One skill walks your agent through all five.
- Safe for agents to write: Row-level security, Entra identity, and injection-safe patterns the skills enforce by default. (https://learn.microsoft.com/sql/relational-databases/security/row-level-security)

## Skills {#skills}

Microsoft SQL Agent Skills

Pick your agent. One install. The skills load themselves when the work matches.

### Claude Code

```bash
claude plugin marketplace add microsoft/microsoft-sql
claude plugin install microsoft-sql@microsoft-sql
```

Two commands: register the marketplace, then install the plugin with every skill. Or the portable form: gh skill install microsoft/microsoft-sql --all --agent claude-code.

### GitHub Copilot

```bash
npx skills add microsoft/microsoft-sql
```

Or gh skill install microsoft/microsoft-sql --all --agent github-copilot. Find them in Copilot Chat under Configure Chat, Skills tab, or type /skills. Committed to .github/skills/ in your repo, they also reach the Copilot coding agent with no install.

### Codex

```bash
npx skills add microsoft/microsoft-sql
```

The repository is an Agent Plugins package, so Codex installs it directly. Confirm with ls .codex/skills.

### Cursor

```bash
npx skills add microsoft/microsoft-sql
```

Or gh skill install microsoft/microsoft-sql --all --agent cursor. Confirm with ls .cursor/skills.

Example prompts once the skills are installed:

- [object Object]
- [object Object]
- [object Object]
- [object Object]

Full catalog, every skill's source, and the feedback form at aka.ms/azuresql-skills. Skills teach your agent the engine; they do not grant access to the Preview container.

## Videos {#watch}

Longer walkthroughs from the Microsoft SQL team. Scroll for more.

- [Boost your SQL development in VS Code: Copilot, containers, and more](https://www.youtube.com/watch?v=pq2drN2Qw5w): Carlos Robles, VS Code Live, Aug 2025
- [Build AI apps with VS Code Agents, GitHub Copilot, and the MSSQL extension](https://www.youtube.com/watch?v=wZUPFCCByfw): Data Exposed, May 2026
- [AI-powered SQL development in VS Code with GitHub Copilot](https://www.youtube.com/watch?v=biJywQPbqn0): MSSQL extension v1.32, May 2025
- [Azure SQL Database Foundations](https://aka.ms/azuresqlfoundationseries): Four sessions: getting started, migration, performance, AI

## Existing data {#existing}

Point the prompts above at an existing development database. Review permissions and schema changes before you let an agent run them.

## Local development {#continuity}

Prefer local development?

The Azure SQL Database container runs the same engine offline. Sign up for the Preview.

## Before you build

### What do I need to get started?

An Azure account and a development database. The free tier covers everything on this page, within its limits. If you want to work offline, sign up for the container Preview.

### Is it safe to let an agent write to my database?

Use a development database with least-privilege access. The skills default to parameterised queries, Entra identity over passwords, and row-level security for multi-tenant work. Review schema changes before they run against anything real.

### Do I need the container?

No. Every prompt here targets Azure SQL Database in the cloud. The container is the local option, in Preview today.

### What does this cost?

The free tier covers the database for every example here, within its limits; see the tier details for what those are. The RAG example needs an embedding service, priced by whoever provides it; the prompt asks which one you have before using it.

### How is this different from SQL Server?

Same engine family, managed for you, with features that ship to Azure SQL Database first. The container runs the Azure SQL Database engine, not the SQL Server image.

## Get started

Ready? Teach your agent, then ask

```bash
npx skills add microsoft/microsoft-sql
```
