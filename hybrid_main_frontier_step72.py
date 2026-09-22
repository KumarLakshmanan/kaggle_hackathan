"""Benchmark-only observation-driven Frontier continuation from step 72."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTIER_PATH = ROOT / "kaggle_public_code" / (
    "evelyn3976__kaggriculture-frontier-v156-coherent-liquidity-v6"
) / "kaggriculture-frontier-v156-coherent-liquidity-v6.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("frontier_step72_main", ROOT / "main.py")
_FRONTIER = _load("frontier_step72_policy", FRONTIER_PATH)


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    frontier_action = _FRONTIER.agent(observation, configuration)
    step = int((observation or {}).get("step", 0) or 0)
    if step >= 72:
        return copy.deepcopy(frontier_action)
    return copy.deepcopy(main_action)
