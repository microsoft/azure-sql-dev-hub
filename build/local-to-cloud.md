---
layout: scenario
title: Ship local to cloud
description: >-
  Preserve the app contract and change the target from the local Azure SQL
  engine to Azure SQL Database.
intro: >-
  Preserve the app contract and change the target from the local Azure SQL
  engine to Azure SQL Database.
prompt: >-
  Prepare this app to move from the local Azure SQL container to Azure SQL
  Database. Keep the application code unchanged where possible and make the
  cloud transition through configuration.
starter:
  language: bash
  code: |-
    SQL_CONNECTION_STRING="Server=tcp:<server>.database.windows.net,1433;Database=<database>;Authentication=Active Directory Default;Encrypt=True"
skill:
  name: azuresql-db-local-to-cloud
  note: >-
    The local-to-cloud skill knows what changes between the container and Azure
    SQL Database, and what deliberately does not.
  install: npx skills add microsoft/azure-sql-database-container --skill azuresql-db-local-to-cloud
docs:
  label: Local to cloud build prompt
  href: https://github.com/microsoft/azure-sql-database-container/blob/main/docs/prompts/local-to-cloud.md
---

## A connection-string change, not a code change

The local container runs the Azure SQL Database engine, so the schema, T-SQL,
and driver behavior you developed against carry forward. What changes is the
target in configuration: the server becomes your logical server's address, and
authentication moves from a local SQL login to Microsoft Entra, which is what
`Authentication=Active Directory Default` in the starter selects for drivers
that support it.

Create the cloud database first if you have not: the Cloud tab on the
[home page](../index.md) has the CLI command with the free offer applied, and
[Start a database](start-database.html) covers the portal path. Then swap the
value of `SQL_CONNECTION_STRING`, run your test suite against the cloud target,
and compare. The container repository's
[local-to-cloud build prompt](https://github.com/microsoft/azure-sql-database-container/blob/main/docs/prompts/local-to-cloud.md)
walks an agent through exactly this sequence.
