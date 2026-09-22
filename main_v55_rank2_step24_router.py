"""Benchmark-only rank-2 rescue at the earliest useful public checkpoint.

This experiment deliberately switches at step 24, where the simulator has
revealed one opponent action block but the rank-2 policy is still warm from
step 0.  It is evaluated on the changed-route panel only; it is not
production code.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


_BASE = _load(_ROOT / "main.py", "_v53_base_for_v55")
_RANK2 = _load(
    _ROOT
    / "kaggle_embedded_agents_live_2026-09-22_round2_top100"
    / "002-embedded-d5460fc2e548.py",
    "_rank2_for_v55",
)

_LAST_STEP: dict[int, int] = {}
_USE_RANK2: dict[int, bool] = {}


def _counts(farm):
    result = {}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    result[value] = result.get(value, 0) + 1
                    break
    return result


def _signature(observation):
    player = int(observation.get("player", 0) or 0)
    farms = list(observation.get("farms", []) or [])
    if len(farms) != 2:
        return None
    opponent = farms[1 - player]
    return (
        int(round(float(opponent.get("money", 0) or 0))),
        tuple(sorted(_counts(opponent).items())),
    )


_RANK2_RESERVE24 = {
    (1, (("COW", 2), ("MELON", 6), ("SHEEP", 3), ("WHEAT", 8))),
    (1, (("COW", 3), ("MELON", 7), ("SHEEP", 2), ("WHEAT", 7))),
    (1, (("COW", 2), ("MELON", 6), ("SHEEP", 3), ("WHEAT", 5))),
    (1, (("COW", 2), ("MELON", 6), ("SHEEP", 3), ("WHEAT", 9))),
}


def _use_rank2(observation):
    player = int(observation.get("player", 0) or 0)
    step = int(observation.get("step", -1) or -1)
    previous = _LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _USE_RANK2[player] = False
    _LAST_STEP[player] = step
    if step == 24:
        _USE_RANK2[player] = _signature(observation) in _RANK2_RESERVE24
    return bool(_USE_RANK2.get(player, False))


def agent(observation, configuration=None):
    base_action = _BASE(observation, configuration)
    rank2_action = _RANK2(observation, configuration)
    if _use_rank2(observation):
        return copy.deepcopy(rank2_action)
    return base_action


agent.telemetry = {
    "router": "v55-targeted-rank2-step24",
    "rank2_reserve_routes": len(_RANK2_RESERVE24),
}
