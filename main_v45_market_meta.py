"""Local-only V45 market meta-controller.

This candidate keeps V45's action book and conditionally borrows market
proposals from the downloaded Haideptry/V43 policies.  The gate uses only the
public first unlocked shop and requires exact farmer/hand agreement.
"""

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


_BASE = _load("_v45_meta_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_HAIDE = _load("_v45_meta_haide", _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py")
_V43 = _load("_v45_meta_v43", _ROOT / "v43_refined_conditional_experiment.py")

HAIDE_FROM_STEP = 168
V43_FROM_STEP = 144


def _physical(action):
    return (list(action.get("farmer") or ["PASS"]), [list(x) for x in action.get("hands", []) or []])


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    haide = _HAIDE.agent(observation, configuration)
    v43 = _V43.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    town = (observation or {}).get("town", {}) or {}
    shops = [str(x) for x in town.get("unlocked_shops", []) or []]
    first = shops[0] if shops else ""
    proposal = None
    if first == "SMOOTHIE_SHOP" and step >= V43_FROM_STEP and _physical(base) == _physical(v43):
        proposal = v43
    elif first in {"ICE_CREAM_SHOP", "PIZZA_SHOP"} and step >= HAIDE_FROM_STEP and _physical(base) == _physical(haide):
        proposal = haide
    if proposal is None:
        return base
    result = copy.deepcopy(base)
    result["market"] = copy.deepcopy(list(proposal.get("market", []) or [])[:10])
    return result
