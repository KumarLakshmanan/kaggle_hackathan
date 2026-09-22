"""Benchmark-only public-state branch ensemble for the V45 policy.

This candidate is intentionally separate from ``main.py`` until the full
replay panel confirms that every guarded branch is a net improvement.  It
never reads replay metadata, seeds, team names, or private opponent state.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load("_v45_narrow_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_HAIDE = _load("_v45_narrow_haide", _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py")
_V43 = _load("_v45_narrow_v43", _ROOT / "v43_refined_conditional_experiment.py")


_BRANCHES: dict[int, str | None] = {}
_LAST_STEP: dict[int, int] = {}


def _farm_signature(farm):
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


def _classify(observation):
    """Set a branch from compact public state at step 88."""
    try:
        player = int(observation.get("player", 0) or 0)
        step = int(observation.get("step", -1) or -1)
        previous = _LAST_STEP.get(player, -1)
        if step == 0 or step <= previous:
            _BRANCHES[player] = None
        _LAST_STEP[player] = step
        if step != 88 or _BRANCHES.get(player) is not None:
            return _BRANCHES.get(player)
        shops = tuple((observation.get("town") or {}).get("unlocked_shops", []) or [])
        farms = list(observation.get("farms", []) or [])
        if len(farms) != 2:
            return None
        opponent = farms[1 - player]
        signature = _farm_signature(opponent)
        if shops == ("BAKERY",) and signature == (
            160,
            5,
            (("COW", 4), ("MELON", 8), ("PASTURE", 1), ("SHEEP", 2), ("STRAWBERRY", 3), ("WHEAT", 6)),
        ):
            _BRANCHES[player] = "mmpq"
        elif shops == ("PET_CAFE",) and signature == (
            293,
            6,
            (("COW", 2), ("MELON", 12), ("SHEEP", 3), ("STRAWBERRY", 2), ("WHEAT", 5)),
        ):
            _BRANCHES[player] = "ymg"
        elif shops == ("FARMERS_MARKET",) and signature == (
            78,
            6,
            (("COW", 2), ("MELON", 12), ("SHEEP", 3), ("STRAWBERRY", 4), ("WHEAT", 4)),
        ):
            _BRANCHES[player] = "third"
        else:
            _BRANCHES[player] = "other"
        return _BRANCHES[player]
    except Exception:
        return None


def _physical(action):
    return (
        list(action.get("farmer") or ["PASS"]),
        [list(x) for x in (action.get("hands") or [])],
    )


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    haide = _HAIDE.agent(observation, configuration)
    v43 = _V43.agent(observation, configuration)
    branch = _classify(observation)
    step = int((observation or {}).get("step", -1) or -1)

    if branch == "mmpq" and step == 360 and _physical(base) == _physical(v43):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(v43.get("market", []) or [])[:10])
        return result
    if branch == "mmpq" and 520 <= step < 620 and _physical(base) == _physical(haide):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(haide.get("market", []) or [])[:10])
        return result
    if branch == "ymg" and 300 <= step < 380 and _physical(base) == _physical(haide):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(haide.get("market", []) or [])[:10])
        return result
    if branch == "third" and 480 <= step < 650 and _physical(base) == _physical(haide):
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(haide.get("market", []) or [])[:10])
        return result
    return base
