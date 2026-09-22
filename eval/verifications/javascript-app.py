"""End-state verification for build/javascript-app.md."""

from __future__ import annotations

import json
from pathlib import Path

from hub_eval.command import CommandError, CommandRunner, ManagedProcess
from hub_eval.models import AzureResources
from hub_eval.progress import ProgressReporter
from hub_eval.scenario_model import ScenarioSpec
from hub_eval.validation import database_environment, project_with


def validate(
    workspace: Path,
    resources: AzureResources,
    evidence: Path,
    timeout: int,
    reporter: ProgressReporter,
) -> list[str]:
    """Build and serve the Next.js app, then verify seeded rows render."""
    project = project_with(workspace, "package.json")
    package = json.loads((project / "package.json").read_text(encoding="utf-8"))
    dependencies = package.get("dependencies", {})
    if "next" not in dependencies or "mssql" not in dependencies:
        raise CommandError("generated app does not use Next.js and node-mssql/Tedious")
    runner = CommandRunner(evidence, reporter=reporter)
    runner.run(
        ["npm", "run", "build"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="javascript-app-build",
        check=True,
    )
    log = evidence / "next-dev.log"
    with ManagedProcess(
        ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"],
        cwd=project,
        env=database_environment(resources),
        log_path=log,
        reporter=reporter,
        label="javascript-app-api",
    ) as server:
        body = server.wait_for_http("http://127.0.0.1:3000", timeout=180)
    if "Tasks" not in body or "Connect the app" not in body:
        raise CommandError("Next.js page did not render the expected seeded task list")
    return [str(runner.evidence_dir), str(log)]


SCENARIO = ScenarioSpec(
    id="javascript-app",
    prompt_file="build/javascript-app.md",
    workspace="javascript",
    dependencies=(),
    validator=validate,
)
