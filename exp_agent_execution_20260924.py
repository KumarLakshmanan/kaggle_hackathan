"""Local day-28 execution experiment; not a Kaggle submission.

This wraps the current, hash-frozen main.py.  The sole policy change replaces
late-season CARE with COLLECT_FERTILIZER when the same observed animal has a
collectible unit.  CARE on day 28 is banked only after the final production
refresh and cannot pay out before the episode ends.  No route identifiers,
seed values, shop predictions, or future action tape are read here.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_BASE_PATH = Path(__file__).resolve().with_name("main.py")
_BASE_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(_BASE_PATH.read_bytes()).hexdigest() != _BASE_SHA256:
    raise RuntimeError("The experiment requires the frozen current main.py")
_SPEC = importlib.util.spec_from_file_location("_exp_execution_frozen_main_20260924", _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot load frozen baseline")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_STATS = {
    "late_care_candidates": 0,
    "late_care_replaced": 0,
    "late_care_storage_skips": 0,
    "late_care_duplicate_skips": 0,
    "late_care_errors": 0,
}


def _salvage(observation, action, configuration):
    if not isinstance(action, dict) or not isinstance(observation, dict):
        return action
    cfg = configuration if hasattr(configuration, "get") else {}
    if int(cfg.get("turnsPerDay", 24)) != 24 or int(cfg.get("boardSize", 10)) != 10:
        return action
    step = int(observation.get("step", -1))
    # The day-28 refresh is the last one; hour 23 is excluded so the parent
    # hour-23 warehouse guard can account for any newly carried fertilizer.
    if not (672 <= step <= 694):
        return action
    player = int(observation["player"])
    farm = observation["farms"][player]
    positions = [farm["farmer"], *farm["hands"]]
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    private = observation["private"]
    load = sum(max(0, int(n)) for n in private["shed"].values())
    load += sum(max(0, int(n)) for bag in private["inventories"] for n in bag.values())
    capacity = int(cfg.get("shedCapacity", 100))
    claimed = set()
    for pos, command in zip(positions, commands):
        if not command:
            continue
        x, y = pos
        if command[0] == "COLLECT_FERTILIZER":
            claimed.add((x, y))
        elif command[0] == "HARVEST":
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict):
                load += max(0, int(tile.get("yield_units", 0)))
    revised = None
    for index, (pos, command) in enumerate(zip(positions, commands)):
        if not command or command[0] != "CARE":
            continue
        x, y = pos
        tile = farm["tiles"][y][x]
        if not isinstance(tile, dict) or not tile.get("animal") or not tile.get("fertilizer_available"):
            continue
        _STATS["late_care_candidates"] += 1
        if (x, y) in claimed:
            _STATS["late_care_duplicate_skips"] += 1
            continue
        if load + 1 > capacity:
            _STATS["late_care_storage_skips"] += 1
            continue
        if revised is None:
            revised = dict(action)
            revised["farmer"] = list(commands[0])
            revised["hands"] = [list(c) for c in commands[1:]]
        if index == 0:
            revised["farmer"] = ["COLLECT_FERTILIZER"]
        else:
            revised["hands"][index - 1] = ["COLLECT_FERTILIZER"]
        claimed.add((x, y))
        load += 1
        _STATS["late_care_replaced"] += 1
    return revised if revised is not None else action


def agent(observation, configuration=None):
    if isinstance(observation, dict) and int(observation.get("step", -1)) == 0:
        for key in _STATS:
            _STATS[key] = 0
    action = _BASE.agent(observation, configuration)
    try:
        return _salvage(observation, action, configuration)
    except Exception:
        _STATS["late_care_errors"] += 1
        return action


agent.telemetry = _STATS
