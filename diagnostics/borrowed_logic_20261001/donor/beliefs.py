"""Bounded, observation-only rival supply and hypothetical future demand models.

No hidden state, episode identity, native seed, recorded action, or rank is read.
A SupplyBelief belongs to ONE policy instance/episode. Its summaries are evidence
plus explicitly labelled hypotheses, never a reconstruction of private state.
"""
from __future__ import annotations

import copy
import math

from . import native_core as core


RULE_DEFAULTS = dict(episodeSteps=720, boardSize=10, turnsPerDay=24,
                     shedCapacity=100, maxMarketOrdersPerTurn=10,
                     townShopSellInterval=4, townCenterSellInterval=24,
                     townShopUnlockInterval=3)
# These are named stress mixtures, not calibrated probabilities or RNG predictions.
# The legacy low/high aliases describe demand for premium animal products only.
REGIMES = {
    'low_demand': dict(shop_weights={'PET_CAFE': 3, 'FARMERS_MARKET': 3, 'BAKERY': 2}, service=1.0, care=1.0),
    'central': dict(shop_weights={name: 1 for name in core.SHOPS}, service=0.8, care=0.65),
    'high_demand': dict(shop_weights={'YARN_STORE': 3, 'ICE_CREAM_SHOP': 3, 'SMOOTHIE_SHOP': 2}, service=0.55, care=0.35),
}
REGIME_ALIASES = {'field': 'low_demand', 'mixed': 'central', 'premium': 'high_demand',
                  'balanced': 'central'}


def _cfg(configuration=None):
    supplied = configuration or {}
    return {k: max(1, int(supplied.get(k, v))) for k, v in RULE_DEFAULTS.items()}


def _zeros():
    return {p: 0.0 for p in core.PRODUCTS}


def _count(value):
    try:
        number = float(value)
        return max(0.0, number) if math.isfinite(number) else 0.0
    except (ValueError, TypeError):
        return 0.0


def _positions(farm):
    return [farm.get('farmer', [0, 0]), *farm.get('hands', [])]


def _tiles(farm):
    return [(x, y, tile) for y, row in enumerate(farm['tiles'])
            for x, tile in enumerate(row) if isinstance(tile, dict)]


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _public_features(farm, step, cfg):
    day = step // cfg['turnsPerDay']
    positions = _positions(farm)
    access = core._shed_access_tiles(len(farm['tiles']))
    held, throughput = _zeros(), _zeros()
    sources, work = {}, 0.0
    animals = 0
    for x, y, tile in _tiles(farm):
        p = None
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; data = core.CROPS[p]
            age = day - int(tile.get('planted_day', day))
            held[p] += _count(tile.get('yield_units', 0)) if age >= data['first_yield_day'] else 0
            lifetime = (data['first_yield_day'] + (data['max_yield'] - 1) * data['interval']
                        if data['ongoing'] else data['max_yield_day'])
            throughput[p] += data['max_yield'] / max(1, lifetime + 1)
            work += 2.0
        elif tile.get('animal') in core.ANIMALS:
            data = core.ANIMALS[tile['animal']]; p = data['product']
            held[p] += _count(tile.get('yield_units', 0))
            throughput[p] += (1 + data['interval']) / data['interval']
            throughput['FERTILIZER'] += 1
            animals += 1; work += 5.5
        if p:
            sources[(x, y)] = p
    worker_capacity = len(positions) * cfg['turnsPerDay'] * 0.7
    service = min(1.0, worker_capacity / max(1.0, work))
    nearby = sum(min((_distance(pos, target) for target in sources), default=999) <= 1
                 for pos in positions)
    # Positions affect delivery readiness, never provide proof of carried stock.
    near_shed = sum(tuple(pos) in access for pos in positions)
    return dict(held=held, throughput=throughput, animals=animals, service=service,
                near_sources=nearby, near_shed=near_shed, sources=sources,
                workers=len(positions))


def _town_consumption(observation, cfg):
    step = int(observation['step'])
    result = _zeros()
    if step % cfg['townShopSellInterval'] == 0:
        for shop in observation['town'].get('unlocked_shops', []):
            products = core.SHOPS.get(shop, ())
            for p in products:
                result[p] += 2 if len(products) == 1 else 1
    if step % cfg['townCenterSellInterval'] == 0:
        for p in core.TOWN_CENTER_PRODUCTS:
            result[p] += 1
    return result


def _own_worker_projection(previous, action, cfg):
    farm = copy.deepcopy(previous['farms'][int(previous['player'])])
    private = copy.deepcopy(previous['private'])
    units = [action.get('farmer', ['PASS']), *action.get('hands', [])]
    demand = {}
    for command in units:
        if isinstance(command, list) and len(command) >= 2 and command[0] == 'PLANT':
            demand[command[1]] = demand.get(command[1], 0) + 1
    blocked = {p for p, n in demand.items() if n > private.get('seeds', {}).get(p, 0)}
    for i, command in enumerate(units):
        if isinstance(command, list) and len(command) >= 2 and command[0] == 'PLANT' and command[1] in blocked:
            command = ['PASS']
        core._apply_unit_action(farm, private, i, command, len(farm['tiles']),
                                int(previous['step']) // cfg['turnsPerDay'],
                                cfg['turnsPerDay'], cfg['shedCapacity'])
    return private


def _total(private, product):
    return _count(private.get('shed', {}).get(product, 0)) + sum(
        _count(inv.get(product, 0)) for inv in private.get('inventories', []))


def _own_market_intervals(previous, current, cfg, action, consumption):
    """Contribution to public inventory, including unknown $1-floor attribution."""
    capacity = cfg['shedCapacity']; orders = cfg['maxMarketOrdersPerTurn']
    maximum = float(capacity * orders)
    if action is None:
        return {p: (-maximum, maximum) if p in ('WHEAT', 'FERTILIZER') else (0., maximum)
                for p in core.PRODUCTS}, False
    sold, bought = _zeros(), _zeros()
    for order in action.get('market', [])[:orders]:
        if not isinstance(order, list) or len(order) < 3 or order[1] not in sold:
            continue
        quantity = min(capacity, _count(order[2]))
        if order[0] == 'SELL':
            sold[order[1]] += quantity
        elif order[0] == 'BUY_PRODUCT' and order[1] in ('WHEAT', 'FERTILIZER'):
            bought[order[1]] += quantity
    before = _own_worker_projection(previous, action, cfg)
    boundary = (int(previous['step']) + 1) % cfg['turnsPerDay'] == 0
    params = core._resolve_market_params(previous['market'].get('params'))
    result = {}
    censored = False
    for p in core.PRODUCTS:
        delta = _total(before, p) - _total(current['private'], p)
        discarded = (sum(_count(inv.get(p, 0)) for inv in before.get('inventories', []))
                     if boundary else 0.0)
        # Non-shed product change is native-known worker action or midnight loss.
        lo = max(-bought[p], delta - discarded)
        hi = min(sold[p], delta)
        if lo > hi + 1e-8:
            # Invalid/out-of-order snapshots: preserve only action quantity limits.
            lo, hi = -bought[p], sold[p]
        start = float(previous['market']['inventory'][p])
        end = float(current['market']['inventory'][p]) + consumption[p]
        # Non-purchasable products are monotone within the market phase.
        # Purchasable products may first peak and then fall, so include all buys.
        peak_bound = max(start, end) + (maximum + bought[p] if p in ('WHEAT', 'FERTILIZER') else 0)
        floor_possible = core.market_price(p, peak_bound, params) <= core.PRICE_FLOOR
        if floor_possible and sold[p] > 0:
            lo = max(-bought[p], lo - sold[p])
            censored = True
        result[p] = (float(lo), float(hi))
    return result, censored


def _harvest_evidence(previous, current, cfg):
    seat = 1 - int(previous['player']); before = previous['farms'][seat]
    after = current['farms'][seat]
    positions = [tuple(p) for p in _positions(before)]
    possible = _zeros(); certain = _zeros(); by_worker = {}
    step = int(previous['step']); day = step // cfg['turnsPerDay']
    boundary = (step + 1) % cfg['turnsPerDay'] == 0
    for x, y, tile in _tiles(before):
        if (x, y) not in positions or _count(tile.get('yield_units', 0)) <= 0:
            continue
        now = after['tiles'][y][x]
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; rule = core.CROPS[p]
            if day - int(tile.get('planted_day', day)) < rule['first_yield_day']:
                continue
            decay = int(tile.get('max_lifespan_step', -1))
            decay = 1 if decay >= 0 and step >= decay and (step - decay) % 2 == 0 else 0
            remaining = _count(now.get('yield_units', 0)) if isinstance(now, dict) else 0
            if remaining >= _count(tile['yield_units']) - decay and isinstance(now, dict) and now.get('crop') == p:
                continue
        elif tile.get('animal') in core.ANIMALS:
            p = core.ANIMALS[tile['animal']]['product']
            if not isinstance(now, dict) or now.get('animal') != tile['animal'] or now.get('placed_day') != tile.get('placed_day'):
                continue
            if _count(now.get('yield_units', 0)) >= _count(tile['yield_units']):
                continue
            if not boundary:
                certain[p] += _count(tile['yield_units'])
        else:
            continue
        quantity = _count(tile['yield_units'])
        possible[p] += quantity
        indexes = [i for i, pos in enumerate(positions) if pos == (x, y)]
        if len(indexes) == 1 and not boundary:
            by_worker[indexes[0]] = {p: quantity * (1.0 if p not in core.CROPS else 0.5)}
    return dict(possible=possible, certain=certain, by_worker=by_worker)


class SupplyBelief:
    """Episode-local finite evidence window; caller owns and resets this object.

    observe() accepts only public farms/market/town, own private state and own
    previous action. Call remember_action() after choosing the ACTUAL action.
    Search branches must never update this object. Non-adjacent/repeated steps,
    changed seat or rules discard history. Explicit reset covers host-side game
    switches that are otherwise observationally indistinguishable.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self._last = None
        self._action = None
        self._signature = None
        self._events = []

    def remember_action(self, action):
        self._action = {k: copy.deepcopy(action.get(k, [] if k != 'farmer' else ['PASS']))
                        for k in ('farmer', 'hands', 'market')}

    def observe(self, observation, configuration=None, previous_action=None):
        cfg = _cfg(configuration)
        # Explicit allowed fields prevent metadata from changing beliefs or resets.
        current = {k: copy.deepcopy(observation[k]) for k in ('farms', 'private', 'market', 'town', 'step', 'player')}
        step = int(current['step']); seat = int(current['player'])
        params = core._resolve_market_params(current['market'].get('params'))
        signature = (seat, tuple(sorted(cfg.items())),
                     int((configuration or {}).get('farmHandCostMult', 1)),
                     float((configuration or {}).get('weedSpawnChance', 0.005)),
                     repr(sorted((p, sorted(params[p].items())) for p in core.PRODUCTS)))
        adjacent = (self._last is not None and step == int(self._last['step']) + 1
                    and signature == self._signature and step > 0)
        if not adjacent:
            self._events = []
            self._action = None
        latest = None
        if adjacent:
            action = previous_action if previous_action is not None else self._action
            consumption = _town_consumption(self._last, cfg)
            own, floor = _own_market_intervals(self._last, current, cfg, action, consumption)
            intervals = {}
            cap = cfg['shedCapacity'] * cfg['maxMarketOrdersPerTurn']
            for p in core.PRODUCTS:
                joint = float(current['market']['inventory'][p]) - float(self._last['market']['inventory'][p]) + consumption[p]
                lo, hi = joint - own[p][1], joint - own[p][0]
                minimum = -cap if p in ('WHEAT', 'FERTILIZER') else 0
                lo, hi = max(minimum, lo), min(cap, hi)
                if lo > hi:
                    lo, hi = float(minimum), float(cap)
                intervals[p] = [float(lo), float(hi)]
            latest = dict(step=step, market_net=intervals, own_market=own,
                          town_consumption=consumption, own_floor_censored=floor,
                          harvest=_harvest_evidence(self._last, current, cfg))
            self._events.append(latest)
            self._events = self._events[-min(256, max(1, cfg['turnsPerDay'] * 2)):]
        features = _public_features(current['farms'][1-seat], step, cfg)
        rates = _zeros(); rates_low = _zeros(); rates_high = _zeros()
        n = len(self._events)
        for event in self._events:
            for p, (lo, hi) in event['market_net'].items():
                rates_low[p] += max(0.0, lo)
                rates_high[p] += max(0.0, hi)
        for p in rates:
            factor = cfg['turnsPerDay'] / max(1, n)
            rates_low[p] *= factor; rates_high[p] *= factor
            # Wide ambiguous residuals are not evidence for a giant hidden farm.
            rates[p] = rates_low[p]
        carry_bound = (step + 1) * max(cfg['shedCapacity'], max(d['max_held'] for d in core.ANIMALS.values()),
                                       max(d['max_yield'] for d in core.CROPS.values()))
        summary = dict(step=step, player=seat, adjacent=adjacent, observed_transitions=n,
                       shed_bounds={p: [0, cfg['shedCapacity']] for p in core.PRODUCTS + list(core.ANIMALS)},
                       shed_total_bound=[0, cfg['shedCapacity']],
                       carried_total_per_worker_bound=[0, carry_bound],
                       workers=features['workers'], near_sources=features['near_sources'],
                       near_shed=features['near_shed'], service=features['service'],
                       public_held=features['held'], visible_daily_throughput=features['throughput'],
                       sale_rate=rates, sale_rate_interval={p: [rates_low[p], rates_high[p]] for p in rates},
                       latest=copy.deepcopy(latest),
                       warning='Bounds are feasible envelopes, not calibrated probabilities. Market net excludes censored floor sales; buys can mask sales.')
        self._last = current; self._signature = signature; self._action = None
        return summary


def estimate_private(public_farm, configuration=None, scale=1.0, summary=None):
    """One feasible hidden-stock hypothesis, NOT a hard-state estimate.

    Shed quantity obeys a shared capacity. Worker inventories are separate and
    only assigned small public-source/carry hypotheses. No own inventory is read.
    """
    cfg = _cfg(configuration)
    step = int((summary or {}).get('step', (configuration or {}).get('currentStep', 0)))
    features = _public_features(public_farm, step, cfg)
    scale = max(0., min(3., float(scale)))
    private = core._new_private()
    private['inventories'] = [{} for _ in _positions(public_farm)]
    weights = _zeros()
    history = (summary or {}).get('sale_rate', {})
    for p in weights:
        # A half-day backlog of serviceable public production. Observed disposal
        # reduces hypothesized backlog rather than creating private inventory.
        baseline = features['throughput'][p] * features['service'] * 0.5
        sold = min(baseline, _count(history.get(p, 0)) * 0.25)
        weights[p] = max(0., baseline - sold) + 0.2 * features['held'][p]
    weights['WHEAT'] += features['animals'] * 0.5
    quantities = {p: int(math.ceil(scale * weight)) for p, weight in weights.items() if weight > 0}
    total = sum(quantities.values()); capacity = cfg['shedCapacity']
    if total > capacity:
        raw = {p: q * capacity / total for p, q in quantities.items()}
        quantities = {p: int(q) for p, q in raw.items()}
        for p in sorted(raw, key=lambda p: (-(raw[p] - quantities[p]), p))[:capacity - sum(quantities.values())]:
            quantities[p] += 1
    private['shed'].update(quantities)
    if scale:
        observed = ((summary or {}).get('latest') or {}).get('harvest', {}).get('by_worker', {})
        for index, pos in enumerate(_positions(public_farm)):
            # Publicly located farm work is ambiguous. Treat unobserved wheat
            # custody as a hypothesis only, small enough to avoid free resources.
            p = features['sources'].get(tuple(pos))
            carry = observed.get(index, observed.get(str(index), {}))
            if carry:
                private['inventories'][index] = {item: min(6, int(math.ceil(n * min(1., scale))))
                                                 for item, n in carry.items() if item in core.PRODUCTS}
            elif p and features['animals'] and p in ('EGG', 'MILK', 'WOOL') and scale >= 1:
                private['inventories'][index] = {'WHEAT': 1}
        for crop in core.CROPS:
            private['seeds'][crop] = min(2, int(scale)) if features['throughput'][crop] else 0
    return private


def _events_between(start, stop, interval):
    """Multiples in [start, stop), matching native consumption-before-midnight."""
    if stop <= start:
        return 0
    return (stop - 1) // interval - (start - 1) // interval


def _farm_supply_path(farm, step, days, cfg, service, care):
    """Finite public-asset output under explicit ideal service, no free renewal."""
    path = [_zeros() for _ in range(days + 1)]
    day = step // cfg['turnsPerDay']
    feature = _public_features(farm, step, cfg)
    factor = service * feature['service']
    positions = _positions(farm)
    for x, y, tile in _tiles(farm):
        near = min((_distance(pos, (x, y)) for pos in positions), default=999)
        access = min(_distance((x, y), s) for s in core._shed_access_tiles(len(farm['tiles'])))
        delivery_days = max(1, int(math.ceil((near + 1 + access + 1) / cfg['turnsPerDay'])))
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; rule = core.CROPS[p]
            age = day - int(tile.get('planted_day', day))
            held = _count(tile.get('yield_units', 0))
            if rule['ongoing']:
                if held and delivery_days <= days:
                    path[delivery_days][p] += held * factor
                for count in range(rule['max_yield']):
                    delay = rule['first_yield_day'] + count * rule['interval'] - age
                    if 1 <= delay <= days and delivery_days <= days:
                        path[max(delay, delivery_days)][p] += factor
            else:
                delay = max(delivery_days, rule['max_yield_day'] - age)
                decay_start = int(tile.get('max_lifespan_step', -1))
                if 1 <= delay <= days and not (decay_start >= 0 and step >= decay_start + 2 * max(1, held)):
                    window = (rule['max_yield_day'] + 1) // 2
                    gains = max(0, rule['max_yield_day'] - max(age, window - 1))
                    path[delay][p] += min(rule['max_yield'], held + gains) * factor
        elif tile.get('animal') in core.ANIMALS:
            rule = core.ANIMALS[tile['animal']]; p = rule['product']
            age = day - int(tile.get('placed_day', day))
            held = _count(tile.get('yield_units', 0))
            if held and delivery_days <= days:
                path[delivery_days][p] += held * factor
            pending_care = _count(tile.get('pending_care_bonus', 0))
            for delay in range(1, days + 1):
                future_age = age + delay
                if delivery_days <= days and future_age >= rule['first_yield_day'] and (future_age - rule['first_yield_day']) % rule['interval'] == 0:
                    # Existing public care is known; future care is hypothetical.
                    # Native consumes pending care before adding today's care.
                    path[max(delay, delivery_days)][p] += min(rule['max_held'], 1 + pending_care) * factor
                    pending_care = 0.0
                pending_care += care
                path[delay]['FERTILIZER'] += factor * 0.7
                # Feed procurement is market demand, represented as negative supply.
                path[delay]['WHEAT'] -= factor
    return path


def _market_addition(product, stock, desired, params):
    """Apply the native $1 censor to approximate daily inventory additions.

    Fractional demand/production paths remain approximate, but never fabricate
    accumulating $1-floor supply. A final indivisible sale may cross the floor.
    """
    if desired <= 0:
        return desired
    if core.market_price(product, stock, params) <= core.PRICE_FLOOR:
        return 0.0
    if core.market_price(product, stock + desired, params) > core.PRICE_FLOOR:
        return desired
    low, high = 0.0, desired
    for _ in range(30):
        mid = (low + high) / 2
        if core.market_price(product, stock + mid, params) > core.PRICE_FLOOR:
            low = mid
        else:
            high = mid
    return min(desired, math.floor(low) + 1.0)


def future_market(observation, configuration=None, horizon_days=8, regime='central', summary=None, exclude_player=None):
    """Daily hypothetical stock/price paths including not-yet-revealed shops.

    Central uses the correct uniform marginal recipe distribution, NOT expected
    price over all native trajectories. Stress mixtures are declared assumptions.
    Revealed shops, duplicates, cadence, unlock cap and remaining game are exact.
    The horizon is days, independent of short native action rollout depth.
    """
    cfg = _cfg(configuration)
    regime = REGIME_ALIASES.get(regime, regime)
    if regime not in REGIMES:
        raise ValueError('Unknown future-demand regime: ' + str(regime))
    model = REGIMES[regime]
    step = int(observation['step']); tpd = cfg['turnsPerDay']
    last = cfg['episodeSteps'] - 1
    days = max(0, min(64, int(horizon_days), int(math.ceil(max(0, last - step) / tpd))))
    params = core._resolve_market_params(observation['market'].get('params'))
    stocks = {p: float(observation['market']['inventory'][p]) for p in core.PRODUCTS}
    rows = [dict(prices={p: float(core.market_price(p, stocks[p], params)) for p in core.PRODUCTS},
                 inventory=dict(stocks), demand=_zeros(), supply=_zeros())]
    weights = model['shop_weights']; weight_sum = sum(weights.values())
    new_recipe = _zeros()
    for name, weight in weights.items():
        recipe = core.SHOPS[name]
        for p in recipe:
            new_recipe[p] += weight / weight_sum * (2 if len(recipe) == 1 else 1)
    shops = list(observation['town'].get('unlocked_shops', []))
    recipe = _zeros()
    for name in shops:
        products = core.SHOPS.get(name, ())
        for p in products:
            recipe[p] += 2 if len(products) == 1 else 1
    # Forecast supply from existing assets only. No assumed future purchases,
    # replants, population growth, or invisible rival action programme.
    paths = []
    for player, farm in enumerate(observation['farms']):
        if player != exclude_player:
            paths.append((player, _farm_supply_path(farm, step, days, cfg, model['service'], model['care'])))
    unlock_every = cfg['townShopUnlockInterval'] * tpd
    first_unlock = (step // unlock_every + 1) * unlock_every
    unlocks = list(range(first_unlock, last, unlock_every))[:max(0, core.MAX_SHOP_INSTANCES - len(shops))]
    for delay in range(1, days + 1):
        start, stop = step + (delay - 1) * tpd, min(last, step + delay * tpd)
        demand = _zeros(); supply = _zeros()
        current_ticks = _events_between(start, stop, cfg['townShopSellInterval'])
        center_ticks = _events_between(start, stop, cfg['townCenterSellInterval'])
        future_ticks = sum(_events_between(max(start, unlock), stop, cfg['townShopSellInterval'])
                           for unlock in unlocks if unlock < stop)
        for p in core.PRODUCTS:
            demand[p] = current_ticks * recipe[p] + future_ticks * new_recipe[p]
            if p in core.TOWN_CENTER_PRODUCTS:
                demand[p] += center_ticks
        for player, path in paths:
            for p in supply:
                projected = path[delay][p]
                if summary and player == 1 - int(summary.get('player', observation['player'])) and p != 'WHEAT':
                    # Recent certain disposal supports a finite decaying supply
                    # alternative; use max rather than double-count visible output.
                    recent = min(cfg['shedCapacity'] * 2, _count(summary.get('sale_rate', {}).get(p, 0)))
                    projected = max(projected, recent * math.exp(-delay / 3.0) * model['service'])
                supply[p] += projected
        for p in stocks:
            supply[p] = _market_addition(p, stocks[p], supply[p], params)
            stocks[p] += supply[p] - demand[p]
        rows.append(dict(prices={p: float(core.market_price(p, stocks[p], params)) for p in core.PRODUCTS},
                         inventory=dict(stocks), demand=demand, supply=supply))
    return rows


def future_prices(observation, configuration=None, horizon_days=8, regime='central', summary=None, exclude_player=None):
    """Price-dict view of future_market; index zero is current market."""
    return [row['prices'] for row in future_market(observation, configuration, horizon_days,
                                                  regime, summary, exclude_player)]
