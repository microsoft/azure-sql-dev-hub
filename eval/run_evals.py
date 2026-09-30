#!/usr/bin/env python3
"""Run Azure SQL Developer Hub prompts through a coding-agent CLI."""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path

from hub_eval.agents import AgentRequest, create_agent
from hub_eval.azure import AzureEnvironment, cleanup_resource_group
from hub_eval.catalog import SUPPORTED_HARNESSES, documented_models
from hub_eval.command import CommandError
from hub_eval.configuration import ConfigurationError, load_validation_environment
from hub_eval.matrix import (
    load_test_matrix,
    validate_targets,
)
from hub_eval.models import (
    AgentPreflightResult,
    CommandResult,
    EvaluationTarget,
    PreflightResult,
    RunSettings,
    output_slug,
)
from hub_eval.runner import (
    EvaluationRunner,
    build_preflight_report,
    create_run_id,
    expand_scenarios,
)
from hub_eval.scenarios import DEFAULT_SCENARIO_ORDER, SCENARIOS

AGENT_PREFLIGHT_RESPONSE = "HUB_AGENT_PREFLIGHT_OK"
AGENT_PREFLIGHT_PROMPT = (
    f"Reply with exactly {AGENT_PREFLIGHT_RESPONSE} and nothing else. "
    "Do not use tools."
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    repository = Path(__file__).resolve().parent.parent
    default_env_file = repository / "eval/validation.env"
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument("--env-file", type=Path, default=default_env_file)
    bootstrap_args, _ = bootstrap.parse_known_args(argv)
    configuration = None
    configuration_error = None
    try:
        configuration = load_validation_environment(bootstrap_args.env_file.resolve())
    except ConfigurationError as exc:
        configuration_error = exc
    parser = argparse.ArgumentParser(
        description=(
            "Run prompt scenarios with coding-agent CLIs and disposable Azure resources."
        )
    )
    parser.add_argument("--env-file", type=Path, default=default_env_file)
    parser.add_argument(
        "--tenant",
        default=configuration.tenant_id if configuration else None,
    )
    parser.add_argument(
        "--subscription",
        default=configuration.subscription_id if configuration else None,
    )
    parser.add_argument(
        "--location",
        default=configuration.location if configuration else None,
    )
    parser.add_argument(
        "--embedding-location",
        default=configuration.embedding_location if configuration else None,
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--configuration", type=Path, metavar="YAML_PATH")
    selection.add_argument(
        "--target",
        action="append",
        type=_parse_target,
        dest="targets",
        metavar="HARNESS:MODEL",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=DEFAULT_SCENARIO_ORDER,
        dest="scenarios",
    )
    parser.add_argument("--agent-timeout-seconds", type=int, default=None)
    parser.add_argument("--validation-timeout-seconds", type=int, default=None)
    parser.add_argument("--output", type=Path, default=repository / "eval/runs")
    parser.add_argument(
        "--keep-workspaces",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--embedding-endpoint",
        default=configuration.embedding_endpoint if configuration else None,
    )
    parser.add_argument(
        "--embedding-deployment",
        default=configuration.embedding_deployment if configuration else None,
    )
    parser.add_argument(
        "--embedding-dimension",
        type=int,
        default=configuration.embedding_dimension if configuration else None,
    )
    parser.add_argument(
        "--existing-resource-group",
        default=configuration.existing_resource_group if configuration else None,
    )
    parser.add_argument(
        "--existing-server",
        default=configuration.existing_server if configuration else None,
    )
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--dry-run", action="store_true")
    operation.add_argument(
        "--list-models",
        choices=SUPPORTED_HARNESSES,
        metavar="HARNESS",
    )
    operation.add_argument(
        "--preflight:agents",
        dest="preflight_agents",
        action="store_true",
    )
    operation.add_argument(
        "--preflight:permissions",
        dest="preflight_permissions",
        action="store_true",
    )
    operation.add_argument("--preflight", action="store_true")
    operation.add_argument("--cleanup-only", metavar="RESOURCE_GROUP")
    args = parser.parse_args(argv)
    azure_required = not (
        args.list_models or args.preflight_agents or args.dry_run
    )
    if configuration_error and azure_required:
        parser.error(str(configuration_error))
    args.repository = repository
    if args.list_models:
        return args
    try:
        if args.configuration is not None:
            args.configuration = args.configuration.resolve()
            matrix = load_test_matrix(args.configuration)
            args.targets = matrix.targets
            args.scenarios = tuple(args.scenarios or matrix.scenarios)
            args.agent_timeout_seconds = (
                args.agent_timeout_seconds
                if args.agent_timeout_seconds is not None
                else matrix.agent_timeout_seconds
            )
            args.validation_timeout_seconds = (
                args.validation_timeout_seconds
                if args.validation_timeout_seconds is not None
                else matrix.validation_timeout_seconds
            )
            args.keep_workspaces = (
                args.keep_workspaces
                if args.keep_workspaces is not None
                else matrix.keep_workspaces
            )
        else:
            args.targets = tuple(
                args.targets or [EvaluationTarget("copilot", "gpt-5.4")]
            )
            validate_targets(args.targets)
            args.scenarios = tuple(args.scenarios or DEFAULT_SCENARIO_ORDER)
            args.agent_timeout_seconds = (
                args.agent_timeout_seconds
                if args.agent_timeout_seconds is not None
                else 2700
            )
            args.validation_timeout_seconds = (
                args.validation_timeout_seconds
                if args.validation_timeout_seconds is not None
                else 900
            )
            args.keep_workspaces = (
                args.keep_workspaces
                if args.keep_workspaces is not None
                else False
            )
    except ConfigurationError as exc:
        parser.error(str(exc))
    if args.agent_timeout_seconds < 60 or args.validation_timeout_seconds < 30:
        parser.error("timeouts are too short for reliable unattended evaluation")
    provided_embedding = (
        args.embedding_endpoint,
        args.embedding_deployment,
        args.embedding_dimension,
    )
    if any(value is not None for value in provided_embedding) and not all(
        value is not None for value in provided_embedding
    ):
        parser.error(
            "--embedding-endpoint, --embedding-deployment, and --embedding-dimension "
            "must be supplied together"
        )
    if bool(args.existing_resource_group) != bool(args.existing_server):
        parser.error("--existing-resource-group and --existing-server must be supplied together")
    return args


def _parse_target(value: str) -> EvaluationTarget:
    """Parse one HARNESS:MODEL target while preserving the model verbatim."""
    harness, separator, model = value.partition(":")
    if not separator or not harness.strip() or not model.strip():
        raise argparse.ArgumentTypeError(
            "--target must use nonblank HARNESS:MODEL"
        )
    if harness not in SUPPORTED_HARNESSES:
        raise argparse.ArgumentTypeError(
            f"--target has unsupported harness {harness!r}; "
            f"choose from {', '.join(SUPPORTED_HARNESSES)}"
        )
    return EvaluationTarget(harness, model)


def main() -> int:
    """Run cleanup, dry-run planning, or the requested live evaluation."""
    args = parse_args()
    if args.list_models:
        print(
            json.dumps(
                {
                    "harness": args.list_models,
                    "models": list(documented_models(args.list_models)),
                    "note": (
                        "Account policy may reduce availability; "
                        "--preflight:agents is authoritative."
                    ),
                },
                indent=2,
            )
        )
        return 0
    if args.cleanup_only:
        cleanup_resource_group(
            args.tenant,
            args.subscription,
            args.location,
            args.embedding_location,
            args.cleanup_only,
            args.output / "cleanup",
        )
        print(f"Deleted {args.cleanup_only}")
        return 0
    selected = expand_scenarios(args.scenarios)
    if args.preflight or args.preflight_agents or args.preflight_permissions:
        return run_preflight(args, selected)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "subscription": args.subscription,
                    "tenant": args.tenant,
                    "env_file": str(args.env_file.resolve()),
                    "location": args.location,
                    "configuration": (
                        str(args.configuration) if args.configuration else None
                    ),
                    "targets": [
                        {"harness": target.harness, "model": target.model}
                        for target in args.targets
                    ],
                    "scenarios": selected,
                    "agent_timeout_seconds": args.agent_timeout_seconds,
                    "validation_timeout_seconds": args.validation_timeout_seconds,
                    "keep_workspaces": args.keep_workspaces,
                    "existing_resource_group": args.existing_resource_group,
                    "existing_server": args.existing_server,
                },
                indent=2,
            )
        )
        return 0
    settings = RunSettings(
        repository=args.repository,
        output_root=args.output.resolve(),
        tenant_id=args.tenant,
        subscription_id=args.subscription,
        location=args.location,
        targets=args.targets,
        scenarios=args.scenarios,
        agent_timeout_seconds=args.agent_timeout_seconds,
        validation_timeout_seconds=args.validation_timeout_seconds,
        keep_workspaces=args.keep_workspaces,
        embedding_location=args.embedding_location,
        embedding_endpoint=args.embedding_endpoint,
        embedding_deployment=args.embedding_deployment,
        embedding_dimension=args.embedding_dimension,
        existing_resource_group=args.existing_resource_group,
        existing_server=args.existing_server,
        configuration_path=args.configuration,
    )
    runner = EvaluationRunner(settings)
    try:
        return runner.run()
    finally:
        runner.remove_workspaces()


def run_preflight(args: argparse.Namespace, selected: tuple[str, ...]) -> int:
    """Run requested standalone preflight components in one run directory."""
    run_id = create_run_id()
    run_dir = args.output.resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    run_agents = bool(
        getattr(args, "preflight_agents", False)
        or getattr(args, "preflight", False)
    )
    run_permissions = bool(
        getattr(args, "preflight_permissions", False)
        or getattr(args, "preflight", False)
    )
    agent_results = (
        run_agent_preflight(args, run_id, run_dir) if run_agents else []
    )
    permission_results = (
        [run_permission_preflight(args, selected, run_dir)]
        if run_permissions
        else []
    )
    failed = any(result.status != "PASS" for result in agent_results) or any(
        result.status != "PASS" for result in permission_results
    )
    mode = (
        "combined"
        if run_agents and run_permissions
        else "agents"
        if run_agents
        else "permissions"
    )
    report = {
        "schema_version": 1,
        "report_type": "standalone-preflight",
        "run_id": run_id,
        "mode": mode,
        "status": "FAIL" if failed else "PASS",
        "agents": (
            {
                "schema_version": 1,
                "results": [result.to_dict() for result in agent_results],
            }
            if run_agents
            else None
        ),
        "permissions": (
            build_preflight_report(run_id, permission_results)
            if run_permissions
            else None
        ),
    }
    preflight_path = run_dir / "preflight.json"
    preflight_path.write_text(
        json.dumps(report, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    output = {"preflight_path": str(preflight_path), **report}
    print(json.dumps(output, indent=2), file=sys.stderr if failed else sys.stdout)
    return 1 if failed else 0


def run_agent_preflight(
    args: argparse.Namespace,
    run_id: str,
    run_dir: Path,
) -> list[AgentPreflightResult]:
    """Probe every resolved coding-agent target and continue after failures."""
    results: list[AgentPreflightResult] = []
    for target in args.targets:
        target_dir = (
            run_dir
            / "agents"
            / output_slug(target.harness)
            / output_slug(target.model)
        )
        workspace = target_dir / "workspace"
        evidence_dir = target_dir / "evidence"
        workspace.mkdir(parents=True)
        started = time.monotonic()
        command_result = None
        try:
            agent = create_agent(target.harness)
            command_result = agent.probe(
                AgentRequest(
                    prompt=AGENT_PREFLIGHT_PROMPT,
                    model=target.model,
                    workspace=workspace,
                    evidence_dir=evidence_dir,
                    timeout_seconds=args.agent_timeout_seconds,
                    session_name=(
                        f"sqlhub-preflight-{output_slug(target.harness)}-"
                        f"{output_slug(target.model)}-{run_id}"
                    ),
                ),
                AGENT_PREFLIGHT_RESPONSE,
            )
            status = "PASS"
            reason = "Executable, authentication, and model access validated"
        except (CommandError, OSError, ValueError, KeyError) as exc:
            if isinstance(exc, CommandError):
                command_result = exc.result
            status = "FAIL"
            reason = f"{type(exc).__name__}: {exc}"
        results.append(
            AgentPreflightResult(
                harness=target.harness,
                model=target.model,
                status=status,
                duration_seconds=time.monotonic() - started,
                reason=reason,
                evidence=_command_evidence(command_result),
            )
        )
    return results


def run_permission_preflight(
    args: argparse.Namespace,
    selected: tuple[str, ...],
    run_dir: Path,
) -> PreflightResult:
    """Run only the existing Azure context and permissions preflight."""
    environment = AzureEnvironment(
        tenant_id=args.tenant,
        subscription_id=args.subscription,
        location=args.location,
        evidence_dir=run_dir,
        embedding_location=args.embedding_location,
        provision_embedding=any(
            SCENARIOS[name].requires_embedding for name in selected
        ),
        existing_embedding_endpoint=args.embedding_endpoint,
        existing_embedding_deployment=args.embedding_deployment,
        existing_embedding_dimension=args.embedding_dimension,
        existing_resource_group=args.existing_resource_group,
        existing_server=args.existing_server,
    )
    started = time.monotonic()
    try:
        identity = environment.preflight()
        result = PreflightResult(
            harness=None,
            model=None,
            status="PASS",
            duration_seconds=time.monotonic() - started,
            subscription_id=args.subscription,
            resource_group=environment.resource_group,
            scenarios=list(selected),
            identity={
                "display_name": identity["displayName"],
                "object_id": identity["id"],
            },
            permission_checks=list(environment.permission_checks),
            reason="Azure context, providers, and permissions validated",
        )
    except (CommandError, OSError, ValueError, KeyError) as exc:
        result = PreflightResult(
            harness=None,
            model=None,
            status="FAIL",
            duration_seconds=time.monotonic() - started,
            subscription_id=args.subscription,
            resource_group=environment.resource_group,
            scenarios=list(selected),
            identity=None,
            permission_checks=list(environment.permission_checks),
            reason=f"{type(exc).__name__}: {exc}",
        )
    return result


def _command_evidence(result: CommandResult | None) -> tuple[str, ...]:
    """Return command evidence paths without exposing captured output."""
    if result is None:
        return ()
    metadata = result.stdout_path.with_suffix("").with_suffix(".json")
    return (
        str(metadata),
        str(result.stdout_path),
        str(result.stderr_path),
    )


def _interrupt(signum, frame) -> None:
    raise KeyboardInterrupt(f"received signal {signum}")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _interrupt)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(130) from None
