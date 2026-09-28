"""Fund an existing animal order before its scheduled next-turn pickup."""
_ANIMAL_PARENT = agent
_ANIMAL_STATS = {"animal_funding_turns": 0, "animal_funding_units": 0,
                 "animal_funding_proposals": 0, "animal_funding_errors": 0}


def _animal_post(obs, action, cfg):
    player = int(obs["player"])
    farm, private = copy.deepcopy(obs["farms"][player]), copy.deepcopy(obs["private"])
    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    demand = {}
    for unit in units:
        if len(unit) >= 2 and unit[0] == "PLANT":
            demand[unit[1]] = demand.get(unit[1], 0) + 1
    blocked = {crop for crop, n in demand.items() if n > private["seeds"].get(crop, 0)}
    for index, unit in enumerate(units):
        if len(unit) >= 2 and unit[0] == "PLANT" and unit[1] in blocked:
            unit = ["PASS"]
        _ANIMAL_CORE["_apply_unit_action"](farm, private, index, unit,
            int(cfg.get("boardSize", 10)), int(obs["step"]) // int(cfg.get("turnsPerDay", 24)),
            int(cfg.get("turnsPerDay", 24)), int(cfg.get("shedCapacity", 100)))
    return farm, private


def _animal_market(obs, orders, rival, post_farm, post_private, cfg):
    player = int(obs["player"])
    farms, market = copy.deepcopy(obs["farms"]), copy.deepcopy(obs["market"])
    farms[player] = copy.deepcopy(post_farm)
    privates = [None, None]
    privates[player] = copy.deepcopy(post_private)
    privates[1-player] = {"shed": dict(post_private["shed"]), "seeds": dict(post_private["seeds"]),
                         "inventories": [{} for _ in range(1 + len(farms[1-player]["hands"]))]}
    states = [_QueueBox(action={"market": orders if i == player else rival},
        observation=_QueueBox(farms=farms, market=market, private=privates[i])) for i in range(2)]
    _ANIMAL_CORE["_process_market"](states, _QueueBox(configuration=cfg))
    return farms, privates


def _animal_other_signature(farm, private, item):
    altered = dict(private, shed={k: v for k, v in private["shed"].items() if k != item})
    return _queue_signature(farm, altered)


def _animal_funding(obs, action, cfg):
    step = int(obs["step"])
    if step < 144 or step >= 718 or (step + 1) % int(cfg.get("turnsPerDay", 24)) == 0:
        return action
    if obs["town"]["unlocked_shops"][:2] != ["YARN_STORE", "FARMERS_MARKET"]:
        return action
    orders = action.get("market", [])
    animal_orders = [(i, order[1]) for i, order in enumerate(orders)
                     if len(order) >= 3 and order[0] == "BUY_ANIMAL" and order[1] in _ANIMAL_CORE["ANIMALS"]]
    if not animal_orders:
        return action
    farm, private = _animal_post(obs, action, cfg)
    nxt = _DATA["routes"]["113349962"][step + 1]
    positions = [farm["farmer"], *farm["hands"]]
    units = [nxt.get("farmer", ["PASS"]), *nxt.get("hands", [])]
    needs = {}
    for pos, unit in zip(positions, units):
        if len(unit) >= 2 and unit[0] == "PICKUP" and unit[1] in _ANIMAL_CORE["ANIMALS"]:
            if _ANIMAL_CORE["_is_shed_adjacent"](pos, int(cfg.get("boardSize", 10))):
                needs[unit[1]] = needs.get(unit[1], 0) + (int(unit[2]) if len(unit) >= 3 else 1)
    if not needs:
        return action
    player = int(obs["player"])
    forecasts = [[], orders]
    controls = [_animal_market(obs, orders, rival, farm, private, cfg) for rival in forecasts]
    chosen, best = orders, (0, 0)
    for index, item in animal_orders:
        if not needs.get(item):
            continue
        if any(p[player]["shed"].get(item, 0) >= needs[item] for _, p in controls):
            continue
        for later in range(index + 1, len(orders)):
            if not orders[later] or orders[later][0] != "SELL":
                continue
            proposal = orders[:index] + orders[index+1:later+1] + [orders[index]] + orders[later+1:]
            extras, gains = [], []
            _ANIMAL_STATS["animal_funding_proposals"] += 1
            for rival, (old_f, old_p) in zip(forecasts, controls):
                new_f, new_p = _animal_market(obs, proposal, rival, farm, private, cfg)
                extra = new_p[player]["shed"].get(item, 0) - old_p[player]["shed"].get(item, 0)
                cost = extra * _ANIMAL_CORE["ANIMALS"][item]["cost"]
                if extra <= 0 or new_f[player]["money"] + cost < old_f[player]["money"]:
                    break
                if _animal_other_signature(new_f[player], new_p[player], item) != _animal_other_signature(old_f[player], old_p[player], item):
                    break
                if _queue_signature(new_f[1-player], new_p[1-player]) != _queue_signature(old_f[1-player], old_p[1-player]):
                    break
                extras.append(extra)
                gains.append(new_f[player]["money"] - new_f[1-player]["money"] + cost
                             - old_f[player]["money"] + old_f[1-player]["money"])
            if len(extras) == len(forecasts):
                key = (min(extras), min(gains))
                if key > best:
                    chosen, best = proposal, key
    if chosen is not orders:
        action["market"] = chosen
        _ANIMAL_STATS["animal_funding_turns"] += 1
        _ANIMAL_STATS["animal_funding_units"] += best[0]
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _ANIMAL_STATS:
            _ANIMAL_STATS[key] = 0
    result = _ANIMAL_PARENT(observation, configuration)
    try:
        result = _animal_funding(observation, result, configuration or {})
    except Exception:
        _ANIMAL_STATS["animal_funding_errors"] += 1
    agent.telemetry.update(_ANIMAL_STATS)
    return result


agent.telemetry = {}


def kaggle_scheduled_animal_funding_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
