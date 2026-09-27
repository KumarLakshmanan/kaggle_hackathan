# Isolated observed-physical milk sale-race pilot; generated into a full source.
_PS_PARENT = agent
_PS_MODEL = __EMBEDDED_MODEL__
_PS_STATES = {}
_PS_REPORT = dict(score_checks=0, risk_high=0, quote_eligible=0,
                  triggered=0, units=0, errors=0)
_PS_SHED = ((4, 4), (5, 4), (4, 5), (5, 5))


def _ps_distance(a, b):
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def _ps_state(player, step):
    state = _PS_STATES.get(player)
    if state is None or step == 0 or step <= state['last_step']:
        state = dict(last_step=-1, quotes=[], inventory=[], own_money=[],
                     rival_money=[], last_sale=-1000, block_until=-1)
        _PS_STATES[player] = state
    state['last_step'] = step
    return state


def _ps_physical(obs, seat):
    farms = obs['farms']
    rival = farms[1-seat]
    workers = [rival['farmer'], *(rival.get('hands') or [])]
    ready = []
    producers = []
    for y, line in enumerate(rival.get('tiles') or []):
        for x, tile in enumerate(line):
            if isinstance(tile, dict) and tile.get('animal') == 'COW':
                producers.append((x, y))
                units = max(0, int(tile.get('yield_units', 0) or 0))
                if units:
                    ready.append(((x, y), units))
    worker_positions = {tuple(worker) for worker in workers}
    ready_units = sum(units for _, units in ready)
    worker_distance = min((_ps_distance(worker, pos)
                           for worker in workers for pos, _ in ready), default=10)
    shed_distance = min((_ps_distance(pos, shed)
                         for pos, _ in ready for shed in _PS_SHED), default=10)
    producer_positions = set(producers)
    matches = total = 0
    for a, b in zip(farms[0].get('tiles') or [], farms[1].get('tiles') or []):
        for x, y in zip(a, b):
            total += 1
            matches += x == y
    return dict(rival_ready_units=ready_units,
                rival_ready_tiles=len(ready),
                rival_worker_on_ready_units=sum(units for pos, units in ready
                                                if pos in worker_positions),
                rival_worker_min_ready_distance=min(10, worker_distance),
                rival_workers_on_item_tiles=sum(tuple(w) in producer_positions for w in workers),
                rival_workers_near_shed=sum(min(_ps_distance(w, s) for s in _PS_SHED) <= 1
                                            for w in workers),
                rival_shed_min_ready_distance=min(10, shed_distance),
                physical_match_fraction=matches / total if total else 0.0)


def _ps_features(obs, action, state, step, player):
    farms = obs['farms']
    own, rival = farms[player], farms[1-player]
    market = obs['market']
    quote = int(market['prices'].get('MILK', 0) or 0)
    level = int(market['inventory'].get('MILK', 0) or 0)
    state['quotes'].append(quote)
    state['inventory'].append(level)
    state['own_money'].append(float(own.get('money', 0) or 0))
    state['rival_money'].append(float(rival.get('money', 0) or 0))
    qhist, ihist = state['quotes'], state['inventory']
    ohist, rhist = state['own_money'], state['rival_money']
    f = dict(item='MILK', step=step, hour=step % 24,
             stock=int((obs.get('private') or {}).get('shed', {}).get('MILK', 0) or 0),
             quote=quote, market_inventory=level,
             quote_delta_1=quote-qhist[max(0, len(qhist)-2)],
             quote_delta_4=quote-qhist[max(0, len(qhist)-5)],
             inventory_delta_1=level-ihist[max(0, len(ihist)-2)],
             inventory_delta_4=level-ihist[max(0, len(ihist)-5)],
             since_own_sale=min(120, step-state['last_sale']),
             own_producers=sum(isinstance(t, dict) and t.get('animal') == 'COW'
                               for line in own.get('tiles') or [] for t in line),
             rival_producers=sum(isinstance(t, dict) and t.get('animal') == 'COW'
                                 for line in rival.get('tiles') or [] for t in line),
             own_money_delta_4=ohist[-1]-ohist[max(0, len(ohist)-5)],
             rival_money_delta_4=rhist[-1]-rhist[max(0, len(rhist)-5)],
             market_order_count=len(action.get('market') or []))
    f.update(_ps_physical(obs, player))
    return f


def _ps_probability(features):
    model = _PS_MODEL
    values = [float(features[key]) for key in model['numeric_features']]
    z = model['weights'][0]
    for i, value in enumerate(values):
        normalized = (value-model['center'][i]) / model['scale'][i]
        normalized = max(-5.0, min(5.0, normalized))
        z += normalized * model['weights'][1+i]
    z += model['weights'][1+len(values)+model['products'].index('MILK')]
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def _ps_next_own_sale(player, step):
    for future in range(step+1, min(718, step+24)+1):
        if future//24 != step//24:
            break
        for order in _adv_future(player, future):
            if (isinstance(order, list) and len(order) >= 3
                    and order[:2] == ['SELL', 'MILK'] and int(order[2] or 0) > 0):
                return future, int(order[2])
    return None


def _ps_action(obs, action, state, f, step, player):
    if not 144 <= step < 718 or step <= state['block_until']:
        return action
    if f['stock'] < 3 or f['rival_ready_units'] < 3:
        return action
    market_orders = action.get('market') or []
    if len(market_orders) >= 10 or any(o and o[0] != 'SELL' for o in market_orders):
        return action
    if any(isinstance(o, list) and len(o) > 1 and o[1] == 'MILK' for o in market_orders):
        return action
    commands = [action.get('farmer') or ['PASS'], *(action.get('hands') or [])]
    if any(isinstance(c, list) and c[:2] == ['PICKUP', 'MILK'] for c in commands):
        return action
    next_sale = _ps_next_own_sale(player, step)
    if next_sale is None:
        return action
    _PS_REPORT['score_checks'] += 1
    probability = _ps_probability(f)
    if probability < 0.30:
        return action
    _PS_REPORT['risk_high'] += 1
    projected = projected_shed(action, FarmView(obs))
    quantity = min(8, f['stock'], int(projected.get('MILK', 0)), next_sale[1])
    if quantity < 3:
        return action
    inventory = f['market_inventory']
    batch = min(10, f['rival_ready_units'])
    params = (obs.get('market') or {}).get('params')
    drop = sum(_r37_market_price('MILK', inventory+j, params)
               - _r37_market_price('MILK', inventory+batch+j, params)
               for j in range(quantity))
    if drop < 16:
        return action
    _PS_REPORT['quote_eligible'] += 1
    result = dict(action, market=[*market_orders, ['SELL', 'MILK', quantity]])
    state['block_until'] = next_sale[0]
    _PS_REPORT['triggered'] += 1
    _PS_REPORT['units'] += quantity
    return result


def agent(observation, configuration=None):
    step = int(observation['step'])
    player = int(observation['player'])
    if step == 0:
        _PS_REPORT.update(score_checks=0, risk_high=0, quote_eligible=0,
                          triggered=0, units=0, errors=0)
    parent = _PS_PARENT(observation, configuration)
    try:
        state = _ps_state(player, step)
        features = _ps_features(observation, parent, state, step, player)
        result = _ps_action(observation, parent, state, features, step, player)
        if any(isinstance(o, list) and len(o) >= 3 and o[:2] == ['SELL', 'MILK']
               and int(o[2] or 0) > 0 for o in result.get('market') or []):
            state['last_sale'] = step
        return result
    except Exception:
        _PS_REPORT['errors'] += 1
        return parent


agent.telemetry = _PS_REPORT
kaggle_submission_agent = agent
