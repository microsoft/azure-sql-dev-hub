---
layout: home
title: Azure SQL Developer Hub
description: Explore app templates and practical patterns for Azure SQL Database. Build dashboards, APIs, search, and multi-tenant applications with your preferred stack.
hero:
  headline: Azure SQL, built for AI workloads
  tagline: Bring the idea. Build with Azure SQL.
  subline: Start with a prompt. Give your AI coding agent SQL skills, and make your next app yours.
  agents:
  - Claude Code
  - GitHub Copilot
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
  # app's name. The apps follow the idea-to-app reference apps (task board,
  # stock reservation, sales analytics, import dashboard, tenant helpdesk) and
  # are drawn in the include, keyed by `key`. The title and sub appear in the
  # markdown twin, and screen readers hear the shown app's alt in place of the
  # animation.
  title: From idea to app
  sub: Azure SQL for the agent era.
  prompt: Scaffold {app} on Azure SQL Database
  skills: [build-app-on-azure-sql, connect-from-typescript-and-node]
  shell: Build the app
  run: npm run build
  output: Compiled successfully
  apps:
  - key: board
    name: a team task board
    alt: 'From idea to app: a prompt builds a team task board on Azure SQL with filters and due dates.'
  - key: inventory
    name: an inventory reservation app
    alt: 'From idea to app: a prompt builds an inventory reservation app on Azure SQL that never oversells.'
  - key: revenue
    name: a revenue dashboard
    alt: 'From idea to app: a prompt builds a revenue dashboard on Azure SQL with exact totals.'
  - key: shipments
    name: a shipment tracker
    alt: 'From idea to app: a prompt builds a shipment tracker on Azure SQL that imports events safely.'
  - key: helpdesk
    name: a multi-tenant helpdesk
    alt: 'From idea to app: a prompt builds a multi-tenant helpdesk on Azure SQL where each organization sees only its own tickets.'
# Get a database running: two ways to get Azure SQL Database, as cards. Each
# card opens its setup dialog, laid out like the template details: the manual
# steps on the left; on the right a Prefer VS Code? card, then the coding-agent
# route. Without scripts the dialogs show in place below the cards. `id`
# prefixes each Copy button's telemetry id. `vscode.type` is the MSSQL
# extension's deep link type (vscode://ms-mssql.mssql/deploy?type=), a public
# contract kept stable in vscode-mssql; `vscode.text` and the version note
# appear in the markdown twin only. `engines` adds a picker above the steps:
# commands are written for Docker, each other engine lists `swap` pairs,
# applied in order, that turn them into its own (Apple container's match the
# MSSQL extension's wizard), `use` says which command to use when the picker
# can't run, and `key` is the telemetry runtime id (`runtime` overrides it).
# In `links`, a path on this site is a page here; a full URL is outbound, of
# `type` docs or other.
setup_heading: Get a database running
setup_text: Start free in Azure, or run the same engine on your machine. Set it up yourself or hand it to your coding agent.
setup_labels:
  open: Set it up
  manual: Set it up yourself
  agent: Set it up with your coding agent
  agents_label: Works with
  copy: Copy prompt
  show_prompt: See the prompt
  resources: Resources
  vscode: Set it up in VS Code
  vscode_title: Prefer VS Code?
  vscode_sub: Set it up with the MSSQL extension
  vscode_open: Open in VS Code
  vscode_need: Needs the MSSQL extension 1.49 or later.
  vscode_get: Get the extension
  vscode_get_href: https://marketplace.visualstudio.com/items?itemName=ms-mssql.mssql
  engine: Choose your container engine
setup:
- key: free
  id: free-setup
  title: Azure SQL Database, free tier
  icon: <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 8.5a4 4 0 0 1-.5 9.5H7z"/></svg>
  card: A serverless database in Azure with a monthly free allowance. Up to 10 free databases per subscription.
  summary: A General Purpose serverless database with a monthly free allowance, created in the Azure portal in a few minutes.
  steps:
  - key: before
    title: Before you start
    text: You need an Azure subscription with permission to create resources. Most subscription types work; Azure for Students Starter doesn't.
  - key: create
    title: Create the database
    text: Open the Azure SQL hub and select <b>Start free</b>. On <b>Basics</b>, pick the subscription, resource group, database name and server. If you create a new server, choose Microsoft Entra authentication. Check that <b>Estimated cost/month</b> shows 0, then select <b>Review + create</b> and <b>Create</b>.
    link:
      label: Open the Azure SQL hub
      href: https://aka.ms/azuresqlhub
  - key: access
    title: Open access
    text: Add your IP to the firewall and sign in with Microsoft Entra. Both are on the server, under Networking and Microsoft Entra ID.
  - key: verify
    title: Verify
    text: Run SELECT 1 in the portal's query editor or the MSSQL extension for VS Code. The database's Overview page shows <b>Free monthly vCore amount</b>.
    code: SELECT 1 AS connected;
  vscode:
    type: azureSqlDatabase
    text: The MSSQL extension creates the free database from your editor and connects to it. Sign in to Azure when it asks.
  free:
    title: What's free, every month
    # Each tile: label, value, and an optional unit shown small under the value.
    tiles:
    - [Compute, '100,000', vCore seconds]
    - [Data storage, 32 GB]
    - [Backup storage, 32 GB]
    - [Free databases, '10', per subscription]
  agent:
    prompt: Create a free Azure SQL Database in my Azure subscription using the free offer, and pause it when the monthly free limit is reached. Use Microsoft Entra authentication only, add my current IP address to the server firewall, then connect and run SELECT 1. Ask me which subscription and region to use, and show me each command before you run it.
  links:
  - label: Full guide on Microsoft Learn
    id: free-setup-docs
    type: docs
    href: https://learn.microsoft.com/azure/azure-sql/database/free-tier
  - label: Prerequisites
    id: free-tier-prerequisites
    type: docs
    href: https://learn.microsoft.com/azure/azure-sql/database/free-tier#prerequisites
  - label: Limits
    id: free-tier-limits
    type: docs
    href: https://learn.microsoft.com/azure/azure-sql/database/free-tier#considerations-and-limitations
- key: container
  id: container
  title: Azure SQL Database container
  pill: Public preview
  icon: <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/></svg>
  card: The Azure SQL Database engine in a container, for development, testing and CI. It runs offline after the first pull.
  summary: The Azure SQL Database engine on your machine. Free, no Azure subscription.
  steps:
  - key: pull
    title: Get the image
    text: Pull the public image from Microsoft Container Registry. No sign-up needed.
    code: docker pull mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: run
    title: Start the container
    text: In a bash or zsh shell, generate a strong SA password, then start the engine on port 1433, bound to localhost.
    code: |-
      MSSQL_SA_PASSWORD="Aa1$(openssl rand -hex 16)"
      docker run --name sqldb -e "ACCEPT_EULA=Y" \
        -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
        -p 127.0.0.1:1433:1433 -d \
        mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: query
    title: Connect and query
    text: The container bundles sqlcmd. A result that names Microsoft SQL Azure confirms the Azure SQL Database engine.
    code: |-
      docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT @@VERSION;"
  copy_all: Copy all three commands
  engines:
  - key: docker
    name: Docker
    use: <code>docker</code>
    note: Docker 24 or later, with the engine running. <code>docker info</code> checks it.
  - key: podman
    name: Podman
    use: <code>podman</code>
    swap:
    - ['docker ', 'podman ']
    note: Podman 5.0 or later. On macOS and Windows, Podman runs in a VM, so start it first with <code>podman machine start</code>.
  - key: apple
    runtime: unknown
    name: Apple container
    use: <code>container</code>, with <code>container image pull</code> to pull and <code>--detach</code> in place of <code>-d</code>
    swap:
    - ['docker pull ', 'container image pull ']
    - [' -d ', ' --detach ']
    - ['docker ', 'container ']
    note: Apple's container tool, on a Mac with Apple silicon and macOS 26 or later. Start it with <code>container system start</code>; <code>container system status</code> checks it.
  - key: wsl
    name: WSL
    use: <code>wslc</code>
    swap:
    - ['docker ', 'wslc ']
    note: WSL containers on Windows 11. The <code>wslc</code> command comes with WSL, and <code>wslc version</code> checks it.
  vscode:
    type: azureSqlContainer
    text: The MSSQL extension creates the container in a few clicks and connects to it. No Azure subscription needed.
  agent:
    prompt: Add a local Azure SQL Database to this project, then scaffold the schema, migrations and data-access layer for my stack.
  links:
  - label: Prerequisites
    id: container-prerequisites
    href: /container/get-started.html#prerequisites
  - label: Limitations
    id: container-limitations
    href: /container/faq.html#feature-availability
  - label: Troubleshooting
    id: container-troubleshooting
    href: /container/get-started.html#troubleshooting
  - label: FAQ
    id: container-faq
    href: /container/faq.html
  - label: View image on MCR
    id: container-image
    type: other
    href: https://mcr.microsoft.com/artifact/mar/mssql/azure-sql-db-server
then:
  from: Local or free tier
  to: Azure SQL Database
  note: Same code, connection string changes, app goes live.
build_heading: Find a template for your next app
build_text: Full apps and focused building blocks for dashboards, APIs, search, and more.
build_note: No database yet? Get a database running.
build_note_link: Get a database running
build_note_href: '#get-running'
build_steps:
  - Choose a template
  - Review the build prompt
  - Build and customize
# The Build section shows two groups of templates behind a filter, as in the
# redesign: full apps first, then the building blocks (scenarios, below). The
# full apps follow the idea-to-app reference apps in the AgentSkills repo: each
# prompt in build/ keeps the reference app's brief and exact semantics, and the
# details here come from its prompt and schema. `shot` picks the app's picture
# from _includes/app-shot.html, the same one the hero demo shows.
template_filter: Template type
template_groups:
- key: apps
  label: Apps
- key: blocks
  label: Building blocks
template_stack: Your stack, or TypeScript and Node
template_runs_on: [Azure SQL Database, Microsoft Entra ID]
# The template details, laid out like a template page: the app and what it
# builds on the left, Build with AI on the right. `features` and `covers` stay
# for the markdown twin.
template_inside:
  build_ai: Build it with your coding agent
  copy_text: Paste it into Claude Code, GitHub Copilot, Codex or Cursor, and your agent builds the app.
  # A collapsed section under Copy prompt.
  skills_title: First time? Add the Azure SQL skills
  skills_text: One install for Claude Code, GitHub Copilot, Codex and Cursor.
  skills_code: npx skills add microsoft/microsoft-sql
  before_text: Needs an Azure SQL Database. No database yet? <a href="#get-running">Get one running</a>.
  features: What it does
  tables: Tables it creates
  sql: Azure SQL features it uses
  try: Check it works
templates:
- slug: team-board
  shot: board
  title: Team board
  tag: Full app
  blurb: Filter by project, assignee, status, priority and overdue together. Due dates from one fixed clock, seed data that's safe to rerun, and edits that survive a restart.
  summary: A team task board with combined filters and due dates.
  covers: Filters, due dates, seed data, restarts
  description:
  - >-
    A shared task board for a small team. Tasks move from Todo to In progress to Done, each with a priority, an assignee and a due date. Narrow the board by project, person, status, priority and what's overdue, all at once, and search titles as plain text, punctuation included.
  - >-
    Azure SQL keeps the board honest. The database accepts only real statuses and priorities, a task can't point at a project or person that doesn't exist, and due dates are calendar dates, so overdue means the same thing on every run. The sample tasks load once, and your edits are still there after a restart.
  features:
  - Todo, In progress and Done, with priority and due dates
  - Filters by project, assignee, status, priority and overdue, combined
  - Title search that treats punctuation as text
  - Seed data that imports once and survives restarts
  tables:
  - [projects, "The projects tasks belong to"]
  - [members, "Who tasks can be assigned to"]
  - [tasks, "Title, description, status, priority, assignee and due date"]
  sql:
  - [CHECK constraints, "Status and priority accept only the allowed values, enforced by the database."]
  - [Foreign keys, "A task can't point at a project or member that doesn't exist."]
  - [date columns, "Due dates are calendar dates, so overdue is a plain comparison with the app's reference date."]
  try:
  - [Stack three filters, "Pick a project, an assignee and Overdue. Only tasks that match all three stay."]
  - [Restart everything, "Edit a seeded task, then restart the app and the database. The edit is still there."]
  - [Check what's overdue, "Overdue comes from the app's own clock, so the same tasks show as overdue on every run."]
- slug: inventory-reservations
  shot: inventory
  title: Inventory reservations
  tag: Full app
  blurb: Reserve stock under concurrent orders without overselling. Retries return the same result, and stock and audit rows change together.
  summary: Reserve stock without overselling, even when orders arrive together.
  covers: Concurrency, retries, transactions
  description:
  - >-
    A reservation system for a small equipment supplier. Browse the stock, see what's on hand, reserved and still available, and reserve, confirm or cancel orders. Every stock change is recorded, so you can trace how each number got where it is.
  - >-
    The hard part is two customers going for the last item at the same moment. Azure SQL settles it: one reservation wins, the other is turned away, and available stock can't drop below zero. A retried request gets the original answer instead of reserving twice, and a reservation and its audit record are saved together or not at all.
  features:
  - Shows on hand, reserved and available stock
  - Reserve, confirm and cancel, with fixed state rules
  - Idempotency keys, so a retry doesn't reserve twice
  - An audit entry for every stock movement
  tables:
  - [products, "Name and on-hand stock, which can't go below zero"]
  - [reservations, "Product, quantity and state: active, confirmed or cancelled"]
  - [movements, "The audit trail of stock changes"]
  - [requests, "Each idempotency key with its payload and first response"]
  sql:
  - [Transactions, "A reservation and its audit entry commit together or not at all."]
  - [CHECK constraints, "Quantities stay positive, stock can't go negative, and states stay valid."]
  - [Primary key on the idempotency key, "A retry finds the stored response instead of reserving again."]
  try:
  - [Buy the last item twice at once, "Two reservations race for the last unit. One succeeds; the other is rejected."]
  - [Retry a reservation, "Send the same request again. You get the original result, not a second reservation."]
  - [Fail halfway through, "Make the audit write fail. Stock and the audit trail both stay unchanged."]
- slug: revenue-reporting
  shot: revenue
  title: Revenue reporting
  tag: Full app
  blurb: Exact money arithmetic, partial refunds, order-date cohorts, and joins that never double-count.
  summary: Revenue reports that add up to the cent.
  covers: Money math, refunds, date ranges, joins
  description:
  - >-
    A revenue dashboard for an online shop. It shows net revenue, completed orders and average order value, a daily revenue chart and the best-selling products. Filter by date range and region, drill down to the orders behind any number, and export what you see to CSV.
  - >-
    Every figure adds up to the cent. Money is kept in whole cents rather than decimals that drift, refunds are totalled per item before they're matched to sales so no sale is counted twice, and a refund counts against the day the order was placed, not the day it was issued.
  features:
  - Net revenue, completed orders and average order value
  - A daily revenue chart and top products
  - Filters by date range and region, with drill-down to orders
  - A CSV export that matches the drill-down
  tables:
  - [customers, "Name and region, which may be empty"]
  - [products, "What was sold"]
  - [orders, "Customer, order time and status"]
  - [lines, "Quantity and unit price in cents"]
  - [refunds, "Partial or full, per line"]
  sql:
  - [Integer cents, "Money is stored as whole cents, so totals add up exactly."]
  - [Aggregate before joining, "Refunds are summed per line before the join, so no sale is counted twice."]
  - [Foreign keys, "Every line belongs to an order and every refund to a line."]
  try:
  - [Refund part of an order twice, "Revenue drops by exactly the two refunds. The sale is counted once."]
  - [Refund days later, "The refund counts against the order's date, not the day it was made."]
  - [Import the same data twice, "Row counts and totals don't change."]
- slug: shipment-tracker
  shot: shipments
  title: Shipment tracker
  tag: Full app
  blurb: Import shipment events atomically, catch duplicates and conflicts, replay safely, and order late events the same way on every run.
  summary: Track shipments from imported event files.
  covers: Atomic imports, duplicates, replay, ordering
  description:
  - >-
    A tracker for shipments whose updates arrive as files of carrier events. Import a batch as CSV or JSON and get a receipt showing what was accepted, what was a duplicate and what was rejected. Then follow each shipment's history, its latest status and a daily count of exceptions.
  - >-
    Imports are all or nothing: new events and the batch's receipt are saved together. Azure SQL recognizes an event it has already stored, so importing the same file twice changes nothing, and an event that contradicts the stored one is rejected rather than overwriting it. Late events sort the same way on every run, so the latest status doesn't depend on arrival order.
  features:
  - Imports CSV or JSON event batches
  - A receipt for each batch, with accepted, duplicate and rejected rows
  - Shipment histories and latest status
  - Daily exception counts
  tables:
  - [events, "One row per source and event ID"]
  - [receipts, "One receipt per batch, with its counts and errors"]
  sql:
  - [Composite primary key, "Source and event ID identify an event, so the database refuses a second copy."]
  - [Binary collation, "Identifiers compare in ordinal order, the same way on every run."]
  - [Transactions, "New events and the batch receipt commit together."]
  try:
  - [Import the same file twice, "The second import returns the original receipt and changes nothing."]
  - [Send a conflicting event, "An event that disagrees with the stored one is rejected, not overwritten."]
  - [Deliver events out of order, "Latest status comes out the same, whatever order the events arrive in."]
- slug: multi-tenant-helpdesk
  shot: helpdesk
  title: Multi-tenant helpdesk
  tag: Full app
  blurb: Signed identities, tenant isolation in both the API and the database, role checks, and safe connection reuse.
  summary: A helpdesk where each organization sees only its own tickets.
  covers: Identity, isolation, roles, connection reuse
  description:
  - >-
    A support desk shared by several organizations. People list, create, update, search and export tickets, and administrators assign them to teammates. Everyone sees only their own organization's tickets.
  - >-
    Who you are comes from your signed identity, not from what a request claims. Azure SQL enforces the separation itself with row-level security, so even a query that forgets to filter can't reach another organization's rows. The app connects as a database user that can work with tickets but can't change those rules, and a reused connection is reset before the next person's request.
  features:
  - List, create, update, search and export tickets
  - "Administrators assign tickets; members can't"
  - The organization comes from the signed identity, not the request
  - Tenant checks in the API and in the database
  tables:
  - [tickets, "Title, description, status, assignee and owning organization"]
  sql:
  - [Row-level security, "A filter predicate and block predicates keep each organization in its own rows."]
  - [SESSION_CONTEXT, "Set for each request from the signed identity, and reset when a connection is reused."]
  - [A least-privilege app user, "The app's database user reads and writes tickets but can't change the security policy."]
  try:
  - [Sign in as the other organization, "You see only that organization's tickets, in the API and in the database."]
  - [Change the organization in a request, "It's ignored. The signed identity decides."]
  - [Assign a ticket as a member, "It's refused. Only that organization's administrators can assign."]
# The building blocks. `shot` picks each one's picture from
# _includes/app-shot.html, drawn like the apps above.
scenarios:
- num: '01'
  slug: javascript-app
  title: Build a task-tracking app
  tag: JavaScript
  blurb: Build a web app that displays tasks stored in Azure SQL. Start with sample data and make it your own.
  shot: tasks
- num: '02'
  slug: python-api
  title: Build an API for your app
  tag: Python
  blurb: Give your app a way to create, complete, and retrieve tasks. Build a Python API that connects to Azure SQL with Microsoft Entra, no passwords.
  shot: api
- num: '03'
  slug: rag-app
  title: Search your content by meaning
  tag: Python / AI
  blurb: Find relevant text with vector search in Azure SQL. Build the retrieval layer for a RAG app using sample text and an embedding model you provide.
  shot: search
- num: '04'
  slug: serverless-api
  title: Create a serverless task API
  tag: .NET
  blurb: Read and save tasks through an Azure Functions API backed by Azure SQL. Build and test the functions locally.
  shot: functions
- num: '05'
  slug: event-driven-app
  title: Respond to data changes
  tag: .NET
  blurb: Extend the serverless API with a function that reacts when tasks change in Azure SQL. Log inserts, updates, and deletes as a starting point for automation.
  shot: changes
- num: '06'
  slug: multi-tenant
  title: Separate each customer's data
  tag: JavaScript
  blurb: Extend a task app for multiple customers. Add row-level security and test that one tenant cannot read another tenant's tasks.
  shot: tenants
workloads_heading: Search, AI, and access control
workloads_text: Add semantic search, work with embeddings, and keep access scoped to the right users.
workloads:
- title: Vector search
  text: A native VECTOR type and VECTOR_DISTANCE. Store embeddings next to the rows they describe.
  icon: <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
  link:
    label: Vector docs
    href: https://learn.microsoft.com/sql/relational-databases/vectors/vectors-sql-server
- title: Embeddings in T-SQL
  text: Generate and chunk from inside the database with external model calls. No separate pipeline.
  icon: <svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="8"/></svg>
  link:
    label: AI_GENERATE_EMBEDDINGS
    href: https://learn.microsoft.com/sql/t-sql/functions/ai-generate-embeddings-transact-sql
- title: RAG, end to end
  text: Chunk, embed, store, and retrieve content in Azure SQL to ground responses in your application.
  icon: <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 10h8M8 14h5"/></svg>
  link:
    label: Copy the RAG prompt
    href: '#rag-app'
- title: Access scoped to each user
  text: Use Microsoft Entra identity and row-level security to keep each tenant's data separate.
  icon: <svg viewBox="0 0 24 24"><path d="M12 3l8 4v6c0 4-3.5 7-8 8-4.5-1-8-4-8-8V7z"/></svg>
  link:
    label: Row-level security docs
    href: https://learn.microsoft.com/sql/relational-databases/security/row-level-security
skills:
  heading: Microsoft SQL Agent Skills
  text: Building with a coding agent? Add Azure SQL guidance to the tools you already use.
  agents:
  - key: claude
    name: Claude Code
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34
      1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>
    code: 'claude plugin marketplace add microsoft/microsoft-sql

      claude plugin install microsoft-sql@microsoft-sql'
    note: 'Two commands: register the marketplace, then install the plugin with every skill. Or the portable form: <code>gh skill install microsoft/microsoft-sql --all --agent claude-code</code>.'
  - key: vscode-copilot
    name: GitHub Copilot
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M23.922 16.997C23.061 18.492 18.063 22.02 12 22.02 5.937 22.02.939 18.492.078 16.997A.641.641 0 0 1 0 16.741v-2.869a.883.883 0 0 1 .053-.22c.372-.935 1.347-2.292 2.605-2.656.167-.429.414-1.055.644-1.517a10.098 10.098 0 0 1-.052-1.086c0-1.331.282-2.499 1.132-3.368.397-.406.89-.717 1.474-.952C7.255 2.937 9.248 1.98 11.978 1.98c2.731 0 4.767.957 6.166 2.093.584.235 1.077.546 1.474.952.85.869 1.132 2.037 1.132 3.368 0 .368-.014.733-.052 1.086.23.462.477 1.088.644 1.517 1.258.364 2.233 1.721 2.605 2.656a.841.841 0 0 1 .053.22v2.869a.641.641 0 0 1-.078.256Zm-11.75-5.992h-.344a4.359 4.359 0 0 1-.355.508c-.77.947-1.918 1.492-3.508 1.492-1.725 0-2.989-.359-3.782-1.259a2.137 2.137 0 0 1-.085-.104L4 11.746v6.585c1.435.779 4.514 2.179 8 2.179 3.486 0 6.565-1.4 8-2.179v-6.585l-.098-.104s-.033.045-.085.104c-.793.9-2.057 1.259-3.782 1.259-1.59 0-2.738-.545-3.508-1.492a4.359 4.359
      0 0 1-.355-.508Zm2.328 3.25c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm-5 0c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm3.313-6.185c.136 1.057.403 1.913.878 2.497.442.544 1.134.938 2.344.938 1.573 0 2.292-.337 2.657-.751.384-.435.558-1.15.558-2.361 0-1.14-.243-1.847-.705-2.319-.477-.488-1.319-.862-2.824-1.025-1.487-.161-2.192.138-2.533.529-.269.307-.437.808-.438 1.578v.021c0 .265.021.562.063.893Zm-1.626 0c.042-.331.063-.628.063-.894v-.02c-.001-.77-.169-1.271-.438-1.578-.341-.391-1.046-.69-2.533-.529-1.505.163-2.347.537-2.824 1.025-.462.472-.705 1.179-.705 2.319 0 1.211.175 1.926.558 2.361.365.414 1.084.751 2.657.751 1.21 0 1.902-.394 2.344-.938.475-.584.742-1.44.878-2.497Z"/></svg>
    code: npx skills add microsoft/microsoft-sql
    note: Or <code>gh skill install microsoft/microsoft-sql --all --agent github-copilot</code>. Find them in Copilot Chat under Configure Chat, Skills tab, or type <code>/skills</code>. Committed to <code>.github/skills/</code> in your repo, they also reach the Copilot coding agent with no install.
  - key: codex
    name: Codex
    logo: <svg aria-hidden="true" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" xmlns="http://www.w3.org/2000/svg">    <g>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(60 12 12)"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(120 12 12)"/>  </g>  <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/></svg>
    code: npx skills add microsoft/microsoft-sql
    note: The repository is an Agent Plugins package, so Codex installs it directly. Confirm with <code>ls .codex/skills</code>.
  - key: cursor
    name: Cursor
    logo: <svg aria-hidden="true" fill="currentColor" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M11.503.131 1.891 5.678a.84.84 0 0 0-.42.726v11.188c0 .3.162.575.42.724l9.609 5.55a1 1 0 0 0 .998 0l9.61-5.55a.84.84 0 0 0 .42-.724V6.404a.84.84 0 0 0-.42-.726L12.497.131a1.01 1.01 0 0 0-.996 0M2.657 6.338h18.55c.263 0 .43.287.297.515L12.23 22.918c-.062.107-.229.064-.229-.06V12.335a.59.59 0 0 0-.295-.51l-9.11-5.257c-.109-.063-.064-.23.061-.23"/></svg>
    code: npx skills add microsoft/microsoft-sql
    note: Or <code>gh skill install microsoft/microsoft-sql --all --agent cursor</code>. Confirm with <code>ls .cursor/skills</code>.
  chips:
  - key: connect_node_passwordless
    text: Connect my Node app to Azure SQL Database without a password
  - key: scaffold_data_layer
    text: Scaffold the schema, migrations, and data layer for this app
  - key: add_vector_search
    text: Add vector search to this table and make it use the index
  - key: troubleshoot_40613
    text: Why does my first query after idle fail with 40613
  # The page shows none of these notes. Each agent's note and the catalog line
  # appear in the markdown twin only, which has no links, so agents still get
  # the other install commands and the catalog's address.
  catalog: Full catalog, every skill's source, and the feedback form at aka.ms/azuresql-skills.
tools_heading: Build with the tools you know.
tools:
- key: github-copilot
  title: GitHub Copilot
  agent_logo: vscode-copilot
  text: Write and explain SQL queries.
  label: Explore SQL capabilities
  href: https://learn.microsoft.com/sql/tools/visual-studio-code-extensions/github-copilot/overview
- key: vscode-mssql
  title: VS Code + MSSQL
  image: /assets/img/vscode.png
  text: Design schemas and query your data.
  label: Explore the extension
  href: https://learn.microsoft.com/sql/tools/visual-studio-code-extensions/mssql/mssql-extension-visual-studio-code
- key: ssms
  title: SQL Server Management Studio
  image: /assets/img/ssms.svg
  text: Inspect query plans and troubleshoot.
  label: Explore SSMS
  href: https://learn.microsoft.com/ssms/sql-server-management-studio-ssms
videos_heading: See it in action
videos_text: Longer walkthroughs from the Microsoft SQL team.
# The video marked `featured` (else the first) leads, large; the next three sit
# beside it as Up next. Any more go in a grid below, behind a Show more button
# once the page script runs. Add a video anywhere in the list; to change the
# lead, move `featured`.
videos_up_next: Up next
videos_all: All videos on YouTube
videos_all_href: https://aka.ms/microsoftsqlyt
videos_more: Show N more videos
videos_less: Show fewer videos
videos:
- id: pq2drN2Qw5w
  title: 'Boost your SQL development in VS Code: Copilot, containers, and more'
  text: Carlos Robles, VS Code Live, Aug 2025
  tag: VS Code Live
  href: https://www.youtube.com/watch?v=pq2drN2Qw5w
  image: https://img.youtube.com/vi/pq2drN2Qw5w/hqdefault.jpg
- id: wZUPFCCByfw
  featured: true
  title: Build AI apps with VS Code Agents, GitHub Copilot, and the MSSQL extension
  text: Data Exposed, May 2026
  tag: Data Exposed
  href: https://www.youtube.com/watch?v=wZUPFCCByfw
  image: https://img.youtube.com/vi/wZUPFCCByfw/hqdefault.jpg
- id: biJywQPbqn0
  title: AI-powered SQL development in VS Code with GitHub Copilot
  text: MSSQL extension v1.32, May 2025
  tag: Release
  href: https://www.youtube.com/watch?v=biJywQPbqn0
  image: https://img.youtube.com/vi/biJywQPbqn0/hqdefault.jpg
- id: foundations
  title: Azure SQL Database Foundations
  text: 'Four sessions: getting started, migration, performance, AI'
  tag: Series
  href: https://aka.ms/azuresqlfoundationseries
  image: https://devblogs.microsoft.com/wp-content/uploads/2026/08/word-image-22210-2.webp
faqs:
- question: What do I need to get started?
  answer: An Azure account and a development database. The free tier covers everything on this page, within its limits. If you want to work offline, run the container instead. It is in public preview and needs no sign-up.
- question: Is it safe to let an agent write to my database?
  answer: Use a development database with least-privilege access. The skills default to parameterised queries, Entra identity over passwords, and row-level security for multi-tenant work. Review schema changes before they run against anything real.
- question: Do I need the container?
  answer: No. Every prompt here targets Azure SQL Database in the cloud. The container is the local option, in public preview.
- question: What does this cost?
  answer: The free tier covers the database for every example here, within its limits; see the tier details for what those are. The RAG example needs an embedding service, priced by whoever provides it; the prompt asks which one you have before using it.
- question: How is this different from SQL Server?
  answer: Same engine family, managed for you, with features that ship to Azure SQL Database first. The container runs the Azure SQL Database engine, not the SQL Server image.
---
