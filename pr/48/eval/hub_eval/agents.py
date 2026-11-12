"""Provider-extensible command-line coding-agent adapters."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
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

    def probe(self, request: AgentRequest, expected_response: str) -> CommandResult:
        """Verify executable, authentication, and model access without tools."""


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

    def probe(self, request: AgentRequest, expected_response: str) -> CommandResult:
        """Run a customization-free Copilot prompt with no effective tools."""
        if shutil.which(self.executable) is None:
            raise CommandError(f"{self.executable} is not installed")
        logs = request.evidence_dir / "copilot-logs"
        logs.mkdir(parents=True, exist_ok=True)
        result = CommandRunner(request.evidence_dir).run(
            [
                self.executable,
                "-p",
                request.prompt,
                "--model",
                request.model,
                "--name",
                request.session_name,
                "--allow-all-tools",
                "--available-tools",
                "--disable-builtin-mcps",
                "--no-custom-instructions",
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
            timeout=request.timeout_seconds,
            label="copilot-preflight",
        )
        self._validate_jsonl(result)
        _require_expected_response(
            result,
            expected_response,
            "Copilot",
            "assistant.message",
        )
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


class ClaudeCli:
    """Run Claude Code in unattended, customization-free JSONL mode."""

    name = "claude"

    def __init__(
        self,
        executable: str = "claude",
        *,
        reporter: ProgressReporter | None = None,
    ):
        self.executable = executable
        self.reporter = reporter

    def run(self, request: AgentRequest) -> CommandResult:
        """Execute one Claude session and validate its final result record."""
        if shutil.which(self.executable) is None:
            raise CommandError(f"{self.executable} is not installed")
        result = CommandRunner(
            request.evidence_dir, reporter=self.reporter
        ).run(
            [
                self.executable,
                "-p",
                request.prompt,
                "--model",
                request.model,
                "--name",
                request.session_name,
                "--output-format",
                "stream-json",
                "--verbose",
                "--permission-mode",
                "bypassPermissions",
                "--permission-prompts",
                "none",
                "--safe-mode",
                "--strict-mcp-config",
                "--no-session-persistence",
                "--no-chrome",
            ],
            cwd=request.workspace,
            timeout=request.timeout_seconds,
            label="claude",
        )
        self._validate_jsonl(result)
        return result

    def probe(self, request: AgentRequest, expected_response: str) -> CommandResult:
        """Run Claude with customizations, MCP servers, and tools disabled."""
        if shutil.which(self.executable) is None:
            raise CommandError(f"{self.executable} is not installed")
        result = CommandRunner(request.evidence_dir).run(
            [
                self.executable,
                "-p",
                request.prompt,
                "--model",
                request.model,
                "--name",
                request.session_name,
                "--output-format",
                "stream-json",
                "--verbose",
                "--permission-mode",
                "dontAsk",
                "--permission-prompts",
                "none",
                "--tools",
                "",
                "--safe-mode",
                "--strict-mcp-config",
                "--no-session-persistence",
                "--no-chrome",
            ],
            cwd=request.workspace,
            timeout=request.timeout_seconds,
            label="claude-preflight",
        )
        self._validate_jsonl(result)
        _require_expected_response(result, expected_response, "Claude", "result")
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
                if isinstance(record, dict) and record.get("type") == "result":
                    final_result = record
        if final_result is None:
            raise CommandError("Claude emitted no final result record", result)
        if final_result.get("is_error") is not False or not result.succeeded:
            raise CommandError("Claude session failed", result)


class CodexCli:
    """Run Codex CLI through its official noninteractive JSONL interface."""

    name = "codex"
    _TOOL_ITEM_TYPES = frozenset(
        {
            "code_interpreter",
            "collab_tool_call",
            "command_execution",
            "computer_action",
            "custom_tool_call",
            "dynamic_tool_call",
            "file_change",
            "function_call",
            "image_generation",
            "image_view",
            "local_shell_call",
            "mcp_tool_call",
            "todo_list",
            "web_search",
        }
    )

    def __init__(
        self,
        executable: str = "codex",
        *,
        reporter: ProgressReporter | None = None,
    ):
        self.executable = executable
        self.reporter = reporter

    def run(self, request: AgentRequest) -> CommandResult:
        """Execute one ephemeral Codex session with workspace-write permission."""
        return self._execute(
            request,
            sandbox="workspace-write",
            label="codex",
            reporter=self.reporter,
        )

    def probe(self, request: AgentRequest, expected_response: str) -> CommandResult:
        """Probe Codex in an isolated read-only session."""
        result = self._execute(
            request,
            sandbox="read-only",
            label="codex-preflight",
            reporter=None,
        )
        self._validate_probe_jsonl(result, expected_response)
        return result

    def _execute(
        self,
        request: AgentRequest,
        *,
        sandbox: str,
        label: str,
        reporter: ProgressReporter | None = None,
    ) -> CommandResult:
        if shutil.which(self.executable) is None:
            raise CommandError(f"{self.executable} is not installed")
        config_args = ["--config", 'approval_policy="never"']
        if sandbox == "workspace-write":
            config_args.extend(
                ["--config", "sandbox_workspace_write.network_access=true"]
            )
        result = CommandRunner(
            request.evidence_dir,
            reporter=reporter,
        ).run(
            [
                self.executable,
                "exec",
                "--json",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                *config_args,
                "--model",
                request.model,
                "--cd",
                str(request.workspace),
                "--sandbox",
                sandbox,
                request.prompt,
            ],
            cwd=request.workspace,
            timeout=request.timeout_seconds,
            label=label,
        )
        self._validate_jsonl(result)
        return result

    @staticmethod
    def _validate_jsonl(result: CommandResult) -> None:
        terminal_type = None
        with result.stdout_path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, Mapping):
                    continue
                record_type = record.get("type")
                if record_type in {"turn.failed", "error"}:
                    raise CommandError("Codex session failed", result)
                terminal_type = record_type
        if terminal_type != "turn.completed":
            raise CommandError("Codex emitted no terminal turn.completed record", result)
        if not result.succeeded:
            raise CommandError("Codex session failed", result)

    @classmethod
    def _validate_probe_jsonl(
        cls,
        result: CommandResult,
        expected_response: str,
    ) -> None:
        """Require an exact agent message and reject any Codex tool activity."""
        found_expected_response = False
        with result.stdout_path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, Mapping):
                    continue
                item = record.get("item")
                if not isinstance(item, Mapping):
                    continue
                item_type = item.get("type")
                if item_type in cls._TOOL_ITEM_TYPES:
                    raise CommandError("Codex preflight used a tool", result)
                if (
                    record.get("type") == "item.completed"
                    and item_type == "agent_message"
                    and isinstance(item.get("text"), str)
                    and item["text"].strip() == expected_response
                ):
                    found_expected_response = True
        if not found_expected_response:
            raise CommandError("Codex preflight returned an unexpected response", result)


def create_agent(
    name: str,
    *,
    reporter: ProgressReporter | None = None,
) -> AgentCli:
    """Resolve an agent adapter by stable provider name."""
    if name == "copilot":
        return CopilotCli(reporter=reporter)
    if name == "claude":
        return ClaudeCli(reporter=reporter)
    if name == "codex":
        return CodexCli(reporter=reporter)
    raise ValueError(
        f"unsupported agent {name!r}; implement AgentCli and register it in create_agent"
    )


def _require_expected_response(
    result: CommandResult,
    expected_response: str,
    harness: str,
    response_record_type: str,
) -> None:
    """Require the harmless preflight marker without exposing response content."""
    with result.stdout_path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                isinstance(record, Mapping)
                and record.get("type") == response_record_type
                and _contains_exact_string(record, expected_response)
            ):
                return
    raise CommandError(f"{harness} preflight returned an unexpected response", result)


def _contains_exact_string(value: object, expected: str) -> bool:
    if isinstance(value, str):
        return value.strip() == expected
    if isinstance(value, Mapping):
        return any(_contains_exact_string(item, expected) for item in value.values())
    if isinstance(value, Sequence):
        return any(_contains_exact_string(item, expected) for item in value)
    return False
