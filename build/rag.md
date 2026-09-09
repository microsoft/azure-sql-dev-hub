---
layout: scenario
title: Wire up RAG
description: >-
  Use Azure SQL for relational data and embeddings so the retrieval path stays
  inside one database.
intro: >-
  Use Azure SQL for relational data and embeddings so the retrieval path stays
  inside one database.
prompt: >-
  Add a RAG workflow to this app using Azure SQL. Create a document table with
  a vector column, load embeddings, and verify cosine similarity search.
starter:
  language: sql
  code: |-
    CREATE TABLE dbo.Documents (
      id int PRIMARY KEY,
      content nvarchar(max),
      embedding vector(1536)
    );

    SELECT TOP (10) *
    FROM dbo.Documents
    ORDER BY VECTOR_DISTANCE('cosine', @query_vector, embedding);
skill:
  name: azuresql-db-rag
  note: >-
    The RAG skill knows the vector type, the similarity functions, and how to
    load embeddings alongside the data they describe.
  install: npx skills add microsoft/azure-sql-database-container --skill azuresql-db-rag
docs:
  label: Vector search in the SQL engine
  href: https://learn.microsoft.com/sql/sql-server/ai/vectors
---

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
