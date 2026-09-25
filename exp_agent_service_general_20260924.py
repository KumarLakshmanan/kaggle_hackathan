"""Observation-legal day-end wheat service float over unchanged main.py.

One predeclared generalization: on any productive day-end with an existing
BUY_PRODUCT WHEAT, fund a next-morning lead pickup that is smaller than the
lead's remaining FEED schedule.  The parent action, its own selected route,
and the current observation are the only inputs.  Extra wheat is bought only
when a conservative cash and shed projection covers every other order; the
pickup is enlarged only after the next observation confirms the expected own
route, commands, and enough shed wheat for all simultaneous hand pickups.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PARENT_PATH = Path(__file__).resolve().with_name("main.py")
_PARENT_NAME = __name__ + "_unchanged_main"
_PARENT_SPEC = importlib.util.spec_from_file_location(_PARENT_NAME, _PARENT_PATH)
if _PARENT_SPEC is None or _PARENT_SPEC.loader is None:
    raise RuntimeError("Cannot load unchanged main.py")
_PARENT = importlib.util.module_from_spec(_PARENT_SPEC)
sys.modules[_PARENT_NAME] = _PARENT
_PARENT_SPEC.loader.exec_module(_PARENT)

_SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
_ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
_PRODUCT_MAX = {item: max(_PARENT._h6_market_price(item, 0), _PARENT._H6_MARKET_PARAMS[item][0])
                for item in ("WHEAT", "FERTILIZER")}
_LAND_COST = (1000, 2000, 4000)
_REPORT = {
    "service_float_buys": 0,
    "service_float_units": 0,
    "service_pickups": 0,
    "service_pickup_units": 0,
    "service_aborts": 0,
    "service_cash_skips": 0,
    "service_shed_skips": 0,
    "service_errors": 0,
    "service_trigger_steps": "",
    "service_abort_steps": "",
}
_ARMED: dict[int, dict] = {}


def _quantity(command) -> int:
    return int(command[2]) if len(command) > 2 else 1


def _route(seat: int, step: int):
    native = _PARENT._IMPL.chassis.players.get(seat)
    if native is None:
        return None, None
    route_id = 2 if step >= 648 else native["route"]
    return route_id, _PARENT._IMPL.chassis.routes[route_id]


def _next_morning_plan(seat: int, step: int):
    dawn = step + 1
    pickup_step = dawn + 1
    if pickup_step > 718 or dawn // 24 >= 29:
        return None
    # A new shop can change the parent router at dawn.  Do not buy against
    # an unobserved future shop draw; all eight shops are known after day 24.
    next_day = dawn // 24
    if next_day <= 24 and next_day % 3 == 0:
        return None
    route_id, tape = _route(seat, pickup_step)
    if tape is None or pickup_step >= len(tape):
        return None
    first = tape[pickup_step]
    lead = first.get("farmer") or []
    if lead[:2] != ["PICKUP", "WHEAT"]:
        return None
    planned_pickup = _quantity(lead)
    feeds = 0
    for t in range(pickup_step + 1, min(dawn + 24, len(tape))):
        command = tape[t].get("farmer") or []
        if command[:2] == ["PICKUP", "WHEAT"]:
            break
        if command[:1] == ["FEED"]:
            feeds += 1
    if feeds <= planned_pickup:
        return None
    other = sum(_quantity(command) for command in first.get("hands", [])
                if command[:2] == ["PICKUP", "WHEAT"])
    return {"buy_step": step, "pickup_step": pickup_step, "route_id": route_id,
            "planned_pickup": planned_pickup, "lead_need": feeds, "other_need": other}


def _post_unit_private(observation: dict, action: dict):
    seat = int(observation["player"])
    farm, private = _PARENT._PLANNER_NS["_clone_state"](
        observation["farms"][seat], observation["private"]
    )
    positions = [farm["farmer"]] + list(farm["hands"])
    commands = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    for actor, command in enumerate(commands[:len(positions)]):
        _PARENT._PLANNER_NS["_apply_unit_action"](
            farm, private, actor, command, 10, int(observation["step"]) // 24, 24, 100
        )
    return farm, private


def _market_projection(observation: dict, action: dict, private: dict):
    """Lower-bound next-dawn wheat and upper-bound cash/storage obligations."""
    farm = observation["farms"][int(observation["player"])]
    market = action.get("market") or []
    if len(market) > 10:
        return None
    wheat = int(private["shed"].get("WHEAT", 0))
    wheat += sum(int(inv.get("WHEAT", 0)) for inv in private["inventories"])
    stock = sum(int(q) for q in private["shed"].values())
    stock += sum(sum(int(q) for q in inv.values()) for inv in private["inventories"])
    worst_cost = 0
    hires = int(farm.get("hires_today", 0))
    land = len(farm.get("unlocked_quadrants") or [])
    wheat_buy_indices = []
    for index, order in enumerate(market):
        if not order:
            continue
        op = order[0]
        if op in ("BUY_PRODUCT", "BUY_ANIMAL", "BUY_SEED", "SELL"):
            if len(order) < 3 or int(order[2]) < 0:
                return None
            item, qty = order[1], int(order[2])
            if op == "BUY_PRODUCT":
                if item not in _PRODUCT_MAX:
                    return None
                stock += qty
                worst_cost += qty * _PRODUCT_MAX[item]
                if item == "WHEAT":
                    wheat += qty
                    wheat_buy_indices.append(index)
            elif op == "BUY_ANIMAL":
                if item not in _ANIMAL_COST:
                    return None
                stock += qty
                worst_cost += qty * _ANIMAL_COST[item]
            elif op == "BUY_SEED":
                if item not in _SEED_COST:
                    return None
                worst_cost += qty * _SEED_COST[item]
            elif item == "WHEAT":
                # Subtract the whole request even if it may not execute: this
                # cannot overstate wheat available at tomorrow's pickup.
                wheat -= qty
        elif op == "HIRE":
            worst_cost += _PARENT._v219_fib(hires)
            hires += 1
        elif op == "BUY_LAND":
            if land < 4:
                worst_cost += _LAND_COST[land - 1]
                land += 1
        else:
            return None
    if len(wheat_buy_indices) != 1:
        return None
    return max(0, wheat), stock, worst_cost, wheat_buy_indices[0]


def _day_end(observation: dict, action: dict) -> dict:
    step = int(observation["step"])
    seat = int(observation["player"])
    plan = _next_morning_plan(seat, step)
    if plan is None:
        return action
    _, private = _post_unit_private(observation, action)
    projected = _market_projection(observation, action, private)
    if projected is None:
        return action
    wheat, stock, worst_cost, buy_index = projected
    deficit = plan["lead_need"] + plan["other_need"] - wheat
    if deficit <= 0:
        return action
    if stock + deficit > 100:
        _REPORT["service_shed_skips"] += 1
        return action
    money = float(observation["farms"][seat]["money"])
    if money < worst_cost + deficit * _PRODUCT_MAX["WHEAT"]:
        _REPORT["service_cash_skips"] += 1
        return action
    market = [list(order) for order in action.get("market", [])]
    market[buy_index][2] = int(market[buy_index][2]) + deficit
    _ARMED[seat] = plan
    _REPORT["service_float_buys"] += 1
    _REPORT["service_float_units"] += deficit
    return dict(action, market=market)


def _pickup(observation: dict, action: dict, plan: dict) -> dict:
    seat = int(observation["player"])
    step = int(observation["step"])
    _ARMED.pop(seat, None)
    route_id, tape = _route(seat, step)
    farmer = list(action.get("farmer") or [])
    actual_other = sum(_quantity(command) for command in action.get("hands", [])
                       if command[:2] == ["PICKUP", "WHEAT"])
    carried = int(observation["private"]["inventories"][0].get("WHEAT", 0))
    wanted = max(plan["planned_pickup"], plan["lead_need"] - carried)
    shed = int(observation["private"]["shed"].get("WHEAT", 0))
    valid = (
        route_id == plan["route_id"] and tape is not None
        and farmer[:2] == ["PICKUP", "WHEAT"]
        and _quantity(farmer) == plan["planned_pickup"]
        and carried == 0
        and actual_other == plan["other_need"]
        and wanted > _quantity(farmer)
        and shed >= wanted + actual_other
    )
    if not valid:
        _REPORT["service_aborts"] += 1
        _REPORT["service_abort_steps"] += ("," if _REPORT["service_abort_steps"] else "") + str(step)
        return action
    _REPORT["service_pickups"] += 1
    _REPORT["service_pickup_units"] += wanted - _quantity(farmer)
    _REPORT["service_trigger_steps"] += (
        ("," if _REPORT["service_trigger_steps"] else "")
        + str(plan["buy_step"]) + ">" + str(step)
    )
    return dict(action, farmer=["PICKUP", "WHEAT", wanted])


def agent(observation, configuration=None):
    step = int(observation.get("step", -1))
    seat = int(observation.get("player", 0))
    if step == 0:
        _ARMED.clear()
        for key in _REPORT:
            _REPORT[key] = "" if key.endswith("_steps") else 0
    action = _PARENT.agent(observation, configuration)
    try:
        cfg = configuration if hasattr(configuration, "get") else {}
        if any(int(cfg.get(key, default)) != default for key, default in (
            ("turnsPerDay", 24), ("boardSize", 10), ("shedCapacity", 100),
            ("maxMarketOrdersPerTurn", 10), ("episodeSteps", 720),
        )) or cfg.get("marketParams"):
            return action
        if not isinstance(action, dict):
            return action
        pending = _ARMED.get(seat)
        if pending is not None:
            if step == pending["pickup_step"]:
                return _pickup(observation, action, pending)
            if step > pending["pickup_step"]:
                _ARMED.pop(seat, None)
                _REPORT["service_aborts"] += 1
                _REPORT["service_abort_steps"] += ("," if _REPORT["service_abort_steps"] else "") + str(step)
        if step >= 0 and step % 24 == 23:
            return _day_end(observation, action)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        _REPORT["service_errors"] += 1
    return action


agent.telemetry = _REPORT
