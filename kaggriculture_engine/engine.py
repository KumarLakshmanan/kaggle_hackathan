"""Generate and search executable action sequences under hypothetical opponents.

The planning interface uses native transitions and only the player's observation.
Unknown rival inventories and future randomness are scenario assumptions. The
online safety mode searches market programs while preserving both farms' noncash
state, so an existing worker schedule can continue executing its commitments.
"""
import copy
import json
import math
import time
from dataclasses import dataclass

from . import native_core as core


class Box(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None
    def __setattr__(self, key, value):
        self[key] = value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def signature(state):
    """All physical and private state, including execution-relevant inventories."""
    farms = copy.deepcopy(state[0].observation.farms)
    for farm in farms:
        farm.pop('money', None)
    return canonical([farms, [s.observation.private for s in state]])


def make_world(observation, configuration, scenario):
    public = copy.deepcopy({key: observation[key] for key in ('farms', 'market', 'town', 'day', 'hour', 'step')})
    seat = int(observation['player'])
    own = copy.deepcopy(observation['private'])
    other = core._new_private()
    multiplier = scenario['stock_multiplier']
    other['shed'].update({item: max(0, int(qty * multiplier)) for item, qty in own['shed'].items()})
    capacity = int(configuration.get('shedCapacity', 100))
    excess = max(0, sum(other['shed'].values()) - capacity)
    for item in sorted(other['shed']):
        take = min(excess, other['shed'][item]); other['shed'][item] -= take; excess -= take
    other['seeds'].update(own['seeds'])
    other['inventories'] = [{} for _ in range(len(public['farms'][1-seat]['hands']) + 1)]
    state = [Box(status='ACTIVE', reward=0, action={}, observation=Box(**public, player=p,
                 private=own if p == seat else other)) for p in (0, 1)]
    cfg = dict(configuration); cfg['seed'] = None
    return state, Box(configuration=Box(**cfg), info={'seed': scenario['future_seed']}, done=False)


DEFAULT_SCENARIOS = (
    {'name': 'idle', 'stock_multiplier': 0, 'market_mode': 'idle', 'future_seed': 3100001},
    {'name': 'mirror', 'stock_multiplier': 1, 'market_mode': 'mirror', 'future_seed': 3100002},
    {'name': 'frontload', 'stock_multiplier': 2, 'market_mode': 'frontload', 'future_seed': 3100003},
)


def rival_action(state, seat, reference, scenario):
    other = 1-seat
    mode = scenario['market_mode']
    if mode == 'idle':
        orders = []
    elif mode == 'mirror':
        orders = copy.deepcopy(reference.get('market', []))
    else:
        orders = copy.deepcopy(reference.get('market', []))
        orders.sort(key=lambda order: 0 if order and order[0] == 'SELL' else 1)
    return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in state[0].observation.farms[other]['hands']],
            'market': orders}


def advance(world, seat, action, reference, scenario):
    state, env = copy.deepcopy(world)
    state[seat].action = copy.deepcopy(action)
    state[1-seat].action = rival_action(state, seat, reference, scenario)
    step = int(state[0].observation.step)
    core.interpreter(state, env)
    for entry in state:
        entry.observation.step = step+1
    return state, env


def cash_margin(world, seat):
    farms = world[0][0].observation.farms
    return float(farms[seat]['money']) - float(farms[1-seat]['money'])


def market_children(orders, max_orders=10, split=True):
    """Synthesize new programs by moving, splitting, and merging orders."""
    for start in range(len(orders)):
        for end in range(len(orders)):
            if start != end:
                child = copy.deepcopy(orders)
                child.insert(end, child.pop(start))
                yield child
    if split and len(orders) < max_orders:
        for index, order in enumerate(orders):
            if len(order) != 3 or order[0] not in ('SELL', 'BUY_PRODUCT'):
                continue
            qty = int(order[2])
            if qty < 2:
                continue
            for part in sorted({1, qty//2, qty-1}):
                for target in (0, len(orders)):
                    child = copy.deepcopy(orders)
                    child[index][2] = qty-part
                    child.insert(target, [order[0], order[1], part])
                    yield child
    for i in range(len(orders)-1):
        a, b = orders[i:i+2]
        if len(a) == len(b) == 3 and a[:2] == b[:2]:
            yield copy.deepcopy(orders[:i]) + [[a[0], a[1], int(a[2])+int(b[2])]] + copy.deepcopy(orders[i+2:])


@dataclass(frozen=True)
class SearchConfig:
    width: int = 3
    depth: int = 3
    max_nodes: int = 72
    seconds: float = 0.
    split_orders: bool = True
    min_gain: float = 1.


def optimize_market(observation, action, configuration, settings=SearchConfig()):
    """Bounded robust search. Money values are forecasts, never win probabilities."""
    cfg = configuration or {}
    orders = action.get('market', [])
    seat = int(observation['player'])
    report = dict(nodes=0, accepted=False, scope='one_turn_market_program', scenarios=[],
                  best_path=[], gain=0., budget_exhausted=False)
    if len(orders) < 2:
        return action, report
    max_orders = int(cfg.get('maxMarketOrdersPerTurn', 10))
    start = time.perf_counter()
    worlds = [make_world(observation, cfg, scenario) for scenario in DEFAULT_SCENARIOS]
    controls = [advance(world, seat, action, action, scenario) for world, scenario in zip(worlds, DEFAULT_SCENARIOS)]
    physical = [signature(world[0]) for world in controls]
    cash = [cash_margin(world, seat) for world in controls]
    owncash = [float(world[0][0].observation.farms[seat]['money']) for world in controls]
    report['scenarios'] = [{'name': scenario['name'], 'baseline_margin': cash[i]} for i, scenario in enumerate(DEFAULT_SCENARIOS)]
    best_key, best_orders, best_path = (0., 0., 0.), orders, []
    frontier = [(best_key, orders, [])]
    seen = {canonical(orders)}
    for depth in range(settings.depth):
        candidates = []
        for _, parent, path in frontier:
            for proposed in market_children(parent, max_orders, settings.split_orders):
                if report['nodes'] >= settings.max_nodes or (settings.seconds > 0 and time.perf_counter()-start >= settings.seconds):
                    report['budget_exhausted'] = True
                    break
                key = canonical(proposed)
                if key in seen:
                    continue
                seen.add(key); report['nodes'] += 1
                trial = dict(action, market=proposed)
                results, valid = [], True
                for i, (world, scenario) in enumerate(zip(worlds, DEFAULT_SCENARIOS)):
                    result = advance(world, seat, trial, action, scenario)
                    if signature(result[0]) != physical[i] or result[0][0].observation.farms[seat]['money'] < owncash[i]:
                        valid = False; break
                    delta = cash_margin(result, seat)-cash[i]
                    if delta < 0:
                        valid = False; break
                    results.append(delta)
                if not valid:
                    continue
                score = (min(results), sum(results), results[0])
                newpath = path + [proposed]
                candidates.append((score, proposed, newpath))
                if score > best_key and sum(results) >= settings.min_gain:
                    best_key, best_orders, best_path = score, proposed, newpath
                    report['scenario_gains'] = results
            if report['budget_exhausted']:
                break
        if not candidates or report['budget_exhausted']:
            break
        candidates.sort(key=lambda row: row[0], reverse=True)
        frontier = candidates[:settings.width]
    report.update(accepted=best_orders != orders, gain=best_key[1], best_path=best_path,
                  elapsed_seconds=time.perf_counter()-start)
    return (dict(action, market=best_orders) if report['accepted'] else action), report


def physical_children(observation, reference, configuration):
    """Generate new local production actions, including coordinated planting."""
    yield copy.deepcopy(reference)
    seat = int(observation['player']); farm = observation['farms'][seat]
    private = observation['private']; cfg = configuration or {}
    commands = [reference.get('farmer', ['PASS'])] + list(reference.get('hands', []))
    positions = [farm['farmer']] + farm['hands']
    while len(commands) < len(positions):
        commands.append(['PASS'])
    for index, pos in enumerate(positions):
        x, y = pos; tile = farm['tiles'][y][x]
        choices = []
        if isinstance(tile, dict):
            if tile.get('kind') == 'PLANT':
                if tile.get('yield_units', 0): choices.append(['HARVEST'])
                if not tile.get('watered_today'): choices.append(['WATER'])
                if private['inventories'][index].get('FERTILIZER', 0): choices.append(['FERTILIZE'])
            elif tile.get('kind') == 'ANIMAL':
                choices.extend([['HARVEST'], ['FEED'], ['CARE'], ['COLLECT_FERTILIZER']])
        elif tile is None:
            choices.extend([['PLANT', crop] for crop, qty in private['seeds'].items() if qty > 0])
            choices.extend([['BUILD_COOP'], ['BUILD_PASTURE']])
        for command in choices:
            if command == commands[index]: continue
            units = copy.deepcopy(commands); units[index] = command
            yield dict(reference, farmer=units[0], hands=units[1:])
    for orders in market_children(reference.get('market', []), int(cfg.get('maxMarketOrdersPerTurn', 10))):
        yield dict(reference, market=orders)
    # Complete investment bundles; they are executed and valued in the rollout.
    for crop, qty in (('WHEAT', 4), ('CARROT', 4), ('MELON', 4), ('STRAWBERRY', 4)):
        orders = list(reference.get('market', []))
        if len(orders) < int(cfg.get('maxMarketOrdersPerTurn', 10)):
            yield dict(reference, market=orders + [['BUY_SEED', crop, qty]])


def terminal_value(world, seat):
    """Approximate leaf value; longer-horizon correctness requires validation."""
    state, env = world
    value = cash_margin(world, seat)
    if state[seat].status == 'DONE': return value
    market = state[0].observation.market
    for player, sign in ((seat, 1), (1-seat, -1)):
        private = state[player].observation.private
        # Discount unsold inventory. Seeds are valued only at acquisition cost;
        # no imagined harvest is credited for an unexecuted planting plan.
        value += sign * .5 * sum(qty * market['prices'].get(item, 0) for item, qty in private['shed'].items())
        value += sign * .25 * sum(qty * core.CROPS[crop]['seed'] for crop, qty in private['seeds'].items())
        for inventory in private['inventories']:
            value += sign * .4 * sum(qty * market['prices'].get(item, 0) for item, qty in inventory.items())
    return value


def search_plan(observation, configuration, continuation, horizon=12, width=4, max_nodes=400, seconds=10.):
    """Offline beam search generating physical/market plans from legal observations.

Continuation must be a deterministic, side-effect-free function of observation.
All retained paths use one common action per step across the scenario worlds.
This is an open-loop recommendation; run again after the next observation.
"""
    if not 1 <= horizon <= 719 or width < 1 or max_nodes < 1 or seconds <= 0:
        raise ValueError('Positive horizon, width, node and time budgets are required.')
    seat = int(observation['player']); cfg = configuration or {}
    worlds = [make_world(observation, cfg, scenario) for scenario in DEFAULT_SCENARIOS]
    started = time.perf_counter(); nodes = 0
    frontier = [(min(terminal_value(world, seat) for world in worlds), worlds, [])]
    for depth in range(horizon):
        expanded = []
        for _, current, path in frontier:
            if current[0][0][seat].status == 'DONE':
                expanded.append((min(terminal_value(w, seat) for w in current), current, path)); continue
            visible = current[0][0][seat].observation
            reference = continuation(copy.deepcopy(visible), cfg)
            seen = set()
            for action in physical_children(visible, reference, cfg):
                key = canonical(action)
                if key in seen: continue
                seen.add(key)
                if nodes >= max_nodes or time.perf_counter()-started >= seconds: break
                next_worlds = [advance(w, seat, action, reference, scenario) for w, scenario in zip(current, DEFAULT_SCENARIOS)]
                nodes += 1
                # Remove no-effect action aliases to conserve the beam.
                scores = [terminal_value(w, seat) for w in next_worlds]
                expanded.append((min(scores), next_worlds, path+[action]))
            if nodes >= max_nodes or time.perf_counter()-started >= seconds: break
        if not expanded: break
        unique = {}
        for node in expanded:
            key = canonical([w[0][seat].observation for w in node[1]])
            if key not in unique or node[0] > unique[key][0]: unique[key] = node
        frontier = sorted(unique.values(), key=lambda n:n[0], reverse=True)[:width]
        if nodes >= max_nodes or time.perf_counter()-started >= seconds: break
    score, selected, path = frontier[0]
    return dict(actions=path, nodes=nodes, requested_horizon=horizon, completed_depth=len(path),
                elapsed_seconds=time.perf_counter()-started, estimated_leaf_value=score,
                scenario_results=[dict(name=s['name'], own_coins=w[0][0].observation.farms[seat]['money'],
                                       opponent_coins=w[0][0].observation.farms[1-seat]['money'],
                                       margin=cash_margin(w, seat), leaf_value=terminal_value(w, seat))
                                  for w,s in zip(selected,DEFAULT_SCENARIOS)],
                assumptions=list(DEFAULT_SCENARIOS), uses_hidden_rival_state=False,
                uses_episode_seed=False, final_season_forecast=all(w[0][seat].status=='DONE' for w in selected),
                limitation='Hypothetical opponent actions/private stocks and discounted leaf valuation; no measured win probability.')
