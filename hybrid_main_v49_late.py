"""Benchmark-only late switch to the downloaded V49 policy."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V49_PATH = ROOT / "kaggle_complete_agents_2026-09-21" / (
    "ahmedberatozer__kaggriculture-v49-funded-sale-timing-and-worker__2916b93119a2.py"
)
_SWITCH_STEP = 480


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("late_v49_main", ROOT / "main.py")
_V49 = _load("late_v49_policy", V49_PATH)


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    v49_action = _V49.agent(observation, configuration)
    step = int((observation or {}).get("step", 0) or 0)
    if step >= int(_SWITCH_STEP):
        return copy.deepcopy(v49_action)
    return copy.deepcopy(main_action)
