"""Bounded subprocess execution and local process lifecycle helpers."""

from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Self

from .models import CommandResult
from .progress import ProgressReporter


class CommandError(RuntimeError):
    """Raised when a required command fails."""

    def __init__(self, message: str, result: CommandResult | None = None):
        super().__init__(message)
        self.result = result


class CommandRunner:
    """Run commands with bounded output, timeouts, and process-group cleanup."""

    def __init__(
        self,
        evidence_dir: Path,
        *,
        reporter: ProgressReporter | None = None,
    ):
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.reporter = reporter
        self._sequence = 0

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout: int = 600,
        label: str = "command",
        check: bool = False,
        input_text: str | None = None,
    ) -> CommandResult:
        """Run a command, capture evidence, and terminate its process group on timeout."""
        self._sequence += 1
        stem = f"{self._sequence:03d}-{label}"
        stdout_path = self.evidence_dir / f"{stem}.stdout.txt"
        stderr_path = self.evidence_dir / f"{stem}.stderr.txt"
        metadata_path = self.evidence_dir / f"{stem}.json"
        started = time.monotonic()
        token = (
            self.reporter.start("command", label, f"evidence={metadata_path}")
            if self.reporter
            else None
        )
        timed_out = False
        try:
            with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
                "w", encoding="utf-8"
            ) as stderr:
                process = subprocess.Popen(
                    list(argv),
                    cwd=cwd,
                    env=dict(env) if env is not None else None,
                    stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    start_new_session=True,
                )
                try:
                    process.communicate(input=input_text, timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._terminate_group(process.pid)
                    process.wait(timeout=30)
                finally:
                    self._terminate_group(process.pid, ignore_missing=True)
        except OSError as exc:
            if token and self.reporter:
                self.reporter.finish(token, status="ERROR", detail=str(exc))
            raise
        duration = time.monotonic() - started
        result = CommandResult(
            argv=list(argv),
            returncode=process.returncode,
            duration_seconds=duration,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timed_out=timed_out,
        )
        metadata_path.write_text(
            json.dumps(
                {
                    "argv": list(argv),
                    "cwd": str(cwd) if cwd else None,
                    "returncode": result.returncode,
                    "duration_seconds": result.duration_seconds,
                    "timed_out": result.timed_out,
                    "stdout": stdout_path.name,
                    "stderr": stderr_path.name,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if token and self.reporter:
            status = "TIMEOUT" if timed_out else "PASS" if result.succeeded else "FAIL"
            error_summary = _stderr_summary(stderr_path) if not result.succeeded else None
            self.reporter.finish(
                token,
                status=status,
                detail=(
                    f"exit={result.returncode} stdout={stdout_path} stderr={stderr_path}"
                    + (f" error={error_summary}" if error_summary else "")
                ),
            )
        if check and not result.succeeded:
            error_summary = _stderr_summary(stderr_path)
            message = (
                f"{label} failed with exit code {result.returncode}"
                + (" after timeout" if timed_out else "")
            )
            if error_summary:
                message += f": {error_summary}"
            raise CommandError(message, result)
        return result

    @staticmethod
    def _terminate_group(pid: int, *, ignore_missing: bool = False) -> None:
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            if not ignore_missing:
                return
        time.sleep(0.2)
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


class ManagedProcess:
    """Start a local server and always terminate its full process group."""

    def __init__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        log_path: Path,
        reporter: ProgressReporter | None = None,
        label: str = "local-process",
    ):
        self.argv = list(argv)
        self.cwd = cwd
        self.env = dict(env)
        self.log_path = log_path
        self.reporter = reporter
        self.label = label
        self._token = None
        self._stream = None
        self.process: subprocess.Popen[str] | None = None

    def __enter__(self) -> Self:
        if self.reporter:
            self._token = self.reporter.start(
                "process", self.label, f"log={self.log_path}"
            )
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            self.argv,
            cwd=self.cwd,
            env=self.env,
            stdin=subprocess.DEVNULL,
            stdout=self._stream,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        return self

    def wait_for_http(self, url: str, *, timeout: int = 120) -> str:
        """Wait for an HTTP endpoint and return its response body."""
        deadline = time.monotonic() + timeout
        last_error = "endpoint not attempted"
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                raise CommandError(f"server exited before {url} became ready")
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    return response.read().decode("utf-8", errors="replace")
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = str(exc)
                time.sleep(2)
        raise CommandError(f"timed out waiting for {url}: {last_error}")

    def wait_for_tcp(self, host: str, port: int, *, timeout: int = 60) -> None:
        """Wait for a TCP listener owned by the managed process."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                raise CommandError(f"server exited before {host}:{port} became ready")
            try:
                with socket.create_connection((host, port), timeout=2):
                    return
            except OSError:
                time.sleep(1)
        raise CommandError(f"timed out waiting for {host}:{port}")

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.process is not None:
            CommandRunner._terminate_group(self.process.pid, ignore_missing=True)
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
        if self._stream is not None:
            self._stream.close()
        if self.reporter and self._token:
            self.reporter.finish(
                self._token,
                status="PASS" if exc_type is None else "FAIL",
                detail=f"log={self.log_path}",
            )


def merged_environment(values: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return the current environment plus explicit non-secret overrides."""
    result = os.environ.copy()
    result.update(values or {})
    return result


def _stderr_summary(path: Path) -> str | None:
    """Return one bounded, redacted error line for console diagnostics."""
    try:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
    except OSError:
        return None
    if not lines:
        return None
    value = lines[0][:600]
    return re.sub(
        r"(?i)\b(password|secret|token|api[-_ ]?key)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        value,
    )
