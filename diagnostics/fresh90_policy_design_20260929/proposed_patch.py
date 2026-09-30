"""Side-effect-free forecast version of cb76's partial-plant repair.

Base candidate SHA-256:
cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74

This helper is intended for a separately built rollout experiment. It does not
change the shared submission or the already-frozen v1 pilot.
"""

import copy

BASE_SHA256 = "cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74"


def _f90_plant_action(observation, action, configuration, core):
    """Apply the cb76 partial-seed planting repair without touching telemetry.

    The policy calls its stateful `_partial_plant` wrapper before the engine.
    Rollout forecasts call this equivalent pure helper so the embedded native
    interpreter does not apply its all-or-none planting guard to raw requests.
    `action` may be modified in place, matching the production helper.
    """
    if not isinstance(action, dict):
        return action

    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    need = {}
    for unit in units:
        if isinstance(unit, list) and len(unit) >= 2 and unit[0] == "PLANT":
            crop = unit[1]
            need[crop] = need.get(crop, 0) + 1

    private_observation = observation["private"]
    available = private_observation["seeds"]
    blocked = {
        crop for crop, count in need.items()
        if 0 < available.get(crop, 0) < count
    }
    if not blocked:
        return action

    player = int(observation["player"])
    farm = copy.deepcopy(observation["farms"][player])
    private = copy.deepcopy(private_observation)
    chosen = copy.deepcopy(units)
    cfg = configuration or {}
    turns_per_day = int(cfg.get("turnsPerDay", 24))
    board_size = int(cfg.get("boardSize", 10))
    day = int(observation["step"]) // turns_per_day
    shed_capacity = int(cfg.get("shedCapacity", 100))

    for index, unit in enumerate(units):
        target = (
            isinstance(unit, list) and len(unit) >= 2
            and unit[0] == "PLANT" and unit[1] in blocked
        )
        before = private["seeds"].get(unit[1], 0) if target else 0
        core["_apply_unit_action"](
            farm, private, index, unit, board_size, day,
            turns_per_day, shed_capacity,
        )
        if target and private["seeds"].get(unit[1], 0) != before - 1:
            chosen[index] = ["PASS"]

    action["farmer"], action["hands"] = chosen[0], chosen[1:]
    return action
