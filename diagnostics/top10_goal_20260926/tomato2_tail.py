"""Experiment: allow the complete V219 late tomato bundle with two demand shops."""

_TOMATO2_PARENT_QUALIFIES = _v219_qualifies
_TOMATO2_PARENT_AGENT = agent
_TOMATO2_REPORT = {"tomato2_checks": 0, "tomato2_new_eligible": 0,
                   "tomato2_old_eligible": 0, "tomato2_errors": 0,
                   "v219_commitments": 0, "v219_confirmed_plants": 0,
                   "v219_tomato_sale_requests": 0}


def _v219_qualifies(obs, native):
    _TOMATO2_REPORT["tomato2_checks"] += 1
    if _TOMATO2_PARENT_QUALIFIES(obs, native):
        _TOMATO2_REPORT["tomato2_old_eligible"] += 1
        return True
    try:
        farm = obs["farms"][obs["player"]]
        if len(farm["tiles"]) != 10 or set(farm["unlocked_quadrants"]) != {"NW", "NE", "SW"}:
            return False
        if farm["money"] < 12000 or obs["market"]["prices"]["TOMATO"] < CROP_MIN_PRICE:
            return False
        shops = obs["town"]["unlocked_shops"]
        if sum(s in ("PIZZA_SHOP", "FARMERS_MARKET") for s in shops) != 2:
            return False
        if any(farm["tiles"][y][x] != "LOCKED" for y in (5, 6) for x in range(5, 10)):
            return False
        if obs["private"]["seeds"].get("TOMATO", 0) or obs["private"]["shed"].get("TOMATO", 0):
            return False
        if any(isinstance(t, dict) and t.get("crop") == "TOMATO"
               for row in farm["tiles"] for t in row):
            return False
        for tape in _IMPL.chassis.routes.values():
            for action in tape[432:719]:
                if any(order and order[0] == "BUY_LAND" for order in action.get("market", [])):
                    return False
                if any(command == ["PLANT", "TOMATO"]
                       for command in [action.get("farmer")] + action.get("hands", [])):
                    return False
        _TOMATO2_REPORT["tomato2_new_eligible"] += 1
        return True
    except Exception:
        _TOMATO2_REPORT["tomato2_errors"] += 1
        return False


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _TOMATO2_REPORT.update(tomato2_checks=0, tomato2_new_eligible=0,
                               tomato2_old_eligible=0, tomato2_errors=0,
                               v219_commitments=0, v219_confirmed_plants=0,
                               v219_tomato_sale_requests=0)
    action = _TOMATO2_PARENT_AGENT(observation, configuration)
    _TOMATO2_REPORT.update(v219_commitments=_V219_REPORT["commitments"],
                           v219_confirmed_plants=_V219_REPORT["confirmed_plants"],
                           v219_tomato_sale_requests=_V219_REPORT["tomato_sale_requests"])
    _TOMATO2_REPORT.update(getattr(_TOMATO2_PARENT_AGENT, "telemetry", {}))
    return action


agent.telemetry = _TOMATO2_REPORT
kaggle_submission_agent = agent
