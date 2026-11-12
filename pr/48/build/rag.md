## Why one database

Embeddings live in a native `vector` column next to the rows they describe, so
the retrieval path is a SQL query, not a second system to provision, sync, and
secure. `VECTOR_DISTANCE` computes cosine distance for an exact top-k search,
which the [vector documentation](https://learn.microsoft.com/sql/sql-server/ai/vectors)
recommends up to roughly 50,000 candidate vectors; approximate search with
DiskANN vector indexes is in preview beyond that.

The same table works on the local container and in Azure SQL Database, so you
can prototype the whole RAG loop offline and ship it by changing the connection
target. The [Prototype a RAG workflow prompt](../prompts.html#rag) hands the
whole job to your agent.
