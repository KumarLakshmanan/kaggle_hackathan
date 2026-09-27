"""Isolated complete-route counterfactual experiment. Never upload this file.

At the original day-six route commitment, compare incumbent route 9 with the
existing coherent route 0. Everything after that choice is executed by the
unchanged incumbent layers. This is an approximate planning model, not a
second invocation of the stateful agent or a simulator oracle.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
from pathlib import Path
import sys

from research_dynamic_planner_20260925 import economics as econ

_INCUMBENT_PATH = Path(__file__).with_name("main.py")
_INCUMBENT_SHA = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
if hashlib.sha256(_INCUMBENT_PATH.read_bytes()).hexdigest() != _INCUMBENT_SHA:
    raise RuntimeError("Incumbent changed during the route commitment experiment")
_spec = importlib.util.spec_from_file_location(__name__ + "_incumbent", _INCUMBENT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load frozen incumbent")
_incumbent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _incumbent
_spec.loader.exec_module(_incumbent)

_ORIGINAL_ROUTER = _incumbent._IMPL.chassis.router
_ROUTES = _incumbent._IMPL.chassis.routes
_MODE = "model"  # off/model/force; benchmark override only
_REPORT = dict(rc_triggered=0, rc_model_route0=0, rc_model_route9=0,
               rc_force_route0=0, rc_errors=0, rc_predicted_min=0.0,
               rc_predicted_mean=0.0, rc_failure_reason="")
_PRODUCTS = econ.PRODUCTS
_LAND_PRICES = (1000, 2000, 4000)


def _fibonacci(index: int) -> int:
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def _plan_action(route: int, step: int) -> dict:
    return _ROUTES[route if step < 648 else 2][step]


def _profiles(observation: dict, route: int) -> dict:
    """Predicted daily physical output from visible assets and route placements.

    Purchases are the ceiling for subsequent planned placements/plantings;
    repeated worker commands cannot silently create animals or seeds.
    """
    day0 = 6
    horizon = 24
    player = int(observation["player"])
    farm = observation["farms"][player]
    flows = {item: [0.0] * horizon for item in _PRODUCTS}
    crop_ready = Counter(observation["private"]["seeds"])
    animal_ready = Counter(observation["private"]["shed"])
    for inventory in observation["private"].get("inventories", []):
        animal_ready.update({k: v for k, v in inventory.items() if k in econ.ANIMALS})
    occupied = 0
    animals = 0
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                occupied += 1
                if tile.get("animal") in econ.ANIMALS:
                    animals += 1
                if tile.get("animal") in econ.ANIMALS or tile.get("crop") in econ.CROPS:
                    profile = econ._profile(tile, day0, horizon)
                    econ._add(flows, profile)
    current_land = len(farm["unlocked_quadrants"])
    land_capacity = current_land * 25
    placements = Counter()
    plantings = Counter()
    feed_actions = Counter()
    jobs = Counter()
    for step in range(144, 719):
        day = step // 24
        action = _plan_action(route, step)
        for order in action.get("market", []):
            if not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else ""
            quantity = max(0, int(order[2])) if len(order) > 2 else 1
            if op == "BUY_SEED" and item in econ.CROPS:
                crop_ready[item] += quantity
            elif op == "BUY_ANIMAL" and item in econ.ANIMALS:
                animal_ready[item] += quantity
            elif op == "BUY_LAND" and land_capacity < 100:
                land_capacity += 25
        for command in [action.get("farmer", ["PASS"])] + action.get("hands", []):
            if not command:
                continue
            op = command[0]
            jobs[day] += op not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST")
            feed_actions[day] += op == "FEED"
            item = command[1] if len(command) > 1 else ""
            if op == "PLACE" and item in econ.ANIMALS and animal_ready[item] > 0:
                if animals >= land_capacity - min(occupied, 25):
                    continue
                animal_ready[item] -= 1
                animals += 1
                placements[item] += 1
                profile = econ._new_profile(item, day, 30 - day)
                for product in _PRODUCTS:
                    for offset, value in enumerate(profile[product]):
                        flows[product][day - day0 + offset] += value
            elif op == "PLANT" and item in econ.CROPS and crop_ready[item] > 0:
                crop_ready[item] -= 1
                plantings[item] += 1
                profile = econ._new_profile(item, day, 30 - day)
                for product in _PRODUCTS:
                    for offset, value in enumerate(profile[product]):
                        flows[product][day - day0 + offset] += value
    # Jobs and feed are reservation checks. A route with a physically
    # unsupported feed schedule loses output credit in the affected days.
    return dict(flows=flows, placements=dict(placements),
                plantings=dict(plantings), jobs=dict(jobs),
                feed_actions=dict(feed_actions), animals=animals,
                land_capacity=land_capacity)


def _rival_profile(observation: dict) -> dict:
    player = int(observation["player"])
    farm = observation["farms"][1 - player]
    flows = {item: [0.0] * 24 for item in _PRODUCTS}
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and (tile.get("animal") in econ.ANIMALS
                                           or tile.get("crop") in econ.CROPS):
                econ._add(flows, econ._profile(tile, 6, 24))
    return flows


def _shop_list(observation: dict, day: int, future: tuple[int, ...]) -> list[str]:
    shops = list(observation["town"]["unlocked_shops"])
    shops.extend("YARN_STORE" for unlock_day in future if day >= unlock_day)
    return shops


def _consume(stock: dict, shops: list[str], center: bool) -> None:
    for shop in shops:
        products = econ.SHOP_PRODUCTS.get(shop, ())
        for item in products:
            stock[item] -= 2 if len(products) == 1 else 1
    if center:
        for item in _PRODUCTS:
            if item != "FERTILIZER":
                stock[item] -= 1


def _simulate(observation: dict, route: int, future: tuple[int, ...],
              physical: dict, rival_flow: dict) -> dict:
    player = int(observation["player"])
    cash = float(observation["farms"][player]["money"])
    rival_cash = float(observation["farms"][1 - player]["money"])
    stock = {item: float(observation["market"]["inventory"][item]) for item in _PRODUCTS}
    shed = Counter(observation["private"]["shed"])
    farm_goods = Counter()
    for inventory in observation["private"].get("inventories", []):
        farm_goods.update({item: value for item, value in inventory.items()
                           if item in _PRODUCTS})
    seed_count = Counter(observation["private"]["seeds"])
    animal_count = Counter({item: shed[item] for item in econ.ANIMALS})
    land_count = len(observation["farms"][player]["unlocked_quadrants"])
    failures = Counter()
    first_sale = {}
    sale_cash = Counter()
    buy_cost = Counter()
    minimum_cash = cash
    for step in range(144, 719):
        day = step // 24
        if step % 24 == 0:
            for item in _PRODUCTS:
                farm_goods[item] += max(0, physical["flows"][item][day - 6])
            hires_today = 0
        shops = _shop_list(observation, day, future)
        if step % 4 == 0:
            _consume(stock, shops, step % 24 == 0)
        action = _plan_action(route, step)
        # The engine resolves worker actions before market orders. A PLACE
        # product delivery is limited by predicted farm stock and shed room.
        for command in [action.get("farmer", ["PASS"])] + action.get("hands", []):
            if not command or command[0] != "PLACE" or len(command) < 2:
                continue
            item = command[1]
            if item not in _PRODUCTS:
                continue
            wanted = max(0, int(command[2])) if len(command) > 2 else 1
            quantity = min(wanted, int(farm_goods[item]),
                           max(0, 100 - sum(shed.values())))
            farm_goods[item] -= quantity
            shed[item] += quantity
        for order in action.get("market", []):
            if not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else ""
            wanted = max(0, int(order[2])) if len(order) > 2 else 1
            if op == "HIRE":
                cost = _fibonacci(hires_today)
                if cash >= cost:
                    cash -= cost
                    hires_today += 1
                    buy_cost["HIRE"] += cost
                else:
                    failures["HIRE:funding"] += 1
            elif op == "BUY_LAND":
                if land_count < 4:
                    cost = _LAND_PRICES[land_count - 1]
                    if cash >= cost:
                        cash -= cost
                        land_count += 1
                        buy_cost["BUY_LAND"] += cost
                    else:
                        failures["LAND:funding"] += 1
            elif op in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "SELL") and item:
                for _ in range(wanted):
                    if op == "BUY_SEED" and item in econ.CROPS:
                        price = econ.CROPS[item][0]
                        if cash < price:
                            failures["SEED:funding"] += 1
                            break
                        cash -= price
                        seed_count[item] += 1
                        buy_cost["SEED:" + item] += price
                    elif op == "BUY_ANIMAL" and item in econ.ANIMALS:
                        price = econ.ANIMALS[item][0]
                        if cash < price or sum(shed.values()) >= 100:
                            failures["ANIMAL:funding_or_room"] += 1
                            break
                        cash -= price
                        shed[item] += 1
                        animal_count[item] += 1
                        buy_cost["ANIMAL:" + item] += price
                    elif op == "BUY_PRODUCT" and item in _PRODUCTS:
                        price = econ.price(item, stock[item])
                        if cash < price or sum(shed.values()) >= 100:
                            failures["PRODUCT:funding_or_room"] += 1
                            break
                        cash -= price
                        shed[item] += 1
                        stock[item] -= 1
                        buy_cost["PRODUCT:" + item] += price
                    elif op == "SELL" and item in _PRODUCTS:
                        if shed[item] <= 0:
                            break
                        price = econ.price(item, stock[item])
                        cash += price
                        shed[item] -= 1
                        if price > 1:
                            stock[item] += 1
                        sale_cash[item] += price
                        first_sale.setdefault(item, day)
                    else:
                        break
        if step % 24 == 23:
            # Rival behavior is unknown. Use 60% of production inferred from
            # *visible* rival assets, identical under both route forecasts.
            for item in _PRODUCTS:
                quantity = max(0, round(0.6 * rival_flow[item][day - 6]))
                for _ in range(quantity):
                    price = econ.price(item, stock[item])
                    rival_cash += price
                    if price > 1:
                        stock[item] += 1
        minimum_cash = min(minimum_cash, cash)
    # The model cannot guarantee geometry or future rival actions. It checks
    # explicit reservations and returns unknowns for the native A/B test.
    feed_due = -sum(min(0, value) for value in physical["flows"]["WHEAT"])
    wheat_supply = (observation["private"]["shed"].get("WHEAT", 0)
                    + sum(max(0, value) for value in physical["flows"]["WHEAT"])
                    + sum(order[2] for step in range(144, 719)
                          for order in _plan_action(route, step).get("market", [])
                          if order and order[0] == "BUY_PRODUCT"
                          and len(order) > 2 and order[1] == "WHEAT"))
    feasible = (failures["HIRE:funding"] == 0 and failures["LAND:funding"] == 0
                and failures["ANIMAL:funding_or_room"] == 0
                and feed_due <= wheat_supply + 20)
    return dict(own=cash, rival=rival_cash, margin=cash - rival_cash,
                minimum_cash=minimum_cash, feasible=feasible,
                feed_due=feed_due, wheat_supply=wheat_supply,
                failures=dict(failures), first_sale=first_sale,
                sale_cash=dict(sale_cash), buy_cost=dict(buy_cost),
                placements=physical["placements"],
                plantings=physical["plantings"])


def _compare(observation: dict) -> dict:
    physical = {route: _profiles(observation, route) for route in (9, 0)}
    rival = _rival_profile(observation)
    scenarios = ((), (15,), (15, 21))
    rows = []
    for future in scenarios:
        base = _simulate(observation, 9, future, physical[9], rival)
        alternate = _simulate(observation, 0, future, physical[0], rival)
        rows.append(dict(future_yarn_days=future,
                         delta_own=alternate["own"] - base["own"],
                         delta_rival=alternate["rival"] - base["rival"],
                         delta_margin=alternate["margin"] - base["margin"],
                         base=base, alternate=alternate))
    margins = [row["delta_margin"] for row in rows]
    return dict(rows=rows, minimum=min(margins),
                mean=sum(margins) / len(margins),
                select=all(row["delta_margin"] > 0 and
                           row["alternate"]["feasible"] for row in rows))


def _router(observation: dict, step: int, state: dict) -> int:
    native = _ORIGINAL_ROUTER(observation, step, state)
    if _MODE == "off" or step != 144 or native != 9:
        return native
    shops = list(observation["town"]["unlocked_shops"][:2])
    if shops.count("YARN_STORE") != 1:
        return native
    _REPORT["rc_triggered"] += 1
    try:
        forecast = _compare(observation)
    except Exception as exc:
        _REPORT["rc_errors"] += 1
        _REPORT["rc_failure_reason"] = type(exc).__name__ + ": " + str(exc)[:120]
        return native
    _REPORT["rc_predicted_min"] = float(forecast["minimum"])
    _REPORT["rc_predicted_mean"] = float(forecast["mean"])
    if _MODE == "force":
        select = True
        _REPORT["rc_force_route0"] += 1
    elif _MODE == "model":
        select = bool(forecast["select"])
        _REPORT["rc_model_route0" if select else "rc_model_route9"] += 1
    else:
        raise ValueError(_MODE)
    if select:
        state["route"] = 0
        return 0
    return native


_incumbent._IMPL.chassis.router = _router


def agent(observation: dict, configuration=None):
    if int(observation["step"]) == 0:
        _REPORT.update(rc_triggered=0, rc_model_route0=0, rc_model_route9=0,
                       rc_force_route0=0, rc_errors=0, rc_predicted_min=0.0,
                       rc_predicted_mean=0.0, rc_failure_reason="")
    return _incumbent.agent(observation, configuration)


agent.telemetry = _REPORT
