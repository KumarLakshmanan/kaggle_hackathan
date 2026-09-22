"""Experimental boundary-switch harness for the public Thomas router.

This file is validation-only.  It advances both policies on every callback so
their private state remains synchronized, then returns the public-state router
from the configured switch step onward.  The switch step is supplied through
KAGGRICULTURE_SWITCH_STEP; production ``main.py`` never reads that variable.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


_BASE = _load(ROOT / "main.py", "hybrid_thomas_base")
_ALT = _load(
    ROOT / "kaggle_complete_agents_live_2026-09-22_page5_top100" /
    "100-thomastschinkel__kaggriculture-95-5-win-rate-via-replay-routing__7756dc86a48d.py",
    "hybrid_thomas_alt",
)

try:
    _SWITCH_STEP = int(os.environ.get("KAGGRICULTURE_SWITCH_STEP", "9999"))
except (TypeError, ValueError):
    _SWITCH_STEP = 9999


def agent(observation, configuration=None):
    base_action = _BASE.agent(copy.deepcopy(observation), configuration)
    alternate_action = _ALT.agent(copy.deepcopy(observation), configuration)
    step = int(observation.get("step", -1))
    return alternate_action if step >= _SWITCH_STEP else base_action

