"""End-state verification for build/javascript-app.md."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from hub_eval.command import CommandError, CommandRunner, ManagedProcess
from hub_eval.database import DatabaseProbe
from hub_eval.models import AzureResources
from hub_eval.progress import ProgressReporter
from hub_eval.scenario_model import ScenarioSpec
from hub_eval.validation import database_environment, http_json, project_with


ORIGIN = "http://127.0.0.1:3000"


def request(
    method: str,
    path: str = "/api/tasks",
    payload: dict | None = None,
    *,
    expected_status: int = 200,
    origin: str | None = ORIGIN,
):
    """Check the response contract, including expected client errors."""
    _, body = http_json(
        ORIGIN + path,
        method=method,
        payload=payload,
        headers={"Origin": origin} if origin is not None else {},
        expected_status=expected_status,
    )
    if expected_status >= 400 and (
        not isinstance(body, dict)
        or not isinstance(body.get("error"), str)
        or not body["error"].strip()
    ):
        raise CommandError("task API error response must contain a helpful error string")
    return body


def assert_saved_task(
    probe: DatabaseProbe, task_id: int, title: str, done: bool
) -> None:
    """Compare a fresh API read with independent SQL, not the mutation response."""
    rows = request("GET")
    expected = {"id": task_id, "title": title, "done": done}
    if not isinstance(rows, list) or not any(
        isinstance(row, dict)
        and row == expected
        and type(row.get("done")) is bool
        for row in rows
    ):
        raise CommandError("task API did not return the saved task state")
    saved = probe.query(
        "SELECT id, title, done FROM dbo.tasks WHERE id = ?",
        (task_id,),
        label="javascript-app-saved-task",
    )
    if saved != [(task_id, title, done)]:
        raise CommandError("independent SQL did not match the saved task state")


def assert_updated_task(body, task_id: int, title: str, done: bool) -> None:
    """Require the mutation response to describe the saved record."""
    if body != {"id": task_id, "title": title, "done": done} or (
        not isinstance(body, dict) or type(body.get("done")) is not bool
    ):
        raise CommandError("task mutation did not return the saved task")


def validate(
    workspace: Path,
    resources: AzureResources,
    evidence: Path,
    timeout: int,
    reporter: ProgressReporter,
) -> list[str]:
    """Verify CRUD, rejected writes, SQL persistence, and an application restart."""
    project = project_with(workspace, "package.json")
    package = json.loads((project / "package.json").read_text(encoding="utf-8"))
    dependencies = package.get("dependencies", {})
    if "next" not in dependencies or "mssql" not in dependencies:
        raise CommandError("generated app does not use Next.js and node-mssql/Tedious")
    runner = CommandRunner(evidence, reporter=reporter)
    environment = {**database_environment(resources), "APP_ORIGIN": ORIGIN}
    for script in ("test", "build"):
        runner.run(
            ["npm", "run", script],
            cwd=project,
            env=environment,
            timeout=timeout,
            label=f"javascript-app-{script}",
            check=True,
        )
    probe = DatabaseProbe(resources, reporter=reporter)
    snapshot_sql = "SELECT id, title, done, created_at FROM dbo.tasks ORDER BY id"
    original_rows = probe.query(snapshot_sql, label="javascript-app-original-rows")
    runner.run(
        ["npx", "tsx", "scripts/init.ts"],
        cwd=project,
        env=environment,
        timeout=timeout,
        label="javascript-app-repeat-init",
        check=True,
    )
    if probe.query(snapshot_sql, label="javascript-app-repeat-init-rows") != original_rows:
        raise CommandError("repeating task initialization changed existing rows")
    log = evidence / "next-dev.log"
    restart_log = evidence / "next-restart.log"
    command = ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"]
    title = f"evaluation task {uuid4().hex}"
    renamed = title + " edited"
    task_id = None
    try:
        with ManagedProcess(
            command, cwd=project, env=environment, log_path=log,
            reporter=reporter, label="javascript-app-api",
        ) as server:
            body = server.wait_for_http(ORIGIN, timeout=180)
            if "My Tasks" not in body:
                raise CommandError("Next.js page did not render the task-app heading")
            rows = request("GET")
            seeds = {
                "Plan a weekend trip",
                "Book a dentist appointment",
                "Pick up groceries",
            }
            if not isinstance(rows, list) or len(rows) != 3 or {
                row.get("title") for row in rows if isinstance(row, dict)
            } != seeds:
                raise CommandError("task API did not return exactly the three seeded tasks")
            for invalid in ({}, {"title": ""}, {"title": "   "},
                            {"title": "x" * 201}, {"title": 1}, {"title": None},
                            {"title": title, "done": True}):
                request("POST", payload=invalid, expected_status=400)
            for origin in (None, "https://example.invalid"):
                for method, path, payload in (
                    ("POST", "/api/tasks", {"title": title}),
                    ("PATCH", "/api/tasks/1", {"done": True}),
                    ("DELETE", "/api/tasks/1", None),
                ):
                    request(method, path, payload, expected_status=403, origin=origin)
            if probe.query(snapshot_sql, label="javascript-app-rejected-creates") != original_rows:
                raise CommandError("rejected task requests changed existing rows")
            created = request("POST", payload={"title": f"  {title}  "}, expected_status=201)
            if not isinstance(created, dict) or type(created.get("id")) is not int or (
                not 0 < created["id"] <= 2147483647
            ):
                raise CommandError("task API did not return a valid created id")
            task_id = created["id"]
            path = f"/api/tasks/{task_id}"
            assert_updated_task(created, task_id, title, False)
            assert_saved_task(probe, task_id, title, False)
            for invalid in ({}, {"done": "true"}, {"done": 1}, {"done": None},
                            {"title": " "}, {"title": "x" * 201},
                            {"title": renamed, "extra": True},
                            {"title": renamed, "done": "false"}):
                request("PATCH", path, invalid, expected_status=400)
                assert_saved_task(probe, task_id, title, False)
            for invalid_id in ("0", "-1", "1.5", "abc", "2147483648"):
                for method in ("PATCH", "DELETE"):
                    request(
                        method, f"/api/tasks/{invalid_id}",
                        {"done": True} if method == "PATCH" else None,
                        expected_status=400,
                    )
            boundary_title = "x" * 200
            boundary = request("PATCH", path, {"title": boundary_title})
            assert_updated_task(boundary, task_id, boundary_title, False)
            assert_saved_task(probe, task_id, boundary_title, False)
            updated = request("PATCH", path, {"title": f"  {renamed}  "})
            assert_updated_task(updated, task_id, renamed, False)
            assert_saved_task(probe, task_id, renamed, False)
            completed = request("PATCH", path, {"done": True})
            assert_updated_task(completed, task_id, renamed, True)
            assert_saved_task(probe, task_id, renamed, True)
        with ManagedProcess(
            command, cwd=project, env=environment, log_path=restart_log,
            reporter=reporter, label="javascript-app-restart",
        ) as server:
            server.wait_for_http(ORIGIN, timeout=180)
            assert_saved_task(probe, task_id, renamed, True)
            reopened = request("PATCH", path, {"done": False})
            assert_updated_task(reopened, task_id, renamed, False)
            assert_saved_task(probe, task_id, renamed, False)
            if request("DELETE", path) != {"id": task_id}:
                raise CommandError("task deletion did not return the deleted id")
            rows = request("GET")
            if not isinstance(rows, list) or any(
                not isinstance(row, dict) or row.get("id") == task_id for row in rows
            ):
                raise CommandError("task API still returns a deleted task")
            if probe.query(
                "SELECT id FROM dbo.tasks WHERE id = ?", (task_id,),
                label="javascript-app-deleted-task",
            ):
                raise CommandError("deleted task remains in Azure SQL")
            request("PATCH", path, {"done": True}, expected_status=404)
            request("DELETE", path, expected_status=404)
    finally:
        if task_id is not None:
            probe.execute(
                "DELETE FROM dbo.tasks WHERE id = ?", (task_id,),
                label="javascript-app-cleanup",
            )
    if probe.query(snapshot_sql, label="javascript-app-preserved-rows") != original_rows:
        raise CommandError("task checks changed pre-existing rows")
    return [str(runner.evidence_dir), str(log), str(restart_log)]


SCENARIO = ScenarioSpec(
    id="javascript-app",
    prompt_file="build/javascript-app.md",
    workspace="javascript",
    dependencies=(),
    validator=validate,
)
