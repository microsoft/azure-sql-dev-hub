"""Strict loading of versioned, non-secret evaluation configurations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, SequenceNode

from .catalog import SUPPORTED_HARNESSES
from .configuration import ConfigurationError
from .models import EvaluationTarget, TestMatrix, output_slug
from .scenarios import DEFAULT_SCENARIO_ORDER

TOP_LEVEL_KEYS = {
    "schema_version",
    "scenarios",
    "agent_timeout_seconds",
    "validation_timeout_seconds",
    "keep_workspaces",
    "harnesses",
}
HARNESS_KEYS = {"name", "models"}


def load_test_matrix(path: Path) -> TestMatrix:
    """Load and validate one schema-versioned YAML evaluation configuration."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc
    try:
        value = _load_unique_mappings(path, text)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path}: root must be a mapping")
    _require_exact_keys(path, "root", value, TOP_LEVEL_KEYS)
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ConfigurationError(f"{path}: schema_version must be the supported integer 1")

    scenarios = _string_list(path, "scenarios", value["scenarios"])
    unknown_scenarios = [name for name in scenarios if name not in DEFAULT_SCENARIO_ORDER]
    if unknown_scenarios:
        raise ConfigurationError(
            f"{path}: scenarios contains unknown scenario {unknown_scenarios[0]!r}"
        )
    _reject_duplicates(path, "scenarios", scenarios)

    agent_timeout = _minimum_integer(
        path, "agent_timeout_seconds", value["agent_timeout_seconds"], 60
    )
    validation_timeout = _minimum_integer(
        path, "validation_timeout_seconds", value["validation_timeout_seconds"], 30
    )
    if type(value["keep_workspaces"]) is not bool:
        raise ConfigurationError(f"{path}: keep_workspaces must be a boolean")

    harness_values = value["harnesses"]
    if not isinstance(harness_values, list) or not harness_values:
        raise ConfigurationError(f"{path}: harnesses must be a non-empty list")
    harness_names: list[str] = []
    targets: list[EvaluationTarget] = []
    target_keys: set[tuple[str, str]] = set()
    for index, harness_value in enumerate(harness_values):
        context = f"harnesses[{index}]"
        if not isinstance(harness_value, dict):
            raise ConfigurationError(f"{path}: {context} must be a mapping")
        _require_exact_keys(path, context, harness_value, HARNESS_KEYS)
        name = _string(path, f"{context}.name", harness_value["name"])
        if name not in SUPPORTED_HARNESSES:
            raise ConfigurationError(f"{path}: {context}.name unsupported harness {name!r}")
        if name in harness_names:
            raise ConfigurationError(f"{path}: duplicate harness {name!r}")
        harness_names.append(name)
        models = _string_list(path, f"{context}.models", harness_value["models"])
        _reject_duplicates(path, f"{context}.models", models)
        slugs: set[str] = set()
        for model in models:
            slug = output_slug(model)
            if not slug:
                raise ConfigurationError(
                    f"{path}: {context}.models contains a model with an empty output slug"
                )
            if slug in slugs:
                raise ConfigurationError(
                    f"{path}: {context}.models has normalized output slug collision {slug!r}"
                )
            slugs.add(slug)
            key = (name, model)
            if key in target_keys:
                raise ConfigurationError(f"{path}: duplicate target {name}:{model}")
            target_keys.add(key)
            targets.append(EvaluationTarget(name, model))
    return TestMatrix(
        targets=tuple(targets),
        scenarios=tuple(scenarios),
        agent_timeout_seconds=agent_timeout,
        validation_timeout_seconds=validation_timeout,
        keep_workspaces=value["keep_workspaces"],
    )


def _load_unique_mappings(path: Path, text: str) -> Any:
    loader = yaml.SafeLoader(text)
    try:
        node = loader.get_single_node()
        if node is None:
            return None
        _reject_duplicate_mapping_keys(path, loader, node, "root", set())
        return loader.construct_document(node)
    finally:
        loader.dispose()


def _reject_duplicate_mapping_keys(
    path: Path,
    loader: yaml.SafeLoader,
    node: Node,
    context: str,
    visited: set[int],
) -> None:
    if id(node) in visited:
        return
    visited.add(id(node))
    if isinstance(node, MappingNode):
        seen: dict[Any, int] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=True)
            try:
                first_line = seen.get(key)
            except TypeError:
                first_line = None
            if first_line is not None:
                duplicate_line = key_node.start_mark.line + 1
                raise ConfigurationError(
                    f"{path}: {context} duplicate property {key!r} at line "
                    f"{duplicate_line}; first defined at line {first_line}"
                )
            try:
                seen[key] = key_node.start_mark.line + 1
            except TypeError:
                pass
            child_context = str(key) if context == "root" else f"{context}.{key}"
            _reject_duplicate_mapping_keys(
                path, loader, value_node, child_context, visited
            )
    elif isinstance(node, SequenceNode):
        for index, item in enumerate(node.value):
            _reject_duplicate_mapping_keys(
                path, loader, item, f"{context}[{index}]", visited
            )


def validate_targets(
    targets: tuple[EvaluationTarget, ...],
    *,
    context: str = "--target",
) -> None:
    """Validate direct targets for duplicates and artifact path collisions."""
    seen: set[tuple[str, str]] = set()
    paths: set[tuple[str, str]] = set()
    for target in targets:
        if target.harness not in SUPPORTED_HARNESSES:
            raise ConfigurationError(
                f"{context}: unsupported harness {target.harness!r}"
            )
        key = (target.harness, target.model)
        if key in seen:
            raise ConfigurationError(
                f"{context}: duplicate target {target.harness}:{target.model}"
            )
        seen.add(key)
        path = (output_slug(target.harness), output_slug(target.model))
        if not all(path):
            raise ConfigurationError(f"{context}: target has an empty output slug")
        if path in paths:
            raise ConfigurationError(
                f"{context}: normalized output path collision "
                f"{path[0]}/{path[1]}"
            )
        paths.add(path)


def _require_exact_keys(
    path: Path, context: str, value: dict[str, Any], expected: set[str]
) -> None:
    unknown = [key for key in value if key not in expected]
    missing = sorted(expected - set(value))
    if unknown:
        raise ConfigurationError(
            f"{path}: {context} unknown property {unknown[0]!r}"
        )
    if missing:
        raise ConfigurationError(f"{path}: {context} missing property {missing[0]}")


def _string(path: Path, context: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{path}: {context} must be a non-blank string")
    return value


def _string_list(path: Path, context: str, value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ConfigurationError(f"{path}: {context} must be a non-empty list")
    return [_string(path, f"{context}[{index}]", item) for index, item in enumerate(value)]


def _reject_duplicates(path: Path, context: str, values: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ConfigurationError(f"{path}: {context} contains duplicate {value!r}")
        seen.add(value)


def _minimum_integer(path: Path, context: str, value: Any, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ConfigurationError(
            f"{path}: {context} must be an integer of at least {minimum}"
        )
    return value
