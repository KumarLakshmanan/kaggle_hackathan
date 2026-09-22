"""Step-360 market parameter sweep for the MMPQ residual replay."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_v45_step360_grid_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py"
)
_BASE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_BASE)

SALE_ITEM = "MILK"
SALE_Q = 9
MILK_Q = 9
EGG_Q = 0
HIRES = 9
SALE_FIRST = True


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    if int((observation or {}).get("step", -1) or -1) != 360:
        return action
    market = []
    if SALE_ITEM:
        market.append(["SELL", str(SALE_ITEM), int(SALE_Q)])
    else:
        if int(MILK_Q) > 0:
            market.append(["SELL", "MILK", int(MILK_Q)])
        if int(EGG_Q) > 0:
            market.append(["SELL", "EGG", int(EGG_Q)])
    hire_orders = [["HIRE"] for _ in range(max(0, int(HIRES)))]
    if SALE_FIRST:
        market.extend(hire_orders)
    else:
        market = hire_orders + market
    if len(market) > 10:
        return action
    result = copy.deepcopy(action)
    result["market"] = market
    return result
