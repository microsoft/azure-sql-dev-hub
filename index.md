---
layout: home
title: Azure SQL Developer Hub
description: >-
  The front door for building with Azure SQL Database in the age of AI-assisted
  development.

hero:
  eyebrow: Trusted in production for three decades
  headline: "Azure SQL, built for"
  headline_accent: "AI workloads."
  subline: >-
    Start locally or in Azure. Build with the coding agent you already use.
    Move from first prompt to production on Azure SQL.
  agents: [Claude Code, GitHub Copilot, Codex, Cursor]

quickstart:
  - key: agent
    name: Agent
    status: Install once. Ask in plain English.
    label: Install Azure SQL skills
    title: Bring Azure SQL into your coding agent.
    desc: >-
      One install gives your agent Azure SQL-specific setup, schema, RAG,
      security, troubleshooting, and local-to-cloud guidance.
    code: npx skills add microsoft/azure-sql-database-container
    copy_event: install_cmd_copy
    prompt: >-
      Set up Azure SQL locally for this app, connect it, and verify the first
      query.
    detail_title: Let the agent handle the setup.
    detail_text: >-
      The Hub gives the human the shortest useful action and gives the agent
      the current product-specific context behind it.
    checks:
      - ["Install the guidance", "Use the same Azure SQL skill collection across supported coding agents."]
      - ["Ask for the outcome", "Setup, schema, RAG, security, troubleshooting, or local-to-cloud."]
      - ["Go deeper only when needed", "Open the scenario page for validated prompts, code, video, docs, and skills."]
    link: { label: "See skills and agent setup →", href: "#skills" }
  - key: local
    name: Local
    status: Current Private Preview container path.
    label: Start Azure SQL locally
    title: Run the Azure SQL Database engine on your machine.
    desc: >-
      Use the local container for development, tests, and agent-driven work
      before you need an Azure resource.
    code: |-
      docker run --name sqldb -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourStr0ng_Passw0rd" \
        -p 1433:1433 -d sqldbpreview-dpgaeqhmgphzd4bk.azurecr.io/azure-sql/db-dev:latest
    copy_event: copy_command
    prompt: ""
    detail_title: From container to first query.
    detail_text: >-
      The preview image requires registry access. The full quickstart covers
      sign-in, non-x64 hosts, and the bundled sqlcmd verification step.
    checks:
      - ["Start the engine", "Run Azure SQL locally on port 1433."]
      - ["Verify the first query", "Use the bundled sqlcmd inside the container."]
      - ["Keep the app contract", "Read the connection string from configuration so the Azure target can change later."]
    link: { label: "Open the full container quickstart →", href: "https://microsoft.github.io/azure-sql-database-container/getting-started.html" }
  - key: cloud
    name: Cloud
    status: Azure CLI quickstart.
    label: Create Azure SQL in Azure
    title: Start directly with an Azure SQL Database.
    desc: >-
      Use the Azure CLI when you want the managed cloud resource from the
      beginning.
    code: >-
      az sql db create -g mygroup -s myserver -n mydb -e GeneralPurpose -f Gen5
      -c 2 --compute-model Serverless --use-free-limit
      --free-limit-exhaustion-behavior AutoPause
    copy_event: copy_command
    prompt: ""
    detail_title: Create the cloud database, then connect.
    detail_text: >-
      This command assumes an existing Azure SQL logical server. Keep the server
      and database names as inputs, then route the app through its
      connection-string configuration.
    checks:
      - ["Create the database", "Use a repeatable Azure CLI path with the free offer applied."]
      - ["Keep the destination measurable", "Outbound Azure links are measured as telemetry events."]
      - ["Connect the same app", "Swap the endpoint and keep the application contract."]
    link: { label: "Open Azure SQL Database docs →", href: "https://learn.microsoft.com/azure/azure-sql/database/" }

continuity:
  heading: Start local. Move to Azure when the app is real.
  text: >-
    Keep the application contract. Change the database endpoint. The engine,
    T-SQL, drivers, and application patterns carry forward.
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
  - { num: "01", slug: start-database,    title: Start a database,   blurb: "Stand up Azure SQL, connect, and verify the first query." }
  - { num: "02", slug: connect-app,       title: Connect your app,   blurb: "Use the current driver and connection pattern for your framework." }
  - { num: "03", slug: rag,               title: Wire up RAG,        blurb: "Keep relational data and vectors together with native vector search." }
  - { num: "04", slug: multi-tenant,      title: Multi-tenant setup, blurb: "Keep tenant data isolated with Row-Level Security." }
  - { num: "05", slug: query-performance, title: Fix a slow query,   blurb: "Measure the query, inspect the plan, and tune with the right context." }
  - { num: "06", slug: local-to-cloud,    title: Ship local to cloud, blurb: "Move the same application from the local engine to Azure SQL." }

prompts_featured:
  - id: local-to-cloud
    tag: Local to cloud
    title: Build locally, ship to Azure
    blurb: >-
      Start on the local Azure SQL engine, then prepare the same app for Azure
      SQL Database.
    prompt: >-
      Set up this app against Azure SQL locally, verify the schema and first
      query, then show me the exact changes needed to point the same app at
      Azure SQL Database.
  - id: rag
    tag: AI / RAG
    title: Prototype a RAG workflow
    blurb: >-
      Use Azure SQL for relational data, embeddings, and vector similarity
      search.
    prompt: >-
      Add a RAG workflow to this app using Azure SQL. Keep the source data and
      embeddings together, create the vector schema, and verify a similarity
      query.
  - id: multi-tenant
    tag: Security
    title: Secure a multi-tenant app
    blurb: >-
      Use Azure SQL security primitives around tenant data and application
      access.
    prompt: >-
      Review this multi-tenant app and add an Azure SQL data-isolation pattern
      using Row-Level Security. Show the schema, policy, and how the app sets
      tenant context.

skills:
  heading: Teach your agent Azure SQL.
  text: >-
    The Azure SQL Database container repository ships 17 agent skills.
    Installing them gives your agent working knowledge of the engine, so it can
    start the container, provision a database, scaffold a schema, write
    migrations, and build the data layer for your stack.
  agents:
    - key: claude-code
      name: Claude Code
      blurb: >-
        Install as a native plugin so Claude Code manages updates. The portable
        installer below it works too.
      code: |-
        /plugin marketplace add microsoft/azure-sql-database-container
        /plugin install azure-sql-database-container@azure-sql-database-container
      alt_code: npx skills add microsoft/azure-sql-database-container
    - key: copilot
      name: GitHub Copilot
      blurb: >-
        The installer writes to a folder Copilot reads automatically. Find the
        skills in Copilot Chat under Configure Chat on the Skills tab.
      code: npx skills add microsoft/azure-sql-database-container
    - key: codex
      name: Codex
      blurb: Install as a native plugin, or use the portable installer below it.
      code: |-
        codex plugin marketplace add microsoft/azure-sql-database-container
        codex plugin add azure-sql-database-container@azure-sql-database-container
      alt_code: npx skills add microsoft/azure-sql-database-container
    - key: cursor
      name: Cursor
      blurb: One command installs the whole collection.
      code: npx skills add microsoft/azure-sql-database-container
  chips:
    - azuresql-db-container
    - azuresql-db-scaffold
    - azuresql-db-schema-migration
    - azuresql-db-connections
    - azuresql-db-local-to-cloud
    - azuresql-db-rag
    - azuresql-db-testing
    - azuresql-db-ci
  mcp_note: "MCP endpoint: coming soon."

existing:
  heading: Your production data can become your AI data.
  text: >-
    Add vector search, RAG, and agent-backed application workflows without
    introducing a separate database just for AI.
  pills: [Native vectors, RAG, Microsoft Entra ID, Row-Level Security]
  sql: |-
    CREATE TABLE dbo.Documents (
      id int PRIMARY KEY,
      content nvarchar(max),
      embedding vector(1536)
    );

    SELECT TOP (10) *
    FROM dbo.Documents
    ORDER BY VECTOR_DISTANCE(
      'cosine',
      @query_vector,
      embedding
    );
---
