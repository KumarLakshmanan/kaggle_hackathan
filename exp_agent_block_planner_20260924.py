"""Observation-legal, bounded lanes of a four-site crop-block experiment.

This is deliberately NOT a Kaggle submission.  It imports the frozen policy
and changes only crop lanes for which a complete worker/seed/shed calendar is
certified from the policy's *own* route tape.  Four naturally available
south-west sites form a candidate block.  The two outer sites remain with
the incumbent: on the observed route their post-harvest replant-and-water
cycles would steal non-idle work from the other crop/animal crews.

No replay identity, score, seed, opponent state, or future shop is read.  The
selected crop uses current market inventory, current unlocked-shop demand and
visible plant count to estimate net receipts at the planned delivery dates.
If any precondition fails, the parent action is returned unchanged.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SPEC = importlib.util.spec_from_file_location(__name__ + "_base", Path(__file__).with_name("main.py"))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot import frozen main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_BLOCK = ((4, 5), (4, 6), (3, 5), (3, 6))
_LANE = _BLOCK[0]  # the only tile with a certified complete rotation calendar
_SECOND_LANE = _BLOCK[1]
_SEED_COST = {"STRAWBERRY": 100, "CARROT": 20, "WHEAT": 10}
_CROP_OPTIONS = ("CARROT", "WHEAT")
_MENU_MODE = 0  # 0=observation-priced menu, 1=carrot-only, 2=wheat-only ablation
_ENABLE_SECOND_LANE = False  # isolated two-lane physical-calendar experiment
_MAX_MARKET_ORDERS = 10
_MIN_EXPECTED_ADVANTAGE = 50.0
_STATES: dict[int, dict] = {}
_STATS = dict(menu_checks=0, committed=0, initial_plants=0, rotations=0,
              watered_after_plant=0, harvests=0, deposited=0, sold=0,
              second_lane_plants=0, second_lane_harvests=0,
              second_lane_sales=0, unsupported=0, mismatches=0, errors=0,
              chosen="")


def _standard(configuration) -> bool:
    cfg = configuration if hasattr(configuration, "get") else {}
    return (int(cfg.get("boardSize", 10)) == 10
            and int(cfg.get("turnsPerDay", 24)) == 24
            and int(cfg.get("episodeSteps", 720)) == 720
            and int(cfg.get("shedCapacity", 100)) == 100
            and int(cfg.get("maxMarketOrdersPerTurn", 10)) == 10
            and not cfg.get("marketParams"))


def _state(seat: int, step: int) -> dict:
    st = _STATES.get(seat)
    if st is None or step == 0 or step < st["last_step"]:
        st = {"last_step": -1, "crop": None, "first_actor": None,
              "day14_actor": None, "day16_actor": None,
              "first_planted": False, "second_planted": False,
              "second_funded": False, "day14_started": False,
              "day16_started": False, "stopped": False,
              "second_lane": False, "lane2_first_planted": False,
              "lane2_second_planted": False, "lane2_first_harvested": False,
              "lane2_sale_pending": 0, "lane2_late_harvested": False,
              "projection": None}
        _STATES[seat] = st
        if step == 0:
            for k, v in _STATS.items():
                _STATS[k] = "" if isinstance(v, str) else 0
    st["last_step"] = step
    return st


def _worker_data(observation, action):
    farm = observation["farms"][int(observation["player"])]
    positions = [tuple(farm["farmer"]), *(tuple(p) for p in farm.get("hands") or [])]
    commands = [list(action.get("farmer") or ["PASS"]),
                *(list(c) for c in action.get("hands") or [])]
    return farm, positions, commands


def _change_worker(action: dict, index: int, command: list) -> dict:
    result = dict(action)
    if index == 0:
        result["farmer"] = command
    else:
        hands = [list(c) for c in action.get("hands") or []]
        hands[index - 1] = command
        result["hands"] = hands
    return result


def _owned_tape(observation):
    # Our own committed policy tape is known at decision time.  This is not a
    # simulator or opponent forecast, and it contains no future-shop draws.
    seat = int(observation["player"])
    native = _BASE._IMPL.chassis.players.get(seat)
    if not native:
        return None
    return _BASE._IMPL.chassis.routes.get(native.get("route"))


def _tape_worker(tape, step: int, index: int) -> list:
    a = tape[step]
    if index == 0:
        return a.get("farmer") or ["PASS"]
    hands = a.get("hands") or []
    return hands[index - 1] if index - 1 < len(hands) else ["PASS"]


def _calendar_ok(tape, day: int, index: int) -> bool:
    if tape is None:
        return False
    if day == 14:
        expected = {
            2: ["WATER"], 3: ["SOUTH"],
            4: ["PASS"], 5: ["PASS"], 6: ["PASS"],
            7: ["PASS"], 8: ["PASS"], 9: ["PASS"],
            10: ["WATER"], 11: ["SOUTH"],
        }
    elif day == 16:
        expected = {
            1: ["WEST"], 2: ["EAST"], 3: ["SOUTH"],
            4: ["WATER"], 5: ["SOUTH"], 6: ["WATER"],
            7: ["WEST"],
        }
    else:
        return False
    return all(_tape_worker(tape, day * 24 + hour, index) == command
               for hour, command in expected.items())


def _crop_projection(observation: dict) -> tuple[str | None, dict]:
    """Compare two delivered two-cycle crops to a visible strawberry cohort.

    The price projection keeps only currently unlocked shop demand and the
    *visible* existing strawberry field.  Future shops are not predicted.
    It is intentionally conservative about any unobserved future production.
    """
    _STATS["menu_checks"] += 1
    farm = observation["farms"][int(observation["player"])]
    prices = observation["market"]["prices"]
    market_inventory = observation["market"]["inventory"]
    plants = sum(isinstance(t, dict) and t.get("crop") == "STRAWBERRY"
                 for row in farm["tiles"] for t in row)
    from_day = int(observation["step"]) // 24
    price_at = {}
    for crop in ("STRAWBERRY", *_CROP_OPTIONS):
        demand = _BASE._h6_demand_per_day(observation, None, crop)
        price_at[crop] = {}
        for delivery_day in (14, 16, 21, 23):
            days = max(0, delivery_day - from_day)
            inventory = int(market_inventory.get(crop, 10000)) - demand * days
            if crop == "STRAWBERRY":
                # A visible, already-planted cohort matures by the first
                # strawberry delivery.  Two units per tile per day is the
                # deliberately lower, not maximal, production assumption.
                inventory += plants * max(0, delivery_day - 16) * 2
            price_at[crop][delivery_day] = max(1, _BASE._h6_market_price(crop, inventory))
    incumbent = (4 * price_at["STRAWBERRY"][21]
                 + 4 * price_at["STRAWBERRY"][23]
                 - _SEED_COST["STRAWBERRY"])
    scores = {"incumbent": incumbent, "defer": 0.0}
    for crop in _CROP_OPTIONS:
        # Two guaranteed units at each planned, in-shift HARVEST.  Unit
        # actions occur before the same-turn DROP and SELL market order.
        scores[crop] = (2 * price_at[crop][14]
                        + 2 * price_at[crop][16]
                        - 2 * _SEED_COST[crop])
    options = ("CARROT",) if _MENU_MODE == 1 else (("WHEAT",) if _MENU_MODE == 2 else _CROP_OPTIONS)
    best = max(options, key=lambda crop: scores[crop])
    choice = best if scores[best] >= max(incumbent, 0) + _MIN_EXPECTED_ADVANTAGE else None
    available_sites = [xy for xy in _BLOCK if farm["tiles"][xy[1]][xy[0]] is None]
    block_plan = {
        f"{x},{y}": (choice if (x, y) == _LANE and choice else
                     "WHEAT" if (x, y) == _SECOND_LANE and _ENABLE_SECOND_LANE
                     and choice == "WHEAT" else "INCUMBENT")
        if (x, y) in available_sites else "DEFER"
        for x, y in _BLOCK
    }
    return choice, {"scores": scores, "prices": price_at, "visible_strawberries": plants,
                    "shops": list(observation["town"]["unlocked_shops"]),
                    "available_sites": available_sites, "block_plan": block_plan}


def _sell_new_delivery(observation, action: dict, worker: int, crop: str) -> dict:
    private = observation["private"]
    inventory = private["inventories"][worker]
    carried = max(0, int(inventory.get(crop, 0)))
    shed = private["shed"]
    room = max(0, 100 - sum(max(0, int(q)) for q in shed.values()))
    deliverable = min(carried, room)
    if deliverable <= 0:
        return action
    market = [list(o) for o in action.get("market") or []]
    if len(market) >= _MAX_MARKET_ORDERS:
        return action
    # Sell only this lane's newly delivered units.  In particular, never
    # consume the parent's WHEAT reserve that feeds livestock.
    market.append(["SELL", crop, deliverable])
    _STATS["deposited"] += deliverable
    _STATS["sold"] += deliverable
    return dict(action, market=market)


def _sell_overnight_increment(observation, action: dict, st: dict) -> dict:
    """Sell only the recorded extra units after the engine's midnight deposit."""
    pending = int(st["lane2_sale_pending"])
    if pending <= 0 or int(observation["market"]["prices"].get("WHEAT", 0)) <= 1:
        return action
    market = [list(o) for o in action.get("market") or []]
    if len(market) >= _MAX_MARKET_ORDERS:
        return action
    stock = max(0, int(observation["private"]["shed"].get("WHEAT", 0)))
    parent_sales = sum(max(0, int(o[2])) for o in market
                       if len(o) >= 3 and o[:2] == ["SELL", "WHEAT"])
    qty = min(pending, max(0, stock - parent_sales))
    if qty <= 0:
        return action
    market.append(["SELL", "WHEAT", qty])
    st["lane2_sale_pending"] -= qty
    _STATS["second_lane_sales"] += qty
    return dict(action, market=market)


def _adapt(observation, action: dict, st: dict) -> dict:
    step = int(observation["step"])
    day, hour = divmod(step, 24)
    farm, positions, commands = _worker_data(observation, action)
    private = observation["private"]
    tiles = farm["tiles"]
    site = tiles[_LANE[1]][_LANE[0]]
    lane2 = tiles[_SECOND_LANE[1]][_SECOND_LANE[0]]

    if day == 11 and hour == 2 and not st["crop"]:
        shops = list(observation["town"]["unlocked_shops"])
        approaching = [i for i, (pos, cmd) in enumerate(zip(positions, commands))
                       if pos == (5, 5) and cmd == ["WEST"]]
        market = [list(o) for o in action.get("market") or []]
        funding = next((i for i, o in enumerate(market)
                        if o == ["BUY_SEED", "STRAWBERRY", 1]), None)
        if (site is None and len(approaching) == 1 and funding is not None
                and "PET_CAFE" in shops and "YARN_STORE" not in shops
                and farm["money"] >= 500
                and int(private["seeds"].get("STRAWBERRY", 0)) >= 1):
            choice, projection = _crop_projection(observation)
            st["projection"] = projection
            if choice:
                second_lane = bool(_ENABLE_SECOND_LANE and choice == "WHEAT"
                                   and lane2 is None)
                market[funding] = ["BUY_SEED", choice, 2 if second_lane else 1]
                st["crop"] = choice
                st["first_actor"] = approaching[0]
                st["second_lane"] = second_lane
                _STATS["committed"] += 1
                _STATS["chosen"] = choice
                return dict(action, market=market)

    if day == 11 and hour == 3 and st["crop"] and not st["first_planted"]:
        actor = st["first_actor"]
        if (actor is not None and actor < len(positions)
                and positions[actor] == _LANE
                and commands[actor] == ["PLANT", "STRAWBERRY"]
                and site is None and int(private["seeds"].get(st["crop"], 0)) > 0):
            st["first_planted"] = True
            _STATS["initial_plants"] += 1
            return _change_worker(action, actor, ["PLANT", st["crop"]])
        _STATS["mismatches"] += 1
        st["stopped"] = True

    if (day == 11 and hour == 6 and st["first_planted"]
            and st["second_lane"] and not st["lane2_first_planted"]):
        actor = st["first_actor"]
        if (actor is not None and actor < len(positions)
                and positions[actor] == _SECOND_LANE
                and commands[actor] == ["PLANT", "STRAWBERRY"]
                and lane2 is None and int(private["seeds"].get("WHEAT", 0)) > 0):
            st["lane2_first_planted"] = True
            _STATS["second_lane_plants"] += 1
            return _change_worker(action, actor, ["PLANT", "WHEAT"])
        st["second_lane"] = False
        _STATS["unsupported"] += 1

    if not st["first_planted"] or st["stopped"]:
        return action

    # First rotation: a worker already assigned to this lane has six idle
    # turns before the remainder of its incumbent watering/wheat path.
    if day == 14:
        if hour == 1 and st["day14_actor"] is None:
            if not (isinstance(site, dict) and site.get("crop") == st["crop"]
                    and int(site.get("planted_day", -1)) == 11):
                return action
            candidates = [i for i, (pos, cmd) in enumerate(zip(positions, commands))
                          if pos == (5, 5) and cmd == ["WEST"]
                          and _calendar_ok(_owned_tape(observation), 14, i)]
            if len(candidates) != 1:
                _STATS["unsupported"] += 1
                return action
            st["day14_actor"] = candidates[0]
            if len(action.get("market") or []) < _MAX_MARKET_ORDERS and farm["money"] >= 100:
                market = [list(o) for o in action.get("market") or []]
                market.append(["BUY_SEED", st["crop"],
                               2 if st["second_lane"] and st["lane2_first_planted"] else 1])
                st["second_funded"] = True
                return dict(action, market=market)
        actor = st["day14_actor"]
        schedule = {2: ["WATER"], 3: ["HARVEST"], 4: ["PLANT", st["crop"]],
                    5: ["WATER"], 6: ["DROP"], 7: ["SOUTH"]}
        if actor is not None and hour in schedule:
            expected = _LANE
            if actor >= len(positions) or positions[actor] != expected:
                _STATS["mismatches"] += 1
                st["stopped"] = True
                return action
            command = schedule[hour]
            if hour == 2:
                if not isinstance(site, dict) or site.get("crop") != st["crop"]:
                    st["stopped"] = True
                return action  # incumbent WATER, increases harvest yield
            if hour == 3:
                if not isinstance(site, dict) or int(site.get("yield_units", 0)) < 1:
                    st["stopped"] = True
                    return action
                _STATS["harvests"] += 1
                st["day14_started"] = True
            if hour == 4:
                if (not st["second_funded"] or site is not None
                        or int(private["seeds"].get(st["crop"], 0)) < 1):
                    command = ["PASS"]
                else:
                    st["second_planted"] = True
                    _STATS["rotations"] += 1
            if hour == 5 and not st["second_planted"]:
                command = ["PASS"]
            if hour == 5 and st["second_planted"]:
                _STATS["watered_after_plant"] += 1
            revised = _change_worker(action, actor, command)
            if hour == 6:
                revised = _sell_new_delivery(observation, revised, actor, st["crop"])
            return revised

        if (st["second_lane"] and st["lane2_first_planted"]
                and actor is not None and hour in (8, 9, 10)):
            if actor >= len(positions) or positions[actor] != _SECOND_LANE:
                st["second_lane"] = False
                _STATS["mismatches"] += 1
                return action
            if hour == 8:
                if (not isinstance(lane2, dict) or lane2.get("crop") != "WHEAT"
                        or int(lane2.get("planted_day", -1)) != 11
                        or int(lane2.get("yield_units", 0)) < 1):
                    st["second_lane"] = False
                    return action
                st["lane2_first_harvested"] = True
                st["lane2_sale_pending"] += int(lane2["yield_units"])
                _STATS["second_lane_harvests"] += 1
                return _change_worker(action, actor, ["HARVEST"])
            if hour == 9:
                if (not st["lane2_first_harvested"] or lane2 is not None
                        or int(private["seeds"].get("WHEAT", 0)) < 1):
                    st["second_lane"] = False
                    return action
                st["lane2_second_planted"] = True
                _STATS["second_lane_plants"] += 1
                return _change_worker(action, actor, ["PLANT", "WHEAT"])
            if hour == 10 and st["lane2_second_planted"]:
                _STATS["watered_after_plant"] += 1
                return action  # incumbent WATER now waters the replacement

    if st["lane2_sale_pending"] and day in (15, 19):
        action = _sell_overnight_increment(observation, action, st)

    # Second harvest: replace the parent's initial WEST/EAST detour with a
    # 2-step crop loop, then rejoin exactly at hour 6.  No livestock/feed
    # command is touched, and no worker is stranded with inventory overnight.
    if day == 16 and st["second_planted"]:
        if hour == 1 and st["day16_actor"] is None:
            if not (isinstance(site, dict) and site.get("crop") == st["crop"]
                    and int(site.get("planted_day", -1)) == 14):
                return action
            candidates = [i for i, (pos, cmd) in enumerate(zip(positions, commands))
                          if pos == (4, 4) and cmd == ["WEST"]
                          and _calendar_ok(_owned_tape(observation), 16, i)]
            if len(candidates) != 1:
                _STATS["unsupported"] += 1
                return action
            st["day16_actor"] = candidates[0]
        actor = st["day16_actor"]
        schedule = {1: ["SOUTH"], 2: ["WATER"], 3: ["HARVEST"],
                    4: ["DROP"], 5: ["SOUTH"]}
        if actor is not None and hour in schedule:
            pos = positions[actor] if actor < len(positions) else None
            expected = (4, 4) if hour == 1 else _LANE
            if pos != expected:
                _STATS["mismatches"] += 1
                st["stopped"] = True
                return action
            if hour == 3:
                if not isinstance(site, dict) or int(site.get("yield_units", 0)) < 1:
                    st["stopped"] = True
                    return action
                _STATS["harvests"] += 1
                st["day16_started"] = True
            if hour == 2:
                _STATS["watered_after_plant"] += 1
            revised = _change_worker(action, actor, schedule[hour])
            if hour == 4:
                revised = _sell_new_delivery(observation, revised, actor, st["crop"])
            return revised

    if (day == 18 and hour == 3 and st["second_lane"]
            and st["lane2_second_planted"] and not st["lane2_late_harvested"]):
        candidates = [i for i, (pos, cmd) in enumerate(zip(positions, commands))
                      if pos == _SECOND_LANE and cmd == ["WATER"]]
        current_load = (sum(int(q) for q in private["shed"].values())
                        + sum(sum(int(q) for q in inv.values())
                              for inv in private["inventories"]))
        if (len(candidates) == 1 and isinstance(lane2, dict)
                and lane2.get("crop") == "WHEAT"
                and int(lane2.get("planted_day", -1)) == 14
                and int(lane2.get("yield_units", 0)) >= 1
                and current_load + int(lane2["yield_units"]) <= 80):
            st["lane2_late_harvested"] = True
            st["lane2_sale_pending"] += int(lane2["yield_units"])
            _STATS["second_lane_harvests"] += 1
            return _change_worker(action, candidates[0], ["HARVEST"])
        _STATS["unsupported"] += 1

    return action


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return action
    try:
        step = int(observation.get("step", -1))
        if step < 0 or not _standard(configuration):
            return action
        st = _state(int(observation["player"]), step)
        return _adapt(observation, action, st)
    except (KeyError, IndexError, ValueError, TypeError, AttributeError):
        _STATS["errors"] += 1
        return action


agent.telemetry = _STATS
kaggle_submission_agent = agent
