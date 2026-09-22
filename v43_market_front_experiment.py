"""Local-only V43 market-order placement ablation."""

from __future__ import annotations

import main_v43_current as _base
from scripts.v22_market_impact import reorder_market


def agent(obs, configuration=None):
    del configuration
    return reorder_market(obs, _base.agent(obs), mode="impact_front")

