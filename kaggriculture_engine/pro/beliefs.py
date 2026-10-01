"""Uncertain rival supply inferred only from legal public observations."""
import copy
from .. import native_core as core


def visible_supply(farm, day):
    result = {p: {'held': 0, 'daily_capacity': 0., 'assets': 0} for p in core.PRODUCTS}
    for row in farm['tiles']:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                item = tile['crop']; spec = core.CROPS[item]
                age = day-tile['planted_day']
                held = tile.get('yield_units', 0) if age >= spec['first_yield_day'] else 0
                rate = spec['max_yield']/max(1, spec['interval'] or spec['max_yield_day'])
            elif tile.get('animal') in core.ANIMALS:
                spec = core.ANIMALS[tile['animal']]; item = spec['product']
                held = tile.get('yield_units', 0)
                rate = (2. if tile.get('cared_today') else 1.)/spec['interval']
                result['FERTILIZER']['daily_capacity'] += 1
            else:
                continue
            result[item]['held'] += held
            result[item]['daily_capacity'] += rate
            result[item]['assets'] += 1
    return result


class RivalBelief:
    def __init__(self):
        self.previous = None
        self.flow = {p: 0. for p in core.PRODUCTS}
        self.spread = {p: 4. for p in core.PRODUCTS}
        self.samples = 0

    def update(self, obs, cfg, previous_action=None):
        seat = int(obs['player']); step = int(obs['step'])
        if self.previous is not None and step <= self.previous['step']:
            self.__init__()
        prior = self.previous
        if prior is not None and step == prior['step']+1 and previous_action is not None:
            tpd = int(cfg.get('turnsPerDay', 24))
            # Native order execution may be clipped or affected by rival prices.
            # Midpoint attribution is explicitly uncertain, not an exact trade log.
            own_net = {p: 0. for p in core.PRODUCTS}
            ambiguity = {p: 0. for p in core.PRODUCTS}
            for order in previous_action.get('market', []):
                if len(order) != 3 or order[1] not in own_net:
                    continue
                op, item, qty = order; qty = max(0, int(qty))
                if op == 'SELL':
                    qty = min(qty, prior['private']['shed'].get(item, 0)+sum(
                        inv.get(item, 0) for inv in prior['private']['inventories']))
                    own_net[item] += qty; ambiguity[item] += qty
                elif op == 'BUY_PRODUCT':
                    own_net[item] -= qty; ambiguity[item] += qty
            consumption = {p: 0 for p in core.PRODUCTS}
            if prior['step'] % int(cfg.get('townShopSellInterval', 4)) == 0:
                for shop in prior['town']['unlocked_shops']:
                    products = core.SHOPS.get(shop, [])
                    for p in products:
                        consumption[p] += 2 if len(products) == 1 else 1
            if prior['step'] % int(cfg.get('townCenterSellInterval', tpd)) == 0:
                for p in core.PRODUCTS:
                    if p != 'FERTILIZER': consumption[p] += 1
            for item in core.PRODUCTS:
                raw = obs['market']['inventory'][item]-prior['market']['inventory'][item]
                residual = raw+consumption[item]-own_net[item]
                self.flow[item] = .85*self.flow[item]+.15*residual
                self.spread[item] = .85*self.spread[item]+.15*(abs(residual-self.flow[item])+ambiguity[item])
            self.samples += 1
        supply = visible_supply(obs['farms'][1-seat], int(obs['day']))
        bounds = {}
        for item, value in supply.items():
            high = min(int(cfg.get('shedCapacity', 100)), int(value['held']+3*value['daily_capacity']+
                2*self.spread[item]+max(0, -self.flow[item])*4+4))
            bounds[item] = {'low': 0, 'high': max(0, high)}
        self.previous = copy.deepcopy(obs)
        return {'stock_bounds': bounds, 'visible_supply': supply, 'net_flow_ema': dict(self.flow),
                'residual_uncertainty': dict(self.spread), 'history_samples': self.samples,
                'scope': 'Heuristic public-state belief; rival private stock is unknown.'}
