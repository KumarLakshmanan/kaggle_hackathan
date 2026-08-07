"""Experimental V32 wrapper for the remaining public Seb market pattern."""

from __future__ import annotations

import main_v32_observable_portfolio as base


_SUPPRESS_START = 648
_SUPPRESS_STOP = 718
_MIN_STRAWBERRY_PRICE = 10**9
_MIN_WOOL_PRICE = 0
_MIN_MILK_PRICE = 0


def agent(obs):
    action = base.agent(obs)
    step = base._step(obs)
    seat = 1 if int(base._get(obs, "player", 0) or 0) == 1 else 0
    town = base._get(obs, "town", {}) or {}
    shops = tuple(base._get(town, "unlocked_shops", []) or [])
    remaining_seb = (
        base._OPPONENT_PASTURE.get(seat, False)
        and shops[:2] == ("FARMERS_MARKET", "BRUNCH_SPOT")
    )
    if remaining_seb and _SUPPRESS_START <= step < _SUPPRESS_STOP:
        prices = base._get(base._get(obs, "market", {}) or {}, "prices", {}) or {}
        minimums = {
            "STRAWBERRY": _MIN_STRAWBERRY_PRICE,
            "WOOL": _MIN_WOOL_PRICE,
            "MILK": _MIN_MILK_PRICE,
        }
        action["market"] = [
            order
            for order in action.get("market", []) or []
            if not (
                len(order) >= 3
                and order[0] == "SELL"
                and order[1] in minimums
                and float(prices.get(order[1], 0) or 0) < minimums[order[1]]
            )
        ]
    return action
