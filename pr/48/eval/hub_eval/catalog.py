"""Documented coding-agent harness and model catalogs."""

from __future__ import annotations

MODEL_CATALOGS: dict[str, tuple[str, ...]] = {
    "copilot": (
        "auto",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "claude-sonnet-5",
        "claude-opus-5",
        "gemini-3.8-flash",
    ),
    "claude": (
        "default",
        "best",
        "fable",
        "sonnet",
        "opus",
        "haiku",
        "claude-sonnet-5",
        "claude-sonnet-5-5",
        "claude-opus-5",
        "claude-opus-5-5",
        "claude-haiku-4-5",
    ),
    "codex": (
        "gpt-6-sol",
        "gpt-6-luna",
    ),
}

SUPPORTED_HARNESSES = tuple(MODEL_CATALOGS)


def documented_models(harness: str) -> tuple[str, ...]:
    """Return stable documented model options for one supported harness."""
    try:
        return MODEL_CATALOGS[harness]
    except KeyError as exc:
        raise ValueError(f"unsupported harness {harness!r}") from exc
