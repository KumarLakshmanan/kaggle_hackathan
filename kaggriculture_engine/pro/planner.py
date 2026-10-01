"""Paired complete production rollouts; no partial leaf can activate a plan."""
import copy
from .. import native_core as core
from .scheduler import action, commitment, counts
from .simulation import make_world, TransitionCache, observation
from .scenarios import generate, rival_action
from .value import estimate


def proposals(obs):
    farm = obs['farms'][int(obs['player'])]; existing = counts(farm)
    options = [('maintain_existing', commitment(obs))]
    prices = obs['market']['prices']
    crops = sorted(('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'),
                   key=lambda c: prices[c]*core.CROPS[c]['max_yield']/core.CROPS[c]['seed'], reverse=True)
    for crop in crops[:2]:
        if int(obs['day'])+core.CROPS[crop]['first_yield_day']+2 < 30:
            options.append(('add_four_'+crop.lower(), commitment(obs, {crop: 4})))
    animal = max(core.ANIMALS, key=lambda a: prices[core.ANIMALS[a]['product']]/core.ANIMALS[a]['cost'])
    if int(obs['day'])+core.ANIMALS[animal]['first_yield_day']+2 < 30:
        options.append(('add_one_'+animal.lower(), commitment(obs, {animal: 1})))
    if len(farm['unlocked_quadrants']) < 4 and int(obs['day']) < 16:
        options.append(('funded_land_and_crop', commitment(obs, {crops[0]: 4}, land=True)))
    return options


def search(obs, cfg, belief, continuation, model, max_transitions=4096, online=False):
    seat = int(obs['player']); scenarios = generate(obs, belief)
    plans = proposals(obs)
    if online: plans = plans[:2]  # Baseline + maintenance + one expansion: bounded complete comparisons.
    # Extend twelve days through first production plus collection travel. Terminal
    # truncation is allowed only at the actual end of the episode.
    horizon = min(288, 719-int(obs['step']))
    report = {'scope': 'Native executable 12-day forecasts with heuristic reacting rivals; baseline uses immutable itinerary.',
        'horizon': horizon, 'transitions': 0, 'cases': [], 'selected': None, 'partial': False,
        'scenarios': [{k:s[k] for k in ('name', 'future_seed', 'weight')} for s in scenarios]}
    controls = []
    cache = TransitionCache(32)
    def rollout(plan):
        outcomes = []
        for scenario in scenarios:
            if report['transitions']+horizon > max_transitions:
                report['partial'] = True
                return None
            world = make_world(obs, cfg, scenario)
            for _ in range(horizon):
                current = observation(world, seat)
                ours = continuation(current, cfg) if plan is None else action(current, cfg, plan)
                theirs = rival_action(world, seat, ours, scenario)
                joint = [None, None]; joint[seat] = ours; joint[1-seat] = theirs
                world = cache.advance(world, joint); report['transitions'] += 1
            current = observation(world, seat); cash = current['farms'][seat]['money']-current['farms'][1-seat]['money']
            outcomes.append(dict(estimate(current, model), cash=cash,
                assets=counts(current['farms'][seat]), own_coins=current['farms'][seat]['money'], rival_coins=current['farms'][1-seat]['money']))
        return outcomes
    controls = rollout(None)
    if controls is None: return report
    report['baseline'] = controls
    best = None
    for name, plan in plans:
        outcomes = rollout(plan)
        if outcomes is None:
            report['cases'].append({'name': name, 'complete': False}); continue
        cash_gain = [o['cash']-c['cash'] for o, c in zip(outcomes, controls)]
        gain = [o['margin']-c['margin'] for o, c in zip(outcomes, controls)]
        uncertainty = max(o['uncertainty'] for o in outcomes)
        # Predictive errors are correlated; this is a conservative heuristic gate,
        # not a formal confidence interval. Fresh matches decide promotion.
        threshold = max(2000., uncertainty/3.)
        viable = min(cash_gain) >= 0 and min(gain) > threshold and not any(o.get('out_of_distribution') for o in outcomes)
        row = {'name': name, 'complete': True, 'plan': plan, 'outcomes': outcomes,
               'relative_cash_gain': cash_gain, 'predicted_margin_gain': gain, 'threshold': threshold, 'viable': viable}
        report['cases'].append(row)
        key = (min(gain), sum(gain))
        if viable and (best is None or key > best[0]): best = key, row
    if best: report['selected'] = {'name': best[1]['name'], 'plan': best[1]['plan']}
    report['cache_hits'] = cache.hits
    return report
