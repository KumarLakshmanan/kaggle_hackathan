import os
agent_code = """
import numpy as np
import collections
import math

def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    fx, fy = me["farmer"]
    tiles = me["tiles"]
    board_size = len(tiles)
    def dist(p1, p2): return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    def get_path_move(start, target):
        if start == target: return None
        tx, ty = target
        sx, sy = start
        if tx > sx: return "EAST"
        if tx < sx: return "WEST"
        if ty > sy: return "SOUTH"
        if ty < sy: return "NORTH"
        return None
    tasks = []
    for y in range(board_size):
        for x in range(board_size):
            tile = tiles[y][x]
            if tile == "LOCKED": continue
            if tile is None:
                if day < 20: tasks.append((5, "PLANT_MELON", (x, y)))
                elif day < 26: tasks.append((6, "PLANT_WHEAT", (x, y)))
            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    if not tile["watered_today"]: tasks.append((1, "WATER", (x, y)))
                    crop, age = tile["crop"], day - tile["planted_day"]
                    should_harvest = False
                    if day >= 29: should_harvest = tile["yield_units"] > 0
                    elif crop == "WHEAT" and age >= 4: should_harvest = True
                    elif crop == "CARROT" and age >= 3: should_harvest = True
                    elif crop == "MELON" and age >= 10: should_harvest = True
                    elif crop in ["TOMATO", "STRAWBERRY"] and tile["yield_units"] >= 1: should_harvest = True
                    if should_harvest: tasks.append((2, "HARVEST", (x, y)))
                    if crop == "MELON" and tile["fertilized_until_day"] <= day and private["shed"].get("FERTILIZER", 0) > 0:
                        tasks.append((3, "FERTILIZE", (x, y)))
                elif tile.get("kind") == "WEED": tasks.append((4, "DIG", (x, y)))
    market_orders = []
    for item, count in private["shed"].items():
        if item != "FERTILIZER" and count > 0: market_orders.append(["SELL", item, count])
    if me["money"] > 50:
        if day < 26 and private["seeds"].get("WHEAT", 0) < 15: market_orders.append(["BUY_SEED", "WHEAT", 15])
        if day < 20 and private["seeds"].get("MELON", 0) < 15 and me["money"] > 1000: market_orders.append(["BUY_SEED", "MELON", 15])
        if day < 25 and private["shed"].get("FERTILIZER", 0) < 10 and me["money" ] > 1500: market_orders.append(["BUY_PRODUCT", "FERTILIZER", 10])
    unlocked = len(me["unlocked_quadrants"])
    if day < 20 and unlocked in {1: 1000, 2: 2000, 3: 4000} and me["money"] > {1: 1000, 2: 2000, 3: 4000}[unlocked] + 500:
        market_orders.append(["BUY_LAND"])
    if day < 28 and me["money"] > 500 and me["hires_today"] < 5: market_orders.append(["HIRE"])
    units = [(fx, fy)] + me["hands"]
    unit_actions = [["PASS"]] * len(units)
    assigned_tasks = set()
    tasks.sort(key=lambda t: t[0])
    seeds_avail = private["seeds"].copy()
    for i, u_pos in enumerate(units):
        available_tasks = [t for t in tasks if t[2] not in assigned_tasks]
        best_task, min_dist = None, 999
        for t_prio, t_type, t_pos in available_tasks:
            d = dist(u_pos, t_pos)
            if d < min_dist: min_dist, best_task = d, (t_prio, t_type, t_pos)
            if d == 0: break
        if best_task:
            t_prio, t_type, t_pos = best_task
            if dist(u_pos, t_pos) == 0:
                if t_type == "WATER": unit_actions[i] = ["WATER"]
                elif t_type == "HARVEST": unit_actions[i] = ["HARVEST"]
                elif t_type == "FERTILIZE": unit_actions[i] = ["FERTILIZE"]
                elif t_type == "DIG": unit_actions[i] = ["DIG"]
                elif t_type == "PLANT_MELON" and seeds_avail.get("MELON", 0) > 0: unit_actions[i] = ["PLANT", "MELON"]; seeds_avail["MELON"] -= 1
                elif t_type == "PLANT_WHEAT" and seeds_avail.get("WHEAT", 0) > 0: unit_actions[i] = ["PLANT", "WHEAT"]; seeds_avail["WHEAT"] -= 1
                assigned_tasks.add(t_pos)
            else:
                move = get_path_move(u_pos, t_pos)
                if move: unit_actions[i] = [move]; assigned_tasks.add(t_pos)
    return {"farmer": unit_actions[0], "hands": unit_actions[1:], "market": market_orders}
"""
with open('main.py', 'w') as f: f.write(agent_code)
print("main.py written to output.")