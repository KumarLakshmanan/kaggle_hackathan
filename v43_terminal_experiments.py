"""Local-only V43 terminal market ablation variants."""

from __future__ import annotations

import os

import main_v43_current as _base
from v19_terminal import terminal_market
from v23.policy_library import terminal_liquidation


_MODE = str(os.environ.get("V43_TERMINAL_MODE", "none"))


def agent(obs, configuration=None):
    action = _base.agent(obs, configuration)
    step = int((obs or {}).get("step", 0) or 0)
    if step != 718:
        return action
    if _MODE == "liquidation":
        return terminal_liquidation(obs, action)
    if _MODE in {"collision", "value", "existing"}:
        return terminal_market(obs, action, _MODE, replace=True)
    return action

