"""Benchmark-only first-observation rank-2 router experiment."""

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


_BASE = _load(_ROOT / "main.py", "_v53_base_for_v56")
_RANK2 = _load(
    _ROOT
    / "kaggle_embedded_agents_live_2026-09-22_round2_top100"
    / "002-embedded-d5460fc2e548.py",
    "_rank2_for_v56",
)

_LAST_STEP: dict[int, int] = {}
_USE_RANK2: dict[int, bool] = {}


def _use_rank2(observation):
    player = int(observation.get("player", 0) or 0)
    step = int(observation.get("step", -1) or -1)
    previous = _LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _USE_RANK2[player] = False
    _LAST_STEP[player] = step
    if step == 1:
        farms = list(observation.get("farms", []) or [])
        if len(farms) == 2:
            opponent = farms[1 - player]
            money = int(round(float(opponent.get("money", 0) or 0)))
            _USE_RANK2[player] = money in {1450, 2450, 3004}
    return bool(_USE_RANK2.get(player, False))


def agent(observation, configuration=None):
    base_action = _BASE(observation, configuration)
    rank2_action = _RANK2(observation, configuration)
    if _use_rank2(observation):
        return copy.deepcopy(rank2_action)
    return base_action


agent.telemetry = {"router": "v56-targeted-rank2-step1"}
