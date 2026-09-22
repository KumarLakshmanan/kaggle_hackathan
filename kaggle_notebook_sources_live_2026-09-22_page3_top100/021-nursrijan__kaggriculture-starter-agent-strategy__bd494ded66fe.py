!pip install -q kaggle-environments matplotlib seaborn pandas numpy


import sys
import os
import json
import math
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual aesthetic style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 120

import kaggle_environments
from kaggle_environments import make, evaluate

print(f"✅ Kaggle Environments version: {kaggle_environments.__version__}")


# Let's plot the theoretical market price curves for key crops to visualize price sensitivity!

def compute_price(base, I0, T, inv, func_below, target_below, func_above, target_above):
    diff = inv - I0
    if diff == 0:
        return base
    
    def apply_f(func, x):
        if func == 'sqrt': return math.sqrt(x)
        if func == 'linear': return x
        if func == 'log': return math.log(1 + x)
        if func == 'sq': return x ** 2
        if func == 'log10': return math.log10(1 + x)
        return x

    if diff < 0: # Scarcity
        x = abs(diff)
        f_val = apply_f(func_below, x)
        f_T = apply_f(func_below, T)
        amp = (target_below * base) / f_T if f_T != 0 else 0
        p = base + amp * f_val
    else: # Glut
        x = diff
        f_val = apply_f(func_above, x)
        f_T = apply_f(func_above, T)
        amp = (target_above * base) / f_T if f_T != 0 else 0
        p = base - amp * f_val

    return max(1, round(p))

# Simulate price dynamics across inventory shifts (-500 to +1000 units relative to I0)
inv_range = np.linspace(9500, 11000, 300)
crops_params = {
    'Wheat': (25, 10000, 400, 'sqrt', 0.80, 'log', 0.20),
    'Melon': (250, 10000, 300, 'log', 0.20, 'sq', 3.60),
    'Strawberry': (120, 10000, 100, 'sqrt', 0.70, 'linear', 1.60),
    'Tomato': (60, 10000, 200, 'linear', 0.40, 'sqrt', 0.60)
}

plt.figure(figsize=(12, 6))
for name, params in crops_params.items():
    prices = [compute_price(*params[:3], inv, *params[3:]) for inv in inv_range]
    plt.plot(inv_range - 10000, prices, label=f"{name} (Base ${params[0]})", linewidth=2.5)

plt.axvline(0, color='gray', linestyle='--', alpha=0.7, label='Initial Market Inventory ($I_0$)')
plt.axhline(1, color='red', linestyle=':', label='Price Floor ($1)')
plt.title("Kaggriculture Market Price Elasticity Curves", fontsize=14, fontweight='bold')
plt.xlabel("Net Inventory Shift from Equilibrium ($inv - I_0$)", fontsize=12)
plt.ylabel("Market Price ($)", fontsize=12)
plt.legend(frameon=True, facecolor='white', framealpha=0.9)
plt.tight_layout()
plt.show()


# Initialize environment
env = make("kaggriculture", debug=True)
print("Configuration parameters:")
for k, v in list(env.configuration.items())[:8]:
    print(f" - {k}: {v}")


class KaggricultureVisualizer:
    """Rich visualizer for Kaggriculture observations and farm grids."""
    
    @staticmethod
    def render_ascii(obs):
        day = obs['day']
        hour = obs['hour']
        m_prices = obs['market']['prices']
        
        print(f"╔══════════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ 📅 DAY {day+1:02d} | ⏰ HOUR {hour:02d}/24 | 🌾 Market Prices: WHEAT ${m_prices.get('WHEAT', 0)} | MELON ${m_prices.get('MELON', 0)} | TOMATO ${m_prices.get('TOMATO', 0)} ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════════╣")
        
        for p_idx, farm in enumerate(obs['farms']):
            money = farm['money']
            farmer = farm['farmer']
            hands = farm['hands']
            quads = len(farm['unlocked_quadrants'])
            
            grid_str = ""
            for y in range(10):
                row = []
                for x in range(10):
                    tile = farm['tiles'][y][x]
                    if [x, y] == farmer:
                        cell = "👨"
                    elif [x, y] in hands:
                        cell = "🧑"
                    elif tile == "LOCKED":
                        cell = "🔒"
                    elif tile is None:
                        cell = "🟫" # Empty dirt
                    elif isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                        crop = tile['crop']
                        if crop == 'WHEAT': cell = "🌾"
                        elif crop == 'CARROT': cell = "🥕"
                        elif crop == 'TOMATO': cell = "🍅"
                        elif crop == 'STRAWBERRY': cell = "🍓"
                        elif crop == 'MELON': cell = "🍈"
                        else: cell = "🌱"
                    elif isinstance(tile, dict) and tile.get('kind') == 'WEED':
                        cell = "🌿"
                    elif isinstance(tile, dict) and tile.get('kind') == 'COOP':
                        cell = "🪿" if tile.get('animal') else "🛖"
                    elif isinstance(tile, dict) and tile.get('kind') == 'PASTURE':
                        cell = "🐮" if tile.get('animal') == 'COW' else ("🐑" if tile.get('animal') == 'SHEEP' else "🪵")
                    else:
                        cell = "▫️"
                    row.append(cell)
                grid_str += " ".join(row) + "\n"
                
            print(f"  P{p_idx} Bank: ${money:.1f} | Quads: {quads}/4 | Position: {farmer}")
            print("  Farm Grid:")
            for r in grid_str.strip().split('\n'):
                print(f"    {r}")
        print(f"╚══════════════════════════════════════════════════════════════════════════════════╝\n")

# Test visualizer on initial step
env.reset()
KaggricultureVisualizer.render_ascii(env.steps[0][0]['observation'])


def pass_agent(obs):
    """Minimal agent that passes every turn."""
    return {"farmer": ["PASS"], "hands": [], "market": []}

def starter_wheat_agent(obs):
    """Official starter agent implementing a basic wheat farming loop."""
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]

    market = []
    
    # 1. Buy wheat seed if none in inventory and money >= 10
    if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])
        
    # 2. Sell any harvested wheat sitting in the shed
    wheat_in_shed = private["shed"].get("WHEAT", 0)
    if wheat_in_shed > 0:
        market.append(["SELL", "WHEAT", wheat_in_shed])

    # 3. Plant wheat if standing on an empty unlocked tile and seeds are available
    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}
        
    # 4. If standing on a plant, water or harvest
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 2:  # Wheat first_yield_day = 2
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile.get("watered_today", False):
            return {"farmer": ["WATER"], "hands": [], "market": market}

    # 5. Otherwise move towards empty tiles or pass
    return {"farmer": ["PASS"], "hands": [], "market": market}


# Run a match between starter_wheat_agent and random agent
env = make("kaggriculture", debug=True)
env.run([starter_wheat_agent, "random"])

final_step = env.steps[-1]
print("Match Results:")
for p_idx, state in enumerate(final_step):
    print(f" Player {p_idx} ({'Starter Wheat' if p_idx==0 else 'Random'}): Final Money = ${state['observation']['farms'][p_idx]['money']:.2f}, Reward = {state['reward']}, Status = {state['status']}")


def agromaster_agent(obs):
    """
    AgroMaster-v1: Strategic Multi-Phase Farm & Market Optimization Agent
    """
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
    
    # -------------------------------------------------------------
    # 1. MARKET STRATEGY: Seeds, Selling, & Hiring
    # -------------------------------------------------------------
    # A. Crop Selection based on Season Phase
    if day < 8:
        target_crop = "WHEAT"
        target_seed_cost = 10
    elif day < 20:
        target_crop = "TOMATO" if money > 80 else "CARROT"
        target_seed_cost = 50 if target_crop == "TOMATO" else 20
    else:
        target_crop = "CARROT"
        target_seed_cost = 20

    # Seed Inventory Management
    current_seeds = private["seeds"].get(target_crop, 0)
    if current_seeds < 3 and money >= target_seed_cost * 3:
        market_orders.append(["BUY_SEED", target_crop, 3])
        
    # Wheat Seed Buffer for Safety
    if private["seeds"].get("WHEAT", 0) < 2 and money >= 20:
        market_orders.append(["BUY_SEED", "WHEAT", 2])

    # B. Price-Elastic Selling from Shed
    for item, qty in private["shed"].items():
        if qty > 0:
            item_price = prices.get(item, 0)
            # Only sell if price is reasonable (above floor unless last 3 days)
            if item_price > 1 or day >= 27:
                market_orders.append(["SELL", item, qty])

    # C. Adaptive Farm Hand Hiring
    # Hire hand if we have high money and lots of tiles to service
    if day > 3 and me["hires_today"] == 0 and money > 500:
        market_orders.append(["HIRE", 1])

    # -------------------------------------------------------------
    # 2. FARMER TILE & MOVEMENT DECISION ENGINE (BFS Target Selection)
    # -------------------------------------------------------------
    current_tile = tiles[fy][fx]
    
    # Action A: Clear Weed immediately if standing on one
    if isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
        return {"farmer": ["DIG"], "hands": [], "market": market_orders}

    # Action B: Harvest ready crops
    if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
        crop = current_tile["crop"]
        crop_age = day - current_tile["planted_day"]
        # Harvest conditions per crop type
        if crop in ["WHEAT", "CARROT", "MELON"] and crop_age >= 2:
            return {"farmer": ["HARVEST"], "hands": [], "market": market_orders}
        elif crop in ["TOMATO", "STRAWBERRY"] and crop_age >= 8:
            return {"farmer": ["HARVEST"], "hands": [], "market": market_orders}

    # Action C: Water unwatered plants
    if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
        if not current_tile.get("watered_today", False):
            return {"farmer": ["WATER"], "hands": [], "market": market_orders}

    # Action D: Plant seed on empty dirt tile
    if current_tile is None:
        if private["seeds"].get(target_crop, 0) > 0:
            return {"farmer": ["PLANT", target_crop], "hands": [], "market": market_orders}
        elif private["seeds"].get("WHEAT", 0) > 0:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market_orders}

    # Action E: BFS Pathfinding to Nearest High-Priority Tile
    def bfs_find_target():
        queue = [(fx, fy, [])]
        visited = set([(fx, fy)])
        
        while queue:
            cx, cy, path = queue.pop(0)
            tile_state = tiles[cy][cx]
            
            # Check if this cell needs attention
            if (cx, cy) != (fx, fy):
                if tile_state is None and (private["seeds"].get(target_crop, 0) > 0 or private["seeds"].get("WHEAT", 0) > 0):
                    return path[0] # Move towards empty dirt
                if isinstance(tile_state, dict) and tile_state.get("kind") == "WEED":
                    return path[0]
                if isinstance(tile_state, dict) and tile_state.get("kind") == "PLANT":
                    if not tile_state.get("watered_today", False):
                        return path[0]
            
            # Explore neighbors
            neighbors = [
                (cx, cy - 1, "NORTH"),
                (cx, cy + 1, "SOUTH"),
                (cx + 1, cy, "EAST"),
                (cx - 1, cy, "WEST")
            ]
            for nx, ny, direction in neighbors:
                if 0 <= nx < 10 and 0 <= ny < 10:
                    if tiles[ny][nx] != "LOCKED" and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [direction]))
        return None

    next_move = bfs_find_target()
    if next_move:
        return {"farmer": [next_move], "hands": [], "market": market_orders}

    return {"farmer": ["PASS"], "hands": [], "market": market_orders}


# Run multi-episode benchmark tournament
N_EPISODES = 5
results = []

print(f"🚀 Running {N_EPISODES}-episode Benchmark Tournament...")

for ep in range(N_EPISODES):
    env = make("kaggriculture", debug=False)
    env.run([agromaster_agent, starter_wheat_agent])
    
    p0_score = env.steps[-1][0]['observation']['farms'][0]['money']
    p1_score = env.steps[-1][1]['observation']['farms'][1]['money']
    winner = "AgroMaster-v1" if p0_score > p1_score else ("Starter Wheat" if p1_score > p0_score else "Tie")
    
    results.append({
        "Episode": ep + 1,
        "AgroMaster-v1 ($)": p0_score,
        "Starter Wheat ($)": p1_score,
        "Winner": winner
    })

df_results = pd.DataFrame(results)
print("\n🏆 Tournament Summary Results:")
print(df_results.to_string(index=False))

# Plot performance distribution
plt.figure(figsize=(10, 5))
df_melted = df_results.melt(id_vars=["Episode", "Winner"], value_vars=["AgroMaster-v1 ($)", "Starter Wheat ($)"], var_name="Agent", value_name="Final Coins ($)")
sns.barplot(data=df_melted, x="Episode", y="Final Coins ($)", hue="Agent")
plt.title("Tournament Comparison: AgroMaster-v1 vs. Starter Wheat Baseline", fontsize=14, fontweight='bold')
plt.xlabel("Episode Number", fontsize=12)
plt.ylabel("Final Coin Balance ($)", fontsize=12)
plt.legend(frameon=True)
plt.tight_layout()
plt.show()


# Write standalone main.py agent file for submission
agent_code = """
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
"""

with open("main.py", "w") as f:
    f.write(agent_code.strip())

print("✅ main.py written successfully!")


# Test running main.py with kaggle-environments
env = make("kaggriculture", debug=True)
env.run(["main.py", starter_wheat_agent])
print(f"✅ Local validation pass! Final Rewards: {[s['reward'] for s in env.steps[-1]]}")
