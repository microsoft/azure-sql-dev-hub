"""Provider-extensible command-line coding-agent adapters."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .command import CommandError, CommandRunner, merged_environment
from .models import CommandResult
from .progress import ProgressReporter


@dataclass(frozen=True)
class AgentRequest:
    """One unattended coding-agent invocation."""

    prompt: str
    model: str
    workspace: Path
    evidence_dir: Path
    timeout_seconds: int
    session_name: str


class AgentCli(Protocol):
    """Interface implemented by each supported coding-agent CLI."""

    name: str

    def run(self, request: AgentRequest) -> CommandResult:
        """Run one prompt and return captured command evidence."""


class CopilotCli:
    """Run GitHub Copilot CLI in unattended JSONL mode."""

    name = "copilot"

    def __init__(
        self,
        executable: str = "copilot",
        *,
        reporter: ProgressReporter | None = None,
    ):
        self.executable = executable
        self.reporter = reporter

    def run(self, request: AgentRequest) -> CommandResult:
        """Execute one Copilot session with bounded time and filesystem scope."""
        if shutil.which(self.executable) is None:
            raise CommandError(f"{self.executable} is not installed")
        logs = request.evidence_dir / "copilot-logs"
        logs.mkdir(parents=True, exist_ok=True)
        runner = CommandRunner(request.evidence_dir, reporter=self.reporter)
        result = runner.run(
            [
                self.executable,
                "-p",
                request.prompt,
                "--model",
                request.model,
                "--name",
                request.session_name,
                "--allow-all-tools",
                "--disable-builtin-mcps",
                "--output-format",
                "json",
                "--stream",
                "off",
                "--log-dir",
                str(logs),
                "-C",
                str(request.workspace),
            ],
            cwd=request.workspace,
            env=merged_environment({"COPILOT_ALLOW_ALL": "true"}),
            timeout=request.timeout_seconds,
            label="copilot",
        )
        self._validate_jsonl(result)
        return result

    @staticmethod
    def _validate_jsonl(result: CommandResult) -> None:
        final_result = None
        with result.stdout_path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") == "result":
                    final_result = record
        if final_result is None:
            raise CommandError("Copilot emitted no final result record", result)
        if final_result.get("exitCode") != 0 or not result.succeeded:
            raise CommandError("Copilot session failed", result)


def create_agent(
    name: str,
    *,
    reporter: ProgressReporter | None = None,
) -> AgentCli:
    """Resolve an agent adapter by stable provider name."""
    if name == "copilot":
        return CopilotCli(reporter=reporter)
    raise ValueError(
        f"unsupported agent {name!r}; implement AgentCli and register it in create_agent"
    )
