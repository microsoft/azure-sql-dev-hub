---
layout: page
title: Make it multi-tenant
description: Make a JavaScript app multi-tenant on Azure SQL Database with row-level security
tag: JavaScript
last_verified: 2026-09-16
validated: false
---

# AI Prompt: Make a JavaScript app multi-tenant on Azure SQL Database with row-level security

**Role:** You are an expert engineer adding tenant isolation to the current project's Azure SQL Database, enforced in the database with row-level security rather than in application code, with a test that proves it.

**Purpose:** Add a `tenant_id` column to `dbo.tasks`, create a filter predicate and security policy keyed on `SESSION_CONTEXT`, set the tenant from the app on every connection, and write a test that shows tenant A cannot read tenant B's rows even when it asks for them.

**Scope:**
- Assumes the scaffold scenario's project exists (Next.js, `mssql` driver, `src/lib/db.ts` with one pool). If not, create it first.
- Isolation is enforced by the engine. Application code sets the tenant; it does not filter rows.
- The security policy filters reads and blocks writes for the wrong tenant.

Read the entire instruction set before executing.

---

## Instructions

Identify the project's package manager (`npm`, `yarn`, `pnpm`, `bun`) and use it for all commands. Examples below use `npm`.

### 1. Add the tenant column and backfill

```sql
ALTER TABLE dbo.tasks ADD tenant_id INT NULL;
UPDATE dbo.tasks SET tenant_id = 1 WHERE tenant_id IS NULL;
ALTER TABLE dbo.tasks ALTER COLUMN tenant_id INT NOT NULL;
CREATE INDEX IX_tasks_tenant ON dbo.tasks (tenant_id);
INSERT INTO dbo.tasks (title, tenant_id) VALUES (N'Tenant two task', 2);
```

### 2. Create the predicate and the policy

```sql
CREATE SCHEMA Security;
GO
CREATE FUNCTION Security.fn_tenantPredicate(@tenant_id INT)
RETURNS TABLE
WITH SCHEMABINDING
AS RETURN SELECT 1 AS allowed
  WHERE @tenant_id = CAST(SESSION_CONTEXT(N'tenant_id') AS INT);
GO
CREATE SECURITY POLICY Security.TenantPolicy
  ADD FILTER PREDICATE Security.fn_tenantPredicate(tenant_id) ON dbo.tasks,
  ADD BLOCK  PREDICATE Security.fn_tenantPredicate(tenant_id) ON dbo.tasks AFTER INSERT
WITH (STATE = ON);
GO
```

A connection with no `tenant_id` in session context now sees zero rows. That is intended.

### 3. Set the tenant on every connection

In `src/lib/db.ts`, add a helper that sets session context before any query. `sp_set_session_context` with `@read_only = 1` prevents the value being changed later in the same session.

```ts
export async function requestFor(tenantId: number) {
  const pool = await getPool();
  const req = pool.request();
  await req.input("tenant", sql.Int, tenantId)
           .query("EXEC sp_set_session_context @key = N'tenant_id', @value = @tenant, @read_only = 1");
  return pool.request();
}
```

Note: session context is per connection. With a pool, set it at the start of each unit of work on the connection you are about to use. If a pooled connection is reused, `@read_only = 1` will reject a second set; handle that by resetting the connection or by not using `@read_only` and setting the value on every request. Choose one and say which.

Update `src/app/page.tsx` to read the tenant from a query string for the demo (`?tenant=1`) and use `requestFor(tenantId)` for the `SELECT`.

### 4. Write the isolation test

Create `tests/rls.test.ts` (use the project's test runner; Vitest shown):

```ts
import { describe, it, expect } from "vitest";
import { requestFor } from "../src/lib/db";

describe("row-level security", () => {
  it("tenant 1 cannot see tenant 2 rows even when asking for them", async () => {
    const req = await requestFor(1);
    const r = await req.query("SELECT COUNT(*) AS n FROM dbo.tasks WHERE tenant_id = 2");
    expect(r.recordset[0].n).toBe(0);
  });
  it("tenant 2 sees its own row", async () => {
    const req = await requestFor(2);
    const r = await req.query("SELECT COUNT(*) AS n FROM dbo.tasks WHERE tenant_id = 2");
    expect(r.recordset[0].n).toBe(1);
  });
});
```

Run:

```bash
npx vitest run
```

Both tests pass.

---

## Validation rules

- `Security.TenantPolicy` exists with `STATE = ON` and both a filter and a block predicate on `dbo.tasks`.
- The first test passes: a query that explicitly asks for another tenant's rows returns zero. That is the isolation proof.
- Tenant is set with `sp_set_session_context`, not by adding `WHERE tenant_id = ?` to application queries.
- No password in config; the connection is unchanged from the scaffold scenario.

## Do not

- Do not implement tenancy as a `WHERE` clause in application code. The policy must hold even if application code forgets.
- Do not set the tenant from user-editable input in real code; the query string here is for the demo only.
- Do not disable the policy to make a test pass.
