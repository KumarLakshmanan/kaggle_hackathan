"""Local-only portfolio experiment: choose V43 or the preserved pre-V32 book.

The choice is deliberately based only on public farm state.  This is not the
production entrypoint and has no submission code.
"""

from __future__ import annotations

import copy

import main_before_v32_submission_backup as _old
import main_v43_current as _v43


_mode = {0: None, 1: None}
_last_step = {0: -1, 1: -1}


def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _choose(obs, seat: int) -> str:
    farms = list(_value(obs, "farms", []) or [])
    opponent = farms[1 - seat] if len(farms) > 1 else {}
    money = float(_value(opponent, "money", 3000.0) or 0.0)
    hands = len(list(_value(opponent, "hands", []) or []))
    # The low-cash, no-hand opening is the public signature for the route on
    # which the preserved pre-V32 book had its largest advantage.
    if money < 1800.0 and hands == 0:
        return "old"
    return "v43"


def agent(obs, configuration=None):
    seat = 1 if int(_value(obs, "player", 0) or 0) == 1 else 0
    step = int(_value(obs, "step", 0) or 0)
    if step == 0 or step < _last_step[seat]:
        _mode[seat] = None
    _last_step[seat] = step

    # Advance both books every turn so stateful V43 repair/router state stays
    # synchronized even when it is not the selected output.
    old_action = _old.agent(obs, configuration)
    v43_action = _v43.agent(obs, configuration)
    if _mode[seat] is None and step >= 1:
        _mode[seat] = _choose(obs, seat)
    return copy.deepcopy(old_action if _mode[seat] == "old" else v43_action)

