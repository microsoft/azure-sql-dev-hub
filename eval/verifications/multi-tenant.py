"""End-state verification for build/multi-tenant.md."""

from __future__ import annotations

from pathlib import Path

from hub_eval.command import CommandError, CommandRunner
from hub_eval.database import DatabaseProbe
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
    """Verify the RLS policy and execute the prompt's isolation tests."""
    project = project_with(workspace, "package.json")
    runner = CommandRunner(evidence, reporter=reporter)
    result = runner.run(
        ["npx", "vitest", "run"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="multi-tenant-tests",
        check=True,
    )
    policy = DatabaseProbe(resources, reporter=reporter).query(
        """
        SELECT p.is_enabled, COUNT(sp.object_id)
        FROM sys.security_policies AS p
        JOIN sys.security_predicates AS sp
          ON sp.object_id = p.object_id
        WHERE p.name = N'TenantPolicy'
          AND SCHEMA_NAME(p.schema_id) = N'Security'
          AND sp.target_object_id = OBJECT_ID(N'dbo.tasks')
        GROUP BY p.is_enabled;
        """,
        label="multi-tenant-rls-policy",
    )
    if not policy or policy[0][0] != 1 or policy[0][1] < 2:
        raise CommandError("enabled RLS policy with filter and block predicates was not found")
    return [str(result.stdout_path), str(result.stderr_path)]


SCENARIO = ScenarioSpec(
    id="multi-tenant",
    prompt_file="build/multi-tenant.md",
    workspace="javascript",
    dependencies=("javascript-app",),
    validator=validate,
)
