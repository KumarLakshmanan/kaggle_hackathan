"""Local-only, observation-driven spare-action fertilizer collection screen.

Predeclared promotion screen: improve own cash and win at least two of the
11 baseline losing recent-live routes without reversing any of 13 wins.
Before changing main.py, also require broad top-100 route and fresh reactive
checks. This wrapper never reads replay identity, seed, or opponent private data.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import uuid


PATH = Path(__file__).with_name("main.py")
EXPECTED_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(PATH.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError("Experiment requires the frozen main.py baseline")
NAME = "_idle_fert_base_" + uuid.uuid4().hex
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load main.py")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = BASE
SPEC.loader.exec_module(BASE)

_MIN_PRICE = 50
_MAX_OCCUPANCY = 80
_DAILY_LIMIT = 3
_STATS = dict(exposed=0, collected=0, crowded=0, errors=0)
_STATE = {}


def _spare_collect(observation, action, configuration):
    step = int(observation["step"])
    if step >= 696 or not isinstance(action, dict):
        return action
    cfg = configuration if isinstance(configuration, dict) else {}
    if int(cfg.get("boardSize", 10)) != 10 or int(cfg.get("turnsPerDay", 24)) != 24:
        return action
    if int(observation["market"]["prices"].get("FERTILIZER", 0)) < _MIN_PRICE:
        return action
    player = int(observation["player"])
    farm = observation["farms"][player]
    positions = [farm["farmer"], *(farm.get("hands") or [])]
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    private = observation["private"]
    occupied = sum(max(0, int(q)) for q in (private.get("shed") or {}).values())
    occupied += sum(max(0, int(q)) for inv in (private.get("inventories") or [])
                    for q in inv.values())
    for index, command in enumerate(commands[:len(positions)]):
        if command and command[0] == "HARVEST":
            x, y = positions[index]
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict):
                occupied += max(0, int(tile.get("yield_units", 0)))
        elif command and command[0] == "COLLECT_FERTILIZER":
            occupied += 1

    day = step // 24
    state = _STATE.get(player)
    if state is None or step <= state["step"] or day != state["day"]:
        state = _STATE[player] = dict(step=-1, day=day, added=0)
    state["step"] = step
    if state["added"] >= _DAILY_LIMIT:
        return action

    selected = []
    claimed = {
        tuple(positions[index])
        for index, command in enumerate(commands[:len(positions)])
        if command == ["COLLECT_FERTILIZER"]
    }
    for index, (pos, command) in enumerate(zip(positions, commands)):
        if command != ["PASS"]:
            continue
        x, y = pos
        tile = farm["tiles"][y][x]
        if not isinstance(tile, dict) or not tile.get("animal") or not tile.get("fertilizer_available"):
            continue
        if (x, y) in claimed:
            continue
        _STATS["exposed"] += 1
        if occupied + len(selected) + 1 > _MAX_OCCUPANCY:
            _STATS["crowded"] += 1
            continue
        selected.append(index)
        claimed.add((x, y))
        if state["added"] + len(selected) >= _DAILY_LIMIT:
            break
    if not selected:
        return action
    revised = dict(action)
    hands = [list(command) for command in action.get("hands") or []]
    for index in selected:
        if index == 0:
            revised["farmer"] = ["COLLECT_FERTILIZER"]
        elif index - 1 < len(hands):
            hands[index - 1] = ["COLLECT_FERTILIZER"]
    revised["hands"] = hands
    state["added"] += len(selected)
    _STATS["collected"] += len(selected)
    return revised


def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        _STATS.update(exposed=0, collected=0, crowded=0, errors=0)
    action = BASE.agent(observation, configuration)
    try:
        return _spare_collect(observation, action, configuration)
    except Exception:
        _STATS["errors"] += 1
        return action


agent.telemetry = _STATS
kaggle_submission_agent = agent
