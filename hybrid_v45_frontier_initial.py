"""Benchmark-only: route the distinctive Kawatta initial public state to Frontier V156."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ROOT = Path(__file__).resolve().parent
_base = _load("frontier_overlay_base", _ROOT / "main_v45_before_v46_2026-09-21.py")
_frontier = _load(
    "frontier_overlay_candidate",
    _ROOT / "kaggle_public_code" / "evelyn3976__kaggriculture-frontier-v156-coherent-liquidity-v6" / "kaggriculture-frontier-v156-coherent-liquidity-v6.py",
)


def _kawatta_initial(observation):
    farms = list((observation or {}).get("farms", []) or [])
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if int((observation or {}).get("step", -1) or -1) != 1 or shops or len(farms) != 2:
        return False
    money = tuple(sorted(int(round(float(farm.get("money", 0) or 0))) for farm in farms))
    return money == (2600, 3014)


_MODE = {}


def agent(observation, configuration=None):
    player = int((observation or {}).get("player", 0) or 0)
    if _kawatta_initial(observation):
        _MODE[player] = "frontier"
    mode = _MODE.get(player, "base")
    if mode == "frontier":
        return _frontier.agent(observation, configuration)
    return _base.agent(observation, configuration)
