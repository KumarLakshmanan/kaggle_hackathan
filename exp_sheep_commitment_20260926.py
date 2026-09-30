"""Isolated day-11 counterfactual commitment experiment. Do not submit.

Only the six-sheep expansion decision is intercepted. The unchanged local
incumbent executes every action, including the entire sheep project if chosen.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path
import sys

_INCUMBENT_PATH = Path(__file__).with_name("main.py")
_INCUMBENT_SHA = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
if hashlib.sha256(_INCUMBENT_PATH.read_bytes()).hexdigest() != _INCUMBENT_SHA:
    raise RuntimeError("Incumbent source changed during the sheep commitment experiment")

_spec = importlib.util.spec_from_file_location(__name__ + "_incumbent", _INCUMBENT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load frozen incumbent")
_incumbent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _incumbent
_spec.loader.exec_module(_incumbent)

_ORIGINAL_ELIGIBILITY = _incumbent._v233_eligible
_BUNDLE_MODE = "model"  # off, model, force; benchmark override only
_STATE: dict[int, dict] = {}
_REPORT = dict(cc_triggered=0, cc_model_expand=0, cc_model_reject=0,
               cc_force_expand=0, cc_errors=0, cc_confirmed=0,
               cc_predicted_min=0.0, cc_predicted_mean=0.0)


def _shape(kind: str, x: float, scale: float) -> float:
    x = max(0.0, x)
    if kind == "sq":
        return x * x
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "log":
        return math.log1p(x)
    if kind == "linear":
        return x
    if kind == "hinge":
        u = x / scale
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    raise ValueError(kind)


def _price(item: str, stock: int, params: dict) -> int:
    """Installed engine's public market-price equation, including rounding."""
    p = params[item]
    base, initial, scale = p["base"], p["I0"], p["T"]
    if stock < initial:
        kind, target, gap = p["below_func"], p["below_target"], initial - stock
        value = base + target * base * _shape(kind, gap, scale) / _shape(kind, scale, scale)
    else:
        kind, target, gap = p["above_func"], p["above_target"], stock - initial
        value = base - target * base * _shape(kind, gap, scale) / _shape(kind, scale, scale)
    return max(1, round(value))


_DEFAULT_PARAMS = {
    "WOOL": dict(base=200, I0=10000, T=105, below_func="log",
                 below_target=0.20, above_func="sq", above_target=3.20),
    "FERTILIZER": dict(base=100, I0=10000, T=200, below_func="linear",
                       below_target=0.40, above_func="linear", above_target=0.40),
}


def _fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _visible_sheep(farm: dict) -> list[dict]:
    return [tile for row in farm["tiles"] for tile in row
            if isinstance(tile, dict) and tile.get("animal") == "SHEEP"]


def _native_hires(native: dict, day: int) -> int:
    tape = _incumbent._IMPL.chassis.routes[native["route"]]
    return sum(bool(order) and order[0] == "HIRE"
               for action in tape[day * 24:min((day + 1) * 24, 719)]
               for order in action.get("market", []))


def _wool_units(sheep: list[dict], day: int) -> int:
    # Existing visible sheep are a conservative half-care forecast; their
    # actual future worker/market behavior remains endogenous in validation.
    count = 0
    for tile in sheep:
        placed = int(tile.get("placed_day", -100))
        if day >= placed + 6 and (day - placed - 6) % 3 == 0:
            count += 2
    return count


def _project_wool_units(start_day: int, day: int) -> int:
    age = day - start_day
    if age < 6 or (age - 6) % 3:
        return 0
    return 6 * (6 if age == 6 else 4)


def _sell(stock: int, quantity: int, params: dict, item: str) -> tuple[int, int]:
    receipts = 0
    for _ in range(quantity):
        quote = _price(item, stock, params)
        receipts += quote
        if quote > 1:
            stock += 1
    return stock, receipts


def _simulate(observation: dict, native: dict, extra_yarn: tuple[int, ...],
              project: bool) -> dict:
    """Marginal time-indexed sheep cash flow under one shop scenario.

    Existing production and workers are the same in both arms. All future
    prices are predictions from current legal public state, never game events.
    """
    player = int(observation["player"])
    own, rival = observation["farms"][player], observation["farms"][1 - player]
    market = observation["market"]
    params = {key: dict(_DEFAULT_PARAMS[key]) for key in _DEFAULT_PARAMS}
    for key in params:
        params[key].update((market.get("params") or {}).get(key, {}))
    wool_stock = int(market["inventory"]["WOOL"])
    fert_stock = int(market["inventory"]["FERTILIZER"])
    own_sheep, rival_sheep = _visible_sheep(own), _visible_sheep(rival)
    current_yarn = sum(shop == "YARN_STORE" for shop in observation["town"]["unlocked_shops"])
    wheat_quote = int(market["prices"]["WHEAT"])
    own_receipts = rival_receipts = 0
    capital = 7000 if project else 0
    feed_cost = wage_cost = 0
    first_sale_day = None
    project_wool_units = project_fert_units = 0
    for day in range(11, 30):
        yarn = current_yarn + sum(day >= unlock for unlock in extra_yarn)
        # Six shop-consumption ticks per day, two wool per Yarn Store,
        # plus one town-center wool purchase. Fertilizer has no town demand.
        wool_stock -= 12 * yarn + 1
        own_existing = _wool_units(own_sheep, day)
        rival_existing = _wool_units(rival_sheep, day)
        if project:
            feed_cost += 6 * wheat_quote
            h = _native_hires(native, day)
            wage_cost += _fib(h) + _fib(h + 1)
        wool_new = _project_wool_units(11, day) if project else 0
        # Three collected fertilizer units per day is deliberately below
        # the six-unit physical maximum. Actual harvest/sale is audited later.
        fert_new = 3 if project and day >= 12 else 0
        project_wool_units += wool_new
        project_fert_units += fert_new
        if (wool_new or fert_new) and first_sale_day is None:
            first_sale_day = day
        wool_stock, amount = _sell(wool_stock, own_existing + wool_new, params, "WOOL")
        own_receipts += amount
        wool_stock, amount = _sell(wool_stock, rival_existing, params, "WOOL")
        rival_receipts += amount
        fert_stock, amount = _sell(fert_stock, fert_new, params, "FERTILIZER")
        own_receipts += amount
    return dict(own_net=own_receipts - capital - feed_cost - wage_cost,
                rival_net=rival_receipts, own_receipts=own_receipts,
                rival_receipts=rival_receipts, capital=capital,
                feed_cost=feed_cost, wage_cost=wage_cost,
                wool_units=project_wool_units, fert_units=project_fert_units,
                first_sale_day=first_sale_day)


def _compare(observation: dict, native: dict) -> dict:
    """Compare complete funded project and incumbent on three shop futures."""
    scenarios = ((), (18,), (15, 24))
    rows = []
    for future in scenarios:
        incumbent = _simulate(observation, native, future, False)
        project = _simulate(observation, native, future, True)
        own = project["own_net"] - incumbent["own_net"]
        rival = project["rival_net"] - incumbent["rival_net"]
        rows.append(dict(future_yarn_days=future, own_delta=own,
                         rival_delta=rival, margin_delta=own-rival,
                         project=project))
    return dict(rows=rows, minimum=min(row["margin_delta"] for row in rows),
                mean=sum(row["margin_delta"] for row in rows) / len(rows),
                select=all(row["margin_delta"] > 0 for row in rows))


def _eligible(observation: dict, native: dict) -> bool:
    original = _ORIGINAL_ELIGIBILITY(observation, native)
    if _BUNDLE_MODE == "off" or int(observation["step"]) // 24 != 11:
        return original
    player = int(observation["player"])
    shops = list(observation["town"]["unlocked_shops"])
    if shops.count("YARN_STORE") != 1:
        return original
    state = _STATE.setdefault(player, {})
    if state.get("decided"):
        return state["expand"]
    # Relax only the shop-count predicate. The incumbent's land, inventory,
    # worker, quote, existing-reservation and funding guards still execute.
    probe = dict(observation, town=dict(observation["town"],
                                        unlocked_shops=shops + ["YARN_STORE"]))
    if not _ORIGINAL_ELIGIBILITY(probe, native):
        return original
    try:
        forecast = _compare(observation, native)
    except Exception:
        _REPORT["cc_errors"] += 1
        return original
    if _BUNDLE_MODE == "force":
        chosen = True
        _REPORT["cc_force_expand"] += 1
    elif _BUNDLE_MODE == "model":
        chosen = bool(forecast["select"])
        _REPORT["cc_model_expand" if chosen else "cc_model_reject"] += 1
    else:
        raise ValueError(_BUNDLE_MODE)
    state.update(decided=True, expand=chosen, forecast=forecast)
    _REPORT["cc_triggered"] += 1
    _REPORT["cc_predicted_min"] = float(forecast["minimum"])
    _REPORT["cc_predicted_mean"] = float(forecast["mean"])
    return chosen


_incumbent._v233_eligible = _eligible


def agent(observation: dict, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _STATE.clear()
        _REPORT.update(cc_triggered=0, cc_model_expand=0, cc_model_reject=0,
                       cc_force_expand=0, cc_errors=0, cc_confirmed=0,
                       cc_predicted_min=0.0, cc_predicted_mean=0.0)
    result = _incumbent.agent(observation, configuration)
    _REPORT["cc_confirmed"] = int(_incumbent._V233_REPORT.get("sheep_committed", 0))
    return result


agent.telemetry = _REPORT
