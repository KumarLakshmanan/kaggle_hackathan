"""Bounded state-derived investments covering every native crop and animal."""
from .. import native_core as core
from .scheduler import commitment


def proposals(obs):
    farm = obs['farms'][int(obs['player'])]; day = int(obs['day'])
    free = sum(t is None or (isinstance(t,dict) and t.get('kind') == 'WEED') for row in farm['tiles'] for t in row)
    prices = obs['market']['prices']; remaining = 30-day
    candidates = []
    def add(name, extra):
        slots = sum(extra.values()); need_land = slots > free
        if need_land and len(farm['unlocked_quadrants']) >= 4: return
        if any(day+core.CROPS.get(item,core.ANIMALS.get(item))['first_yield_day']+2 >= 30 for item in extra): return
        plan = commitment(obs,extra,land=need_land)
        # Screening priority only. Complete native coins, not this proxy, decide.
        priority = 0.
        for item,qty in extra.items():
            spec = core.CROPS.get(item,core.ANIMALS.get(item))
            product = spec.get('product',item)
            cycles = max(0., remaining-spec['first_yield_day'])/max(1,spec.get('interval') or spec.get('max_yield_day',1))
            units = spec.get('max_yield',2)
            priority += qty*(cycles*units*prices[product]-spec.get('seed',spec.get('cost',0)))
        candidates.append((priority,name,plan))
    for crop in core.CROPS: add('funded_four_'+crop.lower(),{crop:4})
    for animal in core.ANIMALS:
        add('funded_one_'+animal.lower(),{animal:1})
        add('funded_'+animal.lower()+'_and_wheat',{animal:1,'WHEAT':4})
    candidates.sort(key=lambda r:(-r[0],r[1]))
    return [('maintain_existing',commitment(obs))]+[(name,plan) for _,name,plan in candidates]
