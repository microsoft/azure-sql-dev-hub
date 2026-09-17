---
layout: page
title: Build a RAG workflow
description: >-
  Build a small Python RAG application using Azure SQL Database for source text
  and embeddings. Ask which embedding and generation services I can access
  before choosing them.
---

**Python / AI**

## What you will build

Build a small Python RAG application using Azure SQL Database for source text and embeddings. Ask which embedding and generation services I can access before choosing them.

## Before you start

Use an Azure account and an accessible development database. Confirm authentication, runtime, permissions, and potential service costs. No private container credentials are required by this prompt.

## Copy this prompt

```text
Build a small Python RAG application using Azure SQL Database for source text and embeddings. Ask which embedding and generation services I can access before choosing them.

Before writing code, ask for my Azure SQL server and database, available authentication method, target runtime, and any missing requirements. Use an existing cloud database unless I explicitly approve resource creation and costs. Do not require the private-preview container. Never ask me to paste credentials into chat or put secrets in source control.

Success criteria: Load a small known document set, retrieve relevant passages, and return an answer with source references. Test a question not covered by the documents.

Use current official documentation to verify driver, authentication, and framework choices. Include complete project files, dependency versions, configuration placeholders, schema setup, and parameterized data access. Explain permissions and any resources that could incur charges. Provide exact run instructions, a small repeatable verification test, expected output, and cleanup steps. Run available tests and report what actually passed, what required a manual change, and what could not be verified. Do not claim completion from code generation alone.
```

## Expected result

Load a small known document set, retrieve relevant passages, and return an answer with source references. Test a question not covered by the documents.

## References

- [Azure SQL documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Optional skill catalog]({{ site.skills_catalog }})


