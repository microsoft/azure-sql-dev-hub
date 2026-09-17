---
layout: page
title: Create a Python API
description: Build a Python HTTP API for a task list backed by Azure SQL Database.
---

**Python**

## What you will build

Build a Python HTTP API for a task list backed by Azure SQL Database.

## Before you start

Use an Azure account and an accessible development database. Confirm authentication, runtime, permissions, and potential service costs. No private container credentials are required by this prompt.

## Copy this prompt

```text
Build a Python HTTP API for a task list backed by Azure SQL Database.

Before writing code, ask for my Azure SQL server and database, available authentication method, target runtime, and any missing requirements. Use an existing cloud database unless I explicitly approve resource creation and costs. Do not require the private-preview container. Never ask me to paste credentials into chat or put secrets in source control.

Success criteria: Exercise create, read, update, and delete endpoints, including invalid input and an unknown record.

Use current official documentation to verify driver, authentication, and framework choices. Include complete project files, dependency versions, configuration placeholders, schema setup, and parameterized data access. Explain permissions and any resources that could incur charges. Provide exact run instructions, a small repeatable verification test, expected output, and cleanup steps. Run available tests and report what actually passed, what required a manual change, and what could not be verified. Do not claim completion from code generation alone.
```

## Expected result

Exercise create, read, update, and delete endpoints, including invalid input and an unknown record.

## References

- [Azure SQL documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Optional skill catalog]({{ site.skills_catalog }})


