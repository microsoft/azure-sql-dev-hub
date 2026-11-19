# Azure SQL Database Dev Container templates

Build and test applications in a ready-to-use development environment with the Azure SQL Database container. Each template includes an app container, the Azure SQL Database engine from `mcr.microsoft.com/mssql/azure-sql-db-server:latest`, and a SQL Database project that creates and seeds the sample `Library` database.

## Choose a template

| Template | App stack | App image variants | Guide |
|---|---|---|---|
| `dotnet` | .NET on Ubuntu 24.04 | `10.0-noble` (default), `8.0-noble` | [Get started with .NET](src/dotnet/README.md) |
| `dotnet-aspire` | .NET and Aspire on Ubuntu 24.04 | `10.0-noble` | [Get started with .NET Aspire](src/dotnet-aspire/README.md) |
| `javascript-node` | Node.js on Debian 13 | `24-trixie` (default), `22-trixie` | [Get started with Node.js](src/javascript-node/README.md) |
| `python` | Python with `mssql-python` on Debian 13 | `3.14-trixie` (default), `3.13-trixie` | [Get started with Python](src/python/README.md) |

.NET 8 reached end of support on 2026-11-10. Choose .NET 10 for a supported .NET environment.

The Azure SQL Database and app images support native AMD64 and ARM64. The container engine selects the host architecture automatically; the templates do not force a platform or require emulation.

## Container engine compatibility

These are multi-service Compose-based Dev Container templates, not single-container setups. They rely on service health dependencies, shared networking (`network_mode: service:db`), bind mounts, and port forwarding. Use an engine and Compose provider that your Dev Containers tooling can drive and that supports those features. Docker Compose with a Docker-compatible CLI is the reference configuration.

Alternative engines need configuration and are not universally supported. VS Code documents Podman 5+ as mostly Docker-CLI compatible; set `dev.containers.dockerPath` to `podman` and provide a Compose provider (`podman compose` wraps Docker Compose or Podman Compose). VS Code notes that other Docker-compliant CLIs are not officially supported. Each template also includes the [`docker-outside-of-docker` feature](https://github.com/devcontainers/features/tree/main/src/docker-outside-of-docker), which expects a Docker/Moby-compatible host socket; other engines have not been tested with that feature.

Microsoft documents WSL `wslc` for building and running individual containers, but does not document Compose or Dev Containers extension compatibility. Apple's `container` CLI documentation likewise does not establish a native Compose or Dev Containers workflow. Neither is verified for these templates as-is; third-party Compose adapters require separate configuration and verification and are not official support. See the [VS Code engine guidance](https://code.visualstudio.com/remote/advancedcontainers/docker-options), [WSL containers documentation](https://learn.microsoft.com/windows/wsl/tutorials/wsl-containers), and [Apple `container` migration guide](https://github.com/apple/container/blob/main/skills/container/references/docker-migration.md).

## Get started

You need a container engine and Compose provider compatible with your Dev Containers tooling, plus either Visual Studio Code with the Dev Containers extension or the Dev Container CLI. Review the [engine compatibility notes](#container-engine-compatibility), then clone this repository and apply a template to a new or empty workspace:

```bash
git clone https://github.com/microsoft/azure-sql-dev-hub.git
cd azure-sql-dev-hub
./devcontainers/test/apply-local.sh dotnet ./workspace
```

Open `workspace` in Visual Studio Code and choose **Reopen in Container**, or start it with the Dev Container CLI:

```bash
devcontainer up --workspace-folder ./workspace
```

Replace `dotnet` with `dotnet-aspire`, `javascript-node`, or `python` to choose another environment. To select a non-default app image variant, pass it as the third argument, for example `./devcontainers/test/apply-local.sh dotnet ./workspace 8.0-noble`. The script does not overwrite files in the destination workspace.

Each template guide covers its language setup, VS Code tasks, database connection, credentials, and troubleshooting. For container setup requirements and known limitations, see the [container get-started guide](../container/get-started.md) and [container FAQ](../container/faq.md). These templates and the Azure SQL Database container are in public preview; validate your application against the managed Azure SQL Database service before production.

## License

Copyright (c) Microsoft Corporation. Licensed under the MIT License. See [LICENSE](../LICENSE).
