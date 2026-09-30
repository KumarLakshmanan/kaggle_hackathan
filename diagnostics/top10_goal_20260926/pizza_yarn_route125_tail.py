"""Pilot: restore the complete R108 route 125 for PIZZA_SHOP,YARN_STORE."""

_PIZZA_YARN_ROUTER_PARENT = _IMPL.chassis.router
_PIZZA_YARN_REPORT = dict(route125_turns=0, route125_errors=0)


def _pizza_yarn_router(observation, step, state):
    selected = _PIZZA_YARN_ROUTER_PARENT(observation, step, state)
    try:
        if 144 <= step < 648:
            shops = tuple((observation["town"]["unlocked_shops"] or [])[:2])
            if shops == ("PIZZA_SHOP", "YARN_STORE"):
                state["route"] = 125
                _PIZZA_YARN_REPORT["route125_turns"] += 1
                return 125
    except Exception:
        _PIZZA_YARN_REPORT["route125_errors"] += 1
    return selected


_IMPL.chassis.router = _pizza_yarn_router
_PIZZA_YARN_PARENT = agent


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _PIZZA_YARN_REPORT.update(route125_turns=0, route125_errors=0)
    action = _PIZZA_YARN_PARENT(observation, configuration)
    _PIZZA_YARN_REPORT.update(getattr(_PIZZA_YARN_PARENT, "telemetry", {}))
    return action


agent.telemetry = _PIZZA_YARN_REPORT
kaggle_submission_agent = agent
