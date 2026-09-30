"""Local-only H6 price-shape correction for Kaggriculture 1.32.7.

Keep the incumbent action policy unchanged except for H6's SELL-slot score
estimate when carrot, tomato, or egg inventory is deeply scarce. Those three
resources use the engine's hinge curve, not the linear approximation in main.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys


_SPEC = importlib.util.spec_from_file_location(__name__ + "_base", Path(__file__).with_name("main.py"))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot load main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_ORIGINAL_PRICE = _BASE._h6_market_price
_ENGINE_HINGE_PRODUCTS = {"CARROT", "TOMATO", "EGG"}
_STATS = {"hinge_price_differences": 0, "max_abs_quote_difference": 0}


def _hinge(x: float, throughput: float) -> float:
    u = max(0.0, x) / throughput
    return u + 8.0 * max(0.0, u - 1.0) ** 2


def _exact_h6_price(item: str, inventory: int) -> int:
    if item not in _ENGINE_HINGE_PRODUCTS:
        return _ORIGINAL_PRICE(item, inventory)
    base, equilibrium, throughput, _, below_target, _, _ = _BASE._H6_MARKET_PARAMS[item]
    if item == "CARROT":
        # The installed engine's scarce-side target is 1.0, not H6's 0.2.
        below_target = 1.0
    if inventory >= equilibrium:
        return _ORIGINAL_PRICE(item, inventory)
    scarcity = equilibrium - inventory
    result = max(1, int(round(base + below_target * base * _hinge(scarcity, throughput))))
    original = _ORIGINAL_PRICE(item, inventory)
    if result != original:
        _STATS["hinge_price_differences"] += 1
        _STATS["max_abs_quote_difference"] = max(
            _STATS["max_abs_quote_difference"], abs(result - original)
        )
    return result


_BASE._h6_market_price = _exact_h6_price


def agent(observation, configuration=None):
    if isinstance(observation, dict) and int(observation.get("step", -1)) == 0:
        _STATS.update(hinge_price_differences=0, max_abs_quote_difference=0)
    return _BASE.agent(observation, configuration)


agent.telemetry = _STATS
kaggle_submission_agent = agent
