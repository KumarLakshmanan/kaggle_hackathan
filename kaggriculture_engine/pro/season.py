"""Offline full-season forecasts with actual maturity and production ledgers.

This uses a compatible maintenance control, not a clone of uploaded main. Rival
stock, policy and future randomness remain hypotheses; terminal cash is exact
within each hypothesis. It cannot establish live competitive strength.
"""
import copy
from .. import native_core as core
from .portfolio import proposals
from .scheduler import action, commitment, counts
from .scenarios import generate, rival_action
from .simulation import make_world, observation, TransitionCache


def harvest_ledger(obs, program, cfg):
    """Count actual shadow harvests in worker execution order, without sales."""
    seat = int(obs['player']); farm = copy.deepcopy(obs['farms'][seat]); private = copy.deepcopy(obs['private'])
    result = {p: 0 for p in core.PRODUCTS}
    for idx, unit in enumerate([program['farmer']]+program.get('hands', [])):
        before = dict(core._farmer_inventory(private, idx))
        core._apply_unit_action(farm, private, idx, unit, len(farm['tiles']), int(obs['day']),
            int(cfg.get('turnsPerDay', 24)), int(cfg.get('shedCapacity', 100)))
        if unit and unit[0] == 'HARVEST':
            after = core._farmer_inventory(private, idx)
            for p in result: result[p] += max(0, after.get(p, 0)-before.get(p, 0))
    return result


def search(obs, cfg, belief, max_transitions=12000):
    seat = int(obs['player']); horizon = int(cfg.get('episodeSteps', 720))-1-int(obs['step'])
    scenarios = generate(obs, belief); base = commitment(obs); initial_counts = counts(obs['farms'][seat])
    initial_ids = set()
    for y, row in enumerate(obs['farms'][seat]['tiles']):
        for x, tile in enumerate(row):
            if isinstance(tile, dict):
                initial_ids.add((tile.get('crop', tile.get('animal')), x, y, tile.get('planted_day', tile.get('placed_day', -1))))
    plans = proposals(obs); cache = TransitionCache(0)
    report = {'scope': 'Exact native full-season cash under three hypothetical reacting rivals; compatible maintenance control; not live win probabilities.',
        'horizon': horizon, 'transitions': 0, 'partial': False, 'selected': None, 'cases': [],
        'scenarios': [{k:s[k] for k in ('name', 'future_seed', 'weight')} for s in scenarios], 'competition_qualified': False}

    def rollout(plan):
        outcomes = []
        for scenario in scenarios:
            if report['transitions']+horizon > max_transitions:
                report['partial'] = True; return None
            world = make_world(obs, cfg, scenario); produced = {p:0 for p in core.PRODUCTS}
            peak = dict(initial_counts); peak_land = len(obs['farms'][seat]['unlocked_quadrants'])
            matured = set()
            for _ in range(horizon):
                current = observation(world, seat); ours = action(current, cfg, plan)
                harvested = harvest_ledger(current, ours, cfg)
                for item, qty in harvested.items(): produced[item] += qty
                for y, row in enumerate(current['farms'][seat]['tiles']):
                    for x, tile in enumerate(row):
                        if not isinstance(tile, dict): continue
                        item = tile.get('crop', tile.get('animal'))
                        if item not in plan['targets']: continue
                        planted = tile.get('planted_day', tile.get('placed_day', -1))
                        spec = core.CROPS.get(item, core.ANIMALS.get(item))
                        if (item, x, y, planted) not in initial_ids and int(current['day'])-planted >= spec['first_yield_day'] and tile.get('yield_units', 0):
                            matured.add((item, x, y, planted))
                theirs = rival_action(world, seat, ours, scenario)
                joint = [None, None]; joint[seat] = ours; joint[1-seat] = theirs
                world = cache.advance(world, joint); report['transitions'] += 1
                current = observation(world, seat); c = counts(current['farms'][seat])
                for item, qty in c.items(): peak[item] = max(peak[item], qty)
                peak_land = max(peak_land, len(current['farms'][seat]['unlocked_quadrants']))
            current = observation(world, seat); own = current['farms'][seat]['money']; rival = current['farms'][1-seat]['money']; margin = own-rival
            additions = {item:max(0, target-initial_counts[item]) for item, target in plan['targets'].items()}
            reached = all(peak[item] >= initial_counts[item]+qty for item, qty in additions.items() if qty) and peak_land >= plan['land']
            first_output = all(sum(m[0] == item for m in matured) >= qty for item, qty in additions.items() if qty)
            outcomes.append({'scenario':scenario['name'], 'own_coins':own, 'rival_coins':rival, 'margin':margin,
                'win_points':1. if margin > 0 else .5 if margin == 0 else 0., 'terminal':world[0][seat].status == 'DONE',
                'harvested_units':produced, 'terminal_shed':current['private']['shed'], 'terminal_seeds':current['private']['seeds'],
                'peak_assets':peak, 'peak_land':peak_land, 'added_commitments_established':reached,
                'added_commitments_reached_maturity':first_output, 'remaining_inventory_has_no_terminal_cash_credit':True})
        return outcomes

    baseline = rollout(base); report['baseline'] = baseline
    if baseline is None: return report
    best = None
    for name, plan in plans:
        outcomes = rollout(plan)
        if outcomes is None:
            report['cases'].append({'name':name, 'complete':False}); continue
        gain = [r['margin']-b['margin'] for r,b in zip(outcomes, baseline)]
        points = [r['win_points']-b['win_points'] for r,b in zip(outcomes, baseline)]
        valid = all(r['terminal'] and r['added_commitments_established'] and r['added_commitments_reached_maturity'] for r in outcomes)
        viable = valid and min(gain) >= 0 and min(points) >= 0 and sum(gain)/len(gain) >= 2000
        row = {'name':name, 'plan':plan, 'complete':True, 'outcomes':outcomes, 'relative_coin_gain':gain,
            'scenario_win_point_gain':points, 'viable':viable}
        report['cases'].append(row); key = (sum(points), min(gain), sum(gain))
        if viable and (best is None or key > best[0]): best = key, row
    if best: report['selected'] = {'name':best[1]['name'], 'plan':best[1]['plan'], 'scope':'Speculative offline suggestion; requires reacting/native qualification.'}
    return report
