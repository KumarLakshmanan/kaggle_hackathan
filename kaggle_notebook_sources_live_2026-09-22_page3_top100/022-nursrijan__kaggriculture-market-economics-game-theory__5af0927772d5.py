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

# Professional academic plot aesthetic
sns.set_theme(style="ticks", palette="deep")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 140
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

import kaggle_environments
from kaggle_environments import make

print(f"Environment Version: {kaggle_environments.__version__}")


# Mathematical Demonstration: Micro-Batch Revenue vs. Single-Dump Price Collapse

def simulate_melon_sale_revenue(batch_sizes, total_units=60, base_price=250, I0=10000, T_calib=300):
    target_above = 3.60
    
    def price_fn(inv):
        diff = inv - I0
        if diff <= 0:
            return base_price
        f_val = diff ** 2
        f_T = T_calib ** 2
        amp = (target_above * base_price) / f_T
        return max(1, round(base_price - amp * f_val))

    results = []
    for b in batch_sizes:
        curr_inv = I0
        total_rev = 0
        units_left = total_units
        price_history = []
        
        while units_left > 0:
            sell_q = min(units_left, b)
            batch_rev = 0
            for _ in range(sell_q):
                p = price_fn(curr_inv)
                batch_rev += p
                curr_inv += 1
                price_history.append(p)
            total_rev += batch_rev
            units_left -= sell_q
            
        results.append({
            "Batch Size": b,
            "Total Revenue ($)": total_rev,
            "Effective Price / Unit ($)": total_rev / total_units,
            "Min Price Reached ($)": min(price_history)
        })
        
    return pd.DataFrame(results)

df_sim = simulate_melon_sale_revenue(batch_sizes=[1, 5, 10, 20, 60], total_units=60)
print("=== SIMULATION: MELON SALE REVENUE VS BATCH SIZE ===")
print(df_sim.to_string(index=False))

# Plot Effective Unit Price vs Batch Size
plt.figure(figsize=(9, 4.5))
plt.plot(df_sim["Batch Size"], df_sim["Effective Price / Unit ($)"], marker='o', linewidth=2.2, color='#1f77b4')
plt.axhline(250, color='gray', linestyle='--', label='Base Price ($250)')
plt.axhline(1, color='red', linestyle=':', label='Price Floor ($1)')
plt.title("Effect of Batch Order Sizing on Realized Unit Price (60 Melons)", fontsize=12, fontweight='bold')
plt.xlabel("Order Batch Size (Units / Order)", fontsize=10)
plt.ylabel("Realized Price per Unit ($)", fontsize=10)
plt.legend(frameon=True)
plt.tight_layout()
plt.show()


# Plot Capital Yield Rate Comparison across crops
crops = ['Wheat', 'Carrot', 'Tomato', 'Strawberry', 'Melon']
cyr_values = [70.0, 60.0, 23.75, 38.0, 142.0]
colors = ['#2ca02c', '#ff7f0e', '#d62728', '#e377c2', '#9467bd']

plt.figure(figsize=(9, 4.5))
bars = plt.bar(crops, cyr_values, color=colors, width=0.55, edgecolor='black', linewidth=0.8)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 3, f"${yval:.2f}/day", ha='center', va='bottom', fontweight='bold')

plt.title("Daily Capital Yield Rate ($CYR$) Comparison per Tile", fontsize=12, fontweight='bold')
plt.ylabel("Net Profit per Tile-Day ($)", fontsize=10)
plt.ylim(0, 165)
plt.tight_layout()
plt.show()


def grandmaster_v4_agent(obs):
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

    if day <= 16:
        primary_crop = "MELON"
        seed_cost = 80
    elif day <= 24:
        primary_crop = "TOMATO" if money > 100 else "CARROT"
        seed_cost = 50 if primary_crop == "TOMATO" else 20
    else:
        primary_crop = "CARROT" if money > 40 else "WHEAT"
        seed_cost = 20 if primary_crop == "CARROT" else 10

    hires_today = me["hires_today"]
    target_hands = 5 if day < 10 else (7 if day < 25 else 3)
    if hires_today < target_hands and money >= 10:
        next_cost = 1 if hires_today < 2 else (2 if hires_today == 2 else (3 if hires_today == 3 else 5))
        if money >= next_cost + 20:
            market_orders.append(["HIRE", 1])

    melon_seeds = private["seeds"].get("MELON", 0)
    wheat_seeds = private["seeds"].get("WHEAT", 0)
    carrot_seeds = private["seeds"].get("CARROT", 0)

    if day <= 16 and melon_seeds < 8 and money >= 400:
        market_orders.append(["BUY_SEED", "MELON", 4])
    if wheat_seeds < 4 and money >= 40:
        market_orders.append(["BUY_SEED", "WHEAT", 4])
    if carrot_seeds < 3 and money >= 60:
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
            else:
                if item == "MELON":
                    if item_price > 120:
                        batch = min(qty, 6)
                        market_orders.append(["SELL", item, batch])
                elif item in ["STRAWBERRY", "MILK", "WOOL"]:
                    if item_price > 50:
                        batch = min(qty, 4)
                        market_orders.append(["SELL", item, batch])
                else:
                    if item_price > 1:
                        batch = min(qty, 10)
                        market_orders.append(["SELL", item, batch])

    assigned_targets = set()

    def get_action_for_unit(ux, uy):
        current_tile = tiles[uy][ux]

        if (ux, uy) not in assigned_targets:
            if isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
                return (ux, uy), ["DIG"]
            
            if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
                crop = current_tile["crop"]
                crop_age = day - current_tile["planted_day"]
                first_yield = CROP_SPECS.get(crop, (10, 2, 4, 24))[1]
                
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
                        crop = t_state.get("crop")
                        crop_age = day - t_state.get("planted_day", day)
                        first_yield = CROP_SPECS.get(crop, (10, 2, 4, 24))[1]
                        if crop_age >= first_yield or not t_state.get("watered_today", False):
                            return (cx, cy), [path[0]]

            for nx, ny, d_name in [(cx, cy - 1, "NORTH"), (cx, cy + 1, "SOUTH"), (cx + 1, cy, "EAST"), (cx - 1, cy, "WEST")]:
                if 0 <= nx < 10 and 0 <= ny < 10:
                    if tiles[ny][nx] != "LOCKED" and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [d_name]))
        return None, ["PASS"]

    f_target, f_act = get_action_for_unit(fx, fy)
    if f_target: assigned_targets.add(f_target)
    farmer_action = f_act

    hands_actions = []
    for h_pos in hands:
        hx, hy = h_pos
        h_target, h_act = get_action_for_unit(hx, hy)
        if h_target: assigned_targets.add(h_target)
        hands_actions.append(h_act)

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market_orders
    }


def starter_wheat_agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]
    market = []

    if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])
    wheat_in_shed = private["shed"].get("WHEAT", 0)
    if wheat_in_shed > 0:
        market.append(["SELL", "WHEAT", wheat_in_shed])

    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 2:
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile.get("watered_today", False):
            return {"farmer": ["WATER"], "hands": [], "market": market}

    return {"farmer": ["PASS"], "hands": [], "market": market}

# Run 3-episode validation tournament
env = make("kaggriculture", debug=False)
results = []

print("🚀 Running Validation Tournament...")
for ep in range(3):
    env.reset()
    env.run([grandmaster_v4_agent, starter_wheat_agent])
    step = env.steps[-1]
    p0_score = step[0]['observation']['farms'][0]['money']
    p1_score = step[1]['observation']['farms'][1]['money']
    results.append({"Episode": ep + 1, "GrandMaster-v4 ($)": p0_score, "Starter Baseline ($)": p1_score})

df_res = pd.DataFrame(results)
print("\nTournament Results:")
print(df_res.to_string(index=False))

plt.figure(figsize=(8, 4))
sns.barplot(data=df_res.melt(id_vars=["Episode"], var_name="Agent", value_name="Final Coins ($)"), x="Episode", y="Final Coins ($)", hue="Agent")
plt.title("Validation Tournament Score Comparison", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()


agent_export_code = """
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
"""

with open("main.py", "w") as f:
    f.write(agent_export_code.strip())

print("✅ Exported main.py successfully!")
