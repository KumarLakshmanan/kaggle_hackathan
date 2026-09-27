"""Use an existing fertilizer dose before its paired watering action."""
_FARM_PARENT = agent
_FARM_PENDING = {}
_FARM_STATS = {"fertilizer_timing_swaps": 0, "timing_followups": 0, "farming_errors": 0}


def _farming_timing(obs, action):
    step = int(obs["step"])
    farm = obs["farms"][int(obs["player"])]
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", ["PASS"])] + action.get("hands", [])
    inventories = obs["private"]["inventories"]
    day = step // 24
    route = _land_route(obs)
    nxt = None
    if route is not None and step < 718 and step % 24 != 23 and step % 72 != 71:
        plan = _DATA["routes"][route][step + 1]
        nxt = [plan.get("farmer", ["PASS"])] + plan.get("hands", [])
    for actor, (pos, unit, inv) in enumerate(zip(positions, units, inventories)):
        x, y = pos
        tile = farm["tiles"][y][x]
        pending = _FARM_PENDING.pop(actor, None)
        if pending is not None and pending == (step, tuple(pos)) and unit == ["FERTILIZE"]:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                units[actor] = ["PASS"] if tile.get("watered_today") else ["WATER"]
                _FARM_STATS["timing_followups"] += 1
                continue
        if nxt is None or actor >= len(nxt) or unit != ["WATER"] or nxt[actor] != ["FERTILIZE"]:
            continue
        if not isinstance(tile, dict) or tile.get("kind") != "PLANT" or tile.get("watered_today"):
            continue
        crop = tile.get("crop")
        maximum = {"WHEAT": 4, "CARROT": 3, "MELON": 12}.get(crop)
        if maximum is None or inv.get("FERTILIZER", 0) < 1 or tile.get("fertilized_until_day", -1) >= day:
            continue
        age = day - int(tile["planted_day"])
        if not (maximum + 1) // 2 <= age <= maximum:
            continue
        units[actor] = ["FERTILIZE"]
        _FARM_PENDING[actor] = (step + 1, tuple(pos))
        _FARM_STATS["fertilizer_timing_swaps"] += 1
    action["farmer"], action["hands"] = units[0], units[1:]
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _FARM_PENDING.clear()
        for key in _FARM_STATS:
            _FARM_STATS[key] = 0
    action = _FARM_PARENT(observation, configuration)
    try:
        action = _farming_timing(observation, action)
    except Exception:
        _FARM_STATS["farming_errors"] += 1
    _FARM_STATS.update(_LAND_STATS)
    return action


agent.telemetry = _FARM_STATS


def kaggle_shunki_farming_timing_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
