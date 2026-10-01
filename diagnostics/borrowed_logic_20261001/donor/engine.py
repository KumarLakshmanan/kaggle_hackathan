"""Observation-only receding-horizon search with explicit imperfect-information models.

All simulated transitions are native rules. Leaf asset values and hidden inventory,
future events and rival decisions are assumptions, not measured final scores.
"""
from __future__ import annotations

import copy
import json
import math
import time
from dataclasses import dataclass, asdict

from . import native_core as core
from . import scheduler
from . import beliefs
from . import commitments
from . import reference_scheduler


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


def clean_config(configuration=None, observation=None):
    """Only rule fields, never episode seed, identity, or arbitrary agent metadata."""
    defaults = dict(episodeSteps=720, boardSize=10, turnsPerDay=24,
                    maxMarketOrdersPerTurn=10, farmHandCostMult=1, shedCapacity=100,
                    townShopSellInterval=4, townCenterSellInterval=24,
                    townShopUnlockInterval=3, weedSpawnChance=0.005)
    cfg = configuration or {}
    for key in defaults:
        if key in cfg:
            defaults[key] = cfg[key]
    if observation:
        defaults['boardSize'] = len(observation['farms'][int(observation['player'])]['tiles'])
    for key in defaults:
        if key != 'weedSpawnChance':
            defaults[key] = int(defaults[key])
    defaults['weedSpawnChance'] = float(defaults['weedSpawnChance'])
    if (defaults['episodeSteps'] < 2 or defaults['boardSize'] < 2 or
            defaults['turnsPerDay'] < 1 or defaults['shedCapacity'] < 1 or
            defaults['maxMarketOrdersPerTurn'] < 1):
        raise ValueError('Invalid rule configuration')
    return defaults


def visible_observation(observation):
    """Enforce the information boundary at entry to every policy and search."""
    keys = ('farms', 'private', 'market', 'town', 'step', 'player')
    result = {key: copy.deepcopy(observation[key]) for key in keys}
    if int(result['player']) not in (0, 1) or len(result['farms']) != 2:
        raise ValueError('Kaggriculture requires two farms and seat 0 or 1')
    result['step'] = int(result['step'])
    if result['step'] < 0:
        raise ValueError('Negative step')
    return result


@dataclass(frozen=True)
class SearchConfig:
    horizon: int = 2
    max_candidates: int = 6
    max_transitions: int = 48
    seconds: float = 0.70
    event_horizon: int = 4
    finalists: int = 2
    cache: bool = True
    risk_weight: float = 0.35

    def __post_init__(self):
        for key in ('horizon','max_candidates','max_transitions','event_horizon','finalists'):
            if type(getattr(self,key)) is not int:
                raise ValueError(key+' must be an integer')
        if not 1 <= self.horizon <= 96:
            raise ValueError('horizon must be in [1, 96]')
        if not 1 <= self.max_candidates <= 64:
            raise ValueError('max_candidates must be in [1, 64]')
        if not 1 <= self.max_transitions <= 20000:
            raise ValueError('max_transitions must be in [1, 20000]')
        if not math.isfinite(self.seconds) or self.seconds < 0:
            raise ValueError('seconds must be finite and nonnegative (0 means node-only)')
        if not 0 <= self.event_horizon <= 96 or not 1 <= self.finalists <= 8:
            raise ValueError('invalid event extension bounds')
        if not 0 <= self.risk_weight <= 1:
            raise ValueError('risk_weight must be in [0, 1]')


# Hypothetical seeds drive only native future events; never evaluator seed input.
# Long-horizon demand regimes matter even when a short rollout crosses no shop.
SCENARIOS = (
    dict(name='low_supply_low_demand', stock_scale=0.25, rival_style='balanced', future_seed=846101, regime='low_demand'),
    dict(name='central_reactive', stock_scale=1.0, rival_style='reference', future_seed=846103, regime='central'),
    dict(name='high_supply_high_demand', stock_scale=1.8, rival_style='growth', future_seed=846107, regime='high_demand'),
)


def clone(value):
    """Copy JSON-like state, preserving insertion order and immutable rule data.

    This does not memoize arbitrary aliases. clone_world explicitly restores the
    authoritative shared public objects used by both native observations.
    """
    if isinstance(value, dict):
        # Foreign mapping subclasses (notably Kaggle Struct) may accept only
        # keyword arguments or maintain stale attribute mirrors. Normalize them
        # to plain JSON dictionaries; retain only our own attribute-aware Box.
        cls = Box if isinstance(value, Box) else dict
        return cls((key, clone(item)) for key, item in value.items())
    if isinstance(value, list):
        return [clone(item) for item in value]
    if isinstance(value, tuple):
        return tuple(clone(item) for item in value)
    return value


def frozen(value):
    """Complete hashable state key; preserve ordered inventories and rule fields."""
    if isinstance(value, dict):
        return tuple((key, frozen(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(frozen(item) for item in value)
    return value


def clone_world(world):
    state, env = world
    public = clone({key: state[0].observation[key] for key in ('farms','market','town','step','day','hour')})
    copied = [Box(status=entry.status, reward=entry.reward, action=clone(entry.action),
                  observation=Box(**public, player=p, private=clone(entry.observation.private)))
              for p, entry in enumerate(state)]
    return copied, Box(configuration=env.configuration, info=dict(env.info), done=env.done, summary=getattr(env,'summary',None))


def guess_private(public_farm, capacity, scale):
    # Backwards-compatible public helper. Full engine uses age/config/history.
    return beliefs.estimate_private(public_farm, {'shedCapacity':capacity}, scale)


def make_world(observation, configuration, scenario, summary=None):
    public = clone({key: observation[key] for key in ('farms', 'market', 'town', 'step')})
    seat = int(observation['player'])
    public['day'], public['hour'] = divmod(public['step'], configuration['turnsPerDay'])
    cfg = dict(configuration, currentStep=public['step'])
    other = beliefs.estimate_private(public['farms'][1-seat], cfg, scenario['stock_scale'], summary)
    state = [Box(status='ACTIVE', reward=0, action={}, observation=Box(**public, player=p,
                 private=clone(observation['private']) if p == seat else other)) for p in (0, 1)]
    return state, Box(configuration=Box(**configuration), info={'seed': scenario['future_seed']}, done=False, summary=summary)


def idle_action(observation):
    seat = int(observation.get('player', 0))
    try:
        count = len(observation['farms'][seat].get('hands', []))
    except (KeyError, IndexError, TypeError):
        count = 0
    return dict(farmer=['PASS'], hands=[['PASS'] for _ in range(count)], market=[])


def unit_fingerprint(farm, private, index):
    """Only state a worker action can mutate, checked against native contracts."""
    pos = core._farmer_position(farm, index)
    if pos is None:
        return None
    tile = farm['tiles'][pos[1]][pos[0]]
    inv = private.get('inventories', [])
    return (tuple(pos), frozen(tile), frozen(private.get('seeds', {})),
            frozen(private.get('shed', {})), frozen(inv[index] if index < len(inv) else {}))


def legalize(observation, action, cfg):
    """Clip worker requests to available units and resources before atomic validation.

    Sequential exact own-worker projection prevents stale shared-tile, seed and
    pickup conflicts. Market quantities remain bounded; execution is modeled by
    the joint transition because the rival may change prices simultaneously.
    """
    seat = int(observation['player'])
    farm = copy.deepcopy(observation['farms'][seat])
    private = copy.deepcopy(observation['private'])
    worker_count = 1 + len(farm.get('hands', []))
    raw = [action.get('farmer', ['PASS'])] + list(action.get('hands', []))[:worker_count-1]
    raw += [['PASS'] for _ in range(worker_count-len(raw))]
    units = []
    for index, command in enumerate(raw):
        if not isinstance(command, list) or not command:
            command = ['PASS']
        else:
            command = copy.deepcopy(command)
        before = unit_fingerprint(farm, private, index)
        try:
            core._apply_unit_action(farm, private, index, command, cfg['boardSize'],
                                    observation['step']//cfg['turnsPerDay'], cfg['turnsPerDay'], cfg['shedCapacity'])
        except (TypeError, ValueError, IndexError, KeyError):
            raise ValueError('Malformed generated worker command') from None
        if unit_fingerprint(farm, private, index) == before:
            command = ['PASS']
        units.append(command)
    market = []
    for order in action.get('market', [])[:cfg['maxMarketOrdersPerTurn']]:
        if not isinstance(order, list) or not order:
            continue
        if order[0] in ('HIRE', 'BUY_LAND'):
            market.append([order[0]])
        elif (len(order) >= 3 and order[0] in ('SELL', 'BUY_SEED', 'BUY_PRODUCT', 'BUY_ANIMAL')
              and isinstance(order[2], (int, float)) and math.isfinite(order[2])):
            item, qty = order[1], max(0, min(200, int(order[2])))
            allowed = (core.PRODUCTS if order[0] == 'SELL' else core.CROPS if order[0] == 'BUY_SEED'
                       else ('WHEAT', 'FERTILIZER') if order[0] == 'BUY_PRODUCT' else core.ANIMALS)
            if item in allowed and qty:
                market.append([order[0], item, qty])
    # Make every emitted order funded against the exact post-worker own state.
    # Concurrent rival trades remain uncertainty, represented in joint rollouts.
    projected_market = copy.deepcopy(observation['market'])
    funded = []
    for order in market:
        op = order[0]
        if op == 'HIRE':
            price = core._hire_cost(farm.get('hires_today', 0), cfg['farmHandCostMult'])
            if farm['money'] >= price:
                core._do_hire(farm, private, cfg['boardSize'], cfg['farmHandCostMult'])
                funded.append(order)
        elif op == 'BUY_LAND':
            extra = len(farm['unlocked_quadrants']) - 1
            if extra < len(core.LAND_PRICES) and farm['money'] >= core.LAND_PRICES[extra]:
                core._do_buy_land(farm, cfg['boardSize'])
                funded.append(order)
        else:
            item, quantity = order[1:]
            filled = 0
            for _ in range(quantity):
                if op == 'BUY_SEED':
                    price = core.CROPS[item]['seed']
                elif op == 'BUY_ANIMAL':
                    price = core.ANIMALS[item]['cost']
                else:
                    stock = projected_market['inventory'][item] - int(op == 'BUY_PRODUCT')
                    price = core.market_price(item, stock, projected_market.get('params'))
                if not core._commit_unit(op, item, price, farm, private, projected_market, cfg['shedCapacity']):
                    break
                filled += 1
            if filled:
                funded.append([op, item, filled])
    return dict(farmer=units[0], hands=units[1:], market=funded)


def schedule_policy(obs, cfg, style='balanced', policy=None):
    if (policy or {}).get('executor') == 'reference':
        action = reference_scheduler.schedule(obs, cfg, style)
        return scheduler.repair_feed_service(obs, cfg, action)
    return scheduler.schedule(obs, cfg, style, policy)


class DecisionCache:
    """Bounded per-decision memo; no cross-game policy or private-state leakage."""
    def __init__(self, enabled=True, maximum=512):
        self.enabled, self.maximum = enabled, maximum
        self.schedules, self.values = {}, {}
        self.hits = self.misses = 0

    def schedule(self, obs, cfg, style, policy=None):
        if not self.enabled:
            return schedule_policy(obs, cfg, style, policy)
        key = (frozen(obs), frozen(cfg), style, frozen(policy))
        if key in self.schedules:
            self.hits += 1
            return clone(self.schedules[key])
        self.misses += 1
        action = schedule_policy(obs, cfg, style, policy)
        if len(self.schedules) < self.maximum:
            self.schedules[key] = clone(action)
        return action


def advance(world, seat, first_action, scenario, policy=None, cache=None):
    state, env = world
    own, rival, cfg = state[seat].observation, state[1-seat].observation, env.configuration
    schedule = cache.schedule if cache is not None else schedule_policy
    state[seat].action = first_action if first_action is not None else schedule(own, cfg, 'balanced', policy)
    rival_policy = {'focus':'diverse', 'item':None, 'regime':scenario.get('regime','central')}
    if scenario['rival_style']=='reference':
        rival_policy['executor']='reference'
    state[1-seat].action = (idle_action(rival) if scenario['rival_style']=='passive' else
                           schedule(rival, cfg, 'balanced' if scenario['rival_style']=='reference' else scenario['rival_style'], rival_policy))
    previous_step = int(own.step)
    core.interpreter(state, env)
    for entry in state:
        entry.observation.step = previous_step + 1
    return world


def inventory_value(observation, cfg):
    """Conservative realizable spot liquidation value, including price impact."""
    private = observation['private']
    total = dict(private.get('shed', {}))
    remaining = cfg['episodeSteps'] - 1 - int(observation['step'])
    for inv in private.get('inventories', []):
        for item, qty in inv.items():
            # Carried goods require transfer or a midnight before the final action.
            if remaining > 1:
                total[item] = total.get(item, 0) + qty
    market = observation['market']
    value = 0.0
    for item in core.PRODUCTS:
        supply = market['inventory'][item]
        for _ in range(min(cfg['shedCapacity']*2, int(total.get(item, 0)))):
            price = core.market_price(item, supply, market.get('params'))
            value += price
            supply += int(price > 1)
    if remaining > 3:
        value += 0.25 * sum(core.CROPS[crop]['seed'] * qty for crop, qty in private.get('seeds', {}).items() if crop in core.CROPS)
        value += 0.2 * sum(core.ANIMALS[item]['cost'] * total.get(item, 0) for item in core.ANIMALS)
    return value


def future_assets(observation, cfg, regime='central', summary=None):
    """Net realizable continuation estimate, charging feed, wages and delivery.

    Capital already paid is sunk; unplaced inputs are credited only through an
    executable future lifecycle. No terminal automatic liquidation is assumed.
    """
    return float(commitments.asset_value(observation, cfg, regime=regime, summary=summary))


def evaluate(world, seat, scenario=None, cache=None):
    state, env = world
    farms = state[0].observation.farms
    cash = float(farms[seat]['money'] - farms[1-seat]['money'])
    if state[seat].status == 'DONE':
        return cash
    regime = (scenario or {}).get('regime','central')
    assets = []
    for p in (seat, 1-seat):
        obs = state[p].observation
        key = (frozen(obs), frozen(env.configuration), regime, frozen(getattr(env,'summary',None)))
        if cache is not None and cache.enabled and key in cache.values:
            value = cache.values[key]; cache.hits += 1
        else:
            value = future_assets(obs, env.configuration, regime, getattr(env,'summary',None))
            if cache is not None and cache.enabled and len(cache.values)<cache.maximum:
                cache.values[key] = value
        assets.append(value)
    return cash + assets[0] - assets[1]


def candidate_programs(observation, cfg, maximum=6, summary=None):
    """Funded production programs plus bounded tactical branches.

    A program carries its economic focus through every simulated future turn.
    Different programs may intentionally share a first action; their exact
    common transition is cached rather than conflated with an identical plan.
    """
    book = commitments.build_book(observation, cfg, summary=summary)
    policies = commitments.market_options(observation, cfg, book)
    result, seen = [], set()
    def add(action, name, policy):
        # Every executor and tactical market variant must preserve the same
        # physically feasible survival commitments before native legalization.
        guarded = scheduler.repair_feed_service(observation, cfg, action)
        normalized = legalize(observation, guarded, cfg)
        key = (frozen(normalized), frozen(policy))
        if key not in seen and len(result)<maximum:
            seen.add(key); result.append((name, normalized, policy))
    # Retain the previous general scheduler as one executable mixed portfolio,
    # not a replay or external fallback. New valuation/scenarios/search compare
    # it on exactly the same footing as the new funded commitment programmes.
    reference_policy={'executor':'reference','focus':'diverse','item':None,'regime':'central'}
    add(reference_scheduler.schedule(observation,cfg,'balanced'),
        'retained_mixed_program',reference_policy)
    for index, policy in enumerate(policies):
        style = 'liquidate' if policy.get('focus')=='liquidate' else 'balanced'
        add(scheduler.schedule(observation,cfg,style,policy),
            'commit_'+str(index)+'_'+str(policy.get('focus'))+'_'+str(policy.get('item')), policy)
    if not result:
        policy={'focus':'diverse','item':None,'regime':'central'}
        add(scheduler.schedule(observation,cfg,'balanced',policy),'balanced',policy)
    base, policy = result[0][1:]
    # Preserve deliberate wait/liquidation alternatives without unbounded tuples.
    liquidation={'focus':'liquidate','item':None,'regime':'central'}
    add(scheduler.schedule(observation,cfg,'liquidate',liquidation),'liquidate',liquidation)
    # Expensive daily hands are optional financial decisions. Keeping a
    # no-hire branch exposes their cash cost to exact joint continuations,
    # particularly when late-day service demand cannot all be profitably met.
    if any(order[0]=='HIRE' for order in base['market']):
        add(dict(base,market=[order for order in base['market'] if order[0]!='HIRE']),
            'defer_new_hires',policy)
    if len(base['market'])>1:
        add(dict(base,market=list(reversed(base['market']))),'reverse_market_program',policy)
    for i, order in enumerate(base['market']):
        if order[0]=='SELL' and order[2]>=2:
            orders=clone(base['market']);orders[i][2]=max(1,order[2]//2)
            add(dict(base,market=orders),'partial_sale_'+order[1],policy)
            break
    return result, book


def candidates(observation, cfg, maximum=6):
    return [(name, action) for name, action, _ in candidate_programs(observation,cfg,maximum)[0]]


def decide(observation, configuration=None, settings=None, belief_summary=None):
    settings = settings or SearchConfig()
    started = time.perf_counter()
    obs = visible_observation(observation)
    cfg = clean_config(configuration, obs)
    obs['day'], obs['hour'] = divmod(obs['step'], cfg['turnsPerDay'])
    if obs['step'] >= cfg['episodeSteps']-1:
        return idle_action(obs),dict(terminal=True,transitions=0,elapsed_seconds=time.perf_counter()-started)
    seat=int(obs['player'])
    roots,book=candidate_programs(obs,cfg,settings.max_candidates,belief_summary)
    chosen=roots[0][1]
    cache=DecisionCache(settings.cache)
    # Search cannot change the emitted action when every generated programme
    # agrees. Avoid paying for indistinguishable root decisions on maintenance
    # turns; this is explicit action-set equivalence, never a strength shortcut.
    if len({frozen(action) for _,action,_ in roots}) == 1:
        return chosen, dict(scope='common_generated_action',settings=asdict(settings),
                            scenarios=[],belief=belief_summary or {},transitions=0,
                            completed_candidates=0,requested_horizon=min(settings.horizon,cfg['episodeSteps']-1-obs['step']),
                            budget_exhausted=False,selected=roots[0][0],candidate_results=[],extensions=[],
                            fallback_unsearched=False,forced_common_action=True,generated_programs=len(roots),
                            cache_hits=0,schedule_evaluations=0,
                            elapsed_seconds=time.perf_counter()-started)
    worlds=[make_world(obs,cfg,s,belief_summary) for s in SCENARIOS]
    initial_scores=[evaluate(w,seat,s,cache) for w,s in zip(worlds,SCENARIOS)]
    horizon=min(settings.horizon,cfg['episodeSteps']-1-obs['step'])
    report=dict(scope='persistent_commitment_programs_equal_scenario_rollouts',settings=asdict(settings),
                scenarios=[dict(s,hidden_stock_assumption=clone(w[0][1-seat].observation.private['shed'])) for s,w in zip(SCENARIOS,worlds)],
                belief=belief_summary or {},transitions=0,completed_candidates=0,requested_horizon=horizon,
                budget_exhausted=False,selected=roots[0][0],candidate_results=[],extensions=[],
                value_warning='Native transitions are exact conditional on hypotheses; lifecycle coin-margin estimates are not guarantees or win probabilities.')
    def expired():
        return settings.seconds and time.perf_counter()-started>=settings.seconds
    def outcome(world,j,depth):
        farms=world[0][0].observation.farms
        return dict(name=SCENARIOS[j]['name'],completed_depth=depth,own_cash=farms[seat]['money'],
                    rival_cash=farms[1-seat]['money'],cash_margin=farms[seat]['money']-farms[1-seat]['money'],
                    heuristic_delta=evaluate(world,seat,SCENARIOS[j],cache)-initial_scores[j],
                    terminal=world[0][seat].status=='DONE')
    def score(outcomes):
        vals=[r['heuristic_delta'] for r in outcomes]
        return (1-settings.risk_weight)*sum(vals)/len(vals)+settings.risk_weight*min(vals)
    finished=[];first_cache={}
    for index,(name,action,policy) in enumerate(roots):
        if report['transitions']+horizon*len(SCENARIOS)>settings.max_transitions or expired():
            report['budget_exhausted']=True;break
        simulated=[];outcomes=[];complete=True
        for j,(initial,scenario) in enumerate(zip(worlds,SCENARIOS)):
            prefix=(j,frozen(action))
            if settings.cache and prefix in first_cache:
                world=clone_world(first_cache[prefix]);first_depth=1;cache.hits+=1
            else:
                world=clone_world(initial);first_depth=0
            for depth in range(first_depth,horizon):
                if expired():complete=False;report['budget_exhausted']=True;break
                advance(world,seat,action if depth==0 else None,scenario,policy,cache)
                report['transitions']+=1
                if depth==0 and settings.cache:first_cache[prefix]=clone_world(world)
            if not complete:break
            simulated.append(world);outcomes.append(outcome(world,j,horizon))
        if not complete:break
        utility=score(outcomes)
        row=dict(name=name,policy=policy,utility=utility,outcomes=outcomes)
        report['candidate_results'].append(row);report['completed_candidates']+=1
        finished.append((utility,index,simulated,row))
    if finished:
        finished.sort(key=lambda r:(r[0],-r[1]),reverse=True)
        _,index,_,_=finished[0];chosen=roots[index][1];report['selected']=roots[index][0]
        # Select finalists only after all shallow scenario sets complete. Deepen
        # them equally through an imminent day boundary, keeping the shallow
        # winner if a complete equal-depth finalist cohort cannot finish.
        event_depth=min(cfg['turnsPerDay']-obs['hour']+1,settings.event_horizon,
                        cfg['episodeSteps']-1-obs['step'])
        finalists=finished[:settings.finalists]
        extra=max(0,event_depth-horizon)
        needed=extra*len(SCENARIOS)*len(finalists)
        if extra and len(finalists)>1 and needed+report['transitions']<=settings.max_transitions and not expired():
            extensions=[];all_complete=True
            for _,index,simulated,row in finalists:
                outcomes=[]
                for j,(previous,scenario) in enumerate(zip(simulated,SCENARIOS)):
                    world=clone_world(previous)
                    for depth in range(horizon,event_depth):
                        if expired():all_complete=False;report['budget_exhausted']=True;break
                        advance(world,seat,None,scenario,roots[index][2],cache);report['transitions']+=1
                    if not all_complete:break
                    outcomes.append(outcome(world,j,event_depth))
                if not all_complete:break
                extensions.append(dict(name=roots[index][0],index=index,utility=score(outcomes),outcomes=outcomes))
            report['extensions_complete']=all_complete
            if all_complete:
                report['extensions']=extensions
                best=max(extensions,key=lambda r:(r['utility'],-r['index']))
                chosen=roots[best['index']][1];report['selected']=best['name']
    report['fallback_unsearched']=not finished
    report['cache_hits']=cache.hits;report['schedule_evaluations']=cache.misses
    report['generated_programs']=len(roots)
    report['commitment_summary']={key:book.get(key) for key in ('owned','reserve','assumptions')}
    report['elapsed_seconds']=time.perf_counter()-started
    return chosen,report


_LAST_REPORT = {}
_STATS = dict(calls=0, errors=0, transitions=0, budget_stops=0, unsearched_fallbacks=0, cache_hits=0, lifecycle_cache_hits=0, lifecycle_cache_misses=0, max_seconds=0.)
_BELIEF = beliefs.SupplyBelief()


def agent(observation, configuration=None):
    """Kaggle entry point; bounded public history resets on episode boundaries; no hidden inputs."""
    global _LAST_REPORT
    started=time.perf_counter()
    if int(observation.get('step',0))==0:
        commitments.clear_caches()
        for key in _STATS:
            _STATS[key]=0
    try:
        obs=visible_observation(observation)
        cfg=clean_config(configuration,obs)
        summary=_BELIEF.observe(obs,cfg)
        action,report=decide(obs,cfg,belief_summary=summary)
        _BELIEF.remember_action(action)
        _LAST_REPORT=report
        _STATS['transitions']+=report['transitions']
        _STATS['cache_hits']+=report.get('cache_hits',0)
        _STATS['budget_stops']+=int(report.get('budget_exhausted',False))
        _STATS['unsearched_fallbacks']+=int(report.get('fallback_unsearched',False))
    except Exception as error:
        _STATS['errors']+=1
        _LAST_REPORT={'error':type(error).__name__+': '+str(error),'fallback':'legal_idle'}
        action=idle_action(observation)
    _STATS['calls']+=1
    lifecycle_info=commitments.cache_info()
    _STATS['lifecycle_cache_hits']=lifecycle_info['hits']
    _STATS['lifecycle_cache_misses']=lifecycle_info['misses']
    _STATS['max_seconds']=max(_STATS['max_seconds'],time.perf_counter()-started)
    agent.telemetry=dict(_STATS)
    return action


agent.telemetry={}
