"""Shared helpers for prompt-specific verification files."""

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path

from .command import CommandError, merged_environment
from .models import AzureResources


def project_with(workspace: Path, filename: str) -> Path:
    """Find one generated project while ignoring build and dependency trees."""
    direct = workspace / filename
    if direct.is_file():
        return workspace
    candidates = sorted(
        path.parent
        for path in workspace.rglob(filename)
        if not {"node_modules", ".next", "bin", "obj"}.intersection(
            path.relative_to(workspace).parts
        )
    )
    if not candidates:
        raise CommandError(f"could not find {filename} under {workspace}")
    if len(candidates) > 1:
        raise CommandError(f"found multiple projects containing {filename} under {workspace}")
    return candidates[0]


def project_python(project: Path) -> str:
    """Resolve a project-local Python interpreter before falling back to python3."""
    candidates = (
        project / ".venv/bin/python",
        project / "venv/bin/python",
        project / ".eval-venv/bin/python",
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    executable = shutil.which("python3")
    if executable is None:
        raise CommandError("python3 is not installed")
    return executable


def http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = 30,
    headers: Mapping[str, str] | None = None,
    expected_status: int | None = None,
):
    """Send one JSON HTTP request and decode its JSON response."""
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            **({"content-type": "application/json"} if payload is not None else {}),
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, body = response.status, response.read().decode()
    except urllib.error.HTTPError as exc:
        if expected_status is None or exc.code != expected_status:
            body = exc.read().decode("utf-8", errors="replace")
            raise CommandError(f"{method} {url} returned {exc.code}: {body}") from exc
        status, body = exc.code, exc.read().decode()
    if expected_status is not None and status != expected_status:
        raise CommandError(
            f"{method} {url} returned {status}, expected {expected_status}: {body}"
        )
    try:
        return status, json.loads(body)
    except json.JSONDecodeError as exc:
        raise CommandError(f"{method} {url} did not return JSON: {body}") from exc


def database_environment(resources: AzureResources) -> dict[str, str]:
    """Build the environment shared by generated database applications."""
    return merged_environment(
        {
            "SQL_SERVER": resources.server_fqdn,
            "SQL_DATABASE": resources.database_name,
        }
    )


def functions_environment(resources: AzureResources) -> dict[str, str]:
    """Build the environment for local Azure Functions validation."""
    environment = database_environment(resources)
    environment["FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT"] = "1"
    return environment
