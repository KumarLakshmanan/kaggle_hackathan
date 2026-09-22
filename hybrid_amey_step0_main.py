"""Benchmark-only common step-0 Amey action followed by main.py."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AMEY_PATH = ROOT / "kaggle_complete_agents_2026-09-21" / (
    "ameythakur20__kaggriculture-premium-first-market-agent__924e8ac73cf9.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("step0_main_policy", ROOT / "main.py")
_AMEY = _load("step0_amey_policy", AMEY_PATH)


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    amey_action = _AMEY.agent(observation, configuration)
    step = int((observation or {}).get("step", 0) or 0)
    return copy.deepcopy(amey_action if step == 0 else main_action)
