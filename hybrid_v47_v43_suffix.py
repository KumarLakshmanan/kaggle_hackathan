"""Local-only probe: keep V47's first action, then try V43 on named routes.

This is an offline benchmark candidate.  It is intentionally not imported by
``main.py`` and never submits anything.
"""

from __future__ import annotations

import copy

import main as _base
import main_v43_current as _v43


_PREVIOUS = -1
_USE_V43 = False


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
    global _PREVIOUS, _USE_V43
    step = int(observation.get("step", -1) or -1)
    if step == 0 or step <= _PREVIOUS:
        _USE_V43 = False
    _PREVIOUS = step

    base_action = _base.agent(observation, configuration)
    if step == 1:
        player = int(observation.get("player", 0) or 0)
        farms = list(observation.get("farms", []) or [])
        if len(farms) == 2:
            opponent = _farm_signature(farms[1 - player])
            # This public state is unique to the captured Otter opening.
            _USE_V43 = opponent == (6, 3, ())

    if _USE_V43:
        try:
            return copy.deepcopy(_v43.agent(observation, configuration))
        except Exception:
            return base_action
    return base_action

