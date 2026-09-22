"""MMPQ-only step-360 market ablation for the local replay panel."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_v45_step360_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py"
)
_BASE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_BASE)

MARKET_VARIANT = 0


def _market(variant):
    hires = lambda n: [["HIRE"] for _ in range(n)]
    if variant == 1:
        return hires(7)
    if variant == 2:
        return hires(8)
    if variant == 3:
        return hires(9)
    if variant == 4:
        return hires(10)
    if variant == 5:
        return [["SELL", "MILK", 9], *hires(9)]
    if variant == 6:
        return [["SELL", "EGG", 4], *hires(9)]
    if variant == 7:
        return [["SELL", "MILK", 9], ["SELL", "EGG", 4], *hires(8)]
    if variant == 8:
        return [*hires(9), ["SELL", "MILK", 9]]
    if variant == 9:
        return [*hires(9), ["SELL", "EGG", 4]]
    if variant == 10:
        return [*hires(8), ["SELL", "MILK", 9], ["SELL", "EGG", 4]]
    if variant == 11:
        return [*hires(7), ["SELL", "MILK", 9], ["SELL", "EGG", 4]]
    if variant == 12:
        return [*hires(8), ["SELL", "MILK", 9]]
    if variant == 13:
        return [*hires(8), ["SELL", "EGG", 4]]
    return None


def agent(observation, configuration=None):
    action = _BASE.agent(observation, configuration)
    if int((observation or {}).get("step", -1) or -1) != 360:
        return action
    proposal = _market(int(MARKET_VARIANT))
    if proposal is None:
        return action
    result = copy.deepcopy(action)
    result["market"] = proposal
    return result

