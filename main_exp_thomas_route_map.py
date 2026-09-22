"""Validation-only public-state route selector.

This keeps `main.py`'s action/tape engine and reactive layers, but asks the
downloaded Thomas Tschinkel public-state tree which schedule family is active
at each 72-turn block.  The returned family is mapped to one of our existing
transparent route IDs.  It is deliberately isolated from production until a
replay-panel improvement is demonstrated.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = _load("thomas_route_map_base", ROOT / "main.py")
thomas = _load(
    "thomas_route_map_policy",
    ROOT
    / "kaggle_complete_agents_live_2026-09-22_page5_top100"
    / "100-thomastschinkel__kaggriculture-95-5-win-rate-via-replay-routing__7756dc86a48d.py",
)


def _mapping() -> dict[int, int]:
    raw = os.environ.get("KAGGRICULTURE_THOMAS_ROUTE_MAP", "12,12,12,12,12")
    values = [int(value.strip()) for value in raw.split(",") if value.strip()]
    if len(values) != 5:
        raise ValueError("KAGGRICULTURE_THOMAS_ROUTE_MAP needs five route IDs")
    if any(value not in base._ROUTES for value in values):
        raise ValueError(f"unknown route in {values}; available={sorted(base._ROUTES)}")
    return dict(enumerate(values))


ROUTE_MAP = _mapping()
_original_router = base._IMPL.chassis.router


def _router(observation, step, state):
    selected = _original_router(observation, step, state)
    try:
        step = int(step)
        if step == 0 or step < int(state.get("thomas_last_step", -1)):
            state.pop("thomas_route", None)
            state["thomas_block"] = -1
        state["thomas_last_step"] = step
        if step >= 144:
            block = step // 72
            if block != int(state.get("thomas_block", -1)):
                previous = int(state.get("thomas_route", 0))
                state["thomas_route"] = int(thomas.route_for(block, observation, previous))
                state["thomas_block"] = block
            return ROUTE_MAP.get(int(state.get("thomas_route", 0)), selected)
    except Exception:
        return selected
    return selected


base._IMPL.chassis.router = _router
if os.environ.get("KAGGRICULTURE_DISABLE_TERMINAL") == "1":
    base._PLANNER_NS["plan_terminal"] = lambda *args, **kwargs: {
        "accepted": False,
        "reason": "disabled by validation harness",
        "simulations": 0,
    }
agent = base.agent
