"""Experimental Kaggriculture policy shell (not a Kaggle submission file).

This file keeps the tested main.py policy frozen and applies only explicitly
selected, observation-legal research overlays. It is intentionally separate
from main.py, and depends on main.py at import time. A promising overlay must
be independently tested and bundled into a single-file artifact before any
submission. Default MODE remains ``baseline`` until an experiment is selected.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("main.py")
_SPEC = importlib.util.spec_from_file_location(__name__ + "_frozen_main", _SOURCE)
_MAIN = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MAIN
_SPEC.loader.exec_module(_MAIN)
_BASE_AGENT = _MAIN.agent

MODE = "baseline"
_STATS = {
    "research_calls": 0, "research_changes": 0, "research_errors": 0,
    "shadow_exposures": 0, "shadow_units": 0,
}
_BASE_PRICE = {"CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
               "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200}
_ANIMAL_OUTPUT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def _rival_ready(observation):
    """Visible rival output that a worker standing on its tile can collect."""
    rival = observation["farms"][1-int(observation["player"])]
    ready = {}
    for location in {tuple(pos) for pos in [rival["farmer"], *(rival.get("hands") or [])]}:
        x, y = int(location[0]), int(location[1])
        tile = rival["tiles"][y][x]
        if not isinstance(tile, dict):
            continue
        item = _ANIMAL_OUTPUT.get(tile.get("animal"), tile.get("crop"))
        units = max(0, int(tile.get("yield_units", 0) or 0))
        if item in _BASE_PRICE and units >= 2:
            ready[item] = ready.get(item, 0) + units
    return ready


def _planned_sale(player, step, item, lookahead=24):
    """Read only the incumbent's own future tape; never a rival or replay."""
    for t in range(step + 5, min(719, step + lookahead + 1)):
        for order in _MAIN._adv_future(player, t):
            if len(order) >= 3 and order[0] == "SELL" and order[1] == item:
                return t, max(0, int(order[2]))
    return None


def _rival_shadow_sale(observation, action, configuration):
    """Pre-empt a visibly imminent rival harvest with already-shed stock.

    This is a *research hypothesis*, not a validated best response. The
    incumbent's own future sale provides a bounded liquidation commitment;
    rival hands/tile output and current market inventory are public.
    """
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return action
    cfg = configuration if isinstance(configuration, dict) else {}
    if any(cfg.get(k, v) != v for k, v in (("turnsPerDay", 24),
                                           ("boardSize", 10),
                                           ("maxMarketOrdersPerTurn", 10))):
        return action
    step = int(observation.get("step", -1))
    if step < 144 or step >= 695 or step % 24 >= 22:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= 10 or any(o and o[0] == "BUY_PRODUCT" for o in market):
        return action
    stock = _MAIN.projected_shed(action, _MAIN.FarmView(observation))
    player = int(observation["player"])
    params = observation["market"].get("params")
    inventory = observation["market"]["inventory"]
    for item, rival_units in sorted(_rival_ready(observation).items(),
                                    key=lambda p: -p[1]*_BASE_PRICE[p[0]]):
        if rival_units < 3 or int(stock.get(item, 0)) < 3:
            continue
        if any(len(o) >= 2 and o[1] == item and o[0] == "SELL" for o in market):
            continue
        planned = _planned_sale(player, step, item)
        if planned is None:
            continue
        quote = int(observation["market"]["prices"].get(item, 0))
        if quote < _BASE_PRICE[item]:
            continue
        # Conservative one-batch shadow price: it must already be cheaper
        # after visible rival output, before crediting unknown future demand.
        after = _MAIN._r37_market_price(
            item, int(inventory[item])+rival_units, params)
        if quote-after < max(5, quote//20):
            continue
        _STATS["shadow_exposures"] += 1
        quantity = min(8, int(stock[item]), int(planned[1]), rival_units)
        if quantity < 3:
            continue
        _STATS["shadow_units"] += quantity
        _STATS["research_changes"] += 1
        return dict(action, market=[["SELL", item, quantity], *market])
    return action


def agent(observation, configuration=None):
    """Return a valid action; experimental overlays may alter only a copy."""
    step = int(observation.get("step", -1)) if isinstance(observation, dict) else -1
    if step == 0:
        for name in _STATS:
            _STATS[name] = 0
    action = _BASE_AGENT(observation, configuration)
    _STATS["research_calls"] += 1
    if MODE == "baseline":
        return action
    if MODE == "rival_shadow":
        try:
            return _rival_shadow_sale(observation, action, configuration)
        except Exception:
            _STATS["research_errors"] += 1
            return action
    raise ValueError(f"Unknown research mode: {MODE!r}")


agent.telemetry = _STATS
