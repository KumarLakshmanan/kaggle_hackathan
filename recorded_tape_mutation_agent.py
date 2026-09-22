"""Benchmark-only single-action mutation of a recorded candidate tape."""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path


_TAPE_PATH = ""
_MUTATION_STEP = -1
_MUTATION_INDEX = -1
_MUTATION_MODE = "none"
_MUTATION_DELTA = 0


def _load():
    with gzip.open(Path(_TAPE_PATH), "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


_ACTIONS = None


def agent(observation, configuration=None):
    global _ACTIONS
    if _ACTIONS is None:
        _ACTIONS = _load()
    step = int((observation or {}).get("step", 0) or 0)
    action = copy.deepcopy(_ACTIONS[min(max(0, step), len(_ACTIONS) - 1)])
    if step != int(_MUTATION_STEP):
        return action
    index = int(_MUTATION_INDEX)
    market = list(action.get("market") or [])
    if not 0 <= index < len(market):
        return action
    if _MUTATION_MODE == "drop":
        del market[index]
    elif _MUTATION_MODE == "delta":
        order = list(market[index])
        if len(order) >= 3:
            try:
                order[2] = max(0, int(order[2]) + int(_MUTATION_DELTA))
                market[index] = order
            except (TypeError, ValueError):
                pass
    action["market"] = market
    return action
