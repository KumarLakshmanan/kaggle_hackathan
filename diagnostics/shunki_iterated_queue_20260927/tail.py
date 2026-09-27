"""Search two sequential improvements over the completed incumbent queue."""
_ITERATED_QUEUE_PARENT = agent
_ITERATED_QUEUE_RAW = _QUEUE_PARENT
_ITERATED_QUEUE_STATS = {
    "iterated_queue_turns": 0,
    "iterated_queue_second_pass_turns": 0,
    "iterated_queue_proposals": 0,
    "iterated_queue_predicted_gain": 0.0,
    "iterated_queue_errors": 0,
}


def _iterated_queue_apply(obs, action, configuration):
    cfg = configuration or {}
    base = action.get("market", [])
    if len(base) < 2 or len(base) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get("market", [])
    forecasts = [[], base]
    if raw != base:
        forecasts.append(raw)
    controls = [_queue_simulate(obs, base, rival, stock, cfg) for rival in forecasts]
    current, best_key = base, (0, 0, 0)
    seen = {tuple(tuple(order) for order in base)}
    accepted_passes = 0
    for _ in range(2):
        proposals = []
        for index, order in enumerate(current):
            if index == 0 or not order or order[0] not in ("SELL", "BUY_PRODUCT"):
                continue
            for earlier in range(index):
                candidate = current[:earlier] + [order] + current[earlier:index] + current[index+1:]
                signature = tuple(tuple(o) for o in candidate)
                if signature not in seen:
                    seen.add(signature)
                    proposals.append(candidate)
                if len(proposals) >= 48:
                    break
            if len(proposals) >= 48:
                break
        best_orders = current
        for proposal in proposals:
            _ITERATED_QUEUE_STATS["iterated_queue_proposals"] += 1
            relative_gains, own_gains = [], []
            valid = True
            for forecast_index, (rival, control) in enumerate(zip(forecasts, controls)):
                result = _queue_simulate(obs, proposal, rival, stock, cfg)
                if result[0] < control[0] or result[2] != control[2]:
                    valid = False
                    break
                if forecast_index:
                    if result[3] != control[3]:
                        valid = False
                        break
                    relative_gains.append((result[0]-result[1])-(control[0]-control[1]))
                own_gains.append(result[0]-control[0])
            if not valid or min(relative_gains) < 0 or sum(relative_gains) <= 0:
                continue
            key = (min(relative_gains), sum(relative_gains), min(own_gains))
            if key > best_key:
                best_key, best_orders = key, proposal
        if best_orders is current:
            break
        current = best_orders
        accepted_passes += 1
    if accepted_passes:
        action["market"] = current
        _ITERATED_QUEUE_STATS["iterated_queue_turns"] += 1
        _ITERATED_QUEUE_STATS["iterated_queue_second_pass_turns"] += int(accepted_passes == 2)
        _ITERATED_QUEUE_STATS["iterated_queue_predicted_gain"] += best_key[0]
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _ITERATED_QUEUE_STATS:
            _ITERATED_QUEUE_STATS[key] = 0
    action = _ITERATED_QUEUE_PARENT(observation, configuration)
    try:
        result = _iterated_queue_apply(observation, action, configuration)
    except Exception:
        _ITERATED_QUEUE_STATS["iterated_queue_errors"] += 1
        result = action
    agent.telemetry.update(_ITERATED_QUEUE_STATS)
    return result


agent.telemetry = {}


def kaggle_iterated_queue_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
