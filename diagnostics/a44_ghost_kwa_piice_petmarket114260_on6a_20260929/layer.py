# Isolated public Pet Cafe gate for route 113517834.
_A44_PET_MARKET_GATE_PARENT = agent
_A44_PET_MARKET_GATE_LEAF = 'PET_CAFE|M8+|C>S|G0'
_A44_PET_MARKET_GATE_ROUTE = 113517834
_A44_PET_MARKET_GATE_MELON = 12
_A44_PET_MARKET_GATE_WHEAT = 9975
_A44_PET_MARKET_GATE_ACTIVE = False
_A44_PET_MARKET_GATE_STATS = {
    'a44_pet_market_gate_key72': '',
    'a44_pet_market_gate_rival_melon72': -1,
    'a44_pet_market_gate_wheat_stock72': -1,
    'a44_pet_market_gate_active72': False,
    'a44_pet_market_gate_route72': '',
    'a44_pet_market_gate_turns': 0,
    'a44_pet_market_gate_errors': 0,
}

def _a44_pet_market_gate_melon_count(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return sum(
        isinstance(tile, dict) and tile.get('crop') == 'MELON'
        for row in rival.get('tiles', [])
        for tile in row
    )

def _a44_pet_market_gate_reset():
    global _A44_PET_MARKET_GATE_ACTIVE
    _A44_PET_MARKET_GATE_ACTIVE = False
    _A44_PET_MARKET_GATE_STATS.update(
        a44_pet_market_gate_key72='',
        a44_pet_market_gate_rival_melon72=-1,
        a44_pet_market_gate_wheat_stock72=-1,
        a44_pet_market_gate_active72=False,
        a44_pet_market_gate_route72='',
        a44_pet_market_gate_turns=0,
        a44_pet_market_gate_errors=0,
    )

def agent(observation, configuration=None):
    global _A44_PET_MARKET_GATE_ACTIVE
    step = int(observation['step'])
    if step == 0:
        _a44_pet_market_gate_reset()
    if step == 72:
        leaf = _a44_goose4_key(observation)
        rival_melon = _a44_pet_market_gate_melon_count(observation)
        wheat_stock = int(observation['market']['inventory']['WHEAT'])
        active = (leaf == _A44_PET_MARKET_GATE_LEAF
                  and rival_melon == _A44_PET_MARKET_GATE_MELON
                  and wheat_stock == _A44_PET_MARKET_GATE_WHEAT)
        _A44_PET_MARKET_GATE_STATS.update(
            a44_pet_market_gate_key72=leaf,
            a44_pet_market_gate_rival_melon72=rival_melon,
            a44_pet_market_gate_wheat_stock72=wheat_stock,
            a44_pet_market_gate_active72=bool(active),
        )
        if active:
            try:
                _a44_goose4_commit(_A44_PET_MARKET_GATE_LEAF,
                                   _A44_PET_MARKET_GATE_ROUTE)
                _A44_PET_MARKET_GATE_ACTIVE = True
                _A44_PET_MARKET_GATE_STATS[
                    'a44_pet_market_gate_route72'] = str(
                        _A44_PET_MARKET_GATE_ROUTE)
            except Exception:
                _A44_PET_MARKET_GATE_STATS[
                    'a44_pet_market_gate_errors'] += 1

    result = _A44_PET_MARKET_GATE_PARENT(observation, configuration)
    if step >= 72 and _A44_PET_MARKET_GATE_ACTIVE:
        _A44_PET_MARKET_GATE_STATS['a44_pet_market_gate_turns'] += 1
    agent.telemetry.update(getattr(_A44_PET_MARKET_GATE_PARENT,
                                   'telemetry', {}))
    agent.telemetry.update(_A44_PET_MARKET_GATE_STATS)
    return result

agent.telemetry = {}

def kaggle_a44_pet_market_gate_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
