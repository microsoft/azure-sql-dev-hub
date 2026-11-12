"""End-state verification for build/rag-app.md."""

from __future__ import annotations

from pathlib import Path

from hub_eval.command import CommandError, CommandRunner
from hub_eval.database import DatabaseProbe
from hub_eval.models import AzureResources
from hub_eval.progress import ProgressReporter
from hub_eval.scenario_model import ScenarioSpec
from hub_eval.validation import database_environment, project_python, project_with


def validate(
    workspace: Path,
    resources: AzureResources,
    evidence: Path,
    timeout: int,
    reporter: ProgressReporter,
) -> list[str]:
    """Run RAG and independently verify native VECTOR storage and ranking."""
    project = project_with(workspace, "rag.py")
    python = project_python(project)
    runner = CommandRunner(evidence, reporter=reporter)
    result = runner.run(
        [python, "rag.py"],
        cwd=project,
        env=database_environment(resources),
        timeout=timeout,
        label="rag-app",
        check=True,
    )
    output = result.stdout_path.read_text(encoding="utf-8")
    ranked = [
        line
        for line in output.splitlines()
        if line.strip() and line.strip()[0].isdigit() and "  " in line
    ]
    if "Query:" not in output or len(ranked) < 3:
        raise CommandError("RAG script did not print a query and three ranked rows", result)
    probe = DatabaseProbe(resources, reporter=reporter)
    column = probe.query(
        """
        SELECT TYPE_NAME(user_type_id), vector_dimensions
        FROM sys.columns
        WHERE object_id = OBJECT_ID(N'dbo.documents')
          AND name = N'embedding';
        """,
        label="rag-vector-column",
    )
    if not column or str(column[0][0]).lower() != "vector":
        raise CommandError("dbo.documents.embedding is not a VECTOR column")
    dimension = int(column[0][1])
    ranked_rows = probe.query(
        f"""
        DECLARE @query VECTOR({dimension}) =
            (SELECT TOP (1) embedding FROM dbo.documents ORDER BY id);
        SELECT TOP (3)
            content,
            VECTOR_DISTANCE('cosine', embedding, @query) AS distance
        FROM dbo.documents
        ORDER BY distance;
        """,
        label="rag-vector-distance",
    )
    if len(ranked_rows) != 3:
        raise CommandError("independent VECTOR_DISTANCE query did not return three rows")
    return [str(result.stdout_path), str(result.stderr_path)]


SCENARIO = ScenarioSpec(
    id="rag-app",
    prompt_file="build/rag-app.md",
    workspace="rag",
    dependencies=(),
    validator=validate,
    requires_embedding=True,
)
