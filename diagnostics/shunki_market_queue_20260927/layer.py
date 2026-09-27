"""Compare current-turn queue orders using two explicit market forecasts."""
_QUEUE_PARENT = agent
_QUEUE_STATS = {"queue_turns": 0, "queue_proposals": 0, "queue_errors": 0,
                "predicted_margin_gain": 0.0}


class _QueueBox:
    def __init__(self, **values):
        self.__dict__.update(values)


def _queue_signature(farm, private):
    return (tuple(sorted(private["shed"].items())),
            tuple(sorted(private["seeds"].items())),
            tuple(tuple(p) for p in farm["hands"]),
            tuple(farm["unlocked_quadrants"]), farm.get("hires_today", 0))


def _queue_simulate(obs, own_orders, rival_orders, stock, cfg):
    player = int(obs["player"])
    farms = copy.deepcopy(obs["farms"])
    market = copy.deepcopy(obs["market"])
    private = obs["private"]
    # The opposing stock is a hypothetical mirror, never rival-private data.
    privates = [{"shed": dict(stock), "seeds": dict(private["seeds"]),
                 "inventories": [{} for _ in range(len(f["hands"])+1)]}
                for f in farms]
    states = [_QueueBox(action={"market": own_orders if i == player else rival_orders},
                        observation=_QueueBox(farms=farms, market=market, private=privates[i]))
              for i in range(2)]
    _QUEUE_ENGINE["_process_market"](states, _QueueBox(configuration=cfg))
    own = farms[player]["money"]
    rival = farms[1-player]["money"]
    return (own, rival, _queue_signature(farms[player], privates[player]),
            _queue_signature(farms[1-player], privates[1-player]))


def _queue_optimize(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    proposals, seen = [], {tuple(tuple(o) for o in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] != "SELL":
            continue
        for earlier in range(index):
            permuted = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            key = tuple(tuple(o) for o in permuted)
            if key not in seen:
                seen.add(key)
                proposals.append(permuted)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    original_idle = _queue_simulate(obs, orders, [], stock, cfg)
    original_mirror = _queue_simulate(obs, orders, orders, stock, cfg)
    best_orders = orders
    best = (original_mirror[0]-original_mirror[1], original_mirror[0])
    for proposal in proposals:
        _QUEUE_STATS["queue_proposals"] += 1
        idle = _queue_simulate(obs, proposal, [], stock, cfg)
        if idle[2] != original_idle[2] or idle[0] < original_idle[0]:
            continue
        mirror = _queue_simulate(obs, proposal, orders, stock, cfg)
        if mirror[2:] != original_mirror[2:] or mirror[0] < original_mirror[0]:
            continue
        score = (mirror[0]-mirror[1], mirror[0])
        if score > best and score[0] > original_mirror[0]-original_mirror[1]:
            best, best_orders = score, proposal
    if best_orders is not orders:
        action["market"] = best_orders
        _QUEUE_STATS["queue_turns"] += 1
        _QUEUE_STATS["predicted_margin_gain"] += best[0]-(original_mirror[0]-original_mirror[1])
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _QUEUE_STATS:
            _QUEUE_STATS[key] = 0
    action = _QUEUE_PARENT(observation, configuration)
    try:
        return _queue_optimize(observation, action, configuration)
    except Exception:
        _QUEUE_STATS["queue_errors"] += 1
        return action


agent.telemetry = _QUEUE_STATS


def kaggle_market_queue_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
