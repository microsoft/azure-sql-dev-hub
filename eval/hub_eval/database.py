"""Independent Azure SQL assertions using the signed-in Azure CLI identity."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import mssql_python
from azure.identity import AzureCliCredential
from mssql_python.exceptions import ConnectionStringParseError

from .command import CommandError
from .models import AzureResources
from .progress import ProgressReporter


class DatabaseProbe:
    """Execute bounded read-only validation queries against the disposable database."""

    def __init__(
        self,
        resources: AzureResources,
        *,
        reporter: ProgressReporter | None = None,
    ):
        self.resources = resources
        self.credential = AzureCliCredential()
        self.reporter = reporter

    def query(
        self,
        statement: str,
        parameters: Sequence[Any] = (),
        *,
        attempts: int = 5,
        label: str = "database-probe",
    ) -> list[tuple]:
        """Run a query with retries for new-server identity and firewall propagation."""
        token = self.reporter.start("sql", label) if self.reporter else None
        errors: list[str] = []
        for attempt in range(1, attempts + 1):
            connection = None
            cursor = None
            try:
                connection = mssql_python.connect(
                    (
                        f"Server=tcp:{self.resources.server_fqdn},1433;"
                        f"Database={self.resources.database_name};"
                        "Encrypt=yes;TrustServerCertificate=no;"
                    ),
                    token_provider=self.credential,
                    timeout=30,
                )
                cursor = connection.cursor()
                cursor.execute(statement, *parameters)
                rows = [tuple(row) for row in cursor.fetchall()]
                if token and self.reporter:
                    self.reporter.finish(
                        token, detail=f"rows={len(rows)} attempts={attempt}"
                    )
                return rows
            except (mssql_python.Error, ConnectionStringParseError) as exc:
                errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
                if self.reporter and attempt < attempts:
                    self.reporter.info(
                        "sql",
                        label,
                        f"retry={attempt}/{attempts} error={type(exc).__name__}",
                    )
                if attempt == attempts:
                    break
                time.sleep(10 * attempt)
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None:
                    connection.close()
        message = "database validation failed: " + "; ".join(errors)
        if token and self.reporter:
            self.reporter.finish(token, status="FAIL", detail=message)
        raise CommandError(message)

    def scalar(
        self,
        statement: str,
        parameters: Sequence[Any] = (),
        *,
        label: str = "database-probe",
    ) -> Any:
        """Return the first column of the first validation row."""
        rows = self.query(statement, parameters, label=label)
        if not rows:
            raise CommandError("database validation query returned no rows")
        return rows[0][0]
