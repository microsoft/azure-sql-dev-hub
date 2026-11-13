---
title: Frequently asked questions
head_title: Azure SQL Database container FAQ
eyebrow: Azure SQL Database container
eyebrow_href: /#containers
pill: Public preview
description: What the Azure SQL Database container is for, which Azure SQL Database features it includes and leaves out, and how to move from the container to Azure SQL Database.
doc: true
permalink: /container/faq.html
---

Azure SQL Database container brings an Azure SQL Database-compatible development experience to your local environment. Use it to build, test, and validate applications locally before deploying to Azure SQL Database.
{: .doc-lead}

## About the container {#about}

### What is Azure SQL Database container?

Azure SQL Database container is a local development target for applications that will use Azure SQL Database. It helps developers start quickly, work offline, and test against Azure SQL Database behavior without provisioning a cloud database for every development or continuous integration environment. No Azure subscription or credit card needed.

### Is it intended for production workloads?

No. The container is intended for local development, automated testing, and continuous integration scenarios. Deploy production applications to Azure SQL Database.

### How is it different from the SQL Server container?

The SQL Server container runs SQL Server. Azure SQL Database container is designed to reflect Azure SQL Database behavior and limitations more closely, which can help identify compatibility issues earlier in the development cycle.

### Will an application that works with the container work unchanged in Azure SQL Database?

The container is designed to reduce differences between local development and Azure SQL Database, but it is not a replacement for validation in Azure. Before you deploy to production, test your application against Azure SQL Database. The [free tier]({{ site.azure_free_tier }}) is enough for that.

## Feature availability {#feature-availability}

### What features available in Azure SQL Database are not available in the container?

These are not in the container. If your application depends on one, validate that part against Azure SQL Database.

- Auditing
- Backup and restore. The managed backup service is not included; keep data between runs with a volume.
- Change Data Capture
- Change Event Streaming
- Change Tracking. The Azure Functions SQL trigger depends on it.
- Global Query
- Always Encrypted
- Cell-level encryption
- SQL Ledger
- Transparent Data Encryption and Azure Key Vault integration

### Are any features temporarily unavailable in the initial Public Preview? {#arm64}

Yes. These are available on x64 only for now, and ARM64 support will follow.

- Full-text search
- PolyBase
- Extensibility runtimes

### Which commonly used database capabilities are included?

The container includes core capabilities used to build and test many Azure SQL Database applications, including:

- Query processing, rowstore, columnstore, and transactions
- In-memory storage
- Query Store and Extended Events
- XML and JSON
- Microsoft Entra authentication
- Data classification, dynamic data masking, permissions, and row-level security
- Built-in CLR types, such as spatial and hierarchy types
- AI functions

## Development and deployment {#development}

### Can I use the container for automated and continuous integration tests?

Yes. A primary scenario is running integration tests locally or in a continuous integration pipeline without creating and sharing a cloud database for every test run. Make sure the pipeline environment can run the supported container image and architecture.

### Can I move my schema and application from the container to Azure SQL Database?

Yes. The intended workflow is to build and test locally, then deploy the database project or schema and connect the application to Azure SQL Database. [Features listed as unavailable](#feature-availability) must be tested separately in Azure.

### Can I run this site's build prompts on the container?

The app prompts, yes: each one tells your agent how to connect to the container or to a cloud database. The building blocks marked Cloud only need Azure SQL Database. See [Build with a prompt]({{ '/' | relative_url }}#build).

### Can I use Microsoft Entra authentication?

Microsoft Entra authentication is included. During Public Preview, some setup may require [command-line configuration]({{ '/container/get-started.html#entra' | relative_url }}). Tooling experiences in SQL Server Management Studio and Visual Studio Code may evolve during the preview.

### Does the container behave exactly like the managed Azure service?

No. Azure SQL Database includes cloud services and operational capabilities that do not apply to a local development container. Examples include service-managed backup and restore, auditing infrastructure, Azure Key Vault integration, and other production operations.

### How should I report an issue? {#report-an-issue}

[Report a bug](https://aka.ms/azuresqldb-container-bug). Include the container image version, host operating system and architecture, startup command, client tool and version, relevant logs, and a minimal reproduction. Do not include passwords, connection secrets, or customer data.

## Related {#related}

- [Get started with the container]({{ '/container/get-started.html' | relative_url }}): prerequisites, setup, and troubleshooting.
- [Azure SQL Database free tier]({{ site.azure_free_tier }}): validate in Azure before you deploy.
