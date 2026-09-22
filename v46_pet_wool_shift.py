"""Benchmark-only one-turn V46 PET market-timing probe."""

from __future__ import annotations

import copy

import main as _base


def agent(observation, configuration=None):
    action = copy.deepcopy(_base.agent(observation, configuration))
    step = int((observation or {}).get("step", 0) or 0)
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if not shops or str(shops[0]).upper() != "PET_CAFE":
        return action
    market = list(action.get("market", []) or [])
    if step == 162:
        action["market"] = [["SELL", "WOOL", 2], *market][:10]
    elif step == 163:
        action["market"] = [order for order in market if order != ["SELL", "WOOL", 2]]
    return action

