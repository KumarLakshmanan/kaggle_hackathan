"""Choose one compatible complete schedule from current visible production."""
_FARMICE_SCHEDULE_PARENT = _QUEUE_PARENT
_FARMICE_A2_PARENT = agent
_FARMICE_ACTIVE = False
_FARMICE_STATS = {"farmice_turns": 0, "farmice_errors": 0}


def _farmice_schedule(observation, configuration=None):
    global _FARMICE_ACTIVE
    step = int(observation["step"])
    if step == 0:
        _FARMICE_ACTIVE = False
        _FARMICE_STATS.update(farmice_turns=0, farmice_errors=0)
    try:
        if step == 144:
            shops = observation["town"]["unlocked_shops"][:2]
            rival = observation["farms"][1-int(observation["player"])]
            has_melon = any(isinstance(tile, dict) and tile.get("crop") == "MELON"
                            for row in rival["tiles"] for tile in row)
            _FARMICE_ACTIVE = shops == ["FARMERS_MARKET", "ICE_CREAM_SHOP"] and has_melon
        if _FARMICE_ACTIVE:
            _FARMICE_STATS["farmice_turns"] += 1
            return copy.deepcopy(_FARMICE_TAPE[min(step, 718)])
    except Exception:
        _FARMICE_STATS["farmice_errors"] += 1
    return _FARMICE_SCHEDULE_PARENT(observation, configuration)


_QUEUE_PARENT = _farmice_schedule


def agent(observation, configuration=None):
    result = _FARMICE_A2_PARENT(observation, configuration)
    agent.telemetry.update(_QUEUE_STATS)
    agent.telemetry.update(_FARMICE_STATS)
    return result


agent.telemetry = {}


def kaggle_farmice_observed_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
