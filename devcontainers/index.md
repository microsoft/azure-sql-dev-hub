---
title: Azure SQL Dev Container templates
head_title: Azure SQL Database Dev Container templates
description: Runnable .NET, Aspire, Node.js, and Python development environments with the Azure SQL Database container and a seeded sample database.
permalink: /devcontainers/
doc: true
---

Build and test applications in a ready-to-use development environment with the Azure SQL Database container. Each template includes an app container, the Azure SQL Database engine, and a SQL Database project that creates and seeds the sample `Library` database. Unlike the [app-building prompts]({{ '/' | relative_url }}#build), these templates provide runnable environments.
{: .doc-lead}

The database image is `mcr.microsoft.com/mssql/azure-sql-db-server:latest`. Both the database and app images support native `linux/amd64` and `linux/arm64`.

These are multi-service Compose-based Dev Container templates, not single-container setups. Use an engine and Compose provider that your Dev Containers tooling can drive and that supports service health dependencies, shared networking, bind mounts, and port forwarding. The templates also include a feature that uses a Docker/Moby-compatible host socket. See the [container engine compatibility notes]({{ site.repo }}/blob/main/devcontainers/README.md#container-engine-compatibility) for Podman, WSL `wslc`, and Apple `container` caveats.

These templates and the Azure SQL Database container are in public preview. Review the [container FAQ]({{ '/container/faq.html' | relative_url }}) and validate your application against the managed Azure SQL Database service before production.

## Choose a template

| Template | App stack | App image variants | Guide |
|---|---|---|---|
| `dotnet` | .NET on Ubuntu 24.04 | `10.0-noble` (default), `8.0-noble` | [Get started with .NET]({{ site.repo }}/blob/main/devcontainers/src/dotnet/README.md) |
| `dotnet-aspire` | .NET and Aspire on Ubuntu 24.04 | `10.0-noble` | [Get started with .NET Aspire]({{ site.repo }}/blob/main/devcontainers/src/dotnet-aspire/README.md) |
| `javascript-node` | Node.js on Debian 13 | `24-trixie` (default), `22-trixie` | [Get started with Node.js]({{ site.repo }}/blob/main/devcontainers/src/javascript-node/README.md) |
| `python` | Python with `mssql-python` on Debian 13 | `3.14-trixie` (default), `3.13-trixie` | [Get started with Python]({{ site.repo }}/blob/main/devcontainers/src/python/README.md) |

.NET 8 reached end of support on 2026-11-10. Choose .NET 10 for a supported .NET environment.

## Get started

Install a container engine and Compose provider compatible with your Dev Containers tooling, plus either Visual Studio Code with the Dev Containers extension or the Dev Container CLI. Review the [engine compatibility notes]({{ site.repo }}/blob/main/devcontainers/README.md#container-engine-compatibility), then clone the [Azure SQL Developer Hub repository]({{ site.repo }}) and apply a template to a new or empty workspace:

```bash
git clone https://github.com/microsoft/azure-sql-dev-hub.git
cd azure-sql-dev-hub
./devcontainers/test/apply-local.sh python ./workspace
```

Open `workspace` in Visual Studio Code and choose **Reopen in Container**, or start it with the Dev Container CLI:

```bash
devcontainer up --workspace-folder ./workspace
```

Replace `python` with `dotnet`, `dotnet-aspire`, or `javascript-node` to choose another environment. To select a non-default app image variant, pass it as the third argument, for example `./devcontainers/test/apply-local.sh dotnet ./workspace 8.0-noble`. The script does not overwrite files in the destination workspace.

## Included in each environment

The `Library` database is built from the SQL Database project and published when the dev container is created. VS Code tasks verify the schema and sample data, rebuild the project, and publish schema changes. The template guides describe the language setup, connection examples, tools, credentials, restricted-network options, and troubleshooting.

Also see the [Azure SQL Database container setup guide]({{ '/container/get-started.html' | relative_url }}) and [container FAQ]({{ '/container/faq.html' | relative_url }}).
