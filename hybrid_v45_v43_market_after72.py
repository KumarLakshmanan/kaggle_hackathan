"""Benchmark-only V45 physical policy with V43 market-order overlay after shop reveal."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import v43_refined_conditional_experiment as _alt


_PATH = Path(__file__).resolve().parent / "main_v45_before_v46_2026-09-21.py"
_SPEC = importlib.util.spec_from_file_location("overlay_v45_base", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
_base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_base)


def agent(observation, configuration=None):
    base = _base.agent(observation, configuration)
    alternate = _alt.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if step >= 72 and shops and str(shops[0]) == "BRUNCH_SPOT":
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(alternate.get("market", []) or [])[:10])
        return result
    return base
