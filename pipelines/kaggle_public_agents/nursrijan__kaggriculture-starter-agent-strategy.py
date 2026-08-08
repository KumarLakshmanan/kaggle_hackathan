
import math

def agent(obs):
    player = obs["player"]
    day = obs["day"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tiles = me["tiles"]
    money = me["money"]
    market_obs = obs["market"]
    prices = market_obs["prices"]
    
    market_orders = []
    
    # 1. Market Operations
    target_crop = "WHEAT" if day < 8 else ("TOMATO" if money > 80 else "CARROT")
    target_seed_cost = 10 if target_crop == "WHEAT" else (50 if target_crop == "TOMATO" else 20)

    if private["seeds"].get(target_crop, 0) < 3 and money >= target_seed_cost * 3:
        market_orders.append(["BUY_SEED", target_crop, 3])
    if private["seeds"].get("WHEAT", 0) < 2 and money >= 20:
        market_orders.append(["BUY_SEED", "WHEAT", 2])

    for item, qty in private["shed"].items():
        if qty > 0 and (prices.get(item, 0) > 1 or day >= 27):
            market_orders.append(["SELL", item, qty])

    if day > 3 and me["hires_today"] == 0 and money > 500:
        market_orders.append(["HIRE", 1])

    # 2. Farmer Movement & Actions
    current_tile = tiles[fy][fx]
    if isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
        return {"farmer": ["DIG"], "hands": [], "market": market_orders}

    if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
        crop = current_tile["crop"]
        crop_age = day - current_tile["planted_day"]
        if crop in ["WHEAT", "CARROT", "MELON"] and crop_age >= 2:
            return {"farmer": ["HARVEST"], "hands": [], "market": market_orders}
        elif crop in ["TOMATO", "STRAWBERRY"] and crop_age >= 8:
            return {"farmer": ["HARVEST"], "hands": [], "market": market_orders}
        if not current_tile.get("watered_today", False):
            return {"farmer": ["WATER"], "hands": [], "market": market_orders}

    if current_tile is None:
        if private["seeds"].get(target_crop, 0) > 0:
            return {"farmer": ["PLANT", target_crop], "hands": [], "market": market_orders}
        elif private["seeds"].get("WHEAT", 0) > 0:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market_orders}

    # BFS Pathfinding
    queue = [(fx, fy, [])]
    visited = set([(fx, fy)])
    while queue:
        cx, cy, path = queue.pop(0)
        tile_state = tiles[cy][cx]
        if (cx, cy) != (fx, fy):
            if tile_state is None and (private["seeds"].get(target_crop, 0) > 0 or private["seeds"].get("WHEAT", 0) > 0):
                return {"farmer": [path[0]], "hands": [], "market": market_orders}
            if isinstance(tile_state, dict) and (tile_state.get("kind") == "WEED" or (tile_state.get("kind") == "PLANT" and not tile_state.get("watered_today", False))):
                return {"farmer": [path[0]], "hands": [], "market": market_orders}
        
        for nx, ny, direction in [(cx, cy-1, "NORTH"), (cx, cy+1, "SOUTH"), (cx+1, cy, "EAST"), (cx-1, cy, "WEST")]:
            if 0 <= nx < 10 and 0 <= ny < 10 and tiles[ny][nx] != "LOCKED" and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, path + [direction]))

    return {"farmer": ["PASS"], "hands": [], "market": market_orders}
