"""Recover one blocked planting through earlier physical fertilizer delivery."""
_SEED_DELIVERY_PARENT = agent
_SEED_DELIVERY_PLAN = None
_SEED_DELIVERY_STATS = {'seed_delivery_starts': 0, 'seed_delivery_funded': 0,
                        'seed_delivery_planted': 0, 'seed_delivery_watered': 0,
                        'seed_delivery_aborts': 0, 'seed_delivery_errors': 0}


def _seed_delivery_abort():
    global _SEED_DELIVERY_PLAN
    _SEED_DELIVERY_STATS['seed_delivery_aborts'] += 1
    _SEED_DELIVERY_PLAN = None


def _seed_delivery_forecasts(obs, action, cfg):
    orders = action.get('market', [])
    raw = _ITERATED_QUEUE_RAW(obs, cfg).get('market', [])
    return [[], orders] + ([raw] if raw != orders else [])


def _seed_delivery_apply(obs, action, configuration):
    global _SEED_DELIVERY_PLAN
    cfg = configuration or {}; step = int(obs['step']); own = obs['farms'][int(obs['player'])]
    private = obs['private']; per_day = int(cfg.get('turnsPerDay', 24)); board = int(cfg.get('boardSize', 10))
    schedule = _hire_recovery_schedule(obs)
    plan = _SEED_DELIVERY_PLAN
    if plan:
        offset = step - plan['start']; worker = plan['worker']; pos = plan['pos']; crop = plan['crop']
        if len(own['hands']) < worker or own['hands'][worker-1] != pos or len(action.get('hands', [])) < worker:
            _seed_delivery_abort(); return action
        if offset == 1:
            if own['farmer'] != plan['shed']:
                _seed_delivery_abort(); return action
            action['farmer'] = ['DROP']
            if action['hands'][worker-1] != ['PASS'] or private['seeds'].get(crop, 0) != plan['available']:
                _seed_delivery_abort(); return action
            units = int(private['inventories'][0].get('FERTILIZER', 0))
            orders = action.get('market', [])
            if units < 1 or len(orders) + 2 > int(cfg.get('maxMarketOrdersPerTurn', 10)):
                _seed_delivery_abort(); return action
            proposal = orders + [['SELL', 'FERTILIZER', units], ['BUY_SEED', crop, 1]]
            stock = _queue_stock(obs, action, cfg)
            for rival in _seed_delivery_forecasts(obs, action, cfg):
                old = _queue_simulate(obs, orders, rival, stock, cfg)
                new = _queue_simulate(obs, proposal, rival, stock, cfg)
                old_shed, old_seed = dict(old[2][0]), dict(old[2][1])
                new_shed, new_seed = dict(new[2][0]), dict(new[2][1])
                old_shed.pop('FERTILIZER', None); new_shed.pop('FERTILIZER', None)
                expected_seed = dict(old_seed); expected_seed[crop] = expected_seed.get(crop, 0) + 1
                if new[0] < old[0] or old_shed != new_shed or new_seed != expected_seed or new[2][2:] != old[2][2:]:
                    _seed_delivery_abort(); return action
            action['market'] = proposal; plan['funded'] = True
            _SEED_DELIVERY_STATS['seed_delivery_funded'] += 1
            return action
        if offset == 2:
            tile = own['tiles'][pos[1]][pos[0]]
            if not plan.get('funded') or tile is not None or action['hands'][worker-1] != ['WATER'] or private['seeds'].get(crop, 0) < 1:
                _seed_delivery_abort(); return action
            action['hands'][worker-1] = ['PLANT', crop]
            _SEED_DELIVERY_STATS['seed_delivery_planted'] += 1
            return action
        if offset == 3:
            tile = own['tiles'][pos[1]][pos[0]]
            if not isinstance(tile, dict) or tile.get('crop') != crop or action['hands'][worker-1] != ['PASS']:
                _seed_delivery_abort(); return action
            action['hands'][worker-1] = ['WATER']
            _SEED_DELIVERY_STATS['seed_delivery_watered'] += 1
            _SEED_DELIVERY_PLAN = None
            return action
        _seed_delivery_abort(); return action
    if step < 144 or step % per_day > per_day - 4 or _HIRE_RECOVERY_QUEUES or action.get('farmer') != ['COLLECT_FERTILIZER']:
        return action
    if step + 3 >= len(schedule):
        return action
    following = schedule[step+1]; later = schedule[step+2]; last = schedule[step+3]
    move = following.get('farmer', ['PASS'])
    deltas = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
    if len(move) != 1 or move[0] not in deltas or later.get('farmer') != ['DROP']:
        return action
    dx, dy = deltas[move[0]]; shed = [own['farmer'][0] + dx, own['farmer'][1] + dy]
    if shed[0] not in (board//2-1, board//2) or shed[1] not in (board//2-1, board//2):
        return action
    fertilizer = int(private['inventories'][0].get('FERTILIZER', 0))
    if fertilizer < 1:
        return action
    orders = action.get('market', []); stock = _queue_stock(obs, action, cfg)
    forecasts = [_queue_simulate(obs, orders, rival, stock, cfg) for rival in _seed_delivery_forecasts(obs, action, cfg)]
    crops = [o[1] for o in orders if len(o) >= 3 and o[0] == 'BUY_SEED' and o[2] > 0]
    next_units = [following.get('farmer', ['PASS']), *following.get('hands', [])]
    for crop in crops:
        plant_workers = [i for i, command in enumerate(next_units) if command == ['PLANT', crop]]
        available = [dict(result[2][1]).get(crop, 0) for result in forecasts]
        if not available or len(set(available)) != 1 or available[0] != len(plant_workers)-1 or available[0] < 0:
            continue
        worker = plant_workers[available[0]]
        if worker == 0 or len(own['hands']) < worker or len(later.get('hands', [])) < worker or len(last.get('hands', [])) < worker:
            continue
        if later['hands'][worker-1] != ['WATER'] or last['hands'][worker-1] != ['PASS']:
            continue
        if fertilizer * max(1, obs['market']['prices']['FERTILIZER'] - fertilizer) < _PLANT_CORE['CROPS'][crop]['seed']:
            continue
        current = action.get('hands', [])[worker-1]
        pos = list(own['hands'][worker-1])
        if current and current[0] in deltas:
            x, y = deltas[current[0]]; pos = [pos[0]+x, pos[1]+y]
        elif current != ['PASS']:
            continue
        if not 0 <= pos[0] < board or not 0 <= pos[1] < board or own['tiles'][pos[1]][pos[0]] is not None:
            continue
        _SEED_DELIVERY_PLAN = dict(start=step, worker=worker, crop=crop, pos=pos, shed=shed, available=available[0])
        action['farmer'] = move
        _SEED_DELIVERY_STATS['seed_delivery_starts'] += 1
        break
    return action


def agent(observation, configuration=None):
    global _SEED_DELIVERY_PLAN
    if int(observation['step']) == 0:
        _SEED_DELIVERY_PLAN = None
        for key in _SEED_DELIVERY_STATS:
            _SEED_DELIVERY_STATS[key] = 0
    action = _SEED_DELIVERY_PARENT(observation, configuration)
    try:
        result = _seed_delivery_apply(observation, action, configuration)
    except Exception:
        _SEED_DELIVERY_STATS['seed_delivery_errors'] += 1
        result = action
    agent.telemetry.update(getattr(_SEED_DELIVERY_PARENT, 'telemetry', {}))
    agent.telemetry.update(_SEED_DELIVERY_STATS)
    return result


agent.telemetry = {}


def kaggle_seed_delivery_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
