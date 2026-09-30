"""Use a wasted tile operation to prepare the following recorded planting."""
_PREPLANT_PARENT = agent
_PREPLANT_STATS = {"preplant_digs": 0, "preplant_errors": 0}
_PREPLANT_NOOPS = {"PASS", "HARVEST", "WATER", "FERTILIZE", "CARE", "FEED",
                   "COLLECT_FERTILIZER", "PLANT", "BUILD_COOP", "BUILD_PASTURE"}


def _preplant_next(obs):
    step = int(obs["step"])
    if step >= 718 or (step + 1) % 24 == 0:
        return None
    if step < 71:
        return _DATA["opening"][step + 1]
    shops = obs["town"]["unlocked_shops"]
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step >= 72 * count:
            route = _DATA["route_map"].get("|".join(shops[:count]), route)
    return _DATA["routes"][str(route)][step + 1] if route is not None else None


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _PREPLANT_STATS.update(preplant_digs=0, preplant_errors=0)
    action = _PREPLANT_PARENT(observation, configuration)
    try:
        nxt = _preplant_next(observation)
        if nxt is None:
            return action
        farm = observation["farms"][int(observation["player"])]
        positions = [farm["farmer"]] + farm["hands"]
        units = [action.get("farmer", [])] + action.get("hands", [])
        future = [nxt.get("farmer", [])] + nxt.get("hands", [])
        for i, (position, unit, upcoming) in enumerate(zip(positions, units, future)):
            if not unit or unit[0] not in _PREPLANT_NOOPS or not upcoming or upcoming[0] not in ("PLANT", "BUILD_COOP", "BUILD_PASTURE"):
                continue
            x, y = position
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                if i == 0:
                    action["farmer"] = ["DIG"]
                else:
                    action["hands"][i - 1] = ["DIG"]
                _PREPLANT_STATS["preplant_digs"] += 1
    except Exception:
        _PREPLANT_STATS["preplant_errors"] += 1
    return action


agent.telemetry = _PREPLANT_STATS


def kaggle_preplant_weed_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
