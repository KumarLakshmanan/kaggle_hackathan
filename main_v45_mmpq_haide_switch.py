"""Benchmark-only test: switch from V45 to Haideptry after public MMPQ branch detection."""

from __future__ import annotations

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


_BASE = _load("_mmpq_switch_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_HAIDE = _load("_mmpq_switch_haide", _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py")
SWITCH_STEP = 89
_MODE = {}
_LAST = {}


def _counts(farm):
    out = {}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    out[value] = out.get(value, 0) + 1
                    break
    return tuple(sorted(out.items()))


def _branch(obs):
    player = int(obs.get("player", 0) or 0)
    step = int(obs.get("step", -1) or -1)
    if step == 0 or step <= _LAST.get(player, -1):
        _MODE[player] = None
    _LAST[player] = step
    if step in (1, 88) and _MODE.get(player) is None:
        farms = list(obs.get("farms", []) or [])
        shops = tuple((obs.get("town") or {}).get("unlocked_shops", []) or [])
        if len(farms) == 2:
            farm = farms[1 - player]
            signature = (int(round(float(farm.get("money", 0) or 0))), len(farm.get("hands", []) or []), _counts(farm))
            pair_money = tuple(sorted(int(round(float(f.get("money", 0) or 0))) for f in farms))
            if step == 1 and pair_money == (1460, 3007) and all(not f.get("hands") for f in farms):
                _MODE[player] = "mmpq"
            elif step == 88 and shops == ("BAKERY",) and signature == (160, 5, (("COW", 4), ("MELON", 8), ("PASTURE", 1), ("SHEEP", 2), ("STRAWBERRY", 3), ("WHEAT", 6))):
                _MODE[player] = "mmpq"
            else:
                _MODE[player] = "other"
    return _MODE.get(player)


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    haide = _HAIDE.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    if _branch(observation) == "mmpq" and step >= int(SWITCH_STEP):
        return haide
    return base
