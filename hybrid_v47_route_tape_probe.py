"""Benchmark-only route-suffix probe for V47.

V47 remains in control until a public opponent signature is visible.  The
selected downloaded action book is then tried from a configurable step.  This
file is deliberately separate from ``main.py`` and never submits anything.
"""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
from pathlib import Path

import main as _base


_ROOT = Path(__file__).resolve().parent
_PREVIOUS = -1
_MODE = None

# These are overridden by the local grid harness through paired_benchmark's
# normal module-setting mechanism.
_SWITCH_STEP = 1
_OTTER_TAPE = "v43"
_THIRD_TAPE = "frontier"


def _load_tape(name: str):
    if name == "frontier":
        path = (
            _ROOT
            / "kaggle_public_code"
            / "evelyn3976__kaggriculture-frontier-v156-coherent-liquidity-v6"
            / "kaggriculture-frontier-v156-coherent-liquidity-v6.py"
        )
        spec = importlib.util.spec_from_file_location("route_probe_frontier", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actions = module._ACTIONS
        return [copy.deepcopy(action) for action in actions]
    path = _ROOT / {
        "v43": "record_v43_brunch.json.gz",
        "amey": "record_amey_brunch.json.gz",
        "v49": "record_v49_brunch.json.gz",
        "main": "record_main_brunch.json.gz",
    }.get(name, "record_v43_brunch.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


_TAPES = {name: _load_tape(name) for name in ("v43", "amey", "v49", "main", "frontier")}


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


def agent(observation, configuration=None):
    global _PREVIOUS, _MODE
    step = int(observation.get("step", -1) or -1)
    if step == 0 or step <= _PREVIOUS:
        _PREVIOUS = step
        _MODE = None
    else:
        _PREVIOUS = step

    base_action = _base.agent(observation, configuration)
    if step == 1 and _MODE is None:
        player = int(observation.get("player", 0) or 0)
        farms = list(observation.get("farms", []) or [])
        if len(farms) == 2:
            opponent = _farm_signature(farms[1 - player])
            if opponent == (6, 3, ()):
                _MODE = "otter"
            elif opponent == (33, 4, (("PASTURE", 1),)):
                _MODE = "third"

    if step >= int(_SWITCH_STEP) and _MODE in {"otter", "third"}:
        name = _OTTER_TAPE if _MODE == "otter" else _THIRD_TAPE
        tape = _TAPES.get(str(name), _TAPES["v43"])
        if 0 <= step < len(tape):
            return copy.deepcopy(tape[step])
    return base_action

