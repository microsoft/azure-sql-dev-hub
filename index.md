---
layout: home
title: Azure SQL Hub
description: >-
  Build on Azure SQL in minutes. Run the engine locally in a container, create a
  free database in the cloud, or install the agent skills and build straight from
  your AI coding agent.

hero:
  headline: Build on Azure SQL in minutes
  subline: "Local container, free cloud tier, or straight from your AI agent."
  command: 'docker run --name sqldb -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourStr0ng_Passw0rd" -p 1433:1433 -d sqldbpreview-dpgaeqhmgphzd4bk.azurecr.io/azure-sql/db-dev:latest'
  trust: Works with Claude Code, GitHub Copilot, Codex, and Cursor.

paths:
  - title: Local
    anchor: start
    what: The Azure SQL Database engine on your own machine.
    facts:
      - Runs in any modern container runtime
      - Works offline once the image is pulled
      - Free for local development
    cta: Run it locally
  - title: Cloud
    anchor: start
    what: A managed Azure SQL Database on the free offer.
    facts:
      - 100,000 vCore seconds per database each month
      - 32 GB data and 32 GB backup storage
      - Created from the Azure portal in a few steps
    cta: Create a free database
  - title: Agent
    anchor: skills
    accent: true
    badge: New
    what: Teach your AI coding agent to do the setup for you.
    facts:
      - 17 skills for the container and the cloud
      - One install command for most agents
      - Native plugin for Claude Code and Codex
    cta: Install the skills
---

## Start {#start}
{: .tab-group}

Three ways in. They lead to the same engine, so anything you build against one
runs against the others without a code change.

### Local
{: .tab}

Run the Azure SQL Database engine on your own machine in three steps.

The image ships from a private registry during the Private Preview. Sign in with
the username and password you get when you
[sign up]({{ site.container_signup }}):

```bash
docker login sqldbpreview-dpgaeqhmgphzd4bk.azurecr.io -u <username>
```

Start the container on port 1433:

```bash
docker run --name sqldb -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourStr0ng_Passw0rd" \
    -p 1433:1433 -d sqldbpreview-dpgaeqhmgphzd4bk.azurecr.io/azure-sql/db-dev:latest
```

Replace `YourStr0ng_Passw0rd` with your own. The container enforces the default
SQL password complexity policy. On a host that is not x64, add
`--platform linux/amd64` so the image runs under emulation.

Verify it is up and answering queries:

```bash
docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "YourStr0ng_Passw0rd" -C -Q "SELECT 1"
```

A result of `1` means the engine is running and reachable. Full detail is in the
[container getting started guide]({{ site.container_site }}/getting-started.html).

### Cloud
{: .tab}

Create a managed Azure SQL Database on the free offer. This path runs in the
Azure portal, so it is a short sequence of screens rather than commands.

You need an Azure account and subscription. The free offer itself adds no cost,
and it applies whatever your subscription type is.

1. Open the [Azure SQL hub in the portal]({{ site.azure_portal_hub }}).
2. In the **Create a database** pane, select **Start free**.
3. Confirm the **Free offer applied** banner appears, then fill in the
   **Basics** tab: subscription, resource group, database name, and server.
4. Select **Review + create**, then **Create**.

Each free database gives you 100,000 vCore seconds of serverless compute, 32 GB
of data, and 32 GB of backup storage per month, for up to 10 databases per
subscription. When a database reaches the monthly limit you choose what happens:
pause until the next month, or keep it online and pay standard rates for the
overage. See the [free offer documentation]({{ site.azure_free_offer }}) for the
current limits and exclusions.

Once the database exists, query it from the portal query editor, from the MSSQL
extension for Visual Studio Code, or from any driver you already use.

### Agent
{: .tab}

Install the agent skills and describe what you want in plain English. The skills
carry the setup knowledge: which image to pull, how to wait for readiness, how to
provision a database, and how the local and cloud paths relate.

This is the fastest path if you already work in an AI coding agent. Head to
[Teach your agent Azure SQL](#skills) for the install command for your tool.

## Teach your agent Azure SQL {#skills}
{: .tab-group}

The [Azure SQL Database container repository]({{ site.container_repo }}) ships 17
agent skills. Installing them gives your agent working knowledge of the engine,
so it can start the container, provision a database, scaffold a schema, write
migrations, and build the data layer for your stack.

### Claude Code
{: .tab}

Install as a native plugin so Claude Code manages updates:

```text
/plugin marketplace add microsoft/azure-sql-database-container
/plugin install azure-sql-database-container@azure-sql-database-container
```

The portable installer works here too:

```bash
npx skills add microsoft/azure-sql-database-container
```

### GitHub Copilot
{: .tab}

`npx skills add` writes to a folder that Copilot reads automatically, so there is
no extra step:

```bash
npx skills add microsoft/azure-sql-database-container
```

Find them in Copilot Chat under **Configure Chat** on the **Skills** tab, or by
typing `/skills` in chat.

### Codex
{: .tab}

Install as a native plugin:

```bash
codex plugin marketplace add microsoft/azure-sql-database-container
codex plugin add azure-sql-database-container@azure-sql-database-container
```

Or use the portable installer:

```bash
npx skills add microsoft/azure-sql-database-container
```

### Cursor
{: .tab}

```bash
npx skills add microsoft/azure-sql-database-container
```

A few of the skills you get:
{: .tab-end}

`azuresql-db-container` `azuresql-db-scaffold` `azuresql-db-schema-migration`
`azuresql-db-connections` `azuresql-db-local-to-cloud` `azuresql-db-rag`
`azuresql-db-testing` `azuresql-db-ci`
{: .chips}

[Full catalog]({{ site.skills_catalog }}) lists all 17 with what each one does.

MCP endpoint: coming soon.
{: .muted}
