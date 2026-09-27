"""Pilot: fund and plant thirteen TOMATO in route 104's day-11 cohort."""

import copy as _tomato_copy

_TOMATO_ROUTE = 104
_TOMATO_STEPS = range(265, 281)
_TOMATO_PARENT = agent
_TOMATO_REPORT = dict(tomato_seed_units=0, tomato_plants=0,
                      tomato_sale_turns=0, tomato_sale_units=0,
                      tomato_errors=0)

for _tomato_step in _TOMATO_STEPS:
    _tomato_action = _tomato_copy.deepcopy(_IMPL.chassis.routes[_TOMATO_ROUTE][_tomato_step])
    for _tomato_order in _tomato_action.get("market") or []:
        if len(_tomato_order) >= 3 and _tomato_order[:2] == ["BUY_SEED", "STRAWBERRY"]:
            _tomato_order[1] = "TOMATO"
            _TOMATO_REPORT["tomato_seed_units"] += int(_tomato_order[2])
    _tomato_units = [_tomato_action.get("farmer"), *(_tomato_action.get("hands") or [])]
    for _tomato_unit in _tomato_units:
        if isinstance(_tomato_unit, list) and _tomato_unit[:2] == ["PLANT", "STRAWBERRY"]:
            _tomato_unit[1] = "TOMATO"
            _TOMATO_REPORT["tomato_plants"] += 1
    _IMPL.chassis.routes[_TOMATO_ROUTE][_tomato_step] = _tomato_action

assert _TOMATO_REPORT["tomato_seed_units"] == 13
assert _TOMATO_REPORT["tomato_plants"] == 13


def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _TOMATO_REPORT.update(tomato_sale_turns=0, tomato_sale_units=0,
                              tomato_errors=0)
    action = _TOMATO_PARENT(observation, configuration)
    try:
        if step < 265:
            return action
        player = int(observation["player"])
        state = _IMPL.chassis.players.get(player)
        if state is None:
            return action
        # Route 2 takes over at day 27; own tomato tiles then identify
        # residual production from the route-104 cohort.
        on_route = state.get("route") == _TOMATO_ROUTE
        own_tiles = observation["farms"][player]["tiles"]
        has_tomato = any(isinstance(tile, dict) and tile.get("crop") == "TOMATO"
                         for row in own_tiles for tile in row)
        if not (on_route or has_tomato):
            return action
        stock = int(observation["private"]["shed"].get("TOMATO", 0) or 0)
        market = [list(order) for order in (action.get("market") or [])]
        if stock < 1 or len(market) >= 10 or any(order[:2] == ["SELL", "TOMATO"] for order in market):
            return action
        if int(observation["market"]["prices"].get("TOMATO", 0) or 0) < 2:
            return action
        _TOMATO_REPORT["tomato_sale_turns"] += 1
        _TOMATO_REPORT["tomato_sale_units"] += stock
        return dict(action, market=[["SELL", "TOMATO", stock], *market])
    except Exception:
        _TOMATO_REPORT["tomato_errors"] += 1
        return action
    finally:
        _TOMATO_REPORT.update(getattr(_TOMATO_PARENT, "telemetry", {}))


agent.telemetry = _TOMATO_REPORT
kaggle_submission_agent = agent
