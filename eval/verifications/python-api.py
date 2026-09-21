"""End-state verification for build/python-api.md."""

from __future__ import annotations

from pathlib import Path

from hub_eval.command import CommandError, CommandRunner, ManagedProcess
from hub_eval.models import AzureResources
from hub_eval.progress import ProgressReporter
from hub_eval.scenario_model import ScenarioSpec
from hub_eval.validation import (
    database_environment,
    http_json,
    project_python,
    project_with,
)


def validate(
    workspace: Path,
    resources: AzureResources,
    evidence: Path,
    timeout: int,
    reporter: ProgressReporter,
) -> list[str]:
    """Initialize the schema and verify FastAPI create/list/complete behavior."""
    project = project_with(workspace, "main.py")
    if "mssql_python" not in (project / "db.py").read_text(encoding="utf-8"):
        raise CommandError("generated API does not use mssql-python")
    python = project_python(project)
    runner = CommandRunner(evidence, reporter=reporter)
    runner.run(
        [python, "init.py"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="python-api-schema",
        check=True,
    )
    log = evidence / "uvicorn.log"
    with ManagedProcess(
        [python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=project,
        env=database_environment(resources),
        log_path=log,
        reporter=reporter,
        label="python-api",
    ) as server:
        server.wait_for_http("http://127.0.0.1:8000/tasks", timeout=120)
        status, created = http_json(
            "http://127.0.0.1:8000/tasks",
            method="POST",
            payload={"title": "prompt evaluation task"},
        )
        if status != 201 or not created.get("id"):
            raise CommandError("Python API did not create a task")
        _, rows = http_json("http://127.0.0.1:8000/tasks")
        if not any(row.get("id") == created["id"] for row in rows):
            raise CommandError("Python API list did not return the created task")
        complete_status, completed = http_json(
            f"http://127.0.0.1:8000/tasks/{created['id']}/complete",
            method="POST",
        )
        if complete_status != 200 or completed.get("done") is not True:
            raise CommandError("Python API did not complete the created task")
    return [str(runner.evidence_dir), str(log)]


SCENARIO = ScenarioSpec(
    id="python-api",
    prompt_file="build/python-api.md",
    workspace="python",
    dependencies=(),
    validator=validate,
)
