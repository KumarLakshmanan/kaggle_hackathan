"""Local-only switchboard for controlled Frontier candidate ablations.

This adapter imports the unmodified plaintext candidate and exposes switches
that the benchmark harness can set with ``--candidate-override``. It is not a
Kaggle submission entrypoint.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any


_CANDIDATE_PATH = (
    Path(__file__).resolve().parent
    / "kaggle_complete_agents_live_2026-09-23_pages11-13_verified"
    / "frontier_plaintext_candidate"
    / "main_exp_frontier_moon_candidate_2026-09-23.py"
)
_SPEC = importlib.util.spec_from_file_location("frontier_ablation_subject", _CANDIDATE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load candidate source: {_CANDIDATE_PATH}")
_CANDIDATE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _CANDIDATE
_SPEC.loader.exec_module(_CANDIDATE)

DISABLE_IG_OPENING_REPAIR = False
DISABLE_VQ_COMPACTION = False
DISABLE_IG_CASH_QUEUE = False
DISABLE_SEEDFLOAT = False
DISABLE_FERTILIZER_KNOCKOUT = False
ENABLE_GUARDED_COW9 = False
ENABLE_UNDERFILLED_PASTURE_COW = False
ENABLE_H6_CLONE_GATED_PREEMPT = os.environ.get("KAGGRICULTURE_H6_CLONE_GATE", "0") == "1"
ENABLE_H6_DEMAND_RANK = os.environ.get("KAGGRICULTURE_H6_DEMAND_RANK", "0") == "1"

_ORIGINAL_IG_OPENING_REPAIR = _CANDIDATE._ig_guard_opening
_ORIGINAL_VQ_COMPACTION = _CANDIDATE._vq_compact
_ORIGINAL_ADV_APPLY = _CANDIDATE._adv_apply
_ORIGINAL_IG_CASH = _CANDIDATE._IG_CASH
_ORIGINAL_SEEDFLOAT_FROM = _CANDIDATE._33_SF_FROM
_ORIGINAL_KNOCKOUT = dict(_CANDIDATE._33_KO)
_DIAGNOSTICS = {
    "cow_place_orders": 0,
    "cow_place_with_inventory": 0,
    "cow_place_on_empty_pasture": 0,
    "cow_place_blocked_with_adjacent_pasture": 0,
    "cow_place_blocked_without_adjacent_pasture": 0,
    "empty_cow_pastures_step718": 0,
    "cows_in_unit_inventory_step718": 0,
    "owned_cows_step289": 0,
    "milk_demand_shops_step289": 0,
    "money_step289": 0,
    "market_orders_step289": 0,
    "cow_buy_orders_step289": 0,
    "cow9_guard_eligible_step289": 0,
    "cow9_extra_buys": 0,
    "empty_cow_pastures_step289": 0,
    "underfilled_cow_eligible_step289": 0,
    "underfilled_cow_extra_buys": 0,
    "h6_clone_gate_checks": 0,
    "h6_clone_gate_passes": 0,
    "h6_clone_gate_skips": 0,
    "h6_demand_rank_checks": 0,
    "h6_demand_rank_changed": 0,
    "h6_demand_urgent_orders": 0,
}

_H6_PRICE_FLOOR = 1
_H6_DEMAND_ALPHA = 0.25
_H6_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_H6_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def _identity_action(observation: Any, action: Any) -> Any:
    return action


def _configure_candidate() -> None:
    _CANDIDATE._ig_guard_opening = (
        _identity_action if DISABLE_IG_OPENING_REPAIR else _ORIGINAL_IG_OPENING_REPAIR
    )
    _CANDIDATE._vq_compact = (
        _identity_action if DISABLE_VQ_COMPACTION else _ORIGINAL_VQ_COMPACTION
    )
    _CANDIDATE._IG_CASH = frozenset() if DISABLE_IG_CASH_QUEUE else _ORIGINAL_IG_CASH
    _CANDIDATE._33_SF_FROM = 720 if DISABLE_SEEDFLOAT else _ORIGINAL_SEEDFLOAT_FROM
    knockout = dict(_ORIGINAL_KNOCKOUT)
    if DISABLE_FERTILIZER_KNOCKOUT:
        knockout.update(frm=720, to=719)
    _CANDIDATE._33_KO = knockout
    _CANDIDATE._adv_apply = (
        _h6_clone_gated_adv_apply
        if ENABLE_H6_CLONE_GATED_PREEMPT
        else _ORIGINAL_ADV_APPLY
    )


def _public_signature(farm: dict[str, Any]) -> tuple[int, int, tuple[int, ...]]:
    keys = (
        "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
        "COW", "SHEEP", "GOOSE", "PASTURE", "COOP", "WEED",
    )
    counts = {key: 0 for key in keys}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (
        len(farm.get("hands", []) or []),
        len(farm.get("unlocked_quadrants", []) or []),
        tuple(counts[key] for key in sorted(counts)),
    )


def _clone_distance(observation: dict[str, Any]) -> int:
    farms = list(observation.get("farms", []) or [])
    if len(farms) < 2:
        return 10**9
    left = _public_signature(farms[0])
    right = _public_signature(farms[1])
    return (
        abs(left[0] - right[0])
        + 3 * abs(left[1] - right[1])
        + sum(abs(a - b) for a, b in zip(left[2], right[2]))
    )


def _h6_clone_gated_adv_apply(observation: Any, action: Any) -> Any:
    step = int(observation.get("step", -1))
    if step % 24 == 23 or not _CANDIDATE._ADV_FROM <= step < _CANDIDATE._ADV_TO:
        return _ORIGINAL_ADV_APPLY(observation, action)
    _DIAGNOSTICS["h6_clone_gate_checks"] += 1
    if _clone_distance(observation) > 6:
        _DIAGNOSTICS["h6_clone_gate_skips"] += 1
        return action
    _DIAGNOSTICS["h6_clone_gate_passes"] += 1
    return _ORIGINAL_ADV_APPLY(observation, action)


def _h6_shape(name: str, value: float) -> float:
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return value ** 0.5
    if name == "log":
        import math
        return math.log1p(value)
    if name == "log10":
        import math
        return math.log10(1.0 + value)
    raise ValueError(name)


def _h6_market_price(item: str, inventory: int) -> int:
    import math
    base, equilibrium, scale, below_func, below_target, above_func, above_target = _H6_MARKET_PARAMS[item]
    if inventory < equilibrium:
        amplitude = below_target * base / _h6_shape(below_func, scale)
        price = base + amplitude * _h6_shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _h6_shape(above_func, scale)
        price = base - amplitude * _h6_shape(above_func, inventory - equilibrium)
    return max(_H6_PRICE_FLOOR, int(round(price)))


def _h6_demand_per_day(observation: dict[str, Any], configuration: Any, item: str) -> float:
    def _cfg(name: str, default: int) -> int:
        try:
            return int(configuration.get(name, default) or default)
        except (AttributeError, TypeError, ValueError):
            return default

    shops = list((observation.get("town", {}) or {}).get("unlocked_shops", []) or [])
    turns_per_day = _cfg("turnsPerDay", 24)
    shop_interval = max(1, _cfg("townShopSellInterval", 4))
    demand = 0.0
    for shop in shops:
        products = _H6_SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += (turns_per_day / shop_interval) * (2 if len(products) == 1 else 1)
    if item != "FERTILIZER":
        center_interval = max(1, _cfg("townCenterSellInterval", 24))
        demand += turns_per_day / center_interval
    return demand


def _h6_order_score(observation: dict[str, Any], configuration: Any, order: Any) -> tuple[float, bool]:
    if not isinstance(order, (list, tuple)) or len(order) < 3 or order[0] != "SELL" or order[1] not in _H6_MARKET_PARAMS:
        return float("-inf"), False
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0, False
    market = observation.get("market", {}) or {}
    inventory = market.get("inventory", {}) or {}
    prices = market.get("prices", {}) or {}
    current_inventory = int(inventory.get(item, 10000) or 0)
    current_quote = float(prices.get(item, _h6_market_price(item, current_inventory)) or 0)
    later_quote = float(_h6_market_price(item, current_inventory + quantity))
    score = float(quantity) * max(0.0, current_quote - later_quote)
    if score <= 0.0:
        return score, False
    demand = max(0.25, _h6_demand_per_day(observation, configuration, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _H6_DEMAND_ALPHA * urgency), urgency > 0.0


def _h6_rank_sell_slots(observation: dict[str, Any], action: Any, configuration: Any) -> Any:
    if not isinstance(action, dict):
        return action
    market = list(action.get("market") or [])
    rows = []
    urgent = 0
    for index, order in enumerate(market):
        if isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] == "SELL" and order[1] in _H6_MARKET_PARAMS:
            score, is_urgent = _h6_order_score(observation, configuration, order)
            urgent += int(is_urgent)
            rows.append((score, -index, list(order)))
    if len(rows) < 2:
        return action
    _DIAGNOSTICS["h6_demand_rank_checks"] += 1
    _DIAGNOSTICS["h6_demand_urgent_orders"] += urgent
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    revised = [next(ranked) if isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] == "SELL" and order[1] in _H6_MARKET_PARAMS else order for order in market]
    if revised == market:
        return action
    _DIAGNOSTICS["h6_demand_rank_changed"] += 1
    return dict(action, market=revised)


def _empty_cow_pasture(tile: Any) -> bool:
    return isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal")


def _tile_at(farm: dict[str, Any], position: Any) -> Any:
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        return None
    try:
        x, y = int(position[0]), int(position[1])
        rows = farm.get("tiles", [])
        if 0 <= y < len(rows) and 0 <= x < len(rows[y]):
            return rows[y][x]
    except (TypeError, ValueError):
        return None
    return None


def _record_cow_placement_diagnostics(observation: Any, action: Any) -> None:
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return
    step = int(observation.get("step", -1))
    seat = int(observation.get("player", 0))
    farms = observation.get("farms", [])
    if not 0 <= seat < len(farms):
        return
    farm = farms[seat]
    positions = [farm.get("farmer"), *list(farm.get("hands", []) or [])]
    commands = [action.get("farmer", ["PASS"]), *list(action.get("hands", []) or [])]
    private = observation.get("private", {}) or {}
    inventories = list(private.get("inventories", []) or [])
    for actor_index, command in enumerate(commands):
        if not isinstance(command, (list, tuple)) or len(command) < 2 or command[:2] != ["PLACE", "COW"]:
            continue
        _DIAGNOSTICS["cow_place_orders"] += 1
        inventory = inventories[actor_index] if actor_index < len(inventories) else {}
        if int((inventory or {}).get("COW", 0) or 0) <= 0:
            continue
        _DIAGNOSTICS["cow_place_with_inventory"] += 1
        position = positions[actor_index] if actor_index < len(positions) else None
        if _empty_cow_pasture(_tile_at(farm, position)):
            _DIAGNOSTICS["cow_place_on_empty_pasture"] += 1
            continue
        try:
            x, y = int(position[0]), int(position[1])
        except (IndexError, TypeError, ValueError):
            _DIAGNOSTICS["cow_place_blocked_without_adjacent_pasture"] += 1
            continue
        has_adjacent = any(
            _empty_cow_pasture(_tile_at(farm, (x + dx, y + dy)))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
        key = (
            "cow_place_blocked_with_adjacent_pasture"
            if has_adjacent
            else "cow_place_blocked_without_adjacent_pasture"
        )
        _DIAGNOSTICS[key] += 1

    if step == 718:
        rows = farm.get("tiles", []) or []
        _DIAGNOSTICS["empty_cow_pastures_step718"] = sum(
            _empty_cow_pasture(tile) for row in rows for tile in (row or [])
        )
        _DIAGNOSTICS["cows_in_unit_inventory_step718"] = sum(
            max(0, int((inventory or {}).get("COW", 0) or 0))
            for inventory in inventories
        )
    if step == 289:
        owned = sum(
            isinstance(tile, dict) and tile.get("animal") == "COW"
            for row in (farm.get("tiles", []) or [])
            for tile in (row or [])
        )
        owned += max(0, int((private.get("shed", {}) or {}).get("COW", 0) or 0))
        owned += sum(max(0, int((inventory or {}).get("COW", 0) or 0)) for inventory in inventories)
        shops = list((observation.get("town", {}) or {}).get("unlocked_shops", []) or [])
        milk_demand = sum(shop in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for shop in shops)
        market = list(action.get("market", []) or [])
        empty_pastures = sum(
            isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal")
            for row in (farm.get("tiles", []) or [])
            for tile in (row or [])
        )
        cow_buys = sum(
            isinstance(order, (list, tuple))
            and len(order) >= 2
            and order[0] == "BUY_ANIMAL"
            and order[1] == "COW"
            for order in market
        )
        money = float(farm.get("money", 0) or 0)
        eligible = (
            owned == 8
            and milk_demand >= 2
            and money >= 800
            and len(market) < 10
            and cow_buys == 0
        )
        underfilled_eligible = (
            owned < 8
            and empty_pastures > 0
            and milk_demand >= 1
            and money >= 800
            and len(market) < 10
            and cow_buys == 0
        )
        _DIAGNOSTICS["owned_cows_step289"] = owned
        _DIAGNOSTICS["milk_demand_shops_step289"] = milk_demand
        _DIAGNOSTICS["money_step289"] = int(money)
        _DIAGNOSTICS["market_orders_step289"] = len(market)
        _DIAGNOSTICS["cow_buy_orders_step289"] = cow_buys
        _DIAGNOSTICS["cow9_guard_eligible_step289"] = int(eligible)
        _DIAGNOSTICS["empty_cow_pastures_step289"] = empty_pastures
        _DIAGNOSTICS["underfilled_cow_eligible_step289"] = int(underfilled_eligible)


def _guarded_cow9(observation: Any, action: Any) -> Any:
    if not ENABLE_GUARDED_COW9 or not isinstance(action, dict):
        return action
    if int(observation.get("step", -1)) != 289:
        return action
    if not _DIAGNOSTICS["cow9_guard_eligible_step289"]:
        return action
    market = [list(order) for order in (action.get("market", []) or [])]
    market.append(["BUY_ANIMAL", "COW", 1])
    _DIAGNOSTICS["cow9_extra_buys"] += 1
    return dict(action, market=market)


def _underfilled_pasture_cow(observation: Any, action: Any) -> Any:
    if not ENABLE_UNDERFILLED_PASTURE_COW or not isinstance(action, dict):
        return action
    if int(observation.get("step", -1)) != 289:
        return action
    if not _DIAGNOSTICS["underfilled_cow_eligible_step289"]:
        return action
    market = [list(order) for order in (action.get("market", []) or [])]
    market.append(["BUY_ANIMAL", "COW", 1])
    _DIAGNOSTICS["underfilled_cow_extra_buys"] += 1
    return dict(action, market=market)


def agent(observation: Any, configuration: Any = None) -> Any:
    _configure_candidate()
    if int(observation.get("step", -1)) == 0:
        for key in _DIAGNOSTICS:
            _DIAGNOSTICS[key] = 0
    action = _CANDIDATE.agent(observation, configuration)
    _record_cow_placement_diagnostics(observation, action)
    action = _guarded_cow9(observation, action)
    action = _underfilled_pasture_cow(observation, action)
    if ENABLE_H6_DEMAND_RANK:
        action = _h6_rank_sell_slots(observation, action, configuration)
    return action


agent.telemetry = _DIAGNOSTICS
kaggle_submission_agent = agent
