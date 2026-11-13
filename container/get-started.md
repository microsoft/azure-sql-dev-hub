---
title: Get started
head_title: Get started with the Azure SQL Database container
eyebrow: Azure SQL Database container
eyebrow_href: /#containers
pill: Public preview
description: Run the Azure SQL Database container locally with Docker, Podman, or WSL containers, connect and create a database, and fix the common first-run problems.
doc: true
permalink: /container/get-started.html
---

Run the Azure SQL Database container on your machine for development, testing, and CI. Three commands take you from pull to your first query, with Docker, Podman, or WSL containers. The image is public on Microsoft Container Registry, so there is nothing to sign up for.
{: .doc-lead}

The container is a development target, not a production database. For what it includes and leaves out, see the [FAQ]({{ '/container/faq.html' | relative_url }}).

- [Prerequisites](#prerequisites)
- [Set up the container](#set-up)
- [Build something on it](#build)
- [Set up with your coding agent](#agent)
- [Microsoft Entra authentication](#entra)
- [Troubleshooting](#troubleshooting)
- [Report an issue](#report-an-issue)
{: .doc-toc}

## Prerequisites {#prerequisites}

### Host platforms

The image provides `linux/amd64` and `linux/arm64` variants. Container runtimes select the matching architecture automatically.

| Host OS | Architecture | Status |
| --- | --- | --- |
| macOS 14 or later | x86_64, ARM64 | Supported |
| Linux (Ubuntu, Debian, Fedora) | x86_64, ARM64 | Supported |
| Windows 11 | x86_64, ARM64 | Supported (WSL2) |

On ARM64, full-text search, PolyBase, and extensibility runtimes are not available yet. See [feature availability]({{ '/container/faq.html#arm64' | relative_url }}).

### Container runtimes

The container is OCI-compliant and runs on any modern runtime. Tested runtimes:

- Docker 24 or later
- Podman 5.0 or later
- Rancher Desktop 1.13 or later
- containerd, through nerdctl or Kubernetes
- [WSL containers](https://learn.microsoft.com/windows/wsl/tutorials/wsl-containers) (`wslc`, included with WSL on Windows)

Pick the runtime that already works on your machine. The container image and the connection behavior are the same across runtimes.

### System resources

Give the container runtime at least:

- CPU: 2 cores
- Memory: 4 GB available to the runtime VM. The engine does not start with less than 2 GB.
- Disk: 10 GB free for the image and a small database, more for larger datasets

With less than this, the container may fail to start or may run slowly.

### Network

- You need an internet connection the first time you pull the image. After the pull, the container runs offline.
- The container listens on port 1433. Make sure the port is free, or [map a different host port](#port-in-use).

### Tools

You do not need sqlcmd or any database tool installed: the container bundles sqlcmd. To connect from your app, use a driver or ORM for your stack, such as mssql for Node.js, mssql-python, pyodbc, EF Core, Prisma, SQLAlchemy, or JDBC.

The container does not need an Azure subscription. To deploy to Azure SQL Database afterwards, you need one, and the [free tier]({{ site.azure_free_tier }}) works.

## Set up the container {#set-up}

The commands use `docker`. With Podman, replace `docker` with `podman`. On Windows with WSL containers, replace `docker` with `wslc`. Steps 2 to 4 are shown for bash and zsh, with the PowerShell form after each.

### 1. Pull the image {#pull}

```bash
docker pull mcr.microsoft.com/mssql/azure-sql-db-server:latest
```

### 2. Start the container {#start}

Generate a strong SA password, then start the engine on port 1433, bound to localhost:

```bash
MSSQL_SA_PASSWORD="Aa1$(openssl rand -hex 16)"
docker run --name sqldb -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
  -p 127.0.0.1:1433:1433 -d \
  mcr.microsoft.com/mssql/azure-sql-db-server:latest
```

In PowerShell:

```powershell
$env:MSSQL_SA_PASSWORD = "Aa1" + [guid]::NewGuid().ToString("N")
docker run --name sqldb -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=$env:MSSQL_SA_PASSWORD" -p 127.0.0.1:1433:1433 -d mcr.microsoft.com/mssql/azure-sql-db-server:latest
```

Confirm it is up with `docker ps --filter "name=sqldb"`. You should see `sqldb` with an Up status. If it exited, run `docker logs sqldb`; the most common cause is a password that does not meet the complexity policy. Keep `MSSQL_SA_PASSWORD` in your environment, not in source control.

Your databases live inside the container, so `docker rm` deletes them. To keep them, add `-v sqldb-data:/var/opt/mssql` to the `docker run` command, or use the compose file below, which does.

Prefer docker compose? Export the password with `export MSSQL_SA_PASSWORD`, save this as `docker-compose.yml`, and run `docker compose up -d`:

```yaml
services:
  sqldb:
    image: mcr.microsoft.com/mssql/azure-sql-db-server:latest
    container_name: sqldb
    ports:
      - "127.0.0.1:1433:1433"
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "${MSSQL_SA_PASSWORD:?Set MSSQL_SA_PASSWORD}"
    volumes:
      - sqldb-data:/var/opt/mssql

volumes:
  sqldb-data:
```

### 3. Connect and run your first query {#connect}

The container bundles sqlcmd, so nothing needs installing on your machine. The `-C` flag trusts the container's self-signed certificate.

```bash
docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT @@VERSION;"
```

In PowerShell, the same command on one line with `$env:MSSQL_SA_PASSWORD`:

```powershell
docker exec sqldb /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$env:MSSQL_SA_PASSWORD" -C -Q "SELECT @@VERSION;"
```

A result that names Microsoft SQL Azure confirms the Azure SQL Database engine.

### 4. Create your database {#create-database}

The engine does not create application databases on its own. Create one on a master connection, named `appdb` here or whatever you choose:

```bash
docker exec sqldb /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -b \
  -Q "IF DB_ID('appdb') IS NULL CREATE DATABASE appdb;"
```

In PowerShell, use the same command on one line with `$env:MSSQL_SA_PASSWORD` in place of `$MSSQL_SA_PASSWORD`.

Then connect to it by name. Select the database in the connection string, `Database=appdb` or `-d appdb` for sqlcmd, rather than switching with `USE`.

### Build something on it {#build}

The app prompts in [Build with a prompt]({{ '/' | relative_url }}#build) run against this container. Paste one into your coding agent and tell it the server is `localhost,1433`, the database is `appdb`, and the SQL login is in `MSSQL_SA_PASSWORD`. When you are ready for Azure, [Move from the container to the cloud]({{ '/build/local-to-cloud.html' | relative_url }}) switches the same app to a free Azure SQL database.

### Other ways to connect {#other-clients}

- **sqlcmd on your machine.** `sqlcmd -S localhost,1433 -U sa -P "$MSSQL_SA_PASSWORD" -C -d appdb`
- **VS Code with the MSSQL extension.** Server `localhost,1433`, SQL Login, user `sa`, your password, and Trust server certificate. Tooling experiences in SQL Server Management Studio and Visual Studio Code may evolve during the preview.
- **Your app.** `Server=localhost,1433;Database=appdb;User Id=sa;TrustServerCertificate=true`, with the password read from your environment. When you move to Azure SQL Database, the connection string changes to your Azure server and Microsoft Entra sign-in.

### Stop and clean up {#clean-up}

```bash
docker rm -f sqldb
# or, with docker compose (add -v to also remove the data volume):
docker compose down
```

## Set up with your coding agent {#agent}

The container skills are part of the microsoft-sql plugin. They cover pulling the image, waiting for the engine to be ready, and creating the database, with you reviewing each step. Install the plugin with the command for your agent in [Skills]({{ '/' | relative_url }}#skills), then paste this into your agent:

```text
Add a local Azure SQL Database to this project, then scaffold the schema, migrations and data-access layer for my stack.
```

## Microsoft Entra authentication {#entra}

Microsoft Entra authentication is included. During the public preview, you set it up from the command line with environment variables and a mounted certificate. SQL authentication with `sa`, as above, stays the simple default; use Microsoft Entra when you want closer parity with Azure SQL Database.

For the app registration and the certificate, follow [Configure Microsoft Entra ID authentication for SQL Server on containers](https://learn.microsoft.com/sql/linux/security/authentication/container-kubernetes-microsoft-entra-deployment). Mount a `.pfx` with an empty export password, then pass `MSSQL_AAD_CLIENT_ID`, `MSSQL_AAD_PRIMARY_TENANT`, and `MSSQL_AAD_CERTIFICATE_FILE_PATH`:

```bash
docker run -d --name sqldb \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=${MSSQL_SA_PASSWORD:?Set MSSQL_SA_PASSWORD}" \
  -e "MSSQL_AAD_CLIENT_ID=<client-id>" \
  -e "MSSQL_AAD_PRIMARY_TENANT=<tenant-id>" \
  -e "MSSQL_AAD_CERTIFICATE_FILE_PATH=/var/opt/mssql/mssql-entra-id.pfx" \
  -v /path/to/mssql-entra-id.pfx:/var/opt/mssql/mssql-entra-id.pfx:ro \
  -p 127.0.0.1:1433:1433 \
  mcr.microsoft.com/mssql/azure-sql-db-server:latest
```

To create a Microsoft Entra server admin at startup, add `MSSQL_AAD_SERVER_ADMIN_NAME`, `MSSQL_AAD_SERVER_ADMIN_TYPE` (0 for a user, 1 for a group), and `MSSQL_AAD_SERVER_ADMIN_SID` (the user or group object ID).

## Troubleshooting {#troubleshooting}

The commands below use `docker`. With another runtime, use its own CLI (`podman`, `nerdctl`, or `wslc`); the behavior is the same.

### Let your coding agent diagnose it {#agent-diagnose}

Paste this into your agent. It can check your machine and read the container logs itself:

```text
My local Azure SQL Database container is not working. Diagnose it. Check my container runtime is installed, running, and set to Linux containers; check it has enough memory (the engine needs at least 2 GB); check port 1433 is free; check the image architecture matches this host (linux/amd64 or linux/arm64); then read the container logs and tell me the actual cause and the fix.
```

### Check your container runtime first {#runtime}

Most first-run failures come from the runtime, not the database. Check all four:

- **It is installed and up to date.** Setup guides: [Docker](https://docs.docker.com/desktop/), [Podman](https://podman.io/docs/installation), [Rancher Desktop](https://docs.rancherdesktop.io/getting-started/installation/), [containerd](https://github.com/containerd/nerdctl), [WSL containers](https://learn.microsoft.com/windows/wsl/tutorials/wsl-containers).
- **It is running.** `docker info` (or `podman info`, or `wslc version`) returns without an error. A fresh install does not always start the engine for you.
- **It runs Linux containers.** On Windows, a runtime set to Windows containers cannot run this image. Switch it to Linux containers. This is the most common failure on Windows.
- **It has enough memory.** The engine needs at least 2 GB to start. Give the runtime 4 GB and 2 CPUs: in Docker Desktop and Rancher Desktop under Settings, Resources; for Podman with `podman machine set --memory`. Too little memory shows up as a container that starts and then stops with no obvious error.

### The container will not start, or will not accept connections {#wont-start}

Read the logs first. They name the cause in almost every case:

```bash
docker logs sqldb
```

- **The container exits.** Check for a missing `ACCEPT_EULA=Y`. The container does not start without it.
- **The container is Up, but connections fail** with a login timeout or "server is not found". The engine inside the container did not start. The usual causes are an SA password that does not meet the policy (8 or more characters, with at least three of upper case, lower case, digits, and symbols) or too little memory.

Fix the cause, remove the container with `docker rm -f sqldb`, and run it again. Changing an environment variable does not affect a container that already exists.

### "no matching manifest" or "exec format error" {#architecture}

The image provides `linux/amd64` and `linux/arm64` variants, and current runtimes select the matching one. Update your runtime, then pull the image again. Do not force `--platform linux/amd64` on an ARM64 host unless you need the x64 image under emulation.

### Port 1433 is already in use {#port-in-use}

Something else is bound to the port, often an existing SQL Server. Map a different host port and connect to `localhost,1434` instead:

```bash
docker run --name sqldb -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
  -p 127.0.0.1:1434:1433 -d \
  mcr.microsoft.com/mssql/azure-sql-db-server:latest
```

### Connection fails right after the container starts {#not-ready}

The engine is not ready the instant `docker run` returns. It takes a few seconds. Retry the connection rather than treating the first failure as final. In a script, run `sqlcmd -C -b -l 2` in a retry loop.

### "Cannot open database" {#no-database}

The engine does not create databases on its own, as in Azure SQL Database. [Create yours](#create-database) on a master connection first.

### USE appdb fails with Msg 40508 {#use-40508}

This is expected, and it matches Azure SQL Database. Select the database in the connection string (`Database=appdb`, or `-d appdb` for sqlcmd) instead of switching with `USE`.

### It is not the Azure SQL Database engine {#wrong-engine}

If `SELECT SERVERPROPERTY('EngineEdition');` does not return 5, you are running the SQL Server image (`mcr.microsoft.com/mssql/server`) rather than this one. Recreate the container with the image from [step 1](#pull).

## Report an issue {#report-an-issue}

[Report a bug](https://aka.ms/azuresqldb-container-bug). When reporting an issue, include the container image version, host operating system and architecture, startup command, client tool and version, relevant logs, and a minimal reproduction. Do not include passwords, connection secrets, or customer data.

## Related {#related}

- [Container FAQ]({{ '/container/faq.html' | relative_url }}): what the container is for, and which features it includes and leaves out.
- [Build with a prompt]({{ '/' | relative_url }}#build): app prompts that run on the container.
- [Azure SQL Database free tier]({{ site.azure_free_tier }}): validate in Azure before you deploy.
