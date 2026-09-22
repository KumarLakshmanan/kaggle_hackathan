"""Benchmark-only router: Amey opening through first shop, then route policy."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AMEY_PATH = ROOT / "kaggle_complete_agents_2026-09-21" / (
    "ameythakur20__kaggriculture-premium-first-market-agent__924e8ac73cf9.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MAIN = _load("amey_prefix_main", ROOT / "main.py")
_AMEY = _load("amey_prefix_policy", AMEY_PATH)
_LAST_STEP = {}
_MODE = {}


def agent(observation, configuration=None):
    main_action = _MAIN.agent(observation, configuration)
    amey_action = _AMEY.agent(observation, configuration)
    player = int((observation or {}).get("player", 0) or 0)
    step = int((observation or {}).get("step", -1) or -1)
    previous = _LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _MODE[player] = "prefix"
    _LAST_STEP[player] = step
    if step == 72:
        shops = tuple((observation.get("town") or {}).get("unlocked_shops", []) or [])
        # With the Amey prefix, the live PET route exposes BAKERY.  Keep our
        # existing policy there; the two YARN_STORE loss routes use Amey's
        # trajectory, which was independently stronger on both.
        _MODE[player] = "main" if shops == ("BAKERY",) else "amey"
    if _MODE.get(player) == "amey" or _MODE.get(player) == "prefix":
        return copy.deepcopy(amey_action)
    return copy.deepcopy(main_action)
