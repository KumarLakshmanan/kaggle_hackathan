"""Benchmark-only multi-action mutation of a recorded candidate tape."""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path


_TAPE_PATH = ""
_MUTATIONS = []


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
    market = list(action.get("market") or [])
    for mutation in _MUTATIONS:
        if int(mutation.get("step", -1)) != step:
            continue
        index = int(mutation.get("index", -1))
        if not 0 <= index < len(market):
            continue
        if mutation.get("mode") == "drop":
            del market[index]
            continue
        if mutation.get("mode") == "delta":
            order = list(market[index])
            if len(order) >= 3:
                try:
                    order[2] = max(0, int(order[2]) + int(mutation.get("delta", 0)))
                    market[index] = order
                except (TypeError, ValueError):
                    pass
    action["market"] = market
    return action
