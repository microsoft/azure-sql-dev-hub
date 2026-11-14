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

The container is designed to reduce differences between local development and Azure SQL Database, but it is not a replacement for validation in Azure. Before production deployment, test your application against the Azure SQL Database. You can most definitely leverage the [Free Tier offering]({{ site.azure_free_tier }}).

## Feature availability {#feature-availability}

### What features available in Azure SQL Database are not available in the container?

The following capabilities are not included in the current container experience. If your application depends on one of these capabilities, validate that part of the application directly against Azure SQL Database.

| Capability not available | What this means for development |
| --- | --- |
| Auditing | Test auditing configuration and audit-output workflows in Azure SQL Database. |
| Backup and restore | The Azure SQL Database backup/restore service and backup/restore engine are not included. Use supported development workflows rather than production backup and restore operations. |
| Change Data Capture | Change Data Capture is not included. |
| Change Event Streaming | Change Event Streaming is not included. |
| Change Tracking | Change Tracking is not included. |
| Global Query | Global Query is not included. |
| Always Encrypted | Always Encrypted is not included. |
| Cell-level encryption | Cell-level encryption is not included. |
| SQL Ledger | SQL Ledger is not included. |
| Transparent Data Encryption and Azure Key Vault integration | These service-managed encryption capabilities are not included in the local container. |

### Are any features temporarily unavailable in the initial Public Preview? {#arm64}

Yes, the below is only available on X64. ARM support on the below will follow soon.

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

### Can I use Microsoft Entra authentication?

Microsoft Entra authentication is included. During Public Preview, some setup may require [command-line configuration]({{ '/container/get-started.html#entra' | relative_url }}). Tooling experiences in SQL Server Management Studio and Visual Studio Code may evolve during the preview.

### Does the container behave exactly like the managed Azure service?

No. Azure SQL Database includes cloud services and operational capabilities that do not apply to a local development container. Examples include service-managed backup and restore, auditing infrastructure, Azure Key Vault integration, and other production operations.

### How should I report an issue? {#report-an-issue}

When reporting an issue, include the container image version, host operating system and architecture, startup command, client tool and version, relevant logs, and a minimal reproduction. Do not include passwords, connection secrets, or customer data.

## Related {#related}

- [Get started with the container]({{ '/container/get-started.html' | relative_url }}): prerequisites, setup, and troubleshooting.
- [Azure SQL Database free tier]({{ site.azure_free_tier }}): validate in Azure before you deploy.
