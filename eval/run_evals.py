#!/usr/bin/env python3
"""Run Azure SQL Developer Hub prompts through a coding-agent CLI."""

from __future__ import annotations

import argparse
import json
import signal
import sys
import tempfile
from pathlib import Path

from hub_eval.azure import AzureEnvironment, cleanup_resource_group
from hub_eval.command import CommandError
from hub_eval.configuration import ConfigurationError, load_validation_environment
from hub_eval.models import RunSettings
from hub_eval.runner import EvaluationRunner, expand_scenarios
from hub_eval.scenarios import DEFAULT_SCENARIO_ORDER, SCENARIOS


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
        description="Run prompt scenarios with Copilot CLI and disposable Azure resources."
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
    parser.add_argument("--agent", default="copilot")
    parser.add_argument(
        "--location",
        default=configuration.location if configuration else None,
    )
    parser.add_argument(
        "--embedding-location",
        default=configuration.embedding_location if configuration else None,
    )
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=DEFAULT_SCENARIO_ORDER,
        dest="scenarios",
    )
    parser.add_argument("--agent-timeout-seconds", type=int, default=2700)
    parser.add_argument("--validation-timeout-seconds", type=int, default=900)
    parser.add_argument("--output", type=Path, default=repository / "eval/runs")
    parser.add_argument("--keep-workspaces", action="store_true")
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
    operation.add_argument("--preflight", action="store_true")
    operation.add_argument("--cleanup-only", metavar="RESOURCE_GROUP")
    args = parser.parse_args(argv)
    if configuration_error:
        parser.error(str(configuration_error))
    args.repository = repository
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


def main() -> int:
    """Run cleanup, dry-run planning, or the requested live evaluation."""
    args = parse_args()
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
    models = tuple(args.models or ["gpt-5.4"])
    scenarios = tuple(args.scenarios or DEFAULT_SCENARIO_ORDER)
    selected = expand_scenarios(scenarios)
    if args.preflight:
        with tempfile.TemporaryDirectory(prefix="sqlhub-eval-preflight-") as temporary:
            environment = AzureEnvironment(
                tenant_id=args.tenant,
                subscription_id=args.subscription,
                location=args.location,
                evidence_dir=Path(temporary),
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
            try:
                identity = environment.preflight()
            except (CommandError, OSError, ValueError, KeyError) as exc:
                print(f"Azure preflight failed: {exc}", file=sys.stderr)
                return 1
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "subscription": args.subscription,
                    "identity": {
                        "display_name": identity["displayName"],
                        "object_id": identity["id"],
                    },
                    "resource_group": args.existing_resource_group,
                    "scenarios": selected,
                },
                indent=2,
            )
        )
        return 0
    if args.dry_run:
        print(
            json.dumps(
                {
                    "subscription": args.subscription,
                    "tenant": args.tenant,
                    "env_file": str(args.env_file.resolve()),
                    "agent": args.agent,
                    "location": args.location,
                    "models": models,
                    "scenarios": selected,
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
        models=models,
        scenarios=scenarios,
        agent_timeout_seconds=args.agent_timeout_seconds,
        validation_timeout_seconds=args.validation_timeout_seconds,
        keep_workspaces=args.keep_workspaces,
        embedding_location=args.embedding_location,
        embedding_endpoint=args.embedding_endpoint,
        embedding_deployment=args.embedding_deployment,
        embedding_dimension=args.embedding_dimension,
        existing_resource_group=args.existing_resource_group,
        existing_server=args.existing_server,
    )
    runner = EvaluationRunner(settings, agent_name=args.agent)
    try:
        return runner.run()
    finally:
        runner.remove_workspaces()


def _interrupt(signum, frame) -> None:
    raise KeyboardInterrupt(f"received signal {signum}")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _interrupt)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(130) from None
