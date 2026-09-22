"""Benchmark-only one-action mutation of a recorded V47 tape."""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path


_ROOT = Path(__file__).resolve().parent
_TAPE_NAME = "third"
_MUTATION_STEP = -1
_MUTATION_INDEX = -1
_MUTATION_MODE = "none"
_MUTATION_DELTA = 0


def _read_tape(name):
    path = _ROOT / f"record_main_{name}_2026-09-21.json.gz"
    if name == "brunch":
        path = _ROOT / "record_main_brunch.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


_TAPE_CACHE = {
    "brunch": _read_tape("brunch"),
    "otter": _read_tape("otter"),
    "third": _read_tape("third"),
}


def agent(observation, configuration=None):
    step = int((observation or {}).get("step", 0) or 0)
    tape = _TAPE_CACHE.get(str(_TAPE_NAME), _TAPE_CACHE["third"])
    action = copy.deepcopy(tape[min(max(0, step), len(tape) - 1)])
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
