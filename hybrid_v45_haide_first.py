"""Benchmark-only first-opening ensemble probe; never used for submission."""

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
_base = _load("first_base", _ROOT / "main_v45_before_v46_2026-09-21.py")
_haide = _load(
    "first_haide",
    _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py",
)
_CALLS = 0
_MODE = None


def _signature(observation):
    farms = list((observation or {}).get("farms", []) or [])
    if len(farms) != 2:
        return None
    player = int((observation or {}).get("player", 0) or 0)
    opponent = farms[1 - player]
    return (
        int(round(float(opponent.get("money", 0) or 0))),
        len(opponent.get("hands", []) or []),
        len(opponent.get("unlocked_quadrants", []) or []),
    )


def agent(observation, configuration=None):
    global _CALLS, _MODE
    _CALLS += 1
    if _MODE is None:
        base_action = _base.agent(observation, configuration)
        haide_action = _haide.agent(observation, configuration)
        signature = _signature(observation)
        if _CALLS >= 2:
            _MODE = "haide" if signature in {(6, 3, 1), (33, 4, 1)} else "base"
        # Probe whether the Haide opening is a useful universal first move.
        return haide_action
    if _MODE == "haide":
        return _haide.agent(observation, configuration)
    return _base.agent(observation, configuration)

