"""Disposable Azure resource provisioning through the authenticated Azure CLI."""

from __future__ import annotations

import json
import re
import shutil
import ssl
import subprocess
import time
from datetime import UTC, datetime, timedelta
from fnmatch import fnmatchcase
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from .command import CommandError, CommandRunner
from .database import DatabaseProbe
from .models import AzureResources, PermissionCheck, PermissionResult
from .progress import ProgressReporter

# Windows ships az.cmd, not az.exe; CreateProcess only appends .exe.
_AZ = shutil.which("az") or "az"

PURPOSE_TAG = "azure-sql-dev-hub-prompt-eval"
PUBLIC_AZURE_CLOUD = "AzureCloud"
AUTHORIZATION_API_VERSION = "2022-04-01"
AZURE_OPENAI_API_VERSION = "2024-10-21"
AZURE_SQL_DATABASE_MANAGER_PERMISSION = (
    "Connect to virtual master as a ##MS_DatabaseManager## member"
)
AZURE_OPENAI_EMBEDDINGS_PERMISSION = (
    "Microsoft.CognitiveServices/accounts/OpenAI/deployments/embeddings/action"
)

RESOURCE_GROUP_PERMISSIONS = (
    "Microsoft.Resources/subscriptions/resourceGroups/read",
)
EXISTING_SQL_PERMISSIONS = (
    "Microsoft.Sql/servers/read",
    "Microsoft.Sql/servers/databases/read",
    "Microsoft.Sql/servers/databases/delete",
    "Microsoft.Sql/servers/firewallRules/write",
    "Microsoft.Sql/servers/firewallRules/delete",
)
DISPOSABLE_SQL_PERMISSIONS = (
    "Microsoft.Resources/subscriptions/resourceGroups/write",
    "Microsoft.Resources/subscriptions/resourceGroups/delete",
    "Microsoft.Sql/servers/read",
    "Microsoft.Sql/servers/write",
    "Microsoft.Sql/servers/administrators/write",
    "Microsoft.Sql/servers/databases/read",
    "Microsoft.Sql/servers/databases/write",
    "Microsoft.Sql/servers/firewallRules/write",
)
EMBEDDING_PERMISSIONS = (
    "Microsoft.CognitiveServices/accounts/read",
    "Microsoft.CognitiveServices/accounts/write",
    "Microsoft.CognitiveServices/accounts/delete",
    "Microsoft.CognitiveServices/accounts/deployments/write",
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete",
    "Microsoft.Authorization/roleDefinitions/read",
)
EMBEDDING_PURGE_PERMISSIONS = (
    "Microsoft.CognitiveServices/locations/resourceGroups/deletedAccounts/read",
    "Microsoft.CognitiveServices/locations/resourceGroups/deletedAccounts/delete",
)


def missing_permissions(
    required_actions: tuple[str, ...],
    permission_sets: list[dict],
) -> list[str]:
    """Return required ARM actions not granted by any effective permission set."""

    def matches(action: str, patterns) -> bool:
        return any(
            isinstance(pattern, str)
            and fnmatchcase(action.casefold(), pattern.casefold())
            for pattern in patterns
        )

    missing = []
    for action in required_actions:
        allowed = any(
            matches(action, permission.get("actions") or ())
            and not matches(action, permission.get("notActions") or ())
            for permission in permission_sets
            if isinstance(permission, dict)
        )
        if not allowed:
            missing.append(action)
    return missing


class AzureCli:
    """Typed JSON wrapper around the locally authenticated `az` command."""

    def __init__(
        self,
        runner: CommandRunner,
        *,
        tenant_id: str,
        subscription_id: str,
    ):
        self.runner = runner
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id

    def json(
        self,
        args: list[str],
        *,
        label: str,
        timeout: int = 600,
        check: bool = True,
    ):
        """Run an Azure CLI command and decode its JSON output."""
        result = self.runner.run(
            [_AZ, *args, "--only-show-errors", "--output", "json"],
            timeout=timeout,
            label=label,
            check=check,
        )
        if not result.succeeded:
            return None
        try:
            return json.loads(result.stdout_path.read_text(encoding="utf-8") or "null")
        except json.JSONDecodeError as exc:
            raise CommandError(f"{label} returned invalid JSON", result) from exc

    def text(
        self,
        args: list[str],
        *,
        label: str,
        timeout: int = 600,
        check: bool = True,
    ) -> str:
        """Run an Azure CLI command and return trimmed text output."""
        result = self.runner.run(
            [_AZ, *args, "--only-show-errors", "--output", "tsv"],
            timeout=timeout,
            label=label,
            check=check,
        )
        return result.stdout_path.read_text(encoding="utf-8").strip()

    def verify_context(self) -> dict:
        """Select and verify the exact authorized subscription."""
        self.runner.run(
            [_AZ, "cloud", "set", "--name", PUBLIC_AZURE_CLOUD],
            label="az-cloud-set",
            check=True,
        )
        self.runner.run(
            [_AZ, "account", "set", "--subscription", self.subscription_id],
            label="az-account-set",
            check=True,
        )
        account = self.json(["account", "show"], label="az-account-show")
        if account["id"] != self.subscription_id or account["state"] != "Enabled":
            raise CommandError("Azure CLI is not using the required enabled subscription")
        if account.get("tenantId") != self.tenant_id:
            raise CommandError("Azure CLI account tenant does not match validation.env")
        if account.get("user", {}).get("type") != "user":
            raise CommandError("an interactive user identity is required for Entra SQL admin")
        return account


class AzureEnvironment:
    """Own one resource group and delete it synchronously at the end of a run."""

    def __init__(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        location: str,
        evidence_dir: Path,
        embedding_location: str,
        provision_embedding: bool,
        existing_embedding_endpoint: str | None = None,
        existing_embedding_deployment: str | None = None,
        existing_embedding_dimension: int | None = None,
        existing_resource_group: str | None = None,
        existing_server: str | None = None,
        reporter: ProgressReporter | None = None,
    ):
        suffix = uuid4().hex[:10]
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.location = location
        self.evidence_dir = evidence_dir
        self.embedding_location = embedding_location
        self.provision_embedding = provision_embedding
        self.existing_embedding_endpoint = existing_embedding_endpoint
        self.existing_embedding_deployment = existing_embedding_deployment
        self.existing_embedding_dimension = existing_embedding_dimension
        if bool(existing_resource_group) != bool(existing_server):
            raise ValueError(
                "existing resource group and existing server must be supplied together"
            )
        self.existing_resource_group = existing_resource_group
        self.existing_server = existing_server
        self.resource_group = existing_resource_group or f"rg-sqlhub-eval-{suffix}"
        self.server_name = existing_server or f"sqlhub-eval-{suffix}"
        self.database_name = f"hub_prompt_eval_{suffix}"
        self.firewall_rule_name = f"evaluation-client-{suffix}"
        self.reporter = reporter
        self.runner = CommandRunner(evidence_dir / "azure", reporter=reporter)
        self.az = AzureCli(
            self.runner,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
        )
        self.group_created = False
        self.server_created = False
        self.database_created = False
        self.firewall_created = False
        self.embedding_account_name: str | None = None
        self.embedding_deployment_name: str | None = None
        self.embedding_role_assignment_id: str | None = None
        self.resources: AzureResources | None = None
        self.permission_checks: list[PermissionCheck] = []

    def create(self, identity: dict | None = None) -> AzureResources:
        """Create a logical server, Basic database, firewall rule, and optional embedding model."""
        if identity is None:
            identity = self.preflight()
        display_name = identity["displayName"]
        object_id = identity["id"]
        if self.existing_resource_group:
            server = self.az.json(
                [
                    "sql",
                    "server",
                    "show",
                    "--resource-group",
                    self.resource_group,
                    "--name",
                    self.server_name,
                ],
                label="az-sql-server-show",
            )
            if (
                server.get("state") != "Ready"
                or server.get("publicNetworkAccess") != "Enabled"
            ):
                raise CommandError("existing SQL server is not ready for public access")
        else:
            expires_at = datetime.now(UTC) + timedelta(hours=12)
            self.az.json(
                [
                    "group",
                    "create",
                    "--name",
                    self.resource_group,
                    "--location",
                    self.location,
                    "--tags",
                    f"purpose={PURPOSE_TAG}",
                    f"expiresAt={expires_at.strftime('%Y%m%dT%H%M%SZ')}",
                ],
                label="az-group-create",
            )
            self.group_created = True
            self.az.json(
                [
                    "sql",
                    "server",
                    "create",
                    "--resource-group",
                    self.resource_group,
                    "--name",
                    self.server_name,
                    "--location",
                    self.location,
                    "--enable-ad-only-auth",
                    "--external-admin-principal-type",
                    "User",
                    "--external-admin-name",
                    display_name,
                    "--external-admin-sid",
                    object_id,
                    "--enable-public-network",
                    "true",
                ],
                label="az-sql-server-create",
                timeout=1200,
            )
            self.server_created = True
        public_ip = self._public_ip()
        self.az.json(
            [
                "sql",
                "server",
                "firewall-rule",
                "create",
                "--resource-group",
                self.resource_group,
                "--server",
                self.server_name,
                "--name",
                self.firewall_rule_name,
                "--start-ip-address",
                public_ip,
                "--end-ip-address",
                public_ip,
            ],
            label="az-sql-firewall-create",
        )
        self.firewall_created = True
        self._create_database()
        self.database_created = True
        self._wait_for_database()
        endpoint, deployment, dimension = self._embedding(identity)
        self.resources = AzureResources(
            subscription_id=self.subscription_id,
            resource_group=self.resource_group,
            location=self.location,
            server_name=self.server_name,
            database_name=self.database_name,
            server_fqdn=f"{self.server_name}.database.windows.net",
            embedding_endpoint=endpoint,
            embedding_deployment=deployment,
            embedding_dimension=dimension,
        )
        (self.evidence_dir / "resources.json").write_text(
            json.dumps(self.resources.__dict__, indent=2) + "\n",
            encoding="utf-8",
        )
        if self.reporter:
            self.reporter.artifact(
                self.evidence_dir / "resources.json", "Azure resource manifest"
            )
        return self.resources

    def preflight(self) -> dict:
        """Verify Azure context, providers, and effective permissions without writes."""
        self.permission_checks.clear()
        self.az.verify_context()
        identity = self.az.json(
            ["ad", "signed-in-user", "show"],
            label="az-signed-in-user",
        )
        display_name = identity.get("displayName")
        object_id = identity.get("id")
        if not display_name or not object_id:
            raise CommandError("could not resolve the signed-in Entra user")
        self._verify_provider_registrations()
        self._verify_permissions()
        self._verify_data_plane_permissions()
        return identity

    def _required_permissions(self) -> tuple[str, ...]:
        permissions = list(RESOURCE_GROUP_PERMISSIONS)
        if self.existing_resource_group:
            permissions.extend(EXISTING_SQL_PERMISSIONS)
        else:
            permissions.extend(DISPOSABLE_SQL_PERMISSIONS)
        if self.provision_embedding and not self.existing_embedding_endpoint:
            permissions.extend(EMBEDDING_PERMISSIONS)
            if not self.existing_resource_group:
                permissions.extend(EMBEDDING_PURGE_PERMISSIONS)
        return tuple(dict.fromkeys(permissions))

    def _verify_provider_registrations(self) -> None:
        namespaces = ["Microsoft.Sql"]
        if self.provision_embedding and not self.existing_embedding_endpoint:
            namespaces.append("Microsoft.CognitiveServices")
        unregistered = []
        for namespace in namespaces:
            state = self.az.text(
                [
                    "provider",
                    "show",
                    "--namespace",
                    namespace,
                    "--query",
                    "registrationState",
                ],
                label=f"az-provider-{namespace.rsplit('.', 1)[-1].lower()}",
            )
            if state != "Registered":
                unregistered.append(namespace)
        if unregistered:
            commands = "\n".join(
                f"az provider register --namespace {namespace} --wait"
                for namespace in unregistered
            )
            raise CommandError(
                "required Azure resource providers are not registered:\n"
                f"{commands}"
            )

    def _verify_permissions(self) -> None:
        if self.existing_resource_group:
            scope = (
                f"/subscriptions/{self.subscription_id}"
                f"/resourceGroups/{self.resource_group}"
            )
        else:
            scope = f"/subscriptions/{self.subscription_id}"
        self._verify_permissions_at_scope(scope, self._required_permissions())
        if (
            self.existing_resource_group
            and self.provision_embedding
            and not self.existing_embedding_endpoint
        ):
            subscription_scope = f"/subscriptions/{self.subscription_id}"
            self._verify_permissions_at_scope(
                subscription_scope,
                EMBEDDING_PURGE_PERMISSIONS,
            )

    def _verify_data_plane_permissions(self) -> None:
        """Verify existing-resource data-plane access and record every outcome."""
        failures: list[str] = []
        if self.existing_server:
            sql_scope = (
                f"/subscriptions/{self.subscription_id}"
                f"/resourceGroups/{self.resource_group}"
                f"/providers/Microsoft.Sql/servers/{self.server_name}"
            )
            try:
                self._verify_existing_sql_database_manager()
                status = "PASS"
            except CommandError as exc:
                status = "FAIL"
                failures.append(str(exc))
            self.permission_checks.append(
                PermissionCheck(
                    scope=sql_scope,
                    permissions=[
                        PermissionResult(
                            permission=AZURE_SQL_DATABASE_MANAGER_PERMISSION,
                            status=status,
                        )
                    ],
                )
            )

        if self.provision_embedding and self.existing_embedding_endpoint:
            try:
                self._verify_existing_embedding_access()
                status = "PASS"
            except CommandError as exc:
                status = "FAIL"
                failures.append(str(exc))
            self.permission_checks.append(
                PermissionCheck(
                    scope=self.existing_embedding_endpoint,
                    permissions=[
                        PermissionResult(
                            permission=AZURE_OPENAI_EMBEDDINGS_PERMISSION,
                            status=status,
                        )
                    ],
                )
            )

        if failures:
            raise CommandError(
                "data-plane preflight failed:\n- " + "\n- ".join(failures)
            )

    def _verify_existing_sql_database_manager(self) -> None:
        membership = self._database_probe("master").scalar(
            "SELECT IS_SRVROLEMEMBER(N'##MS_DatabaseManager##');",
            attempts=1,
            label="sql-database-manager-role",
        )
        if membership == 1:
            return
        raise CommandError(
            "signed-in user is not a member of ##MS_DatabaseManager## "
            f"on SQL server {self.server_name}"
        )

    def _database_probe(self, database_name: str) -> DatabaseProbe:
        return DatabaseProbe(
            AzureResources(
                subscription_id=self.subscription_id,
                resource_group=self.resource_group,
                location=self.location,
                server_name=self.server_name,
                database_name=database_name,
                server_fqdn=f"{self.server_name}.database.windows.net",
            ),
            reporter=self.reporter,
        )

    def _create_database(self) -> None:
        if self.existing_server:
            self._database_probe("master").execute(
                f"""
                CREATE DATABASE [{self.database_name}]
                (
                    EDITION = 'Basic',
                    SERVICE_OBJECTIVE = 'Basic'
                );
                """,
                label="sql-database-create",
            )
            return
        self.az.json(
            [
                "sql",
                "db",
                "create",
                "--resource-group",
                self.resource_group,
                "--server",
                self.server_name,
                "--name",
                self.database_name,
                "--edition",
                "Basic",
                "--service-objective",
                "Basic",
                "--backup-storage-redundancy",
                "Local",
            ],
            label="az-sql-db-create",
            timeout=1800,
        )

    def _verify_existing_embedding_access(self) -> None:
        if (
            not self.existing_embedding_endpoint
            or not self.existing_embedding_deployment
            or not self.existing_embedding_dimension
        ):
            raise CommandError(
                "existing embedding endpoint requires deployment and dimension"
            )
        access_token = self._azure_openai_access_token()
        deployment = quote(self.existing_embedding_deployment, safe="")
        endpoint = self.existing_embedding_endpoint.rstrip("/")
        url = (
            f"{endpoint}/openai/deployments/{deployment}/embeddings"
            f"?api-version={AZURE_OPENAI_API_VERSION}"
        )
        request = Request(
            url,
            data=json.dumps(
                {"input": "Azure SQL evaluation preflight"}
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(
                request,
                timeout=30,
                context=self._https_context(),
            ) as response:
                content = response.read(1_000_001)
        except HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace").strip()
            raise CommandError(
                "existing Azure OpenAI embedding deployment rejected the "
                f"signed-in user with HTTP {exc.code}"
                + (f": {detail}" if detail else "")
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CommandError(
                "could not reach the existing Azure OpenAI embedding deployment: "
                f"{exc}"
            ) from exc
        if len(content) > 1_000_000:
            raise CommandError(
                "existing Azure OpenAI embedding response exceeded 1 MB"
            )
        try:
            payload = json.loads(content)
            embedding = payload["data"][0]["embedding"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise CommandError(
                "existing Azure OpenAI embedding response had an invalid shape"
            ) from exc
        if not isinstance(embedding, list):
            raise CommandError(
                "existing Azure OpenAI embedding response did not contain a vector"
            )
        if len(embedding) != self.existing_embedding_dimension:
            raise CommandError(
                "existing Azure OpenAI embedding deployment returned "
                f"{len(embedding)} dimensions; expected "
                f"{self.existing_embedding_dimension}"
            )

    def _azure_openai_access_token(self) -> str:
        result = subprocess.run(
            [
                _AZ,
                "account",
                "get-access-token",
                "--resource",
                "https://cognitiveservices.azure.com/",
                "--only-show-errors",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip()
            raise CommandError(
                "could not acquire an Azure OpenAI access token from Azure CLI"
                + (f": {detail}" if detail else "")
            )
        try:
            access_token = json.loads(result.stdout)["accessToken"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CommandError(
                "Azure CLI returned an invalid Azure OpenAI access token response"
            ) from exc
        if not isinstance(access_token, str) or not access_token:
            raise CommandError("Azure CLI returned an empty Azure OpenAI access token")
        return access_token

    @staticmethod
    def _https_context() -> ssl.SSLContext:
        try:
            certificate = distribution("certifi").locate_file(
                "certifi/cacert.pem"
            )
        except PackageNotFoundError:
            certificate = None
        if certificate is not None and certificate.is_file():
            return ssl.create_default_context(cafile=str(certificate))
        return ssl.create_default_context()

    def _verify_permissions_at_scope(
        self,
        scope: str,
        required_permissions: tuple[str, ...],
    ) -> None:
        url = (
            f"https://management.azure.com{scope}"
            "/providers/Microsoft.Authorization/permissions"
            f"?api-version={AUTHORIZATION_API_VERSION}"
        )
        permission_sets: list[dict] = []
        page_number = 1
        while url:
            response = self.az.json(
                ["rest", "--method", "get", "--url", url],
                label=f"az-permissions-{page_number}",
            )
            values = response.get("value") if isinstance(response, dict) else None
            if not isinstance(values, list):
                raise CommandError(
                    "Azure permissions response did not contain a value list"
                )
            permission_sets.extend(values)
            next_link = response.get("nextLink")
            if next_link is not None and not isinstance(next_link, str):
                raise CommandError(
                    "Azure permissions response contained an invalid nextLink"
                )
            url = next_link
            page_number += 1
        missing = missing_permissions(required_permissions, permission_sets)
        missing_set = set(missing)
        self.permission_checks.append(
            PermissionCheck(
                scope=scope,
                permissions=[
                    PermissionResult(
                        permission=permission,
                        status="FAIL" if permission in missing_set else "PASS",
                    )
                    for permission in required_permissions
                ],
            )
        )
        if missing:
            formatted = "\n- ".join(missing)
            raise CommandError(
                f"signed-in user is missing Azure permissions at {scope}:\n- {formatted}"
            )

    def cleanup(self) -> None:
        """Delete every resource created by this environment and verify removal."""
        if not any(
            (
                self.database_created,
                self.firewall_created,
                self.embedding_account_name,
                self.embedding_role_assignment_id,
            )
        ):
            return
        errors = []
        errors.extend(self._cleanup_embedding())
        if self.group_created:
            try:
                self._cleanup_resource_group()
            except CommandError as exc:
                errors.append(str(exc))
            if errors:
                raise CommandError("cleanup incomplete: " + "; ".join(errors))
            return
        if self.database_created:
            result = self.runner.run(
                [
                    "az",
                    "sql",
                    "db",
                    "delete",
                    "--resource-group",
                    self.resource_group,
                    "--server",
                    self.server_name,
                    "--name",
                    self.database_name,
                    "--yes",
                    "--only-show-errors",
                ],
                timeout=1800,
                label="az-sql-db-delete",
            )
            if not result.succeeded:
                errors.append("SQL database")
            else:
                self.database_created = False
        if self.firewall_created:
            result = self.runner.run(
                [
                    "az",
                    "sql",
                    "server",
                    "firewall-rule",
                    "delete",
                    "--resource-group",
                    self.resource_group,
                    "--server",
                    self.server_name,
                    "--name",
                    self.firewall_rule_name,
                    "--only-show-errors",
                ],
                timeout=600,
                label="az-sql-firewall-delete",
            )
            if not result.succeeded:
                errors.append("SQL firewall rule")
            else:
                self.firewall_created = False
        if errors:
            raise CommandError("failed to delete created " + ", ".join(errors))

    def _cleanup_embedding(self) -> list[str]:
        errors = []
        if self.embedding_role_assignment_id:
            result = self.runner.run(
                [
                    "az",
                    "role",
                    "assignment",
                    "delete",
                    "--ids",
                    self.embedding_role_assignment_id,
                    "--only-show-errors",
                ],
                timeout=600,
                label="az-openai-role-delete",
            )
            if not result.succeeded:
                errors.append("embedding role assignment")
            else:
                self.embedding_role_assignment_id = None
        if self.embedding_account_name:
            account_name = self.embedding_account_name
            result = self.runner.run(
                [
                    "az",
                    "cognitiveservices",
                    "account",
                    "delete",
                    "--resource-group",
                    self.resource_group,
                    "--name",
                    account_name,
                    "--only-show-errors",
                ],
                timeout=1200,
                label="az-openai-delete",
            )
            if not result.succeeded:
                errors.append("embedding account")
            else:
                purge = self.runner.run(
                    [
                        "az",
                        "cognitiveservices",
                        "account",
                        "purge",
                        "--resource-group",
                        self.resource_group,
                        "--name",
                        account_name,
                        "--location",
                        self.embedding_location,
                        "--only-show-errors",
                    ],
                    timeout=1200,
                    label="az-openai-purge",
                )
                if not purge.succeeded:
                    errors.append("soft-deleted embedding account")
                else:
                    self.embedding_account_name = None
        return errors

    def _cleanup_resource_group(self) -> None:
        errors: list[str] = []
        for attempt in range(1, 4):
            result = self.runner.run(
                [
                    "az",
                    "group",
                    "delete",
                    "--subscription",
                    self.subscription_id,
                    "--name",
                    self.resource_group,
                    "--yes",
                    "--only-show-errors",
                ],
                timeout=2400,
                label=f"az-group-delete-{attempt}",
            )
            if result.succeeded and not self.exists():
                self.group_created = False
                return
            errors.append(
                f"attempt {attempt}: exit={result.returncode}, timeout={result.timed_out}"
            )
            time.sleep(15 * attempt)
        if self.exists():
            raise CommandError(
                f"resource group {self.resource_group} still exists after cleanup: "
                + "; ".join(errors)
            )
        self.group_created = False

    def exists(self) -> bool:
        """Return whether the owned resource group still exists."""
        value = self.az.text(
            [
                "group",
                "exists",
                "--subscription",
                self.subscription_id,
                "--name",
                self.resource_group,
            ],
            label="az-group-exists",
            check=False,
        )
        return value.lower() == "true"

    def _public_ip(self) -> str:
        result = self.runner.run(
            ["curl", "-fsS", "https://api.ipify.org"],
            timeout=30,
            label="public-ip",
            check=True,
        )
        value = result.stdout_path.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", value):
            raise CommandError("public IP lookup returned an unexpected value", result)
        if any(int(part) > 255 for part in value.split(".")):
            raise CommandError("public IP lookup returned an invalid IPv4 address", result)
        return value

    def _wait_for_database(self) -> None:
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            status = self.az.text(
                [
                    "sql",
                    "db",
                    "show",
                    "--resource-group",
                    self.resource_group,
                    "--server",
                    self.server_name,
                    "--name",
                    self.database_name,
                    "--query",
                    "status",
                ],
                label="az-sql-db-status",
                check=False,
            )
            if status == "Online":
                return
            time.sleep(15)
        raise CommandError("Azure SQL database did not become Online within 10 minutes")

    def _embedding(self, identity: dict) -> tuple[str | None, str | None, int | None]:
        if self.existing_embedding_endpoint:
            if not self.existing_embedding_deployment or not self.existing_embedding_dimension:
                raise CommandError(
                    "existing embedding endpoint requires deployment and dimension"
                )
            return (
                self.existing_embedding_endpoint,
                self.existing_embedding_deployment,
                self.existing_embedding_dimension,
            )
        if not self.provision_embedding:
            return None, None, None
        account_name = self.server_name.replace("sqlhub", "aoai")
        if self.existing_server:
            account_name = "aoai-" + uuid4().hex[:16]
        created = self.az.json(
            [
                "cognitiveservices",
                "account",
                "create",
                "--resource-group",
                self.resource_group,
                "--name",
                account_name,
                "--location",
                self.embedding_location,
                "--kind",
                "OpenAI",
                "--sku",
                "S0",
                "--custom-domain",
                account_name,
                "--yes",
            ],
            label="az-openai-create",
            timeout=1200,
            check=True,
        )
        self.embedding_account_name = account_name
        scope = created["id"]
        assignment = self.az.json(
            [
                "role",
                "assignment",
                "create",
                "--assignee-object-id",
                identity["id"],
                "--assignee-principal-type",
                "User",
                "--role",
                "Cognitive Services OpenAI User",
                "--scope",
                scope,
            ],
            label="az-openai-role",
            check=True,
        )
        self.embedding_role_assignment_id = assignment["id"]
        deployment = "text-embedding-3-small"
        self.az.json(
            [
                "cognitiveservices",
                "account",
                "deployment",
                "create",
                "--resource-group",
                self.resource_group,
                "--name",
                account_name,
                "--deployment-name",
                deployment,
                "--model-name",
                deployment,
                "--model-version",
                "1",
                "--model-format",
                "OpenAI",
                "--sku-name",
                "Standard",
                "--sku-capacity",
                "1",
            ],
            label="az-openai-deploy",
            timeout=1200,
            check=True,
        )
        self.embedding_deployment_name = deployment
        endpoint = self.az.text(
            [
                "cognitiveservices",
                "account",
                "show",
                "--resource-group",
                self.resource_group,
                "--name",
                account_name,
                "--query",
                "properties.endpoint",
            ],
            label="az-openai-endpoint",
        )
        return endpoint, deployment, 1536

    def provisioned_resource_ids(self) -> list[str]:
        """Return ARM IDs for every resource provisioned by this environment."""
        resource_group_id = (
            f"/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
        )
        server_id = (
            f"{resource_group_id}/providers/Microsoft.Sql"
            f"/servers/{self.server_name}"
        )
        resource_ids: list[str] = []
        if self.group_created:
            resource_ids.append(resource_group_id)
        if self.server_created:
            resource_ids.append(server_id)
        if self.firewall_created:
            resource_ids.append(
                f"{server_id}/firewallRules/{self.firewall_rule_name}"
            )
        if self.database_created:
            resource_ids.append(f"{server_id}/databases/{self.database_name}")
        if self.embedding_account_name:
            account_id = (
                f"{resource_group_id}/providers/Microsoft.CognitiveServices"
                f"/accounts/{self.embedding_account_name}"
            )
            resource_ids.append(account_id)
            if self.embedding_deployment_name:
                resource_ids.append(
                    f"{account_id}/deployments/{self.embedding_deployment_name}"
                )
        if self.embedding_role_assignment_id:
            resource_ids.append(self.embedding_role_assignment_id)
        return resource_ids


def cleanup_resource_group(
    tenant_id: str,
    subscription_id: str,
    location: str,
    embedding_location: str,
    resource_group: str,
    evidence_dir: Path,
) -> None:
    """Delete one explicitly named evaluation resource group."""
    if not resource_group.startswith("rg-sqlhub-eval-"):
        raise ValueError("refusing to delete a resource group outside the evaluation prefix")
    environment = AzureEnvironment(
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        location=location,
        evidence_dir=evidence_dir,
        embedding_location=embedding_location,
        provision_embedding=False,
        reporter=ProgressReporter(),
    )
    environment.resource_group = resource_group
    environment.group_created = True
    environment.cleanup()
