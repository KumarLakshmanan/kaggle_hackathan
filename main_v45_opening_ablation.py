"""Local-only V45 opening ablation.

The production candidate is ``main.py``.  This wrapper is used to test the
single Pipe16/V9 opening-market change in isolation; it does not belong in a
submission because it imports the extracted benchmark source by path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


_SOURCE = Path(__file__).resolve().parent / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py"
_SPEC = importlib.util.spec_from_file_location("_v45_opening_base", _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_SOURCE}")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)

OPENING = "aurax"
_V9_OPENING = [
    ["BUY_PRODUCT", "WHEAT", 13],
    ["BUY_PRODUCT", "WHEAT", 30],
    ["SELL", "WHEAT", 30],
]


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    if int((observation or {}).get("step", -1) or -1) == 0 and OPENING == "v9":
        action = dict(action)
        action["market"] = [list(order) for order in _V9_OPENING]
    return action
