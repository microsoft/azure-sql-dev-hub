## A connection-string change, not a code change

The local container runs the Azure SQL Database engine, so the schema, T-SQL,
and driver behavior you developed against carry forward. What changes is the
target in configuration: the server becomes your logical server's address, and
authentication moves from a local SQL login to Microsoft Entra, which is what
`Authentication=Active Directory Default` in the starter selects for drivers
that support it.

Create the cloud database first if you have not: the Cloud tab on the
[home page](../index.md) has the CLI command with the free tier applied, and
[Start a database](start-database.html) covers the portal path. Then swap the
value of `SQL_CONNECTION_STRING`, run your test suite against the cloud target,
and compare. The container repository's
[local-to-cloud build prompt](https://github.com/microsoft/azure-sql-database-container/blob/main/docs/prompts/local-to-cloud.md)
walks an agent through exactly this sequence.
