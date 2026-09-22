"""Local-only segment splice for the farm-opening ambiguity.

The two downloaded routes with the same public step-88 farm signature split
at the second shop: one benefits from the full yarn-first suffix and the
other from the original suffix.  This keeps the yarn-first action at the
first branch, then uses the original route after a public step-153 signal.
"""

from __future__ import annotations

import v43_refined_adaptive_experiment as _adaptive


def agent(obs, configuration=None):
    step = int((obs or {}).get("step", 0) or 0)
    town = (obs or {}).get("town", {}) or {}
    shops = [str(value) for value in (town.get("unlocked_shops", []) or [])]
    seat = 1 if int((obs or {}).get("player", 0) or 0) == 1 else 0
    # Refined V43 has already selected yarn-first at step 88 for this public
    # farm family.  At step 153 the second shop is visible; reset the latch
    # before the planner runs so its already-synchronized default child emits
    # the original suffix without a stateful route splice.
    if (
        step >= 153
        and len(shops) >= 2
        and shops[0] == "FARMERS_MARKET"
        and shops[1] == "SMOOTHIE_SHOP"
        and _adaptive._CHOICE.get(seat) == "yarn_first"
    ):
        _adaptive._CHOICE[seat] = "default"
    return _adaptive.agent(obs, configuration)
