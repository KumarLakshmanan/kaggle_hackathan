# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session

# Use the kagglehub client library to attach Kaggle resources like competitions, datasets, and models to your session
# Learn more about kagglehub: https://github.com/Kaggle/kagglehub/blob/main/README.md

import kagglehub
# kagglehub.dataset_download('<owner>/<dataset-slug>')

# Environment Initialization & Dependencies
!pip install -q kaggle-environments

import numpy as np
import pandas as pd
from kaggle_environments import make
from IPython.display import HTML
import warnings

warnings.filterwarnings('ignore')

%%writefile submission.py

def get_tiered_bfs_move(start_x, start_y, tiles, obs, targeted_tiles, task_priority):
    """
    Tiered Breadth-First Search (BFS) with Swarm Collision Avoidance.
    Scans the grid for tasks based on strict operational priority.
    """
    queue = [(start_x, start_y, [])]
    visited = {(start_x, start_y)}
    directions = {"NORTH": (0, 1), "SOUTH": (0, -1), "EAST": (1, 0), "WEST": (-1, 0)}
    
    while queue:
        cx, cy, path = queue.pop(0)
        
        if path:
            tile = tiles[cy][cx]
            is_target = False
            
            if task_priority == "PLANT":
                if tile is None and (cx, cy) not in targeted_tiles:
                    is_target = True
            else:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and (cx, cy) not in targeted_tiles:
                    age = obs["day"] - tile["planted_day"]
                    h_age = 10 if tile.get("seed", "") == "MELON" else 4
                    
                    if task_priority == "HARVEST" and age >= h_age:
                        is_target = True
                    elif task_priority == "WATER" and not tile.get("watered_today", True) and age < h_age:
                        is_target = True
                        
            if is_target:
                targeted_tiles.add((cx, cy))
                return path[0]
        
        for d_name, (dx, dy) in directions.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
                if (nx, ny) not in visited and tiles[ny][nx] != "LOCKED":
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [d_name]))
                    
    return "PASS"


def evaluate_capex(obs, me):
    """Calculates ROI viability for Capital Expenditure (Land Purchasing)."""
    if obs["day"] >= 20: 
        return None # Doomsday protocol: Too late to realize ROI
        
    empty_tiles = sum(1 for row in me["tiles"] for tile in row if tile is None)
    if empty_tiles > 5: 
        return None # Asset utilization check: Fill current land first
        
    money = me["money"]
    unlocked = me.get("unlocked_quadrants", [])
    buffer = 1000 # Maintain cash flow for operations
    
    if "NE" not in unlocked and money >= (1000 + buffer): return ["BUY_LAND"]
    elif "SW" not in unlocked and money >= (2000 + buffer): return ["BUY_LAND"]
    elif "SE" not in unlocked and money >= (4000 + buffer): return ["BUY_LAND"]
    return None


def agent(obs):
    """Master Autonomous Control Loop."""
    me = obs["farms"][obs["player"]]
    private = obs["private"]
    tiles = me["tiles"]
    fx, fy = me["farmer"]
    day = obs["day"]
    
    market = []
    targeted_tiles = set() # Shared memory for the swarm
    
    # ---------------------------------------------------------
    # 1. MACRO-ECONOMICS & CAPEX
    # ---------------------------------------------------------
    expansion_order = evaluate_capex(obs, me)
    if expansion_order: 
        market.append(expansion_order)
        
    # Dynamic asset pivot: Melons yield 6x more profit/day than Wheat
    target_crop = "MELON" if me["money"] >= 300 and day < 20 else "WHEAT"
    seed_cost = 80 if target_crop == "MELON" else 10
    
    # Doomsday planting freeze to prevent stranding capital
    halt_purchases = (target_crop == "MELON" and day >= 20) or (target_crop == "WHEAT" and day >= 26)
    
    # ---------------------------------------------------------
    # 2. PROPORTIONAL LABOR & JIT INVENTORY
    # ---------------------------------------------------------
    active_crops = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")
    optimal_hands = min(4, active_crops // 8) 
    active_hands = len(me.get("hands", []))
    
    if active_hands < optimal_hands and me["money"] >= 50 and day < 28: 
        for _ in range(optimal_hands - active_hands):
            market.append(["HIRE"])
            
    current_target_seeds = private["seeds"].get(target_crop, 0)
    target_buffer = (active_hands + 1) * 2
    
    if not halt_purchases and current_target_seeds < target_buffer:
        amount_needed = target_buffer - current_target_seeds
        buy_amount = min(amount_needed, me["money"] // seed_cost)
        if buy_amount > 0:
            market.append(["BUY_SEED", target_crop, buy_amount])
            
    # ---------------------------------------------------------
    # 3. MARKET SPECULATION (Algorithmic Trading)
    # ---------------------------------------------------------
    for crop, base_price in [("WHEAT", 25), ("MELON", 250)]:
        shed_inv = private["shed"].get(crop, 0)
        current_price = obs.get("prices", {}).get(crop, base_price)
        if shed_inv > 0:
            # Liquidate if: Season ending OR cash starved OR price is surging
            if day >= 28 or me["money"] < 100 or current_price >= (base_price * 1.1):
                market.append(["SELL", crop, shed_inv])

    def get_plantable_seed():
        if day >= 20 and private["seeds"].get("MELON", 0) > 0:
            return None if day >= 20 and target_crop == "MELON" else "MELON" 
        if private["seeds"].get(target_crop, 0) > 0 and not halt_purchases: 
            return target_crop
        for crop, count in private["seeds"].items():
            if count > 0 and ((crop == "WHEAT" and day < 26) or (crop == "MELON" and day < 20)): 
                return crop
        return None

    # ---------------------------------------------------------
    # 4. MICRO-EXECUTION (Unit Command Pipeline)
    # ---------------------------------------------------------
    def get_unit_action(ux, uy):
        current_tile = tiles[uy][ux]
        action = ["PASS"]
        acted = False
        plantable = get_plantable_seed()
        
        # Immediate Tile Action
        if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
            age = day - current_tile["planted_day"]
            h_age = 10 if current_tile.get("seed", "") == "MELON" else 4
            if age >= h_age:
                action = ["HARVEST"]
                acted = True
                targeted_tiles.add((ux, uy))
            elif not current_tile.get("watered_today", True):
                action = ["WATER"]
                acted = True
                targeted_tiles.add((ux, uy))
        elif current_tile is None and plantable:
            action = ["PLANT", plantable]
            private["seeds"][plantable] -= 1
            acted = True
            targeted_tiles.add((ux, uy))
            
        # Tiered Pathfinding (Harvest -> Water -> Plant)
        if not acted:
            for task in ["HARVEST", "WATER", "PLANT"]:
                if task == "PLANT" and not plantable: continue
                move = get_tiered_bfs_move(ux, uy, tiles, obs, targeted_tiles, task)
                if move != "PASS":
                    action = [move]
                    break
        return action

    farmer_action = get_unit_action(fx, fy)
    hands_actions = [get_unit_action(hx, hy) for hx, hy in me.get("hands", [])]

    return {
        "farmer": farmer_action, 
        "hands": hands_actions, 
        "market": market
    }

# Initialize and simulate the environment (Full 30-Day Season / 720 Steps)
env = make("kaggriculture", configuration={"episodeSteps": 720})

# Run the optimized Operations Research agent against the random baseline
env.run(["submission.py", "random"])

# Extract and display the final financial standing
final_rewards = env.state[0]["reward"]

# Print high-visibility styled output
display(HTML(f"""
<div style='background: linear-gradient(135deg, #0f172a, #1e293b); color: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; font-size: 24px; font-family: "Courier New", monospace; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #334155;'>
    Final Portfolio Valuation: <b style="color: #10b981;">${final_rewards:,.2f}</b>
</div>
"""))

# Render the interactive Kaggle visualizer
HTML(env.render(mode="html"))

import pandas as pd
import numpy as np
from sklearn.model_selection import ParameterGrid
from kaggle_environments import make
import os

# 1. Define the Hyperparameter Search Space
param_grid = ParameterGrid({
    "LABOR_RATIO": [6, 8, 10],          # Crops per Farm Hand
    "CAPEX_CUTOFF": [18, 20, 22],       # Doomsday day cutoff
    "MARKET_MARGIN": [1.05, 1.10, 1.15] # Price spike multiplier
})

EPISODES_PER_CONFIG = 3 # Increase for statistical significance
results = []

print(f"Starting Grid Search: {len(param_grid)} configurations...")

# 2. Iterative Headless Evaluation
for idx, params in enumerate(param_grid):
    # Dynamically inject parameters into the agent code
    agent_code = f"""
def agent(obs):
    # Injected Hyperparameters
    LABOR_RATIO = {params['LABOR_RATIO']}
    CAPEX_CUTOFF = {params['CAPEX_CUTOFF']}
    MARKET_MARGIN = {params['MARKET_MARGIN']}
    
    # ... (Insert your main agent logic here, referencing the constants above) ...
    return {{"farmer": ["PASS"], "hands": [], "market": []}}
"""
    # Write the temporary agent file
    temp_file = f"temp_agent_{idx}.py"
    with open(temp_file, "w") as f:
        f.write(agent_code)
        
    config_scores = []
    
    # Run headless episodes
    for _ in range(EPISODES_PER_CONFIG):
        env = make("kaggriculture", configuration={"episodeSteps": 720})
        env.run([temp_file, "random"])
        config_scores.append(env.state[0]["reward"])
        
    # Clean up temp file
    os.remove(temp_file)
    
    # 3. Log Results
    results.append({
        "LABOR_RATIO": params["LABOR_RATIO"],
        "CAPEX_CUTOFF": params["CAPEX_CUTOFF"],
        "MARKET_MARGIN": params["MARKET_MARGIN"],
        "Mean_ROI": np.mean(config_scores),
        "Std_Dev": np.std(config_scores)
    })
    print(f"Config {idx+1}/{len(param_grid)} | Mean ROI: ${np.mean(config_scores):.2f}")

# 4. Analyze Output
results_df = pd.DataFrame(results).sort_values(by="Mean_ROI", ascending=False)
print("\nTop 5 Configurations:")
display(results_df.head())

# %%writefile submission.py

# def get_tiered_bfs_move(start_x, start_y, tiles, obs, targeted_tiles, task_priority):
#     """Tiered BFS: Searches the grid based on task priority (HARVEST -> WATER -> PLANT)."""
#     queue = [(start_x, start_y, [])]
#     visited = {(start_x, start_y)}
#     directions = {"NORTH": (0, 1), "SOUTH": (0, -1), "EAST": (1, 0), "WEST": (-1, 0)}
    
#     while queue:
#         cx, cy, path = queue.pop(0)
        
#         if path:
#             tile = tiles[cy][cx]
#             is_target = False
            
#             if task_priority == "PLANT":
#                 if tile is None and (cx, cy) not in targeted_tiles:
#                     is_target = True
#             else:
#                 if isinstance(tile, dict) and tile.get("kind") == "PLANT" and (cx, cy) not in targeted_tiles:
#                     age = obs["day"] - tile["planted_day"]
#                     h_age = 10 if tile.get("seed", "") == "MELON" else 4
                    
#                     if task_priority == "HARVEST" and age >= h_age:
#                         is_target = True
#                     elif task_priority == "WATER" and not tile.get("watered_today", True) and age < h_age:
#                         is_target = True
                        
#             if is_target:
#                 targeted_tiles.add((cx, cy))
#                 return path[0]
        
#         for d_name, (dx, dy) in directions.items():
#             nx, ny = cx + dx, cy + dy
#             if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#                 if (nx, ny) not in visited and tiles[ny][nx] != "LOCKED":
#                     visited.add((nx, ny))
#                     queue.append((nx, ny, path + [d_name]))
                    
#     return "PASS"


# def check_land_expansion(obs, me):
#     """Calculates ROI viability for Capital Expenditure (Land Purchasing)."""
#     if obs["day"] >= 20: return None
#     empty_tiles = sum(1 for row in me["tiles"] for tile in row if tile is None)
#     if empty_tiles > 5: return None
        
#     money = me["money"]
#     unlocked = me.get("unlocked_quadrants", [])
#     buffer = 1000 
    
#     if "NE" not in unlocked and money >= (1000 + buffer): return ["BUY_LAND"]
#     elif "SW" not in unlocked and money >= (2000 + buffer): return ["BUY_LAND"]
#     elif "SE" not in unlocked and money >= (4000 + buffer): return ["BUY_LAND"]
#     return None


# def agent(obs):
#     """Master Control Loop for Autonomous Agent."""
#     me = obs["farms"][obs["player"]]
#     private = obs["private"]
#     tiles = me["tiles"]
#     fx, fy = me["farmer"]
#     day = obs["day"]
    
#     market = []
#     targeted_tiles = set()
    
#     # 1. CAPITAL & EXPANSION
#     expansion_order = check_land_expansion(obs, me)
#     if expansion_order: market.append(expansion_order)
        
#     target_crop = "MELON" if me["money"] >= 300 and day < 20 else "WHEAT"
#     seed_cost = 80 if target_crop == "MELON" else 10
#     halt_purchases = (target_crop == "MELON" and day >= 20) or (target_crop == "WHEAT" and day >= 26)
    
#     # 2. PROPORTIONAL LABOR SCALING
#     active_crops = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")
#     optimal_hands = min(4, active_crops // 8) 
    
#     active_hands = len(me.get("hands", []))
#     if active_hands < optimal_hands and me["money"] >= 50 and day < 28: 
#         for _ in range(optimal_hands - active_hands):
#             market.append(["HIRE"])
            
#     current_target_seeds = private["seeds"].get(target_crop, 0)
#     target_buffer = (active_hands + 1) * 2
    
#     if not halt_purchases and current_target_seeds < target_buffer:
#         amount_needed = target_buffer - current_target_seeds
#         buy_amount = min(amount_needed, me["money"] // seed_cost)
#         if buy_amount > 0:
#             market.append(["BUY_SEED", target_crop, buy_amount])
            
#     # Diamond Hands: Market Speculation
#     for crop, base_price in [("WHEAT", 25), ("MELON", 250)]:
#         shed_inv = private["shed"].get(crop, 0)
#         current_price = obs.get("prices", {}).get(crop, base_price)
#         if shed_inv > 0:
#             if day >= 28 or me["money"] < 100 or current_price >= (base_price * 1.1):
#                 market.append(["SELL", crop, shed_inv])

#     def get_plantable_seed():
#         if day >= 20 and private["seeds"].get("MELON", 0) > 0:
#             return None if day >= 20 and target_crop == "MELON" else "MELON" 
#         if private["seeds"].get(target_crop, 0) > 0 and not halt_purchases: 
#             return target_crop
#         for crop, count in private["seeds"].items():
#             if count > 0 and ((crop == "WHEAT" and day < 26) or (crop == "MELON" and day < 20)): 
#                 return crop
#         return None

#     # 3. UNIT COMMAND PIPELINE
#     def get_unit_action(ux, uy, is_farmer=False):
#         current_tile = tiles[uy][ux]
#         action = ["PASS"]
#         acted = False
#         plantable = get_plantable_seed()
        
#         if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
#             age = day - current_tile["planted_day"]
#             h_age = 10 if current_tile.get("seed", "") == "MELON" else 4
#             if age >= h_age:
#                 action = ["HARVEST"]
#                 acted = True
#                 targeted_tiles.add((ux, uy))
#             elif not current_tile.get("watered_today", True):
#                 action = ["WATER"]
#                 acted = True
#                 targeted_tiles.add((ux, uy))
#         elif current_tile is None and plantable:
#             action = ["PLANT", plantable]
#             private["seeds"][plantable] -= 1
#             acted = True
#             targeted_tiles.add((ux, uy))
            
#         if not acted:
#             for task in ["HARVEST", "WATER", "PLANT"]:
#                 if task == "PLANT" and not plantable: continue
#                 move = get_tiered_bfs_move(ux, uy, tiles, obs, targeted_tiles, task)
#                 if move != "PASS":
#                     action = [move]
#                     break
#         return action

#     farmer_action = get_unit_action(fx, fy, is_farmer=True)
#     hands_actions = [get_unit_action(hx, hy) for hx, hy in me.get("hands", [])]

#     return {
#         "farmer": farmer_action, 
#         "hands": hands_actions, 
#         "market": market
#     }

# # Initialize and simulate the environment
# env = make("kaggriculture", configuration={"episodeSteps": 720})

# # Run the optimized agent against the random baseline
# env.run(["submission.py", "random"])

# # Extract and display the final financial standing
# # FIX: Access "reward" directly from the agent's state, not from "observation"
# final_rewards = env.state[0]["reward"]

# # Print styled output for the notebook viewer
# from IPython.display import HTML, display

# display(HTML(f"""
# <div style='background-color: #2c3e50; color: white; padding: 15px; border-radius: 8px; text-align: center; font-size: 20px; font-family: monospace;'>
#     Final Portfolio Valuation: <b>${final_rewards:,.2f}</b>
# </div>
# """))

# # Render the interactive visualizer
# HTML(env.render(mode="html"))

# !pip install -U kaggle-environments

# %%writefile submission.py

# def agent(obs):
#     player = obs["player"]
#     me = obs["farms"][player]
#     private = obs["private"]
#     fx, fy = me["farmer"]
#     tile = me["tiles"][fy][fx]

#     market = []

#     # Buy a wheat seed if we have none and have enough money
#     if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
#         market.append(["BUY_SEED", "WHEAT", 1])

#     # Sell any wheat sitting in the shed
#     wheat_in_shed = private["shed"].get("WHEAT", 0)
#     if wheat_in_shed > 0:
#         market.append(["SELL", "WHEAT", wheat_in_shed])

#     # If standing on an empty tile, plant wheat
#     if tile is None and private["seeds"].get("WHEAT", 0) > 0:
#         return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}

#     # If standing on a plant, manage watering and harvesting
#     if isinstance(tile, dict) and tile.get("kind") == "PLANT":
#         crop_age = obs["day"] - tile["planted_day"]
#         if crop_age >= 2:  
#             return {"farmer": ["HARVEST"], "hands": [], "market": market}
#         if not tile["watered_today"]:
#             return {"farmer": ["WATER"], "hands": [], "market": market}

#     return {"farmer": ["PASS"], "hands": [], "market": market}

# from kaggle_environments import make
# from IPython.display import HTML

# # Create the environment and run the match
# env = make("kaggriculture", configuration={"episodeSteps": 720})
# env.run(["submission.py", "random"])

# # Force the notebook to render the HTML output directly
# html_output = env.render(mode="html")
# HTML(html_output)

# from kaggle_environments import make

# # Create the environment and run the match
# env = make("kaggriculture", configuration={"episodeSteps": 720})
# env.run(["submission.py", "random"])

# # Save the visualizer to an HTML file
# with open("replay.html", "w") as f:
#     f.write(env.render(mode="html"))
    
# print("Replay saved as replay.html!")

# %%writefile submission.py

# def agent(obs):
#     me = obs["farms"][obs["player"]]
#     private = obs["private"]
#     fx, fy = me["farmer"]
#     tiles = me["tiles"]
    
#     market = []
    
#     # 1. MARKET STRATEGY: Maintain a seed buffer
#     # Buy seeds if we have fewer than 3 and enough money, so the farmer can plant seamlessly
#     wheat_seeds = private["seeds"].get("WHEAT", 0)
#     if wheat_seeds < 3 and me["money"] >= 10:
#         market.append(["BUY_SEED", "WHEAT", 1])

#     # Sell any wheat sitting in the shed to realize profits
#     wheat_in_shed = private["shed"].get("WHEAT", 0)
#     if wheat_in_shed > 0:
#         market.append(["SELL", "WHEAT", wheat_in_shed])

#     # 2. FIELD STRATEGY: Manage the tile we are currently standing on
#     current_tile = tiles[fy][fx]
    
#     if current_tile is None:
#         if wheat_seeds > 0:
#             return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}
            
#     elif isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
#         crop_age = obs["day"] - current_tile["planted_day"]
#         if crop_age >= 2:  
#             return {"farmer": ["HARVEST"], "hands": [], "market": market}
#         if not current_tile.get("watered_today", True):
#             return {"farmer": ["WATER"], "hands": [], "market": market}

#     # 3. MOVEMENT STRATEGY: Find the next best tile to move to
#     # Map directions to grid coordinate shifts (assuming standard Kaggle y-up/y-down grid bounds)
#     directions = {
#         "NORTH": (0, 1),
#         "SOUTH": (0, -1),
#         "EAST":  (1, 0),
#         "WEST":  (-1, 0)
#     }
    
#     # Priority A: Move to an adjacent plant that urgently needs harvesting or watering
#     for dir_name, (dx, dy) in directions.items():
#         nx, ny = fx + dx, fy + dy
#         if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#             neighbor = tiles[ny][nx]
#             if isinstance(neighbor, dict) and neighbor.get("kind") == "PLANT":
#                 age = obs["day"] - neighbor["planted_day"]
#                 if age >= 2 or not neighbor.get("watered_today", True):
#                     return {"farmer": [dir_name], "hands": [], "market": market}

#     # Priority B: Move to an adjacent empty, unlocked tile to plant more crops
#     for dir_name, (dx, dy) in directions.items():
#         nx, ny = fx + dx, fy + dy
#         if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#             neighbor = tiles[ny][nx]
#             if neighbor is None: # 'None' means empty and unlocked. "LOCKED" is inaccessible.
#                 return {"farmer": [dir_name], "hands": [], "market": market}

#     # Fallback: If trapped or fully saturated, just pass
#     return {"farmer": ["PASS"], "hands": [], "market": market}

# %%writefile submission.py

# def check_land_expansion(obs, me):
#     """Evaluates the mathematical safety of buying a new quadrant."""
#     day = obs["day"]
#     money = me["money"]
#     unlocked = me.get("unlocked_quadrants", [])
    
#     # Rule 1: The Doomsday Clock (No cap-ex if crops can't mature before Day 30)
#     if day >= 20:
#         return None
        
#     # Rule 2: The Capacity Check (Must have < 5 empty workable tiles)
#     empty_tiles = sum(1 for row in me["tiles"] for tile in row if tile is None)
#     if empty_tiles > 5:
#         return None
        
#     # Rule 3: The Capital Buffer ($1000 buffer over sticker price for seeds/labor)
#     buffer = 1000 
#     if "NE" not in unlocked and money >= (1000 + buffer):
#         return ["BUY_LAND"]
#     elif "SW" not in unlocked and money >= (2000 + buffer):
#         return ["BUY_LAND"]
#     elif "SE" not in unlocked and money >= (4000 + buffer):
#         return ["BUY_LAND"]
        
#     return None


# def agent(obs):
#     """Main autonomous control loop."""
#     me = obs["farms"][obs["player"]]
#     private = obs["private"]
#     tiles = me["tiles"]
#     fx, fy = me["farmer"]
    
#     market = []
    
#     # ==========================================
#     # 1. CAPITAL & EXPANSION ECONOMICS
#     # ==========================================
#     expansion_order = check_land_expansion(obs, me)
#     if expansion_order:
#         market.append(expansion_order)
        
#     # Bankroll Switch: Transition to high-yield Melons when safe
#     target_crop = "MELON" if me["money"] >= 300 else "WHEAT"
#     seed_cost = 80 if target_crop == "MELON" else 10
    
#     # ==========================================
#     # 2. LABOR MANAGEMENT
#     # ==========================================
#     active_hands = len(me.get("hands", []))
    
#     # Hire up to 2 hands per day if we have cash
#     if active_hands < 2 and me["money"] >= 20: 
#         hands_to_hire = 2 - active_hands
#         for _ in range(hands_to_hire):
#             market.append(["HIRE"])
            
#     # ==========================================
#     # 3. INVENTORY & SUPPLY CHAIN
#     # ==========================================
#     current_seeds = private["seeds"].get(target_crop, 0)
#     target_buffer = (active_hands + 1) * 2
    
#     # Buy seeds to maintain our buffer
#     if current_seeds < target_buffer and me["money"] >= seed_cost:
#         market.append(["BUY_SEED", target_crop, 1])
        
#     # Liquidate shed inventory immediately
#     for crop in ["WHEAT", "MELON"]:
#         shed_inventory = private["shed"].get(crop, 0)
#         if shed_inventory > 0:
#             market.append(["SELL", crop, shed_inventory])

#     # ==========================================
#     # 4. PATHFINDING & FIELD OPERATIONS
#     # ==========================================
#     directions = {"NORTH": (0, 1), "SOUTH": (0, -1), "EAST": (1, 0), "WEST": (-1, 0)}
    
#     # --- A. Farmer Logic ---
#     farmer_action = ["PASS"]
#     current_tile = tiles[fy][fx]
#     action_taken = False
    
#     if current_tile is None and current_seeds > 0:
#         farmer_action = ["PLANT", target_crop]
#         current_seeds -= 1
#         action_taken = True
        
#     elif isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
#         crop_age = obs["day"] - current_tile["planted_day"]
#         is_melon = current_tile.get("seed", "") == "MELON"
#         harvest_age = 10 if is_melon else 4
        
#         if crop_age >= harvest_age:
#             farmer_action = ["HARVEST"]
#             action_taken = True
#         elif not current_tile.get("watered_today", True):
#             farmer_action = ["WATER"]
#             action_taken = True
            
#     # Farmer Movement (if no action taken on current tile)
#     if not action_taken:
#         moved = False
#         # Priority 1: Rescue adjacent plants
#         for dir_name, (dx, dy) in directions.items():
#             nx, ny = fx + dx, fy + dy
#             if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#                 neighbor = tiles[ny][nx]
#                 if isinstance(neighbor, dict) and neighbor.get("kind") == "PLANT":
#                     age = obs["day"] - neighbor["planted_day"]
#                     h_age = 10 if neighbor.get("seed", "") == "MELON" else 4
#                     if age >= h_age or not neighbor.get("watered_today", True):
#                         farmer_action = [dir_name]
#                         moved = True
#                         break
#         # Priority 2: Seek empty dirt
#         if not moved:
#             for dir_name, (dx, dy) in directions.items():
#                 nx, ny = fx + dx, fy + dy
#                 if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#                     neighbor = tiles[ny][nx]
#                     if neighbor is None:
#                         farmer_action = [dir_name]
#                         break

#     # --- B. Farm Hands Logic ---
#     hands_actions = []
#     for hx, hy in me.get("hands", []):
#         hand_tile = tiles[hy][hx]
#         hand_acted = False
        
#         if isinstance(hand_tile, dict) and hand_tile.get("kind") == "PLANT":
#             crop_age = obs["day"] - hand_tile["planted_day"]
#             h_age = 10 if hand_tile.get("seed", "") == "MELON" else 4
            
#             if crop_age >= h_age:
#                 hands_actions.append(["HARVEST"])
#                 hand_acted = True
#             elif not hand_tile.get("watered_today", True):
#                 hands_actions.append(["WATER"])
#                 hand_acted = True
                
#         elif hand_tile is None and current_seeds > 0:
#             hands_actions.append(["PLANT", target_crop])
#             current_seeds -= 1
#             hand_acted = True
            
#         # Hand Movement
#         if not hand_acted:
#             moved = False
#             for dir_name, (dx, dy) in directions.items():
#                 nx, ny = hx + dx, hy + dy
#                 if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
#                     neighbor = tiles[ny][nx]
#                     if neighbor == "LOCKED":
#                         continue
#                     if neighbor is None or (isinstance(neighbor, dict) and neighbor.get("kind") == "PLANT" and not neighbor.get("watered_today", True)):
#                         hands_actions.append([dir_name])
#                         moved = True
#                         break
#             if not moved:
#                 hands_actions.append(["PASS"])

#     # ==========================================
#     # 5. DISPATCH
#     # ==========================================
#     return {
#         "farmer": farmer_action, 
#         "hands": hands_actions, 
#         "market": market
#     }