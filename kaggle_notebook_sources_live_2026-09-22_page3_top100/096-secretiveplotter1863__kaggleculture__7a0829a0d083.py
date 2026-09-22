
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))


import kagglehub
from kaggle_environments import make


def agent(observation):
    player_id=observation["player"]
    my_farm=observation["farms"][player_id]
    private_data=observation["private"]
    money=my_farm["money"]
    farmer_x, farmer_y = my_farm["farmer"]
    current_tile = my_farm["tiles"][farmer_y][farmer_x]
    seeds=private_data["seeds"]
    market_orders = []
    farmer_action=["PASS"]
    # Wheat Seeds
    if seeds.get("WHEAT",0)==0 and money>=10:
        market_orders.append(
            ["BUY_SEED","WHEAT",1]
        )
    #wheat planting
    if seeds["WHEAT"]!=0 and current_tile is None:
        farmer_action=["PLANT","WHEAT"]
    #wheat watering
    if (
        isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT" and current_tile.get("watered_today") is False
    ):
        farmer_action=["WATER"]

    #harvest
    if ( isinstance(current_tile,dict) and current_tile.get("kind") == "PLANT" and current_tile.get("crop")=="WHEAT" and current_tile.get("watered_today") is True  ):
        crop_age= observation["day"] - current_tile.get("planted_day",observation["day"])
        if(crop_age>=2):
            farmer_action=["HARVEST"]

    #SELL
    wheat_in_shed = private_data["shed"].get("WHEAT", 0)

    if wheat_in_shed > 0:
        market_orders.append(
            ["SELL", "WHEAT", wheat_in_shed]
        )
     
    # Send decisions to the environment.
    return {
        "farmer":farmer_action,
        "hands":[],
        "market":market_orders,
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 100,
        "seed": 42,
    },
    debug=False,
)

env.run([agent, "random"])[-1]


print(env.steps[0][0]["observation"].keys())
print(type(env.steps[0][0]["observation"]["farms"]))
print(env.steps[4][0]["observation"]["farms"][0]["money"])

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run([agent, "random"])  # or env.run(["main.py", "random"]) to load from a file

# View result
final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")

# Render in a notebook
env.render(mode="ipython", width=1200, height=800)

# Or dump a replay JSON for the visualizer / offline analysis
import json
with open("replay.json", "w") as f:
    json.dump(env.toJSON(), f)
