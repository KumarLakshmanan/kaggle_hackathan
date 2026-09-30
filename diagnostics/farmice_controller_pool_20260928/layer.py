"""Replace the active complete Farm/Ice tape while preserving its public trigger."""
_FARMICE_POOL_ROUTE = ROUTE_VALUE
_FARMICE_TAPE = copy.deepcopy(_DATA['routes'][str(_FARMICE_POOL_ROUTE)])
_FARMICE_POOL_PARENT = agent
_FARMICE_POOL_STATS = {'farmice_pool_turns': 0, 'farmice_pool_route': ''}


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        _FARMICE_POOL_STATS.update(farmice_pool_turns=0, farmice_pool_route='')
    result = _FARMICE_POOL_PARENT(observation, configuration)
    if _FARMICE_ACTIVE:
        _FARMICE_POOL_STATS['farmice_pool_turns'] += 1
        _FARMICE_POOL_STATS['farmice_pool_route'] = str(_FARMICE_POOL_ROUTE)
    agent.telemetry.update(_FARMICE_POOL_STATS)
    return result


agent.telemetry = {}


def kaggle_farmice_pool_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
