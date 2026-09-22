"""End-state verification for build/serverless-api.md."""

from __future__ import annotations

import shutil
from pathlib import Path

from hub_eval.command import CommandError, CommandRunner, ManagedProcess
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
    """Run the Function and verify rows are returned through SQL bindings."""
    project = project_with(workspace, "TasksApi.csproj")
    sources = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in project.glob("*.cs")
    )
    if "[SqlInput(" not in sources or "[SqlOutput(" not in sources:
        raise CommandError("generated Functions API does not use SQL input/output bindings")
    runner = CommandRunner(evidence, reporter=reporter)
    runner.run(
        ["dotnet", "build"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="serverless-api-build",
        check=True,
    )
    if shutil.which("func") is None:
        raise CommandError("Azure Functions Core Tools v4 is not installed")
    log = evidence / "func-api.log"
    with ManagedProcess(
        ["azurite", "--silent", "--location", str(evidence / "azurite")],
        cwd=project,
        env=functions_environment(resources),
        log_path=evidence / "azurite.log",
        reporter=reporter,
        label="serverless-api-azurite",
    ) as storage:
        storage.wait_for_tcp("127.0.0.1", 10000)
        with ManagedProcess(
            ["func", "start", "--port", "7071"],
            cwd=project,
            env=functions_environment(resources),
            log_path=log,
            reporter=reporter,
            label="serverless-api",
        ) as server:
            server.wait_for_http("http://127.0.0.1:7071/api/tasks", timeout=180)
            status, _ = http_json(
                "http://127.0.0.1:7071/api/tasks",
                method="POST",
                payload={"title": "functions prompt evaluation"},
            )
            if status != 201:
                raise CommandError("Functions API did not return 201")
            _, rows = http_json("http://127.0.0.1:7071/api/tasks")
            if not any(row.get("title") == "functions prompt evaluation" for row in rows):
                raise CommandError("Functions SQL input did not return the inserted task")
    return [str(runner.evidence_dir), str(log)]


SCENARIO = ScenarioSpec(
    id="serverless-api",
    prompt_file="build/serverless-api.md",
    workspace="functions",
    dependencies=(),
    validator=validate,
)
