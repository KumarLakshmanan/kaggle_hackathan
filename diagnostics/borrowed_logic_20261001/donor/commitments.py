"""Auditable, observation-only lifecycle commitments and marginal production books.

This is a cash-flow approximation, not a hidden-information simulator. Native
crop/animal refresh determines production; movement, prices and rival service
are declared estimates. Existing assets own their future obligations exactly
once. New purchases are compared with that entire book, including cash timing,
marginal daily Fibonacci wages, land, physical supply and shared-market impact.
"""
import copy
import math
from collections import OrderedDict
from . import native_core as core


def _get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def _context(obs, cfg):
    tpd = max(1, int(_get(cfg, 'turnsPerDay', 24)))
    step = int(_get(obs, 'step', 0))
    end = max(1, int(_get(cfg, 'episodeSteps', 720))) - 2
    seat = int(_get(obs, 'player', 0))
    return obs['farms'][seat], obs.get('private', {}), tpd, step, end


def _distance(a, b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def _row():
    return dict(sales={}, feed=0, seed_cost=0., animal_cost=0., land_cost=0.,
                service=0., travel=0., delivery=0.)


def _flow(item, units, row):
    if units > 0:
        row['sales'][item] = row['sales'].get(item, 0)+units


def _merge(target, source):
    for dest, row in zip(target, source):
        for item, qty in row['sales'].items():
            _flow(item, qty, dest)
        for key in ('feed', 'seed_cost', 'animal_cost', 'land_cost', 'service', 'travel', 'delivery'):
            dest[key] += row[key]
    return target


def _lifecycle_uncached(item, day, last_day, tpd=24, tile=None, target=(0, 0),
                        shed_distance=0, owned=False, repeat=False, final_delivery=True):
    """Daily production ledger with native refresh order and finite crop lifetime.

    Sales normally occur the day after harvest because midnight deposits cargo
    automatically. Final-day output requires explicit harvest and shed delivery.
    `repeat` is an explicit replant programme, with every replacement seed paid.
    Already-held yield and pending animal care are preserved; sunk costs are not
    charged again. No fertilizer is invented for crops.
    """
    count = max(0, last_day-day+1)
    rows = [_row() for _ in range(count)]
    if not count:
        return rows
    is_crop = item in core.CROPS
    state = copy.deepcopy(tile) if tile is not None else (
        core._new_plant(item, day, tpd) if is_crop else core._new_animal(item, day))
    simulated = {'tiles': [[state]], 'farmer': [0, 0], 'hands': []}
    private = {'seeds': {}, 'shed': {}, 'inventories': [{}]}
    if tile is None:
        rows[0]['service'] += 1 if is_crop else 3  # plant, or pickup/build/place
        if not owned:
            rows[0]['seed_cost' if is_crop else 'animal_cost'] += (
                core.CROPS[item]['seed'] if is_crop else core.ANIMALS[item]['cost'])
    # An efficient tile tour shares travel with neighbouring assets. This charge
    # is explicit and deliberately never represented as an exact worker route.
    ingress = min(float(shed_distance), 2.0)
    for offset, current in enumerate(range(day, last_day+1)):
        row = rows[offset]
        state = simulated['tiles'][0][0]
        if not isinstance(state, dict) or ('crop' not in state and 'animal' not in state):
            if not (is_crop and repeat and last_day-current >= core.CROPS[item]['first_yield_day']):
                break
            state = core._new_plant(item, current, tpd)
            simulated['tiles'][0][0] = state
            row['seed_cost'] += core.CROPS[item]['seed']
            row['service'] += 1
        final = current == last_day
        active = False
        if is_crop:
            data = core.CROPS[item]
            age = current-state['planted_day']
            exhausted = data['ongoing'] and age > data['first_yield_day']+(data['max_yield']-1)*data['interval']
            if exhausted and not state.get('yield_units', 0):
                if repeat:
                    simulated['tiles'][0][0] = None
                    row['service'] += 1
                    continue
                break
            window = (data['max_yield_day']+1)//2 <= age <= data['max_yield_day']
            if not state.get('watered_today', False) and (not final or (not data['ongoing'] and window)):
                core._apply_unit_action(simulated, private, 0, ['WATER'], 1, current, tpd)
                row['service'] += 1
                active = True
            mature = age >= data['first_yield_day']
            harvest = mature and state.get('yield_units', 0) > 0 and (
                data['ongoing'] or age >= data['max_yield_day'] or final)
        else:
            data = core.ANIMALS[item]
            if not final:
                if not state.get('fed_today', False):
                    private['inventories'][0]['WHEAT'] = 1
                    core._apply_unit_action(simulated, private, 0, ['FEED'], 1, current, tpd)
                    row['feed'] += 1
                    row['service'] += 1.25  # amortized physical feed pickup
                    active = True
                if not state.get('cared_today', False):
                    core._apply_unit_action(simulated, private, 0, ['CARE'], 1, current, tpd)
                    row['service'] += 1
                    active = True
            harvest = state.get('yield_units', 0) > 0
            if state.get('fertilizer_available', False):
                core._apply_unit_action(simulated, private, 0, ['COLLECT_FERTILIZER'], 1, current, tpd)
                row['service'] += 1
                active = True
        if harvest:
            core._apply_unit_action(simulated, private, 0, ['HARVEST'], 1, current, tpd)
            row['service'] += 1
            active = True
        cargo = private['inventories'][0]
        if cargo:
            sale_offset = min(offset+1, count-1)
            can_sell = not final or final_delivery
            if can_sell:
                for product, units in cargo.items():
                    if product in core.PRODUCTS:
                        _flow(product, units, rows[sale_offset])
                if final:
                    row['delivery'] += shed_distance+1
            cargo.clear()
        if active:
            row['travel'] += ingress
        if not final:
            core._daily_refresh_plants(simulated, current, tpd)
            core._daily_refresh_animals(simulated, current)
    return rows



_LIFECYCLE_CACHE = OrderedDict()
_LIFECYCLE_CACHE_LIMIT = 512
_LIFECYCLE_HITS = 0
_LIFECYCLE_MISSES = 0
_LIFECYCLE_RULE_SNAPSHOT = None
_LIFECYCLE_RULE_KEY = None


def _frozen(value):
    """Preserve complete nested rule/observation content and container types."""
    if isinstance(value, dict):
        return ('dict', tuple((key, _frozen(item)) for key,item in value.items()))
    if isinstance(value, list):
        return ('list', tuple(_frozen(item) for item in value))
    if isinstance(value, tuple):
        return ('tuple', tuple(_frozen(item) for item in value))
    return (type(value).__name__, value)


def clear_caches():
    """Discard pure memoized lifecycle work at an episode boundary."""
    global _LIFECYCLE_HITS, _LIFECYCLE_MISSES, _LIFECYCLE_RULE_SNAPSHOT, _LIFECYCLE_RULE_KEY
    _LIFECYCLE_RULE_SNAPSHOT = _LIFECYCLE_RULE_KEY = None
    _LIFECYCLE_CACHE.clear()
    _LIFECYCLE_HITS = _LIFECYCLE_MISSES = 0


def cache_info():
    return dict(hits=_LIFECYCLE_HITS, misses=_LIFECYCLE_MISSES,
                size=len(_LIFECYCLE_CACHE), maxsize=_LIFECYCLE_CACHE_LIMIT)



def _native_rules_key():
    """C-level deep equality checks all rules; fingerprint only on real change."""
    global _LIFECYCLE_RULE_SNAPSHOT, _LIFECYCLE_RULE_KEY
    rules=(core.CROPS,core.ANIMALS,core.PRODUCTS,core.FARMER_MOVES)
    if _LIFECYCLE_RULE_SNAPSHOT is None or rules != _LIFECYCLE_RULE_SNAPSHOT:
        _LIFECYCLE_RULE_SNAPSHOT=copy.deepcopy(rules)
        # A shared immutable string caches its own hash; it contains the full
        # typed representation, not an abbreviated rule-version identifier.
        _LIFECYCLE_RULE_KEY=repr(_frozen(_LIFECYCLE_RULE_SNAPSHOT))
    return _LIFECYCLE_RULE_KEY

def lifecycle(item, day, last_day, tpd=24, tile=None, target=(0, 0),
              shed_distance=0, owned=False, repeat=False, final_delivery=True,
              use_cache=True):
    """Pure lifecycle memo; every returned row and sales map is caller-owned.

    The full native tile, every argument and all consulted mutable native rule
    tables are part of the key. No market, opponent identity or episode seed is
    stored. Disabling the cache changes work reuse only, never economics.
    """
    global _LIFECYCLE_HITS, _LIFECYCLE_MISSES
    if not use_cache:
        return _lifecycle_uncached(item,day,last_day,tpd,tile,target,shed_distance,
                                   owned,repeat,final_delivery)
    rules = _native_rules_key()
    key = (item,day,last_day,tpd,_frozen(tile),_frozen(target),shed_distance,
           owned,repeat,final_delivery,rules)
    cached = _LIFECYCLE_CACHE.get(key)
    if cached is None:
        _LIFECYCLE_MISSES += 1
        cached = _lifecycle_uncached(item,day,last_day,tpd,tile,target,shed_distance,
                                     owned,repeat,final_delivery)
        _LIFECYCLE_CACHE[key] = cached
        if len(_LIFECYCLE_CACHE) > _LIFECYCLE_CACHE_LIMIT:
            _LIFECYCLE_CACHE.popitem(last=False)
    else:
        _LIFECYCLE_HITS += 1
        _LIFECYCLE_CACHE.move_to_end(key)
    return [dict(row, sales=dict(row['sales'])) for row in cached]

def hire_bill(actions, turns, mult=1, existing_workers=1, already_hired=0):
    """Exact native Fibonacci wage staircase for a declared usable action budget."""
    if turns <= 0:
        return 0., 0
    usable = max(1., float(turns)*0.82)
    needed = max(1, int(math.ceil(max(0., actions)/usable)))
    extra = max(0, needed-max(1, existing_workers))
    # Very large malformed observations must not make an unbounded Fibonacci sum.
    extra = min(32, extra)
    return float(sum(core._hire_cost(already_hired+i, mult) for i in range(extra))), extra


def _market_frames(obs, cfg, days, prices, regime, summary=None):
    try:
        from . import beliefs
        frames = beliefs.future_market(obs, cfg, days, regime=regime,
                                       exclude_player=int(obs.get('player', 0)), summary=summary)
    except ImportError:
        # Supports standalone module contracts before the optional beliefs layer
        # is installed. There is no swallowed runtime error from that model.
        market = obs.get('market', {})
        params = core._resolve_market_params(market.get('params'))
        frames = [dict(prices={p: market.get('prices', {}).get(p, params[p]['base']) for p in core.PRODUCTS},
                       inventory={p: market.get('inventory', {}).get(p, params[p]['I0']) for p in core.PRODUCTS},
                       supply={}, demand={}) for _ in range(days+1)]
    if prices is not None:
        quote_rows = prices if isinstance(prices, (list, tuple)) else [prices]*(days+1)
        frames = [dict(frame, prices=dict(quote_rows[min(i, len(quote_rows)-1)]), external_prices=True)
                  for i, frame in enumerate(frames)]
    return frames


def _quotes(item, stock, quantity, params, buy=False):
    """Exact self-impact quotes, including the native $1 sale-stock exception."""
    total = 0.
    for _ in range(max(0, int(quantity))):
        quote = core.market_price(item, stock-1 if buy else stock, params)
        total += quote
        if buy:
            stock -= 1
        elif quote > 1:
            stock += 1
    return total, stock


def _value(rows, frames, obs, cfg, feed_owned=0):
    farm, private, tpd, step, end = _context(obs, cfg)
    params = core._resolve_market_params(obs.get('market', {}).get('params'))
    stock_shift = {p: 0. for p in core.PRODUCTS}
    cumulative = 0.
    minimum = 0.
    total_sales = total_cost = rival_effect = 0.
    audit = []
    for offset, source in enumerate(rows):
        row = dict(source, sales=dict(source['sales']))
        frame = frames[min(offset, len(frames)-1)]
        receipts = 0.
        feed_units = max(0, int(row['feed']))
        credit = min(feed_owned, feed_units)
        feed_owned -= credit
        feed_units -= credit
        base = float(frame['inventory'].get('WHEAT', params['WHEAT']['I0']))
        before = base+stock_shift['WHEAT']
        feed_cost, after = _quotes('WHEAT', before, feed_units, params, buy=True)
        if frame.get('external_prices'):
            feed_cost = feed_units*frame['prices'].get('WHEAT', params['WHEAT']['base'])
        stock_shift['WHEAT'] += after-before
        for item, qty in row['sales'].items():
            base = float(frame['inventory'].get(item, params[item]['I0']))
            before = base+stock_shift[item]
            revenue, after = _quotes(item, before, qty, params)
            if frame.get('external_prices'):
                # Preserve marginal self-impact around the caller's scenario quote.
                native_quote = core.market_price(item, base, params)
                revenue += qty*(frame['prices'].get(item, native_quote)-native_quote)
                revenue = max(float(qty), revenue)
            stock_shift[item] += after-before
            receipts += revenue
        rival_delta = 0.
        for item in core.PRODUCTS:
            supply = float(frame.get('supply', {}).get(item, 0.))
            if supply and stock_shift[item]:
                base = float(frame['inventory'].get(item, params[item]['I0']))
                rival_delta += supply*(core.market_price(item, base+stock_shift[item], params)
                                       - core.market_price(item, base, params))
        turns = min(tpd-step%tpd-1, end-step) if offset == 0 else (end%tpd+1 if offset == len(rows)-1 else tpd-1)
        workers = 1+len(farm.get('hands', [])) if offset == 0 else 1
        hired = int(farm.get('hires_today', 0)) if offset == 0 else 0
        wage, extra = hire_bill(row['service']+row['travel']+row['delivery'], turns,
                               int(_get(cfg, 'farmHandCostMult', 1)), workers, hired)
        costs = feed_cost+wage+row['seed_cost']+row['animal_cost']+row['land_cost']
        # Outgoings must be available before same-day production is collected.
        minimum = min(minimum, cumulative-costs)
        cumulative += receipts-costs
        total_sales += receipts
        total_cost += costs
        rival_effect += rival_delta
        row.update(day=step//tpd+offset, receipts=receipts, feed_cost=feed_cost,
                   wages=wage, hires=extra, costs=costs, cash_flow=receipts-costs,
                   cumulative=cumulative, rival_cash_delta=rival_delta)
        audit.append(row)
    return dict(net=total_sales-total_cost, revenue=total_sales, costs=total_cost,
                rival_cash_delta=rival_effect, margin=total_sales-total_cost-rival_effect,
                required_cash=max(0., -minimum), daily=audit)



def liquidity_requirement(daily, opening_credit=0.):
    """Move known shed receipts before day-zero costs, never count them twice."""
    cumulative=0.;required=0.
    for offset,row in enumerate(daily):
        required=max(required,row['costs']-cumulative-(opening_credit if offset==0 else 0.))
        cumulative+=row['receipts']-row['costs']
    return max(0.,required)

def build_book(observation, configuration=None, style='balanced', prices=None,
               regime='central', include_candidates=True, summary=None):
    """Return baseline commitments and marginal funded candidate programmes.

    Fields are plain JSON. Each seed/unplaced animal is assigned once to one
    compatible owned slot before new purchases are considered. Unplaced assets
    beyond usable ground receive no fictitious salvage. Land candidates buy the
    whole next quadrant and fund a bounded work queue with its complete costs.
    """
    cfg = configuration or {}
    farm, private, tpd, step, end = _context(observation, cfg)
    day, last = step//tpd, end//tpd
    days = max(0, last-day)
    length = days+1
    if step > end:
        return dict(asset_value=0., baseline={'net': 0., 'margin': 0., 'required_cash': 0., 'daily': []},
                    candidates=[], owned=[], reserve=0., assumptions=[])
    access = core._shed_access_tiles(len(farm['tiles']))
    tiles = [(x,y,t) for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) if t != 'LOCKED']
    distance = lambda p: min(_distance(p,a) for a in access)
    empty = sorted([(x,y,t) for x,y,t in tiles if t is None or (isinstance(t,dict) and 'animal' not in t and 'crop' not in t)],
                   key=lambda v:(distance(v[:2]),v[1],v[0]))
    rows = [_row() for _ in range(length)]
    def queued_lifecycle(item, target, ground=None, owned_asset=False, repeat=False, force_delay=0):
        crop=item in core.CROPS
        workers=[farm['farmer'],*farm.get('hands',[])]
        approach=min(_distance(p,target) for p in workers)
        actions=2 if crop else 4  # plant/water or pickup/build/place/feed
        if not crop and isinstance(ground,dict) and ground.get('kind')==core.ANIMALS[item]['structure']:
            actions-=1
        available=min(tpd-step%tpd,end-step+1)-(0 if owned_asset else 1)
        delay=max(force_delay,int(approach+actions>available))
        if delay>=length:
            return [_row() for _ in rows]
        result=[_row() for _ in range(delay)]+lifecycle(item,day+delay,last,tpd,target=target,
                        shed_distance=distance(target),owned=owned_asset,repeat=repeat)
        if delay and not owned_asset:
            key='seed_cost' if crop else 'animal_cost'
            first_cost=core.CROPS[item]['seed'] if crop else core.ANIMALS[item]['cost']
            result[delay][key]-=first_cost
            result[0][key]+=first_cost  # bought now, placed at earliest legal day
        return result
    owned = []
    positions = [farm['farmer'], *farm.get('hands', [])]
    for x,y,tile in tiles:
        if not isinstance(tile,dict):
            continue
        item = tile.get('crop',tile.get('animal'))
        if item not in core.CROPS and item not in core.ANIMALS:
            continue
        reachable = any(_distance(p,(x,y))+1+distance((x,y))+1 <= end-step+1 for p in positions)
        ledger = lifecycle(item,day,last,tpd,tile=tile,target=(x,y),shed_distance=distance((x,y)),
                           final_delivery=(day < last or reachable),repeat=item in core.CROPS)
        _merge(rows,ledger)
        owned.append(dict(kind='placed',item=item,target=[x,y]))
    reserved = set()
    stock_items = [(item,int(qty),'seed') for item,qty in private.get('seeds',{}).items() if item in core.CROPS]
    stock_items += [(item,int(private.get('shed',{}).get(item,0)+sum(i.get(item,0) for i in private.get('inventories',[]))),'animal') for item in core.ANIMALS]
    for item,quantity,kind in stock_items:
        for _ in range(min(quantity,len(empty))):
            home = next(((x,y,t) for x,y,t in empty if (x,y) not in reserved and
                         (kind=='seed' or t is None or t.get('kind') in ('WEED',core.ANIMALS[item]['structure']))),None)
            if home is None:
                break
            x,y,tile=home
            reserved.add((x,y))
            ledger=queued_lifecycle(item,(x,y),tile,owned_asset=True,repeat=item in core.CROPS)
            if tile is not None:
                ledger[next((i for i,r in enumerate(ledger) if r['service']),0)]['service'] += 1 if tile.get('kind')=='WEED' or kind=='seed' else -1
            _merge(rows,ledger)
            owned.append(dict(kind=kind,item=item,target=[x,y]))
    # Existing stock has one ownership path: reserved feed or sale, never both.
    feed_need=sum(row['feed'] for row in rows)
    wheat=int(private.get('shed',{}).get('WHEAT',0)+sum(i.get('WHEAT',0) for i in private.get('inventories',[])))
    feed_owned=min(wheat,int(feed_need))
    feed_remaining=feed_owned
    for item,n in private.get('shed',{}).items():
        if item not in core.PRODUCTS:
            continue
        qty=int(n)
        if item=='WHEAT':
            keep=min(feed_remaining,qty);qty-=keep;feed_remaining-=keep
        _flow(item,qty,rows[0])
    positions=[farm['farmer'],*farm.get('hands',[])]
    cap=max(0,int(_get(cfg,'shedCapacity',100))-sum(private.get('shed',{}).values()))
    for idx,inv in enumerate(private.get('inventories',[])):
        dist=distance(positions[idx]) if idx<len(positions) else 999
        midnight=step+(tpd-step%tpd)
        auto=midnight<=end
        deliver=dist+1<=end-step+1
        sale_day=1 if auto else 0
        goods=[]
        for item,n in inv.items():
            if item not in core.PRODUCTS:
                continue
            qty=int(n)
            if item=='WHEAT':
                keep=min(feed_remaining,qty);qty-=keep;feed_remaining-=keep
            if qty>0:
                goods.append((item,qty))
        # Exact midnight inventory ordering is retained when capacity is tight.
        for item,qty in goods:
            if auto:
                qty=min(qty,cap);cap-=qty
            if auto or deliver:
                _flow(item,qty,rows[sale_day])
        if goods and not auto and deliver:
            rows[0]['delivery']+=dist+1
    frames=_market_frames(observation,cfg,days,prices,regime,summary=summary)
    baseline=_value(rows,frames,observation,cfg,feed_owned)
    candidates=[]
    free=[(x,y,t) for x,y,t in empty if (x,y) not in reserved]
    if include_candidates and style!='liquidate' and days>0:
        candidate_items = include_candidates if isinstance(include_candidates, (list, tuple, set)) else [*core.CROPS,*core.ANIMALS]
        for item in candidate_items:
            is_crop=item in core.CROPS
            data=core.CROPS[item] if is_crop else core.ANIMALS[item]
            if days<data['first_yield_day']:
                continue
            homes=[p for p in free if is_crop or p[2] is None or p[2].get('kind') in ('WEED',data['structure'])]
            if not homes:
                continue
            x,y,tile=homes[0]
            ledger=queued_lifecycle(item,(x,y),tile,repeat=is_crop)
            if tile is not None:
                ledger[next((i for i,r in enumerate(ledger) if r['service']),0)]['service']+=1 if is_crop or tile.get('kind')=='WEED' else -1
            combined=_merge([dict(r, sales=dict(r['sales'])) for r in rows],ledger)
            valued=_value(combined,frames,observation,cfg,feed_owned)
            own_net=valued['net']-baseline['net']
            margin=valued['margin']-baseline['margin']
            candidates.append(dict(item=item,kind='crop' if is_crop else 'animal',target=[x,y],quantity=1,
                                   net=own_net,margin=margin,score=min(own_net,margin),
                                   required_cash=valued['required_cash'],upfront=ledger[0]['seed_cost']+ledger[0]['animal_cost'],
                                   daily=valued['daily'],marginal_daily=ledger,
                                   policy={'focus':'crop' if is_crop else 'animal','item':item,'regime':regime}))
        # A crop cohort is valued as one combined marginal programme, never
        # quantity times a single-plot NPV. Every plot owns a distinct free tile;
        # merged cash, nonlinear sale prices and daily wages are recomputed.
        singles=[candidate for candidate in candidates if candidate['kind']=='crop']
        queue_limit=max(1,min(8,(tpd-step%tpd-1)*max(2,len(farm.get('hands',[]))+1)//4))
        pending_count=sum(1 for entry in owned if entry['kind']!='placed')
        available_queue=max(0,queue_limit-pending_count)
        for single in singles:
            item=single['item']
            maximum=min(len(free),available_queue,
                        max(0,int(farm.get('money',0)//max(1,core.CROPS[item]['seed']))))
            quantities=sorted(set(q for q in (2,maximum) if 1<q<=maximum))
            for quantity in quantities:
                ledger=[_row() for _ in rows]
                for x,y,tile in free[:quantity]:
                    part=queued_lifecycle(item,(x,y),tile,repeat=True)
                    if tile is not None:
                        part[next((i for i,r in enumerate(part) if r['service']),0)]['service']+=1
                    _merge(ledger,part)
                valued=_value(_merge([dict(r,sales=dict(r['sales'])) for r in rows],ledger),frames,observation,cfg,feed_owned)
                own_net=valued['net']-baseline['net'];margin=valued['margin']-baseline['margin']
                candidates.append(dict(item=item,kind='crop',target=[list(p[:2]) for p in free[:quantity]],quantity=quantity,
                                       net=own_net,margin=margin,score=min(own_net,margin),required_cash=valued['required_cash'],
                                       upfront=ledger[0]['seed_cost'],daily=valued['daily'],marginal_daily=ledger,
                                       policy={'focus':'crop','item':item,'quantity':quantity,'regime':regime}))
        extras=len(farm.get('unlocked_quadrants',['NW']))-1
        if len(free)<2 and extras<len(core.LAND_PRICES) and days>=3:
            # Charge the entire land transaction once, never amortize an
            # unaffordable quadrant into a fictitious cheap individual tile.
            options=[c for c in candidates if c['kind']=='crop' and c['quantity']==1]
            if not options:
                # Empty current land is not needed to quote the next quadrant.
                for item,data in core.CROPS.items():
                    if days>=data['first_yield_day']:
                        ledger=lifecycle(item,day,last,tpd,shed_distance=2,repeat=True)
                        options.append(dict(item=item,marginal_daily=ledger,score=0))
            for option in options:
                quantity=min(8,(len(farm['tiles'])//2)**2)
                ledger=[_row() for _ in rows]
                for _ in range(quantity):
                    _merge(ledger,option['marginal_daily'])
                ledger[0]['land_cost']=core.LAND_PRICES[extras]
                valued=_value(_merge([dict(r, sales=dict(r['sales'])) for r in rows],ledger),frames,observation,cfg,feed_owned)
                own_net=valued['net']-baseline['net'];margin=valued['margin']-baseline['margin']
                candidates.append(dict(item=option['item'],kind='land',target=None,quantity=quantity,
                                       net=own_net,margin=margin,score=min(own_net,margin),
                                       required_cash=valued['required_cash'],upfront=ledger[0]['land_cost']+ledger[0]['seed_cost'],
                                       daily=valued['daily'],marginal_daily=ledger,
                                       policy={'focus':'crop','item':option['item'],'regime':regime}))
    candidates.sort(key=lambda c:(-c['score'],c['kind'],c['item']))
    # Immediate shed sales fund feed/hiring before those market orders. Credit
    # only unreserved stock: wheat cannot simultaneously be sold and own feed.
    params=core._resolve_market_params(observation.get('market',{}).get('params'))
    inventory=observation.get('market',{}).get('inventory',{})
    immediate=[]
    stock={p:max(0,int(private.get('shed',{}).get(p,0))) for p in core.PRODUCTS}
    for item,qty in stock.items():
        spendable=max(0,qty-(min(qty,feed_owned) if item=='WHEAT' else 0))
        receipts,_=_quotes(item,inventory.get(item,params[item]['I0']),spendable,params)
        immediate.append(receipts)
    slots=max(1,int(_get(cfg,'maxMarketOrdersPerTurn',10)))
    opening_credit=sum(sorted(immediate,reverse=True)[:slots])
    funding_cash=max(0.,farm.get('money',0))
    baseline['required_cash']=liquidity_requirement(baseline['daily'],opening_credit)
    funded=funding_cash+1e-9>=baseline['required_cash']
    # Reject unfunded future production, retaining only observable liquidation.
    # No fractional phantom herd or borrowed feed is introduced. Midnight stock
    # is capacity-limited; terminal cargo must actually reach the shed in time.
    midnight=step+(tpd-step%tpd)<=end
    cargo_room=max(0,int(_get(cfg,'shedCapacity',100))-(0 if midnight or end-step>=1 else sum(stock.values())))
    for idx,inv in enumerate(private.get('inventories',[])):
        reachable=idx<len(positions) and distance(positions[idx])+1<=end-step+1
        if not midnight and not reachable:
            continue
        for item,qty in inv.items():
            if item not in core.PRODUCTS:
                continue
            take=min(max(0,int(qty)),cargo_room);cargo_room-=take
            stock[item]+=take
    liquidation=[]
    for item,qty in stock.items():
        receipts,_=_quotes(item,inventory.get(item,params[item]['I0']),qty,params)
        liquidation.append(receipts)
    # With only the final market phase remaining, its actual order cap applies.
    liquidation_value=sum(sorted(liquidation,reverse=True)[:slots] if step==end else liquidation)
    asset=max(0.,liquidation_value,baseline['net'] if funded else 0.)
    return dict(asset_value=asset,baseline=baseline,candidates=candidates,owned=owned,
                continuation_funded=funded,liquidation_value=liquidation_value,funding_cash=funding_cash,opening_sale_credit=opening_credit,
                reserve=min(max(0.,farm.get('money',0)),baseline['required_cash']),
                feed_owned=feed_owned,free_slots=len(free),
                assumptions=['Native lifecycle and daily care ordering; full finite crop lifespan',
                             'Shared tile tours, 82% usable worker turns, exact Fibonacci wage staircase',
                             'Midnight cargo deposit except explicit final-day delivery; future capacity approximate',
                             'Scenario prices, visible rival supply, no unseen future shop/RNG information'])


def asset_value(observation,configuration=None,prices=None,regime='central',summary=None):
    return build_book(observation,configuration,prices=prices,regime=regime,include_candidates=False,summary=summary)['asset_value']


def market_options(observation,configuration=None,book=None):
    """Expose genuinely different executable families before same-family variants."""
    book=book or build_book(observation,configuration)
    useful=[c for c in book['candidates'] if c['score']>0]
    policies=[]
    for family in ('crop','animal'):
        candidate=next((c for c in useful if c['kind']==family),None)
        if candidate is not None:
            policies.append(candidate['policy'])
    for candidate in useful:
        if candidate['policy'] not in policies:
            policies.append(candidate['policy'])
        if len(policies)>=3:
            break
    policies.append({'focus':'liquidate','item':None,'regime':'central'})
    return policies


def service_hires(observation, configuration=None, prices=None, max_hires=32):
    """Conservative spatial marginal-hire audit, never a mandatory-work bill.

    Existing workers reserve reachable bundles first. A new hand starts at its
    native next-turn spawn and must recover its exact wage from still-unclaimed
    work within the day. Terminal bundles include physical sale delivery and no
    future husbandry. This bounded greedy executable-route estimate can leave
    work undone; more demanded work is not permission to spend unlimited cash.
    """
    cfg=configuration or {}
    farm,private,tpd,step,end=_context(observation,cfg)
    turns=max(0,min(tpd-step%tpd-1,end-step))
    if turns<2:
        return []
    day=step//tpd;days=max(0,end//tpd-day);terminal=days==0
    quotes=prices or observation.get('market',{}).get('prices',{})
    size=len(farm['tiles']);access=core._shed_access_tiles(size)
    nearest=lambda p:min(access,key=lambda a:(_distance(p,a),a))
    tasks=[]
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict):
                continue
            value=0.;work=0;feed=0;sale=False
            item=tile.get('crop',tile.get('animal'))
            if item in core.CROPS:
                data=core.CROPS[item];price=max(1.,quotes.get(item,core.MARKET_PARAMS[item]['base']))
                age=day-tile.get('planted_day',day);held=tile.get('yield_units',0)
                mature=age>=data['first_yield_day']
                if mature and held and (data['ongoing'] or age>=data['max_yield_day'] or terminal):
                    value+=held*price*.8;work+=1;sale=True
                future_dates=(max(0,min(data['max_yield'],1+(age+days-data['first_yield_day'])//max(1,data['interval'])))-
                              max(0,min(data['max_yield'],1+(age-data['first_yield_day'])//max(1,data['interval'])))) if data['ongoing'] else int(age+days>=data['first_yield_day'])
                if not terminal and not tile.get('watered_today',False) and (future_dates or held):
                    survival=min(data['seed']+2*price,(held+max(1,future_dates))*price*.6)
                    value+=survival if tile.get('consecutive_unwatered',0)>=1 else survival/max(2,data['first_yield_day']-age+1)
                    work+=1
            elif item in core.ANIMALS:
                data=core.ANIMALS[item];price=max(1.,quotes.get(data['product'],core.MARKET_PARAMS[data['product']]['base']))
                held=tile.get('yield_units',0)
                if held:
                    value+=held*price*.8;work+=1;sale=True
                if tile.get('fertilizer_available',False):
                    value+=max(1.,quotes.get('FERTILIZER',100))*.8;work+=1;sale=True
                age=day-tile.get('placed_day',day)
                future=any(age+d>=data['first_yield_day'] and (age+d-data['first_yield_day'])%data['interval']==0 for d in range(1,days+1))
                if not terminal and future:
                    if not tile.get('fed_today',False):
                        feed=1;work+=1
                        tomorrow=age+1>=data['first_yield_day'] and (age+1-data['first_yield_day'])%data['interval']==0
                        survival=(min(data['cost'],price*(1+data['interval']))*.6
                                  if tile.get('consecutive_unfed',0)>=1 else
                                  tile.get('pending_care_bonus',0)*price*.8 if tomorrow else 0.)
                        value+=max(0.,survival-quotes.get('WHEAT',25))
                    if not tile.get('cared_today',False):
                        value+=price*.6/max(1,data['interval']);work+=1
            if work and value>0:
                tasks.append(dict(target=(x,y),work=work,value=value,feed=feed,sale=sale))
    # Owned seed/animal stock contributes executable placement tasks, each once.
    free=[(x,y) for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) if t is None]
    free.sort(key=lambda p:(_distance(p,nearest(p)),p))
    for item,qty in private.get('seeds',{}).items():
        if item not in core.CROPS or days<core.CROPS[item]['first_yield_day']:
            continue
        for _ in range(min(int(qty),len(free))):
            target=free.pop(0);data=core.CROPS[item]
            price=quotes.get(item,core.MARKET_PARAMS[item]['base'])
            value=max(0.,data['max_yield']*price*.5-data['seed'])
            tasks.append(dict(target=target,work=2,value=value,feed=0,sale=False))
    for animal,data in core.ANIMALS.items():
        if days<data['first_yield_day']:
            continue
        carriers=[(idx,int(inv.get(animal,0))) for idx,inv in enumerate(private.get('inventories',[])) if inv.get(animal,0)]
        stocks=[(None,int(private.get('shed',{}).get(animal,0))),*carriers]
        for owner,quantity in stocks:
            for _ in range(min(quantity,len(free))):
                target=free.pop(0)
                price=quotes.get(data['product'],core.MARKET_PARAMS[data['product']]['base'])
                value=max(0.,min(data['cost'],price*data['first_yield_day']*.6)-quotes.get('WHEAT',25))
                tasks.append(dict(target=target,work=3 if owner is not None else 4,value=value,
                                  feed=1,sale=False,owner=owner,shed_pickup=owner is None))
    feed_available=int(private.get('shed',{}).get('WHEAT',0))
    pool=list(tasks)
    def route(position,carried,budget,consume,worker_id=None):
        nonlocal feed_available
        plan=[];value=0.;used_feed=0
        while pool:
            choices=[]
            for index,task in enumerate(pool):
                if task.get('owner') is not None and task['owner'] != worker_id:
                    continue
                target=task['target'];cost=_distance(position,target)+task['work']
                need=max(0,task['feed']-carried)
                if need or task.get('shed_pickup'):
                    if need>feed_available-used_feed:
                        continue
                    shed=nearest(position)
                    cost=_distance(position,shed)+1+_distance(shed,target)+task['work']
                if terminal and task['sale']:
                    cost+=_distance(target,nearest(target))+1
                if cost<=budget:
                    choices.append((task['value']/max(1,cost),task['value'],-cost,-index,index,cost,need))
            if not choices:
                break
            _,_,_,_,index,cost,need=max(choices)
            task=pool.pop(index);plan.append(task);budget-=cost;value+=task['value'];used_feed+=need
            carried=max(0,carried-task['feed'])
            position=nearest(task['target']) if terminal and task['sale'] else task['target']
        if consume:
            feed_available-=used_feed
        return value,plan,used_feed
    positions=[farm['farmer'],*farm.get('hands',[])]
    for index,pos in enumerate(positions):
        inv=private.get('inventories',[{}])[index] if index<len(private.get('inventories',[])) else {}
        route(tuple(pos),int(inv.get('WHEAT',0)),turns,True,worker_id=index)
    audit=[];virtual=dict(farm,hands=list(farm.get('hands',[])))
    for i in range(min(32,max(0,int(max_hires)))):
        wage=core._hire_cost(int(farm.get('hires_today',0))+i,int(_get(cfg,'farmHandCostMult',1)))
        spawn=core._spawn_hand(virtual,size)
        before=list(pool)
        value,plan,used_feed=route(tuple(spawn),0,turns,False)
        if not plan or value<=wage:
            pool=before
            break
        feed_available-=used_feed
        audit.append(dict(wage=wage,executable_value=value,targets=[list(t['target']) for t in plan],
                          turns=turns,terminal=terminal))
        virtual['hands'].append(spawn)
    return audit
