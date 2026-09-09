---
layout: scenario
title: Connect your app
description: >-
  Keep the application pointed at one configuration value so local and Azure
  targets stay interchangeable.
intro: >-
  Keep the application pointed at one configuration value so local and Azure
  targets stay interchangeable.
prompt: >-
  Connect this application to Azure SQL using the current supported driver. Put
  the connection string in environment configuration, verify the connection,
  and show one parameterized query.
starter:
  language: javascript
  code: |-
    const pool = await sql.connect(process.env.SQL_CONNECTION_STRING)
    const result = await pool.query`SELECT TOP 5 * FROM dbo.Users`
skill:
  name: azuresql-db-connections
  note: >-
    The connections skill knows the current driver and connection pattern for
    each stack, including how authentication differs between local and Azure.
  install: npx skills add microsoft/azure-sql-database-container --skill azuresql-db-connections
docs:
  label: Connect and query guide
  href: https://learn.microsoft.com/azure/azure-sql/database/connect-query-content-reference-guide
---

## The one rule that matters

Read the connection string from configuration, never from code. The starter
shows the Node.js `mssql` driver doing exactly that: `SQL_CONNECTION_STRING`
comes from the environment, and the tagged-template query is parameterized by
construction. Every supported language has the same shape with its own driver;
the [connect and query guide](https://learn.microsoft.com/azure/azure-sql/database/connect-query-content-reference-guide)
lists them per language and tool.

Locally the container listens on `localhost,1433` with SQL authentication. In
Azure the same application authenticates with Microsoft Entra. Because the app
only ever reads one configuration value, that difference stays in `.env`, which
is the whole local-to-cloud story: see
[Ship local to cloud](local-to-cloud.html) when you are ready to move.
