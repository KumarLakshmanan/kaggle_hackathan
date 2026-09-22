"""Local-only V43 branch-selection experiment.

The three V43 farm routes share a verified prefix through the public branch
points.  This wrapper keeps the original opening and chooses a continuation
only at those points, using public shop/capital state.  It is deliberately not
the production submission file.
"""

from __future__ import annotations

import os
import sys

import main_v43_current as _v43


_MODE = str(os.environ.get("V43_BRANCH_MODE", "pet_cash"))
_ORIGINAL_SELECTOR = sys.modules["v43.sparse_router"].selected_route
_ROUTER_MODULE = sys.modules["v43.sparse_router"]
_CHOICES = {0: "default", 1: "default"}
_LAST_STEP = {0: -1, 1: -1}


def _number(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _select_route(obs, config):
    step = int((obs or {}).get("step", 0) or 0)
    seat = 1 if int((obs or {}).get("player", 0) or 0) == 1 else 0
    if step == 0 or step < _LAST_STEP[seat]:
        _CHOICES[seat] = "default"
    _LAST_STEP[seat] = step

    choice = _CHOICES[seat]
    town = (obs or {}).get("town", {}) or {}
    shops = [str(value) for value in (town.get("unlocked_shops", []) or [])]

    if step == 88 and choice == "default":
        first = shops[0] if shops else ""
        # Preserve the validated public YARN branch.
        if first == "YARN_STORE":
            choice = "yarn_first"
        elif _MODE in {"pet_first", "pet_cash", "pet_cash_pizza"} and first == "PET_CAFE":
            farms = list((obs or {}).get("farms", []) or [])
            opponent = farms[1 - seat] if len(farms) > 1 else {}
            # The probe panel separates the weak PET opponents from the
            # already-strong PET/YARN continuation using this public signal.
            if _MODE == "pet_first" or _number(opponent.get("money")) < 350.0:
                choice = "yarn_first"

    if step == 153 and choice == "default":
        first = shops[0] if shops else ""
        second = shops[1] if len(shops) >= 2 else ""
        if second == "YARN_STORE":
            choice = "yarn_second"
        elif (
            _MODE in {"farm_pizza", "pet_cash_pizza"}
            and first == "FARMERS_MARKET"
            and second == "PIZZA_SHOP"
        ):
            choice = "yarn_second"

    _CHOICES[seat] = choice
    return choice


_ROUTER_MODULE.selected_route = _select_route


def agent(obs, configuration=None):
    return _v43.agent(obs, configuration)

