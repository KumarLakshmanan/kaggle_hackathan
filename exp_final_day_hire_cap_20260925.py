"""Diagnostic wrapper: cap hires only during the final game day.

This standalone local experiment imports the unchanged ``main.py`` and limits
only HIRE market orders after the observed daily hire count reaches the
parameterized cap on steps 696-719 (day 29 in the native 720-step game).
The decision uses public step/farm fields only; it does not inspect a seed,
route, replay identity, or hidden state.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


MAX_FINAL_DAY_HIRES = 10
FINAL_DAY_START_STEP = 29 * 24
FINAL_DAY_END_STEP = 30 * 24

_BASE_PATH = Path(__file__).with_name("main.py")
_BASE_SPEC = importlib.util.spec_from_file_location("final_day_hire_cap_base_policy", _BASE_PATH)
if _BASE_SPEC is None or _BASE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load base policy: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_BASE_SPEC)
sys.modules[_BASE_SPEC.name] = _BASE
_BASE_SPEC.loader.exec_module(_BASE)

_TELEMETRY = {
    "final_day_hire_cap_blocked_orders": 0,
    "final_day_hire_cap_blocked_turns": 0,
}


def agent(observation: Any, configuration: Any = None) -> Any:
    """Apply a cumulative hire cap on the final day and nowhere else."""
    action = _BASE.agent(observation, configuration)
    if not isinstance(action, dict) or not isinstance(observation, dict):
        return action

    try:
        step = int(observation.get("step", -1))
    except (TypeError, ValueError):
        return action
    if not FINAL_DAY_START_STEP <= step < FINAL_DAY_END_STEP:
        return action

    farms = observation.get("farms") or []
    try:
        player = int(observation.get("player", 0) or 0)
    except (TypeError, ValueError):
        return action
    if not 0 <= player < len(farms):
        return action

    try:
        hired_today = max(0, int(farms[player].get("hires_today", 0) or 0))
        cap = max(0, int(MAX_FINAL_DAY_HIRES))
    except (AttributeError, TypeError, ValueError):
        return action
    remaining = max(0, cap - hired_today)

    kept = []
    blocked = 0
    for order in action.get("market") or []:
        if isinstance(order, (list, tuple)) and order and order[0] == "HIRE":
            if remaining <= 0:
                blocked += 1
                continue
            remaining -= 1
        kept.append(order)

    if not blocked:
        return action
    _TELEMETRY["final_day_hire_cap_blocked_orders"] += blocked
    _TELEMETRY["final_day_hire_cap_blocked_turns"] += 1
    revised = dict(action)
    revised["market"] = kept
    return revised


agent.telemetry = _TELEMETRY
kaggle_submission_agent = agent
