---
layout: page
title: Create a Python API
description: Build a Python API on Azure SQL Database
tag: Python
last_verified: 2026-09-16
validated: false
---

# AI Prompt: Build a Python API on Azure SQL Database

**Role:** You are an expert backend engineer adding an HTTP API to the current project, backed by Azure SQL Database in the cloud.

**Purpose:** Build a FastAPI service for a task list with list, create, and complete endpoints, connected to an existing Azure SQL Database with a Microsoft Entra token. No passwords.

**Scope:**
- Assumes Python 3.10 or newer (`mssql-python` has no distribution for 3.9) and an Azure SQL Database that already exists. The person running this has signed in with `az login`.
- Uses `mssql-python`, the current Microsoft driver, not `pyodbc`. The connection URL dialect name is not needed here; there is no ORM.
- If the project already has code, add this as a new module and preserve what exists.

Read the entire instruction set before executing.

---

## Instructions

### 1. Confirm the target database

Ask for the server and database names if they are not in `.env`. Do not create a database.

### 2. Install dependencies

```bash
pip install fastapi uvicorn mssql-python azure-identity python-dotenv
```

### 3. Configure the connection with a token

Create `.env`:

```dotenv
SQL_SERVER=<server>.database.windows.net
SQL_DATABASE=<database>
```

Create `db.py`. The token comes from `azure-identity`; the driver receives it as an access token attribute rather than a password.

```python
import os, struct
import mssql_python
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
SQL_COPT_SS_ACCESS_TOKEN = 1256

def _token_struct() -> bytes:
    token = DefaultAzureCredential().get_token("https://database.windows.net/.default").token
    raw = token.encode("utf-16-le")
    return struct.pack("<I", len(raw)) + raw

def connect():
    conn_str = (
        f"Server=tcp:{os.environ['SQL_SERVER']},1433;"
        f"Database={os.environ['SQL_DATABASE']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return mssql_python.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: _token_struct()})
```

### 4. Create the schema

Create `init.py` and run it once with `python init.py`:

```python
from db import connect

conn = connect(); cur = conn.cursor()
cur.execute("""
IF OBJECT_ID('dbo.tasks') IS NULL
CREATE TABLE dbo.tasks (
  id INT IDENTITY(1,1) PRIMARY KEY,
  title NVARCHAR(200) NOT NULL,
  done BIT NOT NULL DEFAULT 0,
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
""")
conn.commit(); cur.close(); conn.close()
print("schema ready")
```

### 5. Build the API

Create `main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import connect

app = FastAPI(title="Tasks on Azure SQL")

class NewTask(BaseModel):
    title: str

@app.get("/tasks")
def list_tasks():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM dbo.tasks ORDER BY created_at")
    rows = [{"id": r[0], "title": r[1], "done": bool(r[2])} for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows

@app.post("/tasks", status_code=201)
def create_task(t: NewTask):
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO dbo.tasks (title) OUTPUT INSERTED.id VALUES (?)", t.title)
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "title": t.title, "done": False}

@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    conn = connect(); cur = conn.cursor()
    cur.execute("UPDATE dbo.tasks SET done = 1 WHERE id = ?", task_id)
    updated = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if updated == 0:
        raise HTTPException(404, "task not found")
    return {"id": task_id, "done": True}
```

Run it:

```bash
uvicorn main:app --reload
```

Then:

```bash
curl -s -X POST localhost:8000/tasks -H "content-type: application/json" -d '{"title":"first task"}'
curl -s localhost:8000/tasks
```

---

## Validation rules

- `GET /tasks` returns 200 and a JSON array read from `dbo.tasks` on Azure SQL Database.
- `POST /tasks` returns 201 with the new id; a second `GET` shows the row.
- Every query is parameterized with `?`. No string formatting into SQL.
- No password anywhere. The connection uses an Entra access token from `DefaultAzureCredential`.
- `Encrypt=yes` and `TrustServerCertificate=no`.

## Do not

- Do not use `pyodbc` unless `mssql-python` fails to install; if you must, say so and why.
- Do not interpolate user input into SQL.
- Do not create the database.
