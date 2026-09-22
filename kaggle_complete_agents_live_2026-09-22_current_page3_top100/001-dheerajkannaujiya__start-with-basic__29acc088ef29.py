
def get_direction(fx, fy, tx, ty):
    """Calculates Manhattan directional vector for grid navigation."""
    if fx < tx: return "EAST"
    if fx > tx: return "WEST"
    if fy < ty: return "SOUTH"
    if fy > ty: return "NORTH"
    return "PASS"

def agent(obs):
    """Pro-Tier Agent: Farm Hands, Task Delegation, and Shed Protection"""
    try:
        player = obs.get("player", 0)
        me = obs.get("farms", [])[player]
        private = obs.get("private", {})
        
        market_state = obs.get("market", {})
        prices = market_state.get("prices", {})
        
        fx, fy = me.get("farmer", [0, 0])
        hands = me.get("hands", [])
        tiles = me.get("tiles", [])
        unlocked = me.get("unlocked_quadrants", [])
        
        market_orders = []
        
        # --- 1. Shed Management & Market Execution ---
        total_items_in_shed = sum(private.get("shed", {}).values())
        
        for item, count in private.get("shed", {}).items():
            if count > 0:
                current_price = prices.get(item, 60)
                # Agar shed full hone wala hai (> 80), toh force sell karo. 
                # Warna Smart Sell (price > 30)
                if total_items_in_shed > 80 or current_price > 30 or item != "TOMATO":
                    market_orders.append(["SELL", item, count])
                    
        # --- 2. Scaling (Land, Seeds & Hires) ---
        TARGET_CROP = "TOMATO" 
        SEED_PRICE = 50
        
        # Zameen badhne par zyada seeds chahiye (Buffer = 15)
        if private.get("seeds", {}).get(TARGET_CROP, 0) < 15 and me.get("money", 0) >= SEED_PRICE:
            market_orders.append(["BUY_SEED", TARGET_CROP, 2])
            
        # Buy Land (1500 coins par)
        if me.get("money", 0) > 1500 and len(unlocked) < 4:
            market_orders.append(["BUY_LAND"])

        # --- 3. Grid Scanning (10x10) ---
        action_needed_tiles = []
        empty_tiles = []
        
        for y in range(len(tiles)):
            for x in range(len(tiles[0])):
                t = tiles[y][x]
                if t == "LOCKED": continue
                    
                if t is None:
                    empty_tiles.append((x, y, "PLANT"))
                elif isinstance(t, dict):
                    if t.get("kind") == "WEED":
                        action_needed_tiles.append((x, y, "DIG"))
                    elif t.get("kind") == "PLANT":
                        if t.get("yield_units", 0) > 0:
                            action_needed_tiles.append((x, y, "HARVEST"))
                        elif not t.get("watered_today", False):
                            action_needed_tiles.append((x, y, "WATER"))
                            
        # Hire Farm Hands agar pending kaam bohot zyada hai
        # Agar pending task 5 se zyada hain aur budget hai, toh ek helper bulao (max 2 per day)
        if len(action_needed_tiles) > 5 and me.get("money", 0) > 200 and me.get("hires_today", 0) < 2:
            market_orders.append(["HIRE"])

        # --- 4. Worker Task Delegation (Multi-Agent Control) ---
        # Sabhi workers (farmer + hands) ki list banate hain
        workers = [("farmer", fx, fy)]
        for hx, hy in hands:
            workers.append(("hand", hx, hy))
            
        claimed_targets = set()
        worker_actions = {"farmer": ["PASS"], "hands": []}
        
        has_seeds = private.get("seeds", {}).get(TARGET_CROP, 0) > 0

        for w_type, wx, wy in workers:
            my_action = ["PASS"]
            
            # Priority A: Current tile par koi kaam hai jo abhi tak kisi ne claim nahi kiya?
            current_task = None
            for ax, ay, act in action_needed_tiles:
                if ax == wx and ay == wy and (ax, ay) not in claimed_targets:
                    current_task = act
                    break
            
            if current_task:
                my_action = [current_task]
                claimed_targets.add((wx, wy))
            
            # Priority B: Current tile khali hai aur plant karna hai
            elif tiles[wy][wx] is None and has_seeds and (wx, wy) not in claimed_targets:
                my_action = ["PLANT", TARGET_CROP]
                claimed_targets.add((wx, wy))
                
            # Priority C: Nearest pending task ki taraf move karo
            else:
                closest_target = None
                min_dist = 999
                
                # Check pending tasks (Harvest/Water)
                available_targets = [(ax, ay, act) for ax, ay, act in action_needed_tiles if (ax, ay) not in claimed_targets]
                
                # Agar urgent kaam nahi hai, toh empty tiles target karo (agar seeds hain)
                if not available_targets and has_seeds:
                    available_targets = [(ex, ey, "PLANT") for ex, ey, _ in empty_tiles if (ex, ey) not in claimed_targets]
                    
                for tx, ty, _ in available_targets:
                    dist = abs(wx - tx) + abs(wy - ty)
                    if dist < min_dist:
                        min_dist = dist
                        closest_target = (tx, ty)
                        
                if closest_target:
                    my_action = [get_direction(wx, wy, closest_target[0], closest_target[1])]
                    claimed_targets.add((closest_target[0], closest_target[1]))
            
            # Assign action to specific worker
            if w_type == "farmer":
                worker_actions["farmer"] = my_action
            else:
                worker_actions["hands"].append(my_action)

        return {
            "farmer": worker_actions["farmer"],
            "hands": worker_actions["hands"],
            "market": market_orders
        }
        
    except Exception as e:
        # Failsafe
        return {"farmer": ["PASS"], "hands": [], "market": []}