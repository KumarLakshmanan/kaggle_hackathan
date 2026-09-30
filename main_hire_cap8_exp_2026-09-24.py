"""Local ablation only: cap the base agent at eight hires per day.

This thin, readable wrapper is for simulator experiments and is not a standalone
Kaggle submission. It imports the unchanged main.py policy, then suppresses only
HIRE market orders beyond the observed daily hire count of eight.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


MAX_DAILY_HIRES = 8
_BASE_PATH = Path(__file__).with_name("main.py")
_BASE_SPEC = importlib.util.spec_from_file_location("hire_cap8_base_policy", _BASE_PATH)
if _BASE_SPEC is None or _BASE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load base policy: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_BASE_SPEC)
sys.modules[_BASE_SPEC.name] = _BASE
_BASE_SPEC.loader.exec_module(_BASE)

_TELEMETRY = {"hire_cap8_blocked_orders": 0, "hire_cap8_blocked_turns": 0}


def agent(observation: Any, configuration: Any = None) -> Any:
    """Run the base policy and block only hires over the daily cap."""
    action = _BASE.agent(observation, configuration)
    if not isinstance(action, dict) or not isinstance(observation, dict):
        return action

    farms = observation.get("farms") or []
    player = int(observation.get("player", 0) or 0)
    if not 0 <= player < len(farms):
        return action

    farm = farms[player]
    hired_today = max(0, int(farm.get("hires_today", 0) or 0))
    remaining = max(0, MAX_DAILY_HIRES - hired_today)
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
    _TELEMETRY["hire_cap8_blocked_orders"] += blocked
    _TELEMETRY["hire_cap8_blocked_turns"] += 1
    revised = dict(action)
    revised["market"] = kept
    return revised


agent.telemetry = _TELEMETRY
kaggle_submission_agent = agent
