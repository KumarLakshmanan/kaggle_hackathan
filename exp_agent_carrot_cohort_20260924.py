"""Experimental, observation-legal day-11 carrot cohort instead of strawberry.

This is a local candidate, not a Kaggle submission. It reuses the parent's
worker paths and acts only on observed plants, seeds, shops and shed stock.
No opponent identity, replay outcome, seed, or future shop is consulted.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SPEC = importlib.util.spec_from_file_location(__name__ + "_base", Path(__file__).with_name("main.py"))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot load main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_MAX_SWAP = 13
_MIN_CARROT_QUOTE = 35
_ALLOW_REPLANT = False
_DEST_CROP = "CARROT"  # Controlled alternatives: WHEAT, NONE.
_HARVEST_AGE = 3
_ROUTE_OVERRIDE = -1  # Diagnostic only; selected from the visible first two shops.
_ORIGINAL_ROUTE = _BASE._R108_SHOP_ROUTES[("ICE_CREAM_SHOP", "BAKERY")]
_STATES: dict[int, dict] = {}
_STATS = dict(seed_swaps=0, initial_plants=0, replants=0, harvests=0,
              seed_topups=0, carrot_sales=0, errors=0)


def _standard(config) -> bool:
    cfg = config if hasattr(config, "get") else {}
    return all(int(cfg.get(key, default)) == default for key, default in (
        ("boardSize", 10), ("turnsPerDay", 24), ("episodeSteps", 720),
        ("shedCapacity", 100), ("maxMarketOrdersPerTurn", 10),
    )) and not cfg.get("marketParams")


def _reset(seat: int, step: int) -> dict:
    previous = _STATES.get(seat)
    if previous is None or step == 0 or step <= previous["last_step"]:
        previous = dict(last_step=-1, committed=False, swapped=0, pending=0,
                        sites=set(), topup_day=-1)
        _STATES[seat] = previous
        if step == 0:
            for key in _STATS:
                _STATS[key] = 0
    previous["last_step"] = step
    return previous


def _adapt(observation: dict, action: dict, config, state: dict) -> dict:
    step = int(observation["step"])
    day = step // 24
    seat = int(observation["player"])
    shops = list((observation.get("town") or {}).get("unlocked_shops") or [])
    market_state = observation.get("market") or {}
    prices = market_state.get("prices") or {}
    if day == 11 and not state["committed"]:
        if ("PET_CAFE" in shops and "YARN_STORE" not in shops
                and float(prices.get("CARROT", 0)) >= _MIN_CARROT_QUOTE):
            state["committed"] = True
    if not state["committed"]:
        return action

    market = [list(order) for order in action.get("market") or []]
    farmer = list(action.get("farmer") or ["PASS"])
    hands = [list(command) for command in action.get("hands") or []]
    commands = [farmer, *hands]
    farm = observation["farms"][seat]
    positions = [farm["farmer"], *(farm.get("hands") or [])]
    tiles = farm["tiles"]
    private = observation.get("private") or {}
    seeds = private.get("seeds") or {}
    available = max(0, int(seeds.get(_DEST_CROP, 0))) if _DEST_CROP != "NONE" else 0
    # Preserve seeds used by the parent's own carrot actions on this turn.
    reserved = sum(command[:2] == ["PLANT", _DEST_CROP] for command in commands)
    free = max(0, available - reserved)
    changed = False

    if day == 11 and state["swapped"] < _MAX_SWAP:
        revised_market = []
        for order in market:
            if (len(order) == 3 and order[:2] == ["BUY_SEED", "STRAWBERRY"]
                    and 0 < int(order[2]) <= _MAX_SWAP - state["swapped"]):
                quantity = int(order[2])
                if _DEST_CROP != "NONE":
                    order[1] = _DEST_CROP
                    # The optional second cohort is funded at the same order.
                    order[2] = (2 if _ALLOW_REPLANT else 1) * quantity
                state["swapped"] += quantity
                state["pending"] += quantity
                _STATS["seed_swaps"] += quantity
                changed = True
                if _DEST_CROP == "NONE":
                    continue
            revised_market.append(order)
        market = revised_market

    for actor, (pos, command) in enumerate(zip(positions, commands)):
        site = (int(pos[0]), int(pos[1]))
        tile = tiles[site[1]][site[0]]
        if (day <= 13 and state["pending"] > 0
                and command[:2] == ["PLANT", "STRAWBERRY"] and tile is None):
            if _DEST_CROP == "NONE":
                command[:] = ["PASS"]
                state["pending"] -= 1
                changed = True
                continue
            if free > 0:
                command[:] = ["PLANT", _DEST_CROP]
                state["sites"].add(site)
                state["pending"] -= 1
                free -= 1
                _STATS["initial_plants"] += 1
                changed = True
                continue
        if site not in state["sites"] or command[:1] not in (["WATER"], ["HARVEST"]):
            continue
        if isinstance(tile, dict) and tile.get("crop") == _DEST_CROP:
            planted = int(tile.get("planted_day", day))
            if day - planted >= _HARVEST_AGE and int(tile.get("yield_units", 0)) > 0:
                if command != ["HARVEST"]:
                    command[:] = ["HARVEST"]
                    changed = True
                _STATS["harvests"] += 1
            elif command != ["WATER"] and not tile.get("watered_today"):
                command[:] = ["WATER"]
                changed = True
        elif _ALLOW_REPLANT and tile is None and day <= 24 and free > 0:
            command[:] = ["PLANT", _DEST_CROP]
            free -= 1
            _STATS["replants"] += 1
            changed = True

    if (_ALLOW_REPLANT and day >= 15 and day <= 23 and state["sites"]
            and state["topup_day"] != day):
        # Refill only as the converted plots consume their reserve, and never
        # put new purchases before the parent's spending priorities.
        if available <= 4 and len(market) < 10:
            qty = min(len(state["sites"]), 13)
            money = float(farm.get("money", 0))
            cost = 10 if _DEST_CROP == "WHEAT" else 20
            if money >= 300 + cost * qty:
                market.append(["BUY_SEED", _DEST_CROP, qty])
                state["topup_day"] = day
                _STATS["seed_topups"] += qty
                changed = True

    if state["sites"] and _DEST_CROP == "CARROT":
        shed = private.get("shed") or {}
        stock = max(0, int(shed.get("CARROT", 0)))
        already = sum(int(order[2]) for order in market
                      if len(order) == 3 and order[:2] == ["SELL", "CARROT"])
        if stock > already and len(market) < 10:
            market.append(["SELL", "CARROT", stock - already])
            _STATS["carrot_sales"] += stock - already
            changed = True

    if not changed:
        return action
    return dict(action, farmer=farmer, hands=hands, market=market)


def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        _BASE._R108_SHOP_ROUTES[("ICE_CREAM_SHOP", "BAKERY")] = (
            _ROUTE_OVERRIDE if _ROUTE_OVERRIDE >= 0 else _ORIGINAL_ROUTE
        )
    action = _BASE.agent(observation, configuration)
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return action
    step = int(observation.get("step", -1))
    seat = int(observation.get("player", 0))
    state = _reset(seat, step)
    if step < 0 or not _standard(configuration):
        return action
    try:
        return _adapt(observation, action, configuration, state)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        _STATS["errors"] += 1
        return action


agent.telemetry = _STATS
kaggle_submission_agent = agent
