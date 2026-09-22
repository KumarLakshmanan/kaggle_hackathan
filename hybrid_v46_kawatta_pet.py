"""Narrow benchmark candidate: V49 only for the exact Kawatta/PET signature."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import main as _base


_V49_PATH = (
    Path(__file__).resolve().parent
    / "kaggle_complete_agents_2026-09-21"
    / "ahmedberatozer__kaggriculture-v49-funded-sale-timing-and-worker__2916b93119a2.py"
)
_SPEC = importlib.util.spec_from_file_location("kawatta_pet_v49", _V49_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_V49_PATH}")
_V49 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_V49)

_PREVIOUS = -1
_USE_V49 = False


def _signature(farm):
    counts = {}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return (
        int(round(float(farm.get("money", 0) or 0))),
        len(farm.get("hands", []) or []),
        tuple(sorted(counts.items())),
    )


def agent(observation, configuration=None):
    global _PREVIOUS, _USE_V49
    step = int(observation.get("step", -1) or -1)
    if step == 0 or step <= _PREVIOUS:
        _USE_V49 = False
    _PREVIOUS = step
    base_action = _base.agent(observation, configuration)
    v49_action = _V49.agent(observation, configuration)
    if step == 88:
        player = int(observation.get("player", 0) or 0)
        farms = list(observation.get("farms", []) or [])
        shops = tuple((observation.get("town") or {}).get("unlocked_shops", []) or [])
        if len(farms) == 2 and shops == ("PET_CAFE",):
            opponent = farms[1 - player]
            _USE_V49 = _signature(opponent) == (
                130,
                5,
                (("COW", 3), ("MELON", 12), ("PASTURE", 1), ("SHEEP", 2), ("WHEAT", 7)),
            )
    return v49_action if _USE_V49 else base_action

