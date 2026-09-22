"""Benchmark-only V49 market overlay on the current main trajectory."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V49_PATH = ROOT / "kaggle_complete_agents_2026-09-21" / (
    "ahmedberatozer__kaggriculture-v49-funded-sale-timing-and-worker__2916b93119a2.py"
)
_SWITCH_STEP = 360


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("market_overlay_main", ROOT / "main.py")
_V49 = _load("market_overlay_v49", V49_PATH)
_LAST_STEP = {}
_ROUTE = {}


def _signature(farm):
    counts = {}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return int(round(float(farm.get("money", 0) or 0))), len(farm.get("hands", []) or []), counts


def _route(observation):
    player = int((observation or {}).get("player", 0) or 0)
    step = int((observation or {}).get("step", 0) or 0)
    previous = _LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _ROUTE[player] = None
    _LAST_STEP[player] = step
    if step == 72:
        farms = list((observation or {}).get("farms", []) or [])
        shops = tuple(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
        if len(farms) == 2:
            opponent = _signature(farms[1 - player])[2]
            if shops == ("BRUNCH_SPOT",):
                _ROUTE[player] = "brunch"
            elif shops == ("PET_CAFE",):
                _ROUTE[player] = "otter" if opponent.get("GOOSE", 0) >= 1 else "pet"
            elif shops == ("YARN_STORE",):
                _ROUTE[player] = "third"
    return _ROUTE.get(player)


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    v49_action = _V49.agent(observation, configuration)
    route = _route(observation)
    step = int((observation or {}).get("step", 0) or 0)
    if route in {"brunch", "otter"} and step >= int(_SWITCH_STEP):
        result = copy.deepcopy(main_action)
        result["market"] = copy.deepcopy(v49_action.get("market") or [])
        return result
    return copy.deepcopy(main_action)
