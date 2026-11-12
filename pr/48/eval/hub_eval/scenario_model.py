"""Scenario contract shared by exact prompt-named verification modules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .models import AzureResources
from .progress import ProgressReporter

Validator = Callable[
    [Path, AzureResources, Path, int, ProgressReporter],
    list[str],
]


@dataclass(frozen=True)
class ScenarioSpec:
    """One prompt, its shared workspace, dependencies, and validator."""

    id: str
    prompt_file: str
    workspace: str
    dependencies: tuple[str, ...]
    validator: Validator
    requires_embedding: bool = False
