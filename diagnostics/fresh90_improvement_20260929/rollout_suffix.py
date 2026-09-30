"""Choose a whole prefix-compatible schedule using legal-state forecasts."""

_F90_ROLLOUT_PARENT = agent
_F90_ORIGINAL_MAP = dict(_DATA['route_map'])
_F90_ROLLOUT_STATS = {}


class _F90State(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


def _f90_route(step, shops):
    chosen = None
    for count in range(1, min(len(shops), 8) + 1):
        if step < 72 * count:
            break
        candidate = _F90_ORIGINAL_MAP.get('|'.join(shops[:count]))
        if candidate is not None:
            chosen = str(candidate)
    return chosen or str(next(iter(_DATA['routes'])))


def _f90_raw(step, shops, route=None):
    return copy.deepcopy(_DATA['routes'][route or _f90_route(step, shops)][min(step, 718)])


def _f90_forecast(obs, cfg, route, scenario_seed, rival_kind):
    player = int(obs['player'])
    public = copy.deepcopy({key: obs[key] for key in ('farms', 'market', 'town', 'day', 'hour', 'step')})
    own = copy.deepcopy(obs['private'])
    rival = copy.deepcopy(own) if rival_kind == 'router' else {'shed': {}, 'seeds': {}, 'inventories': []}
    # Inventories are hidden. A fresh-day forecast starts workers with no carry.
    rival['inventories'] = [{} for _ in range(len(public['farms'][1-player]['hands']) + 1)]
    states = [_F90State(status='ACTIVE', reward=0, action={}, observation=_F90State(
                  **public, player=i, private=own if i == player else rival)) for i in (0, 1)]
    visible_cfg = dict(cfg)
    visible_cfg['seed'] = None
    env = _F90State(configuration=_F90State(**visible_cfg), info={'seed': scenario_seed}, done=False)
    for step in range(144, 719):
        shops = states[0].observation.town['unlocked_shops']
        states[player].action = _f90_raw(step, shops, route)
        states[1-player].action = (_f90_raw(step, shops) if rival_kind == 'router'
                                   else {'farmer': ['PASS'], 'hands': [], 'market': []})
        _PLANT_CORE['interpreter'](states, env)
        for item in states:
            item.observation.step = step + 1
    own_cash, rival_cash = float(states[player].reward), float(states[1-player].reward)
    return own_cash, rival_cash


def _f90_choose(obs, cfg):
    shops = list(obs['town']['unlocked_shops'][:2])
    if len(shops) != 2 or shops == ['FARMERS_MARKET', 'ICE_CREAM_SHOP']:
        return
    pair = '|'.join(shops)
    first = str(_F90_ORIGINAL_MAP[shops[0]])
    prefix = _DATA['opening'][:72] + _DATA['routes'][first][72:144]
    distinct = {}
    for route in sorted(_DATA['routes']):
        tape = _DATA['routes'][route]
        if tape[:144] == prefix:
            signature = json.dumps(tape[144:], sort_keys=True, separators=(',', ':'))
            distinct.setdefault(signature, str(route))
    compatible = list(distinct.values())
    if not compatible or len(compatible) > 24:
        _F90_ROLLOUT_STATS['rollout_ineligible_pool'] = len(compatible)
        return
    scenarios = [(seed, rival) for seed in (610001, 610002) for rival in ('idle', 'router')]
    controls = [_f90_forecast(obs, cfg, None, *scenario) for scenario in scenarios]
    best_key, selected = (1500.0, 3000.0), None
    scores = []
    for route in compatible:
        outcomes = [_f90_forecast(obs, cfg, route, *scenario) for scenario in scenarios]
        gains = [(own - rival) - (base_own - base_rival)
                 for (own, rival), (base_own, base_rival) in zip(outcomes, controls)]
        own_gains = [outcome[0] - control[0] for outcome, control in zip(outcomes, controls)]
        worst, mean = min(gains), sum(gains) / len(gains)
        scores.append({'route': route, 'worst_margin_gain': worst, 'mean_margin_gain': mean,
                       'minimum_own_gain': min(own_gains), 'scenario_gains': gains})
        if worst > 1500 and mean > 3000 and min(own_gains) >= 0 and (worst, mean) > best_key:
            best_key, selected = (worst, mean), route
    _F90_ROLLOUT_STATS.update(rollout_pair=pair, rollout_options=len(compatible),
                              rollout_scores=scores, rollout_control_forecasts=controls,
                              rollout_selected=selected or '', rollout_switched=bool(selected))
    if selected:
        for key in list(_DATA['route_map']):
            if key == pair or key.startswith(pair + '|'):
                _DATA['route_map'][key] = int(selected)
        _DATA['route_map'][pair] = int(selected)


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        _DATA['route_map'].clear()
        _DATA['route_map'].update(_F90_ORIGINAL_MAP)
        _F90_ROLLOUT_STATS.clear()
        _F90_ROLLOUT_STATS.update(rollout_errors=0, rollout_switched=False, rollout_selected='')
    if int(observation['step']) == 144:
        try:
            _f90_choose(observation, configuration or {})
        except Exception:
            _F90_ROLLOUT_STATS['rollout_errors'] += 1
    result = _F90_ROLLOUT_PARENT(observation, configuration)
    agent.telemetry.update(_F90_ROLLOUT_STATS)
    return result


agent.telemetry = {}


def kaggle_fresh90_rollout_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
