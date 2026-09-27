"""Pilot ablation: keep V219's late cohort eligible after early tomato planting."""

_TOMATO_QUAL_PARENT = _v219_qualifies


def _v219_qualifies(obs, native):
    if native.get("route") != 104:
        return _TOMATO_QUAL_PARENT(obs, native)
    farm = obs["farms"][obs["player"]]
    if len(farm["tiles"]) != 10 or set(farm["unlocked_quadrants"]) != {"NW", "NE", "SW"}:
        return False
    if farm["money"] < 12000 or obs["market"]["prices"]["TOMATO"] < CROP_MIN_PRICE:
        return False
    if sum(shop in ("PIZZA_SHOP", "FARMERS_MARKET")
           for shop in obs["town"]["unlocked_shops"]) < 3:
        return False
    if any(farm["tiles"][y][x] != "LOCKED" for y in (5, 6) for x in range(5, 10)):
        return False
    if obs["private"]["seeds"].get("TOMATO", 0) or obs["private"]["shed"].get("TOMATO", 0):
        return False
    for tape in _IMPL.chassis.routes.values():
        for action in tape[432:719]:
            if any(order and order[0] == "BUY_LAND" for order in action.get("market", [])):
                return False
            if any(command == ["PLANT", "TOMATO"]
                   for command in [action.get("farmer"), *(action.get("hands") or [])]):
                return False
    return True
