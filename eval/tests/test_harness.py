"""Unit tests for the prompt evaluation harness."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from hub_eval.agents import AgentRequest, CopilotCli
from hub_eval.azure import AzureEnvironment, cleanup_resource_group, missing_permissions
from hub_eval.command import CommandError, CommandRunner
from hub_eval.configuration import load_validation_environment
from hub_eval.models import (
    AzureResources,
    EnvironmentResult,
    PermissionCheck,
    PermissionResult,
    PreflightResult,
    RunSettings,
    ScenarioResult,
)
from hub_eval.progress import ProgressReporter
from hub_eval.runner import EvaluationRunner, build_prompt, expand_scenarios
from hub_eval.validation import project_with
from run_evals import run_preflight


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

    def test_rag_prompt_requires_embedding_service(self) -> None:
        resources = AzureResources(
            subscription_id="sub",
            resource_group="rg",
            location="test-region",
            server_name="server",
            database_name="db",
            server_fqdn="server.database.windows.net",
        )
        with self.assertRaisesRegex(
            CommandError,
            "requires a provisioned Azure OpenAI embedding deployment",
        ):
            build_prompt(
                "published prompt",
                scenario="rag-app",
                resources=resources,
                workspace=Path("/tmp/workspace"),
            )

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


class AzurePermissionTests(unittest.TestCase):
    """Verify Azure permission matching and mode-specific preflight requirements."""

    def test_preflight_checks_context_identity_providers_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_resource_group="rg",
                existing_server="server",
            )
            identity = {"displayName": "Test User", "id": "user-id"}
            with (
                patch.object(environment.az, "verify_context") as verify_context,
                patch.object(environment.az, "json", return_value=identity) as az_json,
                patch.object(
                    environment,
                    "_verify_provider_registrations",
                ) as verify_providers,
                patch.object(
                    environment,
                    "_verify_permissions",
                ) as verify_permissions,
            ):
                self.assertEqual(environment.preflight(), identity)
            verify_context.assert_called_once_with()
            az_json.assert_called_once_with(
                ["ad", "signed-in-user", "show"],
                label="az-signed-in-user",
            )
            verify_providers.assert_called_once_with()
            verify_permissions.assert_called_once_with()

    def test_permission_matching_honors_wildcards_and_not_actions(self) -> None:
        required = (
            "Microsoft.Sql/servers/read",
            "Microsoft.Sql/servers/delete",
            "Microsoft.CognitiveServices/accounts/write",
        )
        permissions = [
            {
                "actions": ["Microsoft.Sql/*"],
                "notActions": ["Microsoft.Sql/servers/delete"],
            },
            {
                "actions": ["Microsoft.CognitiveServices/accounts/read"],
                "notActions": [],
            },
        ]
        self.assertEqual(
            missing_permissions(required, permissions),
            [
                "Microsoft.Sql/servers/delete",
                "Microsoft.CognitiveServices/accounts/write",
            ],
        )

    def test_permission_check_records_scope_and_required_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=False,
                existing_resource_group="rg",
                existing_server="server",
            )
            scope = "/subscriptions/sub/resourceGroups/rg"
            required = (
                "Microsoft.Sql/servers/read",
                "Microsoft.Sql/servers/delete",
            )
            with patch.object(
                environment.az,
                "json",
                return_value={
                    "value": [
                        {
                            "actions": ["Microsoft.Sql/*"],
                            "notActions": ["Microsoft.Sql/servers/delete"],
                        }
                    ]
                },
            ):
                with self.assertRaisesRegex(CommandError, "servers/delete"):
                    environment._verify_permissions_at_scope(scope, required)

            self.assertEqual(
                environment.permission_checks,
                [
                    PermissionCheck(
                        scope=scope,
                        permissions=[
                            PermissionResult(
                                permission="Microsoft.Sql/servers/read",
                                status="PASS",
                            ),
                            PermissionResult(
                                permission="Microsoft.Sql/servers/delete",
                                status="FAIL",
                            ),
                        ],
                    )
                ],
            )

    def test_existing_server_rag_preflight_checks_embedding_permissions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_resource_group="rg",
                existing_server="server",
            )
            required = environment._required_permissions()
            self.assertIn("Microsoft.Sql/servers/databases/write", required)
            self.assertIn("Microsoft.CognitiveServices/accounts/write", required)
            self.assertIn("Microsoft.Authorization/roleAssignments/write", required)
            self.assertNotIn(
                "Microsoft.CognitiveServices/locations/resourceGroups/"
                "deletedAccounts/delete",
                required,
            )
            self.assertNotIn(
                "Microsoft.Resources/subscriptions/resourceGroups/write",
                required,
            )

    def test_existing_embedding_does_not_require_provisioning_permissions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_embedding_endpoint="https://example.openai.azure.com/",
                existing_embedding_deployment="embedding",
                existing_embedding_dimension=1536,
                existing_resource_group="rg",
                existing_server="server",
            )
            required = environment._required_permissions()
            self.assertNotIn("Microsoft.CognitiveServices/accounts/write", required)
            self.assertNotIn("Microsoft.Authorization/roleAssignments/write", required)

    def test_provider_preflight_requires_cognitive_services_for_provisioning(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_resource_group="rg",
                existing_server="server",
            )
            with patch.object(
                environment.az,
                "text",
                side_effect=["Registered", "NotRegistered"],
            ):
                with self.assertRaisesRegex(
                    CommandError,
                    "az provider register --namespace Microsoft.CognitiveServices --wait",
                ):
                    environment._verify_provider_registrations()

    def test_existing_server_checks_purge_permissions_at_subscription_scope(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_resource_group="rg",
                existing_server="server",
            )
            with patch.object(
                environment,
                "_verify_permissions_at_scope",
            ) as verify:
                environment._verify_permissions()
            self.assertEqual(verify.call_count, 2)
            self.assertEqual(verify.call_args_list[1].args[0], "/subscriptions/sub")
            self.assertIn(
                "Microsoft.CognitiveServices/locations/resourceGroups/"
                "deletedAccounts/delete",
                verify.call_args_list[1].args[1],
            )

    def test_provisioned_resource_ids_include_only_created_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_resource_group="rg",
                existing_server="server",
            )
            environment.firewall_created = True
            environment.database_created = True
            environment.embedding_account_name = "aoai-test"
            environment.embedding_deployment_name = "embedding"
            environment.embedding_role_assignment_id = (
                "/subscriptions/sub/providers/Microsoft.Authorization/"
                "roleAssignments/assignment"
            )

            self.assertEqual(
                environment.provisioned_resource_ids(),
                [
                    "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/"
                    "servers/server/firewallRules/"
                    f"{environment.firewall_rule_name}",
                    "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/"
                    f"servers/server/databases/{environment.database_name}",
                    "/subscriptions/sub/resourceGroups/rg/providers/"
                    "Microsoft.CognitiveServices/accounts/aoai-test",
                    "/subscriptions/sub/resourceGroups/rg/providers/"
                    "Microsoft.CognitiveServices/accounts/aoai-test/"
                    "deployments/embedding",
                    "/subscriptions/sub/providers/Microsoft.Authorization/"
                    "roleAssignments/assignment",
                ],
            )

    def test_provisioned_resource_ids_include_created_group_and_server(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=False,
            )
            environment.group_created = True
            environment.server_created = True

            self.assertEqual(
                environment.provisioned_resource_ids(),
                [
                    f"/subscriptions/sub/resourceGroups/{environment.resource_group}",
                    f"/subscriptions/sub/resourceGroups/{environment.resource_group}/"
                    "providers/Microsoft.Sql/servers/"
                    f"{environment.server_name}",
                ],
            )


class ReportTests(unittest.TestCase):
    """Verify aggregate machine-readable result output."""

    def test_scenario_result_matches_aggregate_result(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            scenario_dir = runner.run_dir / "gpt-5-4/scenarios/javascript-app"
            scenario_dir.mkdir(parents=True)
            result = ScenarioResult(
                scenario="javascript-app",
                model="gpt-5.4",
                status="PASS",
                reason="independent end-state validation passed",
                workspace="/tmp/workspace",
                agent_duration_seconds=10.0,
                validation_duration_seconds=2.0,
                evidence=["evidence.txt"],
            )

            runner._record_scenario_result(scenario_dir, result)
            runner._write_reports()

            scenario_result = json.loads(
                (scenario_dir / "result.json").read_text()
            )
            aggregate = json.loads((runner.run_dir / "results.json").read_text())
            self.assertEqual(scenario_result, result.to_dict())
            self.assertEqual(aggregate["results"], [scenario_result])

    def test_results_include_environment_durations_and_resource_ids(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.environments.append(
                EnvironmentResult(
                    model="gpt-5.4",
                    setup_duration_seconds=12.5,
                    cleanup_duration_seconds=3.25,
                    provisioned_resource_ids=[
                        "/subscriptions/sub/resourceGroups/rg"
                    ],
                )
            )
            runner.duration_seconds = 20.5

            runner._write_reports()

            results = json.loads((runner.run_dir / "results.json").read_text())
            self.assertEqual(results["schema_version"], 6)
            self.assertEqual(results["duration_seconds"], 20.5)
            self.assertEqual(
                results["environments"],
                [
                    {
                        "model": "gpt-5.4",
                        "setup_duration_seconds": 12.5,
                        "cleanup_duration_seconds": 3.25,
                        "provisioned_resource_ids": [
                            "/subscriptions/sub/resourceGroups/rg"
                        ],
                    }
                ],
            )

    def test_model_run_records_setup_and_cleanup_durations(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.reporter = Mock()
            resources = AzureResources(
                subscription_id="sub",
                resource_group="rg",
                location="test-region",
                server_name="server",
                database_name="db",
                server_fqdn="server.database.windows.net",
            )
            environment = Mock()
            identity = {"displayName": "Test User", "id": "user-id"}
            environment.preflight.return_value = identity
            environment.resource_group = "rg"
            environment.permission_checks = [
                PermissionCheck(
                    scope="/subscriptions/sub/resourceGroups/rg",
                    permissions=[
                        PermissionResult(
                            permission="Microsoft.Sql/servers/read",
                            status="PASS",
                        )
                    ],
                )
            ]
            environment.provisioned_resource_ids.return_value = [
                "/subscriptions/sub/resourceGroups/rg"
            ]

            def create_after_preflight(preflight_identity):
                preflight = json.loads(
                    (runner.run_dir / "preflight.json").read_text()
                )
                self.assertEqual(
                    preflight["results"][0]["status"],
                    "PASS",
                )
                self.assertEqual(preflight_identity, identity)
                return resources

            environment.create.side_effect = create_after_preflight

            with (
                patch("hub_eval.runner.AzureEnvironment", return_value=environment),
                patch.object(runner, "_run_scenarios"),
                patch(
                    "hub_eval.runner.time.monotonic",
                    side_effect=[
                        5.0,
                        10.0,
                        11.0,
                        12.0,
                        14.0,
                        20.0,
                        23.25,
                        25.0,
                    ],
                ),
            ):
                runner._run_model("gpt-5.4", ("javascript-app",))

            self.assertEqual(
                runner.preflight_results,
                [
                    PreflightResult(
                        model="gpt-5.4",
                        status="PASS",
                        duration_seconds=1.0,
                        subscription_id="sub",
                        resource_group="rg",
                        scenarios=["javascript-app"],
                        identity={
                            "display_name": "Test User",
                            "object_id": "user-id",
                        },
                        permission_checks=[
                            PermissionCheck(
                                scope="/subscriptions/sub/resourceGroups/rg",
                                permissions=[
                                    PermissionResult(
                                        permission="Microsoft.Sql/servers/read",
                                        status="PASS",
                                    )
                                ],
                            )
                        ],
                        reason=(
                            "Azure context, providers, and permissions validated"
                        ),
                    )
                ],
            )
            self.assertEqual(
                runner.environments,
                [
                    EnvironmentResult(
                        model="gpt-5.4",
                        setup_duration_seconds=4.0,
                        cleanup_duration_seconds=3.25,
                        provisioned_resource_ids=[
                            "/subscriptions/sub/resourceGroups/rg"
                        ],
                    )
                ],
            )
            environment.create.assert_called_once_with(identity)
            environment.cleanup.assert_called_once_with()
            model_results = json.loads(
                (runner.run_dir / "gpt-5-4/results.json").read_text()
            )
            self.assertEqual(model_results["schema_version"], 1)
            self.assertEqual(model_results["model"], "gpt-5.4")
            self.assertEqual(model_results["duration_seconds"], 20.0)
            self.assertEqual(
                model_results["environment"],
                runner.environments[0].to_dict(),
            )
            self.assertEqual(
                model_results["preflight"],
                runner.preflight_results[0].to_dict(),
            )
            self.assertEqual(model_results["results"], [])
            self.assertEqual(model_results["cleanup_errors"], [])

    def test_run_records_total_execution_duration(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.reporter = Mock()

            with (
                patch.object(runner, "_run_model"),
                patch(
                    "hub_eval.runner.time.monotonic",
                    side_effect=[10.0, 25.0],
                ),
            ):
                exit_code = runner.run()

            results = json.loads((runner.run_dir / "results.json").read_text())
            self.assertEqual(exit_code, 0)
            self.assertEqual(results["duration_seconds"], 15.0)

    def test_preflight_file_matches_aggregate_preflight(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.preflight_results.append(
                PreflightResult(
                    model="gpt-5.4",
                    status="PASS",
                    duration_seconds=1.5,
                    subscription_id="sub",
                    resource_group="rg",
                    scenarios=["javascript-app"],
                    identity={
                        "display_name": "Test User",
                        "object_id": "user-id",
                    },
                    permission_checks=[
                        PermissionCheck(
                            scope="/subscriptions/sub/resourceGroups/rg",
                            permissions=[
                                PermissionResult(
                                    permission="Microsoft.Sql/servers/read",
                                    status="PASS",
                                )
                            ],
                        )
                    ],
                    reason="Azure context, providers, and permissions validated",
                )
            )

            runner._write_reports()

            preflight = json.loads((runner.run_dir / "preflight.json").read_text())
            results = json.loads((runner.run_dir / "results.json").read_text())
            self.assertEqual(preflight["schema_version"], 3)
            self.assertEqual(results["preflight"], preflight)

    def test_failed_preflight_is_written_before_provisioning(self) -> None:
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
                embedding_location="test-embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.reporter = Mock()
            environment = Mock()
            environment.preflight.side_effect = CommandError("missing permissions")
            environment.resource_group = "rg"
            environment.permission_checks = [
                PermissionCheck(
                    scope="/subscriptions/sub/resourceGroups/rg",
                    permissions=[
                        PermissionResult(
                            permission="Microsoft.Sql/servers/read",
                            status="FAIL",
                        )
                    ],
                )
            ]
            environment.provisioned_resource_ids.return_value = []

            with (
                patch("hub_eval.runner.AzureEnvironment", return_value=environment),
                patch(
                    "hub_eval.runner.time.monotonic",
                    side_effect=[
                        5.0,
                        10.0,
                        11.0,
                        12.0,
                        14.0,
                        20.0,
                        21.0,
                        25.0,
                    ],
                ),
            ):
                runner._run_model("gpt-5.4", ("javascript-app",))

            preflight = json.loads((runner.run_dir / "preflight.json").read_text())
            results = json.loads((runner.run_dir / "results.json").read_text())
            self.assertEqual(preflight["results"][0]["status"], "FAIL")
            self.assertEqual(
                preflight["results"][0]["reason"],
                "CommandError: missing permissions",
            )
            self.assertEqual(
                preflight["results"][0]["permission_checks"],
                [
                    {
                        "scope": "/subscriptions/sub/resourceGroups/rg",
                        "permissions": [
                            {
                                "permission": "Microsoft.Sql/servers/read",
                                "status": "FAIL",
                            }
                        ],
                    }
                ],
            )
            self.assertEqual(results["preflight"], preflight)
            self.assertEqual(results["results"][0]["scenario"], "azure-setup")
            model_results = json.loads(
                (runner.run_dir / "gpt-5-4/results.json").read_text()
            )
            self.assertEqual(model_results["duration_seconds"], 20.0)
            self.assertEqual(
                model_results["results"][0]["scenario"],
                "azure-setup",
            )
            environment.create.assert_not_called()

    def test_standalone_preflight_creates_run_folder_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "runs"
            args = argparse.Namespace(
                output=output,
                tenant="tenant",
                subscription="sub",
                location="test-region",
                embedding_location="embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group="rg",
                existing_server="server",
            )
            identity = {"displayName": "Test User", "id": "user-id"}
            environment = Mock()
            environment.preflight.return_value = identity
            environment.resource_group = "rg"
            environment.permission_checks = [
                PermissionCheck(
                    scope="/subscriptions/sub/resourceGroups/rg",
                    permissions=[
                        PermissionResult(
                            permission="Microsoft.Sql/servers/read",
                            status="PASS",
                        )
                    ],
                )
            ]

            with (
                patch("run_evals.AzureEnvironment", return_value=environment),
                patch("run_evals.create_run_id", return_value="test-run"),
                patch("run_evals.time.monotonic", side_effect=[10.0, 12.0]),
                patch("builtins.print"),
            ):
                exit_code = run_preflight(args, ("javascript-app",))

            preflight_path = output / "test-run/preflight.json"
            self.assertEqual(exit_code, 0)
            self.assertTrue(preflight_path.is_file())
            preflight = json.loads(preflight_path.read_text())
            self.assertEqual(preflight["run_id"], "test-run")
            self.assertEqual(preflight["results"][0]["model"], None)
            self.assertEqual(
                preflight["results"][0]["permission_checks"][0]["permissions"],
                [
                    {
                        "permission": "Microsoft.Sql/servers/read",
                        "status": "PASS",
                    }
                ],
            )


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

    def test_final_result_lines_use_status_emoji_and_nonpass_details(self) -> None:
        output = io.StringIO()
        reporter = ProgressReporter(stream=output, error_stream=output)
        reporter.result(
            status="PASS",
            scenario="javascript-app",
            harness="copilot",
            model="gpt",
            details="not printed",
        )
        reporter.result(
            status="BLOCKED",
            scenario="multi-tenant",
            harness="copilot",
            model="claude",
            details="dependency failed\nwith details",
        )
        lines = output.getvalue().splitlines()
        self.assertEqual(
            lines[0],
            "✅ PASS | scenario=javascript-app | harness=copilot | model=gpt",
        )
        self.assertEqual(
            lines[1],
            (
                "⚠️ BLOCKED | scenario=multi-tenant | harness=copilot | "
                "model=claude | details=dependency failed with details"
            ),
        )

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

    def test_copilot_adapter_tolerates_malformed_intermediate_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "fake-copilot"
            executable.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf '%s\\n' '{"type":"assistant.message","data":'
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

    def test_copilot_adapter_rejects_malformed_stream_without_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "fake-copilot"
            executable.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf '%s\\n' '{"type":"assistant.message","data":'
                    """
                )
            )
            executable.chmod(0o755)
            workspace = root / "workspace"
            workspace.mkdir()
            with self.assertRaisesRegex(
                CommandError,
                "Copilot emitted no final result record",
            ):
                CopilotCli(str(executable)).run(
                    AgentRequest(
                        prompt="test",
                        model="test-model",
                        workspace=workspace,
                        evidence_dir=root / "evidence",
                        timeout_seconds=60,
                        session_name="test-session",
                    )
                )

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
HUB_EVAL_EMBEDDING_ENDPOINT=
HUB_EVAL_EMBEDDING_DEPLOYMENT=
HUB_EVAL_EMBEDDING_DIMENSION=
"""
            )
            config = load_validation_environment(path)
            self.assertEqual(config.tenant_id, "tenant")
            self.assertEqual(config.existing_server, "test-server")


if __name__ == "__main__":
    unittest.main()
