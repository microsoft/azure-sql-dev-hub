---
layout: home
title: Azure SQL Developer Hub
description: The front door for building applications on Azure SQL Database with an AI coding agent. Start free in the cloud, hand your agent a build prompt, verify a working app.
hero:
  headline: Azure SQL, built for
  headline_accent: AI workloads.
  subline: Start free in the cloud, or straight from your AI coding agent. The engine your production already runs on, now with the setup an agent can finish for you.
  agents:
  - Claude Code
  - GitHub Copilot
  - Codex
  - Cursor
video:
  id: biJywQPbqn0
  title: Build on Azure SQL with your AI agent
  sub: One prompt. The agent does the setup. The query runs.
  placeholder: PLACEHOLDER  replace with the demo cover image
  chapters:
  - stamp: 0:05
    seconds: 5
    label: One prompt
  - stamp: 0:18
    seconds: 18
    label: Agent does the setup
  - stamp: 0:34
    seconds: 34
    label: Query runs
  note: Chapter times are placeholders until the final edit lands.
quickstart_heading: Get a database running.
quickstart_text: Pick your path. The same engine everywhere, so what you build here ships unchanged.
quickstart:
- key: cloud
  name: Cloud, free tier
  title: Create a free Azure SQL database.
  desc: Create it in the Azure portal with the free offer, then verify from any SQL editor. Prerequisites and offer limits are in the setup guide.
  code: SELECT 1 AS connected;
  copy_event: copy_verify
  detail_title: Three steps, then you are live.
  checks:
  - - Create the database
    - You need an Azure subscription with permission to create resources. Follow the free-offer guide and pick the free offer when prompted.
  - - Open access
    - Add your IP to the firewall and sign in with Microsoft Entra.
  - - Verify
    - Run SELECT 1. A result of 1 means your connection works and you are ready for a build prompt.
  link:
    label: 'Free offer: setup guide, prerequisites, and limits'
    href: https://learn.microsoft.com/azure/azure-sql/database/free-offer
    event: docs_free_offer
- key: local
  name: Local container
  pill: Preview
  title: Run the Azure SQL Database engine on your laptop.
  desc: Same engine as the cloud, in a container, offline. Preview today. Sign up and we send registry access.
  button:
    label: Sign up for the Preview
    href: https://aka.ms/sqldbcontainerpreview-signup
    event: container_signup
  detail_title: What you get once you are in.
  checks:
  - - One docker run
    - Sign in to the preview registry, pull the image, start the engine.
  - - Agent skills included
    - Your agent already knows how to provision, connect, migrate, seed, and ship it.
  - - Ship to Azure unchanged
    - Only the connection string changes.
  link:
    label: Container quickstart
    href: https://microsoft.github.io/azure-sql-database-container/getting-started.html
    event: docs_container
- key: agent
  name: Let your agent do it
  title: Install the skills, then ask in plain English.
  desc: One command teaches Claude Code, Copilot, Codex, or Cursor how Azure SQL actually works.
  code: npx skills add microsoft/azure-sql-skills
  copy_event: copy_skills_start
  detail_title: Then say what you want.
  checks:
  - - Create a free database first
    - Provisioning is still your step today. The agent takes it from there.
  - - Prompt your agent
    - '"Connect to my Azure SQL database and scaffold the schema, migrations, and data layer for my stack."'
  - - Verify
    - The agent runs the first query and shows you the result.
  link:
    label: What the skills teach, per agent
    href: https://aka.ms/azuresql-skills
    event: docs_skills
then:
  from: Local or free tier
  to: Azure SQL Database
  note: Same code, connection string changes, app goes live.
build_heading: What will you build?
build_text: Each prompt targets Azure SQL Database in the cloud and ends in a working app. Copy the full prompt, hand it to your agent, check the result against the validation rules at the end.
scenarios:
- num: '01'
  slug: javascript-app
  title: Scaffold a JavaScript app
  tag: JavaScript
  blurb: A Next.js task app on the mssql driver, Entra sign-in, one pool, three seeded rows on screen.
  art:
    bg: '#eaf3fc'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><rect x="10" y="12" width="100" height="66" rx="8" fill="#fff" stroke="#0067b8" stroke-width="2"/><rect x="10" y="12" width="100" height="14" rx="8" fill="#0067b8"/><rect x="22" y="36" width="50" height="6" rx="3" fill="#c7dcf0"/><rect x="22" y="48" width="70" height="6" rx="3" fill="#c7dcf0"/><rect x="22" y="60" width="40" height="6" rx="3" fill="#0067b8"/></svg>
- num: '02'
  slug: python-api
  title: Create a Python API
  tag: Python
  blurb: A FastAPI service for a task list, connected with an Entra token. No password.
  art:
    bg: '#eaf6ec'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><rect x="14" y="20" width="92" height="50" rx="8" fill="#fff" stroke="#107c10" stroke-width="2"/><path d="M30 45h20M60 45h30M30 57h40" stroke="#107c10" stroke-width="4" stroke-linecap="round"/><circle cx="34" cy="33" r="3" fill="#107c10"/><circle cx="44" cy="33" r="3" fill="#a9d8ab"/><circle cx="54" cy="33" r="3" fill="#a9d8ab"/></svg>
- num: '03'
  slug: rag-app
  title: Wire up RAG
  tag: Python / AI
  blurb: Source text and embeddings in one table, native VECTOR column, ranked similarity search.
  art:
    bg: '#f2ecfa'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><circle cx="40" cy="45" r="16" fill="#fff" stroke="#7719aa" stroke-width="2"/><circle cx="80" cy="30" r="9" fill="#fff" stroke="#7719aa" stroke-width="2"/><circle cx="84" cy="62" r="9" fill="#fff" stroke="#7719aa" stroke-width="2"/><path d="M54 40l17-7M55 51l20 8" stroke="#7719aa" stroke-width="2"/><circle cx="40" cy="45" r="5" fill="#7719aa"/></svg>
- num: '04'
  slug: serverless-api
  title: Go serverless
  tag: .NET
  blurb: An HTTP API in Azure Functions using the SQL input and output bindings. Managed identity, no password in config.
  art:
    bg: '#fdf1e7'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><path d="M52 12l-18 40h16l-8 26 30-42H56z" fill="#fff" stroke="#c05612" stroke-width="2" stroke-linejoin="round"/><rect x="14" y="66" width="30" height="10" rx="5" fill="#f5d8c2"/><rect x="78" y="14" width="28" height="10" rx="5" fill="#f5d8c2"/></svg>
- num: '05'
  slug: event-driven-app
  title: React to row changes
  tag: .NET
  blurb: A SQL trigger in Azure Functions that fires when rows change. Change Tracking on, no polling.
  art:
    bg: '#fdeef1'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><rect x="14" y="30" width="40" height="30" rx="6" fill="#fff" stroke="#b0244a" stroke-width="2"/><rect x="66" y="30" width="40" height="30" rx="6" fill="#fff" stroke="#b0244a" stroke-width="2"/><path d="M54 45h12" stroke="#b0244a" stroke-width="3"/><path d="M62 40l6 5-6 5" fill="none" stroke="#b0244a" stroke-width="3"/><circle cx="34" cy="45" r="5" fill="#b0244a"/><path d="M80 40v10M86 40v10M92 40v10" stroke="#f3c3ce" stroke-width="3"/></svg>
- num: '06'
  slug: multi-tenant
  title: Make it multi-tenant
  tag: JavaScript
  blurb: Row-level security enforced by the engine, set from the app per connection, with a test that proves the isolation holds.
  art:
    bg: '#e8f4f4'
    svg: <svg viewBox="0 0 120 90" aria-hidden="true"><path d="M60 12l30 10v22c0 16-13 28-30 34-17-6-30-18-30-34V22z" fill="#fff" stroke="#0e7c7c" stroke-width="2"/><path d="M46 46l9 9 19-19" fill="none" stroke="#0e7c7c" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>
workloads_heading: Built for AI workloads.
workloads_text: The pieces an AI app needs, inside the engine. No extension to install, no second database to run.
workloads:
- title: Vector search
  text: A native VECTOR type and VECTOR_DISTANCE. Store embeddings next to the rows they describe.
  icon: <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
  link:
    label: Vector docs
    href: https://learn.microsoft.com/sql/relational-databases/vectors/vectors-sql-server
    event: docs_vector
- title: Embeddings in T-SQL
  text: Generate and chunk from inside the database with external model calls. No separate pipeline.
  icon: <svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="8"/></svg>
  link:
    label: AI_GENERATE_EMBEDDINGS
    href: https://learn.microsoft.com/sql/t-sql/functions/ai-generate-embeddings-transact-sql
    event: docs_embeddings
- title: RAG, end to end
  text: Chunk, embed, store, retrieve, ground. One skill walks your agent through all five.
  icon: <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 10h8M8 14h5"/></svg>
  link:
    label: Copy the RAG prompt
    href: '#rag-app'
    event: tile_rag_prompt
- title: Safe for agents to write
  text: Row-level security, Entra identity, and injection-safe patterns the skills enforce by default.
  icon: <svg viewBox="0 0 24 24"><path d="M12 3l8 4v6c0 4-3.5 7-8 8-4.5-1-8-4-8-8V7z"/></svg>
  link:
    label: Row-level security docs
    href: https://learn.microsoft.com/sql/relational-databases/security/row-level-security
    event: docs_rls
skills:
  heading: Teach your agent Azure SQL.
  text: Pick your agent. One install. The skills load themselves when the work matches.
  agents:
  - key: claude
    name: Claude Code
    blurb: native plugin
    logo: <svg aria-hidden="true" fill="#ffffff" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34
      1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>
    code: 'claude plugin marketplace add microsoft/azure-sql-skills

      claude plugin install azure-sql-skills@azure-sql-skills'
    note: 'Two commands: register the marketplace, then install the plugin with every skill. Or the portable form: <code>gh skill install microsoft/azure-sql-skills --all --agent claude-code</code>.'
  - key: copilot
    name: GitHub Copilot
    blurb: VS Code, CLI, app
    logo: <svg aria-hidden="true" fill="#ffffff" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M23.922 16.997C23.061 18.492 18.063 22.02 12 22.02 5.937 22.02.939 18.492.078 16.997A.641.641 0 0 1 0 16.741v-2.869a.883.883 0 0 1 .053-.22c.372-.935 1.347-2.292 2.605-2.656.167-.429.414-1.055.644-1.517a10.098 10.098 0 0 1-.052-1.086c0-1.331.282-2.499 1.132-3.368.397-.406.89-.717 1.474-.952C7.255 2.937 9.248 1.98 11.978 1.98c2.731 0 4.767.957 6.166 2.093.584.235 1.077.546 1.474.952.85.869 1.132 2.037 1.132 3.368 0 .368-.014.733-.052 1.086.23.462.477 1.088.644 1.517 1.258.364 2.233 1.721 2.605 2.656a.841.841 0 0 1 .053.22v2.869a.641.641 0 0 1-.078.256Zm-11.75-5.992h-.344a4.359 4.359 0 0 1-.355.508c-.77.947-1.918 1.492-3.508 1.492-1.725 0-2.989-.359-3.782-1.259a2.137 2.137 0 0 1-.085-.104L4 11.746v6.585c1.435.779 4.514 2.179 8 2.179 3.486 0 6.565-1.4 8-2.179v-6.585l-.098-.104s-.033.045-.085.104c-.793.9-2.057 1.259-3.782 1.259-1.59 0-2.738-.545-3.508-1.492a4.359 4.359
      0 0 1-.355-.508Zm2.328 3.25c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm-5 0c.549 0 1 .451 1 1v2c0 .549-.451 1-1 1-.549 0-1-.451-1-1v-2c0-.549.451-1 1-1Zm3.313-6.185c.136 1.057.403 1.913.878 2.497.442.544 1.134.938 2.344.938 1.573 0 2.292-.337 2.657-.751.384-.435.558-1.15.558-2.361 0-1.14-.243-1.847-.705-2.319-.477-.488-1.319-.862-2.824-1.025-1.487-.161-2.192.138-2.533.529-.269.307-.437.808-.438 1.578v.021c0 .265.021.562.063.893Zm-1.626 0c.042-.331.063-.628.063-.894v-.02c-.001-.77-.169-1.271-.438-1.578-.341-.391-1.046-.69-2.533-.529-1.505.163-2.347.537-2.824 1.025-.462.472-.705 1.179-.705 2.319 0 1.211.175 1.926.558 2.361.365.414 1.084.751 2.657.751 1.21 0 1.902-.394 2.344-.938.475-.584.742-1.44.878-2.497Z"/></svg>
    code: npx skills add microsoft/azure-sql-skills
    note: Or <code>gh skill install microsoft/azure-sql-skills --all --agent github-copilot</code>. Find them in Copilot Chat under Configure Chat, Skills tab, or type <code>/skills</code>. Committed to <code>.github/skills/</code> in your repo, they also reach the Copilot coding agent with no install.
  - key: codex
    name: Codex
    blurb: Agent Plugins client
    logo: <svg aria-hidden="true" role="img" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.3" xmlns="http://www.w3.org/2000/svg">    <g>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(60 12 12)"/>    <ellipse cx="12" cy="12" rx="3.4" ry="8.4" transform="rotate(120 12 12)"/>  </g>  <circle cx="12" cy="12" r="1.5" fill="#ffffff" stroke="none"/></svg>
    code: npx skills add microsoft/azure-sql-skills
    note: The repository is an Agent Plugins package, so Codex installs it directly. Confirm with <code>ls .codex/skills</code>.
  - key: cursor
    name: Cursor
    blurb: AI-native editor
    logo: <svg aria-hidden="true" fill="#ffffff" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M11.503.131 1.891 5.678a.84.84 0 0 0-.42.726v11.188c0 .3.162.575.42.724l9.609 5.55a1 1 0 0 0 .998 0l9.61-5.55a.84.84 0 0 0 .42-.724V6.404a.84.84 0 0 0-.42-.726L12.497.131a1.01 1.01 0 0 0-.996 0M2.657 6.338h18.55c.263 0 .43.287.297.515L12.23 22.918c-.062.107-.229.064-.229-.06V12.335a.59.59 0 0 0-.295-.51l-9.11-5.257c-.109-.063-.064-.23.061-.23"/></svg>
    code: npx skills add microsoft/azure-sql-skills
    note: Or <code>gh skill install microsoft/azure-sql-skills --all --agent cursor</code>. Confirm with <code>ls .cursor/skills</code>.
  chips:
  - Connect my Node app to Azure SQL Database without a password
  - Scaffold the schema, migrations, and data layer for this app
  - Add vector search to this table and make it use the index
  - Why does my first query after idle fail with 40613
  note: Full catalog, every skill's source, and the feedback form at aka.ms/azuresql-skills. Skills teach your agent the engine; they do not grant access to the Preview container.
videos_heading: See it in action.
videos_text: Longer walkthroughs from the Microsoft SQL team. Scroll for more.
videos:
- id: pq2drN2Qw5w
  title: 'Boost your SQL development in VS Code: Copilot, containers, and more'
  text: Carlos Robles, VS Code Live, Aug 2025
  tag: VS Code Live
  href: https://www.youtube.com/watch?v=pq2drN2Qw5w
  image: https://img.youtube.com/vi/pq2drN2Qw5w/hqdefault.jpg
- id: wZUPFCCByfw
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
existing:
  heading: Already have Azure SQL data?
  text: Point the prompts above at an existing development database. Review permissions and schema changes before you let an agent run them.
  link: Start with the RAG example
continuity:
  heading: Prefer local development?
  text: The Azure SQL Database container runs the same engine offline. Sign up for the Preview.
faqs:
- question: What do I need to get started?
  answer: An Azure account and a development database. The free offer covers everything on this page, within its limits. If you want to work offline, sign up for the container Preview.
- question: Is it safe to let an agent write to my database?
  answer: Use a development database with least-privilege access. The skills default to parameterised queries, Entra identity over passwords, and row-level security for multi-tenant work. Review schema changes before they run against anything real.
- question: Do I need the container?
  answer: No. Every prompt here targets Azure SQL Database in the cloud. The container is the local option, in Preview today.
- question: What does this cost?
  answer: The free offer covers the database for every example here, within its limits; see the offer details for what those are. The RAG example needs an embedding service, priced by whoever provides it; the prompt asks which one you have before using it.
- question: How is this different from SQL Server?
  answer: Same engine family, managed for you, with features that ship to Azure SQL Database first. The container runs the Azure SQL Database engine, not the SQL Server image.
close:
  heading: Ready? Teach your agent, then ask.
  code: npx skills add microsoft/azure-sql-skills
---
