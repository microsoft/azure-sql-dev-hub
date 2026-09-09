---
layout: scenario
title: Multi-tenant setup
description: >-
  Apply tenant isolation in the database so the application does not rely only
  on query discipline.
intro: >-
  Apply tenant isolation in the database so the application does not rely only
  on query discipline.
prompt: >-
  Add Row-Level Security to this multi-tenant Azure SQL schema. Use session
  context for the active tenant and verify that one tenant cannot read another
  tenant's rows.
starter:
  language: sql
  code: |-
    CREATE SCHEMA Security;
    GO

    CREATE FUNCTION Security.fn_tenantAccessPredicate(@TenantId int)
        RETURNS TABLE
        WITH SCHEMABINDING
    AS
        RETURN SELECT 1 AS fn_accessResult
        WHERE CAST(SESSION_CONTEXT(N'TenantId') AS int) = @TenantId;
    GO

    CREATE SECURITY POLICY Security.TenantPolicy
    ADD FILTER PREDICATE Security.fn_tenantAccessPredicate(TenantId)
    ON dbo.AppData
    WITH (STATE = ON);
skill:
  name: ""
  note: >-
    No skill in the collection is dedicated to Row-Level Security yet. The
    catalog covers authentication, schema, and migrations around it.
  install: ""
docs:
  label: Row-Level Security
  href: https://learn.microsoft.com/sql/relational-databases/security/row-level-security
---

## How the pattern works

The isolation logic lives in the database tier. An inline table-valued function
is the predicate: it returns a row only when the `TenantId` on the data matches
the tenant the application placed in `SESSION_CONTEXT` after opening its
connection. The security policy binds that predicate to the table as a filter,
so every `SELECT`, `UPDATE`, and `DELETE` is filtered no matter which query path
reached the table.

Two things complete the pattern in a real application, both covered with worked
examples in the [Row-Level Security documentation](https://learn.microsoft.com/sql/relational-databases/security/row-level-security):
the app sets the tenant with `sp_set_session_context` (pass `@read_only = 1` so
the value cannot change on a pooled connection), and a block predicate stops
inserts that carry another tenant's id. The scenario prompt asks your agent to
verify the isolation, not just create it: a test that reads as tenant A after
writing as tenant B is the proof that matters.
