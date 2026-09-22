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

from IPython.display import Image, display

display(Image("/kaggle/input/datasets/chaimaamatrag/description/description.png"))

buy_count = 0
plant_count = 0
water_count = 0
harvest_count = 0
sell_count = 0
max_wheat_plants = 0
movement_count = 0

max_wheat_positions = 0
last_empty_positions = []
last_plant_positions = []

movement_same_target = 0

long_move_count = 0


last_farmer_position = None
last_nearest_target = None
last_nearest_distance = None
last_move = None

current_target = None
current_target_type = None

visited_positions = set()

def agent(obs):
    global buy_count, plant_count, water_count
    global harvest_count, sell_count, max_wheat_plants

    global max_wheat_positions
    global last_empty_positions, last_plant_positions
    
    global last_farmer_position, last_nearest_target, last_nearest_distance
    global last_move
    global movement_count
    global movement_same_target
    global long_move_count

    global current_target, current_target_type
    # who Im a
    player = obs["player"]
    me = obs["farms"][player]
    
    private = obs["private"] # my privte information about seeds etc ..
    fx, fy = me["farmer"]  # cordinates of my farmer 
    if obs["step"] < 10:
        print("STEP", obs["step"], "FARMER", (fx, fy))
    visited_positions.add((fx, fy))
    tile = me["tiles"][fy][fx]

    market = [] # empty list of market actions. Later the agent can add things
    prices = obs["market"]["prices"]
    
    wheat_price = prices["WHEAT"]
    wheat_in_shed = private["shed"].get("WHEAT", 0)
    wheat_plants = 0

    for row in me["tiles"]:
        for cell in row:
            if (isinstance(cell, dict) 
                and cell.get("kind") == "PLANT" 
                and cell.get("crop") == "WHEAT"):
                wheat_plants += 1
            
    if wheat_plants > max_wheat_plants:
        max_wheat_plants = wheat_plants

    # Diagnostic: record exactly which tiles are empty and which contain wheat
    empty_positions = []
    plant_positions = []

    for y, row in enumerate(me["tiles"]):
        for x, cell in enumerate(row):
            if cell is None:
                empty_positions.append((x, y))
            elif (
                isinstance(cell, dict)
                and cell.get("kind") == "PLANT"
                and cell.get("crop") == "WHEAT"
            ):
                plant_positions.append((x, y))

    last_empty_positions = empty_positions
    last_plant_positions = plant_positions

    if len(plant_positions) > max_wheat_positions:
        max_wheat_positions = len(plant_positions)

    
        
    print("Wheat plants:", wheat_plants)

# Buy a wheat seed if we have none and have enough money
    TARGET_WHEAT_PLANTS = len(me["tiles"]) * len(me["tiles"][0])  # fill every real tile, not a guessed cap
    
    
    # Buy WHEAT seeds when we have fewer than 16 wheat plants.
    if ( 
        private["seeds"].get("WHEAT", 0) == 0 
        and me["money"] >= 10
        and wheat_plants < TARGET_WHEAT_PLANTS):
        buy_count += 1
        market.append(["BUY_SEED", "WHEAT", 1])
        

    # Sell any wheat sitting in the shed
    wheat_in_shed = private["shed"].get("WHEAT", 0)
    WHEAT_BASE_PRICE =25  # from the infographic's "Base Market Price" table
    WHEAT_PRICE_PERCENT = 95

    wheat_sell_price = WHEAT_BASE_PRICE * (1 + WHEAT_PRICE_PERCENT / 100)
    
    if wheat_in_shed > 0 and  wheat_price >= wheat_sell_price:
        print(f"Day {obs['day']} Hour {obs['hour']} — wheat_price={wheat_price}, wheat_in_shed={wheat_in_shed}")
        sell_count += wheat_in_shed
        market.append(["SELL", "WHEAT", wheat_in_shed])


    # If standing on an empty tile, plant wheat
    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        plant_count += 1
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}

    

    # If standing on a plant, manage watering and harvesting
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 2:
            harvest_count += 1
            return {"farmer": ["HARVEST"], "hands": [], "market": market}

        
        if not tile["watered_today"]:
            water_count += 1
            return {"farmer": ["WATER"], "hands": [], "market": market}

    ## Find the nearest useful tiles
    nearest_harvest = None
    nearest_harvest_distance = float("inf")
        
    nearest_water = None
    nearest_water_distance = float("inf")
        
    nearest_empty = None
    nearest_empty_distance = float("inf")
    
    for y, row in enumerate(me["tiles"]):
        for x, cell in enumerate(row):
        
            distance = abs(x - fx) + abs(y - fy)
        
            if cell is None:
                if distance < nearest_empty_distance:
                    nearest_empty_distance = distance
                    nearest_empty = ("EMPTY", x, y)
        
            elif isinstance(cell, dict) and cell.get("kind") == "PLANT":
                crop_age = obs["day"] - cell["planted_day"]
        
                if crop_age >= 2:
                    if distance < nearest_harvest_distance:
                        nearest_harvest_distance = distance
                        nearest_harvest = ("HARVEST", x, y)
                            
        
                elif not cell["watered_today"]:
                    if distance < nearest_water_distance:
                        nearest_water_distance = distance
                        nearest_water = ("WATER", x, y)
        

    # V2.3 movement priority
    
    if nearest_harvest is not None:
        # Highest priority: harvest ready wheat
        nearest_target = nearest_harvest
        nearest_distance = nearest_harvest_distance
    
    elif nearest_water is not None:
        # Second priority: water dry wheat
        nearest_target = nearest_water
        nearest_distance = nearest_water_distance
    
    elif wheat_plants < TARGET_WHEAT_PLANTS and nearest_empty is not None:
        # Third priority: expand the farm if we still need plants
        nearest_target = nearest_empty
        nearest_distance = nearest_empty_distance
    
    else:
        # Nothing urgent: keep the old fallback
        nearest_target = nearest_empty
        nearest_distance = nearest_empty_distance
    

    
    if obs["step"] < 10:
        print(
            "STEP", obs["step"],
            "TARGET", nearest_target,
            "DIST", nearest_distance
        )
                    
    move = "PASS"
    if nearest_target is not None:
        target_type, tx, ty = nearest_target
    
        if tx > fx:
            move = "EAST"
        elif tx < fx:
            move = "WEST"
        elif ty > fy:
            move = "SOUTH"
        elif ty < fy:
            move = "NORTH"
   
    if move in ["NORTH", "SOUTH", "EAST", "WEST"]:
        movement_count += 1

    if move in ["NORTH", "SOUTH", "EAST", "WEST"] and nearest_distance > 1:
        long_move_count += 1
        
    last_move = move

    last_farmer_position = (fx, fy)
    last_nearest_target = nearest_target
    last_nearest_distance = nearest_distance

    if last_nearest_target == nearest_target:
        movement_same_target += 1
    
    return {"farmer": [move], "hands": [], "market": market}

from kaggle_environments import make

def run_trials(n=5, steps=720):
    global buy_count, plant_count, water_count
    global harvest_count, sell_count, max_wheat_plants
    global visited_positions
    global last_farmer_position, last_nearest_target, last_nearest_distance
    global last_move
    
    buy_count = 0
    plant_count = 0
    water_count = 0
    harvest_count = 0
    sell_count = 0
    max_wheat_plants = 0
    visited_positions = set()
    
    last_farmer_position = None
    last_nearest_target = None
    last_nearest_distance = None
    last_move = None
    results = []

    for i in range(n):
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": steps},
            debug=False
        )

        env.run([agent, "random"])

        final = env.steps[-1]
        us, them = final[0].reward, final[1].reward

        results.append((us, them))
        print(f"Trial {i+1}: us={us}, them={them}")

    avg_us = sum(r[0] for r in results) / n
    avg_them = sum(r[1] for r in results) / n

    print(f"\nAverage over {n} trials — us: {avg_us:.1f}, them: {avg_them:.1f}")


run_trials(n=30, steps=720)

print("\n===== DIAGNOSTICS =====")
print("Seeds bought:", buy_count)
print("Wheat planted:", plant_count)
print("Wheat watered:", water_count)
print("Harvest actions:", harvest_count)
print("Wheat units sold:", sell_count)
print("Max wheat plants:", max_wheat_plants)
print("Positions visited:", len(visited_positions))
print("Visited:", sorted(visited_positions))
print("Farmer:", last_farmer_position)

print("Suggested move:", last_move)
print("Farmer:", last_farmer_position)
print("Nearest target:", last_nearest_target)
print("Distance:", last_nearest_distance)
print("Movement actions:", movement_count)

print("Max wheat positions:", max_wheat_positions)
print("Final empty positions:", sorted(last_empty_positions))
print("Final wheat positions:", sorted(last_plant_positions))
print("Movement actions:", movement_count)
print("Long-distance movement actions:", long_move_count)

print("=======================")

from kaggle_environments import make

def run_trials(n=5, steps=720):
    results = []
    for i in range(n):
        env = make("kaggriculture", configuration={"episodeSteps": steps}, debug=False)
        env.run([agent, "random"])
        final = env.steps[-1]
        us, them = final[0].reward, final[1].reward
        results.append((us, them))
        print(f"Trial {i+1}: us={us}, them={them}")
    avg_us = sum(r[0] for r in results) / n
    avg_them = sum(r[1] for r in results) / n
    print(f"\nAverage over {n} trials — us: {avg_us:.1f}, them: {avg_them:.1f}")

run_trials()

import inspect

source = inspect.getsource(agent)

# Remove diagnostic-only lines from the submission
lines = source.splitlines()

clean_lines = []

for line in lines:
    stripped = line.strip()

    if stripped.startswith("global "):
        continue

    if "buy_count" in stripped:
        continue

    if "plant_count" in stripped:
        continue

    if "water_count" in stripped:
        continue

    if "harvest_count" in stripped:
        continue

    if "sell_count" in stripped:
        continue

    if "max_wheat_plants" in stripped:
        continue

    if "last_move" in stripped:
        continue

    if "last_farmer_position" in stripped:
        continue

    if "last_nearest_target" in stripped:
        continue

    if "last_nearest_distance" in stripped:
        continue

    if "visited_positions" in stripped:
        continue

    clean_lines.append(line)

with open("submission.py", "w") as f:
    f.write("\n".join(clean_lines))

print(open("submission.py").read())