"""Fund existing scheduled animal work only after a whole remaining-day check."""
_ANIMAL_CASH_PARENT = agent
_ANIMAL_CASH_STATS = {'animal_cash_turns': 0, 'animal_cash_proposals': 0,
                      'animal_cash_units': 0, 'animal_cash_errors': 0}
_ANIMAL_CASH_PRODUCTS = ('CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL')


def _animal_cash_owned(farm, private, item):
    return (sum(isinstance(tile, dict) and tile.get('animal') == item for row in farm['tiles'] for tile in row)
            + int(private['shed'].get(item, 0)) + sum(int(inv.get(item, 0)) for inv in private['inventories']))


def _animal_cash_snapshot(farm, private):
    return dict(seeds=copy.deepcopy(private['seeds']), land=list(farm['unlocked_quadrants']),
                farmer=list(farm['farmer']), hands=copy.deepcopy(farm['hands']), tiles=copy.deepcopy(farm['tiles']))


def _animal_cash_simulate(obs, action, proposal, cfg, mirror, animal):
    core = _PLANT_CORE
    player = int(obs['player']); other = 1-player
    own = obs['farms'][player]
    farms = [copy.deepcopy(own), copy.deepcopy(own)]
    farms[other]['money'] = obs['farms'][other]['money']
    privates = [copy.deepcopy(obs['private']), copy.deepcopy(obs['private'])]
    market = copy.deepcopy(obs['market']); town = copy.deepcopy(obs['town'])
    states = [_QueueBox(action={}, observation=_QueueBox(farms=farms, private=privates[i], market=market, town=town)) for i in (0, 1)]
    env = _QueueBox(configuration=cfg)
    start = int(obs['step']); per_day = int(cfg.get('turnsPerDay', 24)); day = start // per_day
    end = min((day+1)*per_day, 719)
    board = int(cfg.get('boardSize', 10)); cap = int(cfg.get('shedCapacity', 100))
    schedule = _hire_recovery_schedule(obs)
    before = _animal_cash_owned(farms[player], privates[player], animal)
    snapshots = []; acquired = 0
    for turn in range(start, end):
        chosen = copy.deepcopy(action if turn == start else schedule[turn])
        rival = copy.deepcopy(chosen) if mirror else {'farmer': ['PASS'], 'hands': [], 'market': []}
        if turn == start:
            chosen['market'] = copy.deepcopy(proposal)
        for i, commanded in ((player, chosen), (other, rival)):
            units = [commanded.get('farmer', ['PASS']), *commanded.get('hands', [])]
            demand = {}
            for unit in units:
                if len(unit) >= 2 and unit[0] == 'PLANT':
                    demand[unit[1]] = demand.get(unit[1], 0) + 1
            blocked = {crop for crop, count in demand.items() if count > privates[i]['seeds'].get(crop, 0)}
            for worker, unit in enumerate(units):
                if len(unit) >= 2 and unit[0] == 'PLANT' and unit[1] in blocked:
                    unit = ['PASS']
                core['_apply_unit_action'](farms[i], privates[i], worker, unit, board, day, per_day, cap)
            states[i].action = commanded
        core['_process_market'](states, env)
        if turn == start:
            acquired = _animal_cash_owned(farms[player], privates[player], animal) - before
        core['_town_consume'](env, states, turn)
        for farm in farms:
            core['_decay_plants'](farm, turn)
        snapshots.append(_animal_cash_snapshot(farms[player], privates[player]))
    animal_tiles = [tile for row in farms[player]['tiles'] for tile in row if isinstance(tile, dict) and tile.get('animal')]
    wheat = int(privates[player]['shed'].get('WHEAT', 0)) + sum(int(inv.get('WHEAT', 0)) for inv in privates[player]['inventories'])
    return dict(snapshots=snapshots, acquired=acquired, farm=farms[player], private=privates[player],
                own=farms[player]['money'], rival=farms[other]['money'],
                feed_reserve=max(0, len(animal_tiles)-wheat)*market['prices']['WHEAT'])


def _animal_cash_preserves(old, new, animal):
    if old['acquired'] != 0 or new['acquired'] != 1 or new['own'] < new['feed_reserve']:
        return False
    for before, after in zip(old['snapshots'], new['snapshots']):
        if any(before[k] != after[k] for k in ('seeds', 'land', 'farmer', 'hands')):
            return False
        for y, tiles in enumerate(before['tiles']):
            for x, tile in enumerate(tiles):
                if isinstance(tile, dict) and (tile.get('kind') == 'PLANT' or tile.get('animal')):
                    if after['tiles'][y][x] != tile:
                        return False
    added = []
    for y, tiles in enumerate(new['farm']['tiles']):
        for x, tile in enumerate(tiles):
            prior = old['farm']['tiles'][y][x]
            if isinstance(tile, dict) and tile.get('animal') == animal and not (isinstance(prior, dict) and prior.get('animal') == animal):
                added.append(tile)
    return len(added) == 1 and bool(added[0].get('fed_today'))


def _animal_cash_apply(obs, action, configuration):
    if _HIRE_RECOVERY_QUEUES:
        return action
    cfg = configuration or {}; orders = action.get('market', [])
    animal_orders = [(i, order) for i, order in enumerate(orders) if len(order) >= 3 and order[0] == 'BUY_ANIMAL']
    if len(animal_orders) != 1 or animal_orders[0][1][2] != 1 or len(orders) >= int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    index, order = animal_orders[0]; animal = order[1]
    stock = _queue_stock(obs, action, cfg)
    available = [(product, quantity) for product in _ANIMAL_CASH_PRODUCTS for quantity in (1, 2) if stock.get(product, 0) >= quantity]
    if not available:
        return action
    controls = [_animal_cash_simulate(obs, action, orders, cfg, mirror, animal) for mirror in (False, True)]
    if any(control['acquired'] != 0 for control in controls):
        return action
    best = None; chosen = None; units = 0
    for product, quantity in available:
        _ANIMAL_CASH_STATS['animal_cash_proposals'] += 1
        proposal = orders[:index] + [['SELL', product, quantity]] + orders[index:]
        outcomes = [_animal_cash_simulate(obs, action, proposal, cfg, mirror, animal) for mirror in (False, True)]
        if not all(_animal_cash_preserves(old, new, animal) for old, new in zip(controls, outcomes)):
            continue
        delta = sum((new['own']-new['rival'])-(old['own']-old['rival']) for old, new in zip(controls, outcomes))
        score = (-quantity, delta, -_ANIMAL_CASH_PRODUCTS.index(product))
        if best is None or score > best:
            best, chosen, units = score, proposal, quantity
    if chosen is not None:
        action['market'] = chosen
        _ANIMAL_CASH_STATS['animal_cash_turns'] += 1
        _ANIMAL_CASH_STATS['animal_cash_units'] += units
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _ANIMAL_CASH_STATS:
            _ANIMAL_CASH_STATS[key] = 0
    result = _ANIMAL_CASH_PARENT(observation, configuration)
    try:
        result = _animal_cash_apply(observation, result, configuration)
    except Exception:
        _ANIMAL_CASH_STATS['animal_cash_errors'] += 1
    agent.telemetry.update(getattr(_ANIMAL_CASH_PARENT, 'telemetry', {}))
    agent.telemetry.update(_ANIMAL_CASH_STATS)
    return result


agent.telemetry = {}


def kaggle_observed_animal_liquidity_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
