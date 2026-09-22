"""Benchmark-only late switch to Amey's observation-driven policy."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AMEY_PATH = ROOT / "kaggle_complete_agents_2026-09-21" / (
    "ameythakur20__kaggriculture-premium-first-market-agent__924e8ac73cf9.py"
)
_SWITCH_STEP = 680


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("late_amey_main", ROOT / "main.py")
_AMEY = _load("late_amey_policy", AMEY_PATH)


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    amey_action = _AMEY.agent(observation, configuration)
    step = int((observation or {}).get("step", 0) or 0)
    if step >= int(_SWITCH_STEP):
        return copy.deepcopy(amey_action)
    return copy.deepcopy(main_action)
