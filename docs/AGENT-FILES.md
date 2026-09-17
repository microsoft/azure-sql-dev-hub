
This site is one set of content published two ways. The HTML is for people. The
surfaces below are for agents, and they are generated from the same source
files at build time, so they cannot drift from what a person sees.

## The surfaces {#surfaces}

| Surface | Where | What it is |
| --- | --- | --- |
| llms.txt | [/llms.txt](llms.txt) | Short site description and a linked index of every page's markdown source. |
| llms-full.txt | [/llms-full.txt](llms-full.txt) | Every page of the site concatenated into one document. |
| Markdown twins | append `.md` to any page URL | The markdown source of that page, published next to the HTML. |
| Alternate links | in every page head | `<link rel="alternate" type="text/markdown">` points each HTML page at its own source. |
| Structured data | home page | A schema.org WebSite object in JSON-LD. |

## Markdown twins {#markdown-twins}

Every page here is authored as a `.md` file and published twice: once rendered,
once as source. So `/index.html` has its source at `/index.md`, and
`/build/rag.html` at `/build/rag.md`. If you are an agent deciding what to
fetch: take the `.md`. It is smaller, it is the same content, and the code
blocks are fenced.

## Skills {#skills}

The [Azure SQL Database container repository]({{ site.container_repo }}) ships
17 agent skills that carry current product knowledge into Claude Code, GitHub
Copilot, Codex, and Cursor:

```bash
npx skills add microsoft/azure-sql-database-container
```

Claude Code and Codex can install them as a native plugin instead:

```text
/plugin marketplace add microsoft/azure-sql-database-container
```

Per-tool detail and the full catalog live on the
[agent skills page]({{ site.container_site }}/agent-skills.html).

## MCP {#mcp}

An Azure SQL MCP endpoint is not published yet. When it is, this page will
document it and the site will register the discovery metadata for it.

Until then, the skills above optionally use the public
[Microsoft Learn MCP](https://learn.microsoft.com/api/mcp) as a live
documentation layer. The skills work without it.

## What this site expects of you

Nothing special. Every page is static, every URL is stable, and nothing
requires JavaScript to read. If something an agent needs is missing or wrong,
[open an issue]({{ site.repo }}/issues/new).
