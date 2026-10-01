"""Prioritized, deduplicated market programs preserving executable commitments."""
from ..engine import market_children, canonical, cash_margin
from .simulation import make_world, physical_signature, TransitionCache
from .scenarios import generate, rival_action


def optimize(obs, cfg, reference, belief, nodes=12):
    orders = reference.get('market', [])
    report = {'nodes': 0, 'changed': False, 'cache_hits': 0, 'gains': []}
    if len(orders) < 2 or int(obs['hour'])%4:
        return reference, report
    seat = int(obs['player']); scenarios = generate(obs, belief, anchors=True)
    worlds = [make_world(obs, cfg, s) for s in scenarios]
    cache = TransitionCache(96)
    rivals = [rival_action(w, seat, reference, s) for w, s in zip(worlds, scenarios)]
    def advance(world, proposed, rival):
        joint = [None, None]; joint[seat] = proposed; joint[1-seat] = rival
        return cache.advance(world, joint)
    controls = [advance(w, reference, r) for w, r in zip(worlds, rivals)]
    signatures = [physical_signature(w) for w in controls]
    children = {canonical(c): c for c in market_children(orders, int(cfg.get('maxMarketOrdersPerTurn', 10)))}
    def priority(program):
        return sum((len(program)-i)*float(obs['market']['prices'].get(o[1], 0))*int(o[2])
            for i, o in enumerate(program) if len(o) == 3 and o[0] == 'SELL')
    ranked = sorted(children.values(), key=priority, reverse=True)[:nodes]
    best = (0., 0.); chosen = reference
    for program in ranked:
        proposed = dict(reference, market=program); gains = []; valid = True; report['nodes'] += 1
        for i, (w, r) in enumerate(zip(worlds, rivals)):
            result = advance(w, proposed, r)
            if physical_signature(result) != signatures[i] or result[0][0].observation.farms[seat]['money'] < controls[i][0][0].observation.farms[seat]['money']:
                valid = False; break
            gain = cash_margin(result, seat)-cash_margin(controls[i], seat)
            if gain < 0: valid = False; break
            gains.append(gain)
        score = (min(gains), sum(gains)) if valid else (-1., -1.)
        if score > best and score[1] >= 1:
            best = score; chosen = proposed; report.update(changed=True, gains=gains)
    report['cache_hits'] = cache.hits
    return chosen, report
