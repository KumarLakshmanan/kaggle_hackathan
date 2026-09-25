
# SPDX-License-Identifier: Apache-2.0
"""Harvest Nocturne: observed competition pressure over a frozen farm plan.

New work: occupied-tile similarity, guarded three-turn reservations, and exact
price-curve risk ordering. Production, feeding, and route assets are inherited
from Two Coins / Moon / Shop Router. Full attribution travels with the archive.
"""
import importlib.util
import math
from pathlib import Path
import sys

SETTINGS = {'adaptive_horizon': True, 'quote_order': True}
_ROOT = Path(globals().get('__file__') or (lambda: None).__code__.co_filename).resolve().parent
_spec = importlib.util.spec_from_file_location(__name__ + '_farm', _ROOT / 'router.py')
_farm = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _farm
_spec.loader.exec_module(_farm)
_price_spec = importlib.util.spec_from_file_location(__name__ + '_prices', _ROOT / 'prices.py')
_prices = importlib.util.module_from_spec(_price_spec)
_price_spec.loader.exec_module(_prices)
_last_step = -1
_similar_streak = 0
telemetry = {'three_turn_calls': 0, 'reordered_turns': 0,
             'overlay_errors': 0, 'baseline_fallbacks': 0, 'parent_errors': 0}


def active_similarity(observation):
    """Empty tiles cannot make two unrelated production layouts look alike."""
    farms = observation['farms']
    own, rival = farms[observation['player']], farms[1-observation['player']]
    if own['unlocked_quadrants'] != rival['unlocked_quadrants']:
        return 0.0
    matches = total = 0
    for a, b in zip([t for row in own['tiles'] for t in row],
                    [t for row in rival['tiles'] for t in row]):
        sa = (a.get('crop'), a.get('animal')) if isinstance(a, dict) else (None, None)
        sb = (b.get('crop'), b.get('animal')) if isinstance(b, dict) else (None, None)
        if sa != (None, None) or sb != (None, None):
            total += 1
            matches += sa == sb
    return matches / total if total >= 8 else 0.0


def quote_priority(observation, order, stock):
    """Revenue exposed to a small rival batch, not nominal headline revenue."""
    item = order[1]
    quantity = min(max(0, int(order[2])), stock.get(item, 0))
    if not quantity or item not in _prices.MARKET_PARAMS:
        return 0.0
    inventory = observation['market']['inventory'][item]
    params = {k: dict(v) for k, v in _prices.MARKET_PARAMS.items()}
    for k, patch in observation['market'].get('params', {}).items():
        if k in params:
            params[k].update(patch)
    rival = observation['farms'][1-observation['player']]
    crop_item = item if item in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON') else None
    animal = {'EGG':'GOOSE','MILK':'COW','WOOL':'SHEEP'}.get(item)
    standing = sum(max(0, int(t.get('yield_units', 0))) for row in rival['tiles'] for t in row
                   if isinstance(t, dict) and
                   ((crop_item is not None and t.get('crop') == crop_item) or
                    (animal is not None and t.get('animal') == animal)))
    # Public fields do not reveal the rival shed. Eight units are a scenario,
    # not a recovered hidden quantity; visible ripe yield increases the stress.
    batch = min(24, max(8, standing))
    now = sum(_prices.market_price(item, inventory+j, params) for j in range(quantity))
    later = sum(_prices.market_price(item, inventory+batch+j, params) for j in range(quantity))
    return now-later


def reorder_sales(observation, action):
    """Keep quantities and purchase barriers; rank distinct contiguous sales."""
    stock = _farm.projected_shed(action, _farm.FarmView(observation))
    orders = [list(o) for o in action['market']]
    start = 0
    while start < len(orders):
        if orders[start][0] != 'SELL':
            start += 1
            continue
        end = start
        while end < len(orders) and orders[end][0] == 'SELL':
            end += 1
        block = orders[start:end]
        if len({o[1] for o in block}) == len(block):
            orders[start:end] = sorted(block, key=lambda o: quote_priority(observation, o, stock), reverse=True)
        start = end
    if orders != action['market']:
        telemetry['reordered_turns'] += 1
        action = dict(action, market=orders)
    return action


def baseline(observation, configuration=None):
    """Last-resort legal action: deliver reachable goods and liquidate the shed."""
    own = observation['farms'][observation['player']]
    center = len(own['tiles']) // 2
    positions = [own['farmer'], *own['hands']]
    work = [['DROP'] if p[0] in (center-1,center) and p[1] in (center-1,center)
            else ['PASS'] for p in positions]
    action = {'farmer':work[0], 'hands':work[1:], 'market':[]}
    stock = _farm.projected_shed(action, _farm.FarmView(observation))
    action['market'] = [['SELL', item, int(q)] for item,q in stock.items()
                        if item in _prices.MARKET_PARAMS and q > 0][:10]
    return action


def agent(observation, configuration=None):
    global _last_step, _similar_streak
    step = int(observation['step'])
    if step <= _last_step:
        _similar_streak = 0
    _last_step = step
    _farm.SALE_HORIZON = 2
    try:
        _similar_streak = _similar_streak + 1 if active_similarity(observation) >= 0.90 else 0
        if SETTINGS['adaptive_horizon'] and 336 <= step < 648 and _similar_streak >= 6:
            _farm.SALE_HORIZON = 3
            telemetry['three_turn_calls'] += 1
    except Exception:
        telemetry['overlay_errors'] += 1
    try:
        action = _farm.agent(observation, configuration)
    except Exception:
        telemetry['parent_errors'] += 1
        telemetry['baseline_fallbacks'] += 1
        return baseline(observation, configuration)
    # New ranking starts only after the irreversible farm setup is complete.
    if SETTINGS['quote_order'] and step >= 288:
        try:
            return reorder_sales(observation, action)
        except Exception:
            telemetry['overlay_errors'] += 1
    return action


agent.telemetry = telemetry
