import hashlib as _sale_hashlib

_MODEL_PARENT = agent
_MODEL_HISTORY = []
_MODEL_DEBTS = {}
_MODEL_STATS = {"matched_turns": 0, "advanced_turns": 0, "advanced_units": 0, "debt_units": 0}
_MODEL_ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
_MODEL_SHOPS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
                "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
                "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
                "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}


def _model_position(farm):
    return ",".join(str(int(x) + 10 * int(y)) for x, y in [farm["farmer"], *farm["hands"]])


def _model_tape(obs):
    shops = obs["town"]["unlocked_shops"]
    chosen = _OPT_TABLE.get("|".join(shops[:2]))
    if chosen is None:
        for n in range(1, min(len(shops), 8) + 1):
            current = _DATA["route_map"].get("|".join(shops[:n]))
            if current is not None:
                chosen = current
    return _DATA["routes"].get(str(chosen))


def _model_adjust(obs, action, cfg):
    step = int(obs["step"])
    player = int(obs["player"])
    _MODEL_HISTORY.append(_model_position(obs["farms"][1-player]))
    if len(_MODEL_HISTORY) > 8:
        del _MODEL_HISTORY[0]
    if step < 144:
        return action
    orders = action.get("market", [])
    debt = _MODEL_DEBTS.pop(step, {})
    for order in orders:
        if len(order) < 3 or order[0] != "SELL":
            continue
        item = order[1]
        paid = min(max(0, int(order[2])), debt.get(item, 0))
        if paid:
            order[2] -= paid
            debt[item] -= paid
            _MODEL_STATS["debt_units"] += paid
            if order[2] == 0:
                order[:] = ["NOOP"]
    if len(_MODEL_HISTORY) != 8 or len(set(_MODEL_HISTORY)) < 3:
        return action
    key = _sale_hashlib.sha256((str(step) + ":" + "|".join(_MODEL_HISTORY)).encode()).hexdigest()[:24]
    predicted = _SALE_MODEL.get(key)
    if not predicted:
        return action
    _MODEL_STATS["matched_turns"] += 1
    tape = _model_tape(obs)
    if tape is None:
        return action
    stock = dict(obs["private"]["shed"])
    current_commands = [action.get("farmer", []), *action.get("hands", [])]
    for command in current_commands:
        if len(command) > 1 and command[0] == "PICKUP":
            item = command[1]
            stock[item] = max(0, stock.get(item, 0) - (int(command[2]) if len(command) > 2 else 1))
    # Only pre-existing shed stock is used; same-turn drops are conservative
    # omissions. Avoid sharing quantities with a sale already in this queue.
    for order in orders:
        if len(order) > 1 and order[0] == "SELL":
            stock[order[1]] = 0
    cap = int(cfg.get("maxMarketOrdersPerTurn", 10))
    stop = min(step+24, 718, (step//72 + 1)*72 - 1)
    additions = {}
    for future in range(step+1, stop+1):
        later = tape[future]
        for command in [later.get("farmer", []), *later.get("hands", [])]:
            if len(command) > 1 and command[0] == "PICKUP":
                item = command[1]
                stock[item] = max(0, stock.get(item, 0) - (int(command[2]) if len(command) > 2 else 1))
        for planned in later.get("market", []):
            if len(planned) < 3 or planned[0] != "SELL":
                continue
            item = planned[1]
            if item not in predicted or stock.get(item, 0) <= 0 or obs["market"]["prices"].get(item, 0) <= 1:
                continue
            town = sum(1 for turn in range(step, future) if turn % int(cfg.get("townCenterSellInterval", 24)) == 0)
            shop_ticks = sum(1 for turn in range(step, future) if turn % int(cfg.get("townShopSellInterval", 4)) == 0)
            for shop in obs["town"]["unlocked_shops"]:
                products = _MODEL_SHOPS[shop]
                if item in products:
                    town += shop_ticks * (2 if len(products) == 1 else 1)
            if predicted[item] <= town:
                continue
            if item not in additions and len(orders) + len(additions) >= cap:
                continue
            booked = _MODEL_DEBTS.setdefault(future, {})
            qty = min(max(0, int(planned[2]) - booked.get(item, 0)), stock[item])
            if qty:
                additions[item] = additions.get(item, 0) + qty
                booked[item] = booked.get(item, 0) + qty
                stock[item] -= qty
    if additions:
        action["market"] = [["SELL", item, qty] for item, qty in additions.items()] + orders
        _MODEL_STATS["advanced_turns"] += 1
        _MODEL_STATS["advanced_units"] += sum(additions.values())
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _MODEL_HISTORY.clear()
        _MODEL_DEBTS.clear()
        for key in _MODEL_STATS:
            _MODEL_STATS[key] = 0
    action = _MODEL_PARENT(observation, configuration)
    cfg = configuration or {}
    if int(cfg.get("boardSize", 10)) == 10:
        action = _model_adjust(observation, action, cfg)
    return action


agent.telemetry = _MODEL_STATS


def kaggle_public_movement_sales_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
