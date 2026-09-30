"""Two fixed public-hand opening selectors with explicit physical bridges."""
_BRIDGE_SOURCE_AGENT = agent
_BRIDGE_COMMON = copy.deepcopy(_DATA['opening'][0])
assert _BRIDGE_COMMON['market'][4] == ['BUY_ANIMAL', 'SHEEP', 3]
assert _BRIDGE_COMMON['market'][5] == ['BUY_SEED', 'STRAWBERRY', 1]
_BRIDGE_COMMON['market'][4][2] = 2
_BRIDGE_COMMON['market'][5] = ['SELL', 'STRAWBERRY', 0]
_BRIDGE_SOURCE_ONE = copy.deepcopy(_DATA['opening'][1])
_BRIDGE_SOURCE_ONE['market'] += [['BUY_ANIMAL', 'SHEEP', 1], ['BUY_SEED', 'STRAWBERRY', 1]]
_DATA['opening'][0] = copy.deepcopy(_BRIDGE_COMMON)
_DATA['opening'][1] = copy.deepcopy(_BRIDGE_SOURCE_ONE)
_BRIDGE_PERMUTATION = (4, 1, 2, 3, 5)
_BRIDGE_DONORS = {}
for _bridge_name, _bridge_code in _BRIDGE_DONOR_CODE.items():
    _bridge_namespace = {'__name__': '_bridge_' + _bridge_name}
    exec(_bridge_code, _bridge_namespace)
    for _bridge_route in _bridge_namespace['_DONOR_ROUTES'].values():
        _bridge_original = copy.deepcopy(_bridge_route[:24])
        assert ['BUY_PRODUCT', 'WHEAT', 5] in _bridge_original[0]['market']
        _bridge_route[0] = copy.deepcopy(_BRIDGE_COMMON)
        if _bridge_name == 'shared151':
            _bridge_route[1]['hands'][4] = ['PASS']
            _bridge_route[1]['market'] = [['SELL', 'WHEAT', 1], ['HIRE'], ['BUY_ANIMAL', 'SHEEP', 1],
                                         ['BUY_SEED', 'MELON', 6], ['BUY_SEED', 'WHEAT', 2]]
            assert _bridge_original[8]['hands'][4] == ['DROP']
            for _bridge_turn in range(2, 9):
                _bridge_route[_bridge_turn]['hands'][4] = copy.deepcopy(_bridge_original[_bridge_turn-1]['hands'][4])
        else:
            assert _bridge_name == 'shared150'
            assert _bridge_original[1]['market'] == [['HIRE']]*5 + [['BUY_ANIMAL','COW',2],['BUY_ANIMAL','SHEEP',2]]
            _bridge_route[1]['hands'] = [['PASS'] for _ in range(5)]
            _bridge_route[1]['market'] = [['SELL','STRAWBERRY',0] for _ in range(4)] + [['HIRE']]
            _bridge_route[1]['market'] += [['SELL','STRAWBERRY',0] for _ in range(2)]
            _bridge_route[1]['market'] += [['BUY_SEED','WHEAT',1], ['SELL','WHEAT',1]]
            for _bridge_turn in range(2, 24):
                _bridge_commands = _bridge_original[_bridge_turn]['hands']
                _bridge_mapped = [['PASS'] for _ in range(5)]
                assert len(_bridge_commands) <= 5
                for _bridge_index, _bridge_command in enumerate(_bridge_commands):
                    _bridge_mapped[_BRIDGE_PERMUTATION[_bridge_index]-1] = copy.deepcopy(_bridge_command)
                _bridge_route[_bridge_turn]['hands'] = _bridge_mapped
    _BRIDGE_DONORS[_bridge_name] = _bridge_namespace
del _bridge_name, _bridge_code, _bridge_namespace, _bridge_route, _bridge_original
_BRIDGE_SELECTED = 'source'
_BRIDGE_INITIAL = None
_BRIDGE_STATS = {'bridge_selected':'source', 'bridge_requested':'source', 'bridge_rival_hands':-1,
                 'bridge_common_failed':0, 'bridge_guard_refusals':0, 'bridge_source_guard_failed':0,
                 'bridge_errors':0}


def _bridge_positive(values):
    return {key:int(value) for key,value in values.items() if value}


def _bridge_physical(farm, private):
    return dict(farm={key:copy.deepcopy(value) for key,value in farm.items() if key != 'money'},
                shed=_bridge_positive(private['shed']), seeds=_bridge_positive(private['seeds']),
                inventories=[_bridge_positive(inv) for inv in private['inventories']])


def _bridge_expected(branch, configuration):
    cfg = configuration or {}
    farm, private = copy.deepcopy(_BRIDGE_INITIAL)
    farm['hands'] = []
    for _ in range(4):
        farm['hands'].append(_QUEUE_ENGINE['_spawn_hand'](farm, int(cfg.get('boardSize',10))))
    farm['hires_today'] = 4
    private['inventories'] = [{} for _ in range(5)]
    if branch == 'common':
        private['shed'] = {'WHEAT':6,'COW':2,'SHEEP':2}
        private['seeds'] = {}
    elif branch == 'source':
        farm['hands'][1][1] -= 1
        farm['hands'][2][1] -= 1
        private['inventories'] = [{'COW':1},{'WHEAT':1},{},{},{'WHEAT':3}]
        private['shed'] = {'COW':1,'SHEEP':3}
        private['seeds'] = {'WHEAT':1,'STRAWBERRY':1}
    elif branch == 'shared151':
        farm['hands'].append(_QUEUE_ENGINE['_spawn_hand'](farm, int(cfg.get('boardSize',10))))
        farm['hires_today'] = 5
        private['inventories'] = [{'COW':1},{'SHEEP':1},{'SHEEP':1},{},{'COW':1},{}]
        private['shed'] = {'WHEAT':5,'SHEEP':1}
        private['seeds'] = {'MELON':6,'WHEAT':2}
    else:
        assert branch == 'shared150'
        farm['farmer'][1] -= 1
        farm['hands'].append(_QUEUE_ENGINE['_spawn_hand'](farm, int(cfg.get('boardSize',10))))
        farm['hires_today'] = 5
        private['inventories'] = [{} for _ in range(6)]
        private['shed'] = {'WHEAT':5,'COW':2,'SHEEP':2}
        private['seeds'] = {'WHEAT':1}
    return _bridge_physical(farm, private)


def _bridge_forecast(observation, action, configuration, mirror):
    cfg = configuration or {}; player = int(observation['player'])
    farms = [copy.deepcopy(observation['farms'][player]) for _ in (0,1)]
    farms[1-player]['money'] = observation['farms'][1-player]['money']
    private = [copy.deepcopy(observation['private']) for _ in (0,1)]
    market = copy.deepcopy(observation['market'])
    state = [_QueueBox(action={}, observation=_QueueBox(farms=farms,private=private[i],market=market)) for i in (0,1)]
    for seat in (0,1):
        chosen = copy.deepcopy(action) if seat == player or mirror else {'farmer':['PASS'],'hands':[],'market':[]}
        state[seat].action = chosen
        units = [chosen.get('farmer',['PASS']), *chosen.get('hands',[])]
        demand = {}
        for unit in units:
            if len(unit)>=2 and unit[0]=='PLANT':
                demand[unit[1]] = demand.get(unit[1],0)+1
        blocked = {crop for crop,n in demand.items() if n > private[seat]['seeds'].get(crop,0)}
        for index,unit in enumerate(units):
            if len(unit)>=2 and unit[0]=='PLANT' and unit[1] in blocked:
                unit = ['PASS']
            _PLANT_CORE['_apply_unit_action'](farms[seat],private[seat],index,unit,int(cfg.get('boardSize',10)),0,
                                               int(cfg.get('turnsPerDay',24)),int(cfg.get('shedCapacity',100)))
    _PLANT_CORE['_process_market'](state,_QueueBox(configuration=cfg))
    return farms[player],private[player]


def _bridge_guard(observation, action, configuration, branch):
    if branch != 'source':
        wheat = observation['private']['shed'].get('WHEAT',0) + sum(inv.get('WHEAT',0) for inv in observation['private']['inventories'])
        if wheat != 6:
            return False
    expected = _bridge_expected(branch,configuration)
    for mirror in (False,True):
        farm,private = _bridge_forecast(observation,action,configuration,mirror)
        if farm['money'] < 0 or _bridge_physical(farm,private) != expected:
            return False
    return True


def agent(observation, configuration=None):
    global _BRIDGE_SELECTED, _BRIDGE_INITIAL
    step = int(observation['step']); player = int(observation['player'])
    if step == 0:
        _BRIDGE_INITIAL = (copy.deepcopy(observation['farms'][player]),copy.deepcopy(observation['private']))
        _BRIDGE_SELECTED = 'source'
        _BRIDGE_STATS.update(bridge_selected='source',bridge_requested='source',bridge_rival_hands=-1,
                             bridge_common_failed=0,bridge_guard_refusals=0,bridge_source_guard_failed=0,bridge_errors=0)
        agent.telemetry.clear()
        _BRIDGE_SOURCE_AGENT(observation,configuration)
        for namespace in _BRIDGE_DONORS.values():
            namespace['agent'](observation,configuration)
        result = copy.deepcopy(_BRIDGE_COMMON)
    elif step == 1:
        if _bridge_physical(observation['farms'][player],observation['private']) != _bridge_expected('common',configuration):
            _BRIDGE_STATS['bridge_common_failed'] += 1
        hands = len(observation['farms'][1-player]['hands'])
        branch = 'shared151' if hands>=5 else ('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')
        _BRIDGE_STATS.update(bridge_requested=branch,bridge_rival_hands=hands)
        result = (_BRIDGE_SOURCE_AGENT(observation,configuration) if branch=='source'
                  else _BRIDGE_DONORS[branch]['agent'](observation,configuration))
        if not _bridge_guard(observation,result,configuration,branch):
            if branch != 'source':
                _BRIDGE_STATS['bridge_guard_refusals'] += 1
                branch = 'source'
                result = _BRIDGE_SOURCE_AGENT(observation,configuration)
            if not _bridge_guard(observation,result,configuration,'source'):
                _BRIDGE_STATS['bridge_source_guard_failed'] += 1
        _BRIDGE_SELECTED = branch
        _BRIDGE_STATS['bridge_selected'] = branch
    elif _BRIDGE_SELECTED == 'source':
        result = _BRIDGE_SOURCE_AGENT(observation,configuration)
    else:
        result = _BRIDGE_DONORS[_BRIDGE_SELECTED]['agent'](observation,configuration)
    if _BRIDGE_SELECTED != 'source':
        agent.telemetry.clear()
        agent.telemetry.update(_BRIDGE_DONORS[_BRIDGE_SELECTED]['agent'].telemetry)
    agent.telemetry.update(_BRIDGE_STATS)
    return result


agent.telemetry = {}


def kaggle_adaptive_opening_bridge_entrypoint(observation, configuration=None):
    return agent(observation,configuration)
