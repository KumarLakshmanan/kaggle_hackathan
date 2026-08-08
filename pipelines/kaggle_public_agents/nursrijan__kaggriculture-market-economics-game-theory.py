
import math

def agent(obs):
    player = obs["player"]
    day = obs["day"]
    hour = obs["hour"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    hands = me["hands"]
    tiles = me["tiles"]
    money = me["money"]
    market_obs = obs["market"]
    prices = market_obs["prices"]
    market_orders = []

    CROP_SPECS = {
        "WHEAT": (10, 2, 4, 24),
        "CARROT": (20, 2, 3, 25),
        "TOMATO": (50, 8, None, 19),
        "STRAWBERRY": (100, 10, None, 16),
        "MELON": (80, 10, 12, 16)
    }

    primary_crop = "MELON" if day <= 16 else ("TOMATO" if money > 100 else "CARROT")
    seed_cost = 80 if primary_crop == "MELON" else (50 if primary_crop == "TOMATO" else 20)

    hires_today = me["hires_today"]
    target_hands = 5 if day < 10 else (7 if day < 25 else 3)
    if hires_today < target_hands and money >= 10:
        next_cost = 1 if hires_today < 2 else (2 if hires_today == 2 else (3 if hires_today == 3 else 5))
        if money >= next_cost + 20:
            market_orders.append(["HIRE", 1])

    if day <= 16 and private["seeds"].get("MELON", 0) < 8 and money >= 400:
        market_orders.append(["BUY_SEED", "MELON", 4])
    if private["seeds"].get("WHEAT", 0) < 4 and money >= 40:
        market_orders.append(["BUY_SEED", "WHEAT", 4])
    if private["seeds"].get("CARROT", 0) < 3 and money >= 60:
        market_orders.append(["BUY_SEED", "CARROT", 3])

    unlocked_quads = len(me["unlocked_quadrants"])
    if unlocked_quads == 1 and money >= 1000 and day < 20:
        market_orders.append(["BUY_LAND", 1])
    elif unlocked_quads == 2 and money >= 2000 and day < 18:
        market_orders.append(["BUY_LAND", 1])
    elif unlocked_quads == 3 and money >= 4000 and day < 15:
        market_orders.append(["BUY_LAND", 1])

    shed_items = private.get("shed", {})
    for item, qty in shed_items.items():
        if qty > 0:
            item_price = prices.get(item, 0)
            if day >= 27:
                market_orders.append(["SELL", item, qty])
            elif item == "MELON" and item_price > 120:
                market_orders.append(["SELL", item, min(qty, 6)])
            elif item_price > 1:
                market_orders.append(["SELL", item, min(qty, 10)])

    assigned_targets = set()
    def get_action_for_unit(ux, uy):
        current_tile = tiles[uy][ux]
        if (ux, uy) not in assigned_targets:
            if isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
                return (ux, uy), ["DIG"]
            if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
                crop_age = day - current_tile["planted_day"]
                first_yield = CROP_SPECS.get(current_tile["crop"], (10, 2, 4, 24))[1]
                if crop_age >= first_yield:
                    return (ux, uy), ["HARVEST"]
                if not current_tile.get("watered_today", False):
                    return (ux, uy), ["WATER"]
            if current_tile is None:
                if private["seeds"].get("MELON", 0) > 0 and day <= 16:
                    return (ux, uy), ["PLANT", "MELON"]
                elif private["seeds"].get("CARROT", 0) > 0:
                    return (ux, uy), ["PLANT", "CARROT"]
                elif private["seeds"].get("WHEAT", 0) > 0:
                    return (ux, uy), ["PLANT", "WHEAT"]

        queue = [(ux, uy, [])]
        visited = set([(ux, uy)])
        while queue:
            cx, cy, path = queue.pop(0)
            t_state = tiles[cy][cx]
            if (cx, cy) != (ux, uy) and (cx, cy) not in assigned_targets:
                if t_state is None and (private["seeds"].get("MELON", 0) > 0 or private["seeds"].get("CARROT", 0) > 0 or private["seeds"].get("WHEAT", 0) > 0):
                    return (cx, cy), [path[0]]
                if isinstance(t_state, dict):
                    if t_state.get("kind") == "WEED":
                        return (cx, cy), [path[0]]
                    if t_state.get("kind") == "PLANT":
                        crop_age = day - t_state.get("planted_day", day)
                        first_yield = CROP_SPECS.get(t_state.get("crop"), (10, 2, 4, 24))[1]
                        if crop_age >= first_yield or not t_state.get("watered_today", False):
                            return (cx, cy), [path[0]]

            for nx, ny, d_name in [(cx, cy - 1, "NORTH"), (cx, cy + 1, "SOUTH"), (cx + 1, cy, "EAST"), (cx - 1, cy, "WEST")]:
                if 0 <= nx < 10 and 0 <= ny < 10 and tiles[ny][nx] != "LOCKED" and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [d_name]))
        return None, ["PASS"]

    f_target, f_act = get_action_for_unit(fx, fy)
    if f_target: assigned_targets.add(f_target)

    hands_actions = []
    for h_pos in hands:
        h_target, h_act = get_action_for_unit(h_pos[0], h_pos[1])
        if h_target: assigned_targets.add(h_target)
        hands_actions.append(h_act)

    return {"farmer": f_act, "hands": hands_actions, "market": market_orders}
