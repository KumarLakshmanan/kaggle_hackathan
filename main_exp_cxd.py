"""Experimental transfer of V57's bounded market-order counter.

The farming/route policy remains the current production main.  Only the
audited, observation-local CXD order search is applied after its clone gate;
the downloaded agent is never used as a stateful replacement.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load(ROOT / "main.py", "cxd_base_main")
_V57 = _load(
    ROOT / "kaggle_packed_agents_live_2026-09-22_current_page1_top100" /
    "003-ahmedberatozer__kaggriculture-v57-funding-order-invariant__packed.py",
    "cxd_v57_source",
)


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    try:
        step = int(observation.get("step", -1))
        if step >= 216 and _V57._v44y_clone_gate(observation):
            return _V57._cxd_reorder(copy.deepcopy(observation), copy.deepcopy(action))
    except Exception:
        return action
    return action
