"""Commit to quantity forecasts only after a visible matching farm plan."""
_MIRROR_QUANTITY_PARENT = agent
_MIRROR_QUANTITY_ACTIVE = False
_MIRROR_QUANTITY_STATS = {"mirror_quantity_active": False, "mirror_quantity_errors": 0}


def _mirror_quantity_signature(farm):
    return (tuple(farm["unlocked_quadrants"]),
            tuple((x, y, tile.get("kind"), tile.get("crop"), tile.get("animal"))
                  for y, row in enumerate(farm["tiles"]) for x, tile in enumerate(row)
                  if isinstance(tile, dict)))


def agent(observation, configuration=None):
    global _MIRROR_QUANTITY_ACTIVE
    step = int(observation["step"])
    if step == 0:
        _MIRROR_QUANTITY_ACTIVE = False
        _MIRROR_QUANTITY_STATS.update(mirror_quantity_active=False, mirror_quantity_errors=0)
        for key in _QUANTITY_STATS:
            _QUANTITY_STATS[key] = 0
    try:
        if step == 144:
            farms = observation["farms"]
            _MIRROR_QUANTITY_ACTIVE = _mirror_quantity_signature(farms[0]) == _mirror_quantity_signature(farms[1])
            _MIRROR_QUANTITY_STATS["mirror_quantity_active"] = _MIRROR_QUANTITY_ACTIVE
    except Exception:
        _MIRROR_QUANTITY_STATS["mirror_quantity_errors"] += 1
        _MIRROR_QUANTITY_ACTIVE = False
    result = (_MIRROR_QUANTITY_PARENT if _MIRROR_QUANTITY_ACTIVE else _QUANTITY_PARENT)(observation, configuration)
    agent.telemetry.update(_QUEUE_STATS)
    agent.telemetry.update(_QUANTITY_STATS)
    agent.telemetry.update(_MIRROR_QUANTITY_STATS)
    return result


agent.telemetry = {}


def kaggle_mirror_quantity_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
