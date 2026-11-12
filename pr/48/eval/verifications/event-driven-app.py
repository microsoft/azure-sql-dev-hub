"""End-state verification for build/event-driven-app.md."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from uuid import uuid4

from hub_eval.command import CommandError, CommandRunner, ManagedProcess
from hub_eval.database import DatabaseProbe
from hub_eval.models import AzureResources
from hub_eval.progress import ProgressReporter
from hub_eval.scenario_model import ScenarioSpec
from hub_eval.validation import (
    database_environment,
    functions_environment,
    http_json,
    project_with,
)


def validate(
    workspace: Path,
    resources: AzureResources,
    evidence: Path,
    timeout: int,
    reporter: ProgressReporter,
) -> list[str]:
    """Verify Change Tracking and exactly one trigger event for one insert."""
    project = project_with(workspace, "TasksApi.csproj")
    if shutil.which("func") is None:
        raise CommandError("Azure Functions Core Tools v4 is not installed")
    runner = CommandRunner(evidence, reporter=reporter)
    runner.run(
        ["dotnet", "build"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="event-driven-app-build",
        check=True,
    )
    log = evidence / "func-trigger.log"
    marker = f"trigger evaluation task {uuid4().hex}"
    with ManagedProcess(
        ["azurite", "--silent", "--location", str(evidence / "azurite")],
        cwd=project,
        env=functions_environment(resources),
        log_path=evidence / "azurite.log",
        reporter=reporter,
        label="event-driven-app-azurite",
    ) as storage:
        storage.wait_for_tcp("127.0.0.1", 10000)
        with ManagedProcess(
            ["func", "start", "--port", "7071"],
            cwd=project,
            env=functions_environment(resources),
            log_path=log,
            reporter=reporter,
            label="event-driven-app",
        ) as server:
            server.wait_for_http("http://127.0.0.1:7071/api/tasks", timeout=180)
            status, _ = http_json(
                "http://127.0.0.1:7071/api/tasks",
                method="POST",
                payload={"title": marker},
            )
            if status != 201:
                raise CommandError("Functions API did not return 201")
            _, rows = http_json("http://127.0.0.1:7071/api/tasks")
            inserted = [
                row
                for row in rows
                if isinstance(row, dict)
                and row.get("title") == marker
                and row.get("id") is not None
            ]
            if len(inserted) != 1:
                raise CommandError(
                    "Functions SQL input did not return exactly one inserted task"
                )
            expected_log = f"Insert task {inserted[0]['id']}"

            def matching_events() -> list[str]:
                return [
                    line
                    for line in log.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    if line.rstrip().endswith(expected_log)
                ]

            deadline = time.monotonic() + min(timeout, 300)
            while time.monotonic() < deadline:
                if matching_events():
                    break
                time.sleep(5)
            else:
                raise CommandError(
                    "SQL trigger did not log the inserted task within five minutes"
                )
            time.sleep(10)
            events = matching_events()
            if len(events) != 1:
                raise CommandError(
                    f"expected exactly one trigger event, observed {len(events)}"
                )
            if marker in log.read_text(encoding="utf-8", errors="replace"):
                raise CommandError("SQL trigger logged task row content")
    tracking_enabled = DatabaseProbe(resources, reporter=reporter).scalar(
        """
        SELECT COUNT(*)
        FROM sys.change_tracking_tables
        WHERE object_id = OBJECT_ID(N'dbo.tasks');
        """,
        label="event-driven-change-tracking",
    )
    if tracking_enabled != 1:
        raise CommandError("Change Tracking is not enabled on dbo.tasks")
    return [str(runner.evidence_dir), str(log)]


SCENARIO = ScenarioSpec(
    id="event-driven-app",
    prompt_file="build/event-driven-app.md",
    workspace="functions",
    dependencies=("serverless-api",),
    validator=validate,
)
