"""Diagnostic wrapper testing a capacity-capped, observation-only premium hold.

This wrapper delegates production and routing to the frozen main.py, then
reduces existing SELL quantities only.  It never reads a route, episode ID,
seed, future shop draw, or opponent-private state.  It is not a submission.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import main as _base


BASE_PRICE = {"STRAWBERRY": 120, "MELON": 250, "MILK": 160, "WOOL": 200}
RESERVE_TARGET = {"STRAWBERRY": 40, "MELON": 2, "MILK": 8, "WOOL": 8}
SHOP_DEMAND = {
    "STRAWBERRY": frozenset(("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")),
    "MELON": frozenset(),
    "MILK": frozenset(("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP")),
    "WOOL": frozenset(("YARN_STORE",)),
}
SHED_CAPACITY = 100
CAPACITY_BUFFER = 8
FLUSH_HOUR = 21
FINAL_RELEASE_STEP = 718

_HOLDING = {0: set(), 1: set()}
_REPORT: dict[str, Any] = {}


def _reset() -> None:
    _HOLDING[0].clear()
    _HOLDING[1].clear()
    _REPORT.clear()
    _REPORT.update(
        calls=0,
        low_demand_triggers=0,
        hold_decisions=0,
        held_units_by_product={item: 0 for item in BASE_PRICE},
        capacity_limited_decisions=0,
        flush_window_decisions=0,
        price_releases=0,
        final_releases=0,
        modified_orders=0,
    )


_reset()


def _counts(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): max(0, int(count or 0)) for key, count in value.items()}


def _harvest_units(observation: Mapping[str, Any], action: Mapping[str, Any]) -> int:
    farms = observation.get("farms", [])
    seat = int(observation.get("player", 0) or 0)
    if not isinstance(farms, list) or not 0 <= seat < len(farms):
        return 0
    farm = farms[seat] if isinstance(farms[seat], Mapping) else {}
    tiles = farm.get("tiles", []) or []
    positions = [farm.get("farmer"), *(farm.get("hands", []) or [])]
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    total = 0
    for actor, command in enumerate(commands):
        if actor >= len(positions) or not isinstance(command, (list, tuple)) or not command or command[0] != "HARVEST":
            continue
        position = positions[actor]
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            continue
        x, y = int(position[0]), int(position[1])
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
            tile = tiles[y][x]
            if isinstance(tile, Mapping):
                total += max(0, int(tile.get("yield_units", 0) or 0))
    return total


def _sell_reservations(market: list[Any], shed: Mapping[str, Any]) -> tuple[int, dict[str, int]]:
    remaining = _counts(shed)
    total = 0
    by_product: dict[str, int] = {}
    for order in market:
        if not isinstance(order, (list, tuple)) or len(order) < 3 or order[0] != "SELL":
            continue
        item = str(order[1])
        quantity = max(0, int(order[2] or 0))
        committed = min(quantity, remaining.get(item, 0))
        remaining[item] = remaining.get(item, 0) - committed
        total += committed
        by_product[item] = by_product.get(item, 0) + committed
    return total, by_product


def agent(observation: Mapping[str, Any], configuration: Any = None) -> Any:
    step = int(observation.get("step", -1)) if isinstance(observation, Mapping) else -1
    seat = int(observation.get("player", 0) or 0) if isinstance(observation, Mapping) else 0
    if step == 0:
        _reset()
    _REPORT["calls"] += 1

    action = _base.agent(observation, configuration)
    if not isinstance(observation, Mapping) or not isinstance(action, Mapping):
        return action
    market = action.get("market") or []
    if not isinstance(market, list):
        return action

    town = observation.get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])
    prices = ((observation.get("market", {}) or {}).get("prices", {}) or {})
    private = observation.get("private", {}) or {}
    shed = _counts(private.get("shed", {}) or {})
    inventories = private.get("inventories", []) or []
    carried = sum(_counts(inventory or {}).get(item, 0) for inventory in inventories for item in (inventory or {}))
    shed_total = sum(shed.values())

    held: set[str] = _HOLDING.setdefault(seat, set())
    for item, base in BASE_PRICE.items():
        consumers = sum(shop in SHOP_DEMAND[item] for shop in shops)
        current_price = max(0, int(prices.get(item, 0) or 0))
        if item in held and current_price >= base:
            held.remove(item)
            _REPORT["price_releases"] += 1
        elif item not in held and consumers <= 1 and current_price > 0 and current_price < base:
            held.add(item)
            _REPORT["low_demand_triggers"] += 1

    if step >= FINAL_RELEASE_STEP:
        if held:
            _REPORT["final_releases"] += len(held)
        held.clear()
        return action

    if step % 24 >= FLUSH_HOUR:
        _REPORT["flush_window_decisions"] += int(bool(held))
        return action
    if not held:
        return action

    baseline_sell_units, sell_by_product = _sell_reservations(market, shed)
    harvest = _harvest_units(observation, action)
    capacity_budget = max(
        0,
        SHED_CAPACITY
        - max(0, shed_total - baseline_sell_units)
        - carried
        - harvest
        - CAPACITY_BUFFER,
    )
    if capacity_budget <= 0:
        _REPORT["capacity_limited_decisions"] += 1
        return action

    result = deepcopy(dict(action))
    adjusted_market = [list(order) if isinstance(order, (list, tuple)) else order for order in market]
    for item in ("STRAWBERRY", "WOOL", "MILK", "MELON"):
        if item not in held or sell_by_product.get(item, 0) <= 0:
            continue
        base_sold = sell_by_product[item]
        stock_left = max(0, shed.get(item, 0) - base_sold)
        desired_hold = max(0, min(RESERVE_TARGET[item], shed.get(item, 0)) - stock_left)
        actual_hold = min(desired_hold, capacity_budget)
        if actual_hold <= 0:
            if desired_hold:
                _REPORT["capacity_limited_decisions"] += 1
            continue
        capacity_budget -= actual_hold
        remaining_hold = actual_hold
        for index in range(len(adjusted_market) - 1, -1, -1):
            order = adjusted_market[index]
            if not isinstance(order, list) or len(order) < 3 or order[0] != "SELL" or order[1] != item:
                continue
            quantity = max(0, int(order[2] or 0))
            reduction = min(quantity, remaining_hold)
            if reduction:
                order[2] = quantity - reduction
                remaining_hold -= reduction
                if order[2] <= 0:
                    adjusted_market.pop(index)
                if remaining_hold <= 0:
                    break
        _REPORT["hold_decisions"] += 1
        _REPORT["held_units_by_product"][item] += actual_hold
        _REPORT["modified_orders"] += 1

    result["market"] = adjusted_market
    return result


agent.telemetry = _REPORT
kaggle_submission_agent = agent
