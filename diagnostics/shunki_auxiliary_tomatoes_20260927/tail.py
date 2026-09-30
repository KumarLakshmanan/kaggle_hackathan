"""Additional, fully staffed SE tomato field with explicit daytime delivery."""
_AUX_PARENT = agent
_AUX = None
_AUX_PLOTS = (((5,5),(6,5),(7,5),(7,6),(6,6),(5,6)),
              ((5,7),(6,7),(7,7),(7,8),(6,8),(5,8)))
_AUX_STATS = dict(aux_started=0, aux_start_step=-1, aux_reserved_wages=0,
                  aux_planted=0, aux_harvested=0, aux_dropped=0,
                  aux_sales_requested=0, aux_extra_hires=0, aux_completed=0,
                  aux_wait_turns=0, aux_errors=0)


def _aux_fib(index):
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a+b
    return a


def _aux_source(obs):
    if _FARMICE_ACTIVE:
        return _FARMICE_TAPE
    step = int(obs["step"])
    shops = obs["town"]["unlocked_shops"]
    route = None
    for count in range(1, min(len(shops), 8)+1):
        if step < count*72:
            break
        route = _DATA["route_map"].get("|".join(shops[:count]), route)
    if route is None:
        route = next(iter(_DATA["routes"]))
    return _DATA["routes"][str(route)]


def _aux_day_schedule(tape, day):
    hires = []
    for step in range(day*24, min((day+1)*24,719)):
        hires.extend(step%24 for order in tape[step].get("market", []) if order and order[0] == "HIRE")
    return len(hires), max(hires, default=-1), len(tape[day*24+2].get("market", []))


def _aux_confirm(obs):
    if not _AUX or not _AUX.get("pending"):
        return
    farm = obs["farms"][int(obs["player"])]
    for pending in _AUX["pending"]:
        actor, operation, value, x, y = pending
        if operation == "PLANT":
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict) and tile.get("crop") == "TOMATO" and tile.get("planted_day") == _AUX["start_day"]:
                _AUX_STATS["aux_planted"] += 1
            else:
                _AUX_STATS["aux_errors"] += 1
        else:
            inventories = obs["private"]["inventories"]
            if actor >= len(inventories):
                _AUX_STATS["aux_errors"] += 1
                continue
            current = inventories[actor].get("TOMATO", 0)
            if operation == "HARVEST":
                before, expected = value
                delta = current-before
                _AUX_STATS["aux_harvested"] += max(0, delta)
                if delta != expected:
                    _AUX_STATS["aux_errors"] += 1
            elif operation == "DROP":
                if current:
                    _AUX_STATS["aux_errors"] += 1
                else:
                    _AUX_STATS["aux_dropped"] += value
    _AUX["pending"] = []


def _aux_admit(obs, action, cfg):
    global _AUX
    step = int(obs["step"])
    day = step//24
    if step%24 != 2 or not 12 <= day <= 17 or _AUX_STATS["aux_started"]:
        return False
    farm = obs["farms"][int(obs["player"])]
    shops = obs["town"]["unlocked_shops"]
    if (int(cfg.get("boardSize",10)) != 10 or int(cfg.get("turnsPerDay",24)) != 24
            or farm["unlocked_quadrants"] != ["NW","NE","SW"] or len(shops)<4
            or sum(s in ("FARMERS_MARKET","PIZZA_SHOP") for s in shops)<2):
        return False
    tape = _aux_source(obs)
    if any(order and order[0] == "BUY_LAND" for a in tape[step:] for order in a.get("market", [])):
        return False
    days = [_aux_day_schedule(tape,d) for d in range(day,day+12)]
    if any(last > 1 or orders > 8 for n,last,orders in days):
        return False
    base = days[0][0]
    if len(farm["hands"]) != base or farm["hires_today"] != base or len(action.get("market", [])) > 6:
        return False
    mult = int(cfg.get("farmHandCostMult",1))
    wages = sum((_aux_fib(n)+_aux_fib(n+1))*mult for n,_,_ in days)
    stock = _queue_stock(obs, action, cfg)
    orders = action.get("market", [])
    cash = min(_queue_simulate(obs,orders,rival,stock,cfg)[0] for rival in ([],orders))
    if cash < 4600+wages+2000:
        return False
    _AUX = dict(start_day=day, day=day, base=base, hired=True, checked=False,
                failed=False, indices=[0,0], pending=[], finished=False)
    _AUX_STATS.update(aux_started=1,aux_start_step=step,aux_reserved_wages=wages)
    action["market"] = orders + [["BUY_LAND"],["BUY_SEED","TOMATO",12],["HIRE"],["HIRE"]]
    return True


def _aux_command(obs, worker, age):
    farm = obs["farms"][int(obs["player"])]
    actor = _AUX["base"]+worker+1
    pos = farm["hands"][actor-1]
    targets = _AUX_PLOTS[worker]
    index = _AUX["indices"][worker]
    harvest_day = age in (9,11)
    while index < len(targets):
        x,y = targets[index]
        _AUX["indices"][worker] = index
        if pos[0] != x:
            return ["EAST" if pos[0]<x else "WEST"]
        if pos[1] != y:
            return ["SOUTH" if pos[1]<y else "NORTH"]
        tile = farm["tiles"][y][x]
        if tile is None and age == 0:
            _AUX["pending"].append((actor,"PLANT",0,x,y))
            return ["PLANT","TOMATO"]
        if not isinstance(tile,dict) or tile.get("crop") != "TOMATO":
            _AUX_STATS["aux_errors"] += 1
            return ["PASS"]
        if harvest_day and tile["yield_units"] > 0:
            before = obs["private"]["inventories"][actor].get("TOMATO",0)
            _AUX["pending"].append((actor,"HARVEST",(before,tile["yield_units"]),x,y))
            return ["HARVEST"]
        if not harvest_day and not tile["watered_today"]:
            return ["WATER"]
        index += 1
        _AUX["indices"][worker] = index
    if harvest_day and obs["private"]["inventories"][actor].get("TOMATO",0):
        if pos[0] != 5:
            return ["EAST" if pos[0]<5 else "WEST"]
        if pos[1] != 5:
            return ["SOUTH" if pos[1]<5 else "NORTH"]
        return ["DROP"]
    return ["PASS"]


def _aux_apply(obs, action, cfg):
    _aux_confirm(obs)
    step = int(obs["step"])
    day,hour = divmod(step,24)
    if _AUX is None:
        _aux_admit(obs,action,cfg)
        return action
    age = day-_AUX["start_day"]
    if age >= 12:
        if not _AUX["finished"]:
            _AUX["finished"] = True
            _AUX_STATS["aux_completed"] = 1
            if (_AUX_STATS["aux_planted"],_AUX_STATS["aux_harvested"],_AUX_STATS["aux_dropped"]) != (12,48,48):
                _AUX_STATS["aux_errors"] += 1
        return action
    farm = obs["farms"][int(obs["player"])]
    if day != _AUX["day"]:
        _AUX.update(day=day,base=None,hired=False,checked=False,failed=False,indices=[0,0])
    if hour == 2 and not _AUX["hired"]:
        base,last,_ = _aux_day_schedule(_aux_source(obs),day)
        mult = int(cfg.get("farmHandCostMult",1))
        cost = (_aux_fib(base)+_aux_fib(base+1))*mult
        stock = _queue_stock(obs,action,cfg)
        cash = min(_queue_simulate(obs,action.get("market",[]),rival,stock,cfg)[0]
                   for rival in ([],action.get("market",[])))
        if (last>1 or len(farm["hands"])!=base or farm["hires_today"]!=base
                or len(action.get("market",[]))>8 or cash<cost):
            _AUX_STATS["aux_errors"] += 1
            _AUX["failed"] = True
            return action
        _AUX.update(base=base,hired=True)
        action["market"] = action.get("market",[]) + [["HIRE"],["HIRE"]]
        return action
    if hour < 3 or not _AUX["hired"] or _AUX["failed"]:
        return action
    if not _AUX["checked"]:
        _AUX["checked"] = True
        if len(farm["hands"]) != _AUX["base"]+2 or "SE" not in farm["unlocked_quadrants"]:
            _AUX_STATS["aux_errors"] += 1
            _AUX["failed"] = True
            return action
        _AUX_STATS["aux_extra_hires"] += 2
    base = _AUX["base"]
    stock = _queue_stock(obs,action,cfg)
    hands = list(action.get("hands",[]))
    while len(hands)<base+2:
        hands.append(["PASS"])
    dropped = 0
    for worker in (0,1):
        command = _aux_command(obs,worker,age)
        actor = base+worker+1
        cargo = obs["private"]["inventories"][actor].get("TOMATO",0)
        if command[0] == "DROP":
            if sum(stock.values())+cargo>int(cfg.get("shedCapacity",100)) or len(action.get("market",[]))>=10:
                command = ["PASS"]
                _AUX_STATS["aux_wait_turns"] += 1
            else:
                stock["TOMATO"] = stock.get("TOMATO",0)+cargo
                dropped += cargo
                _AUX["pending"].append((actor,"DROP",cargo,5,5))
        if hour == 23 and cargo and command[0] != "DROP":
            _AUX_STATS["aux_errors"] += 1
        hands[base+worker] = command
    action["hands"] = hands
    if dropped:
        action["market"] = action.get("market",[]) + [["SELL","TOMATO",dropped]]
        _AUX_STATS["aux_sales_requested"] += dropped
    return action


def agent(observation, configuration=None):
    global _AUX
    if int(observation["step"]) == 0:
        _AUX = None
        for key in _AUX_STATS:
            _AUX_STATS[key] = -1 if key == "aux_start_step" else 0
    action = _AUX_PARENT(observation,configuration)
    try:
        result = _aux_apply(observation,action,configuration or {})
    except Exception:
        _AUX_STATS["aux_errors"] += 1
        result = action
    agent.telemetry.update(_AUX_STATS)
    return result


agent.telemetry = {}


def kaggle_auxiliary_tomato_entrypoint(observation, configuration=None):
    return agent(observation,configuration)
