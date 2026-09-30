"""Guarded adjacent sale/seed swap appended to exact uploaded 4ee."""

_SEED_PREFUND_PARENT = agent
_SEED_PREFUND_STATS = {"seed_prefund_structural": 0, "seed_prefund_turns": 0,
                       "seed_prefund_rejected": 0, "seed_prefund_errors": 0}


def _seed_prefund_signature_ok(before, after, crop):
    # _queue_signature: shed, seeds, hands, unlocked land, hires_today.
    if before[0] != after[0] or before[2:] != after[2:]:
        return 0
    old_seeds, new_seeds = dict(before[1]), dict(after[1])
    gain = new_seeds.get(crop, 0) - old_seeds.get(crop, 0)
    if gain < 1:
        return 0
    for item in set(old_seeds) | set(new_seeds):
        if item != crop and old_seeds.get(item, 0) != new_seeds.get(item, 0):
            return 0
    return gain


def _seed_prefund_apply(observation, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if not isinstance(orders, list) or not (2 <= len(orders) <= int(cfg.get("maxMarketOrdersPerTurn", 10))):
        return action
    seed, sale = orders[0], orders[1]
    if not (isinstance(seed, list) and len(seed) >= 3 and seed[0] == "BUY_SEED"
            and isinstance(sale, list) and len(sale) >= 3 and sale[0] == "SELL"
            and sale[1] == "WHEAT"):
        return action
    crop = seed[1]
    if crop not in _QUEUE_ENGINE["CROPS"]:
        return action
    try:
        requested_seeds, requested_sales = int(seed[2]), int(sale[2])
    except (TypeError, ValueError):
        return action
    if requested_seeds < 1 or requested_sales < 1:
        return action
    player = int(observation["player"])
    cash = float(observation["farms"][player]["money"])
    seed_price = float(_QUEUE_ENGINE["CROPS"][crop]["seed"])
    if cash >= seed_price:
        return action  # Existing first seed unit already executes.
    stock = _queue_stock(observation, action, cfg)
    if stock.get("WHEAT", 0) < 1:
        return action
    _SEED_PREFUND_STATS["seed_prefund_structural"] += 1
    candidate = [sale, seed] + orders[2:]

    # Installed 1.32.7 market semantics, first with no rival order and then
    # against a hypothetical mirror queue. No rival-private holdings are read.
    idle_old = _queue_simulate(observation, orders, [], stock, cfg)
    idle_new = _queue_simulate(observation, candidate, [], stock, cfg)
    mirror_old = _queue_simulate(observation, orders, orders, stock, cfg)
    mirror_new = _queue_simulate(observation, candidate, orders, stock, cfg)
    idle_gain = _seed_prefund_signature_ok(idle_old[2], idle_new[2], crop)
    mirror_gain = _seed_prefund_signature_ok(mirror_old[2], mirror_new[2], crop)
    if idle_gain < 1 or mirror_gain < 1 or mirror_new[3] != mirror_old[3]:
        _SEED_PREFUND_STATS["seed_prefund_rejected"] += 1
        return action
    # Beyond the known seed cost, do not accept a modeled market loss larger
    # than 20 coins to either our receipts or our relative cash margin.
    idle_market_delta = idle_new[0] - idle_old[0] + idle_gain * seed_price
    mirror_market_delta = (mirror_new[0] - mirror_old[0]
                           + mirror_gain * seed_price
                           - (mirror_new[1] - mirror_old[1]))
    if idle_market_delta < -20 or mirror_market_delta < -20:
        _SEED_PREFUND_STATS["seed_prefund_rejected"] += 1
        return action
    result = dict(action)
    result["market"] = candidate
    _SEED_PREFUND_STATS["seed_prefund_turns"] += 1
    return result


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _SEED_PREFUND_STATS:
            _SEED_PREFUND_STATS[key] = 0
    action = _SEED_PREFUND_PARENT(observation, configuration)
    try:
        result = _seed_prefund_apply(observation, action, configuration)
    except Exception:
        _SEED_PREFUND_STATS["seed_prefund_errors"] += 1
        result = action
    agent.telemetry.update(_SEED_PREFUND_STATS)
    return result


agent.telemetry = {}


def kaggle_seed_prefund_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
