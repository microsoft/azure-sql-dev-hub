---
layout: page
title: Scaffold a .NET app
description: >-
  Scaffold a small .NET web application with Azure SQL Database and a supported
  data-access library.
---

**.NET · Draft prompt. Engineering validation pending.**

## What you will build

Scaffold a small .NET web application with Azure SQL Database and a supported data-access library.

## Before you start

Use an Azure account and an accessible development database. Confirm authentication, runtime, permissions, and potential service costs. No private container credentials are required by this prompt.

## Copy this prompt

```text
Scaffold a small .NET web application with Azure SQL Database and a supported data-access library.

Before writing code, ask for my Azure SQL server and database, available authentication method, target runtime, and any missing requirements. Use an existing cloud database unless I explicitly approve resource creation and costs. Do not require the private-preview container. Never ask me to paste credentials into chat or put secrets in source control.

Success criteria: Apply the schema, create a record through the app, restart it, and verify the record remains.

Use current official documentation to verify driver, authentication, and framework choices. Include complete project files, dependency versions, configuration placeholders, schema setup, and parameterized data access. Explain permissions and any resources that could incur charges. Provide exact run instructions, a small repeatable verification test, expected output, and cleanup steps. Run available tests and report what actually passed, what required a manual change, and what could not be verified. Do not claim completion from code generation alone.
```

## Expected result

Apply the schema, create a record through the app, restart it, and verify the record remains.

## Validation status

This is a proposed example, not a tested walkthrough. Runnable starter code, exact dependency versions, and a recorded test result are pending engineering validation.

## References

- [Azure SQL documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Optional skill catalog]({{ site.skills_catalog }})

## Walkthrough

A walkthrough will be added after the example is validated.
