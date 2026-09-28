"""Retain executable planting requests when available seeds cannot cover all."""
_PARTIAL_PARENT = agent
_PARTIAL_STATS = {"partial_plant_turns": 0, "partial_plant_kept": 0,
                  "partial_plant_removed": 0, "partial_plant_errors": 0}


def _partial_plant(obs, action, cfg):
    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    need = {}
    for unit in units:
        if len(unit) >= 2 and unit[0] == "PLANT":
            need[unit[1]] = need.get(unit[1], 0) + 1
    available = obs["private"]["seeds"]
    blocked = {crop for crop, count in need.items() if 0 < available.get(crop, 0) < count}
    if not blocked:
        return action
    farm, private = copy.deepcopy(obs["farms"][int(obs["player"])]), copy.deepcopy(obs["private"])
    chosen = copy.deepcopy(units)
    kept = removed = 0
    for index, unit in enumerate(units):
        target = len(unit) >= 2 and unit[0] == "PLANT" and unit[1] in blocked
        before = private["seeds"].get(unit[1], 0) if target else 0
        _PLANT_CORE["_apply_unit_action"](farm, private, index, unit,
            int(cfg.get("boardSize", 10)), int(obs["step"]) // int(cfg.get("turnsPerDay", 24)),
            int(cfg.get("turnsPerDay", 24)), int(cfg.get("shedCapacity", 100)))
        if target:
            if private["seeds"].get(unit[1], 0) == before - 1:
                kept += 1
            else:
                chosen[index] = ["PASS"]
                removed += 1
    if removed:
        action["farmer"], action["hands"] = chosen[0], chosen[1:]
        _PARTIAL_STATS["partial_plant_turns"] += 1
        _PARTIAL_STATS["partial_plant_kept"] += kept
        _PARTIAL_STATS["partial_plant_removed"] += removed
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _PARTIAL_STATS:
            _PARTIAL_STATS[key] = 0
    result = _PARTIAL_PARENT(observation, configuration)
    try:
        result = _partial_plant(observation, result, configuration or {})
    except Exception:
        _PARTIAL_STATS["partial_plant_errors"] += 1
    agent.telemetry.update(_PARTIAL_STATS)
    return result


agent.telemetry = {}


def kaggle_partial_planting_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
