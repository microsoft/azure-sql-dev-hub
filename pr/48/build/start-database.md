## Local path

The starter above verifies a running container. Getting there is three commands,
covered end to end in the [getting started guide](https://microsoft.github.io/azure-sql-database-container/getting-started.html):
sign in to the preview registry, start the container on port 1433, then run the
verification query. The registry credentials come from
[signing up for the Preview](https://aka.ms/sqldbcontainerpreview-signup).
The container bundles sqlcmd, so nothing needs installing on your machine, and
the `-C` flag trusts the container's self-signed certificate.

The engine does not create application databases on its own. Create one, named
`appdb` in these examples or whatever you choose, before pointing an app at it.
The container skill handles this for you when an agent drives the setup.

## Cloud path

Prefer a managed database from the start? The Azure SQL Database free tier
gives each database 100,000 vCore seconds of serverless compute, 32 GB of data,
and 32 GB of backup storage per month, for up to 10 databases per subscription.
You need an Azure account and subscription.

1. Open the [Azure SQL hub in the portal](https://aka.ms/azuresqlhub).
2. In the **Create a database** pane, select **Start free**.
3. Confirm the **Free tier** applied, fill in the Basics tab, then
   select **Review + create**.

The [free tier documentation](https://learn.microsoft.com/azure/azure-sql/database/free-tier)
has the current limits and what happens when a database reaches its monthly cap.
The same creation is scriptable with the Azure CLI; the Cloud tab on the
[home page](../index.md) carries the command.
