"""Benchmark-only MMPQ hybrid: V43 step-360 market plus bounded Haideptry markets."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load("_mmpq_combo_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_HAIDE = _load("_mmpq_combo_haide", _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py")
_V43 = _load("_mmpq_combo_v43", _ROOT / "v43_refined_conditional_experiment.py")
MARKET_FROM_STEP = 300
MARKET_TO_STEP = 380


def _physical(action):
    return (list(action.get("farmer") or ["PASS"]), [list(x) for x in action.get("hands", []) or []])


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    haide = _HAIDE.agent(observation, configuration)
    v43 = _V43.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    if step == 360 and _physical(base) == _physical(v43):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(v43.get("market", []) or [])[:10])
        return result
    if MARKET_FROM_STEP <= step < MARKET_TO_STEP and _physical(base) == _physical(haide):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(haide.get("market", []) or [])[:10])
        return result
    return base

