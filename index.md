---
layout: home
title: Azure SQL Developer Hub
description: The front door for building with Azure SQL Database in the age of AI-assisted development.
hero:
  eyebrow: Build with Azure SQL Database
  headline: From a prompt to
  headline_accent: a working app.
  subline: >-
    Start with a focused application prompt for Azure SQL Database. Review the prerequisites, copy
    the prompt, and verify the result with your coding agent.
  agents:
    - Claude Code
    - GitHub Copilot
    - Codex
    - Cursor
quickstart:
  - key: cloud
    name: Cloud
    status: Portal setup, then verify.
    label: Create Azure SQL in Azure
    title: Create or choose a development database.
    desc: >-
      Follow the Azure SQL free-offer guide in the portal. Review eligibility and limits, configure
      access, then run this query in a connected SQL editor.
    code: SELECT 1 AS connected;
    copy_event: copy_code
    prompt: ''
    detail_title: Confirm access before running a prompt.
    detail_text: >-
      Use an existing development database or follow the portal guide. A result of 1 confirms that
      the query executed on your connection.
    checks:
      - - Review prerequisites
        - You need an Azure subscription and permission to use the database.
      - - Configure access
        - Follow the documented networking and authentication steps.
      - - Verify
        - Run SELECT 1 and confirm the result is 1.
    link:
      label: Open the free-offer setup guide →
      href: https://learn.microsoft.com/azure/azure-sql/database/free-offer
continuity:
  heading: Prefer local development?
  text: >-
    The Azure SQL Database container is an optional Private Preview path requiring signup and
    registry access. The featured prompts target Azure SQL in Azure.
  local_env: |-
    SQL_CONNECTION_STRING=
    Server=localhost,1433;
    Database=appdb;
    User Id=sa;
    TrustServerCertificate=true
  azure_env: |-
    SQL_CONNECTION_STRING=
    Server=app.database.windows.net;
    Database=appdb;
    Authentication=Active Directory Default
scenarios:
  - num: '01'
    slug: javascript-app
    title: Build a JavaScript app
    blurb: >-
      Build a small task-tracking web app with a supported JavaScript framework and Azure SQL
      Database.
    tag: JavaScript
    prompt: >-
      Build a small task-tracking web app with a supported JavaScript framework and Azure SQL
      Database.


      Before writing code, ask for my Azure SQL server and database, available authentication
      method, target runtime, and any missing requirements. Use an existing cloud database unless I
      explicitly approve resource creation and costs. Do not require the private-preview container.
      Never ask me to paste credentials into chat or put secrets in source control.


      Success criteria: Create a task, reload the app, and confirm it persists. Update and delete it
      through the UI.


      Use current official documentation to verify driver, authentication, and framework choices.
      Include complete project files, dependency versions, configuration placeholders, schema setup,
      and parameterized data access. Explain permissions and any resources that could incur charges.
      Provide exact run instructions, a small repeatable verification test, expected output, and
      cleanup steps. Run available tests and report what actually passed, what required a manual
      change, and what could not be verified. Do not claim completion from code generation alone.
  - num: '02'
    slug: python-api
    title: Create a Python API
    blurb: Build a Python HTTP API for a task list backed by Azure SQL Database.
    tag: Python
    prompt: >-
      Build a Python HTTP API for a task list backed by Azure SQL Database.


      Before writing code, ask for my Azure SQL server and database, available authentication
      method, target runtime, and any missing requirements. Use an existing cloud database unless I
      explicitly approve resource creation and costs. Do not require the private-preview container.
      Never ask me to paste credentials into chat or put secrets in source control.


      Success criteria: Exercise create, read, update, and delete endpoints, including invalid input
      and an unknown record.


      Use current official documentation to verify driver, authentication, and framework choices.
      Include complete project files, dependency versions, configuration placeholders, schema setup,
      and parameterized data access. Explain permissions and any resources that could incur charges.
      Provide exact run instructions, a small repeatable verification test, expected output, and
      cleanup steps. Run available tests and report what actually passed, what required a manual
      change, and what could not be verified. Do not claim completion from code generation alone.
  - num: '03'
    slug: rag-app
    title: Build a RAG workflow
    blurb: >-
      Build a small Python RAG application using Azure SQL Database for source text and embeddings.
      Ask which embedding and generation services I can access before choosing them.
    tag: Python / AI
    prompt: >-
      Build a small Python RAG application using Azure SQL Database for source text and embeddings.
      Ask which embedding and generation services I can access before choosing them.


      Before writing code, ask for my Azure SQL server and database, available authentication
      method, target runtime, and any missing requirements. Use an existing cloud database unless I
      explicitly approve resource creation and costs. Do not require the private-preview container.
      Never ask me to paste credentials into chat or put secrets in source control.


      Success criteria: Load a small known document set, retrieve relevant passages, and return an
      answer with source references. Test a question not covered by the documents.


      Use current official documentation to verify driver, authentication, and framework choices.
      Include complete project files, dependency versions, configuration placeholders, schema setup,
      and parameterized data access. Explain permissions and any resources that could incur charges.
      Provide exact run instructions, a small repeatable verification test, expected output, and
      cleanup steps. Run available tests and report what actually passed, what required a manual
      change, and what could not be verified. Do not claim completion from code generation alone.
prompts_featured: []
skills:
  heading: Teach your agent Azure SQL.
  text: >-
    Optional guidance is available from the Azure SQL Database container repository. Check each
    skill for cloud suitability and prerequisites. Installing skills does not grant access to the
    Private Preview container.
  agents: []
  chips: []
  mcp_note: ''
---
