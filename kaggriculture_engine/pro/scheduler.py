"""Generate physically executable programs for whole-portfolio commitments.

Workers are assigned against a native shadow in execution order. Purchases and
new hires occur after work, never appear as supplies available earlier that turn.
"""
import copy
import math
from .. import native_core as core


def counts(farm):
    result = {p: 0 for p in list(core.CROPS)+list(core.ANIMALS)}
    for row in farm['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                item = tile.get('crop', tile.get('animal'))
                if item in result: result[item] += 1
    return result


def commitment(obs, extra=None, land=False):
    target = counts(obs['farms'][int(obs['player'])])
    for item, amount in (extra or {}).items(): target[item] += amount
    return {'targets': target, 'land': len(obs['farms'][int(obs['player'])]['unlocked_quadrants'])+int(land)}


def distance(a, b): return abs(a[0]-b[0])+abs(a[1]-b[1])


def move(source, target):
    dx, dy = target[0]-source[0], target[1]-source[1]
    for name, vector in core.FARMER_MOVES.items():
        if (dx > 0 and vector == (1, 0)) or (dx < 0 and vector == (-1, 0)) or (
            dx == 0 and dy > 0 and vector == (0, 1)) or (dx == 0 and dy < 0 and vector == (0, -1)):
            return [name]
    return ['PASS']


def _tasks(farm, private, idx, day, hour, cfg, plan, reserved):
    size = len(farm['tiles']); pos = core._farmer_position(farm, idx)
    pack = core._farmer_inventory(private, idx)
    held = counts(farm); target = plan['targets']; tasks = []
    access = core._shed_access_tiles(size)
    nearest = min(access, key=lambda p: distance(pos, p))
    animals = sum(held[a] for a in core.ANIMALS)
    products = sum(pack.get(p, 0) for p in core.PRODUCTS if p != 'WHEAT')
    if products or sum(pack.values()) > 18:
        tasks.append((105+products, nearest, ['DROP']))
    if animals and pack.get('WHEAT', 0) == 0 and private['shed'].get('WHEAT', 0):
        tasks.append((108+hour, nearest, ['PICKUP', 'WHEAT', min(12, animals)]))
    for animal in core.ANIMALS:
        if target[animal] > held[animal] and not pack.get(animal, 0) and private['shed'].get(animal, 0):
            tasks.append((92, nearest, ['PICKUP', animal, 1]))
    for y, row in enumerate(farm['tiles']):
        for x, tile in enumerate(row):
            p = (x, y)
            if p in reserved: continue
            if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                spec = core.CROPS[tile['crop']]; age = day-tile['planted_day']
                mature = age >= spec['first_yield_day'] and tile.get('yield_units', 0) > 0
                # Nonongoing crops remain until their maximum yield window.
                if mature and (spec['ongoing'] or age >= spec['max_yield_day'] or day >= 29):
                    tasks.append((110+tile['yield_units']*2, p, ['HARVEST']))
                if not tile.get('watered_today'):
                    tasks.append((100+hour+20*tile.get('consecutive_unwatered', 0), p, ['WATER']))
                if pack.get('FERTILIZER', 0) and tile.get('fertilized_until_day', -1) < day:
                    tasks.append((65, p, ['FERTILIZE']))
            elif isinstance(tile, dict) and tile.get('animal'):
                if not tile.get('fed_today') and pack.get('WHEAT', 0):
                    tasks.append((140+hour+35*tile.get('consecutive_unfed', 0), p, ['FEED']))
                if tile.get('yield_units', 0):
                    tasks.append((115+8*tile['yield_units'], p, ['HARVEST']))
                if not tile.get('cared_today') and tile.get('fed_today'):
                    tasks.append((82, p, ['CARE']))
                if tile.get('fertilizer_available'):
                    tasks.append((45, p, ['COLLECT_FERTILIZER']))
            elif isinstance(tile, dict) and tile.get('kind') in ('COOP', 'PASTURE'):
                for animal, spec in core.ANIMALS.items():
                    if spec['structure'] == tile['kind'] and pack.get(animal, 0) and target[animal] > held[animal]:
                        tasks.append((98, p, ['PLACE', animal]))
            elif tile is None:
                for animal, spec in core.ANIMALS.items():
                    if pack.get(animal, 0) and target[animal] > held[animal]:
                        tasks.append((93, p, ['BUILD_'+spec['structure']]))
                for crop, spec in core.CROPS.items():
                    if target[crop] > held[crop] and private['seeds'].get(crop, 0) and day+spec['first_yield_day'] < 30:
                        tasks.append((72, p, ['PLANT', crop]))
            elif isinstance(tile, dict) and tile.get('kind') == 'WEED' and sum(target.values()) > sum(held.values()):
                tasks.append((40, p, ['DIG']))
    return tasks


def action(obs, cfg, plan, sell_mode='immediate'):
    seat = int(obs['player']); farm = copy.deepcopy(obs['farms'][seat]); private = copy.deepcopy(obs['private'])
    day, hour = int(obs['day']), int(obs['hour']); size = len(farm['tiles'])
    units = []; reserved = set()
    for idx in range(len(farm['hands'])+1):
        pos = core._farmer_position(farm, idx)
        tasks = _tasks(farm, private, idx, day, hour, cfg, plan, reserved)
        tasks.sort(key=lambda t: (-(t[0]-5*distance(pos, t[1])), distance(pos, t[1]), t[1], t[2]))
        chosen = ['PASS']
        if tasks:
            _, destination, work = tasks[0]
            chosen = work if tuple(pos) == tuple(destination) else move(pos, destination)
            reserved.add(destination)
        core._apply_unit_action(farm, private, idx, chosen, size, day,
            int(cfg.get('turnsPerDay', 24)), int(cfg.get('shedCapacity', 100)))
        units.append(chosen)
    held = counts(farm); targets = plan['targets']; animals = sum(held[a] for a in core.ANIMALS)
    reserve = min(int(cfg.get('shedCapacity', 100))//2, animals*2)
    orders = []; funding = float(farm['money'])
    for item in core.PRODUCTS:
        qty = private['shed'].get(item, 0)-(reserve if item == 'WHEAT' else 0)
        price = obs['market']['prices'][item]
        spec = obs['market'].get('params', core.MARKET_PARAMS)[item]
        should_sell = sell_mode == 'immediate' or day >= 27 or sum(private['shed'].values()) >= 75 or price >= spec['base']
        if qty > 0 and should_sell:
            orders.append(['SELL', item, qty])
            # Conservative funding estimate; native execution remains authoritative.
            funding += qty*max(1, price//2)
    need_feed = max(0, reserve-private['shed'].get('WHEAT', 0)-sum(i.get('WHEAT', 0) for i in private['inventories']))
    if need_feed and funding > need_feed*obs['market']['prices']['WHEAT']*2:
        orders.append(['BUY_PRODUCT', 'WHEAT', need_feed]); funding -= need_feed*obs['market']['prices']['WHEAT']*2
    for item, count in targets.items():
        spec = core.CROPS.get(item, core.ANIMALS.get(item))
        if day+spec['first_yield_day'] >= 30: continue
        already = private['seeds'].get(item, 0) if item in core.CROPS else (
            private['shed'].get(item, 0)+sum(i.get(item, 0) for i in private['inventories']))
        missing = max(0, count-held[item]-already)
        cost = spec.get('seed', spec.get('cost', 0))
        qty = min(missing, max(0, int((funding-300)//cost)))
        if qty:
            orders.append(['BUY_SEED' if item in core.CROPS else 'BUY_ANIMAL', item, qty]); funding -= qty*cost
    if len(farm['unlocked_quadrants']) < plan['land'] and day < 16:
        cost = [1000, 2000, 4000][len(farm['unlocked_quadrants'])-1]
        if funding > cost+500: orders.append(['BUY_LAND']); funding -= cost
    work = sum(held[c]*2.8 for c in core.CROPS)+sum(held[a]*5 for a in core.ANIMALS)
    desired = max(1, min(10, math.ceil(work/18)))
    if hour <= 2:
        hires = farm.get('hires_today', 0)
        for _ in range(max(0, desired-len(units))):
            cost = core._hire_cost(hires, float(cfg.get('farmHandCostMult', 1)))
            if funding < cost+200: break
            orders.append(['HIRE']); funding -= cost; hires += 1
    orders = orders[:int(cfg.get('maxMarketOrdersPerTurn', 10))]
    return {'farmer': units[0], 'hands': units[1:], 'market': orders}
