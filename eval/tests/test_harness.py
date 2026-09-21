"""Unit tests for the prompt evaluation harness."""

from __future__ import annotations

import io
import json
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from hub_eval.agents import AgentRequest, CopilotCli
from hub_eval.azure import cleanup_resource_group
from hub_eval.command import CommandError, CommandRunner
from hub_eval.configuration import load_validation_environment
from hub_eval.models import AzureResources, RunSettings
from hub_eval.progress import ProgressReporter
from hub_eval.runner import EvaluationRunner, build_prompt, expand_scenarios
from hub_eval.validation import project_with


class ScenarioTests(unittest.TestCase):
    """Verify dependency expansion and unattended prompt construction."""

    def test_dependencies_are_included_in_canonical_order(self) -> None:
        self.assertEqual(
            expand_scenarios(("event-driven-app", "multi-tenant")),
            (
                "javascript-app",
                "serverless-api",
                "event-driven-app",
                "multi-tenant",
            ),
        )

    def test_prompt_supplies_all_required_database_inputs(self) -> None:
        resources = AzureResources(
            subscription_id="sub",
            resource_group="rg",
            location="test-region",
            server_name="server",
            database_name="db",
            server_fqdn="server.database.windows.net",
            embedding_endpoint="https://example.openai.azure.com/",
            embedding_deployment="text-embedding-3-small",
            embedding_dimension=1536,
        )
        prompt = build_prompt(
            "published prompt",
            scenario="rag-app",
            resources=resources,
            workspace=Path("/tmp/workspace"),
        )
        self.assertIn("Do not ask the user questions", prompt)
        self.assertIn("server.database.windows.net", prompt)
        self.assertIn("text-embedding-3-small", prompt)
        self.assertIn("Microsoft Entra via DefaultAzureCredential", prompt)
        self.assertTrue(prompt.endswith("published prompt\n"))

    def test_rag_prompt_uses_fixture_when_embedding_service_is_unavailable(
        self,
    ) -> None:
        resources = AzureResources(
            subscription_id="sub",
            resource_group="rg",
            location="test-region",
            server_name="server",
            database_name="db",
            server_fqdn="server.database.windows.net",
        )
        prompt = build_prompt(
            "published prompt",
            scenario="rag-app",
            resources=resources,
            workspace=Path("/tmp/workspace"),
        )
        self.assertIn("EMBED_PROVIDER=fixture", prompt)
        self.assertIn("EMBED_DIM=8", prompt)

    def test_project_discovery_ignores_dependency_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "package.json").write_text("{}")
            dependency = workspace / "node_modules/example"
            dependency.mkdir(parents=True)
            (dependency / "package.json").write_text("{}")
            self.assertEqual(project_with(workspace, "package.json"), workspace)

    def test_parallel_runners_get_unique_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = RunSettings(
                repository=root,
                output_root=root / "runs",
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                models=("gpt-5.4",),
                scenarios=("javascript-app",),
                agent_timeout_seconds=60,
                validation_timeout_seconds=30,
                keep_workspaces=False,
                provision_embedding=False,
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            first = EvaluationRunner(settings)
            second = EvaluationRunner(settings)
            self.assertNotEqual(first.run_dir, second.run_dir)


class CommandTests(unittest.TestCase):
    """Verify command and Copilot evidence contracts without external services."""

    def test_command_runner_captures_stdout_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = CommandRunner(root).run(
                ["python3", "-c", "print('ok')"],
                label="sample",
                check=True,
            )
            self.assertEqual(result.stdout_path.read_text().strip(), "ok")
            metadata = json.loads(next(root.glob("*-sample.json")).read_text())
            self.assertEqual(metadata["returncode"], 0)
            self.assertFalse(metadata["timed_out"])

    def test_command_runner_prints_start_end_and_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            reporter = ProgressReporter(stream=output, error_stream=output)
            CommandRunner(Path(temporary), reporter=reporter).run(
                ["python3", "-c", "print('ok')"],
                label="sample",
                check=True,
            )
            text = output.getvalue()
            self.assertIn("START | command | sample", text)
            self.assertIn("END | command | sample | PASS", text)
            self.assertIn("duration=", text)

    def test_command_failure_prints_redacted_error_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            reporter = ProgressReporter(stream=output, error_stream=output)
            with self.assertRaisesRegex(CommandError, "permission denied"):
                CommandRunner(Path(temporary), reporter=reporter).run(
                    [
                        "python3",
                        "-c",
                        (
                            "import sys; "
                            "print('permission denied token=super-secret', file=sys.stderr); "
                            "raise SystemExit(2)"
                        ),
                    ],
                    label="failing-command",
                    check=True,
                )
            text = output.getvalue()
            self.assertIn("permission denied", text)
            self.assertIn("token=[REDACTED]", text)
            self.assertNotIn("super-secret", text)

    def test_copilot_adapter_accepts_valid_jsonl_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "fake-copilot"
            executable.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf '%s\\n' '{"type":"assistant.message","data":{"content":"OK"}}'
                    printf '%s\\n' '{"type":"result","exitCode":0}'
                    """
                )
            )
            executable.chmod(0o755)
            workspace = root / "workspace"
            workspace.mkdir()
            result = CopilotCli(str(executable)).run(
                AgentRequest(
                    prompt="test",
                    model="test-model",
                    workspace=workspace,
                    evidence_dir=root / "evidence",
                    timeout_seconds=60,
                    session_name="test-session",
                )
            )
            self.assertTrue(result.succeeded)

    def test_process_cleanup_tolerates_permission_race(self) -> None:
        with (
            patch("hub_eval.command.os.killpg", side_effect=PermissionError),
            patch("hub_eval.command.time.sleep"),
        ):
            CommandRunner._terminate_group(12345, ignore_missing=True)


class CleanupSafetyTests(unittest.TestCase):
    """Verify manual cleanup refuses unrelated Azure resource groups."""

    def test_cleanup_rejects_unrelated_resource_group(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaises(ValueError),
        ):
            cleanup_resource_group(
                "tenant",
                "subscription",
                "test-region",
                "test-embedding-region",
                "production-resource-group",
                Path(temporary),
            )


class ConfigurationTests(unittest.TestCase):
    """Verify strict validation.env parsing."""

    def test_loads_complete_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "validation.env"
            path.write_text(
                """\
HUB_EVAL_AZURE_TENANT_ID=tenant
HUB_EVAL_AZURE_SUBSCRIPTION_ID=subscription
HUB_EVAL_AZURE_LOCATION=test-region
HUB_EVAL_EXISTING_RESOURCE_GROUP=test-group
HUB_EVAL_EXISTING_SQL_SERVER=test-server
HUB_EVAL_EMBEDDING_LOCATION=test-embedding-region
HUB_EVAL_PROVISION_EMBEDDING=false
HUB_EVAL_EMBEDDING_ENDPOINT=
HUB_EVAL_EMBEDDING_DEPLOYMENT=
HUB_EVAL_EMBEDDING_DIMENSION=
"""
            )
            config = load_validation_environment(path)
            self.assertEqual(config.tenant_id, "tenant")
            self.assertEqual(config.existing_server, "test-server")
            self.assertFalse(config.provision_embedding)


if __name__ == "__main__":
    unittest.main()
