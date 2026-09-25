"""Local experiment: sell a small amount of non-input stock at unusually high quotes.

This wraps the current opening-arm candidate and is intended only for paired
replay experiments. It does not inspect opponent identity or future tape actions.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent
_BASE_PATH = _ROOT / "main_frontier_h6_opening_arm_2026-09-24.py"
_SPEC = importlib.util.spec_from_file_location(
    f"h6_spike_probe_base_{__name__}", _BASE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load base candidate: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_H6 = _BASE._BASE
_PRICE_BASES = {
    item: float(params[0])
    for item, params in _H6._H6_MARKET_PARAMS.items()
    if item not in {"WHEAT", "FERTILIZER"}
}
_HIGH_QUOTE_RATIO = float(os.environ.get("KAGG_SPIKE_PRICE_RATIO", "0.55"))
_MAX_SELL_PER_TURN = int(os.environ.get("KAGG_SPIKE_MAX_SELL", "10"))
_MAX_SELL_PER_ITEM_EPISODE = int(os.environ.get("KAGG_SPIKE_ITEM_BUDGET", "0"))
_ITEM_BUDGETS = {
    item: int(
        os.environ.get(
            f"KAGG_SPIKE_BUDGET_{item}", str(_MAX_SELL_PER_ITEM_EPISODE)
        )
    )
    for item in _PRICE_BASES
}
_MIN_STOCK = 5
_DIAGNOSTICS: dict[str, Any] = {
    "spike_sell_checks": 0,
    "spike_sell_orders": 0,
    "spike_sell_units": 0,
    "spike_sell_ratio": _HIGH_QUOTE_RATIO,
    "spike_sell_cap": _MAX_SELL_PER_TURN,
    "spike_sell_item_budget": _MAX_SELL_PER_ITEM_EPISODE,
    **{f"spike_budget_{item.lower()}": budget for item, budget in _ITEM_BUDGETS.items()},
    **{
        key: 0
        for item in _PRICE_BASES
        for key in (f"spike_orders_{item.lower()}", f"spike_units_{item.lower()}")
    },
}


def agent(observation: Any, configuration: Any = None) -> Any:
    step = int(observation.get("step", -1)) if isinstance(observation, dict) else -1
    if step == 0:
        _DIAGNOSTICS["spike_sell_checks"] = 0
        _DIAGNOSTICS["spike_sell_orders"] = 0
        _DIAGNOSTICS["spike_sell_units"] = 0
        for item in _PRICE_BASES:
            _DIAGNOSTICS[f"spike_orders_{item.lower()}"] = 0
            _DIAGNOSTICS[f"spike_units_{item.lower()}"] = 0

    action = _BASE.agent(observation, configuration)
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return action

    _DIAGNOSTICS["spike_sell_checks"] += 1
    seat = int(observation.get("player", 0) or 0)
    farms = observation.get("farms", []) or []
    if not 0 <= seat < len(farms):
        return action

    market = [list(order) for order in (action.get("market") or [])]
    try:
        order_limit = int((configuration or {}).get("maxMarketOrdersPerTurn", 10))
    except (AttributeError, TypeError, ValueError):
        order_limit = 10
    if len(market) >= order_limit:
        return action

    private = observation.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    prices = (observation.get("market", {}) or {}).get("prices", {}) or {}
    already_selling = {
        order[1]
        for order in market
        if len(order) >= 2 and order[0] == "SELL"
    }

    candidates = []
    for item, base_price in _PRICE_BASES.items():
        if item in already_selling:
            continue
        price = float(prices.get(item, 0) or 0)
        stock = max(0, int(shed.get(item, 0) or 0))
        if price < base_price * _HIGH_QUOTE_RATIO or stock < _MIN_STOCK:
            continue
        already_sold = int(_DIAGNOSTICS.get(f"spike_units_{item.lower()}", 0))
        item_budget = _ITEM_BUDGETS[item]
        budget_left = (
            max(0, item_budget - already_sold)
            if item_budget > 0
            else stock
        )
        quantity = min(stock, _MAX_SELL_PER_TURN, budget_left)
        if quantity <= 0:
            continue
        candidates.append((-(price * quantity), item, quantity))

    if not candidates:
        return action

    _, item, quantity = min(candidates)
    market.append(["SELL", item, quantity])
    result = dict(action, market=market)
    _DIAGNOSTICS.update(getattr(_BASE.agent, "telemetry", {}) or {})
    _DIAGNOSTICS["spike_sell_orders"] = _DIAGNOSTICS.get("spike_sell_orders", 0) + 1
    _DIAGNOSTICS["spike_sell_units"] = _DIAGNOSTICS.get("spike_sell_units", 0) + quantity
    _DIAGNOSTICS[f"spike_orders_{item.lower()}"] = (
        _DIAGNOSTICS.get(f"spike_orders_{item.lower()}", 0) + 1
    )
    _DIAGNOSTICS[f"spike_units_{item.lower()}"] = (
        _DIAGNOSTICS.get(f"spike_units_{item.lower()}", 0) + quantity
    )
    return result


agent.telemetry = _DIAGNOSTICS
kaggle_submission_agent = agent
