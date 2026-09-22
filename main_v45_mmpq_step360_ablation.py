"""Local-only step-360 market ablation for one replay diagnosis."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_SOURCE = Path(__file__).resolve().parent / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py"
_SPEC = importlib.util.spec_from_file_location("_mmpq_v45", _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load V45 source")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)
HIRES = 9


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    if int((observation or {}).get("step", -1) or -1) == 360:
        result = copy.deepcopy(action)
        result["market"] = [["HIRE"] for _ in range(max(0, int(HIRES)))]
        return result
    return action
