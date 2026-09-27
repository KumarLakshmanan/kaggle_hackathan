"""Pilot: turn two funded wheat cohorts into strawberry on smoothie demand."""

_SMOOTHIE_PARENT = agent
_SMOOTHIE_STATE = {}
_SMOOTHIE_REPORT = dict(smoothie_day11=0, smoothie_day12=0,
                        smoothie_seed_units=0, smoothie_plants=0,
                        smoothie_errors=0)


def agent(observation, configuration=None):
    step = int(observation["step"])
    player = int(observation["player"])
    if step == 0:
        _SMOOTHIE_STATE.pop(player, None)
        _SMOOTHIE_REPORT.update(smoothie_day11=0, smoothie_day12=0,
                                smoothie_seed_units=0, smoothie_plants=0,
                                smoothie_errors=0)
    action = _SMOOTHIE_PARENT(observation, configuration)
    try:
        if configuration is not None and any(configuration.get(key, value) != value
                                             for key, value in (("boardSize", 10),
                                                                ("turnsPerDay", 24),
                                                                ("shedCapacity", 100))):
            return action
        if not (274 <= step <= 286 or 297 <= step <= 306):
            return action
        native = _IMPL.chassis.players.get(player)
        if native is None or native.get("route") != 116:
            return action
        state = _SMOOTHIE_STATE.setdefault(player, {})
        shops = list(observation["town"]["unlocked_shops"])
        if step == 274:
            state["day11"] = shops[:3] == ["PET_CAFE", "BRUNCH_SPOT", "SMOOTHIE_SHOP"]
            if state["day11"]:
                _SMOOTHIE_REPORT["smoothie_day11"] += 1
        if step == 297:
            state["day12"] = (state.get("day11", False)
                              and shops[:4] == ["PET_CAFE", "BRUNCH_SPOT",
                                                "SMOOTHIE_SHOP", "SMOOTHIE_SHOP"])
            if state["day12"]:
                _SMOOTHIE_REPORT["smoothie_day12"] += 1
        enabled = state.get("day11", False) if step <= 286 else state.get("day12", False)
        if not enabled:
            return action
        revised = dict(action)
        revised["market"] = [list(order) for order in (action.get("market") or [])]
        for order in revised["market"]:
            if len(order) >= 3 and order[:2] == ["BUY_SEED", "WHEAT"]:
                order[1] = "STRAWBERRY"
                _SMOOTHIE_REPORT["smoothie_seed_units"] += int(order[2])
        farmer = list(action.get("farmer") or ["PASS"])
        hands = [list(command) for command in (action.get("hands") or [])]
        for command in [farmer, *hands]:
            if command[:2] == ["PLANT", "WHEAT"]:
                command[1] = "STRAWBERRY"
                _SMOOTHIE_REPORT["smoothie_plants"] += 1
        revised["farmer"], revised["hands"] = farmer, hands
        return revised
    except Exception:
        _SMOOTHIE_REPORT["smoothie_errors"] += 1
        return action
    finally:
        _SMOOTHIE_REPORT.update(getattr(_SMOOTHIE_PARENT, "telemetry", {}))


agent.telemetry = _SMOOTHIE_REPORT
kaggle_submission_agent = agent
