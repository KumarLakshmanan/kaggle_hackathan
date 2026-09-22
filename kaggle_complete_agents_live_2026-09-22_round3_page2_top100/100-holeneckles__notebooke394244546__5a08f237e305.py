def agent(obs, config):
    """
    High-performance Kaggriculture simulation agent optimized for coin accumulation,
    strategic land expansion, and efficient crop harvesting cycles.
    """
    player_idx = obs["player"]
    my_farm = obs["farms"][player_idx]
    money = my_farm["money"]
    farmer_pos = my_farm["farmer"]
    unlocked = my_farm["unlocked_quadrants"]
    
    shed = obs["private"]["shed"]
    seeds = obs["private"]["seeds"]
    
    actions = {}
    market_orders = []
    
    # Shed proximity optimization coordinates (center layout)
    shed_adjacent_tiles = [(4, 4), (5, 4), (4, 5), (5, 5)]
    is_near_shed = tuple(farmer_pos) in shed_adjacent_tiles
    
    # 1. Economic Land Expansion Rules
    if money >= 1000 and "NE" not in unlocked:
        market_orders.append(["BUY_LAND"])
    elif money >= 2000 and "SW" not in unlocked:
        market_orders.append(["BUY_LAND"])
        
    # 2. Re-stocking Inventory Seed Levels
    if seeds.get("WHEAT", 0) < 10 and money >= 100:
        market_orders.append(["BUY_SEED", "WHEAT", 10])

    # 3. Farmer Navigation and Field Operations
    fx, fy = farmer_pos
    current_tile = my_farm["tiles"][fy][fx]
    
    total_shed_items = sum(shed.values()) if isinstance(shed, dict) else 0
    
    # Offload harvested goods to central shed when space permits
    if is_near_shed and total_shed_items < 90:
        farmer_inv = obs["private"]["inventories"].get(0, {}) if isinstance(obs["private"]["inventories"], dict) else {}
        if farmer_inv:
            actions["farmer"] = "DROP"
            return {"actions": actions, "market": market_orders[:10]}

    # Cultivation logic
    if current_tile is None:
        if seeds.get("WHEAT", 0) > 0:
            actions["farmer"] = "PLANT WHEAT"
        else:
            market_orders.append(["BUY_SEED", "WHEAT", 5])
            actions["farmer"] = "PASS"
            
    elif isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
        # Water plants daily to avoid crop decay into weeds
        if not current_tile.get("watered_today", False):
            actions["farmer"] = "WATER"
        # Harvest once mature to clear tile and accumulate profit points
        elif current_tile.get("yield_units", 0) > 1:
            actions["farmer"] = "HARVEST"
        else:
            actions["farmer"] = "PASS"
    else:
        # Field routing movement pattern
        if fx < 6:
            actions["farmer"] = "EAST"
        elif fy < 6:
            actions["farmer"] = "SOUTH"
        else:
            actions["farmer"] = "PASS"

    return {
        "actions": actions,
        "market": market_orders[:10]
    }
