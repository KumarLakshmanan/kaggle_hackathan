"""Benchmark-only step-zero market opening variants on the current agent."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("step0_variant_main", _ROOT / "main.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load main.py")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

_STEP0_MARKET = None


def agent(observation, configuration=None):
    action = copy.deepcopy(_MODULE.agent(observation, configuration))
    step = int((observation or {}).get("step", -1) or -1)
    # Kaggriculture's first callback is observation step 1; the simulator's
    # action tape has index 0 for that callback.
    if step == 1 and _STEP0_MARKET is not None:
        action["market"] = copy.deepcopy(_STEP0_MARKET)
    return action
