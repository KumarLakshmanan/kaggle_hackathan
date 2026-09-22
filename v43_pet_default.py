"""Benchmark-only V43 variant forcing the five-hand PET opening to default."""

from __future__ import annotations

import v43_refined_conditional_experiment as _v43


_adaptive = _v43._adaptive
_router = _adaptive._ROUTER
_original = _router.selected_route


def _route(observation, configuration=None):
    result = _original(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    seat = 1 if int((observation or {}).get("player", 0) or 0) == 1 else 0
    shops = list(((observation or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    farms = list((observation or {}).get("farms", []) or [])
    opponent = farms[1 - seat] if len(farms) == 2 else {}
    if step == 88 and shops and str(shops[0]) == "PET_CAFE" and len(opponent.get("hands", []) or []) == 5:
        _adaptive._CHOICE[seat] = "default"
        return "default"
    return result


_router.selected_route = _route


def agent(observation, configuration=None):
    return _v43.agent(observation, configuration)
