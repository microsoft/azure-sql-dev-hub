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

from hub_eval.agents import (
    AgentRequest,
    ClaudeCli,
    CodexCli,
    CopilotCli,
    create_agent,
)
from hub_eval.catalog import documented_models
from hub_eval.azure import (
    AZURE_OPENAI_EMBEDDINGS_PERMISSION,
    AZURE_SQL_DATABASE_MANAGER_PERMISSION,
    AzureEnvironment,
    cleanup_resource_group,
    missing_permissions,
)
from hub_eval.command import CommandError, CommandRunner
from hub_eval.configuration import ConfigurationError, load_validation_environment
from hub_eval.database import DatabaseProbe
from hub_eval.models import (
    AgentPreflightResult,
    AzureResources,
    CommandResult,
    EnvironmentResult,
    EvaluationTarget,
    PermissionCheck,
    PermissionResult,
    PreflightResult,
    RunSettings,
    ScenarioResult,
)
from hub_eval.matrix import load_test_matrix
from hub_eval.progress import ProgressReporter
from hub_eval.runner import EvaluationRunner, build_prompt, expand_scenarios
from hub_eval.validation import project_with
from run_evals import (
    AGENT_PREFLIGHT_RESPONSE,
    main,
    parse_args,
    run_agent_preflight,
    run_preflight,
)


class RunnerTests(unittest.TestCase):
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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

    def test_cross_harness_same_model_uses_distinct_target_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            targets = (
                EvaluationTarget("copilot", "shared-model"),
                EvaluationTarget("claude", "shared-model"),
            )
            settings = RunSettings(
                repository=root,
                output_root=root / "runs",
                tenant_id="tenant",
                subscription_id="sub",
                location="region",
                targets=targets,
                scenarios=("javascript-app",),
                agent_timeout_seconds=60,
                validation_timeout_seconds=30,
                keep_workspaces=False,
                embedding_location="embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            runner.reporter = Mock()
            environment = Mock()
            environment.preflight.return_value = {
                "displayName": "User",
                "id": "id",
            }
            environment.resource_group = "rg"
            environment.permission_checks = []
            environment.create.return_value = Mock()
            environment.provisioned_resource_ids.return_value = []
            adapters = {"copilot": Mock(name="copilot"), "claude": Mock(name="claude")}
            with (
                patch("hub_eval.runner.AzureEnvironment", return_value=environment),
                patch(
                    "hub_eval.runner.create_agent",
                    side_effect=lambda name, reporter: adapters[name],
                ) as create_agent_mock,
                patch.object(runner, "_run_scenarios") as run_scenarios,
            ):
                for target in targets:
                    runner._run_target(target, ("javascript-app",))
            self.assertTrue(
                (runner.run_dir / "copilot/shared-model/results.json").is_file()
            )
            self.assertTrue(
                (runner.run_dir / "claude/shared-model/results.json").is_file()
            )
            self.assertEqual(
                [call.args[0] for call in create_agent_mock.call_args_list],
                ["copilot", "claude"],
            )
            self.assertIs(run_scenarios.call_args_list[0].args[1], adapters["copilot"])
            self.assertIs(run_scenarios.call_args_list[1].args[1], adapters["claude"])

    def test_manifest_copies_exact_source_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            configuration = root / "input.yml"
            source = "schema_version: 1\n# exact source\n"
            configuration.write_text(source, encoding="utf-8")
            settings = RunSettings(
                repository=root,
                output_root=root / "runs",
                tenant_id="tenant",
                subscription_id="sub",
                location="region",
                targets=(EvaluationTarget("claude", "model"),),
                scenarios=("javascript-app",),
                agent_timeout_seconds=60,
                validation_timeout_seconds=30,
                keep_workspaces=False,
                embedding_location="embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
                configuration_path=configuration,
            )
            runner = EvaluationRunner(settings)
            runner.reporter = Mock()
            with patch.object(runner, "_run_target"):
                self.assertEqual(runner.run(), 0)
            manifest = json.loads((runner.run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(
                manifest["settings"]["targets"],
                [{"harness": "claude", "model": "model"}],
            )
            self.assertEqual(
                manifest["source_configuration"], str(configuration)
            )
            self.assertEqual(
                (runner.run_dir / "configuration.yml").read_text(), source
            )

    def test_workspace_cleanup_traverses_every_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            targets = (
                EvaluationTarget("copilot", "same"),
                EvaluationTarget("claude", "same"),
            )
            settings = RunSettings(
                repository=root,
                output_root=root / "runs",
                tenant_id="tenant",
                subscription_id="sub",
                location="region",
                targets=targets,
                scenarios=("javascript-app",),
                agent_timeout_seconds=60,
                validation_timeout_seconds=30,
                keep_workspaces=False,
                embedding_location="embedding-region",
                embedding_endpoint=None,
                embedding_deployment=None,
                embedding_dimension=None,
                existing_resource_group=None,
                existing_server=None,
            )
            runner = EvaluationRunner(settings)
            for target in targets:
                workspace = (
                    runner.run_dir
                    / target.harness
                    / target.model
                    / "workspaces"
                )
                workspace.mkdir(parents=True)
            runner.remove_workspaces()
            for target in targets:
                self.assertFalse(
                    (
                        runner.run_dir
                        / target.harness
                        / target.model
                        / "workspaces"
                    ).exists()
                )


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
                patch.object(
                    environment,
                    "_verify_data_plane_permissions",
                ) as verify_data_plane_permissions,
            ):
                self.assertEqual(environment.preflight(), identity)
            verify_context.assert_called_once_with()
            az_json.assert_called_once_with(
                ["ad", "signed-in-user", "show"],
                label="az-signed-in-user",
            )
            verify_providers.assert_called_once_with()
            verify_permissions.assert_called_once_with()
            verify_data_plane_permissions.assert_called_once_with()

    def test_data_plane_preflight_records_all_failures(self) -> None:
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
            with (
                patch.object(
                    environment,
                    "_verify_existing_sql_database_manager",
                    side_effect=CommandError("SQL database manager missing"),
                ),
                patch.object(
                    environment,
                    "_verify_existing_embedding_access",
                    side_effect=CommandError("embedding access denied"),
                ),
            ):
                with self.assertRaisesRegex(
                    CommandError,
                    "data-plane preflight failed",
                ):
                    environment._verify_data_plane_permissions()

            self.assertEqual(
                environment.permission_checks,
                [
                    PermissionCheck(
                        scope=(
                            "/subscriptions/sub/resourceGroups/rg/providers/"
                            "Microsoft.Sql/servers/server"
                        ),
                        permissions=[
                            PermissionResult(
                                permission=AZURE_SQL_DATABASE_MANAGER_PERMISSION,
                                status="FAIL",
                            )
                        ],
                    ),
                    PermissionCheck(
                        scope="https://example.openai.azure.com/",
                        permissions=[
                            PermissionResult(
                                permission=AZURE_OPENAI_EMBEDDINGS_PERMISSION,
                                status="FAIL",
                            )
                        ],
                    ),
                ],
            )

    def test_existing_sql_database_manager_membership_passes(self) -> None:
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
            probe = Mock()
            probe.scalar.return_value = 1
            with patch.object(
                environment,
                "_database_probe",
                return_value=probe,
            ) as database_probe:
                environment._verify_existing_sql_database_manager()

            database_probe.assert_called_once_with("master")
            probe.scalar.assert_called_once_with(
                "SELECT IS_SRVROLEMEMBER(N'##MS_DatabaseManager##');",
                attempts=1,
                label="sql-database-manager-role",
            )

    def test_existing_sql_database_manager_membership_fails(self) -> None:
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
            probe = Mock()
            probe.scalar.return_value = 0
            with patch.object(
                environment,
                "_database_probe",
                return_value=probe,
            ):
                with self.assertRaisesRegex(
                    CommandError,
                    "not a member of ##MS_DatabaseManager##",
                ):
                    environment._verify_existing_sql_database_manager()

    def test_existing_embedding_access_validates_output_dimension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = AzureEnvironment(
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                evidence_dir=Path(temporary),
                embedding_location="embedding-region",
                provision_embedding=True,
                existing_embedding_endpoint="https://example.openai.azure.com/",
                existing_embedding_deployment="embedding deployment",
                existing_embedding_dimension=3,
                existing_resource_group="rg",
                existing_server="server",
            )
            response = Mock()
            response.read.return_value = json.dumps(
                {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
            ).encode()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            with (
                patch(
                    "hub_eval.azure.AzureEnvironment._azure_openai_access_token",
                    return_value="access-token",
                ),
                patch(
                    "hub_eval.azure.urlopen",
                    return_value=response,
                ) as urlopen_mock,
            ):
                environment._verify_existing_embedding_access()

            request = urlopen_mock.call_args.args[0]
            self.assertIn(
                "/deployments/embedding%20deployment/embeddings",
                request.full_url,
            )
            self.assertEqual(
                json.loads(request.data),
                {"input": "Azure SQL evaluation preflight"},
            )
            self.assertEqual(
                request.get_header("Authorization"),
                "Bearer access-token",
            )

    def test_existing_embedding_access_rejects_wrong_dimension(self) -> None:
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
                existing_embedding_dimension=3,
                existing_resource_group="rg",
                existing_server="server",
            )
            response = Mock()
            response.read.return_value = json.dumps(
                {"data": [{"embedding": [0.1, 0.2]}]}
            ).encode()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            with (
                patch(
                    "hub_eval.azure.AzureEnvironment._azure_openai_access_token",
                    return_value="access-token",
                ),
                patch("hub_eval.azure.urlopen", return_value=response),
            ):
                with self.assertRaisesRegex(
                    CommandError,
                    "returned 2 dimensions; expected 3",
                ):
                    environment._verify_existing_embedding_access()

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
            self.assertNotIn("Microsoft.Sql/servers/databases/write", required)
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

    def test_existing_server_database_is_created_through_sql(self) -> None:
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
            probe = Mock()
            with patch.object(
                environment,
                "_database_probe",
                return_value=probe,
            ) as database_probe:
                environment._create_database()

            database_probe.assert_called_once_with("master")
            statement = probe.execute.call_args.args[0]
            self.assertIn(
                f"CREATE DATABASE [{environment.database_name}]",
                statement,
            )
            self.assertIn("EDITION = 'Basic'", statement)
            self.assertIn("SERVICE_OBJECTIVE = 'Basic'", statement)
            probe.execute.assert_called_once_with(
                statement,
                label="sql-database-create",
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


class DatabaseProbeTests(unittest.TestCase):
    """Verify read and autocommit execution behavior for SQL probes."""

    def test_execute_uses_autocommit_without_fetching_rows(self) -> None:
        resources = AzureResources(
            subscription_id="sub",
            resource_group="rg",
            location="test-region",
            server_name="server",
            database_name="master",
            server_fqdn="server.database.windows.net",
        )
        credential = Mock()
        connection = Mock()
        cursor = connection.cursor.return_value
        with (
            patch(
                "hub_eval.database.AzureCliCredential",
                return_value=credential,
            ),
            patch(
                "hub_eval.database.mssql_python.connect",
                return_value=connection,
            ) as connect,
        ):
            probe = DatabaseProbe(resources)
            probe.execute(
                "CREATE DATABASE [evaluation];",
                label="sql-database-create",
            )

        connect.assert_called_once_with(
            (
                "Server=tcp:server.database.windows.net,1433;"
                "Database=master;"
                "Encrypt=yes;TrustServerCertificate=no;"
            ),
            autocommit=True,
            token_provider=credential,
            timeout=30,
        )
        cursor.execute.assert_called_once_with(
            "CREATE DATABASE [evaluation];"
        )
        cursor.fetchall.assert_not_called()
        cursor.close.assert_called_once_with()
        connection.close.assert_called_once_with()


class ReportingTests(unittest.TestCase):
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
            scenario_dir = (
                runner.run_dir / "copilot/gpt-5-4/scenarios/javascript-app"
            )
            scenario_dir.mkdir(parents=True)
            result = ScenarioResult(
                scenario="javascript-app",
                harness="copilot",
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
            self.assertTrue(
                (runner.run_dir / "summary.md")
                .read_text()
                .startswith("| Harness | Model | Scenario | Status | Reason |")
            )

    def test_results_include_environment_durations_and_resource_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = RunSettings(
                repository=root,
                output_root=root / "runs",
                tenant_id="tenant",
                subscription_id="sub",
                location="test-region",
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
                    harness="copilot",
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
            self.assertEqual(results["schema_version"], 7)
            self.assertEqual(results["duration_seconds"], 20.5)
            self.assertEqual(
                results["environments"],
                [
                    {
                        "harness": "copilot",
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
                runner._run_target(
                    EvaluationTarget("copilot", "gpt-5.4"),
                    ("javascript-app",),
                )

            self.assertEqual(
                runner.preflight_results,
                [
                    PreflightResult(
                        harness="copilot",
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
                        harness="copilot",
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
                (runner.run_dir / "copilot/gpt-5-4/results.json").read_text()
            )
            self.assertEqual(model_results["schema_version"], 2)
            self.assertEqual(model_results["harness"], "copilot")
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
                patch.object(runner, "_run_target"),
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
                    harness="copilot",
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
            self.assertEqual(preflight["schema_version"], 4)
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
                targets=(EvaluationTarget("copilot", "gpt-5.4"),),
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
                runner._run_target(
                    EvaluationTarget("copilot", "gpt-5.4"),
                    ("javascript-app",),
                )

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
                (runner.run_dir / "copilot/gpt-5-4/results.json").read_text()
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
                preflight=False,
                preflight_agents=False,
                preflight_permissions=True,
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
            self.assertEqual(preflight["mode"], "permissions")
            self.assertEqual(
                preflight["permissions"]["results"][0]["model"], None
            )
            self.assertEqual(
                preflight["permissions"]["results"][0]["permission_checks"][0][
                    "permissions"
                ],
                [
                    {
                        "permission": "Microsoft.Sql/servers/read",
                        "status": "PASS",
                    }
                ],
            )


class AgentAdapterTests(unittest.TestCase):
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

    def test_copilot_probe_disables_customizations_and_effective_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "fake-copilot"
            executable.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' "
                f"'{{\"type\":\"assistant.message\",\"content\":\"{AGENT_PREFLIGHT_RESPONSE}\"}}'\n"
                "printf '%s\\n' '{\"type\":\"result\",\"exitCode\":0}'\n"
            )
            executable.chmod(0o755)
            workspace = root / "workspace"
            workspace.mkdir()
            result = CopilotCli(str(executable)).probe(
                AgentRequest(
                    prompt="probe prompt",
                    model="probe-model",
                    workspace=workspace,
                    evidence_dir=root / "evidence",
                    timeout_seconds=60,
                    session_name="probe-session",
                ),
                AGENT_PREFLIGHT_RESPONSE,
            )
            self.assertIn("--available-tools", result.argv)
            self.assertIn("--disable-builtin-mcps", result.argv)
            self.assertIn("--no-custom-instructions", result.argv)

    def _run_fake_claude(self, script: str):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        executable = root / "fake-claude"
        executable.write_text("#!/bin/sh\n" + script, encoding="utf-8")
        executable.chmod(0o755)
        workspace = root / "workspace"
        workspace.mkdir()
        request = AgentRequest(
            prompt="test prompt",
            model="test-model",
            workspace=workspace,
            evidence_dir=root / "evidence",
            timeout_seconds=60,
            session_name="test-session",
        )
        return ClaudeCli(str(executable)).run(request), executable, workspace

    def test_claude_adapter_builds_exact_command(self) -> None:
        result, executable, workspace = self._run_fake_claude(
            "printf '%s\\n' '{\"type\":\"result\",\"is_error\":false}'\n"
        )
        self.assertEqual(
            result.argv,
            [
                str(executable),
                "-p",
                "test prompt",
                "--model",
                "test-model",
                "--name",
                "test-session",
                "--output-format",
                "stream-json",
                "--verbose",
                "--permission-mode",
                "bypassPermissions",
                "--permission-prompts",
                "none",
                "--safe-mode",
                "--strict-mcp-config",
                "--no-session-persistence",
                "--no-chrome",
            ],
        )
        metadata = json.loads(next(result.stdout_path.parent.glob("*-claude.json")).read_text())
        self.assertEqual(metadata["cwd"], str(workspace))

    def test_claude_probe_uses_dontask_and_no_tools(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        executable = root / "fake-claude"
        executable.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' "
            f"'{{\"type\":\"result\",\"is_error\":false,\"result\":\"{AGENT_PREFLIGHT_RESPONSE}\"}}'\n"
        )
        executable.chmod(0o755)
        workspace = root / "workspace"
        workspace.mkdir()
        result = ClaudeCli(str(executable)).probe(
            AgentRequest(
                prompt="probe prompt",
                model="probe-model",
                workspace=workspace,
                evidence_dir=root / "evidence",
                timeout_seconds=60,
                session_name="probe-session",
            ),
            AGENT_PREFLIGHT_RESPONSE,
        )
        permission_index = result.argv.index("--permission-mode")
        tools_index = result.argv.index("--tools")
        self.assertEqual(result.argv[permission_index + 1], "dontAsk")
        self.assertEqual(result.argv[tools_index + 1], "")
        self.assertIn("--safe-mode", result.argv)
        self.assertIn("--strict-mcp-config", result.argv)

    def test_claude_adapter_accepts_final_result_after_malformed_record(self) -> None:
        result, _, _ = self._run_fake_claude(
            "printf '%s\\n' '{not-json}'\n"
            "printf '%s\\n' '{\"type\":\"result\",\"is_error\":false}'\n"
        )
        self.assertTrue(result.succeeded)

    def test_claude_adapter_ignores_scalar_list_and_null_records(self) -> None:
        result, _, _ = self._run_fake_claude(
            "printf '%s\\n' '42' '[\"intermediate\"]' 'null'\n"
            "printf '%s\\n' '{\"type\":\"result\",\"is_error\":false}'\n"
        )
        self.assertTrue(result.succeeded)

    def test_claude_adapter_rejects_missing_final_result(self) -> None:
        with self.assertRaisesRegex(CommandError, "no final result"):
            self._run_fake_claude(
                "printf '%s\\n' '{\"type\":\"assistant\"}'\n"
            )

    def test_claude_adapter_rejects_error_final_result(self) -> None:
        with self.assertRaisesRegex(CommandError, "session failed"):
            self._run_fake_claude(
                "printf '%s\\n' '{\"type\":\"result\",\"is_error\":true}'\n"
            )

    def test_claude_adapter_rejects_missing_is_error(self) -> None:
        with self.assertRaisesRegex(CommandError, "session failed"):
            self._run_fake_claude(
                "printf '%s\\n' '{\"type\":\"result\"}'\n"
            )

    def test_claude_adapter_rejects_non_boolean_is_error(self) -> None:
        with self.assertRaisesRegex(CommandError, "session failed"):
            self._run_fake_claude(
                "printf '%s\\n' '{\"type\":\"result\",\"is_error\":0}'\n"
            )

    def test_claude_adapter_rejects_nonzero_process(self) -> None:
        with self.assertRaises(CommandError) as raised:
            self._run_fake_claude(
                "printf '%s\\n' '{\"type\":\"result\",\"is_error\":false}'\n"
                "exit 2\n"
            )
        self.assertEqual(raised.exception.result.returncode, 2)

    def test_claude_adapter_rejects_missing_executable(self) -> None:
        request = AgentRequest(
            prompt="test",
            model="model",
            workspace=Path.cwd(),
            evidence_dir=Path.cwd(),
            timeout_seconds=60,
            session_name="session",
        )
        with self.assertRaisesRegex(CommandError, "not installed"):
            ClaudeCli("definitely-missing-claude-executable").run(request)

    def _run_fake_codex(self, script: str, *, probe: bool = False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        executable = root / "fake-codex"
        executable.write_text("#!/bin/sh\n" + script, encoding="utf-8")
        executable.chmod(0o755)
        workspace = root / "workspace"
        workspace.mkdir()
        request = AgentRequest(
            prompt="test prompt",
            model="test-model",
            workspace=workspace,
            evidence_dir=root / "evidence",
            timeout_seconds=60,
            session_name="test-session",
        )
        adapter = CodexCli(str(executable))
        result = (
            adapter.probe(request, AGENT_PREFLIGHT_RESPONSE)
            if probe
            else adapter.run(request)
        )
        return result, executable, workspace

    def test_codex_adapter_builds_exact_actual_command(self) -> None:
        result, executable, workspace = self._run_fake_codex(
            "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n"
        )
        self.assertEqual(
            result.argv,
            [
                str(executable),
                "exec",
                "--json",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--config",
                'approval_policy="never"',
                "--config",
                "sandbox_workspace_write.network_access=true",
                "--model",
                "test-model",
                "--cd",
                str(workspace),
                "--sandbox",
                "workspace-write",
                "test prompt",
            ],
        )

    def test_codex_adapter_builds_exact_read_only_probe_command(self) -> None:
        result, executable, workspace = self._run_fake_codex(
            "printf '%s\\n' "
            f"'{{\"type\":\"item.completed\",\"item\":{{\"type\":\"agent_message\","
            f"\"text\":\"{AGENT_PREFLIGHT_RESPONSE}\"}}}}'\n"
            "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n",
            probe=True,
        )
        self.assertEqual(
            result.argv,
            [
                str(executable),
                "exec",
                "--json",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--config",
                'approval_policy="never"',
                "--model",
                "test-model",
                "--cd",
                str(workspace),
                "--sandbox",
                "read-only",
                "test prompt",
            ],
        )

    def test_codex_adapter_ignores_malformed_and_nonmapping_intermediates(self) -> None:
        result, _, _ = self._run_fake_codex(
            "printf '%s\\n' '{not-json}' '42' '[\"event\"]' 'null'\n"
            "printf '%s\\n' '{\"type\":\"item.completed\"}'\n"
            "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n"
        )
        self.assertTrue(result.succeeded)

    def test_codex_probe_rejects_unexpected_response(self) -> None:
        with self.assertRaisesRegex(CommandError, "unexpected response"):
            self._run_fake_codex(
                "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n",
                probe=True,
            )

    def test_codex_probe_rejects_marker_in_command_output(self) -> None:
        with self.assertRaisesRegex(CommandError, "used a tool"):
            self._run_fake_codex(
                "printf '%s\\n' "
                f"'{{\"type\":\"item.completed\",\"item\":"
                f"{{\"type\":\"command_execution\",\"aggregated_output\":"
                f"\"{AGENT_PREFLIGHT_RESPONSE}\"}}}}'\n"
                "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n",
                probe=True,
            )

    def test_codex_probe_rejects_tool_before_valid_agent_message(self) -> None:
        with self.assertRaisesRegex(CommandError, "used a tool"):
            self._run_fake_codex(
                "printf '%s\\n' "
                "'{\"type\":\"item.started\",\"item\":"
                "{\"type\":\"mcp_tool_call\",\"server\":\"test\",\"tool\":\"echo\"}}'\n"
                "printf '%s\\n' "
                f"'{{\"type\":\"item.completed\",\"item\":{{\"type\":\"agent_message\","
                f"\"text\":\"{AGENT_PREFLIGHT_RESPONSE}\"}}}}'\n"
                "printf '%s\\n' '{\"type\":\"turn.completed\"}'\n",
                probe=True,
            )

    def test_codex_adapter_rejects_failure_terminal_and_process_cases(self) -> None:
        cases = (
            (
                "printf '%s\\n' '{\"type\":\"item.completed\"}'\n",
                "no terminal turn.completed",
            ),
            (
                "printf '%s\\n' '{\"type\":\"turn.failed\"}'\n",
                "session failed",
            ),
            (
                "printf '%s\\n' '{\"type\":\"error\"}'\n",
                "session failed",
            ),
            (
                "printf '%s\\n' '{\"type\":\"turn.completed\"}'\nexit 2\n",
                "session failed",
            ),
        )
        for script, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(CommandError, message):
                    self._run_fake_codex(script)

    def test_codex_adapter_rejects_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stdout = root / "stdout"
            stderr = root / "stderr"
            stdout.write_text('{"type":"turn.completed"}\n')
            stderr.write_text("")
            result = CommandResult(
                argv=["codex"],
                returncode=-15,
                duration_seconds=1,
                stdout_path=stdout,
                stderr_path=stderr,
                timed_out=True,
            )
            with self.assertRaisesRegex(CommandError, "session failed"):
                CodexCli._validate_jsonl(result)

    def test_agent_factory_resolves_all_harnesses(self) -> None:
        self.assertIsInstance(create_agent("copilot"), CopilotCli)
        self.assertIsInstance(create_agent("claude"), ClaudeCli)
        self.assertIsInstance(create_agent("codex"), CodexCli)
        with self.assertRaisesRegex(ValueError, "unsupported agent"):
            create_agent("unknown")

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


class MatrixConfigurationTests(unittest.TestCase):
    """Verify strict versioned YAML matrix loading."""

    VALID = """\
schema_version: 1
scenarios: [javascript-app, rag-app]
agent_timeout_seconds: 2700
validation_timeout_seconds: 900
keep_workspaces: false
harnesses:
  - name: copilot
    models: [gpt-5.4, claude-sonnet-5]
  - name: claude
    models: [claude-sonnet-5]
"""

    def _load(self, content: str):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "configuration.yml"
            path.write_text(content, encoding="utf-8")
            return load_test_matrix(path)

    def test_valid_matrix_expands_targets_in_declaration_order(self) -> None:
        matrix = self._load(self.VALID)
        self.assertEqual(
            [(target.harness, target.model) for target in matrix.targets],
            [
                ("copilot", "gpt-5.4"),
                ("copilot", "claude-sonnet-5"),
                ("claude", "claude-sonnet-5"),
            ],
        )
        self.assertEqual(matrix.scenarios, ("javascript-app", "rag-app"))
        self.assertFalse(matrix.keep_workspaces)

    def test_codex_is_supported_and_example_uses_documented_model(self) -> None:
        matrix = self._load(
            self.VALID
            + "  - name: codex\n"
            + "    models: [gpt-6-sol]\n"
        )
        self.assertEqual(matrix.targets[-1], EvaluationTarget("codex", "gpt-6-sol"))
        example = load_test_matrix(
            Path(__file__).resolve().parents[1] / "configuration.EXAMPLE.yml"
        )
        self.assertIn(EvaluationTarget("codex", "gpt-6-sol"), example.targets)

    def test_rejects_unknown_and_missing_properties(self) -> None:
        for content, message in (
            (self.VALID + "unexpected: true\n", "unknown property"),
            (self.VALID.replace("keep_workspaces: false\n", ""), "missing property"),
            (self.VALID.replace("    models:", "    extra: true\n    models:", 1), "unknown property"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ConfigurationError, message):
                    self._load(content)

    def test_rejects_duplicate_root_mapping_key_before_validation(self) -> None:
        content = self.VALID.replace(
            "schema_version: 1",
            "schema_version: 1\nschema_version: 2",
        )
        with self.assertRaises(ConfigurationError) as raised:
            self._load(content)
        self.assertRegex(
            str(raised.exception),
            r"configuration\.yml: root duplicate property 'schema_version'",
        )

    def test_rejects_duplicate_harness_mapping_key_before_validation(self) -> None:
        content = self.VALID.replace(
            "  - name: copilot",
            "  - name: copilot\n    name: unknown",
        )
        with self.assertRaises(ConfigurationError) as raised:
            self._load(content)
        self.assertRegex(
            str(raised.exception),
            r"configuration\.yml: harnesses\[0\] duplicate property 'name'",
        )

    def test_rejects_unsupported_version_and_inexact_types(self) -> None:
        cases = (
            (self.VALID.replace("schema_version: 1", "schema_version: 2"), "schema_version"),
            (self.VALID.replace("agent_timeout_seconds: 2700", "agent_timeout_seconds: true"), "agent_timeout"),
            (self.VALID.replace("keep_workspaces: false", "keep_workspaces: 0"), "keep_workspaces"),
            (self.VALID.replace("name: copilot", "name: ' '"), "non-blank"),
        )
        for content, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ConfigurationError, message):
                    self._load(content)

    def test_rejects_empty_lists_and_duplicates(self) -> None:
        cases = (
            (self.VALID.replace("scenarios: [javascript-app, rag-app]", "scenarios: []"), "non-empty"),
            (
                self.VALID.replace(
                    """harnesses:
  - name: copilot
    models: [gpt-5.4, claude-sonnet-5]
  - name: claude
    models: [claude-sonnet-5]
""",
                    "harnesses: []\n",
                ),
                "non-empty",
            ),
            (self.VALID.replace("[javascript-app, rag-app]", "[javascript-app, javascript-app]"), "duplicate"),
            (self.VALID.replace("[gpt-5.4, claude-sonnet-5]", "[gpt-5.4, gpt-5.4]"), "duplicate"),
            (self.VALID.replace("  - name: claude\n", "  - name: copilot\n"), "duplicate harness"),
        )
        for content, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ConfigurationError, message):
                    self._load(content)

    def test_rejects_unknown_scenario_and_harness(self) -> None:
        for content, message in (
            (self.VALID.replace("rag-app", "unknown-scenario", 1), "unknown scenario"),
            (self.VALID.replace("name: claude", "name: unknown"), "unsupported harness"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ConfigurationError, message):
                    self._load(content)

    def test_rejects_short_timeouts(self) -> None:
        for content, message in (
            (self.VALID.replace("2700", "59"), "at least 60"),
            (self.VALID.replace("900", "29"), "at least 30"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ConfigurationError, message):
                    self._load(content)

    def test_rejects_normalized_model_slug_collision(self) -> None:
        content = self.VALID.replace(
            "[gpt-5.4, claude-sonnet-5]",
            "['same model', 'same-model']",
        )
        with self.assertRaisesRegex(ConfigurationError, "slug collision"):
            self._load(content)


class CommandLineTests(unittest.TestCase):
    """Verify direct-target and YAML configuration CLI resolution."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env_file = self.root / "validation.env"
        self.env_file.write_text(
            """\
HUB_EVAL_AZURE_TENANT_ID=tenant
HUB_EVAL_AZURE_SUBSCRIPTION_ID=subscription
HUB_EVAL_AZURE_LOCATION=test-region
HUB_EVAL_EMBEDDING_LOCATION=embedding-region
""",
            encoding="utf-8",
        )
        self.configuration = self.root / "configuration.yml"
        self.configuration.write_text(MatrixConfigurationTests.VALID, encoding="utf-8")

    def _parse(self, *arguments: str) -> argparse.Namespace:
        return parse_args(["--env-file", str(self.env_file), *arguments])

    def test_default_resolves_copilot_target(self) -> None:
        args = self._parse()
        self.assertEqual(
            args.targets, (EvaluationTarget("copilot", "gpt-5.4"),)
        )
        self.assertEqual(args.agent_timeout_seconds, 2700)
        self.assertFalse(args.keep_workspaces)

    def test_direct_claude_target_resolves(self) -> None:
        args = self._parse("--target", "claude:claude-sonnet-5")
        self.assertEqual(
            args.targets, (EvaluationTarget("claude", "claude-sonnet-5"),)
        )

    def test_repeatable_targets_preserve_order(self) -> None:
        args = self._parse(
            "--target",
            "copilot:gpt-5.4",
            "--target",
            "copilot:claude-sonnet-5",
            "--target",
            "claude:claude-sonnet-5",
        )
        self.assertEqual(
            args.targets,
            (
                EvaluationTarget("copilot", "gpt-5.4"),
                EvaluationTarget("copilot", "claude-sonnet-5"),
                EvaluationTarget("claude", "claude-sonnet-5"),
            ),
        )

    def test_configuration_expands_targets_and_uses_yaml_settings(self) -> None:
        args = self._parse("--configuration", str(self.configuration))
        self.assertEqual(len(args.targets), 3)
        self.assertEqual(args.scenarios, ("javascript-app", "rag-app"))
        self.assertEqual(args.agent_timeout_seconds, 2700)
        self.assertEqual(args.validation_timeout_seconds, 900)
        self.assertFalse(args.keep_workspaces)

    def test_configuration_cli_values_replace_yaml_values(self) -> None:
        args = self._parse(
            "--configuration",
            str(self.configuration),
            "--scenario",
            "python-api",
            "--scenario",
            "multi-tenant",
            "--agent-timeout-seconds",
            "3600",
            "--validation-timeout-seconds",
            "1200",
            "--keep-workspaces",
        )
        self.assertEqual(args.scenarios, ("python-api", "multi-tenant"))
        self.assertEqual(args.agent_timeout_seconds, 3600)
        self.assertEqual(args.validation_timeout_seconds, 1200)
        self.assertTrue(args.keep_workspaces)
        args = self._parse(
            "--configuration",
            str(self.configuration),
            "--no-keep-workspaces",
        )
        self.assertFalse(args.keep_workspaces)

    def test_rejects_malformed_duplicate_and_colliding_targets(self) -> None:
        cases = (
            ("--target", "claude"),
            ("--target", "unknown:model"),
            ("--target", "copilot:model", "--target", "copilot:model"),
            (
                "--target",
                "copilot:same model",
                "--target",
                "copilot:same-model",
            ),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(SystemExit):
                    self._parse(*arguments)

    def test_target_and_configuration_are_mutually_exclusive(self) -> None:
        with self.assertRaises(SystemExit):
            self._parse(
                "--target",
                "copilot:gpt-5.4",
                "--configuration",
                str(self.configuration),
            )

    def test_removed_agent_and_model_flags_are_unrecognized(self) -> None:
        for arguments in (("--agent", "copilot"), ("--model", "gpt-5.4")):
            with self.subTest(arguments=arguments):
                with self.assertRaises(SystemExit):
                    self._parse(*arguments)

    def test_dry_run_prints_resolved_plan_without_constructing_agent(self) -> None:
        args = self._parse(
            "--configuration", str(self.configuration), "--dry-run"
        )
        output = io.StringIO()
        with (
            patch("run_evals.parse_args", return_value=args),
            patch("hub_eval.runner.create_agent") as create_agent_mock,
            patch("sys.stdout", output),
        ):
            self.assertEqual(main(), 0)
        create_agent_mock.assert_not_called()
        plan = json.loads(output.getvalue())
        self.assertEqual(plan["targets"][2]["harness"], "claude")
        self.assertEqual(plan["agent_timeout_seconds"], 2700)
        self.assertFalse(plan["keep_workspaces"])

    def test_preflight_resolution_does_not_construct_agent(self) -> None:
        args = self._parse(
            "--configuration", str(self.configuration), "--preflight"
        )
        with (
            patch("run_evals.parse_args", return_value=args),
            patch("run_evals.run_preflight", return_value=0) as preflight,
        ):
            self.assertEqual(main(), 0)
        preflight.assert_called_once()

    def test_list_models_needs_neither_env_nor_executable(self) -> None:
        missing = self.root / "missing.env"
        args = parse_args(
            ["--env-file", str(missing), "--list-models", "codex"]
        )
        output = io.StringIO()
        with (
            patch("run_evals.parse_args", return_value=args),
            patch("run_evals.create_agent") as create_agent_mock,
            patch("sys.stdout", output),
        ):
            self.assertEqual(main(), 0)
        create_agent_mock.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(result["harness"], "codex")
        self.assertIn("gpt-6-sol", result["models"])
        self.assertEqual(tuple(result["models"]), documented_models("codex"))

    def test_agents_preflight_resolves_targets_without_azure_env(self) -> None:
        args = parse_args(
            [
                "--env-file",
                str(self.root / "missing.env"),
                "--configuration",
                str(self.configuration),
                "--preflight:agents",
            ]
        )
        self.assertTrue(args.preflight_agents)
        self.assertEqual(len(args.targets), 3)
        self.assertIsNone(args.subscription)

    def test_azure_operations_require_validation_env(self) -> None:
        missing = str(self.root / "missing.env")
        cases = (
            (),
            ("--cleanup-only", "hub-eval-test"),
            ("--preflight:permissions",),
            ("--preflight",),
        )
        for operation in cases:
            with self.subTest(operation=operation):
                with self.assertRaises(SystemExit):
                    parse_args(["--env-file", missing, *operation])

    def test_preflight_modes_are_mutually_exclusive_with_operations(self) -> None:
        operations = (
            "--dry-run",
            "--preflight:permissions",
            "--preflight",
            "--cleanup-only",
            "--list-models",
        )
        for operation in operations:
            arguments = ["--preflight:agents", operation]
            if operation == "--cleanup-only":
                arguments.append("group")
            elif operation == "--list-models":
                arguments.append("copilot")
            with self.subTest(operation=operation):
                with self.assertRaises(SystemExit):
                    self._parse(*arguments)


class StandalonePreflightTests(unittest.TestCase):
    """Verify split standalone preflight execution and reporting."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _args(self, **overrides) -> argparse.Namespace:
        values = {
            "output": self.root / "runs",
            "preflight": False,
            "preflight_agents": True,
            "preflight_permissions": False,
            "targets": (
                EvaluationTarget("copilot", "gpt-5.4"),
                EvaluationTarget("claude", "claude-sonnet-5"),
                EvaluationTarget("codex", "gpt-6-sol"),
            ),
            "agent_timeout_seconds": 60,
            "tenant": "tenant",
            "subscription": "subscription",
            "location": "region",
            "embedding_location": "embedding-region",
            "embedding_endpoint": None,
            "embedding_deployment": None,
            "embedding_dimension": None,
            "existing_resource_group": None,
            "existing_server": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def _successful_command(self) -> CommandResult:
        evidence = self.root / "command"
        evidence.mkdir(exist_ok=True)
        stdout = evidence / "001-probe.stdout.txt"
        stderr = evidence / "001-probe.stderr.txt"
        metadata = evidence / "001-probe.json"
        stdout.write_text(AGENT_PREFLIGHT_RESPONSE)
        stderr.write_text("")
        metadata.write_text("{}")
        return CommandResult(
            argv=["fake"],
            returncode=0,
            duration_seconds=0.1,
            stdout_path=stdout,
            stderr_path=stderr,
        )

    def test_agents_only_probes_every_target_continues_and_reports_failure(
        self,
    ) -> None:
        success = self._successful_command()
        missing = Mock()
        missing.probe.side_effect = CommandError("copilot is not installed")
        passing = Mock()
        passing.probe.return_value = success
        denied = Mock()
        denied.probe.side_effect = CommandError("Codex session failed", success)
        args = self._args()
        with (
            patch(
                "run_evals.create_agent",
                side_effect=[missing, passing, denied],
            ) as factory,
            patch("run_evals.create_run_id", return_value="agents-run"),
            patch("builtins.print"),
        ):
            exit_code = run_preflight(args, ("javascript-app",))
        self.assertEqual(exit_code, 1)
        self.assertEqual(factory.call_count, 3)
        report = json.loads(
            (self.root / "runs/agents-run/preflight.json").read_text()
        )
        self.assertEqual(report["mode"], "agents")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            [result["status"] for result in report["agents"]["results"]],
            ["FAIL", "PASS", "FAIL"],
        )
        self.assertIn(
            "not installed",
            report["agents"]["results"][0]["reason"],
        )
        self.assertEqual(len(report["agents"]["results"][1]["evidence"]), 3)
        self.assertIsNone(report["permissions"])

    def test_permissions_only_never_constructs_an_agent(self) -> None:
        args = self._args(
            preflight_agents=False,
            preflight_permissions=True,
        )
        environment = Mock()
        environment.preflight.return_value = {
            "displayName": "Test User",
            "id": "object-id",
        }
        environment.resource_group = "group"
        environment.permission_checks = []
        with (
            patch("run_evals.AzureEnvironment", return_value=environment),
            patch("run_evals.create_agent") as factory,
            patch("run_evals.create_run_id", return_value="permissions-run"),
            patch("builtins.print"),
        ):
            self.assertEqual(run_preflight(args, ("javascript-app",)), 0)
        factory.assert_not_called()
        report = json.loads(
            (self.root / "runs/permissions-run/preflight.json").read_text()
        )
        self.assertEqual(report["mode"], "permissions")
        self.assertIsNone(report["agents"])
        self.assertEqual(report["permissions"]["schema_version"], 4)

    def test_combined_aggregates_exit_in_one_directory(self) -> None:
        args = self._args(
            preflight=True,
            preflight_agents=False,
        )
        agent_result = AgentPreflightResult(
            harness="copilot",
            model="gpt-5.4",
            status="FAIL",
            duration_seconds=0.1,
            reason="model unavailable",
            evidence=(),
        )
        permission_result = PreflightResult(
            harness=None,
            model=None,
            status="PASS",
            duration_seconds=0.1,
            subscription_id="subscription",
            resource_group="group",
            scenarios=["javascript-app"],
            identity={"display_name": "User", "object_id": "id"},
            permission_checks=[],
            reason="validated",
        )
        with (
            patch(
                "run_evals.run_agent_preflight",
                return_value=[agent_result],
            ) as agents,
            patch(
                "run_evals.run_permission_preflight",
                return_value=permission_result,
            ) as permissions,
            patch("run_evals.create_run_id", return_value="combined-run"),
            patch("builtins.print"),
        ):
            self.assertEqual(run_preflight(args, ("javascript-app",)), 1)
        self.assertEqual(
            agents.call_args.args[2],
            permissions.call_args.args[2],
        )
        self.assertEqual(
            [path.name for path in (self.root / "runs").iterdir()],
            ["combined-run"],
        )
        report = json.loads(
            (self.root / "runs/combined-run/preflight.json").read_text()
        )
        self.assertEqual(report["mode"], "combined")
        self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
