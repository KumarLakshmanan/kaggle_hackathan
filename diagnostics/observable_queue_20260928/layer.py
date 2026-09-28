"""Reorder current orders with uncertainty over observable past rival flow."""
_FLOW_PARENT = agent
_FLOW_HISTORY = {}
_FLOW_PREVIOUS = None
_FLOW_STATS = {"flow_turns": 0, "flow_proposals": 0, "flow_errors": 0,
               "flow_observations": 0, "flow_forecast_turns": 0, "flow_predicted_gain": 0.0}


def _flow_simulate(obs, orders, forecast, own_private, cfg):
    player = int(obs["player"])
    farms, market = copy.deepcopy(obs["farms"]), copy.deepcopy(obs["market"])
    rival_orders, rival_shed, rival_seeds, kind = forecast
    privates = [None, None]
    privates[player] = copy.deepcopy(own_private)
    privates[1-player] = {"shed": dict(rival_shed), "seeds": dict(rival_seeds),
                         "inventories": [{} for _ in range(len(farms[1-player]["hands"])+1)]}
    states = [_QueueBox(action={"market": orders if i == player else rival_orders},
                         observation=_QueueBox(farms=farms, market=market, private=privates[i])) for i in range(2)]
    _QUEUE_ENGINE["_process_market"](states, _QueueBox(configuration=cfg))
    return (farms[player]["money"], farms[1-player]["money"],
            _queue_signature(farms[player], privates[player]),
            _queue_signature(farms[1-player], privates[1-player]))


def _flow_reorder(obs, action, cfg):
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    if float(obs.get("remainingOverageTime", 60)) < 5:
        return action
    own_private = _FLOW_LOGIC["post_worker_private"](obs, action, cfg)
    forecasts = [([], {}, {}, "idle"),
                 (orders, own_private["shed"], own_private["seeds"], "mirror")]
    seen_forecasts = set()
    for lag in (24, 48):
        past = _FLOW_HISTORY.get(int(obs["step"])-lag)
        if past is None:
            continue
        historical, shed = [], {}
        room = int(cfg.get("shedCapacity", 100))
        for item in _FLOW_CORE["PRODUCTS"]:
            amount = past.get(item)
            if amount is None or amount == 0:
                continue
            if amount > 0 and room:
                quantity = min(int(amount), room)
                historical.append(["SELL", item, quantity])
                shed[item] = quantity
                room -= quantity
            elif amount < 0 and item in ("WHEAT", "FERTILIZER"):
                historical.append(["BUY_PRODUCT", item, min(-int(amount), int(cfg.get("shedCapacity", 100)))])
        if not historical:
            continue
        for queue in (historical, list(reversed(historical))):
            signature = tuple(tuple(o) for o in queue)
            if signature not in seen_forecasts:
                seen_forecasts.add(signature)
                forecasts.append((queue, shed, {}, "history"))
    if len(forecasts) == 2:
        return action
    _FLOW_STATS["flow_forecast_turns"] += 1
    proposals, seen = [], {tuple(tuple(o) for o in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] not in ("SELL", "BUY_PRODUCT"):
            continue
        for earlier in range(index):
            proposed = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            signature = tuple(tuple(o) for o in proposed)
            if signature not in seen:
                proposals.append(proposed); seen.add(signature)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    raw = _ITERATED_QUEUE_RAW(obs, cfg).get("market", [])
    raw_key = tuple(tuple(o) for o in raw)
    if raw_key not in seen and sorted(raw_key) == sorted(tuple(tuple(o) for o in orders)):
        proposals.append(raw)
    if not proposals:
        return action
    controls = [_flow_simulate(obs, orders, f, own_private, cfg) for f in forecasts]
    best_key, selected = (0, 0, 0, 0), orders
    for proposed in proposals:
        _FLOW_STATS["flow_proposals"] += 1
        gains, own_gains = [], []
        for index, (forecast, control) in enumerate(zip(forecasts, controls)):
            result = _flow_simulate(obs, proposed, forecast, own_private, cfg)
            gain = (result[0]-result[1])-(control[0]-control[1])
            if result[0] < control[0] or result[2] != control[2] or gain < 0:
                break
            if index and result[3] != control[3]:
                break
            gains.append(gain); own_gains.append(result[0]-control[0])
        if len(gains) != len(forecasts) or sum(gains[2:]) <= 0:
            continue
        key = (min(gains[2:]), sum(gains[2:]), sum(gains), min(own_gains))
        if key > best_key:
            best_key, selected = key, proposed
    if selected is not orders:
        action["market"] = selected
        _FLOW_STATS["flow_turns"] += 1
        _FLOW_STATS["flow_predicted_gain"] += best_key[1]
    return action


def agent(observation, configuration=None):
    global _FLOW_PREVIOUS
    step = int(observation["step"])
    cfg = configuration or {}
    if step == 0:
        _FLOW_HISTORY.clear(); _FLOW_PREVIOUS = None
        for key in _FLOW_STATS: _FLOW_STATS[key] = 0
    result = _FLOW_PARENT(observation, configuration)
    try:
        if _FLOW_PREVIOUS is not None:
            previous, action = _FLOW_PREVIOUS
            inferred = _FLOW_LOGIC["infer_rival_net_sales"](previous, action, observation, cfg)
            _FLOW_HISTORY[int(previous["step"])] = inferred
            _FLOW_STATS["flow_observations"] += int(inferred is not None)
            for old_step in list(_FLOW_HISTORY):
                if old_step < step-72: del _FLOW_HISTORY[old_step]
        result = _flow_reorder(observation, result, cfg)
    except Exception:
        _FLOW_STATS["flow_errors"] += 1
    _FLOW_PREVIOUS = (copy.deepcopy(observation), copy.deepcopy(result))
    agent.telemetry.update(_FLOW_STATS)
    return result


agent.telemetry = {}


def kaggle_observable_queue_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
