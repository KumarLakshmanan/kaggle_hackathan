"""Benchmark-only static action-tape splice probe.

The simulator exposes the first shop at step 72.  This probe lets the search
harness combine a common opening tape with a shop-specific continuation.  It
never submits or modifies ``main.py``.
"""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def _read(path: str):
    with gzip.open(_ROOT / path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["actions"]


_TAPES = {
    "amey": _read("record_amey_brunch.json.gz"),
    "v49": _read("record_v49_brunch.json.gz"),
    "main": _read("record_main_brunch.json.gz"),
    "v45": _read("record_v45_brunch.json.gz"),
    "v43": _read("record_v43_brunch.json.gz"),
    "c14": _read("record_c14_brunch.json.gz"),
}

_PREFIX_TAPE = "main"
_BRUNCH_TAPE = "amey"
_PET_TAPE = "v49"
_SWITCH_STEP = 72


def agent(observation, configuration=None):
    step = int((observation or {}).get("step", 0) or 0)
    if step < _SWITCH_STEP:
        source = _TAPES[_PREFIX_TAPE]
    else:
        shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
        source = _TAPES[_BRUNCH_TAPE if shops and str(shops[0]).upper() == "BRUNCH_SPOT" else _PET_TAPE]
    return copy.deepcopy(source[min(max(0, step), len(source) - 1)])

