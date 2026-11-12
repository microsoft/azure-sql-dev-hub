## The one rule that matters

Read the connection string from configuration, never from code. The starter
shows the Node.js `mssql` driver doing exactly that: `SQL_CONNECTION_STRING`
comes from the environment, and the tagged-template query is parameterized by
construction. Every supported language has the same shape with its own driver;
the [connect and query guide](https://learn.microsoft.com/azure/azure-sql/database/connect-query-content-reference-guide)
lists them per language and tool.

Locally the container listens on `localhost,1433` with SQL authentication. In
Azure the same application authenticates with Microsoft Entra. Because the app
only ever reads one configuration value, that difference stays in `.env`, which
is the whole local-to-cloud story: see
[Ship local to cloud](local-to-cloud.html) when you are ready to move.
