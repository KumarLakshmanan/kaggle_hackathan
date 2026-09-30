"""Bounded, observation-legal early-tomato substitution experiment.

Local research only.  The imported parent is SHA-pinned; this file is not a
submission.  The policy never reads a replay, episode ID, seed, opponent tape,
or future shop.  It may replace one uncommitted order for two strawberry seeds
with two tomato seeds, and only the two plants funded by that order.  Every
other worker command and original market-order position is retained.  Future
calendar checks inspect only the parent's own precommitted route tape.

``python -B exp_agent_early_tomato_20260924.py --probe`` prints a compact
diagnostic for one preselected route.  ``--bench`` runs the declared paired
routes and writes only diagnostics/early_tomato_* files.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parent
PARENT = ROOT / "main.py"
PARENT_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA256:
    raise RuntimeError("early-tomato pilot requires the frozen main.py parent")
_spec = importlib.util.spec_from_file_location("_early_tomato_frozen_parent", PARENT)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot import frozen parent")
_BASE = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _BASE
_spec.loader.exec_module(_BASE)

LIMIT = 2
MIN_PROJECTED_GAIN = 200.0
MAX_ORDERS = 10
SITES_HORIZON = 719  # Include every actionable step, including day 29/terminal.
_STATES: dict[int, dict[str, Any]] = {}
_AUDIT: list[dict[str, Any]] = []
_STATS: dict[str, int | float] = {
    "orders_considered": 0, "certified": 0, "economic_rejects": 0,
    "physical_rejects": 0, "orders_replaced": 0, "plants_requested": 0,
    "plants_confirmed": 0, "water_confirmed": 0, "harvests_observed": 0,
    "tomato_sell_requested": 0, "market_full": 0, "fallbacks": 0,
    "v219_eligibility_preserved": 0, "errors": 0,
    "last_projected_gain": 0.0, "last_projected_tomato_units": 0,
    "last_projected_strawberry_removed": 0,
    "max_policy_ms": 0.0, "max_adapt_ms": 0.0,
}
_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_SHED = ((4, 4), (5, 4), (4, 5), (5, 5))


def _standard(configuration: Any) -> bool:
    cfg = configuration if hasattr(configuration, "get") else {}
    return all(int(cfg.get(k, v)) == v for k, v in (
        ("boardSize", 10), ("turnsPerDay", 24), ("episodeSteps", 720),
        ("shedCapacity", 100), ("maxMarketOrdersPerTurn", 10),
    )) and not cfg.get("marketParams")


def _new_state(seat: int, step: int) -> dict[str, Any]:
    st = _STATES.get(seat)
    if st is None or step == 0 or step <= st["step"]:
        st = {"step": -1, "committed": False, "stopped": False,
              "plant_slots": {}, "sites": {}, "water_slots": {},
              "projection": None, "pending": {}, "last_harvest": {}}
        _STATES[seat] = st
        if step == 0:
            _AUDIT.clear()
            for k in _STATS:
                _STATS[k] = 0.0 if k.startswith("max_") else 0
    st["step"] = step
    return st


def _units(action: dict[str, Any]) -> list[list[Any]]:
    return [list(action.get("farmer") or ["PASS"]),
            *(list(c) for c in action.get("hands") or [])]


def _set_unit(action: dict[str, Any], actor: int, command: list[Any]) -> dict[str, Any]:
    revised = dict(action)
    if actor == 0:
        revised["farmer"] = command
    else:
        hands = [list(c) for c in action.get("hands") or []]
        hands[actor - 1] = command
        revised["hands"] = hands
    return revised


def _spawn(positions: list[tuple[int, int]]) -> tuple[int, int]:
    occupancy = {p: positions.count(p) for p in _SHED}
    return min(_SHED, key=lambda p: (occupancy[p], _SHED.index(p)))


def _calendar(observation: dict[str, Any], action: dict[str, Any], tape: list[dict[str, Any]],
              end: int = SITES_HORIZON) -> dict[int, list[tuple[int, tuple[int, int], list[Any]]]]:
    """Own-route coordinates; market HIRE follows all unit actions each turn."""
    step = int(observation["step"])
    farm = observation["farms"][int(observation["player"])]
    positions = [tuple(farm["farmer"]), *(tuple(p) for p in farm["hands"])]
    events: dict[int, list[tuple[int, tuple[int, int], list[Any]]]] = {}
    for t in range(step, min(end, len(tape))):
        if t > step and t % 24 == 0:
            positions = [(4, 4)]
        a = action if t == step else tape[t]
        commands = _units(a)
        row = []
        for actor in range(min(len(positions), len(commands))):
            pos, command = positions[actor], commands[actor]
            row.append((actor, pos, command))
            movement = _MOVES.get(command[0]) if command else None
            if movement:
                positions[actor] = (pos[0] + movement[0], pos[1] + movement[1])
        events[t] = row
        for order in a.get("market") or []:
            if order and order[0] == "HIRE":
                positions.append(_spawn(positions))
    return events


def _crop_outcome(calendar: dict[int, list[tuple[int, tuple[int, int], list[Any]]]],
                  site: tuple[int, int], plant_step: int, crop: str) -> tuple[list[tuple[int, int]], bool]:
    """Single-tile exact ongoing-crop water, yield, harvest, decay semantics.

    This projects unit work to the final actionable step.  Delivery is a
    separate capacity risk: the engine auto-deposits carried goods at midnight,
    but the future shed load and wrappers' market slots are not known here.
    """
    first, interval = (8, 1) if crop == "TOMATO" else (10, 2)
    birth = plant_step // 24
    dry, watered, yield_units, lifespan = 1, False, 0, -1
    harvests: list[tuple[int, int]] = []
    for step in range(plant_step, SITES_HORIZON):
        for _actor, pos, cmd in calendar.get(step, []):
            if pos != site or not cmd:
                continue
            if step == plant_step and cmd == ["PLANT", "STRAWBERRY"]:
                continue
            if cmd[0] == "WATER" and not watered:
                watered = True
            elif cmd[0] == "HARVEST" and yield_units and step // 24 - birth >= first:
                harvests.append((step, yield_units))
                yield_units = 0
            elif cmd[0] in ("DIG", "PLANT", "BUILD_COOP", "BUILD_PASTURE"):
                # A later replant/dig must not be displaced by this cohort.
                if yield_units or step // 24 - birth <= first + 3 * interval:
                    return harvests, False
                return harvests, True
        if lifespan >= 0 and step >= lifespan and (step - lifespan) % 2 == 0:
            yield_units -= 1
            if yield_units <= 0:
                return harvests, True
        if step % 24 == 23:
            dry = 0 if watered else dry + 1
            if dry >= 2:
                return harvests, True
            next_day = step // 24 + 1
            elapsed = next_day - birth - first
            if elapsed >= 0 and elapsed % interval == 0:
                count = elapsed // interval + 1
                if count <= 4:
                    yield_units = min(4, yield_units + 1)
                    if count == 4:
                        lifespan = (next_day + 1) * 24
            watered = False
    return harvests, True


def _seed_calendar_ok(observation: dict[str, Any], action: dict[str, Any],
                      tape: list[dict[str, Any]], plant_slots: list[tuple[int, int, tuple[int, int]]]) -> bool:
    seeds = dict(observation["private"]["seeds"])
    chosen = {(t, actor) for t, actor, _ in plant_slots}
    start = int(observation["step"])
    end = start // 24 * 24 + 24
    for step in range(start, end):
        a = action if step == start else tape[step]
        demand = {"STRAWBERRY": 0, "TOMATO": 0}
        for actor, cmd in enumerate(_units(a)):
            if cmd[:1] != ["PLANT"] or len(cmd) < 2:
                continue
            crop = "TOMATO" if (step, actor) in chosen else cmd[1]
            if crop in demand:
                demand[crop] += 1
        if any(demand[crop] > int(seeds.get(crop, 0)) for crop in demand):
            return False
        for crop, qty in demand.items():
            seeds[crop] = int(seeds.get(crop, 0)) - qty
        for order in a.get("market") or []:
            if len(order) == 3 and order[0] == "BUY_SEED" and int(order[2]) > 0:
                seeds[order[1]] = int(seeds.get(order[1], 0)) + int(order[2])
    return True


def _sale_slot(tape: list[dict[str, Any]], delivery_step: int) -> int | None:
    for step in range(delivery_step, min(delivery_step + 48, len(tape))):
        orders = tape[step].get("market") or []
        if len(orders) < MAX_ORDERS:
            return step
    return None


def _price_model(observation: dict[str, Any], configuration: Any,
                 tape: list[dict[str, Any]], baseline_harvests: list[tuple[int, int]],
                 candidate_harvests: list[tuple[int, int]]) -> dict[str, Any]:
    """Optimistic forecast of affected sales under both supply paths.

    The observed shop roster is held fixed.  Future opponent output is unknown:
    a +80 tomato-inventory stress and -20 strawberry-inventory opportunity cost
    are deliberately adverse to conversion.  Existing own strawberry sale
    requests are reduced only by cohort units projected for delivery before
    those requests.  A free slot on the raw tape is not an actual future sale:
    the benchmark must confirm successful deposits and receipts in both arms.
    """
    start = int(observation["step"])
    start_day = start // 24
    market = observation["market"]
    items = ("TOMATO", "STRAWBERRY")
    demand = {i: _BASE._h6_demand_per_day(observation, configuration, i) for i in items}
    existing = []
    for step in range(start + 1, len(tape)):
        for order in tape[step].get("market") or []:
            if len(order) == 3 and order[:1] == ["SELL"] and order[1] in items and int(order[2]) > 0:
                existing.append((step, order[1], int(order[2])))
    # Model the parent's conditional day-18 tomato project in both arms.  The
    # wrapper below explicitly preserves its eligibility if it later qualifies.
    project = [(24 * day, "TOMATO", 20) for day in (26, 27, 28, 29)]
    baseline_pool = sorted(((step // 24 + 1) * 24, qty) for step, qty in baseline_harvests)
    strawberry_reductions: dict[int, int] = {}
    pool, pointer = 0, 0
    for index, (step, item, qty) in enumerate(existing):
        if item != "STRAWBERRY":
            continue
        while pointer < len(baseline_pool) and baseline_pool[pointer][0] <= step:
            pool += baseline_pool[pointer][1]
            pointer += 1
        take = min(pool, qty)
        pool -= take
        strawberry_reductions[index] = take
    tomato_sales = []
    for harvest_step, qty in candidate_harvests:
        delivery_step = (harvest_step // 24 + 1) * 24
        slot = _sale_slot(tape, delivery_step)
        if slot is None:
            return {"gain": float("-inf"), "reason": "no sale slot"}
        tomato_sales.append((slot, "TOMATO", qty))

    def receipts(converted: bool) -> tuple[float, dict[str, float]]:
        inv = {"TOMATO": float(market["inventory"]["TOMATO"]) + 80.0,
               "STRAWBERRY": float(market["inventory"]["STRAWBERRY"]) - 20.0}
        events = [(step, item, qty - (strawberry_reductions.get(index, 0) if converted else 0))
                  for index, (step, item, qty) in enumerate(existing)] + project
        if converted:
            events += tomato_sales
        events.sort(key=lambda row: row[0])
        last_day, by_item = start_day, dict.fromkeys(items, 0.0)
        for step, item, qty in events:
            day = step // 24
            if day > last_day:
                for product in items:
                    inv[product] = max(0.0, inv[product] - (day - last_day) * demand[product])
                last_day = day
            if qty <= 0:
                continue
            unit_prices = [_BASE._h6_market_price(item, int(inv[item]) + k) for k in range(qty)]
            by_item[item] += float(sum(unit_prices))
            inv[item] += qty
        return sum(by_item.values()), by_item

    base_total, base_items = receipts(False)
    candidate_total, candidate_items = receipts(True)
    # Replacing two $100 strawberry seeds with two $50 tomato seeds saves $100.
    gain = candidate_total - base_total + LIMIT * 50
    return {"gain": gain, "forecast_is_optimistic": True,
            "base_receipts": base_items,
            "candidate_receipts": candidate_items, "seed_saving": LIMIT * 50,
            "baseline_cohort_units_removed": sum(strawberry_reductions.values()),
            "candidate_tomato_units_sold": sum(q for _, _, q in tomato_sales),
            "tomato_sale_steps": [step for step, _, _ in tomato_sales],
            "shops_now": list(observation["town"]["unlocked_shops"]),
            "demand_per_day": demand}


def _certificate(observation: dict[str, Any], action: dict[str, Any],
                 configuration: Any) -> tuple[dict[str, Any] | None, str]:
    step = int(observation["step"])
    seat = int(observation["player"])
    day = step // 24
    if not 6 <= day <= 9 or step % 24 >= 20:
        return None, "outside window"
    shops = observation["town"]["unlocked_shops"]
    if not any(s in ("PIZZA_SHOP", "FARMERS_MARKET") for s in shops):
        return None, "no active tomato shop"
    orders = action.get("market") or []
    order_indices = [i for i, o in enumerate(orders) if o == ["BUY_SEED", "STRAWBERRY", LIMIT]]
    if not order_indices or len(orders) > MAX_ORDERS:
        return None, "no uncommitted two-seed order"
    if observation["private"]["seeds"].get("TOMATO", 0):
        return None, "pre-existing tomato seed"
    native = _BASE._IMPL.chassis.players.get(seat) or {}
    tape = _BASE._IMPL.chassis.routes.get(native.get("route"))
    if tape is None or len(tape) < SITES_HORIZON:
        return None, "no own route calendar"
    if _units(action) != _units(tape[step]):
        return None, "current unit action differs from own calendar"
    farm = observation["farms"][seat]
    current_cash = float(farm["money"])
    mandatory = 0.0
    for order in orders:
        if order[:1] == ["BUY_PRODUCT"]:
            mandatory += int(order[2]) * (float(observation["market"]["prices"][order[1]]) + 10)
        elif order[:1] == ["BUY_ANIMAL"]:
            mandatory += int(order[2]) * {"GOOSE": 300, "COW": 400, "SHEEP": 500}[order[1]]
        elif order[:1] == ["BUY_SEED"]:
            mandatory += int(order[2]) * {"WHEAT": 10, "CARROT": 20, "TOMATO": 50,
                                           "STRAWBERRY": 100, "MELON": 80}[order[1]]
        elif order[:1] == ["BUY_LAND"]:
            mandatory += 2000
        elif order[:1] == ["HIRE"]:
            mandatory += 1000
    if current_cash < mandatory + 300:
        return None, "cash after parent obligations"
    revised = copy.deepcopy(action)
    revised["market"][order_indices[0]][1] = "TOMATO"
    calendar = _calendar(observation, action, tape)
    plant_slots = []
    for future in range(step + 1, (day + 1) * 24):
        for actor, pos, cmd in calendar[future]:
            if cmd == ["PLANT", "STRAWBERRY"]:
                plant_slots.append((future, actor, pos))
                if len(plant_slots) == LIMIT:
                    break
        if len(plant_slots) == LIMIT:
            break
    if len(plant_slots) != LIMIT or len({pos for _, _, pos in plant_slots}) != LIMIT:
        return None, "not two distinct same-day strawberry sites"
    if any(farm["tiles"][pos[1]][pos[0]] is not None for _, _, pos in plant_slots):
        return None, "site not currently free"
    for plant_step, _actor, pos in plant_slots:
        if not any(t > plant_step and t // 24 == day and site == pos and cmd == ["WATER"]
                   for t in range(plant_step + 1, (day + 1) * 24)
                   for _, site, cmd in calendar[t]):
            return None, "no planting-day WATER"
    if not _seed_calendar_ok(observation, revised, tape, plant_slots):
        return None, "seed sequence would starve parent plant"
    baseline_harvests, candidate_harvests = [], []
    for plant_step, _actor, pos in plant_slots:
        strawberry, clean_s = _crop_outcome(calendar, pos, plant_step, "STRAWBERRY")
        tomato, clean_t = _crop_outcome(calendar, pos, plant_step, "TOMATO")
        if not clean_s or not clean_t or not tomato:
            return None, "no clean tomato harvest calendar"
        baseline_harvests += strawberry
        candidate_harvests += tomato
    if sum(q for _, q in candidate_harvests) < 4:
        return None, "too few deliverable tomato units"
    shed = observation["private"]["shed"]
    carrying = sum(sum(int(q) for q in bag.values()) for bag in observation["private"]["inventories"])
    if sum(int(q) for q in shed.values()) + carrying > 75:
        return None, "insufficient current shed headroom"
    economics = _price_model(observation, configuration, tape, baseline_harvests, candidate_harvests)
    if economics["gain"] < MIN_PROJECTED_GAIN:
        return None, "projected marginal receipts"
    return {"action": revised, "slots": plant_slots,
            "water_slots": [(t, actor, pos) for plant_step, _actor, pos in plant_slots
                            for t in range(plant_step + 1, (day + 1) * 24)
                            for actor, site, cmd in calendar[t]
                            if site == pos and cmd == ["WATER"]],
            "baseline_harvests": baseline_harvests,
            "tomato_harvests": candidate_harvests,
            "economics": economics, "seed_step": step}, "accepted"


_ORIGINAL_V219_QUALIFIES = _BASE._v219_qualifies


def _preserve_v219_qualifies(observation: dict[str, Any], native: dict[str, Any]) -> bool:
    """Ignore only our already-confirmed early tiles at the day-18 gate.

    The late project's SE land, worker, cash, seed, and shop conditions remain
    exactly the parent's.  Nonzero tomato seeds/shed stock still fail closed.
    """
    seat = int(observation["player"])
    st = _STATES.get(seat)
    if not st or not st.get("sites") or int(observation["step"]) != 432:
        return _ORIGINAL_V219_QUALIFIES(observation, native)
    if observation["private"]["seeds"].get("TOMATO", 0) or observation["private"]["shed"].get("TOMATO", 0):
        return _ORIGINAL_V219_QUALIFIES(observation, native)
    altered = dict(observation)
    farms = list(observation["farms"])
    farm = dict(farms[seat])
    board = [list(row) for row in farm["tiles"]]
    for x, y in st["sites"]:
        tile = board[y][x]
        if isinstance(tile, dict) and tile.get("crop") == "TOMATO":
            board[y][x] = None
    farm["tiles"] = board
    farms[seat] = farm
    altered["farms"] = farms
    eligible = _ORIGINAL_V219_QUALIFIES(altered, native)
    if eligible:
        _STATS["v219_eligibility_preserved"] += 1
    return eligible


_BASE._v219_qualifies = _preserve_v219_qualifies


def _adapt(observation: dict[str, Any], action: dict[str, Any], configuration: Any,
           st: dict[str, Any]) -> dict[str, Any]:
    step, seat = int(observation["step"]), int(observation["player"])
    farm = observation["farms"][seat]
    if not st["committed"] and not st["stopped"] and 144 <= step < 240:
        if any(o == ["BUY_SEED", "STRAWBERRY", LIMIT] for o in action.get("market") or []):
            _STATS["orders_considered"] += 1
            certificate, reason = _certificate(observation, action, configuration)
            if certificate is None:
                if reason == "projected marginal receipts":
                    _STATS["economic_rejects"] += 1
                else:
                    _STATS["physical_rejects"] += 1
            else:
                _STATS["certified"] += 1
                _STATS["orders_replaced"] += 1
                _STATS["last_projected_gain"] = float(certificate["economics"]["gain"])
                _STATS["last_projected_tomato_units"] = int(certificate["economics"]["candidate_tomato_units_sold"])
                _STATS["last_projected_strawberry_removed"] = int(certificate["economics"]["baseline_cohort_units_removed"])
                st["committed"] = True
                st["plant_slots"] = {(t, actor): pos for t, actor, pos in certificate["slots"]}
                st["water_slots"] = {(t, actor): pos for t, actor, pos in certificate["water_slots"]}
                st["projection"] = certificate["economics"]
                st["pending"] = {"step": step, "tomato_before": int(observation["private"]["seeds"].get("TOMATO", 0))}
                _AUDIT.append({"step": step, "kind": "certified_order",
                               "sites": [list(pos) for _, _, pos in certificate["slots"]],
                               "plant_slots": [(t, actor) for t, actor, _ in certificate["slots"]],
                               "tomato_harvests": certificate["tomato_harvests"],
                               "economics": certificate["economics"]})
                return certificate["action"]

    if not st["committed"] or st["stopped"]:
        return action
    pending = st.get("pending") or {}
    if pending and step > pending["step"]:
        gained = int(observation["private"]["seeds"].get("TOMATO", 0)) - pending["tomato_before"]
        st["pending"] = {}
        if gained < LIMIT:
            st["stopped"] = True
            _STATS["fallbacks"] += 1
            _AUDIT.append({"step": step, "kind": "fallback", "reason": "tomato seed order not executed"})
            return action

    positions = [tuple(farm["farmer"]), *(tuple(p) for p in farm["hands"])]
    commands = _units(action)
    for (planned_step, actor), pos in st["plant_slots"].items():
        if planned_step != step:
            continue
        if (actor >= len(positions) or actor >= len(commands)
                or positions[actor] != pos or commands[actor] != ["PLANT", "STRAWBERRY"]
                or farm["tiles"][pos[1]][pos[0]] is not None
                or int(observation["private"]["seeds"].get("TOMATO", 0)) <= 0):
            st["stopped"] = True
            _STATS["fallbacks"] += 1
            _AUDIT.append({"step": step, "kind": "fallback", "reason": "plant precondition changed"})
            return action
        action = _set_unit(action, actor, ["PLANT", "TOMATO"])
        _STATS["plants_requested"] += 1
        _AUDIT.append({"step": step, "kind": "plant_request", "actor": actor, "site": list(pos)})

    # Confirm actual mutation on the next callback, before trusting the lane.
    for (planned_step, actor), pos in st["plant_slots"].items():
        if planned_step + 1 != step:
            continue
        tile = farm["tiles"][pos[1]][pos[0]]
        if not isinstance(tile, dict) or tile.get("crop") != "TOMATO":
            st["stopped"] = True
            _STATS["fallbacks"] += 1
            _AUDIT.append({"step": step, "kind": "fallback", "reason": "plant did not execute", "site": list(pos)})
            return action
        st["sites"][pos] = planned_step
        _STATS["plants_confirmed"] += 1
        _AUDIT.append({"step": step, "kind": "plant_confirmed", "site": list(pos)})

    for (water_step, actor), pos in st["water_slots"].items():
        if water_step + 1 == step and pos in st["sites"]:
            tile = farm["tiles"][pos[1]][pos[0]]
            if isinstance(tile, dict) and tile.get("crop") == "TOMATO" and tile.get("watered_today"):
                _STATS["water_confirmed"] += 1
                _AUDIT.append({"step": step, "kind": "water_confirmed", "site": list(pos)})
            else:
                st["stopped"] = True
                _STATS["fallbacks"] += 1
                _AUDIT.append({"step": step, "kind": "fallback", "reason": "same-day WATER missing", "site": list(pos)})
                return action

    for actor, (pos, cmd) in enumerate(zip(positions, commands)):
        if pos in st["sites"] and cmd == ["HARVEST"]:
            tile = farm["tiles"][pos[1]][pos[0]]
            if isinstance(tile, dict) and tile.get("crop") == "TOMATO" and int(tile.get("yield_units", 0)) > 0:
                _STATS["harvests_observed"] += 1
                _AUDIT.append({"step": step, "kind": "harvest_parent_command", "actor": actor,
                               "site": list(pos), "units_before": int(tile["yield_units"])})

    # Sell only physically available tomato, after retaining every parent
    # market order and its order position.  Parent V219 may already sell it.
    if st["sites"] and step >= min(st["sites"].values()) + 8 * 24:
        market = [list(o) for o in action.get("market") or []]
        projected = _BASE.projected_shed(action, _BASE.FarmView(observation))
        stock = max(0, int(projected.get("TOMATO", 0)))
        requested = sum(max(0, int(o[2])) for o in market
                        if len(o) == 3 and o[:2] == ["SELL", "TOMATO"])
        extra = max(0, stock - requested)
        if extra and len(market) < MAX_ORDERS:
            market.append(["SELL", "TOMATO", extra])
            action = dict(action, market=market)
            _STATS["tomato_sell_requested"] += extra
            _AUDIT.append({"step": step, "kind": "tomato_sale_request", "quantity": extra})
        elif extra:
            _STATS["market_full"] += 1
    return action


def agent(observation: Any, configuration: Any = None) -> dict[str, Any]:
    start = time.perf_counter()
    action = _BASE.agent(observation, configuration)
    try:
        if not isinstance(observation, dict) or not isinstance(action, dict):
            return action
        step = int(observation.get("step", -1))
        st = _new_state(int(observation.get("player", 0)), step)
        if step < 0 or not _standard(configuration):
            return action
        begun = time.perf_counter()
        result = _adapt(observation, action, configuration, st)
        _STATS["max_adapt_ms"] = max(float(_STATS["max_adapt_ms"]),
                                     (time.perf_counter() - begun) * 1000)
        return result
    except Exception as exc:
        _STATS["errors"] += 1
        _AUDIT.append({"step": int(observation.get("step", -1)) if isinstance(observation, dict) else -1,
                       "kind": "exception_fallback", "type": type(exc).__name__})
        return action
    finally:
        _STATS["max_policy_ms"] = max(float(_STATS["max_policy_ms"]),
                                      (time.perf_counter() - start) * 1000)


agent.telemetry = _STATS
kaggle_submission_agent = agent


_PANEL_MANIFEST = ROOT / "diagnostics/top50_current_2026-09-24/routes/summary.json"
_PANEL_BASELINE = ROOT / "diagnostics/top50_current_2026-09-24/main_100routes.json"
_ROUTE_IDS = (
    (112933084, "loss", "Excluding"),
    (112941285, "loss", "ActiveMusyoku"),
    (112937075, "loss", "ActiveMusyoku"),
    (112939032, "loss", "Boey"),
    (112928864, "control", "KawattaTaido"),
    (112940393, "control", "Gatswei"),
)


def _compact_trace(result: dict[str, Any], seat: int) -> dict[str, Any]:
    records = result["traces"][seat]
    by_step = {int(row["step"]): row for row in records}
    early_plants: dict[tuple[int, int], int] = {}
    unit_checks = []
    sales: dict[int, dict[str, dict[str, float]]] = {0: {}, 1: {}}
    buys: dict[int, dict[str, int]] = {0: {}, 1: {}}
    for event in result["events"]:
        player = event.get("player")
        if player not in (0, 1):
            continue
        if event["phase"] == "market_unit" and event.get("success"):
            item = str(event["item"])
            if event["operation"] == "SELL":
                target = sales[player].setdefault(item, {"units": 0, "receipts": 0.0})
                target["units"] += 1
                target["receipts"] += float(event["cash_delta"])
            elif event["operation"] == "BUY_SEED":
                buys[player][item] = buys[player].get(item, 0) + 1
        if event["phase"] != "unit_action" or player != seat:
            continue
        step = int(event["step"])
        row = by_step.get(step)
        if row is None:
            continue
        actor = int(event["actor"])
        farm = row["observation"]["farms"][seat]
        positions = [farm["farmer"], *(farm["hands"] or [])]
        if actor >= len(positions):
            continue
        site = tuple(int(x) for x in positions[actor])
        command = event.get("action") or []
        if step < 240 and command == ["PLANT", "TOMATO"]:
            if event["changed"]:
                early_plants[site] = step
            unit_checks.append({"step": step, "actor": actor, "site": list(site),
                                "op": "PLANT_TOMATO", "executed": bool(event["changed"])})
    for event in result["events"]:
        if event.get("phase") != "unit_action" or event.get("player") != seat:
            continue
        step, actor = int(event["step"]), int(event["actor"])
        row = by_step.get(step)
        if row is None:
            continue
        farm = row["observation"]["farms"][seat]
        positions = [farm["farmer"], *(farm["hands"] or [])]
        if actor >= len(positions):
            continue
        site = tuple(int(x) for x in positions[actor])
        if site not in early_plants:
            continue
        command = event.get("action") or []
        if command in (["WATER"], ["HARVEST"]):
            tile = farm["tiles"][site[1]][site[0]]
            unit_checks.append({"step": step, "actor": actor, "site": list(site),
                                "op": command[0], "executed": bool(event["changed"]),
                                "crop_before": tile.get("crop") if isinstance(tile, dict) else None,
                                "yield_before": int(tile.get("yield_units", 0)) if isinstance(tile, dict) else 0})
    day_end_deposits = []
    for turn in result["turns"]:
        if int(turn["step"]) % 24 != 23:
            continue
        before = int(turn["players_before"][seat]["shed"].get("TOMATO", 0))
        after = int(turn["players_after"][seat]["shed"].get("TOMATO", 0))
        if after > before:
            day_end_deposits.append({"step": int(turn["step"]), "tomato_shed_gain": after - before})
    market_cap = max(len(row["action"].get("market") or []) for row in records)
    early_actions = [
        {"step": int(row["step"]), "action": row["action"]}
        for row in records if 144 <= int(row["step"]) < 240
    ]
    return {
        "shops": list(records[-1]["observation"]["town"]["unlocked_shops"]),
        "shops_day6": list(by_step[156]["observation"]["town"]["unlocked_shops"]),
        "candidate_cash": result["candidate_reward"],
        "rival_cash": result["opponent_reward"],
        "margin": result["margin"],
        "status": [result["candidate_status"], result["opponent_status"]],
        "max_action_ms": 1000 * float(result["candidate_timing"]["max_seconds"]),
        "mean_action_ms": 1000 * float(result["candidate_timing"]["seconds"]) / max(1, int(result["candidate_timing"]["calls"])),
        "max_market_orders": market_cap,
        "sales": sales,
        "seed_buys": buys,
        "early_tomato_sites": [{"site": list(site), "plant_step": step}
                               for site, step in sorted(early_plants.items())],
        "unit_checks": unit_checks,
        "day_end_tomato_deposits": day_end_deposits,
        "early_actions": early_actions,
    }


def _bench_one(job: tuple[dict[str, Any], int, str, str, list[str] | None]) -> dict[str, Any]:
    route, seat, arm, mode, shops = job
    import trace_paired_game_events as runner

    agent_path = str(PARENT if arm == "parent" else Path(__file__).resolve())
    opponent = "rawroute:" + str(Path(route["path"]).resolve())
    original_loader = runner._load_agent
    holder: dict[str, Any] = {}

    def _capture_loader(*args: Any, **kwargs: Any) -> Any:
        loaded = original_loader(*args, **kwargs)
        if len(args) >= 2 and str(args[1]).startswith("event_candidate"):
            holder["timed"] = loaded[1]
        return loaded

    runner._load_agent = _capture_loader
    try:
        result = runner.run(agent_path, opponent, int(route["seed"]), seat,
                            shop_sequence=shops if mode == "fixed" else None)
        compact = _compact_trace(result, seat)
        timed = holder.get("timed")
        telemetry = getattr(timed.function, "telemetry", None) if timed else None
        audit = timed.function.__globals__.get("_AUDIT", []) if timed else []
        compact.update({
            "episode_id": int(route["episode_id"]), "team": str(route["team"]),
            "seat": seat, "arm": arm, "mode": mode,
            "telemetry": dict(telemetry) if isinstance(telemetry, dict) else None,
            "audit": copy.deepcopy(audit),
        })
        return compact
    finally:
        runner._load_agent = original_loader


def _receipt(row: dict[str, Any], item: str, who: str = "own") -> tuple[int, float]:
    seat = int(row["seat"])
    source = row["sales"][seat if who == "own" else 1 - seat].get(item, {})
    return int(source.get("units", 0)), float(source.get("receipts", 0))


def _paired_rows(rows: list[dict[str, Any]]) -> dict[tuple[int, int, str, str], dict[str, Any]]:
    return {(int(r["episode_id"]), int(r["seat"]), str(r["arm"]), str(r["mode"])): r for r in rows}


def _report(rows: list[dict[str, Any]], declared: list[dict[str, Any]],
            baseline_panel: dict[str, Any]) -> str:
    lookup = _paired_rows(rows)
    panel_lookup = {int(row["episode_id"]): row for row in baseline_panel["rows"]}
    lines = [
        "# Early tomato two-plot pilot — 2026-09-24", "",
        "Local fixed-replay experiment, not a Kaggle submission. The candidate imports",
        f"`main.py` SHA-256 `{PARENT_SHA256}` and does not modify it. Opponent tapes are",
        "fixed historical actions; native shops can change when occupancy changes. Fixed-shop",
        "runs force each original parent/native shop sequence and are counterfactual, not native scores.", "",
        "The policy substitutes one two-seed strawberry order on days 6–9, only after",
        "a same-day plant→water, later harvest, day-end delivery, market SELL-slot, cash,",
        "and projected portfolio-receipts certificate. It uses only the observed shops,",
        "prices/inventory, own physical state, and own committed tape. No opponent/episode/seed",
        "lookup or future-shop information enters the policy. The parent day-18 tomato",
        "gate remains active when all its conditions hold; only these confirmed early",
        "tomato tiles are excluded from its unrelated pre-existing-tomato check.", "",
        "| Role | Team / episode | Parent native pair | Candidate native pair | Native Δ pair | Parent fixed pair | Candidate fixed pair | Fixed Δ pair |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for route in declared:
        ep = int(route["episode_id"])
        def pair(arm: str, mode: str) -> float:
            return sum(float(lookup[(ep, seat, arm, mode)]["margin"]) for seat in (0, 1))
        pn, cn = pair("parent", "native"), pair("candidate", "native")
        pf, cf = pair("parent", "fixed"), pair("candidate", "fixed")
        lines.append(f"| {route['role']} | {route['team']} / {ep} | {pn:+,.0f} | {cn:+,.0f} | {cn-pn:+,.0f} | {pf:+,.0f} | {cf:+,.0f} | {cf-pf:+,.0f} |")
    lines += ["", "## Execution and economics", "",
              "Values below are executed market commits, not attempted tape quantities.", ""]
    for route in declared:
        ep = int(route["episode_id"])
        base_panel = panel_lookup[ep]
        lines += [f"### {route['team']} / {ep} ({route['role']})", "",
                  f"Frozen panel pair margin: {float(base_panel['pair_margin']):+,.0f}.", ""]
        for seat in (0, 1):
            p = lookup[(ep, seat, "parent", "fixed")]
            c = lookup[(ep, seat, "candidate", "fixed")]
            pn = lookup[(ep, seat, "parent", "native")]
            cn = lookup[(ep, seat, "candidate", "native")]
            p_tom, p_tom_cash = _receipt(p, "TOMATO")
            c_tom, c_tom_cash = _receipt(c, "TOMATO")
            p_str, p_str_cash = _receipt(p, "STRAWBERRY")
            c_str, c_str_cash = _receipt(c, "STRAWBERRY")
            sites = c["early_tomato_sites"]
            same_day_water = sum(1 for v in c["unit_checks"] if v["op"] == "WATER"
                                 and v["executed"] and v["step"] // 24 == next((s["plant_step"] // 24 for s in sites if s["site"] == v["site"]), -1))
            early_harvest = sum(int(v["yield_before"]) for v in c["unit_checks"]
                                if v["op"] == "HARVEST" and v["executed"] and v["crop_before"] == "TOMATO")
            audit = c.get("audit") or []
            certified = next((a for a in audit if a.get("kind") == "certified_order"), None)
            projected = certified["economics"]["gain"] if certified else None
            lines.append(
                f"- Seat {seat}: fixed own/rival {p['candidate_cash']:,.0f}/{p['rival_cash']:,.0f}"
                f" → {c['candidate_cash']:,.0f}/{c['rival_cash']:,.0f};"
                f" native {pn['candidate_cash']:,.0f}/{pn['rival_cash']:,.0f}"
                f" → {cn['candidate_cash']:,.0f}/{cn['rival_cash']:,.0f}."
                f" Executed early plants {len(sites)}, same-day WATER {same_day_water},"
                f" early-plot tomato HARVEST {early_harvest} units;"
                f" tomato sold {p_tom}/{p_tom_cash:,.0f} → {c_tom}/{c_tom_cash:,.0f};"
                f" strawberry sold {p_str}/{p_str_cash:,.0f} → {c_str}/{c_str_cash:,.0f};"
                f" modeled gain {projected if projected is not None else 'abstained'}."
            )
            if c["max_market_orders"] > MAX_ORDERS or c["max_action_ms"] >= 1000:
                lines.append(f"  - Execution limit breach: market cap {c['max_market_orders']}, max action {c['max_action_ms']:.1f} ms.")
        lines.append("")
    fixed_control_reversals = []
    wins = 0
    seat_wins = 0
    for route in declared:
        ep = int(route["episode_id"])
        pair_candidate = sum(lookup[(ep, seat, "candidate", "fixed")]["margin"] for seat in (0, 1))
        pair_parent = sum(lookup[(ep, seat, "parent", "fixed")]["margin"] for seat in (0, 1))
        if route["role"] == "control" and pair_parent > 0 and pair_candidate <= 0:
            fixed_control_reversals.append(ep)
        wins += pair_candidate > 0
        seat_wins += sum(lookup[(ep, seat, "candidate", "fixed")]["margin"] > 0 for seat in (0, 1))
    loss_routes = [r for r in declared if r["role"] == "loss"]
    recoveries = []
    for route in loss_routes:
        ep = int(route["episode_id"])
        original = -float(panel_lookup[ep]["pair_margin"])
        gain = sum(lookup[(ep, seat, "candidate", "fixed")]["margin"]
                   - lookup[(ep, seat, "parent", "fixed")]["margin"] for seat in (0, 1))
        recoveries.append((ep, gain, original, gain / original if original else 0.0))
    lines += ["## Decision", "",
              "Predeclared promotion screen: ≥20% of the original paired deficit on each of",
              "four losses spanning three teams, no exposed winning-control reversal, then",
              "a top-20 test and finally ≥72/100 routes plus ≥143/200 seats on the full panel.", "",
              "Observed fixed-shop deficit recoveries: " + "; ".join(
                  f"{ep}: {gain:+,.0f}/{original:,.0f} ({100 * fraction:+.1f}%)"
                  for ep, gain, original, fraction in recoveries) + ".", "",
              f"Exposed control reversals: {fixed_control_reversals or 'none'}."
              " The 1-second per-action budget is " +
              ("met." if all(r["max_action_ms"] < 1000 for r in rows if r["arm"] == "candidate") else "breached."),
              "", "Do not promote unless the loss-recovery and control criteria both pass.", ""]
    return "\n".join(lines)


def _run_benchmark() -> None:
    manifest = json.loads(_PANEL_MANIFEST.read_text(encoding="utf-8"))
    baseline = json.loads(_PANEL_BASELINE.read_text(encoding="utf-8"))
    by_episode = {int(row["episode_id"]): row for row in manifest}
    declared = [{**by_episode[ep], "role": role, "team": team} for ep, role, team in _ROUTE_IDS]
    if len({r["episode_id"] for r in declared}) != len(_ROUTE_IDS):
        raise RuntimeError("preselected route manifest mismatch")
    tasks = [(route, seat) for route in declared for seat in (0, 1)]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for arm, mode in (("parent", "native"), ("candidate", "native"),
                          ("parent", "fixed"), ("candidate", "fixed")):
            previous = _paired_rows(rows)
            jobs = [
                (route, seat, arm, mode,
                 previous[(int(route["episode_id"]), seat, "parent", "native")]["shops"]
                 if mode == "fixed" else None)
                for route, seat in tasks
            ]
            futures = [pool.submit(_bench_one, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                row = future.result()
                rows.append(row)
                print(f"{arm:9s} {mode:6s} {row['team']} {row['episode_id']}"
                      f" seat={row['seat']} own/rival={row['candidate_cash']:.0f}/"
                      f"{row['rival_cash']:.0f} margin={row['margin']:+.0f}"
                      f" early_plants={len(row['early_tomato_sites'])}"
                      f" max_ms={row['max_action_ms']:.1f}", flush=True)
    rows.sort(key=lambda r: (int(r["episode_id"]), int(r["seat"]), r["arm"], r["mode"]))
    output = ROOT / "diagnostics/early_tomato_pilot_20260924.json"
    report = ROOT / "diagnostics/early_tomato_report_20260924.md"
    payload = {
        "parent_sha256": PARENT_SHA256,
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(_PANEL_MANIFEST.read_bytes()).hexdigest(),
        "parent_panel_sha256": hashlib.sha256(_PANEL_BASELINE.read_bytes()).hexdigest(),
        "selection": [{"episode_id": r["episode_id"], "team": r["team"], "role": r["role"]}
                      for r in declared],
        "rows": rows,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report.write_text(_report(rows, declared, baseline), encoding="utf-8")
    print(f"wrote {output} and {report}")


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--bench", action="store_true")
    args = parser.parse_args()
    if args.probe:
        from paired_benchmark import run_game
        route = next(row for row in json.loads(_PANEL_MANIFEST.read_text(encoding="utf-8"))
                     if int(row["episode_id"]) == 112941285)
        result = run_game(str(Path(__file__).resolve()), "rawroute:" + route["path"],
                          int(route["seed"]), 0, False, 156, {})
        print(json.dumps({k: result[k] for k in ("margin", "candidate_reward", "opponent_reward",
                                                 "candidate_timing", "candidate_telemetry")}, indent=2))
        return
    if args.bench:
        _run_benchmark()
        return
    parser.print_help()


if __name__ == "__main__":
    _main()
