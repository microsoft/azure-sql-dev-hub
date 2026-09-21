"""Strict loading of local Azure evaluation configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when validation.env is absent or inconsistent."""


@dataclass(frozen=True)
class ValidationEnvironment:
    """Azure defaults loaded from the ignored validation.env file."""

    tenant_id: str
    subscription_id: str
    location: str
    existing_resource_group: str | None
    existing_server: str | None
    embedding_location: str
    provision_embedding: bool
    embedding_endpoint: str | None
    embedding_deployment: str | None
    embedding_dimension: int | None


KEYS = {
    "HUB_EVAL_AZURE_TENANT_ID",
    "HUB_EVAL_AZURE_SUBSCRIPTION_ID",
    "HUB_EVAL_AZURE_LOCATION",
    "HUB_EVAL_EXISTING_RESOURCE_GROUP",
    "HUB_EVAL_EXISTING_SQL_SERVER",
    "HUB_EVAL_EMBEDDING_LOCATION",
    "HUB_EVAL_PROVISION_EMBEDDING",
    "HUB_EVAL_EMBEDDING_ENDPOINT",
    "HUB_EVAL_EMBEDDING_DEPLOYMENT",
    "HUB_EVAL_EMBEDDING_DIMENSION",
}

REQUIRED = {
    "HUB_EVAL_AZURE_TENANT_ID",
    "HUB_EVAL_AZURE_SUBSCRIPTION_ID",
    "HUB_EVAL_AZURE_LOCATION",
    "HUB_EVAL_EMBEDDING_LOCATION",
    "HUB_EVAL_PROVISION_EMBEDDING",
}


def load_validation_environment(path: Path) -> ValidationEnvironment:
    """Load one strict KEY=VALUE file without mutating the process environment."""
    if not path.is_file():
        raise ConfigurationError(
            f"{path} does not exist; copy eval/validation.EXAMPLE.env to "
            "eval/validation.env and fill in the Azure values"
        )
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ConfigurationError(f"{path}:{line_number}: expected KEY=VALUE")
        if key not in KEYS:
            raise ConfigurationError(f"{path}:{line_number}: unknown property {key}")
        if key in values:
            raise ConfigurationError(f"{path}:{line_number}: duplicate property {key}")
        values[key] = _unquote(value.strip())
    missing = sorted(key for key in REQUIRED if not values.get(key))
    if missing:
        raise ConfigurationError(f"{path}: missing required values: {', '.join(missing)}")
    existing_group = _optional(values, "HUB_EVAL_EXISTING_RESOURCE_GROUP")
    existing_server = _optional(values, "HUB_EVAL_EXISTING_SQL_SERVER")
    if bool(existing_group) != bool(existing_server):
        raise ConfigurationError(
            f"{path}: existing resource group and SQL server must both be set or both be blank"
        )
    endpoint = _optional(values, "HUB_EVAL_EMBEDDING_ENDPOINT")
    deployment = _optional(values, "HUB_EVAL_EMBEDDING_DEPLOYMENT")
    dimension_text = _optional(values, "HUB_EVAL_EMBEDDING_DIMENSION")
    if any((endpoint, deployment, dimension_text)) and not all(
        (endpoint, deployment, dimension_text)
    ):
        raise ConfigurationError(
            f"{path}: embedding endpoint, deployment, and dimension must all be set or all be blank"
        )
    try:
        dimension = int(dimension_text) if dimension_text else None
    except ValueError as exc:
        raise ConfigurationError(
            f"{path}: HUB_EVAL_EMBEDDING_DIMENSION must be an integer"
        ) from exc
    if dimension is not None and dimension < 1:
        raise ConfigurationError(
            f"{path}: HUB_EVAL_EMBEDDING_DIMENSION must be greater than zero"
        )
    return ValidationEnvironment(
        tenant_id=values["HUB_EVAL_AZURE_TENANT_ID"],
        subscription_id=values["HUB_EVAL_AZURE_SUBSCRIPTION_ID"],
        location=values["HUB_EVAL_AZURE_LOCATION"],
        existing_resource_group=existing_group,
        existing_server=existing_server,
        embedding_location=values["HUB_EVAL_EMBEDDING_LOCATION"],
        provision_embedding=_boolean(
            path,
            "HUB_EVAL_PROVISION_EMBEDDING",
            values["HUB_EVAL_PROVISION_EMBEDDING"],
        ),
        embedding_endpoint=endpoint,
        embedding_deployment=deployment,
        embedding_dimension=dimension,
    )


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _optional(values: dict[str, str], key: str) -> str | None:
    return values.get(key) or None


def _boolean(path: Path, key: str, value: str) -> bool:
    normalized = value.lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ConfigurationError(f"{path}: {key} must be true or false")
