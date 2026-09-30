"""Observe failed scheduled hires, fund their retry, and reconcile worker timing."""
_HIRE_RECOVERY_PARENT = agent
_HIRE_RECOVERY_PLAN = None
_HIRE_RECOVERY_QUEUES = {}
_HIRE_RECOVERY_STATS = {'hire_recovery_turns': 0, 'hire_recovery_requested': 0,
                        'hire_recovery_delayed_commands': 0, 'hire_recovery_caught_up': 0,
                        'hire_recovery_unfilled': 0, 'hire_recovery_day_aborts': 0,
                        'hire_recovery_errors': 0}


def _hire_recovery_schedule(obs):
    if globals().get('_FARMICE_ACTIVE', False):
        return _FARMICE_TAPE
    step = int(obs['step'])
    if step < 72:
        return _DATA['opening']
    shops = obs['town'].get('unlocked_shops', [])
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step < 72 * count:
            break
        candidate = _DATA['route_map'].get('|'.join(shops[:count]))
        if candidate is not None:
            route = candidate
    if route is None:
        route = next(iter(_DATA['routes']))
    return _DATA['routes'][str(route)]


def _hire_recovery_apply(obs, action, configuration):
    global _HIRE_RECOVERY_PLAN, _HIRE_RECOVERY_QUEUES
    cfg = configuration or {}; step = int(obs['step'])
    per_day = int(cfg.get('turnsPerDay', 24)); hour = step % per_day
    own = obs['farms'][int(obs['player'])]; hands = own['hands']
    moves = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
    if hour == 0:
        _HIRE_RECOVERY_STATS['hire_recovery_day_aborts'] += len(_HIRE_RECOVERY_QUEUES)
        _HIRE_RECOVERY_QUEUES = {}; _HIRE_RECOVERY_PLAN = None
        hires = sum(order == ['HIRE'] for order in action.get('market', []))
        farmer = action.get('farmer', ['PASS'])
        if not hands and hires and farmer and farmer[0] not in moves:
            planned = copy.deepcopy(own)
            for _ in range(hires):
                planned['hands'].append(_QUEUE_ENGINE['_spawn_hand'](planned, int(cfg.get('boardSize', 10))))
            _HIRE_RECOVERY_PLAN = dict(step=step, farmer=copy.deepcopy(own['farmer']), hands=planned['hands'])
        return action

    for worker, pending in list(_HIRE_RECOVERY_QUEUES.items()):
        if worker >= len(hands) or worker >= len(action.get('hands', [])):
            _HIRE_RECOVERY_STATS['hire_recovery_unfilled'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
            continue
        current = action['hands'][worker]
        if pending and pending[0] == 'CARE':
            _HIRE_RECOVERY_STATS['hire_recovery_caught_up'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
        else:
            action['hands'][worker] = pending
            _HIRE_RECOVERY_QUEUES[worker] = current
            _HIRE_RECOVERY_STATS['hire_recovery_delayed_commands'] += 1

    plan = _HIRE_RECOVERY_PLAN
    if hour != 1 or not plan or plan['step'] != step - 1:
        return action
    missing = len(plan['hands']) - len(hands)
    if missing not in (1, 2) or hands != plan['hands'][:len(hands)] or own['farmer'] != plan['farmer']:
        return action
    active_commands = [action.get('farmer', ['PASS']), *action.get('hands', [])[:len(hands)]]
    if any(command and command[0] in moves for command in active_commands):
        return action
    orders = action.get('market', [])
    if any(order == ['HIRE'] for order in orders) or len(orders) + missing > int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    schedule = _hire_recovery_schedule(obs)
    allowed = moves | {'PICKUP', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'WATER', 'PASS'}
    delayed = {}
    for worker in range(len(hands), len(plan['hands'])):
        commands = action.get('hands', [])
        if worker >= len(commands) or commands[worker][:2] != ['PICKUP', 'WHEAT']:
            return action
        found = False
        for future in range(step + 1, min(step + 9, len(schedule))):
            upcoming = schedule[future].get('hands', [])
            if worker >= len(upcoming) or not upcoming[worker] or upcoming[worker][0] not in allowed:
                return action
            if upcoming[worker][0] == 'CARE':
                found = True
                break
        if not found:
            return action
        delayed[worker] = copy.deepcopy(commands[worker])
    proposal = orders + [['HIRE'] for _ in range(missing)]
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get('market', [])
    forecasts = [[], orders] + ([raw] if raw != orders else [])
    for rival in forecasts:
        old = _queue_simulate(obs, orders, rival, stock, cfg)
        new = _queue_simulate(obs, proposal, rival, stock, cfg)
        if new[0] < 0 or new[2][0:2] != old[2][0:2] or new[2][3] != old[2][3]:
            return action
        if new[2][2] != tuple(tuple(p) for p in plan['hands']):
            return action
    action['market'] = proposal
    _HIRE_RECOVERY_QUEUES = delayed
    _HIRE_RECOVERY_STATS['hire_recovery_turns'] += 1
    _HIRE_RECOVERY_STATS['hire_recovery_requested'] += missing
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _HIRE_RECOVERY_STATS:
            _HIRE_RECOVERY_STATS[key] = 0
    result = _HIRE_RECOVERY_PARENT(observation, configuration)
    try:
        result = _hire_recovery_apply(observation, result, configuration)
    except Exception:
        _HIRE_RECOVERY_STATS['hire_recovery_errors'] += 1
    agent.telemetry.update(getattr(_HIRE_RECOVERY_PARENT, 'telemetry', {}))
    agent.telemetry.update(_HIRE_RECOVERY_STATS)
    return result


agent.telemetry = {}


def kaggle_observed_hire_recovery_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
