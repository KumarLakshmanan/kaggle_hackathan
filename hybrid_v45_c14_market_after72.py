"""Benchmark-only V45 physical policy with C14 market-order overlay after PET reveal."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ALT_PATH = Path(__file__).resolve().parent / "kaggle_public_code" / "beicicc__kaggriculture-c14-late-crop-weed-recovery" / "kaggriculture-c14-late-crop-weed-recovery.py"
_ALT_SPEC = importlib.util.spec_from_file_location("overlay_c14", _ALT_PATH)
if _ALT_SPEC is None or _ALT_SPEC.loader is None:
    raise RuntimeError(f"cannot load {_ALT_PATH}")
_alt = importlib.util.module_from_spec(_ALT_SPEC)
_ALT_SPEC.loader.exec_module(_alt)

_BASE_PATH = Path(__file__).resolve().parent / "main_v45_before_v46_2026-09-21.py"
_BASE_SPEC = importlib.util.spec_from_file_location("overlay_v45_base_c14", _BASE_PATH)
if _BASE_SPEC is None or _BASE_SPEC.loader is None:
    raise RuntimeError(f"cannot load {_BASE_PATH}")
_base = importlib.util.module_from_spec(_BASE_SPEC)
_BASE_SPEC.loader.exec_module(_base)


def agent(observation, configuration=None):
    base = _base.agent(observation, configuration)
    alternate = _alt.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if step >= 72 and shops and str(shops[0]) == "PET_CAFE":
        result = copy.deepcopy(base)
        result["market"] = copy.deepcopy(list(alternate.get("market", []) or [])[:10])
        return result
    return base
