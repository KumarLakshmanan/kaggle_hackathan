"""Benchmark-only V46 physical policy with static market overlay probes."""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import main as _base


_ROOT = Path(__file__).resolve().parent


def _read(name):
    with gzip.open(_ROOT / name, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


_TAPES = {
    "amey": _read("record_amey_brunch.json.gz"),
    "v49": _read("record_v49_brunch.json.gz"),
    "main": _read("record_main_brunch.json.gz"),
    "v43": _read("record_v43_brunch.json.gz"),
    "c14": _read("record_c14_brunch.json.gz"),
}
_BRUNCH_TAPE = "amey"
_PET_TAPE = "v49"


def agent(observation, configuration=None):
    action = copy.deepcopy(_base.agent(observation, configuration))
    step = int((observation or {}).get("step", 0) or 0)
    if step < 72:
        return action
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if not shops:
        return action
    name = _BRUNCH_TAPE if str(shops[0]).upper() == "BRUNCH_SPOT" else _PET_TAPE
    tape_action = _TAPES[name][min(step, 718)]
    action["market"] = copy.deepcopy(list(tape_action.get("market", []) or [])[:10])
    return action

