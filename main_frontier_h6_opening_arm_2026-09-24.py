"""Diagnostic opening-queue arms over the current Frontier H6 candidate.

Set KAGG_OPENING_ARM to A, B, C, or D when benchmarking:
  A: unchanged BUY 20 / SELL 15 opening (same-build control)
  B: BUY 8 / SELL 8 / BUY 5 (current candidate intervention)
  C: BUY 5 only (removes the round trip)
  D: BUY 13 / SELL 8 (same gross quantities as B, one split removed)
  P: BUY 8 / BUY 5 / SELL 8 (same orders and quantities as B, swapped middle slots)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any


_BASE_PATH = Path(__file__).resolve().with_name("main_frontier_h6_candidate_2026-09-24.py")
_SPEC = importlib.util.spec_from_file_location("main_frontier_h6_opening_arm_base", _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load base candidate: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

# Suppress the candidate's built-in B arm so all four options share the same
# exact controller and differ only in their step-0 market queue.
_BASE._H6_OPENING_QUEUE_FROM = None
_ARM = os.environ.get("KAGG_OPENING_ARM", "A").upper()
_QUEUES = {
    "A": None,
    "B": [
        ["BUY_PRODUCT", "WHEAT", 8],
        ["SELL", "WHEAT", 8],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "C": [
        ["BUY_PRODUCT", "WHEAT", 5],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "D": [
        ["BUY_PRODUCT", "WHEAT", 13],
        ["SELL", "WHEAT", 8],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "P": [
        ["BUY_PRODUCT", "WHEAT", 8],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["SELL", "WHEAT", 8],
        ["BUY_SEED", "WHEAT", 1],
    ],
}
if _ARM not in _QUEUES:
    raise ValueError(f"KAGG_OPENING_ARM must be A, B, C, or D; got {_ARM!r}")
_ORIGINAL_QUEUE = [
    ["BUY_PRODUCT", "WHEAT", 20],
    ["SELL", "WHEAT", 15],
    ["BUY_SEED", "WHEAT", 1],
]
_DIAGNOSTICS: dict[str, Any] = {}
_APPLIED = 0


def agent(observation: Any, configuration: Any = None) -> Any:
    global _APPLIED
    action = _BASE.agent(observation, configuration)
    if (
        _ARM != "A"
        and isinstance(observation, dict)
        and int(observation.get("step", -1)) == 0
        and isinstance(action, dict)
        and action.get("market") == _ORIGINAL_QUEUE
    ):
        action = dict(action, market=[list(order) for order in _QUEUES[_ARM]])
        _APPLIED += 1
    _DIAGNOSTICS.clear()
    _DIAGNOSTICS.update(_BASE.agent.telemetry)
    _DIAGNOSTICS["opening_arm"] = _ARM
    _DIAGNOSTICS["opening_arm_applied"] = _APPLIED
    return action


agent.telemetry = _DIAGNOSTICS
kaggle_submission_agent = agent
