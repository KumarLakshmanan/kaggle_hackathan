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

%%writefile main.py
import math
from typing import Dict, List, Any, Tuple

# --- 1. HELPER FUNCTIONS ---

def distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_move_direction(current: Tuple[int, int], target: Tuple[int, int]) -> str:
    cx, cy = current
    tx, ty = target
    if cx < tx: return "EAST"
    if cx > tx: return "WEST"
    if cy < ty: return "SOUTH"
    if cy > ty: return "NORTH"
    return "PASS"

def scan_farm_grid(tiles: List[List[Any]]) -> Dict[str, List[Tuple[int, int]]]:
    scan_results = {
        "unwatered_crops": [],
        "harvestable_crops": [],
        "unfed_animals": [],
        "harvestable_animals": [],
        "empty_tiles": [],
        "weeds": []
    }
    grid_size = len(tiles)
    for y in range(grid_size):
        for x in range(grid_size):
            tile = tiles[y][x]
            pos = (x, y)
            if tile is None:
                scan_results["empty_tiles"].append(pos)
                continue
            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    scan_results["weeds"].append(pos)
                elif kind == "PLANT":
                    if not tile.get("watered_today", False):
                        scan_results["unwatered_crops"].append(pos)
                    if tile.get("yield_units", 0) > 0:
                        scan_results["harvestable_crops"].append(pos)
                elif kind in ("COOP", "PASTURE") and tile.get("animal") is not None:
                    if not tile.get("fed_today", False):
                        scan_results["unfed_animals"].append(pos)
                    if tile.get("yield_units", 0) > 0:
                        scan_results["harvestable_animals"].append(pos)
    return scan_results

def generate_market_orders(obs: Dict[str, Any], min_sell_price: int = 5, max_sell_qty: int = 5) -> List[List[Any]]:
    orders = []
    my_shed = obs["private"]["shed"]
    my_seeds = obs["private"]["seeds"]
    prices = obs["market"]["prices"]
    money = obs["farms"][obs["player"]]["money"]
    
    # 1. Sell produce
    sellable_items = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]
    for item in sellable_items:
        qty_in_shed = my_shed.get(item, 0)
        current_price = prices.get(item, 0)
        if qty_in_shed > 0 and current_price >= min_sell_price:
            qty_to_sell = min(qty_in_shed, max_sell_qty)
            orders.append(["SELL", item, qty_to_sell])
            
    # 2. Buy basic seeds
    if money >= 50 and my_seeds.get("WHEAT", 0) < 5:
        orders.append(["BUY_SEED", "WHEAT", 5])
        
    return orders[:10]

# --- 2. MAIN AGENT ENTRYPOINT ---

def my_agent(obs: Dict[str, Any], configuration: Dict[str, Any] = None) -> Dict[str, List]:
    """
    Kaggle Simulation Runner Entrypoint
    """
    player_id = obs["player"]
    my_farm = obs["farms"][player_id]
    my_seeds = obs["private"]["seeds"]
    farmer_pos = tuple(my_farm["farmer"])
    hands_pos = [tuple(h) for h in my_farm.get("hands", [])]
    
    # Scan environment
    scan = scan_farm_grid(my_farm["tiles"])
    
    # Determine Farmer Movement/Action
    farmer_cmd = "PASS"
    wheat_seeds = my_seeds.get("WHEAT", 0)
    
    if scan["unwatered_crops"]:
        target = min(scan["unwatered_crops"], key=lambda p: distance(farmer_pos, p))
        farmer_cmd = "WATER" if farmer_pos == target else get_move_direction(farmer_pos, target)
    elif scan["harvestable_crops"]:
        target = min(scan["harvestable_crops"], key=lambda p: distance(farmer_pos, p))
        farmer_cmd = "HARVEST" if farmer_pos == target else get_move_direction(farmer_pos, target)
    elif scan["empty_tiles"] and wheat_seeds > 0:
        target = min(scan["empty_tiles"], key=lambda p: distance(farmer_pos, p))
        farmer_cmd = "PLANT WHEAT" if farmer_pos == target else get_move_direction(farmer_pos, target)
        
    farmer_actions = [farmer_cmd] + ["PASS" for _ in hands_pos]
    market_actions = generate_market_orders(obs)
    
    return {
        "farmer": farmer_actions,
        "market": market_actions
    }

import sys
# Force python to refresh imported modules from disk
if 'main' in sys.modules:
    del sys.modules['main']

from kaggle_environments import make
from main import my_agent

# Run 50 turns simulation match
env = make("kaggriculture", configuration={"episodeSteps": 50}, debug=True)
env.run([my_agent, "random"])

print("\n=== MATCH RESULTS ===")
print(f"Agent Money : ${env.state[0]['reward']}")
print(f"Random Bot  : ${env.state[1]['reward']}")

from kaggle_environments import make
from typing import Dict, List, Any, Tuple
import math

# ==========================================
# VERSION 1 AGENT (Baseline Machine)
# ==========================================
def v1_agent(obs: Dict[str, Any], configuration: Dict[str, Any] = None) -> Dict[str, List]:
    player_id = obs["player"]
    my_farm = obs["farms"][player_id]
    my_seeds = obs["private"]["seeds"]
    my_shed = obs["private"]["shed"]
    farmer_pos = tuple(my_farm["farmer"])
    hands_pos = [tuple(h) for h in my_farm.get("hands", [])]
    
    # 1. Scan grid
    unwatered, harvestable, empty = [], [], []
    tiles = my_farm["tiles"]
    grid_size = len(tiles)
    for y in range(grid_size):
        for x in range(grid_size):
            tile = tiles[y][x]
            pos = (x, y)
            if tile is None:
                empty.append(pos)
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if not tile.get("watered_today", False):
                    unwatered.append(pos)
                if tile.get("yield_units", 0) > 0:
                    harvestable.append(pos)

    # 2. Farmer movement priority
    farmer_cmd = "PASS"
    wheat_seeds = my_seeds.get("WHEAT", 0)
    
    def dist(p1, p2): return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
    def move(curr, tgt):
        if curr[0] < tgt[0]: return "EAST"
        if curr[0] > tgt[0]: return "WEST"
        if curr[1] < tgt[1]: return "SOUTH"
        if curr[1] > tgt[1]: return "NORTH"
        return "PASS"

    if unwatered:
        target = min(unwatered, key=lambda p: dist(farmer_pos, p))
        farmer_cmd = "WATER" if farmer_pos == target else move(farmer_pos, target)
    elif harvestable:
        target = min(harvestable, key=lambda p: dist(harvestable, key=lambda p: dist(farmer_pos, p)))
        farmer_cmd = "HARVEST" if farmer_pos == target else move(farmer_pos, target)
    elif empty and wheat_seeds > 0:
        target = min(empty, key=lambda p: dist(farmer_pos, p))
        farmer_cmd = "PLANT WHEAT" if farmer_pos == target else move(farmer_pos, target)
        
    farmer_actions = [farmer_cmd] + ["PASS" for _ in hands_pos]

    # 3. Basic Market Selling & Buying
    market_actions = []
    prices = obs["market"]["prices"]
    money = my_farm["money"]
    
    for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        qty = my_shed.get(item, 0)
        if qty > 0 and prices.get(item, 0) >= 5:
            market_actions.append(["SELL", item, min(qty, 5)])
            
    if money >= 50 and wheat_seeds < 5:
        market_actions.append(["BUY_SEED", "WHEAT", 5])
        
    return {"farmer": farmer_actions, "market": market_actions[:10]}


# ==========================================
# VERSION 2 AGENT (Town Demand + Paced Engine + HIRE)
# ==========================================
def v2_agent(obs: Dict[str, Any], configuration: Dict[str, Any] = None) -> Dict[str, List]:
    player_id = obs["player"]
    my_farm = obs["farms"][player_id]
    my_seeds = obs["private"]["seeds"]
    my_shed = obs["private"]["shed"]
    market_prices = obs["market"]["prices"]
    market_inv = obs["market"]["inventory"]
    unlocked_shops = obs.get("town", {}).get("unlocked_shops", [])
    money = my_farm["money"]
    hires_today = my_farm.get("hires_today", 0)

    farmer_pos = tuple(my_farm["farmer"])
    hands_pos = [tuple(h) for h in my_farm.get("hands", [])]

    # 1. Dynamic Crop Target Selector based on Town Shops
    target_crop = "WHEAT"
    target_seed = "WHEAT"
    
    if "ICE_CREAM_SHOP" in unlocked_shops or "SMOOTHIE_SHOP" in unlocked_shops:
        if market_prices.get("STRAWBERRY", 0) > 40:
            target_crop, target_seed = "STRAWBERRY", "STRAWBERRY"
    elif "PIZZA_SHOP" in unlocked_shops or "FARMERS_MARKET" in unlocked_shops:
        if market_prices.get("TOMATO", 0) > 25:
            target_crop, target_seed = "TOMATO", "TOMATO"

    # 2. Grid Scan
    unwatered, harvestable, empty = [], [], []
    tiles = my_farm["tiles"]
    grid_size = len(tiles)
    for y in range(grid_size):
        for x in range(grid_size):
            tile = tiles[y][x]
            pos = (x, y)
            if tile is None:
                empty.append(pos)
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if not tile.get("watered_today", False):
                    unwatered.append(pos)
                if tile.get("yield_units", 0) > 0:
                    harvestable.append(pos)

    def dist(p1, p2): return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
    def move(curr, tgt):
        if curr[0] < tgt[0]: return "EAST"
        if curr[0] > tgt[0]: return "WEST"
        if curr[1] < tgt[1]: return "SOUTH"
        if curr[1] > tgt[1]: return "NORTH"
        return "PASS"

    # 3. Priority Unit Allocator (Farmer & Hired Hands)
    farmer_cmd = "PASS"
    crop_seeds = my_seeds.get(target_seed, 0)

    if unwatered:
        target = min(unwatered, key=lambda p: dist(farmer_pos, p))
        farmer_cmd = "WATER" if farmer_pos == target else move(farmer_pos, target)
    elif harvestable:
        target = min(harvestable, key=lambda p: dist(farmer_pos, p))
        farmer_cmd = "HARVEST" if farmer_pos == target else move(farmer_pos, target)
    elif empty and crop_seeds > 0:
        target = min(empty, key=lambda p: dist(farmer_pos, p))
        farmer_cmd = f"PLANT {target_seed}" if farmer_pos == target else move(farmer_pos, target)

    farmer_actions = [farmer_cmd] + ["PASS" for _ in hands_pos]

    # 4. Market Pacing & HIRE Decision Engine
    market_actions = []

    # Hire 1 farm hand if workload is heavy and cost is minimal ($1)
    total_urgent = len(unwatered) + len(harvestable)
    if hires_today == 0 and total_urgent >= 5 and money >= 300:
        market_actions.append(["HIRE", 1])

    # Sell produce with price pacing
    for item in ["STRAWBERRY", "TOMATO", "WHEAT", "CARROT", "MELON"]:
        qty = my_shed.get(item, 0)
        curr_price = market_prices.get(item, 0)
        if qty > 0 and curr_price >= 8:
            # Paced sales cap to prevent market crashes
            sell_qty = min(qty, 4)
            market_actions.append(["SELL", item, sell_qty])

    # Replenish target seeds
    if money >= 100 and crop_seeds < 5:
        market_actions.append(["BUY_SEED", target_seed, 5])

    return {"farmer": farmer_actions, "market": market_actions[:10]}

# Full 30-day season simulation test
env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run([my_agent, "random"])

print("\n=== FULL 720-TURN MATCH RESULTS ===")
print(f"Agent Final Money : ${env.state[0]['reward']}")
print(f"Random Bot Money  : ${env.state[1]['reward']}")

import time

print("🚀 Starting 720-Turn Match: Agent V1 vs Agent V2...")
start_time = time.time()

# Create standard 720-step Kaggriculture environment
env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=False)

# Run V1 (Player 0) vs V2 (Player 1)
env.run([v1_agent, v2_agent])

elapsed_time = time.time() - start_time

# Extract final rewards (Bank Balance)
v1_final_bank = env.state[0]["reward"]
v2_final_bank = env.state[1]["reward"]

# Determine Winner & Margin
margin = abs(v2_final_bank - v1_final_bank)
winner = "Agent V2" if v2_final_bank > v1_final_bank else ("Agent V1" if v1_final_bank > v2_final_bank else "Tie")

print("\n" + "="*45)
print("📊 BENCHMARK MATCH RESULTS (720 TURNS / 30 DAYS)")
print("="*45)
print(f"🥇 Winner               : {winner}")
print(f"💰 Agent V1 Final Money : ${v1_final_bank:,.2f}")
print(f"💰 Agent V2 Final Money : ${v2_final_bank:,.2f}")
print(f"📈 Profit Difference    : ${margin:,.2f}")
print(f"⏱️ Match Runtime       : {elapsed_time:.2f} seconds")
print("="*45)

import pandas as pd
import matplotlib.pyplot as plt

# Extract turn-by-turn rewards from environment history
v1_history = [step[0]["reward"] for step in env.steps]
v2_history = [step[1]["reward"] for step in env.steps]
turns = list(range(len(v1_history)))

plt.figure(figsize=(12, 5))
plt.plot(turns, v1_history, label="Agent V1 (Baseline)", color="red", linestyle="--")
plt.plot(turns, v2_history, label="Agent V2 (Town Demand + HIRE)", color="green", linewidth=2)
plt.title("Kaggriculture Benchmark: 720-Turn Season Comparison", fontsize=14)
plt.xlabel("Turns (Hour of Season)", fontsize=12)
plt.ylabel("Bank Balance ($)", fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

import tarfile

# Compress main.py into submission.tar.gz
with tarfile.open("submission.tar.gz", "w:gz") as tar:
    tar.add("main.py")

print("submission.tar.gz created successfully!")