"""Bounded two-level native order search with optional rival queue stresses."""
from ..engine import market_children, canonical
from .simulation import make_world
from .scenarios import generate, rival_action
from .projection import prepare, project, fingerprint, margin

GUARD = False


def optimize(obs, cfg, reference, belief, nodes=36):
    orders = reference.get('market', [])
    report = {'nodes': 0, 'changed': False, 'cache_hits': 0, 'gains': [], 'stress_cases': 0}
    if len(orders) < 2 or int(obs['hour'])%4:
        return reference, report
    seat = int(obs['player'])
    limit = int(cfg.get('maxMarketOrdersPerTurn', 10))
    scenarios = generate(obs, belief, anchors=True)
    cases = []
    for scenario in scenarios:
        world = make_world(obs, cfg, scenario)
        rival = rival_action(world, seat, reference, scenario)
        joint = [None, None]; joint[seat] = reference; joint[1-seat] = rival
        cases.append((prepare(world, joint), rival.get('market', [])))
    if GUARD:
        # Rival stock and ordering are hypotheses, never its hidden inventory.
        # Use a producer/own-stock mixture and test both first and delayed sales.
        relevant = sorted({o[1] for o in orders if len(o) == 3 and o[0] == 'SELL'},
                          key=lambda p: float(obs['market']['prices'].get(p, 0)), reverse=True)[:2]
        stock = {p: max(int(v['high']), int(obs['private']['shed'].get(p, 0)))
                 for p, v in belief['stock_bounds'].items()}
        for product in relevant:
            for delay in (0, 1):
                s = dict(scenarios[2], stock=stock)
                world = make_world(obs, cfg, s)
                qty = world[0][1-seat].observation.private['shed'].get(product, 0)
                queue = [[] for _ in range(delay)]+[['SELL', product, qty]]
                rival = {'farmer': ['PASS'], 'hands': [], 'market': queue}
                joint = [None, None]; joint[seat] = reference; joint[1-seat] = rival
                cases.append((prepare(world, joint), queue))
                report['stress_cases'] += 1
    controls = []
    for prepared, rival_queue in cases:
        queues = [None, None]; queues[seat] = orders; queues[1-seat] = rival_queue
        control = project(prepared, queues)
        controls.append((fingerprint(control), control[0].observation.farms[seat]['money'],
                         margin(control, seat), dict(control[0].observation.market['inventory'])))
    def priority(program):
        return sum((len(program)-i)*float(obs['market']['prices'].get(o[1], 0))*int(o[2])
                   for i, o in enumerate(program) if len(o) == 3 and o[0] == 'SELL')
    best = (0., 0.); chosen = orders; frontier = [orders]
    seen = {canonical(orders)}
    for depth in range(2):
        proposals = {}
        for parent in frontier:
            for program in market_children(parent, limit):
                key = canonical(program)
                if key not in seen: proposals[key] = program
        ranked = sorted(proposals.items(), key=lambda x: priority(x[1]), reverse=True)
        level = []
        # Reserve half of the total budget for each depth. It includes all of
        # the original v2's twelve highest-priority first-level programs.
        for key, program in ranked[:nodes//2]:
            if report['nodes'] >= nodes: break
            seen.add(key); report['nodes'] += 1
            gains = []; valid = True
            for (prepared, rival_queue), (physical, cash, baseline, inventory) in zip(cases, controls):
                queues = [None, None]; queues[seat] = program; queues[1-seat] = rival_queue
                result = project(prepared, queues)
                if (fingerprint(result) != physical or
                    result[0].observation.farms[seat]['money'] < cash or
                    result[0].observation.market['inventory'] != inventory):
                    valid = False; break
                gain = margin(result, seat)-baseline
                if gain < 0: valid = False; break
                gains.append(gain)
            if valid:
                score = (min(gains), sum(gains))
                level.append((score, program))
                if score > best and score[1] >= 1:
                    best = score; chosen = program
                    report.update(changed=True, gains=gains)
        if not level: break
        level.sort(key=lambda x: x[0], reverse=True)
        frontier = [p for _, p in level[:2]]
    return (dict(reference, market=chosen) if report['changed'] else reference), report
