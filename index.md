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
  copy: Copy prompt
  show_prompt: See the prompt
  resources: Resources
  vscode: Set it up in VS Code
  vscode_title: Set it up in VS Code
  vscode_sub: A few clicks with the MSSQL extension
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
  summary: A serverless database with a monthly free allowance, created in the Azure portal in a few minutes.
  # Shown under Set it up yourself, before the steps.
  need: You need an Azure subscription that can create resources. Azure for Students Starter doesn't work.
  steps:
  # A step's link is set inside its text where the text names it.
  - key: create
    title: Start a free database
    text: Open the Azure SQL hub and select <b>Start free</b>.
    link:
      label: Open the Azure SQL hub
      href: https://aka.ms/azuresqlhub
  - key: basics
    title: Fill in the basics
    text: Pick the subscription, resource group, database name and server. For a new server, choose Microsoft Entra authentication.
  - key: review
    title: Create it
    text: Check that <b>Estimated cost/month</b> shows 0, then select <b>Review + create</b> and <b>Create</b>.
  - key: access
    title: Open access
    text: On the server, add your IP under <b>Networking</b> and sign in under <b>Microsoft Entra ID</b>.
  - key: verify
    title: Verify
    text: Run this in the portal's query editor or the MSSQL extension for VS Code.
    code: SELECT 1 AS connected;
  vscode:
    type: azureSqlDatabase
    text: The MSSQL extension creates the free database from your editor and connects to it. Sign in to Azure when it asks.
  free:
    title: What's free, every month
    # Each tile: label, value, and an optional unit shown small under the value.
    tiles:
    - [Compute, '100,000', vCore seconds]
    - [Data storage, 32 GB, per database]
    - [Backup storage, 32 GB, per database]
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
    text: It's public on Microsoft Container Registry. No sign-up needed.
    code: docker pull mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: run
    title: Start the container
    text: In bash or zsh. This makes a strong SA password and starts the engine on localhost, port 1433.
    code: |-
      MSSQL_SA_PASSWORD="Aa1$(openssl rand -hex 16)"
      docker run --name sqldb -e "ACCEPT_EULA=Y" \
        -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
        -p 127.0.0.1:1433:1433 -d \
        mcr.microsoft.com/mssql/azure-sql-db-server:latest
  - key: query
    title: Connect and query
    text: Run this in the same terminal, so it can read the password. The result should name <b>Microsoft SQL Azure</b>.
    code: |-
      docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
        -Q "SELECT @@VERSION;"
  copy_all: Copy all three commands
  engines:
  - key: docker
    name: Docker
    use: <code>docker</code>
    note: You need Docker 24 or later, with the engine running. <code>docker info</code> checks it.
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
  agents_for: For Claude Code, GitHub Copilot, Codex or Cursor.
  # The agent route's two steps, in the setup and template dialogs.
  skills_title: First time? Add the Azure SQL skills
  paste_title: Paste the prompt into your agent
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
# The apps below show a screenshot in place of a drawn screen: `img` names
# its files in assets/img/apps and `window` is the window's title. Each is a
# real app built from its prompt, restyled in the Fluent look and shown in use
# (assets/img/apps/SOURCES.md).
- slug: docs-chat
  img: docs-chat
  window: Contoso Handbook
  title: Chat with your docs
  tag: Full app
  blurb: Answers grounded in your documents, each citing the passages it used. Passages are found with VECTOR_DISTANCE in SQL, and conversations pick up where they left off.
  summary: Ask your team's documents a question and see where the answer came from.
  covers: Vector search, citations, conversations
  description:
  - >-
    A question-and-answer app for a team handbook. Add text or Markdown documents, ask questions in a chat, and get answers that cite the passages they came from. Conversations are saved, so you can open one later and keep going.
  - >-
    Azure SQL holds everything, embeddings included. Each passage's embedding sits in a VECTOR column, and the three passages nearest a question are found with VECTOR_DISTANCE in SQL rather than in app code. When nothing is close enough, the answer says the documents don't cover it. Deleting a document removes its passages in one transaction, so it's never cited again.
  features:
  - Text or Markdown documents, split into numbered passages
  - Answers that cite each passage by document and number
  - A plain "not covered" when the documents don't say
  - Saved conversations you can reopen and continue
  tables:
  - [documents, "Title and body"]
  - [passages, "Each document's numbered passages and their embeddings"]
  - [conversations, "A title for each saved chat"]
  - [messages, "Role, text, citations and time, in order"]
  sql:
  - [VECTOR type, "Embeddings are stored in the database, not in a separate vector store."]
  - [VECTOR_DISTANCE, "Cosine distance in SQL finds the three passages nearest a question."]
  - [Transactions, "A document, its passages and their embeddings are deleted together."]
  try:
  - [Ask about vacation, "Ask how many vacation days you get. The answer says 20 and cites the Leave policy."]
  - [Ask what it doesn't know, "Ask for the office Wi-Fi password. The answer says the documents don't cover it and cites nothing."]
  - [Delete a document, "Delete the Expense policy. A question about meal limits no longer cites it."]
- slug: ask-your-data
  img: ask-your-data
  window: Contoso Sales
  title: Ask your data
  tag: Full app
  blurb: Plain-English questions become one read-only query. See the SQL, the result and a chart, run by a database user that can only read.
  summary: Ask questions about sales data in plain English.
  covers: Read-only access, query limits, charts
  description:
  - >-
    An app for asking questions about a sales dataset in plain English. Each question becomes one SQL query, and the app shows the SQL it wrote, the result table and a chart. Save a question to run it again later against current data.
  - >-
    The database is the safety boundary. Generated SQL runs as a database user that can only read the sales tables: it can't write, can't change the schema and can't see the app's own data. Each query stops after 5 seconds and returns at most 1,000 rows, and the app says when a result was cut off.
  features:
  - Plain-English questions turned into one SELECT
  - The generated SQL, the result table and a bar or line chart
  - Saved questions that run again on current data
  - A 5-second timeout and a 1,000-row limit
  tables:
  - [sales.orders, "Customer, order date and status"]
  - [sales.order_lines, "Product, quantity and unit price in cents"]
  - [sales.products, "Each product and its category"]
  - [sales.customers, "Each customer and their region"]
  - [app.saved_questions, "A saved question's text and SQL"]
  sql:
  - [A read-only database user, "Generated SQL runs with SELECT on the sales schema and nothing else."]
  - [Separate schemas, "Sales data and the app's own data live apart, so the query user can't reach saved questions."]
  - [Integer cents, "Money is stored as whole cents, so totals match a direct query to the cent."]
  try:
  - [Ask for revenue by region, "Ask for total revenue by region for completed orders in 2025. The totals match a direct SQL query, with a bar chart of the four regions."]
  - [Ask it to delete, "Ask it to delete all refunded orders. Nothing changes, and the app says it only runs read-only queries."]
  - [Ask for too much, "List every order line. The app shows 1,000 rows and says the result was cut off."]
- slug: catalog-search
  img: catalog-search
  window: Contoso Store
  title: Product catalog search
  tag: Full app
  blurb: Ranked keyword search, filters with counts that match the data, and keyset paging that never skips or repeats a product.
  summary: Search, filter and page through a store's catalog.
  covers: Ranking, facet counts, keyset paging
  description:
  - >-
    A product catalog for an electronics and home store. Search by keyword, narrow by category, brand, price and stock, see how many products each filter would show, sort, and page through the results. The search, filters and page are in the URL, so a shared link shows the same results.
  - >-
    Ranking, filtering, counting and paging all happen in Azure SQL. Products with every word in the name rank first. Each filter's counts reflect the search and the other filters. Pages use a keyset cursor instead of an offset, so paging through returns each product exactly once, even across equal prices. Characters like % and _ in a search are matched as text.
  features:
  - Keyword search ranked by name match, then rating
  - Filters by category, brand, price and stock, with counts
  - Sort by relevance, price or rating, 20 to a page
  - Shareable URLs for any search, filter and page
  tables:
  - [products, "Name, description, category, brand, price in cents, rating and stock"]
  sql:
  - [Keyset pagination, "An opaque cursor picks up after the last row shown, so no product is skipped or repeated."]
  - [Grouped counts, "Facet counts are computed in SQL for the current search and the other filters."]
  - [Escaped pattern matching, "Characters such as %, _ and [ are matched literally and never cause an error."]
  try:
  - [Search for wireless headphones, "Every result has both words, and results with both in the name come first."]
  - [Check the counts, "Filter to Audio and one brand. Each count matches a direct SQL count."]
  - [Page through by price, "Sort by price, low to high, and page through. Prices never go down, even across pages."]
- slug: iot-telemetry
  img: iot-telemetry
  window: Contoso Buildings
  title: IoT telemetry
  tag: Full app
  blurb: Batched ingest without duplicates, a columnstore readings table, exact rollups by time window, late readings, and alerts.
  summary: A dashboard for sensor readings from three buildings.
  covers: Ingest, columnstore, rollups, alerts
  description:
  - >-
    A dashboard for temperature and humidity sensors in three buildings. Devices send readings in batches, and the dashboard shows each site's devices, a chart for any device, metric and time window, and the current alerts.
  - >-
    Azure SQL keeps the numbers exact. Raw readings go into a table with a clustered columnstore index, and a repeated reading is counted as a duplicate rather than stored twice. Minimum, maximum, average and count for 5-minute, hourly and daily windows are computed in SQL, so they agree with the raw readings even after a late reading lands. A 5-minute window that averages above 30 degrees raises an alert.
  features:
  - Batches of up to 1,000 readings, with duplicates counted and skipped
  - Readings up to 7 days late land in the right window
  - Minimum, maximum, average and count by 5 minutes, hour or day
  - Alerts for windows that run hot
  tables:
  - [devices, "Name and site: north, south or east"]
  - [readings, "Device, metric, value, and when it was recorded and received"]
  sql:
  - [Clustered columnstore index, "Raw readings are stored by column, compressed and quick to aggregate."]
  - [A unique key on device, metric and time, "A repeated reading is recognized and stored once."]
  - [Windowed aggregates, "Rollups group readings by UTC window in SQL, so they match the raw data."]
  try:
  - [Check an hour, "A device's hourly minimum, maximum, average and count match a direct SQL query."]
  - [Send a duplicate, "Repeat a stored reading. The response counts it as a duplicate, and it's stored once."]
  - [Send a late reading, "Send a reading from two hours ago. Its 5-minute window's average and count change."]
- slug: job-queue
  img: job-queue
  window: Contoso Jobs
  title: Background job queue
  tag: Full app
  blurb: Workers claim jobs safely with READPAST, retries back off, a crashed worker's job is picked up again, and each side effect goes out once.
  summary: A job queue with a dashboard, where every job's side effect goes out once.
  covers: Locking hints, leases, retries, outbox
  description:
  - >-
    A background job queue with a dashboard. Apps enqueue jobs, three worker processes run them, and failed jobs retry with growing delays until they're marked dead. Watch the queue, enqueue test jobs and retry dead ones from the dashboard.
  - >-
    Azure SQL does the coordination. A worker claims the oldest runnable job in one statement with UPDLOCK, READPAST and ROWLOCK, so two workers never take the same job and a locked job doesn't hold up the rest. Each claim is a 30-second lease, so a crashed worker's job runs again. A job's success and its outbox row are written in one transaction, and each outbox row is published once.
  features:
  - Three workers sharing one queue without double claims
  - Retries after 2, then 4 seconds, then marked dead
  - Idempotency keys, so enqueuing twice makes one job
  - A dashboard with counts, recent jobs and retry for dead jobs
  tables:
  - [jobs, "Type, payload, status, attempts, lease and result"]
  - [outbox, "One row per succeeded job, and whether it's published"]
  - [workers, "The worker processes and when each was last seen"]
  sql:
  - [UPDLOCK, READPAST and ROWLOCK, "A worker claims a job in one statement and skips jobs other workers hold."]
  - [Transactions, "A job's success and its outbox row commit together."]
  - [A unique idempotency key, "A second enqueue with the same key finds the first job."]
  try:
  - [Seed demo jobs, "Enqueue the 20 demo jobs. Eighteen succeed, and the two that fail are tried three times, then marked dead."]
  - [Stop a worker mid-job, "After its lease ends, another worker finishes the job."]
  - [Count the outbox, "Every succeeded job has exactly one outbox row, published once."]
- slug: room-bookings
  img: room-bookings
  window: Contoso Rooms
  title: Room bookings
  tag: Full app
  blurb: Book meeting rooms in office time. Two bookings for the same room can't overlap, even when requests arrive at once.
  summary: Book meeting rooms without double bookings.
  covers: Concurrency, time zones, validation
  description:
  - >-
    A meeting-room booking app for a small office. See each room's bookings for a day, book a room for a time range and cancel a booking. Times are entered and shown in the office's time zone, and errors appear next to the field they're about.
  - >-
    Azure SQL makes sure a room is never double-booked. The overlap check and the insert happen in one transaction, so when ten people grab the same slot at once, one succeeds and the rest get a conflict that names the booking already there. Starts and ends are stored as exact instants, so daylight saving can't move a booking, and a cancelled booking frees its time.
  features:
  - A day view of every room's bookings
  - 15-minute slots, from 15 minutes to 8 hours
  - Conflict errors that name the booking already there
  - Cancellations kept in the history
  tables:
  - [rooms, "Name and capacity"]
  - [bookings, "Room, title, who booked it, start, end and status"]
  sql:
  - [Transactions, "The overlap check and the insert happen together, so concurrent requests can't both win."]
  - [UTC instants, "Starts and ends are stored as exact moments, so a booking keeps its time across daylight-saving changes."]
  - [CHECK constraints, "Status stays active or cancelled, and every booking ends after it starts."]
  try:
  - [Book an overlapping slot, "Book Aurora from 10:00 to 11:00, then from 10:30 to 11:30. The second is rejected and names the first."]
  - [Book back to back, "Book Aurora from 11:00 to 12:00, straight after. It's accepted."]
  - [Race for one slot, "Send ten identical requests at once. Exactly one booking is made."]
- slug: saas-starter
  img: saas-starter
  window: Contoso Projects
  title: SaaS starter
  tag: Full app
  blurb: Organizations, members and roles, plan limits, row-level security, and billing webhooks applied exactly once.
  summary: The start of a multi-tenant business app, with plans and billing.
  covers: Row-level security, roles, plan limits, webhooks
  description:
  - >-
    The base of a business SaaS app. Organizations have members with roles and work on projects. Each organization is on a plan, Free or Team, and the app enforces its limits on members and projects. A billing page shows the current plan and paid invoices.
  - >-
    Azure SQL keeps each organization's data to itself with row-level security keyed on SESSION_CONTEXT, so even a query that forgets to filter can't reach another organization's rows. Billing events arrive at a signed webhook: a repeated event changes nothing, and an older subscription event that arrives late doesn't undo a newer one.
  features:
  - A development sign-in you can swap for a real identity provider
  - Owner, admin and member roles, and the last owner can't leave
  - Plan limits, with messages that name the limit and the plan
  - A signed billing webhook, applied once per event
  tables:
  - [organizations, "Name and current plan"]
  - [memberships, "Who belongs to each organization, and their role"]
  - [projects, "Each organization's projects"]
  - [billing_events, "Every webhook event, by event ID"]
  - [invoices, "Paid invoices in integer cents"]
  sql:
  - [Row-level security, "A filter predicate and a block predicate keep each organization in its own rows."]
  - [SESSION_CONTEXT, "Set for each request with sp_set_session_context from the signed-in user."]
  - [A unique event ID, "A repeated webhook event is recognized and applied once."]
  try:
  - [Sign in as Cara, "Only Acme's projects and members appear. Nothing from Globex does."]
  - [Hit the Free plan limit, "As Gus, a third Globex project is rejected with the limit named. After a Team activation event, it's accepted."]
  - [Send an invoice twice, "The same signed invoice.paid event, sent twice, records one invoice."]
- slug: wiki-history
  img: wiki-history
  window: Contoso Wiki
  title: Team wiki with history
  tag: Full app
  blurb: Full version history from temporal tables. View any page as it was, compare and restore versions, and catch conflicting edits.
  summary: A team wiki where the database keeps every version.
  covers: Temporal tables, conflicts, restore
  description:
  - >-
    A team wiki for Markdown pages. See each page's full history, view it as it was at any moment, compare two versions line by line and restore an old one. Deleted pages can be brought back.
  - >-
    The history comes from Azure SQL itself. The pages table is a system-versioned temporal table, so every save, restore and delete is recorded by the database, and FOR SYSTEM_TIME AS OF shows a page as it stood at any time. Each save carries the version it started from, so when two people edit the same version, the second save is caught and its text kept instead of silently overwriting the first.
  features:
  - Markdown pages with a full history, newest first
  - Any page as of any moment, and two versions side by side
  - Restore an old version as a new one, keeping every version
  - Deleted pages you can bring back with their history
  tables:
  - [pages, "Slug, title, Markdown body, author and edit summary"]
  - [pages_history, "Every earlier version, kept by the database"]
  sql:
  - [Temporal tables, "The database records every version in a history table, not app code."]
  - [FOR SYSTEM_TIME AS OF, "Shows a page exactly as it was at any moment."]
  - [Optimistic concurrency, "A save based on an old version is rejected, so no edit is lost."]
  try:
  - [Edit three times, "Create a page and edit it three times. Its history lists four versions, newest first."]
  - [Go back in time, "View the page as of a moment between the second and third edits. The second edit's text shows."]
  - [Save the same version twice, "Open one version in two places and save both. The second save is rejected, and its text is kept."]
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
