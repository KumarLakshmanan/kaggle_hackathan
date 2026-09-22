"""Experiment: remove the first-turn wheat buy/sell round-trip.

This benchmark-only wrapper preserves the base policy's net five units of
wheat, but buys those five units directly instead of buying 20 and selling 15.
It does not modify the production entry point.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_v58_v52_base", _ROOT / "main_v52_before_v53_promotion.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load V52 base policy")
_BASE_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE_MODULE)
_BASE_AGENT = _BASE_MODULE.agent


def agent(observation: dict[str, Any], configuration=None):
    action = _BASE_AGENT(observation, configuration)
    step = int(observation.get("step", -1))
    if not isinstance(action, dict) or step != 0:
        return action

    orders = action.get("market")
    if not isinstance(orders, list):
        return action

    has_buy = any(
        isinstance(order, (list, tuple))
        and len(order) >= 2
        and order[0] == "BUY_PRODUCT"
        and order[1] == "WHEAT"
        for order in orders
    )
    has_sell = any(
        isinstance(order, (list, tuple))
        and len(order) >= 2
        and order[0] == "SELL"
        and order[1] == "WHEAT"
        for order in orders
    )
    if not (has_buy and has_sell):
        return action

    rewritten = []
    inserted = False
    for order in orders:
        if (
            isinstance(order, (list, tuple))
            and len(order) >= 2
            and order[0] == "BUY_PRODUCT"
            and order[1] == "WHEAT"
        ):
            if not inserted:
                rewritten.append(["BUY_PRODUCT", "WHEAT", 5])
                inserted = True
            continue
        if (
            isinstance(order, (list, tuple))
            and len(order) >= 2
            and order[0] == "SELL"
            and order[1] == "WHEAT"
        ):
            continue
        rewritten.append(list(order) if isinstance(order, tuple) else order)

    action["market"] = rewritten
    return action


agent.telemetry = {"experiment": "v58-direct-five-wheat-opening-buy"}
