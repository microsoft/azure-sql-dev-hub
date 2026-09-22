"""Load exact prompt-named verification modules."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from .scenario_model import ScenarioSpec

DEFAULT_SCENARIO_ORDER = (
    "javascript-app",
    "python-api",
    "rag-app",
    "serverless-api",
    "event-driven-app",
    "multi-tenant",
)

VERIFICATION_ROOT = Path(__file__).resolve().parent.parent / "verifications"


def _load_module(name: str) -> ModuleType:
    path = VERIFICATION_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(
        f"hub_eval.verification_{name.replace('-', '_')}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load verification module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_scenarios() -> dict[str, ScenarioSpec]:
    scenarios = {}
    for name in DEFAULT_SCENARIO_ORDER:
        module = _load_module(name)
        scenario = getattr(module, "SCENARIO", None)
        if not isinstance(scenario, ScenarioSpec):
            raise TypeError(f"{name}.py does not export a ScenarioSpec named SCENARIO")
        if scenario.id != name or Path(scenario.prompt_file).stem != name:
            raise RuntimeError(
                f"{name}.py must verify the prompt with the same filename stem"
            )
        scenarios[name] = scenario
    return scenarios


SCENARIOS = _load_scenarios()
