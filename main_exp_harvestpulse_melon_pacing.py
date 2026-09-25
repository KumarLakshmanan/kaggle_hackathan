"""Transparent validation wrapper for demand-paced melon sales.

This keeps the production policy intact and only caps its profitable MELON
sell quantity, inspired by the visible-demand pacing idea in
alexandergremyakov/harvest-pulse-goose-dividend-v2.  It uses current public
state (plus the acting player's private inventory) and never identifies a
route, opponent, episode, or seed.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("melon_pacing_base", ROOT / "main.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
try:
    _SPEC.loader.exec_module(_BASE)
except Exception:
    sys.modules.pop(_SPEC.name, None)
    raise
sys.modules.pop(_SPEC.name, None)

_BASE_AGENT = _BASE.agent
_MELON_DEMAND_SHARE = 0.65
_MELON_MATURITY_DAYS = 10
_TELEMETRY = {
    "melon_pace_turns": 0,
    "melon_pace_units_avoided": 0,
    "melon_pace_errors": 0,
}


def _day(observation):
    return max(0, int(observation.get("day", int(observation.get("step", 0)) // 24)))


def _visible_melon_tiles(farm):
    count = 0
    for row in farm.get("tiles", []) or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "MELON"
            ):
                count += 1
    return count


def _next_supply_horizon(observation, own_farm, day):
    waits = []
    for row in own_farm.get("tiles", []) or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "MELON"
            ):
                planted_day = int(tile.get("planted_day", day))
                waits.append(max(1, _MELON_MATURITY_DAYS - (day - planted_day)))
    if waits:
        return min(waits)
    return min(10, max(1, 29 - day))


def _storage_occupancy(observation):
    private = observation.get("private", {}) or {}
    total = 0
    for value in (private.get("shed", {}) or {}).values():
        try:
            total += max(0, int(value))
        except (TypeError, ValueError):
            continue
    for bag in private.get("inventories", []) or []:
        if not isinstance(bag, dict):
            continue
        for value in bag.values():
            try:
                total += max(0, int(value))
            except (TypeError, ValueError):
                continue
    return total


def _paced_cap(observation):
    day = _day(observation)
    demand = 2 * (4 if day >= 20 else 2 if day >= 10 else 1)
    shops = (observation.get("town", {}) or {}).get("unlocked_shops", []) or []
    shop_products = {
        "BAKERY": ("EGG", "WHEAT"),
        "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
        "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
        "YARN_STORE": ("WOOL",),
        "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
        "PET_CAFE": ("CARROT",),
        "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
        "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
    }
    for shop in shops:
        if "MELON" in shop_products.get(shop, ()):
            demand += 12 if len(shop_products[shop]) == 1 else 6

    farms = observation.get("farms", []) or []
    player = int(observation.get("player", 0) or 0)
    own_farm = farms[player] if player < len(farms) else {}
    opponent = farms[1 - player] if len(farms) == 2 else {}
    horizon = _next_supply_horizon(observation, own_farm, day)
    opponent_front_run = min(12, _visible_melon_tiles(opponent))
    paced = math.ceil(demand * horizon * _MELON_DEMAND_SHARE) + opponent_front_run
    headroom_relief = max(0, _storage_occupancy(observation) - 80)
    return max(1, paced, headroom_relief)


def agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        _TELEMETRY.update(
            melon_pace_turns=0,
            melon_pace_units_avoided=0,
            melon_pace_errors=0,
        )
    action = _BASE_AGENT(observation, configuration)
    try:
        step = int(observation.get("step", 0))
        if step // 24 >= 27:
            return action
        market = action.get("market")
        if not isinstance(market, list):
            return action
        total_melon = sum(
            max(0, int(order[2]))
            for order in market
            if isinstance(order, (list, tuple))
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == "MELON"
        )
        cap = _paced_cap(observation)
        if total_melon <= cap:
            return action
        remaining = cap
        rewritten = []
        for order in market:
            if (
                isinstance(order, (list, tuple))
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] == "MELON"
            ):
                quantity = max(0, int(order[2]))
                keep = min(quantity, remaining)
                remaining -= keep
                if keep:
                    rewritten.append(["SELL", "MELON", keep])
            else:
                rewritten.append(list(order) if isinstance(order, tuple) else order)
        _TELEMETRY["melon_pace_turns"] += 1
        _TELEMETRY["melon_pace_units_avoided"] += total_melon - cap
        return dict(action, market=rewritten)
    except Exception:
        _TELEMETRY["melon_pace_errors"] += 1
        return action


agent.telemetry = _TELEMETRY
