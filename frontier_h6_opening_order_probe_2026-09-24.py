"""Local benchmark adapter for the turn-0 wheat queue experiment.

This is not a Kaggle submission file. It layers one opening market-order
rewrite over the existing readable Frontier ablation adapter.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from typing import Any


_BASE_PATH = Path(__file__).resolve().parent / "ablation_frontier_adapter_2026-09-23.py"
_BASE_NAME = f"opening_order_base_{time.time_ns()}"
_SPEC = importlib.util.spec_from_file_location(_BASE_NAME, _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load base candidate adapter: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

OPENING_MARKET = [
    ["BUY_PRODUCT", "WHEAT", 8],
    ["SELL", "WHEAT", 8],
    ["BUY_PRODUCT", "WHEAT", 5],
    ["BUY_SEED", "WHEAT", 1],
]


def agent(observation: Any, configuration: Any = None) -> Any:
    action = _BASE.agent(observation, configuration)
    if isinstance(observation, dict) and int(observation.get("step", -1)) == 0:
        if isinstance(action, dict):
            action = dict(action, market=[list(order) for order in OPENING_MARKET])
    return action


agent.telemetry = _BASE.agent.telemetry
kaggle_submission_agent = agent
