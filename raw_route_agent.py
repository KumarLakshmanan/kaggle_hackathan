"""Exact fixed-action agent for replay validation.

This module deliberately performs no repair, delay, or strategy transformation.
It is used only to replay a recorded player's action stream against the local
engine so that route extraction can be checked independently of any agent
logic.
"""

from __future__ import annotations

import copy
from typing import Any


ACTIONS: list[dict[str, Any]] = []
_CALLS = 0


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def agent(obs: Any, config: Any = None) -> dict[str, Any]:
    del config
    global _CALLS
    raw_step = _value(obs, "step", None)
    try:
        step = int(raw_step) if raw_step is not None else _CALLS
    except (TypeError, ValueError):
        step = _CALLS
    _CALLS += 1
    if not ACTIONS:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    step = max(0, min(step, len(ACTIONS) - 1))
    return copy.deepcopy(ACTIONS[step])
