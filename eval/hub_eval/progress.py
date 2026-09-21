"""Human-readable, flushed console progress reporting."""

from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class ProgressToken:
    """Start time and identity for one reported operation."""

    category: str
    name: str
    started: float


class ProgressReporter:
    """Print concise lifecycle events while detailed output remains in evidence files."""

    def __init__(
        self,
        *,
        stream: TextIO = sys.stdout,
        error_stream: TextIO = sys.stderr,
    ):
        self.stream = stream
        self.error_stream = error_stream
        self._lock = threading.Lock()

    def start(self, category: str, name: str, detail: str | None = None) -> ProgressToken:
        """Print a START event and return a duration token."""
        token = ProgressToken(category=category, name=name, started=time.monotonic())
        self._write("START", category, name, detail=detail)
        return token

    def finish(
        self,
        token: ProgressToken,
        *,
        status: str = "PASS",
        detail: str | None = None,
    ) -> float:
        """Print an END event with elapsed time and return the duration."""
        duration = time.monotonic() - token.started
        self._write(
            "END",
            token.category,
            token.name,
            status=status,
            duration=duration,
            detail=detail,
            error=status not in {"PASS", "SKIP"},
        )
        return duration

    def info(self, category: str, name: str, detail: str | None = None) -> None:
        """Print a one-shot informational event."""
        self._write("INFO", category, name, detail=detail)

    def error(self, category: str, name: str, detail: str) -> None:
        """Print a one-shot error event."""
        self._write("ERROR", category, name, detail=detail, error=True)

    def artifact(self, path: Path, description: str) -> None:
        """Report an evidence or generated artifact path."""
        self.info("artifact", description, str(path))

    def _write(
        self,
        event: str,
        category: str,
        name: str,
        *,
        status: str | None = None,
        duration: float | None = None,
        detail: str | None = None,
        error: bool = False,
    ) -> None:
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        fields = [f"[{timestamp}]", event, category, name]
        if status:
            fields.append(status)
        if duration is not None:
            fields.append(f"duration={_duration(duration)}")
        if detail:
            fields.append(detail)
        target = self.error_stream if error else self.stream
        with self._lock:
            print(" | ".join(fields), file=target, flush=True)


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m{remainder:04.1f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h{int(minutes):02d}m{remainder:04.1f}s"
