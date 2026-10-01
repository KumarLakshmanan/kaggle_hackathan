"""Unobserved stock, future shops and reacting rivals as explicit hypotheses."""
import hashlib
from .. import native_core as core
from ..engine import canonical
from .scheduler import action, commitment


def generate(obs, belief, count=3, anchors=False):
    public = [obs['day'], obs['town'], obs['market']['inventory']]
    seed = int(hashlib.sha256(canonical(public).encode()).hexdigest()[:8], 16)
    result = []
    for i, mode in enumerate(('immediate', 'patient', 'immediate')[:count]):
        fraction = (0., .5, 1.)[i]
        stock = {p: int(v['high']*fraction) for p, v in belief['stock_bounds'].items()}
        rival_obs = dict(obs, player=1-int(obs['player']))
        rival_plan = commitment(rival_obs, {'GOOSE': 1} if i == 2 and int(obs['day']) < 16 else None)
        result.append({'name': ('low_stock_seller', 'mid_stock_patient', 'high_stock_producer')[i],
                       'stock': stock, 'future_seed': (seed+i*104729)%2147483647,
                       'sell_mode': mode, 'market_mode': 'reactive', 'weight': 1./count, 'rival_plan': rival_plan})
    if anchors:
        own = obs['private']
        for i, mode in enumerate(('idle', 'mirror', 'frontload')):
            result.append({'name': 'v1_'+mode, 'stock': {p: int(q*(0, 1, 2)[i]) for p, q in own['shed'].items()},
                'seeds': dict(own['seeds']), 'future_seed': 3100001+i,
                'market_mode': mode, 'weight': 0.})
    return result


def rival_action(world, seat, reference, scenario):
    other = 1-seat; obs = world[0][other].observation
    if scenario['market_mode'] == 'reactive':
        plan = scenario.get('rival_plan') or commitment(obs)
        return action(obs, world[1].configuration, plan, scenario['sell_mode'])
    orders = [] if scenario['market_mode'] == 'idle' else list(reference.get('market', []))
    if scenario['market_mode'] == 'frontload': orders.sort(key=lambda o: 0 if o[0] == 'SELL' else 1)
    return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in obs.farms[other]['hands']], 'market': orders}
