"""Benchmark-only first-action opening probes against V46."""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
from pathlib import Path


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ROOT = Path(__file__).resolve().parent
_base = _load("v46_first_open_base", _ROOT / "main.py")


def _tape(name):
    with gzip.open(_ROOT / name, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


_OPENINGS = {
    "main": _tape("record_main_brunch.json.gz"),
    "v49": _tape("record_v49_brunch.json.gz"),
    "amey": _tape("record_amey_brunch.json.gz"),
    "v43": _tape("record_v43_brunch.json.gz"),
    "c14": _tape("record_c14_brunch.json.gz"),
}
_OPENING = "main"
_OPENING_STEPS = 1
_CALLS = 0


def agent(observation, configuration=None):
    global _CALLS
    base_action = _base.agent(observation, configuration)
    if _CALLS < int(_OPENING_STEPS):
        step = int((observation or {}).get("step", 0) or 0)
        _CALLS += 1
        return copy.deepcopy(_OPENINGS[_OPENING][min(step, 718)])
    _CALLS += 1
    return base_action
