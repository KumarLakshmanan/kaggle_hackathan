"""Benchmark-only hybrid: keep both engines synchronized, then switch at a threshold."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import v43_refined_conditional_experiment as _v43


_PATH = Path(__file__).resolve().parent / "main_v45_before_v46_2026-09-21.py"
_SPEC = importlib.util.spec_from_file_location("hybrid_v45_base", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
_v45 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_v45)

_SWITCH_STEP = 72


def agent(observation, configuration=None):
    step = int((observation or {}).get("step", -1) or -1)
    v43_action = _v43.agent(observation, configuration)
    v45_action = _v45.agent(observation, configuration)
    return v43_action if step >= _SWITCH_STEP else v45_action
