"""Matrix orchestration, prompt construction, evidence, and cleanup."""

from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .agents import AgentRequest, create_agent
from .azure import AzureEnvironment
from .command import CommandError
from .models import AzureResources, RunSettings, ScenarioResult
from .progress import ProgressReporter
from .scenarios import DEFAULT_SCENARIO_ORDER, SCENARIOS

HANDLED_ERRORS = (CommandError, OSError, ValueError, KeyError)


def expand_scenarios(requested: tuple[str, ...]) -> tuple[str, ...]:
    """Include dependencies and retain the canonical execution order."""
    selected: set[str] = set()

    def include(name: str) -> None:
        if name not in SCENARIOS:
            raise ValueError(f"unknown scenario {name!r}")
        for dependency in SCENARIOS[name].dependencies:
            include(dependency)
        selected.add(name)

    for name in requested:
        include(name)
    return tuple(name for name in DEFAULT_SCENARIO_ORDER if name in selected)


def build_prompt(
    prompt_text: str,
    *,
    scenario: str,
    resources: AzureResources,
    workspace: Path,
) -> str:
    """Combine the published prompt with complete unattended test inputs."""
    embedding = ""
    if scenario == "rag-app":
        if resources.embedding_endpoint:
            embedding = (
                "\nEmbedding inputs already selected for this evaluation:\n"
                "- Provider: Azure OpenAI\n"
                f"- Endpoint: {resources.embedding_endpoint}\n"
                f"- Deployment/model: {resources.embedding_deployment}\n"
                f"- Output dimension: {resources.embedding_dimension}\n"
                "- Authentication: Microsoft Entra via DefaultAzureCredential; do not request or use a key.\n"
            )
        else:
            embedding = (
                "\nNo hosted embedding service can be provisioned by the authenticated "
                "identity. Use the prompt's deterministic evaluation fallback with "
                "EMBED_PROVIDER=fixture and EMBED_DIM=8. Do not request another input and "
                "do not describe fixture vectors as production embeddings.\n"
            )
    return f"""# Unattended evaluation context

Execute the prompt below in the current workspace. This is an unattended end-to-end
evaluation, not a request for an explanation.

- Do not ask the user questions. All required values are supplied here.
- Work only inside {workspace}.
- Azure CLI is already authenticated to subscription {resources.subscription_id}.
- Use the existing database. Do not create, rename, or delete Azure resources.
- Azure resource group: {resources.resource_group}
- Azure SQL server: {resources.server_fqdn}
- Azure SQL database: {resources.database_name}
- The signed-in Azure CLI identity is the Microsoft Entra database administrator.
- Prefer a project-local virtual environment for Python dependencies.
- Execute the implementation and its validation commands. Fix implementation errors
  you encounter, but do not weaken the prompt's validation or security requirements.
- Do not leave development servers running. The harness independently validates the
  result after you exit.
- Finish with a concise statement of files created, commands run, and any unmet
  validation rule.
{embedding}
# Published prompt

{prompt_text}
"""


class EvaluationRunner:
    """Run requested scenarios for each model in isolated Azure environments."""

    def __init__(self, settings: RunSettings, *, agent_name: str = "copilot"):
        self.settings = settings
        self.reporter = ProgressReporter()
        self.agent = create_agent(agent_name, reporter=self.reporter)
        self.run_id = (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        )
        self.run_dir = settings.output_root / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.results: list[ScenarioResult] = []
        self.cleanup_errors: list[str] = []

    def run(self) -> int:
        """Execute the matrix and return a process exit code."""
        selected = expand_scenarios(self.settings.scenarios)
        run_token = self.reporter.start(
            "run",
            self.run_id,
            f"models={','.join(self.settings.models)} scenarios={','.join(selected)}",
        )
        self.reporter.artifact(self.run_dir, "run evidence directory")
        manifest = {
            "schema_version": 1,
            "run_id": self.run_id,
            "started_at": datetime.now(UTC).isoformat(),
            "settings": {
                **asdict(self.settings),
                "repository": str(self.settings.repository),
                "output_root": str(self.settings.output_root),
            },
            "expanded_scenarios": selected,
            "agent": self.agent.name,
            "source_note": (
                "Criteria were transcribed from the user-supplied validation table after "
                "Hub-Prompt-Validation.docx proved DRM-protected. Detailed assertions also "
                "use each published prompt's Validation rules section."
            ),
        }
        self._write_json("manifest.json", manifest)
        self.reporter.artifact(self.run_dir / "manifest.json", "run manifest")
        for model in self.settings.models:
            self._run_model(model, selected)
        self._write_reports()
        failed = any(result.status not in {"PASS", "SKIP"} for result in self.results)
        exit_code = 1 if failed or self.cleanup_errors else 0
        self.reporter.artifact(self.run_dir / "summary.md", "run summary")
        self.reporter.finish(
            run_token,
            status="PASS" if exit_code == 0 else "FAIL",
            detail=f"exit={exit_code} summary={self.run_dir / 'summary.md'}",
        )
        return exit_code

    def _run_model(self, model: str, selected: tuple[str, ...]) -> None:
        model_token = self.reporter.start("model", model)
        result_start = len(self.results)
        model_dir = self.run_dir / _slug(model)
        model_dir.mkdir()
        environment = AzureEnvironment(
            tenant_id=self.settings.tenant_id,
            subscription_id=self.settings.subscription_id,
            location=self.settings.location,
            evidence_dir=model_dir,
            embedding_location=self.settings.embedding_location,
            provision_embedding=(
                self.settings.provision_embedding
                and any(SCENARIOS[name].requires_embedding for name in selected)
            ),
            existing_embedding_endpoint=self.settings.embedding_endpoint,
            existing_embedding_deployment=self.settings.embedding_deployment,
            existing_embedding_dimension=self.settings.embedding_dimension,
            existing_resource_group=self.settings.existing_resource_group,
            existing_server=self.settings.existing_server,
            reporter=self.reporter,
        )
        resources = None
        try:
            resources = environment.create()
            self._run_scenarios(model, model_dir, resources, selected)
        except HANDLED_ERRORS as exc:
            if resources is None:
                result = ScenarioResult(
                    scenario="azure-setup",
                    model=model,
                    status="ERROR",
                    reason=f"{type(exc).__name__}: {exc}",
                    workspace="",
                )
                self.results.append(result)
                self.reporter.error("model", model, result.reason)
        finally:
            try:
                environment.cleanup()
            except HANDLED_ERRORS as exc:
                message = f"{model}: {type(exc).__name__}: {exc}"
                self.cleanup_errors.append(message)
                (model_dir / "CLEANUP_REQUIRED.txt").write_text(
                    f"Manual cleanup required for {environment.resource_group}\n{message}\n",
                    encoding="utf-8",
                )
                self.reporter.error("cleanup", model, message)
            self._write_reports()
            model_results = self.results[result_start:]
            model_failed = any(
                result.status not in {"PASS", "SKIP"} for result in model_results
            )
            self.reporter.finish(
                model_token,
                status="FAIL" if model_failed or self.cleanup_errors else "PASS",
                detail=f"results={len(model_results)}",
            )

    def _run_scenarios(
        self,
        model: str,
        model_dir: Path,
        resources: AzureResources,
        selected: tuple[str, ...],
    ) -> None:
        statuses: dict[str, str] = {}
        workspace_root = model_dir / "workspaces"
        workspace_root.mkdir()
        for name in selected:
            spec = SCENARIOS[name]
            workspace = workspace_root / spec.workspace
            workspace.mkdir(exist_ok=True)
            scenario_dir = model_dir / "scenarios" / name
            scenario_dir.mkdir(parents=True)
            failed_dependencies = [
                dependency
                for dependency in spec.dependencies
                if statuses.get(dependency) != "PASS"
            ]
            if failed_dependencies:
                result = ScenarioResult(
                    scenario=name,
                    model=model,
                    status="BLOCKED",
                    reason="dependencies did not pass: " + ", ".join(failed_dependencies),
                    workspace=str(workspace),
                )
                statuses[name] = result.status
                self.results.append(result)
                self.reporter.info("scenario", name, result.reason)
                continue
            result = self._run_scenario(model, workspace, scenario_dir, resources, name)
            statuses[name] = result.status
            self.results.append(result)

    def _run_scenario(
        self,
        model: str,
        workspace: Path,
        scenario_dir: Path,
        resources: AzureResources,
        name: str,
    ) -> ScenarioResult:
        spec = SCENARIOS[name]
        scenario_token = self.reporter.start(
            "scenario", name, f"model={model} workspace={workspace}"
        )
        prompt_path = self.settings.repository / spec.prompt_file
        prompt_text = prompt_path.read_text(encoding="utf-8")
        prompt = build_prompt(
            prompt_text,
            scenario=name,
            resources=resources,
            workspace=workspace,
        )
        (scenario_dir / "prompt.md").write_text(prompt, encoding="utf-8")
        self.reporter.artifact(scenario_dir / "prompt.md", f"{name} agent prompt")
        started = time.monotonic()
        try:
            agent_result = self.agent.run(
                AgentRequest(
                    prompt=prompt,
                    model=model,
                    workspace=workspace,
                    evidence_dir=scenario_dir / "agent",
                    timeout_seconds=self.settings.agent_timeout_seconds,
                    session_name=f"sqlhub-{_slug(model)}-{name}-{self.run_id}",
                )
            )
            agent_duration = time.monotonic() - started
        except HANDLED_ERRORS as exc:
            result = ScenarioResult(
                scenario=name,
                model=model,
                status="FAIL",
                reason=f"agent failed: {type(exc).__name__}: {exc}",
                workspace=str(workspace),
                agent_duration_seconds=time.monotonic() - started,
            )
            self.reporter.finish(
                scenario_token, status="FAIL", detail=result.reason
            )
            return result
        validation_started = time.monotonic()
        try:
            evidence = spec.validator(
                workspace,
                resources,
                scenario_dir / "validation",
                self.settings.validation_timeout_seconds,
                self.reporter,
            )
            result = ScenarioResult(
                scenario=name,
                model=model,
                status="PASS",
                reason="independent end-state validation passed",
                workspace=str(workspace),
                agent_duration_seconds=agent_duration,
                validation_duration_seconds=time.monotonic() - validation_started,
                evidence=[
                    str(agent_result.stdout_path),
                    str(agent_result.stderr_path),
                    *evidence,
                ],
            )
            self.reporter.finish(
                scenario_token,
                detail=(
                    f"agent={agent_duration:.1f}s "
                    f"validation={result.validation_duration_seconds:.1f}s"
                ),
            )
            return result
        except HANDLED_ERRORS as exc:
            result = ScenarioResult(
                scenario=name,
                model=model,
                status="FAIL",
                reason=f"validation failed: {type(exc).__name__}: {exc}",
                workspace=str(workspace),
                agent_duration_seconds=agent_duration,
                validation_duration_seconds=time.monotonic() - validation_started,
                evidence=[str(agent_result.stdout_path), str(agent_result.stderr_path)],
            )
            self.reporter.finish(
                scenario_token, status="FAIL", detail=result.reason
            )
            return result

    def _write_reports(self) -> None:
        self._write_json(
            "results.json",
            {
                "schema_version": 1,
                "run_id": self.run_id,
                "results": [result.to_dict() for result in self.results],
                "cleanup_errors": self.cleanup_errors,
            },
        )
        rows = [
            "| Model | Scenario | Status | Reason |",
            "|---|---|---|---|",
        ]
        for result in self.results:
            reason = result.reason.replace("|", "\\|").replace("\n", " ")
            rows.append(
                f"| {result.model} | {result.scenario} | {result.status} | {reason} |"
            )
        if self.cleanup_errors:
            rows.extend(
                ["", "## Cleanup errors", ""]
                + [f"- {message}" for message in self.cleanup_errors]
            )
        (self.run_dir / "summary.md").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def _write_json(self, name: str, value) -> None:
        (self.run_dir / name).write_text(
            json.dumps(value, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    def remove_workspaces(self) -> None:
        """Remove generated workspaces after reports are complete when requested."""
        if self.settings.keep_workspaces:
            return
        for model in self.settings.models:
            path = self.run_dir / _slug(model) / "workspaces"
            if path.is_dir():
                shutil.rmtree(path)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
