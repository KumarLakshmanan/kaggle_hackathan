"""Coherent wheat-for-carrot crop-chain substitution experiment."""
_CROP_PARENT = agent
_CROP_STATS = {"crop_plant_changes": 0, "crop_market_changes": 0, "crop_transfer_changes": 0}


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _CROP_STATS:
            _CROP_STATS[key] = 0
    action = _CROP_PARENT(observation, configuration)
    for unit in [action.get("farmer", [])] + action.get("hands", []):
        if len(unit) > 1 and unit[1] == "CARROT" and unit[0] in ("PLANT", "PLACE", "PICKUP"):
            unit[1] = "WHEAT"
            _CROP_STATS["crop_plant_changes" if unit[0] == "PLANT" else "crop_transfer_changes"] += 1
    for order in action.get("market", []):
        if len(order) > 1 and order[1] == "CARROT" and order[0] in ("BUY_SEED", "SELL"):
            order[1] = "WHEAT"
            _CROP_STATS["crop_market_changes"] += 1
    _CROP_STATS.update(_LAND_STATS)
    return action


agent.telemetry = _CROP_STATS


def kaggle_shunki_farming_crop_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
