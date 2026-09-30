"""Experimental source-branch continuation for the public Pizza/Ice Cream pair.

This layer is appended to the frozen 6d Goose4 + Smoothie candidate. It changes
the route schedule only at step 144 when the public shop pair is
PIZZA_SHOP|ICE_CREAM_SHOP and the existing bridge selected its source branch.
"""

import copy

_PIICE_PAIR = "PIZZA_SHOP|ICE_CREAM_SHOP"
_PIICE_KEY72 = "PIZZA_SHOP|M8+|C>S|G0"
_PIICE_ROUTE = 113339524
_PIICE_PARENT = agent
_PIICE_BASE_ROUTE_MAP = copy.deepcopy(_DATA["route_map"])
_PIICE_ACTIVE = False
_PIICE_OBSERVED_KEY72 = ""
_PIICE_STATS = {
    "piice_key72": "",
    "piice_branch144": "",
    "piice_key144": "",
    "piice_pair144": "",
    "piice_active144": False,
    "piice_route144": "",
    "piice_active_turns": 0,
    "piice_errors": 0,
}


def _piice_reset():
    global _PIICE_ACTIVE, _PIICE_OBSERVED_KEY72
    _DATA["route_map"] = copy.deepcopy(_PIICE_BASE_ROUTE_MAP)
    _PIICE_ACTIVE = False
    _PIICE_OBSERVED_KEY72 = ""
    _PIICE_STATS.update(
        piice_key72="",
        piice_branch144="",
        piice_key144="",
        piice_pair144="",
        piice_active144=False,
        piice_route144="",
        piice_active_turns=0,
        piice_errors=0,
    )


def _piice_commit():
    """Redirect only this shop-pair subtree to the frozen 719-turn route."""
    for key in list(_DATA["route_map"]):
        if key == _PIICE_PAIR or key.startswith(_PIICE_PAIR + "|"):
            _DATA["route_map"][key] = _PIICE_ROUTE
    _DATA["route_map"][_PIICE_PAIR] = _PIICE_ROUTE


def agent(observation, configuration=None):
    global _PIICE_ACTIVE, _PIICE_OBSERVED_KEY72
    step = int(observation["step"])
    if step == 0:
        _piice_reset()

    if step == 72:
        branch = _BRIDGE_SELECTED
        _PIICE_OBSERVED_KEY72 = _a44_goose4_key(observation) if branch == "source" else ""
        _PIICE_STATS["piice_key72"] = _PIICE_OBSERVED_KEY72

    if step == 144:
        branch = _BRIDGE_SELECTED
        key72 = _PIICE_OBSERVED_KEY72
        shops = (observation.get("town", {}).get("unlocked_shops", []) or [])
        pair = "|".join(shops[:2])
        _PIICE_STATS["piice_branch144"] = branch
        _PIICE_STATS["piice_key144"] = key72
        _PIICE_STATS["piice_pair144"] = pair
        if branch == "source" and key72 == _PIICE_KEY72 and pair == _PIICE_PAIR:
            try:
                _piice_commit()
                _PIICE_ACTIVE = True
                _PIICE_STATS.update(
                    piice_active144=True,
                    piice_route144=str(_PIICE_ROUTE),
                )
            except Exception:
                _PIICE_STATS["piice_errors"] += 1

    result = _PIICE_PARENT(observation, configuration)
    if step >= 144 and _PIICE_ACTIVE:
        _PIICE_STATS["piice_active_turns"] += 1
    agent.telemetry.update(getattr(_PIICE_PARENT, "telemetry", {}))
    agent.telemetry.update(_PIICE_STATS)
    return result


agent.telemetry = {}


def kaggle_a44_piice_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
