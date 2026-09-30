"""Bounded joint order/quantity search, using public current-turn forecasts."""
_JOINT_MARKET_PARENT = agent
_JOINT_MARKET_STATS = {'joint_market_turns': 0, 'joint_market_proposals': 0,
                       'joint_market_depth2_turns': 0, 'joint_market_gain': 0,
                       'joint_market_errors': 0}


def _joint_market_neighbors(orders):
    for item in ('WHEAT', 'FERTILIZER'):
        buys = [i for i, o in enumerate(orders) if o[:2] == ['BUY_PRODUCT', item] and len(o) > 2]
        sells = [i for i, o in enumerate(orders) if o[:2] == ['SELL', item] and len(o) > 2]
        if not buys or not sells:
            continue
        bi, si = buys[0], sells[0]
        for delta in (4, 12, 24, -4, -12, -24):
            if min(orders[bi][2], orders[si][2]) + delta <= 0 or max(orders[bi][2], orders[si][2]) + delta > 100:
                continue
            new = [list(o) for o in orders]
            new[bi][2] += delta; new[si][2] += delta
            yield new
    for index, order in enumerate(orders):
        if not order or order[0] not in ('SELL', 'BUY_PRODUCT'):
            continue
        rest = orders[:index] + orders[index+1:]
        for destination in range(len(orders)):
            if destination != index:
                yield rest[:destination] + [order] + rest[destination:]


def _joint_market_apply(obs, action, configuration):
    cfg = configuration or {}; base = action.get('market', [])
    if int(obs['step']) < 144 or float(obs.get('remainingOverageTime', 60)) < 10 or not 2 <= len(base) <= int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get('market', [])
    forecasts = [[], base] + ([raw] if raw != base else [])
    controls = [_queue_simulate(obs, base, rival, stock, cfg) for rival in forecasts]
    seen = {tuple(tuple(o) for o in base)}
    best_key = (0, 0, 0); best_orders = base; best_depth = 0
    beam = [(best_key, base)]; count = 0
    for depth in (1, 2):
        limit = count + 32
        next_beam = []
        for _, node in beam:
            for proposal in _joint_market_neighbors(node):
                key = tuple(tuple(o) for o in proposal)
                if key in seen:
                    continue
                if count >= limit:
                    break
                seen.add(key); count += 1
                _JOINT_MARKET_STATS['joint_market_proposals'] += 1
                gains = []; own_gains = []
                for i, (forecast, control) in enumerate(zip(forecasts, controls)):
                    result = _queue_simulate(obs, proposal, forecast, stock, cfg)
                    if result[2] != control[2] or result[0] < control[0]:
                        break
                    own_gains.append(result[0] - control[0])
                    if i:
                        gain = (result[0] - result[1]) - (control[0] - control[1])
                        if result[3] != control[3] or gain < 0:
                            break
                        gains.append(gain)
                else:
                    score = (min(gains), sum(gains), min(own_gains))
                    if score > (0, 0, 0):
                        next_beam.append((score, proposal))
                        if score > best_key:
                            best_key, best_orders, best_depth = score, proposal, depth
            if count >= limit:
                break
        if not next_beam:
            break
        next_beam.sort(key=lambda pair: pair[0], reverse=True)
        beam = next_beam[:2]
    if best_orders is not base:
        action['market'] = best_orders
        _JOINT_MARKET_STATS['joint_market_turns'] += 1
        _JOINT_MARKET_STATS['joint_market_depth2_turns'] += int(best_depth == 2)
        _JOINT_MARKET_STATS['joint_market_gain'] += best_key[0]
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _JOINT_MARKET_STATS:
            _JOINT_MARKET_STATS[key] = 0
    action = _JOINT_MARKET_PARENT(observation, configuration)
    try:
        result = _joint_market_apply(observation, action, configuration)
    except Exception:
        _JOINT_MARKET_STATS['joint_market_errors'] += 1
        result = action
    agent.telemetry.update(getattr(_JOINT_MARKET_PARENT, 'telemetry', {}))
    agent.telemetry.update(_JOINT_MARKET_STATS)
    return result


agent.telemetry = {}


def kaggle_joint_market_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
