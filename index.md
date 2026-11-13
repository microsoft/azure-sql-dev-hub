---
layout: home
title: Azure SQL Developer Hub
description: Build applications on Azure SQL Database with an AI coding agent. Create a free database, paste a build prompt into your agent, and check the app against the list each prompt ends with.
hero:
  headline: Build your next app on Azure SQL
  subline: A free database, and prompts your coding agent can run.
  primary:
    label: Create a free database
    href: '#get-running'
    path: get-running
  secondary:
    label: Browse prompts
    href: '#build'
    path: build
  agents:
  - Claude Code
  - GitHub Copilot CLI
  - Codex
  - Cursor
demo:
  # Hero demo (_includes/hero-demo.html). It plays like an animated GIF: the
  # terminal types the prompt with the first app's name, shows the skills and
  # the build once, and the first app opens below the terminal's last line.
  # After that only the app name in the prompt and the app picture change,
  # every few seconds, through the list and around again; the terminal does
  # not replay. Without scripts or with reduced motion, the first app shows
  # finished. The run is illustrative, not recorded; the skills are real ones
  # from microsoft/microsoft-sql. `{app}` in the prompt is replaced by each
  # app's name. The apps are the Build section's apps and are drawn in
  # _includes/app-shot.html, keyed by `key`. Screen readers hear the shown
  # app's alt in place of the animation.
  prompt: Scaffold {app} on Azure SQL Database
  skills: [build-app-on-azure-sql, connect-from-typescript-and-node]
  shell: Build the app
  run: npm run build
  output: Compiled successfully
  apps:
  - key: board
    name: a team task board
    alt: 'From prompt to app: a prompt builds a team task board on Azure SQL with filters and due dates.'
  - key: inventory
    name: an inventory reservation app
    alt: 'From prompt to app: a prompt builds an inventory reservation app on Azure SQL that does not oversell.'
  - key: kb
    name: a knowledge base search app
    alt: 'From prompt to app: a prompt builds a knowledge base on Azure SQL that finds articles by meaning with vector search.'
  - key: revenue
    name: a revenue dashboard
    alt: 'From prompt to app: a prompt builds a revenue dashboard on Azure SQL with exact totals.'
  - key: shipments
    name: a shipment tracker
    alt: 'From prompt to app: a prompt builds a shipment tracker on Azure SQL that imports events safely.'
  - key: helpdesk
    name: a multi-tenant helpdesk
    alt: 'From prompt to app: a prompt builds a multi-tenant helpdesk on Azure SQL where each organization sees only its own tickets.'
# Get a database: two tabs. Each has numbered steps, some with a command to
# copy. `button` is the tab's main action; a step's `key` names its Copy button
# in telemetry. A link's href decides its kind: `#` stays on the page, `/` is a
# page on this site, anything else opens in a new tab. Keep every line short:
# the guides the links point at hold the detail.
quickstart_heading: Get a database
quickstart_text: Free in the cloud, or the same engine on your laptop.
quickstart:
- key: cloud
  name: Cloud, free tier
  title: Create a free Azure SQL database
  desc: 100,000 vCore seconds and 32 GB free every month. Needs an Azure subscription.
  button:
    label: Create a free database
    href: https://aka.ms/azuresqlhub
    id: azure-sql-free-database
  steps:
  - key: create
    title: Start free
    text: In the Azure SQL hub, under Create a database, select Start free.
  - key: access
    title: Open access
    text: Make yourself the Microsoft Entra admin and add your IP to the firewall.
  - key: verify
    title: Verify
    text: Run this in the portal's query editor.
    code: SELECT 1 AS connected;
  links:
  - label: Free tier limits
    href: https://learn.microsoft.com/azure/azure-sql/database/free-tier
    id: free-tier-docs
  - label: Have your agent create it
    href: https://learn.microsoft.com/azure/azure-sql/database/free-tier?tabs=agent-prompt#create-a-database
    id: free-tier-agent-prompt
- key: local
  name: Local container
  pill: Public preview
  title: Run the Azure SQL Database engine locally
  desc: The same engine in a container. No sign-up, and it works offline.
  steps:
  - key: pull
    title: Get the image
    code: docker pull mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: run
    title: Start the container
    code: |-
      MSSQL_SA_PASSWORD="Aa1$(openssl rand -hex 16)"
      docker run --name sqldb -e "ACCEPT_EULA=Y" \
        -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
        -p 127.0.0.1:1433:1433 -d \
        mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: query
    title: Connect and query
    code: |-
      docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT @@VERSION;"
  links:
  - label: Full guide, with PowerShell
    href: /container/get-started.html
    id: container-get-started
  - label: Troubleshooting
    href: /container/get-started.html#troubleshooting
    id: container-troubleshooting
  - label: What it leaves out
    href: /container/faq.html#feature-availability
    id: container-limitations
build_heading: Build with a prompt
build_text: Complete prompts for your coding agent. Copy one, paste it, and name your database.
build_note: Need a database? Create a free one.
build_note_link: Create a free one
build_note_href: '#get-running'
# The Build section shows two groups of prompts behind a filter: full apps
# first, then the building blocks (scenarios, below). Each app's prompt in
# build/ names the tables and the Azure SQL features listed here, so a card's
# details are what the prompt asks for. `shot` picks the app's picture from
# _includes/app-shot.html, the same one the hero demo shows. `needs` is shown
# when an app needs more than a database. Keep blurbs to one short line.
template_filter: Prompt type
template_groups:
- key: apps
  label: Apps
- key: blocks
  label: Building blocks
template_runs_on: [Azure SQL Database, Local container]
template_create:
  label: Create a free database
  href: https://aka.ms/azuresqlhub
template_inside:
  tables: Tables
  sql: Azure SQL features
templates:
- slug: team-board
  shot: board
  title: Team board
  tag: Full app
  blurb: Tasks with combined filters, due dates, edit conflicts, and change history.
  tables: [projects, members, tasks, tasks_history]
  sql:
  - [Temporal tables, "History kept by the engine."]
  - [Version check in the UPDATE, "A stale edit is refused."]
  - [CHECK constraints, "Only valid statuses and priorities."]
- slug: inventory-reservations
  shot: inventory
  title: Inventory reservations
  tag: Full app
  blurb: Reserve stock under concurrent orders without overselling.
  tables: [products, reservations, stock_movements, idempotency_keys]
  sql:
  - [Transactions and row locks, "The database decides the race."]
  - [CHECK constraints, "Stock cannot go negative."]
  - [Primary key on the idempotency key, "A retry cannot reserve twice."]
- slug: knowledge-base
  shot: kb
  title: Knowledge base search
  tag: Full app · AI
  blurb: Search support articles by meaning, with vector search in the engine.
  needs: an embedding model, such as one in Azure OpenAI
  tables: [articles, article_chunks]
  sql:
  - [VECTOR and VECTOR_DISTANCE, "Rank passages by cosine distance."]
  - [AI_GENERATE_EMBEDDINGS, "Chunk and embed in T-SQL."]
  - [JSON, "Filter by product and tags."]
- slug: revenue-reporting
  shot: revenue
  title: Revenue reporting
  tag: Full app
  blurb: Revenue reports that add up to the cent, refunds included.
  tables: [customers, products, orders, order_lines, refunds]
  sql:
  - [bigint cents, "Totals add up exactly."]
  - [GENERATE_SERIES, "Days with no sales show as zero."]
  - [Columnstore index, "Fast aggregates over order lines."]
- slug: shipment-tracker
  shot: shipments
  title: Shipment tracker
  tag: Full app
  blurb: Import event batches without duplicates, in an order that does not change.
  tables: [shipment_events, import_receipts]
  sql:
  - [OPENJSON, "A whole batch in one statement."]
  - [Composite primary key, "No second copy of an event."]
  - [Binary collation, "The same ordering on every run."]
- slug: multi-tenant-helpdesk
  shot: helpdesk
  title: Multi-tenant helpdesk
  tag: Full app
  blurb: Each organization sees only its own tickets, enforced by the database.
  tables: [organizations, tickets]
  sql:
  - [Row-level security, "Each organization stays in its own rows."]
  - [SESSION_CONTEXT, "Set per request, cleared on reuse."]
  - [Least-privilege app user, "The app cannot change the policy."]
# The building blocks. `shot` picks each one's picture from
# _includes/app-shot.html. `after` names the block whose project this one
# extends, and `cloud` marks a block that needs Azure SQL Database in the
# cloud; both show as one short line on the card.
scenarios:
- slug: javascript-app
  title: Start a Next.js app
  tag: JavaScript
  blurb: A read-only task page on Azure SQL, with no passwords.
  cloud: true
  shot: tasks
- slug: python-api
  title: Add a Python API
  tag: Python
  blurb: A FastAPI service that lists, creates, and completes tasks.
  cloud: true
  shot: api
- slug: rag-app
  title: Search text by meaning
  tag: Python / AI
  blurb: Embeddings in a VECTOR column, ranked with VECTOR_DISTANCE.
  cloud: true
  shot: search
- slug: serverless-api
  title: Add a serverless API
  tag: .NET
  blurb: Azure Functions that read and write through the SQL bindings.
  cloud: true
  shot: functions
- slug: event-driven-app
  title: React to data changes
  tag: .NET
  blurb: A function that runs when rows change.
  after: serverless-api
  after_title: Add a serverless API
  cloud: true
  shot: changes
- slug: multi-tenant
  title: Isolate each tenant's rows
  tag: JavaScript
  blurb: Row-level security, with tests that prove the isolation.
  after: javascript-app
  after_title: Start a Next.js app
  cloud: true
  shot: tenants
- slug: data-api
  title: Get a REST and GraphQL API
  tag: Data API builder
  blurb: Data API builder over a table. No handler code.
  shot: dab
- slug: local-to-cloud
  title: Move from the container to the cloud
  tag: Any stack
  blurb: Switch a local app to a free Azure SQL database.
  shot: cloud
workloads_heading: Built for AI workloads
workloads_text: In the same engine as the rest of your data.
workloads:
- title: Vector search
  text: A native VECTOR type and VECTOR_DISTANCE.
  icon: <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
  link:
    label: Vector docs
    href: https://learn.microsoft.com/sql/sql-server/ai/vectors
- title: Embeddings in T-SQL
  text: Call a model from a query. No separate pipeline.
  icon: <svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="8"/></svg>
  link:
    label: AI_GENERATE_EMBEDDINGS
    href: https://learn.microsoft.com/sql/t-sql/functions/ai-generate-embeddings-transact-sql
- title: JSON with relational data
  text: Flexible attributes beside your tables, in one query.
  icon: <svg viewBox="0 0 24 24"><path d="M8 4c-2 0-3 1-3 3v2c0 1.5-1 2.5-2 3 1 .5 2 1.5 2 3v2c0 2 1 3 3 3M16 4c2 0 3 1 3 3v2c0 1.5 1 2.5 2 3-1 .5-2 1.5-2 3v2c0 2-1 3-3 3"/></svg>
  link:
    label: JSON docs
    href: https://learn.microsoft.com/azure/azure-sql/database/json-features
- title: Knowledge base search
  text: An app prompt that uses all three.
  icon: <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 10h8M8 14h5"/></svg>
  link:
    label: See the prompt
    href: '#knowledge-base'
skills:
  heading: Microsoft SQL Agent Skills
  text: Instructions your agent loads when a task calls for them. Install once, then ask.
  agents:
  - key: claude
    name: Claude Code
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34
      1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>
    code: |-
      claude plugin marketplace add microsoft/microsoft-sql
      claude plugin install microsoft-sql@microsoft-sql
    note: Inside a session, the same commands start with <code>/plugin</code>.
  - key: copilot-cli
    name: GitHub Copilot CLI
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M23.922 16.997C23.061 18.492 18.063 22.02 12 22.02 5.937 22.02.939 18.492.078 16.997A.641.641 0 0 1 0 16.741v-2.869a.883.883 0 0 1 .053-.22c.372-.935 1.347-2.292 2.605-2.656.167-.429.414-1.055.644-1.517a10.098 10.098 0 0 1-.052-1.086c0-1.331.282-2.499 1.132-3.368.397-.406.89-.717 1.474-.952C7.255 2.937 9.248 1.98 11.978 1.98c2.731 0 4.767.957 6.166 2.093.584.235 1.077.546 1.474.952.85.869 1.132 2.037 1.132 3.368 0 .368-.014.733-.052 1.086.23.462.477 1.088.644 1.517 1.258.364 2.233 1.721 2.605 2.656a.841.841 0 0 1 .053.22v2.869a.641.641 0 0 1-.078.256Zm-11.75-5.992h-.344a4.359 4.359 0 0 1-.355.508c-.77.947-1.918 1.492-3.508 1.492-1.725 0-2.989-.359-3.782-1.259a2.137 2.137 0 0 1-.085-.104L4 11.746v6.585c1.435.779 4.514 2.179 8 2.179 3.486 0 6.565-1.4 8-2.179v-6.585l-.098-.104s-.033.045-.085.104c-.793.9-2.057 1.259-3.782 1.259-1.59 0-2.738-.545-3.508-1.492a4.359 4.359
      0 0 1-.355-.508Zm2.328 3.25c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm-5 0c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm3.313-6.185c.136 1.057.403 1.913.878 2.497.442.544 1.134.938 2.344.938 1.573 0 2.292-.337 2.657-.751.384-.435.558-1.15.558-2.361 0-1.14-.243-1.847-.705-2.319-.477-.488-1.319-.862-2.824-1.025-1.487-.161-2.192.138-2.533.529-.269.307-.437.808-.438 1.578v.021c0 .265.021.562.063.893Zm-1.626 0c.042-.331.063-.628.063-.894v-.02c-.001-.77-.169-1.271-.438-1.578-.341-.391-1.046-.69-2.533-.529-1.505.163-2.347.537-2.824 1.025-.462.472-.705 1.179-.705 2.319 0 1.211.175 1.926.558 2.361.365.414 1.084.751 2.657.751 1.21 0 1.902-.394 2.344-.938.475-.584.742-1.44.878-2.497Z"/></svg>
    code: |-
      copilot plugin marketplace add microsoft/microsoft-sql
      copilot plugin install microsoft-sql@microsoft-sql
    note: In a session, <code>/skills</code> lists what was installed.
  - key: codex
    name: Codex
    logo: <svg aria-hidden="true" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" xmlns="http://www.w3.org/2000/svg">    <g>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(60 12 12)"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(120 12 12)"/>  </g>  <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/></svg>
    code: |-
      codex plugin marketplace add microsoft/microsoft-sql --ref main
      codex plugin add microsoft-sql@microsoft-sql
    note: Codex uses <code>plugin add</code>, not <code>plugin install</code>.
  - key: cursor
    name: Cursor
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M11.503.131 1.891 5.678a.84.84 0 0 0-.42.726v11.188c0 .3.162.575.42.724l9.609 5.55a1 1 0 0 0 .998 0l9.61-5.55a.84.84 0 0 0 .42-.724V6.404a.84.84 0 0 0-.42-.726L12.497.131a1.01 1.01 0 0 0-.996 0M2.657 6.338h18.55c.263 0 .43.287.297.515L12.23 22.918c-.062.107-.229.064-.229-.06V12.335a.59.59 0 0 0-.295-.51l-9.11-5.257c-.109-.063-.064-.23.061-.23"/></svg>
    code: cursor-agent plugin marketplace add https://github.com/microsoft/microsoft-sql
    note: Then start <code>cursor-agent</code>, enter <code>/plugin</code>, and install microsoft-sql from the Marketplace tab.
  asks_label: 'Then ask:'
  chips:
  - key: create_free_database
    text: Create a free Azure SQL database for this project and connect to it
  - key: connect_node_passwordless
    text: Connect my Node app to Azure SQL Database without a password
  - key: add_vector_search
    text: Add vector search to this table
  - key: diagnose_slow_query
    text: This query is slow. Find out why and propose the smallest safe fix
  catalog:
    label: Browse all the skills
    text: Every skill and its source is at aka.ms/azuresql-skills.
videos_heading: Videos
videos:
- id: wZUPFCCByfw
  title: Build AI apps with VS Code Agents, GitHub Copilot, and the MSSQL extension
  text: Data Exposed, May 2026
  tag: Data Exposed
  href: https://www.youtube.com/watch?v=wZUPFCCByfw
  image: https://img.youtube.com/vi/wZUPFCCByfw/hqdefault.jpg
- id: foundations
  title: Azure SQL Database Foundations
  text: 'Four sessions: getting started, migration, performance, AI'
  tag: Series
  href: https://aka.ms/azuresqlfoundationseries
  image: https://devblogs.microsoft.com/wp-content/uploads/2026/08/word-image-22210-2.webp
- id: pq2drN2Qw5w
  title: 'Boost your SQL development in VS Code: Copilot, containers, and more'
  text: Carlos Robles, VS Code Live, Aug 2025
  tag: VS Code Live
  href: https://www.youtube.com/watch?v=pq2drN2Qw5w
  image: https://img.youtube.com/vi/pq2drN2Qw5w/hqdefault.jpg
- id: biJywQPbqn0
  title: AI-powered SQL development in VS Code with GitHub Copilot
  text: MSSQL extension v1.32, May 2025
  tag: Release
  href: https://www.youtube.com/watch?v=biJywQPbqn0
  image: https://img.youtube.com/vi/biJywQPbqn0/hqdefault.jpg
faq_heading: FAQ
faqs:
- question: What do I need?
  answer: A coding agent and a database, either a free Azure SQL database or the local container.
- question: What does it cost?
  answer: Nothing for the database within the free tier's monthly limits, and nothing for the container. An embedding model is billed by whoever provides it.
- question: Do I need the skills to use the prompts?
  answer: No. The prompts are self-contained. The skills help with what you ask next.
- question: Do the prompts work on the local container?
  answer: The apps do. Building blocks marked Cloud only need Azure SQL Database.
- question: Is it safe to let an agent write to my database?
  answer: Use a development database. Every prompt tells the agent to ask before it drops data, grants permissions, or creates Azure resources.
---
