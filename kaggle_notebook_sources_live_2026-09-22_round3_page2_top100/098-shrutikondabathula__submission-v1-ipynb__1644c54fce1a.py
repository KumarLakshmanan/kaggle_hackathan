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

%%writefile submission.py
# ===========================================
# Crop priorities
# ===========================================

def crop_score(state, crop):

    day = state["day"]

    if day < 5:

        table = {
            "WHEAT":100,
            "CARROT":90,
            "TOMATO":70,
            "STRAWBERRY":40,
            "MELON":20
        }

    elif day < 15:

        table = {
            "WHEAT":40,
            "CARROT":60,
            "TOMATO":80,
            "STRAWBERRY":90,
            "MELON":100
        }

    else:

        table = {
            "WHEAT":10,
            "CARROT":20,
            "TOMATO":60,
            "STRAWBERRY":90,
            "MELON":120
        }

    return table[crop]

# ===========================================
# Base Action Scores
# ===========================================

ACTION_PRIORITY = {
    "HARVEST": 1000,
    "WATER": 600,
    "PLANT": 400,
    "DIG": 150,
    "PASS": 0
}

DISTANCE_COST = 4

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def step_toward(start, goal):

    sx, sy = start
    gx, gy = goal

    if gx > sx:
        return "EAST"

    if gx < sx:
        return "WEST"

    if gy > sy:
        return "SOUTH"

    if gy < sy:
        return "NORTH"

    return "PASS"

def analyze_state(obs):

    player = obs["player"]

    farm = obs["farms"][player]

    state = {}

    state["player"] = player

    state["day"] = obs["day"]

    state["hour"] = obs["hour"]

    state["farm"] = farm

    state["tiles"] = farm["tiles"]

    state["farmer"] = tuple(farm["farmer"])

    state["money"] = farm["money"]

    state["hands"] = farm["hands"]

    state["private"] = obs["private"]

    state["market"] = obs["market"]

    state["town"] = obs["town"]

    return state

def scan_farm(state):

    scan = {

        "empty": [],

        "water": [],

        "harvest": [],

        "weed": [],

        "animals": [],

        "locked": []

    }

    tiles = state["tiles"]

    for y, row in enumerate(tiles):

        for x, tile in enumerate(row):

            pos = (x, y)

            if tile == "LOCKED":

                scan["locked"].append(pos)

                continue

            if tile is None:

                scan["empty"].append(pos)

                continue

            kind = tile.get("kind")

            if kind == "WEED":

                scan["weed"].append(pos)

                continue

            if kind == "PLANT":

                plant = {

                    "pos": pos,

                    "crop": tile["crop"],

                    "yield": tile["yield_units"],

                    "watered": tile["watered_today"],

                    "planted_day": tile["planted_day"],

                    "fertilized_until": tile["fertilized_until_day"]

                }

                if tile["yield_units"] > 0:

                    scan["harvest"].append(plant)

                if not tile["watered_today"]:

                    scan["water"].append(plant)

                continue

            scan["animals"].append(pos)

    return scan

def build_task_queue(state, scan):

    tasks = []

    # Harvest (highest priority)
    for plant in scan["harvest"]:

        tasks.append({
            "priority": 5000,
            "action": {
                "type": "HARVEST",
                "target": plant["pos"],
                "crop": plant["crop"],
                "yield": plant["yield"]
            }
        })

    # Water
    for plant in scan["water"]:

        tasks.append({
            "priority": 1500,
            "action": {
                "type": "WATER",
                "target": plant["pos"],
                "crop": plant["crop"]
            }
        })

    # Plant
    seeds = state["private"]["seeds"]

    for crop, amount in seeds.items():

        if amount <= 0:
            continue

        crop_priority = crop_score(state, crop)

        for tile in scan["empty"]:

            tasks.append({
                "priority": crop_priority,
                "action": {
                    "type": "PLANT",
                    "crop": crop,
                    "target": tile
                }
            })

    # Dig weeds
    for tile in scan["weed"]:

        tasks.append({
            "priority": 100,
            "action": {
                "type": "DIG",
                "target": tile
            }
        })

    return tasks

def score_task(state, task):

    action = task["action"]

    score = task["priority"]

    if action["type"] == "HARVEST":

        price = state["market"]["prices"][action["crop"]]

        score += price * action["yield"]

    farmer = state["farmer"]

    distance = manhattan(farmer, action["target"])

    score -= distance * DISTANCE_COST

    return score

def choose_best_action(state, tasks):

    if len(tasks) == 0:

        return {
            "type": "PASS"
        }

    best = None

    best_score = -1e9

    for task in tasks:

        score = score_task(state, task)

        if score > best_score:

            best_score = score

            best = task["action"]

    return best

def generate_market_actions(state):

    actions = []

    seeds = state["private"]["seeds"]
    shed = state["private"]["shed"]
    money = state["money"]

    # Buy one wheat seed if we have none
    if seeds["WHEAT"] == 0 and money >= 10:
        actions.append(["BUY_SEED", "WHEAT", 1])

    # Sell everything harvested
    for crop in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:

        if shed.get(crop, 0) > 0:

            actions.append([
                "SELL",
                crop,
                shed[crop]
            ])

    return actions

def convert_action_to_kaggle(state, action):

    if action["type"] == "PASS":

        return {
            "farmer":["PASS"],
            "hands":[],
            "market":[]
        }

    farmer = state["farmer"]
    target = action["target"]

    if farmer == target:

        if action["type"] == "HARVEST":
            return {"farmer":["HARVEST"],"hands":[],"market":[]}

        if action["type"] == "WATER":
            return {"farmer":["WATER"],"hands":[],"market":[]}

        if action["type"] == "DIG":
            return {"farmer":["DIG"],"hands":[],"market":[]}

        if action["type"] == "PLANT":
            return {
                "farmer":["PLANT",action["crop"]],
                "hands":[],
                "market":[]
            }

    move = step_toward(farmer,target)

    return {
        "farmer":[move],
        "hands":[],
        "market":[]
    }

def submission_agent(obs, config=None):

    state = analyze_state(obs)

    scan = scan_farm(state)

    tasks = build_task_queue(state, scan)

    action = choose_best_action(state, tasks)

    kaggle_action = convert_action_to_kaggle(state, action)

    kaggle_action["market"] = generate_market_actions(state)

    return kaggle_action


def agent(obs, config):
    return submission_agent(obs, config)

import importlib
import submission

importlib.reload(submission)

print(hasattr(submission, "agent"))
print(hasattr(submission, "submission_agent"))

from kaggle_environments import make

env = make("kaggriculture", debug=True)

env.run([submission.agent, "random"])

print(env.steps[-1][0].reward)

