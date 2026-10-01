"""Reuse exact physical execution, then branch with the native market engine."""
import copy
from .. import native_core as core
from ..engine import Box, canonical


def prepare(world, actions):
    state, env = copy.deepcopy(world)
    cfg = env.configuration
    size = int(cfg.get('boardSize', 10))
    tpd = max(1, int(cfg.get('turnsPerDay', 24)))
    cap = int(cfg.get('shedCapacity', 100))
    day = int(state[0].observation.step)//tpd
    for seat in (0, 1):
        act = actions[seat]
        commands = [act.get('farmer', ['PASS'])]+list(act.get('hands', []))
        demand = {}
        for cmd in commands:
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == 'PLANT':
                demand[cmd[1]] = demand.get(cmd[1], 0)+1
        private = state[seat].observation.private
        blocked = {p for p, n in demand.items() if n > private['seeds'].get(p, 0)}
        for idx, cmd in enumerate(commands):
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == 'PLANT' and cmd[1] in blocked:
                cmd = ['PASS']
            core._apply_unit_action(state[0].observation.farms[seat], private, idx,
                                   cmd, size, day, tpd, cap)
    return state, env


def project(prepared, queues):
    original, env = prepared
    # _process_market mutates money, hands, land, tile cells and private dicts.
    # Clone tile dictionaries too so returned branches cannot mutate the parent.
    farms = []
    for old in original[0].observation.farms:
        farm = dict(old)
        farm['farmer'] = list(old['farmer'])
        farm['hands'] = [list(p) for p in old['hands']]
        farm['unlocked_quadrants'] = list(old['unlocked_quadrants'])
        farm['tiles'] = [[dict(tile) if isinstance(tile, dict) else tile for tile in row]
                         for row in old['tiles']]
        farms.append(farm)
    old_market = original[0].observation.market
    market = dict(old_market, inventory=dict(old_market['inventory']), prices=dict(old_market['prices']))
    if 'params' in market:
        market['params'] = {p: dict(spec) for p, spec in market['params'].items()}
    state = []
    for seat in (0, 1):
        old = original[seat].observation.private
        private = dict(old, shed=dict(old['shed']), seeds=dict(old['seeds']),
                       inventories=[dict(inv) for inv in old['inventories']])
        obs = Box(farms=farms, market=market, private=private)
        state.append(Box(action={'market': queues[seat]}, observation=obs))
    core._process_market(state, env)
    return state


def fingerprint(state):
    farms = [dict(f) for f in state[0].observation.farms]
    for farm in farms: farm.pop('money', None)
    return canonical([farms, [s.observation.private for s in state]])


def margin(state, seat):
    farms = state[0].observation.farms
    return float(farms[seat]['money'])-float(farms[1-seat]['money'])
