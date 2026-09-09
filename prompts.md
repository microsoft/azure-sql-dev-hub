---
layout: page
eyebrow: Prompt library
title: Validated build prompts
description: >-
  Copy a prompt, paste it into your coding agent, and keep building. Each one
  turns a common Azure SQL job into a one-click starting point.
---

Copy a prompt, paste it into your coding agent, and keep building. Prompts work
best with the [Azure SQL skills](/#skills) installed: the prompt states the
outcome, the skills carry the product-specific context.

## Build locally, ship to Azure {#local-to-cloud}

Start on the local Azure SQL engine, then prepare the same app for Azure SQL
Database.

```text
Set up this app against Azure SQL locally, verify the schema and first query, then show me the exact changes needed to point the same app at Azure SQL Database.
```

Pairs with the [Ship local to cloud](build/local-to-cloud.html) scenario.

## Prototype a RAG workflow {#rag}

Use Azure SQL for relational data, embeddings, and vector similarity search.

```text
Add a RAG workflow to this app using Azure SQL. Keep the source data and embeddings together, create the vector schema, and verify a similarity query.
```

Pairs with the [Wire up RAG](build/rag.html) scenario.

## Secure a multi-tenant app {#multi-tenant}

Use Azure SQL security primitives around tenant data and application access.

```text
Review this multi-tenant app and add an Azure SQL data-isolation pattern using Row-Level Security. Show the schema, policy, and how the app sets tenant context.
```

Pairs with the [Multi-tenant setup](build/multi-tenant.html) scenario.

## More build prompts, from the container repository

The Azure SQL Database container repository maintains a set of copy-and-run
build prompts, each a full working session for an agent:

- [Build locally, ship to Azure (Node.js)]({{ site.container_repo }}/blob/main/docs/prompts/local-to-cloud.md)
- [Prototype AI / RAG with vector search (Python + Ollama)]({{ site.container_repo }}/blob/main/docs/prompts/ai-rag.md)
- [Run integration tests in CI]({{ site.container_repo }}/blob/main/docs/prompts/ci.md)
- [Convert from the SQL Server image]({{ site.container_repo }}/blob/main/docs/prompts/from-sql-server.md)
- [Develop offline]({{ site.container_repo }}/blob/main/docs/prompts/offline.md)
- [Drop in as a sidecar]({{ site.container_repo }}/blob/main/docs/prompts/sidecar.md)
- [Scaffold a new project]({{ site.container_repo }}/blob/main/docs/prompts/templates.md)
- [Instant REST and GraphQL API with Data API Builder]({{ site.container_repo }}/blob/main/docs/prompts/dab.md)
- [Serverless and event-driven with Azure Functions]({{ site.container_repo }}/blob/main/docs/prompts/functions.md)

Every scenario page also carries its own prompt: browse them from
[Start with the job you need done](/#build).
