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

def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]
    market = []

    # ─── Auto-sell everything in shed ───
    for item, qty in private["shed"].items():
        if qty > 0:
            market.append(["SELL", item, qty])

    # ─── Buy 1 melon seed if we have none ───
    if private["seeds"].get("MELON", 0) == 0 and me["money"] >= 80:
        market.append(["BUY_SEED", "MELON", 1])

    # ─── Plant on empty tile ───
    if tile is None and private["seeds"].get("MELON", 0) > 0:
        return {"farmer": ["PLANT", "MELON"], "hands": [], "market": market}

    # ─── Harvest at peak (day 10) ───
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 10:
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile["watered_today"]:
            return {"farmer": ["WATER"], "hands": [], "market": market}

    return {"farmer": ["PASS"], "hands": [], "market": market}

# ⚠️ THIS CELL CREATES THE FILE KAGGLE NEEDS
import json

# Write agent to submission.py
with open("submission.py", "w") as f:
    f.write("""
def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]
    market = []

    # Sell everything in shed
    for item, qty in private["shed"].items():
        if qty > 0:
            market.append(["SELL", item, qty])

    # Buy wheat seeds if needed
    if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # Plant on empty tile
    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}

    # Manage plants
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if tile["crop"] == "WHEAT" and crop_age >= 2:
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile["watered_today"]:
            return {"farmer": ["WATER"], "hands": [], "market": market}

    return {"farmer": ["PASS"], "hands": [], "market": market}
""")

print("✅ submission.py created successfully!")
print("📁 Files in /kaggle/working/:")
print(os.listdir("/kaggle/working/"))