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

import numpy as np 
import pandas as pd 
import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

import kagglehub

!pip install -U -q kaggle-environments
import json
from kaggle_environments import make
print("Kaggle Environments successfully imported and ready!")

%%writefile submission.py
import math

FIB_COSTS = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597]

PATROL_ROUTES = {
    0: [(6,6), (7,6), (8, 6), (8, 7), (7, 7), (6, 7)],
    1: [(6,8), (7, 8), (8, 8), (8, 9), (7, 9), (6, 9)]
}

def get_hire_cost(hires_today, extra_hands):
    start_idx = hires_today + 1
    end_idx = start_idx + extra_hands
    if end_idx > len(FIB_COSTS):
        return float('inf')
    return sum(FIB_COSTS[start_idx:end_idx])

def execute_town_shop_arbitrage(obs, private_state):
    market_actions = []
    shed = private_state.get("shed", {})
    hour = obs.get("hour", 0)
    is_demand_window = (hour % 4 == 0)
    
    priority = {
        "MELON": 0, "MILK": 1, "WOOL": 2, "STRAWBERRY": 3, 
        "TOMATO": 4, "CARROT": 5, "WHEAT": 6, "EGG": 7
    }
    
    for item, amount in shed.items():
        if amount <= 0: continue
        is_premium = priority.get(item, 99) <= 3
        if is_premium and not is_demand_window: continue
        market_actions.append(["SELL", item, amount])
        
    market_actions.sort(key=lambda cmd: priority.get(cmd[1], 99) if cmd[0] == "SELL" else 100)
    return market_actions

def manage_labor_and_liquidity(obs, target_hands):
    player_id = obs.get("player")
    my_farm = obs.get("farms", [])[player_id]
    available_capital = my_farm.get("money", 0) - 2000
    
    if available_capital <= 0:
        return []
        
    hands_to_hire = 0
    hires_today = my_farm.get("hires_today", 0)
    
    for i in range(1, target_hands + 1):
        cost = get_hire_cost(hires_today, i)
        if cost > available_capital:
            break
        hands_to_hire = i
        
    return ["HIRE"] * hands_to_hire

def get_hand_action(hand_id, current_pos, me_state):
    hx, hy = current_pos
    tile = me_state.get("tiles", [])[hy][hx]
    
    if isinstance(tile, dict) and tile.get("kind") in ["COOP", "PASTURE"]:
        if not tile.get("fed_today"): return ["FEED"]
        if not tile.get("cared_today"): return ["CARE"]
        
    route = PATROL_ROUTES.get(hand_id, [])
    if not route: return ["PASS"]
    
    if current_pos in route:
        current_idx = route.index(current_pos)
        next_target = route[(current_idx + 1) % len(route)]
    else:
        next_target = route[0]
        
    tx, ty = next_target
    if tx > hx: return ["MOVE", "E"]
    if tx < hx: return ["MOVE", "W"]
    if ty > hy: return ["MOVE", "S"]
    if ty < hy: return ["MOVE", "N"]
    
    return ["PASS"]

def agent(obs, config=None):
    my_farm = obs.get("farms", [])[obs.get("player")]
    private_state = obs.get("private", {})
    current_day = obs.get("day", 0)
    
    if current_day >= 29:
        market_queue = [["SELL", item, amt] for item, amt in private_state.get("shed", {}).items() if amt > 0]
        return {
            "farmer": ["PASS"],
            "hands": ["PASS"] * len(my_farm.get("hands", [])),
            "market": market_queue
        }
        
    market_queue = execute_town_shop_arbitrage(obs, private_state)
    if private_state.get("seeds", {}).get("WHEAT", 0) < 10:
        market_queue.append(["BUY_SEED", "WHEAT", 5])
        
    market_queue.extend(manage_labor_and_liquidity(obs, 2))
    
    hand_actions = []
    for i, hand_coords in enumerate(my_farm.get("hands", [])):
        if current_day >= 27:
            hand_actions.append(["PASS"])
        else:
            hand_actions.append(get_hand_action(i, hand_coords, my_farm))

    return {
        "farmer": ["PASS"], 
        "hands": hand_actions, 
        "market": market_queue
    }

env = make("kaggriculture", debug=True)
env.run(["submission.py", "random"])
env.render(mode="html")