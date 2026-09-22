"""Experimental livestock-mix wrapper; never used for Kaggle submission.

When the current policy requests a cow, but already has spare pasture and is
behind the visible opponent in sheep, test redirecting that single purchase
to a sheep. This isolates the composition signal seen in recent loss traces.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_v57_base_main", _ROOT / "main.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load main.py")
_BASE_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE_MODULE)
_BASE_AGENT = _BASE_MODULE.agent


def _animal_count(farm: dict[str, Any], animal: str) -> int:
    count = 0
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if isinstance(tile, dict) and tile.get("animal") == animal:
                count += 1
    return count


def _empty_pastures(farm: dict[str, Any]) -> int:
    count = 0
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PASTURE"
                and not tile.get("animal")
            ):
                count += 1
    return count


def _owned_sheep(obs: dict[str, Any], player: int, farm: dict[str, Any]) -> int:
    total = _animal_count(farm, "SHEEP")
    private_rows = obs.get("private", []) or []
    private = (
        private_rows[player]
        if isinstance(private_rows, list) and player < len(private_rows)
        else {}
    )
    total += int((private.get("shed", {}) or {}).get("SHEEP", 0) or 0)
    for inventory in private.get("inventories", []) or []:
        total += int((inventory or {}).get("SHEEP", 0) or 0)
    return total


def agent(observation, configuration=None):
    action = _BASE_AGENT(observation, configuration)
    if not isinstance(action, dict):
        return action

    player = int(observation.get("player", 0) or 0)
    farms = list(observation.get("farms", []) or [])
    if len(farms) != 2 or player not in (0, 1):
        return action
    farm = farms[player]
    opponent = farms[1 - player]
    step = int(observation.get("step", 0) or 0)
    own_sheep = _owned_sheep(observation, player, farm)
    opponent_sheep = _animal_count(opponent, "SHEEP")
    target_sheep = min(6, max(4, opponent_sheep))
    spare_pastures = _empty_pastures(farm)
    remaining_turns = 719 - step
    stock = int(
        ((observation.get("market", {}) or {}).get("inventory", {}) or {}).get(
            "SHEEP", 0
        )
        or 0
    )
    money = float(farm.get("money", 0) or 0)

    if spare_pastures < 1 or remaining_turns < 160 or stock < 1:
        return action

    orders = action.get("market")
    if not isinstance(orders, list):
        return action
    redirected = []
    for order in orders:
        if (
            isinstance(order, (list, tuple))
            and len(order) >= 2
            and order[0] == "BUY_ANIMAL"
            and order[1] == "COW"
            and own_sheep < target_sheep
            and money >= 500
            and stock >= 1
        ):
            quantity = int(order[2]) if len(order) >= 3 else 1
            if quantity == 1:
                redirected.append(["BUY_ANIMAL", "SHEEP", 1])
                own_sheep += 1
                money -= 500
                stock -= 1
                continue
        redirected.append(list(order) if isinstance(order, tuple) else order)

    action["market"] = redirected
    return action


agent.telemetry = {"router": "v57-sheep-capacity-guard"}
