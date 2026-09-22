import math
from collections import defaultdict

# ---- Game Constants ----
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["GOOSE", "COW", "SHEEP"]

CROP_DATA = {
    "WHEAT":   {"seed_cost": 10, "base_price": 25, "first_yield": 2, "max_yield_day": 4, "max_yield": 6, "type": "one_time"},
    "CARROT":  {"seed_cost": 20, "base_price": 35, "first_yield": 2, "max_yield_day": 3, "max_yield": 4, "type": "one_time"},
    "TOMATO":  {"seed_cost": 50, "base_price": 60, "first_yield": 8, "max_yield_day": 11, "max_yield": 4, "type": "ongoing"},
    "STRAWBERRY": {"seed_cost": 100, "base_price": 120, "first_yield": 10, "max_yield_day": 16, "max_yield": 4, "type": "ongoing"},
    "MELON":   {"seed_cost": 80, "base_price": 250, "first_yield": 10, "max_yield_day": 10, "max_yield": 6, "type": "one_time"},
}

ANIMAL_DATA = {
    "GOOSE": {"cost": 300, "base_price": 50, "interval": 1, "structure": "COOP"},
    "COW":   {"cost": 400, "base_price": 160, "interval": 2, "structure": "PASTURE"},
    "SHEEP": {"cost": 500, "base_price": 200, "interval": 3, "structure": "PASTURE"},
}

BOARD_SIZE = 10
HALF = BOARD_SIZE // 2
SHED_TILES = [(HALF-1, HALF-1), (HALF, HALF-1), (HALF-1, HALF), (HALF, HALF)]  # shed-adjacent positions

def is_shed_adjacent(pos):
    x, y = pos
    return (x, y) in SHED_TILES

def crop_age(obs, tile):
    return obs["day"] - tile["planted_day"]

def get_price(obs, item):
    return obs["market"]["prices"].get(item, 0)

def get_inventory(obs, item):
    return obs["private"]["shed"].get(item, 0)

def get_seeds(obs, crop):
    return obs["private"]["seeds"].get(crop, 0)

def enough_money(obs, amount):
    return obs["farms"][obs["player"]]["money"] >= amount

def available_tiles(obs, player):
    """Return list of (x,y) for empty unlocked tiles."""
    tiles = obs["farms"][player]["tiles"]
    unlocked = obs["farms"][player]["unlocked_quadrants"]
    positions = []
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if tiles[y][x] is None:
                qx = x // HALF
                qy = y // HALF
                qname = ["NW","NE","SW","SE"][qy*2 + qx]
                if qname in unlocked:
                    positions.append((x,y))
    return positions

def expected_profit(crop, obs, remaining_days):
    """Compute expected profit per tile if planted now."""
    data = CROP_DATA[crop]
    price = get_price(obs, crop)
    seed_cost = data["seed_cost"]
    max_yield = data["max_yield"]
    if data["type"] == "one_time":
        harvest_day = min(data["max_yield_day"], remaining_days)
        if harvest_day < data["first_yield"]:
            return 0
        bonus_start = math.ceil(data["max_yield_day"] / 2)
        bonus_days = max(0, harvest_day - bonus_start + 1)
        fertilized = (crop == "MELON" and obs["private"]["shed"].get("FERTILIZER", 0) > 0)
        bonus_per_day = 2 if fertilized else 1
        yield_est = min(1 + bonus_days * bonus_per_day, max_yield)
        profit = (yield_est * price) - seed_cost
        return profit / (harvest_day + 1)
    else:  # ongoing
        first_yield = data["first_yield"]
        interval = 1 if crop == "TOMATO" else 2
        max_harvests = data["max_yield"]
        yields = 0
        day = first_yield
        while day <= remaining_days and yields < max_harvests:
            yields += 1
            day += interval
        if yields == 0:
            return 0
        total_yield = yields
        profit = (total_yield * price) - seed_cost
        occupancy = data["first_yield"] + (yields - 1) * interval
        return profit / (occupancy + 1)
    return 0

class Strategy:
    def __init__(self):
        self.farmer_action = None
        self.hand_actions = []
        self.market_orders = []
        self.assigned_tasks = set()

    def decide(self, obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        day = obs["day"]
        remaining_days = 29 - day
        fx, fy = me["farmer"]
        farmer_pos = (fx, fy)
        self.farmer_action = None
        self.hand_actions = []
        self.market_orders = []
        self.assigned_tasks = set()

        # ---- 1. Market Orders ----
        empty_tiles = available_tiles(obs, player)
        seeds_needed = len(empty_tiles) - sum(private["seeds"].values())
        if seeds_needed > 0:
            best_crop = self.best_crop_to_plant(obs, remaining_days)
            if best_crop and me["money"] >= CROP_DATA[best_crop]["seed_cost"]:
                to_buy = min(seeds_needed, 5)
                self.market_orders.append(["BUY_SEED", best_crop, to_buy])

        # Sell products when price > 120% of base price
        for item, count in private["shed"].items():
            if item in CROPS or item in ANIMALS or item == "FERTILIZER":
                price = get_price(obs, item)
                base = CROP_DATA.get(item, {}).get("base_price", ANIMAL_DATA.get(item, {}).get("base_price", 0))
                if price > base * 1.2 and count > 0:
                    self.market_orders.append(["SELL", item, count])

        # Buy land if possible
        unlocked = me["unlocked_quadrants"]
        land_costs = {"NE": 1000, "SW": 2000, "SE": 4000}
        for q in ["NE", "SW", "SE"]:
            if q not in unlocked and me["money"] >= land_costs[q] and day > 3:
                self.market_orders.append(["BUY_LAND"])
                break

        # Hire hands if many tasks and cash available
        if len(empty_tiles) > 5 and me["money"] > 500 and me["hires_today"] < 5:
            self.market_orders.append(["HIRE"])

        # ---- 2. Farmer Action ----
        tile = me["tiles"][fy][fx]
        self.farmer_action = self.decide_tile_action(tile, farmer_pos, obs, player, is_hand=False)

        if self.farmer_action is None or self.farmer_action[0] == "PASS":
            target = self.find_nearest_task(obs, player, farmer_pos)
            if target:
                dx = target[0] - fx
                dy = target[1] - fy
                if dx != 0:
                    self.farmer_action = ["EAST" if dx > 0 else "WEST"]
                elif dy != 0:
                    self.farmer_action = ["SOUTH" if dy > 0 else "NORTH"]
                else:
                    self.farmer_action = self.decide_tile_action(me["tiles"][fy][fx], (fx, fy), obs, player, is_hand=False)
            else:
                self.farmer_action = ["PASS"]

        # ---- 3. Hand Actions ----
        for hand_pos in me["hands"]:
            hx, hy = hand_pos
            tile_hand = me["tiles"][hy][hx]
            action = self.decide_tile_action(tile_hand, (hx, hy), obs, player, is_hand=True)
            if action is None or action[0] == "PASS":
                target = self.find_nearest_task(obs, player, (hx, hy), assigned=self.assigned_tasks)
                if target:
                    dx = target[0] - hx
                    dy = target[1] - hy
                    if dx != 0:
                        action = ["EAST" if dx > 0 else "WEST"]
                    elif dy != 0:
                        action = ["SOUTH" if dy > 0 else "NORTH"]
                    else:
                        action = self.decide_tile_action(me["tiles"][hy][hx], (hx, hy), obs, player, is_hand=True)
                else:
                    action = ["PASS"]
            if action is not None:
                self.hand_actions.append(action)
                if action[0] in ["PLANT", "WATER", "HARVEST", "FERTILIZE", "FEED", "CARE", "COLLECT_FERTILIZER"]:
                    self.assigned_tasks.add((hx, hy))

        return {
            "farmer": self.farmer_action,
            "hands": self.hand_actions,
            "market": self.market_orders
        }

    def decide_tile_action(self, tile, pos, obs, player, is_hand):
        """Return action for a unit standing on a tile, or None if no action."""
        if tile is None:
            best = self.best_crop_to_plant(obs, 29 - obs["day"])
            if best and get_seeds(obs, best) > 0:
                return ["PLANT", best]
            return None
        elif isinstance(tile, dict):
            if tile.get("kind") == "PLANT":
                crop = tile["crop"]
                age = obs["day"] - tile["planted_day"]
                if not tile["watered_today"]:
                    return ["WATER"]
                first_yield = CROP_DATA[crop]["first_yield"]
                if age >= first_yield and tile["yield_units"] > 0:
                    return ["HARVEST"]
                if crop == "MELON" and tile["fertilized_until_day"] < obs["day"]:
                    if obs["private"]["shed"].get("FERTILIZER", 0) > 0:
                        return ["FERTILIZE"]
                return None
            elif tile.get("kind") in ["COOP", "PASTURE"]:
                animal = tile.get("animal")
                if animal is not None:
                    if not tile["fed_today"]:
                        return ["FEED"]
                    if not tile["cared_today"] and obs["hour"] < 20:
                        return ["CARE"]
                    if tile["yield_units"] > 0:
                        return ["HARVEST"]
                    if tile["fertilizer_available"]:
                        return ["COLLECT_FERTILIZER"]
                else:
                    for animal_type in ANIMALS:
                        if animal_type in obs["private"]["shed"] and obs["private"]["shed"][animal_type] > 0:
                            if (animal_type == "GOOSE" and tile["kind"] == "COOP") or \
                               (animal_type in ["COW","SHEEP"] and tile["kind"] == "PASTURE"):
                                return ["PLACE", animal_type, 1]
                return None
            elif tile.get("kind") == "WEED":
                return ["DIG"]
        return None

    def best_crop_to_plant(self, obs, remaining_days):
        best = None
        best_profit = -1
        for crop in CROPS:
            profit = expected_profit(crop, obs, remaining_days)
            if get_seeds(obs, crop) == 0:
                profit -= 5
            if profit > best_profit:
                best_profit = profit
                best = crop
        return best

    def find_nearest_task(self, obs, player, pos, assigned=None):
        me = obs["farms"][player]
        tasks = []
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                tile = me["tiles"][y][x]
                if tile is None and get_seeds(obs, self.best_crop_to_plant(obs, 29-obs["day"])) > 0:
                    tasks.append((x,y))
                elif isinstance(tile, dict):
                    if tile.get("kind") == "PLANT":
                        if not tile["watered_today"] or tile["yield_units"] > 0:
                            tasks.append((x,y))
                    elif tile.get("kind") in ["COOP", "PASTURE"]:
                        if tile.get("animal") is not None:
                            if not tile["fed_today"] or tile["yield_units"] > 0 or tile["fertilizer_available"]:
                                tasks.append((x,y))
                        else:
                            tasks.append((x,y))
                    elif tile.get("kind") == "WEED":
                        tasks.append((x,y))
        if assigned:
            tasks = [t for t in tasks if t not in assigned]
        if not tasks:
            return None
        return min(tasks, key=lambda t: abs(t[0]-pos[0]) + abs(t[1]-pos[1]))

# Global instance (optional) – we instantiate fresh each call for simplicity.
def agent(obs):
    return Strategy().decide(obs)

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
result = env.run([agent, "random"])   # or compare with "starter"

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")

# Render (if in Jupyter)
env.render(mode="ipython", width=1200, height=800)