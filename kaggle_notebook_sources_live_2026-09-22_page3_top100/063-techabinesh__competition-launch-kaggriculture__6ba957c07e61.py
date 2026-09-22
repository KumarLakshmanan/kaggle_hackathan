import random
import math
from collections import deque

# --- STRATEGIC CONSTANTS ---
CROP_PRIORITY = ["STRAWBERRY", "MELON", "TOMATO", "WHEAT"]
QUADRANT_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}
TERMINAL_STEP = 710  # When to start panic-selling everything

def agent(obs, config):
    # 1. DATA EXTRACTION
    step = obs['step']
    day = obs['day']
    hour = obs['hour']
    player_id = obs['player']
    me = obs['farms'][player_id]
    opp = obs['farms'][1-player_id]
    private = obs['private']
    money = me['money']
    prices = obs['market']['prices']
    
    # 2. HELPER: BFS PATHFINDING
    # Finds the nearest tile that matches a specific condition
    def find_target(start_pos, condition_func):
        queue = deque([(start_pos, [])])
        visited = {tuple(start_pos)}
        while queue:
            (cx, cy), path = queue.popleft()
            if condition_func(me['tiles'][cy][cx], cx, cy):
                return path[0] if path else "HERE"
            
            for dx, dy, move in [(0, -1, "NORTH"), (0, 1, "SOUTH"), (1, 0, "EAST"), (-1, 0, "WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in visited:
                    if me['tiles'][ny][nx] != "LOCKED":
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [move]))
        return None

    # 3. UNIT LOGIC (Farmer & Hands)
    def get_action(unit_pos, unit_inv):
        ux, uy = unit_pos
        current_tile = me['tiles'][uy][ux]

        # A. If standing on a target, act immediately
        if isinstance(current_tile, dict):
            if current_tile.get("kind") == "WEED":
                return ["DIG"]
            if current_tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if current_tile.get("kind") == "PLANT" and not current_tile.get("watered_today"):
                return ["WATER"]
        
        # B. If tile is empty, plant the best seed we have
        if current_tile is None:
            for crop in CROP_PRIORITY:
                if private['seeds'].get(crop, 0) > 0:
                    return ["PLANT", crop]

        # C. Navigation: Find the nearest tile that needs work
        # Priority: Weeds > Harvest > Water > Empty space for planting
        def needs_work(tile, x, y):
            if not isinstance(tile, dict): return tile is None
            return tile.get("kind") == "WEED" or tile.get("yield_units", 0) > 0 or not tile.get("watered_today")

        move = find_target(unit_pos, needs_work)
        if move and move != "HERE":
            return [move]
        
        return ["PASS"]

    # 4. MARKET LOGIC (Dynamic Economy)
    market_actions = []
    
    # Buy Land if we are wealthy
    unlocked = me['unlocked_quadrants']
    if "NE" not in unlocked and money > 1100: market_actions.append(["BUY_LAND"])
    elif "SW" not in unlocked and money > 2200: market_actions.append(["BUY_LAND"])

    # Seed Management: Buy seeds based on day
    if day < 20:
        if private['seeds'].get("STRAWBERRY", 0) < 10 and money > 1000:
            market_actions.append(["BUY_SEED", "STRAWBERRY", 5])
        if private['seeds'].get("WHEAT", 0) < 10 and money > 300:
            market_actions.append(["BUY_SEED", "WHEAT", 10])

    # Smart Selling (The "Tran" Logic)
    # Don't sell if price is $1, unless the game is ending.
    for item, count in private['shed'].items():
        if count > 0:
            if prices.get(item, 0) > 1 or step > TERMINAL_STEP:
                market_actions.append(["SELL", item, count])

    # Hire hands if we have a lot of land and money
    if len(unlocked) > 1 and me['hires_today'] < 2 and money > 1500:
        market_actions.append(["HIRE"])

    # 5. EXECUTION
    # Farmer
    farmer_act = get_action(me['farmer'], private['inventories'][0])
    
    # Hands
    hand_acts = []
    for i, h_pos in enumerate(me['hands']):
        hand_acts.append(get_action(h_pos, private['inventories'][i+1]))

    return {
        "farmer": farmer_act,
        "hands": hand_acts,
        "market": market_actions[:10]
    }

# --- TEST LOCAL RUN ---
if __name__ == "__main__":
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run([agent, "starter"])
    print("Final Reward:", env.steps[-1][0].reward)
    # env.render(mode="ipython", width=800, height=600) # Uncomment in Notebook