"""Standalone stock-clipped H6 sale-slot ranking experiment; not submitted."""

from collections import Counter
import importlib.util
from pathlib import Path
import sys
import time


SOURCE = Path(__file__).with_name("main.py")
MODULE_NAME = f"h6_stock_parent_{time.time_ns()}"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SOURCE)
assert SPEC is not None and SPEC.loader is not None
INCUMBENT = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = INCUMBENT
SPEC.loader.exec_module(INCUMBENT)


def _stock_clipped_rank(observation: dict, action: dict) -> dict:
    if not isinstance(action, dict):
        return action
    market = action.get("market") or []
    products = [order[1] for order in market if isinstance(order, list)
                and len(order) >= 3 and order[0] == "SELL"
                and order[1] in INCUMBENT._H6_MARKET_PARAMS]
    if len(products) < 2 or len(set(products)) != len(products):
        return action
    if any(isinstance(order, list) and len(order) >= 3
           and order[0] == "BUY_PRODUCT" and order[1] in products
           for order in market):
        return action
    stock = INCUMBENT.projected_shed(action, INCUMBENT.FarmView(observation))
    rows = []
    slots = []
    for index, order in enumerate(market):
        if not isinstance(order, list) or len(order) < 3 or order[0] != "SELL":
            continue
        if order[1] not in INCUMBENT._H6_MARKET_PARAMS:
            continue
        effective = min(max(0, int(order[2])), max(0, int(stock.get(order[1], 0))))
        scored_order = list(order)
        scored_order[2] = effective
        score, _ = INCUMBENT._h6_order_score(observation, None, scored_order)
        rows.append((score, -index, list(order)))
        slots.append(index)
    rows.sort(reverse=True)
    revised = [list(order) if isinstance(order, list) else order for order in market]
    for index, row in zip(slots, rows):
        revised[index] = row[2]
    if revised == market:
        return action
    return dict(action, market=revised)


def agent(observation, configuration=None):
    action = INCUMBENT.agent(observation, configuration)
    try:
        if not INCUMBENT._ig_standard(configuration):
            return action
        return _stock_clipped_rank(observation, action)
    except Exception:
        return action


kaggle_submission_agent = agent
