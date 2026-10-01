"""Exact initialized native transitions with isolated, bounded cached branches."""
import copy
from collections import OrderedDict
from .. import native_core as core
from ..engine import Box, canonical


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def make_world(obs, cfg, scenario):
    public = copy.deepcopy({k: obs[k] for k in ('farms', 'market', 'town', 'day', 'hour', 'step')})
    seat = int(obs['player'])
    other = core._new_private()
    other['shed'].update(scenario.get('stock', {}))
    remaining = int(cfg.get('shedCapacity', 100))
    for item in sorted(other['shed']):
        qty = max(0, min(remaining, int(other['shed'][item])))
        other['shed'][item] = qty
        remaining -= qty
    other['seeds'].update(scenario.get('seeds', {}))
    other['inventories'] = [{} for _ in range(len(public['farms'][1-seat]['hands'])+1)]
    own = copy.deepcopy(obs['private'])
    state = [Box(status='ACTIVE', reward=0, action={}, observation=Box(**public, player=p,
             private=own if p == seat else other)) for p in (0, 1)]
    config = dict(cfg, seed=None)
    return state, Box(configuration=Box(**config), info={'seed': scenario['future_seed']}, done=False)


class TransitionCache:
    """The cache owns its values; callers can never mutate a stored branch."""
    def __init__(self, capacity=128):
        self.capacity = capacity
        self.values = OrderedDict()
        self.hits = self.misses = 0

    def advance(self, world, actions):
        state, env = world
        # Include both private states, every public field, status, config and seed.
        key = canonical([state, env, actions])
        if key in self.values:
            self.hits += 1
            self.values.move_to_end(key)
            return copy.deepcopy(self.values[key])
        self.misses += 1
        result = copy.deepcopy(world)
        entries, environment = result
        step = int(entries[0].observation.step)
        for p in (0, 1):
            entries[p].action = copy.deepcopy(actions[p])
        core.interpreter(entries, environment)
        for entry in entries:
            entry.observation.step = step+1
        if self.capacity:
            self.values[key] = copy.deepcopy(result)
            if len(self.values) > self.capacity:
                self.values.popitem(last=False)
        return result


def observation(world, seat):
    return plain(world[0][seat].observation)


def physical_signature(world):
    farms = copy.deepcopy(world[0][0].observation.farms)
    for farm in farms:
        farm.pop('money', None)
    return canonical([farms, [s.observation.private for s in world[0]]])
