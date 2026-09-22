"""Local-only V45 + GoodPJW market proposal ablation."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load("_v45_good_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_ALT = _load("_goodpjw_market_proposal", _ROOT / "kaggle_extracted_agents_2026-09-21" / "goodpjw_melon_2749.py")
MARKET_FROM_STEP = 144


def _physical(action):
    return (list(action.get("farmer") or ["PASS"]), [list(x) for x in action.get("hands", []) or []])


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    alt = _ALT.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    if step < MARKET_FROM_STEP or _physical(base) != _physical(alt):
        return base
    result = copy.deepcopy(base)
    result["market"] = copy.deepcopy(list(alt.get("market", []) or [])[:10])
    return result
