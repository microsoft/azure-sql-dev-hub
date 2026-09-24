"""Shared data models for prompt evaluation runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    """Result of a bounded subprocess invocation."""

    argv: list[str]
    returncode: int
    duration_seconds: float
    stdout_path: Path
    stderr_path: Path
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        """Return whether the command completed successfully."""
        return self.returncode == 0 and not self.timed_out


@dataclass(frozen=True)
class AzureResources:
    """Names and connection data for one disposable Azure environment."""

    subscription_id: str
    resource_group: str
    location: str
    server_name: str
    database_name: str
    server_fqdn: str
    embedding_endpoint: str | None = None
    embedding_deployment: str | None = None
    embedding_dimension: int | None = None


@dataclass
class ScenarioResult:
    """Outcome and evidence for one prompt scenario."""

    scenario: str
    model: str
    status: str
    reason: str
    workspace: str
    agent_duration_seconds: float | None = None
    validation_duration_seconds: float | None = None
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for JSON evidence."""
        return asdict(self)


@dataclass(frozen=True)
class RunSettings:
    """Validated command-line settings for one matrix run."""

    repository: Path
    output_root: Path
    tenant_id: str
    subscription_id: str
    location: str
    models: tuple[str, ...]
    scenarios: tuple[str, ...]
    agent_timeout_seconds: int
    validation_timeout_seconds: int
    keep_workspaces: bool
    embedding_location: str
    embedding_endpoint: str | None
    embedding_deployment: str | None
    embedding_dimension: int | None
    existing_resource_group: str | None
    existing_server: str | None
