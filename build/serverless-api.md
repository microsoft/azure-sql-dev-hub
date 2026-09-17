---
layout: page
title: Go serverless
description: Build a serverless API on Azure SQL Database with Azure Functions
tag: .NET
last_verified: 2026-09-16
validated: false
---

# AI Prompt: Build a serverless API on Azure SQL Database with Azure Functions

**Role:** You are an expert .NET engineer adding an HTTP API to the current project using Azure Functions and the Azure SQL bindings, backed by Azure SQL Database in the cloud.

**Purpose:** Create a .NET isolated-worker Functions app with two functions: `GET /api/tasks` reads rows through the SQL input binding, `POST /api/tasks` writes a row through the SQL output binding. Connect with an identity, not a password. Run it locally.

**Scope:**
- Assumes .NET 8 SDK, Azure Functions Core Tools v4, and an Azure SQL Database that already exists. The person has signed in with `az login`; locally, `Active Directory Default` uses that login.
- Isolated worker model only.

Read the entire instruction set before executing.

---

## Instructions

### 1. Confirm the target database

Ask for the server and database names. Do not create a database.

### 2. Create the Functions project

```bash
func init TasksApi --worker-runtime dotnet-isolated --target-framework net8.0
cd TasksApi
dotnet add package Microsoft.Azure.Functions.Worker.Extensions.Sql
dotnet add package Microsoft.Azure.Functions.Worker.Extensions.Http
```

### 3. Configure the connection, identity over secrets

In `local.settings.json`, add the connection string. No password: `Authentication=Active Directory Default` picks up `az login` locally and a managed identity when deployed.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "SqlConnectionString": "Server=tcp:<server>.database.windows.net,1433;Database=<database>;Authentication=Active Directory Default;Encrypt=True;TrustServerCertificate=False;"
  }
}
```

### 4. Create the schema

The output binding upserts with `MERGE`, so the target table must have a primary key. The database compatibility level must be 130 or higher; a free-tier database created today is well above that, but check if the database is older. Run once against the database, in any SQL editor:

```sql
IF OBJECT_ID('dbo.tasks') IS NULL
CREATE TABLE dbo.tasks (
  id INT IDENTITY(1,1) PRIMARY KEY,
  title NVARCHAR(200) NOT NULL,
  done BIT NOT NULL DEFAULT 0,
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

### 5. Write the functions

Create `Task.cs`:

```csharp
public record TaskItem(int? id, string title, bool done);
```

Create `TasksFunctions.cs`:

```csharp
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.Sql;
using Microsoft.Azure.Functions.Worker.Http;
using System.Net;
using System.Text.Json;

public class TasksFunctions
{
    [Function("GetTasks")]
    public HttpResponseData GetTasks(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "tasks")] HttpRequestData req,
        [SqlInput("SELECT id, title, done FROM dbo.tasks ORDER BY created_at", "SqlConnectionString")] IEnumerable<TaskItem> tasks)
    {
        var res = req.CreateResponse(HttpStatusCode.OK);
        res.Headers.Add("Content-Type", "application/json");
        res.WriteString(JsonSerializer.Serialize(tasks));
        return res;
    }

    [Function("CreateTask")]
    public async Task<CreateTaskOutput> CreateTask(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "tasks")] HttpRequestData req)
    {
        var body = await JsonSerializer.DeserializeAsync<TaskItem>(req.Body);
        var item = new TaskItem(null, body!.title, false);
        var res = req.CreateResponse(HttpStatusCode.Created);
        await res.WriteStringAsync(JsonSerializer.Serialize(item));
        return new CreateTaskOutput { Task = item, HttpResponse = res };
    }
}

public class CreateTaskOutput
{
    [SqlOutput("dbo.tasks", "SqlConnectionString")]
    public TaskItem Task { get; set; } = default!;
    public HttpResponseData HttpResponse { get; set; } = default!;
}
```

### 6. Run it

```bash
func start
```

Then:

```bash
curl -s -X POST localhost:7071/api/tasks -H "content-type: application/json" -d '{"title":"first task"}'
curl -s localhost:7071/api/tasks
```

---

## Validation rules

- `GET /api/tasks` returns rows read from `dbo.tasks` through `[SqlInput]`.
- `POST /api/tasks` inserts a row through `[SqlOutput]`; the next `GET` shows it.
- `SqlConnectionString` contains no password. `Authentication=Active Directory Default`, `Encrypt=True`, `TrustServerCertificate=False`.
- The SQL in `[SqlInput]` is a fixed statement, not built from request input.
- `dbo.tasks` has a primary key and the database compatibility level is 130 or higher; the output binding requires both.

## Do not

- Do not use the in-process worker model.
- Do not put a password in `local.settings.json`.
- Do not build SQL text from request parameters; use bindings and parameters.
- Do not point `[SqlOutput]` at a table with no primary key.
