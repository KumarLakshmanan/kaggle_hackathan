"""Pilot: plan a complete early cow-to-goose bundle from public day-6 shops."""

import copy as _eg_copy

_EG_PARENT = agent
_EG_TARGETS = frozenset(((5, 2), (6, 4)))
_EG_MILK_SHOPS = frozenset(("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
_EG_EGG_SHOPS = frozenset(("BAKERY", "BRUNCH_SPOT"))
_EG_STATE = {}
_EG_REPORT = dict(eg_eligible=0, eg_builds=0, eg_buys=0,
                  eg_pickups=0, eg_pickup_skips=0, eg_places=0, eg_confirmed=0, eg_sale_turns=0,
                  eg_egg_units=0, eg_errors=0)


def _eg_new_state():
    return dict(last=-1, decided=False, eligible=False, planned=set(),
                verified=set(), bought=0, sites=set())


def _eg_select(observation, state):
    if state["decided"] or int(observation["step"]) < 144:
        return
    state["decided"] = True
    shops = set((observation.get("town") or {}).get("unlocked_shops") or [])
    state["eligible"] = (
        bool(shops & _EG_EGG_SHOPS) and not (shops & _EG_MILK_SHOPS)
        and "YARN_STORE" not in shops and _ig_standard(None)
    )
    if state["eligible"]:
        _EG_REPORT["eg_eligible"] += 1


def _eg_verify(observation, state):
    farm = observation["farms"][int(observation["player"])]
    tiles = farm["tiles"]
    state["verified"] = {
        site for site in state["planned"]
        if isinstance(tiles[site[1]][site[0]], dict)
        and tiles[site[1]][site[0]].get("kind") == "COOP"
    }
    state["sites"] = {
        site for site in state["planned"]
        if isinstance(tiles[site[1]][site[0]], dict)
        and tiles[site[1]][site[0]].get("animal") == "GOOSE"
    }
    _EG_REPORT["eg_confirmed"] = max(_EG_REPORT["eg_confirmed"], len(state["sites"]))


def _eg_future_place(seat, actor, step):
    """Whether the inherited route plans a cow placement by this worker today."""
    end = ((step // 24) + 1) * 24
    for t in range(step + 1, end):
        future = _cs_tape(seat, t)
        if actor == 0:
            work = future.get("farmer") or []
        else:
            hands = future.get("hands") or []
            work = hands[actor - 1] if actor - 1 < len(hands) else []
        if len(work) >= 2 and work[:2] == ["PLACE", "COW"]:
            return True
    return False


def _eg_change(observation, action, state):
    step = int(observation["step"])
    seat = int(observation["player"])
    farm = observation["farms"][seat]
    private = observation.get("private") or {}
    tiles = farm["tiles"]
    positions = [farm["farmer"], *(farm["hands"] or [])]
    workers = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    market = action.get("market") or []

    if 144 <= step < 168:
        for i in range(min(len(positions), len(workers))):
            pos = tuple(int(x) for x in positions[i])
            if (pos in _EG_TARGETS and workers[i] == ["BUILD_PASTURE"]
                    and tiles[pos[1]][pos[0]] is None):
                workers[i] = ["BUILD_COOP"]
                state["planned"].add(pos)
                _EG_REPORT["eg_builds"] += 1

    _eg_verify(observation, state)
    if 168 <= step < 192 and state["verified"]:
        budget = len(state["verified"]) - state["bought"]
        for order in market:
            if (budget > 0 and len(order) >= 3 and order[:2] == ["BUY_ANIMAL", "COW"]):
                n = min(budget, max(0, int(order[2])))
                if n == int(order[2]) and n > 0:
                    order[1] = "GOOSE"
                    state["bought"] += n
                    budget -= n
                    _EG_REPORT["eg_buys"] += n

    if state["bought"]:
        shed = private.get("shed") or {}
        stock_goose = int(shed.get("GOOSE", 0))
        stock_cow = int(shed.get("COW", 0))
        inventories = private.get("inventories") or []
        for i in range(min(len(positions), len(workers))):
            work = workers[i]
            pos = tuple(int(x) for x in positions[i])
            inv = inventories[i] if i < len(inventories) else {}
            if (len(work) >= 2 and work[:2] == ["PICKUP", "COW"]
                    and stock_goose > 0):
                if _eg_future_place(seat, i, step):
                    workers[i] = ["PICKUP", "GOOSE"] + list(work[2:])
                    stock_goose -= 1
                    _EG_REPORT["eg_pickups"] += 1
                elif stock_cow == 0:
                    workers[i] = ["PASS"]
                    _EG_REPORT["eg_pickup_skips"] += 1
            elif (len(work) >= 2 and work[:2] == ["PLACE", "COW"]
                  and pos in state["verified"] and int(inv.get("GOOSE", 0)) > 0):
                workers[i] = ["PLACE", "GOOSE"] + list(work[2:])
                _EG_REPORT["eg_places"] += 1

    action["farmer"] = workers[0]
    action["hands"] = workers[1:]
    action["market"] = market
    if state["sites"] and 192 <= step < 719:
        try:
            stock = projected_shed(action, FarmView(observation))
        except Exception:
            stock = dict(private.get("shed") or {})
        eggs = max(0, int(stock.get("EGG", 0)))
        price = int((observation.get("market") or {}).get("prices", {}).get("EGG", 0))
        if eggs > 0 and (price >= 5 or step >= 696):
            hit = next((o for o in market if len(o) >= 3 and o[:2] == ["SELL", "EGG"]), None)
            if hit is not None:
                old = int(hit[2])
                if eggs > old:
                    hit[2] = eggs
                    _EG_REPORT["eg_sale_turns"] += 1
                    _EG_REPORT["eg_egg_units"] += eggs - old
            elif len(market) < 10:
                market.insert(0, ["SELL", "EGG", eggs])
                _EG_REPORT["eg_sale_turns"] += 1
                _EG_REPORT["eg_egg_units"] += eggs
    return action


def agent(observation, configuration=None):
    seat = int(observation["player"])
    step = int(observation["step"])
    state = _EG_STATE.get(seat)
    if state is None or step <= state["last"]:
        state = _EG_STATE[seat] = _eg_new_state()
        if step == 0:
            _EG_REPORT.update(eg_eligible=0, eg_builds=0, eg_buys=0,
                              eg_pickups=0, eg_pickup_skips=0, eg_places=0,
                              eg_confirmed=0, eg_sale_turns=0,
                              eg_egg_units=0, eg_errors=0)
    state["last"] = step
    action = _EG_PARENT(observation, configuration)
    try:
        if not isinstance(action, dict):
            return action
        _eg_select(observation, state)
        if state["eligible"] and _ig_standard(configuration):
            action = _eg_change(observation, _eg_copy.deepcopy(action), state)
    except Exception:
        _EG_REPORT["eg_errors"] += 1
    return action


agent.telemetry = _EG_REPORT
kaggle_submission_agent = agent
