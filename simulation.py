"""Standalone Python simulator for Kaggriculture v2.0.

Matches the REAL Kaggle observation format:
- obs["player"], obs["day"], obs["hour"], obs["step"]
- obs["private"]["shed"], obs["private"]["seeds"], obs["private"]["inventories"]
- obs["farms"][player]["money"], obs["farms"][player]["unlocked_quadrants"]
- obs["farms"][player]["hires_today"]
- tile["planted_day"], tile["yield_units"], tile["fertilized_until_day"]
- Starting money: $3,000

Full 720-turn (30-day) simulation with:
- Crop growth, watering, fertilization, harvest yields
- Animal feed, care bonus, fertilizer production
- Market price elasticity, town shop consumption
- Weed spawning, labor scaling
"""

import math
import random
import copy

BOARD_SIZE = 10
SHED_CAPACITY = 100
SHED_ADJACENT = [(4, 4), (5, 4), (4, 5), (5, 5)]

CROPS = {
    "WHEAT":      {"cost": 10, "base_price": 25, "first_yield_day": 2, "max_yield_day": 4, "max_yield": 6, "unfert_max": 4, "type": "one_time"},
    "CARROT":     {"cost": 20, "base_price": 35, "first_yield_day": 2, "max_yield_day": 3, "max_yield": 4, "unfert_max": 3, "type": "one_time"},
    "MELON":      {"cost": 80, "base_price": 250, "first_yield_day": 10, "max_yield_day": 10, "max_yield": 6, "type": "one_time"},
    "TOMATO":     {"cost": 50, "base_price": 60, "first_yield_day": 8, "max_yield_day": 11, "max_yield": 4, "type": "ongoing"},
    "STRAWBERRY": {"cost": 100, "base_price": 120, "first_yield_day": 10, "max_yield_day": 16, "max_yield": 4, "type": "ongoing"},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "product": "EGG", "base_price": 50, "structure": "COOP", "interval": 1, "max_held": 4},
    "COW":   {"cost": 400, "product": "MILK", "base_price": 160, "structure": "PASTURE", "interval": 2, "max_held": 6},
    "SHEEP": {"cost": 500, "product": "WOOL", "base_price": 200, "structure": "PASTURE", "interval": 3, "max_held": 6},
}

FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

SHOP_TYPES = ["BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE",
              "ICE_CREAM_SHOP", "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET"]


class FarmState:
    def __init__(self, seat=0):
        self.seat = seat
        self.money = 3000.0  # Starting money per spec
        self.unlocked_quadrants = ["NW"]
        self.farmer_pos = [4, 4]
        self.hands_pos = []
        self.farmer_inv = {}
        self.hands_inv = []
        self.shed = {}       # Non-seed items
        self.seeds = {}      # Seeds (separate from shed per spec)
        self.tiles = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.hires_today = 0

    def is_unlocked(self, x, y):
        if x < 0 or x >= BOARD_SIZE or y < 0 or y >= BOARD_SIZE:
            return False
        if x < 5 and y < 5: return "NW" in self.unlocked_quadrants
        if x >= 5 and y < 5: return "NE" in self.unlocked_quadrants
        if x < 5 and y >= 5: return "SW" in self.unlocked_quadrants
        return "SE" in self.unlocked_quadrants

    def shed_count(self):
        return sum(max(0, v) for v in self.shed.values())


class KaggricultureSim:
    def __init__(self, seed=42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.step = 0
        self.farms = [FarmState(0), FarmState(1)]
        self.market_inventory = {
            "WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000,
            "STRAWBERRY": 10000, "MELON": 10000,
            "EGG": 10000, "MILK": 10000, "WOOL": 10000,
            "FERTILIZER": 10000,
        }
        self.unlocked_shops = []
        self.shop_pool = list(SHOP_TYPES)
        self.rng.shuffle(self.shop_pool)

    @property
    def day(self):
        return self.step // 24

    @property
    def hour(self):
        return self.step % 24

    def _calc_price(self, item):
        """Calculate current market price for an item using simplified elasticity."""
        inv = self.market_inventory.get(item, 10000)
        I0 = 10000
        base_prices = {
            "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
            "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100,
        }
        base = base_prices.get(item, 25)
        diff = abs(inv - I0)
        if inv < I0:
            # Scarcity: price goes up
            t = {"WHEAT": 400, "CARROT": 450, "TOMATO": 200, "STRAWBERRY": 100,
                 "MELON": 300, "EGG": 332, "MILK": 122, "WOOL": 105, "FERTILIZER": 200}.get(item, 300)
            target = {"WHEAT": 0.80, "CARROT": 0.20, "TOMATO": 0.40, "STRAWBERRY": 0.70,
                      "MELON": 0.20, "EGG": 0.40, "MILK": 0.60, "WOOL": 0.20, "FERTILIZER": 0.40}.get(item, 0.4)
            f_val = math.sqrt(diff) if item in ("WHEAT", "STRAWBERRY", "MILK") else math.log1p(diff) if item in ("CARROT", "MELON", "WOOL") else diff
            f_t = math.sqrt(t) if item in ("WHEAT", "STRAWBERRY", "MILK") else math.log1p(t) if item in ("CARROT", "MELON", "WOOL") else t
            if f_t > 0:
                amp = target * base / f_t
                price = base + amp * f_val
            else:
                price = base
        elif inv > I0:
            # Glut: price goes down
            t = {"WHEAT": 400, "CARROT": 450, "TOMATO": 200, "STRAWBERRY": 100,
                 "MELON": 300, "EGG": 332, "MILK": 122, "WOOL": 105, "FERTILIZER": 200}.get(item, 300)
            target = {"WHEAT": 0.20, "CARROT": 0.70, "TOMATO": 0.60, "STRAWBERRY": 1.60,
                      "MELON": 3.60, "EGG": 0.20, "MILK": 1.60, "WOOL": 3.20, "FERTILIZER": 0.40}.get(item, 0.4)
            # Above functions
            if item in ("CARROT", "TOMATO"): f_val = math.sqrt(diff)
            elif item in ("MELON", "WOOL"): f_val = diff * diff
            elif item in ("WHEAT", "EGG"): f_val = math.log1p(diff)
            elif item in ("STRAWBERRY", "MILK"): f_val = diff
            else: f_val = diff
            if item in ("CARROT", "TOMATO"): f_t = math.sqrt(t)
            elif item in ("MELON", "WOOL"): f_t = t * t
            elif item in ("WHEAT", "EGG"): f_t = math.log1p(t)
            elif item in ("STRAWBERRY", "MILK"): f_t = t
            else: f_t = t
            if f_t > 0:
                amp = target * base / f_t
                price = base - amp * f_val
            else:
                price = base
        else:
            price = base
        return max(1, round(price))

    def _get_prices(self):
        return {item: self._calc_price(item) for item in self.market_inventory}

    def get_obs(self, seat=0):
        farm = self.farms[seat]
        opp = self.farms[1 - seat]
        prices = self._get_prices()

        def fmt(f):
            grid = []
            for y in range(BOARD_SIZE):
                row = []
                for x in range(BOARD_SIZE):
                    if not f.is_unlocked(x, y):
                        row.append("LOCKED")
                    elif f.tiles[y][x] is None:
                        row.append(None)
                    else:
                        row.append(copy.deepcopy(f.tiles[y][x]))
                grid.append(row)
            return grid

        return {
            "player": seat,
            "step": self.step,
            "day": self.day,
            "hour": self.hour,
            "private": {
                "shed": copy.deepcopy(farm.shed),
                "seeds": copy.deepcopy(farm.seeds),
                "inventories": [copy.deepcopy(farm.farmer_inv)] + [copy.deepcopy(h) for h in farm.hands_inv],
            },
            "farms": [
                {
                    "money": farm.money if i == seat else opp.money,
                    "farmer": list((farm if i == seat else opp).farmer_pos),
                    "hands": [list(h) for h in (farm if i == seat else opp).hands_pos],
                    "unlocked_quadrants": list((farm if i == seat else opp).unlocked_quadrants),
                    "hires_today": (farm if i == seat else opp).hires_today,
                    "tiles": fmt(farm if i == seat else opp),
                }
                for i in range(2)
            ],
            "market": {
                "prices": prices,
                "inventory": copy.deepcopy(self.market_inventory),
            },
            "town": {
                "unlocked_shops": list(self.unlocked_shops),
            },
        }

    def _exec_market(self, seat, orders):
        farm = self.farms[seat]
        prices = self._get_prices()
        for order in orders[:10]:
            if not isinstance(order, list) or not order:
                continue
            cmd = order[0]
            if cmd == "BUY_LAND":
                n = len(farm.unlocked_quadrants)
                cost = [1000, 2000, 4000][n - 1] if 1 <= n <= 3 else 99999
                if n < 4 and farm.money >= cost:
                    farm.money -= cost
                    farm.unlocked_quadrants.append(["NE", "SW", "SE"][n - 1])
            elif cmd == "HIRE":
                cost = FIB[min(farm.hires_today, len(FIB) - 1)]
                if farm.money >= cost:
                    farm.money -= cost
                    farm.hires_today += 1
                    spawn = [5, 4] if len(farm.hands_pos) % 4 < 2 else [4, 5]
                    farm.hands_pos.append(list(spawn))
                    farm.hands_inv.append({})
            elif cmd == "BUY_SEED" and len(order) >= 3:
                crop, qty = order[1], max(0, int(order[2]))
                if crop in CROPS:
                    cost = CROPS[crop]["cost"] * qty
                    if farm.money >= cost:
                        farm.money -= cost
                        farm.seeds[crop] = farm.seeds.get(crop, 0) + qty
            elif cmd == "BUY_ANIMAL" and len(order) >= 3:
                animal, qty = order[1], max(0, int(order[2]))
                if animal in ANIMALS:
                    cost = ANIMALS[animal]["cost"] * qty
                    if farm.money >= cost:
                        farm.money -= cost
                        farm.shed[animal] = farm.shed.get(animal, 0) + qty
            elif cmd == "BUY_PRODUCT" and len(order) >= 3:
                prod, qty = order[1], max(0, int(order[2]))
                price = prices.get(prod, 100)
                cost = price * qty
                if farm.money >= cost:
                    farm.money -= cost
                    farm.shed[prod] = farm.shed.get(prod, 0) + qty
                    self.market_inventory[prod] = self.market_inventory.get(prod, 10000) - qty
            elif cmd == "SELL" and len(order) >= 3:
                item, qty = order[1], max(0, int(order[2]))
                available = farm.shed.get(item, 0)
                sell = min(available, qty)
                if sell > 0:
                    price = prices.get(item, 10)
                    farm.money += sell * price
                    farm.shed[item] -= sell
                    if farm.shed[item] <= 0:
                        del farm.shed[item]
                    self.market_inventory[item] = self.market_inventory.get(item, 10000) + sell

    def _exec_unit(self, seat, unit_idx, action):
        farm = self.farms[seat]
        pos = farm.farmer_pos if unit_idx == 0 else farm.hands_pos[unit_idx - 1]
        inv = farm.farmer_inv if unit_idx == 0 else farm.hands_inv[unit_idx - 1]

        if not isinstance(action, list) or not action:
            return
        cmd = action[0]

        # Movement
        dx, dy = 0, 0
        if cmd == "NORTH": dy = -1
        elif cmd == "SOUTH": dy = 1
        elif cmd == "WEST": dx = -1
        elif cmd == "EAST": dx = 1
        if dx or dy:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                pos[0], pos[1] = nx, ny
            return

        x, y = pos[0], pos[1]
        tile = farm.tiles[y][x] if 0 <= y < BOARD_SIZE and 0 <= x < BOARD_SIZE else None

        if cmd == "BUILD_COOP" and tile is None and farm.is_unlocked(x, y):
            farm.tiles[y][x] = {"kind": "COOP", "animal": None}
        elif cmd == "BUILD_PASTURE" and tile is None and farm.is_unlocked(x, y):
            farm.tiles[y][x] = {"kind": "PASTURE", "animal": None}
        elif cmd == "PLANT" and len(action) >= 2 and tile is None and farm.is_unlocked(x, y):
            crop = action[1]
            if farm.seeds.get(crop, 0) > 0:
                farm.seeds[crop] -= 1
                farm.tiles[y][x] = {
                    "kind": "PLANT", "crop": crop,
                    "planted_day": self.day, "watered_today": False,
                    "consecutive_unwatered": 1,  # Plant day counts as first missed
                    "yield_units": 0,
                    "fertilized_until_day": -1,
                }
        elif cmd == "WATER" and isinstance(tile, dict) and tile.get("kind") == "PLANT":
            tile["watered_today"] = True
        elif cmd == "FERTILIZE" and isinstance(tile, dict) and tile.get("kind") == "PLANT":
            has_fert = inv.get("FERTILIZER", 0) > 0 or farm.shed.get("FERTILIZER", 0) > 0
            if has_fert:
                if inv.get("FERTILIZER", 0) > 0:
                    inv["FERTILIZER"] -= 1
                else:
                    farm.shed["FERTILIZER"] -= 1
                tile["fertilized_until_day"] = self.day + 3
        elif cmd == "HARVEST" and isinstance(tile, dict):
            if tile.get("kind") == "PLANT":
                crop = tile["crop"]
                yield_units = max(1, tile.get("yield_units", 1))
                inv[crop] = inv.get(crop, 0) + yield_units
                cfg = CROPS.get(crop, {})
                if cfg.get("type") == "one_time":
                    farm.tiles[y][x] = None
                else:
                    tile["yield_units"] = 0
            elif tile.get("animal"):
                animal = tile["animal"]
                prod = ANIMALS[animal]["product"]
                yield_u = max(0, tile.get("yield_units", 0))
                if yield_u > 0:
                    inv[prod] = inv.get(prod, 0) + yield_u
                    tile["yield_units"] = 0
        elif cmd == "FEED" and isinstance(tile, dict) and tile.get("animal"):
            has_wheat = inv.get("WHEAT", 0) > 0 or farm.shed.get("WHEAT", 0) > 0
            if has_wheat:
                if inv.get("WHEAT", 0) > 0:
                    inv["WHEAT"] -= 1
                else:
                    farm.shed["WHEAT"] -= 1
                tile["fed_today"] = True
        elif cmd == "CARE" and isinstance(tile, dict) and tile.get("animal"):
            tile["cared_today"] = True
        elif cmd == "COLLECT_FERTILIZER" and isinstance(tile, dict) and tile.get("fertilizer_available"):
            inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
            tile["fertilizer_available"] = False
        elif cmd == "DIG" and farm.is_unlocked(x, y):
            if isinstance(tile, dict) and tile.get("kind") in ("WEED", "PLANT"):
                farm.tiles[y][x] = None
            elif isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and not tile.get("animal"):
                farm.tiles[y][x] = None
        elif cmd == "PLACE" and len(action) >= 2 and isinstance(tile, dict):
            item = action[1]
            if item in ANIMALS and tile.get("animal") is None:
                src = inv if inv.get(item, 0) > 0 else farm.shed
                if src.get(item, 0) > 0:
                    src[item] -= 1
                    tile["animal"] = item
                    tile["placed_day"] = self.day
                    tile["fed_today"] = True
                    tile["cared_today"] = False
                    tile["yield_units"] = 0
                    tile["fertilizer_available"] = False
                    tile["consecutive_unfed"] = 0
                    tile["pending_care_bonus"] = 0
        elif cmd == "DROP" and (x, y) in SHED_ADJACENT:
            for k, v in list(inv.items()):
                room = max(0, SHED_CAPACITY - farm.shed_count())
                amt = min(v, room)
                if amt > 0:
                    farm.shed[k] = farm.shed.get(k, 0) + amt
            inv.clear()
        elif cmd == "PICKUP" and len(action) >= 2 and (x, y) in SHED_ADJACENT:
            item = action[1]
            qty = int(action[2]) if len(action) >= 3 else 1
            avail = farm.shed.get(item, 0)
            take = min(avail, qty)
            if take > 0:
                inv[item] = inv.get(item, 0) + take
                farm.shed[item] -= take
                if farm.shed[item] <= 0:
                    del farm.shed[item]

    def step_game(self, actions_list):
        """Run one game step with actions from both players."""
        # Market orders
        for seat in range(2):
            act = actions_list[seat]
            if isinstance(act, dict) and "market" in act:
                self._exec_market(seat, act["market"])

        # Unit actions
        for seat in range(2):
            farm = self.farms[seat]
            act = actions_list[seat]
            if isinstance(act, dict):
                self._exec_unit(seat, 0, act.get("farmer", ["PASS"]))
                for idx, hand_act in enumerate(act.get("hands", [])):
                    if idx < len(farm.hands_pos):
                        self._exec_unit(seat, idx + 1, hand_act)

        self.step += 1

        # End-of-day processing
        if self.step % 24 == 0:
            current_day = self.step // 24

            # Unlock new shop every 3 days
            if current_day % 3 == 0 and self.shop_pool:
                self.unlocked_shops.append(self.shop_pool.pop())

            for seat in range(2):
                farm = self.farms[seat]
                farm.hires_today = 0

                # Auto-drop all hand inventories
                for inv in [farm.farmer_inv] + farm.hands_inv:
                    for k, v in list(inv.items()):
                        room = max(0, SHED_CAPACITY - farm.shed_count())
                        amt = min(v, room)
                        if amt > 0:
                            farm.shed[k] = farm.shed.get(k, 0) + amt
                    inv.clear()

                # Dismiss hired hands
                farm.hands_pos = []
                farm.hands_inv = []

                # Process tiles
                for y in range(BOARD_SIZE):
                    for x in range(BOARD_SIZE):
                        tile = farm.tiles[y][x]
                        if not isinstance(tile, dict):
                            continue

                        if tile.get("kind") == "PLANT":
                            crop = tile["crop"]
                            cfg = CROPS.get(crop, {})
                            planted = tile.get("planted_day", 0)
                            age = current_day - planted

                            # Watering check
                            if tile.get("watered_today", False):
                                tile["consecutive_unwatered"] = 0
                                # Yield accumulation for one-time crops
                                if cfg.get("type") == "one_time":
                                    bonus_start = math.ceil(cfg.get("max_yield_day", 4) / 2)
                                    if age >= bonus_start and age <= cfg.get("max_yield_day", 4):
                                        fert_until = tile.get("fertilized_until_day", -1)
                                        bonus = 2 if fert_until >= current_day else 1
                                        tile["yield_units"] = min(
                                            tile.get("yield_units", 0) + bonus,
                                            cfg.get("max_yield", 6)
                                        )
                                    elif age >= cfg.get("first_yield_day", 2) and tile.get("yield_units", 0) == 0:
                                        tile["yield_units"] = 1  # Base yield
                            else:
                                tile["consecutive_unwatered"] = tile.get("consecutive_unwatered", 0) + 1
                                if tile["consecutive_unwatered"] >= 2:
                                    farm.tiles[y][x] = {"kind": "WEED"}
                                    continue

                            tile["watered_today"] = False

                            # Ongoing crop production
                            if cfg.get("type") == "ongoing":
                                if age >= cfg.get("first_yield_day", 8):
                                    # Simple production: 1 base yield per interval
                                    fert_until = tile.get("fertilized_until_day", -1)
                                    prod = 2 if fert_until >= current_day and tile.get("watered_today", False) else 1
                                    tile["yield_units"] = min(
                                        tile.get("yield_units", 0) + prod,
                                        cfg.get("max_yield", 4)
                                    )

                        elif tile.get("animal"):
                            # Animal end-of-day
                            animal = tile["animal"]
                            acfg = ANIMALS.get(animal, {})

                            if tile.get("fed_today", False):
                                tile["consecutive_unfed"] = 0
                                # Care bonus
                                if tile.get("cared_today", False):
                                    tile["pending_care_bonus"] = tile.get("pending_care_bonus", 0) + 1
                                # Production check
                                placed = tile.get("placed_day", 0)
                                animal_age = current_day - placed
                                interval = acfg.get("interval", 1)
                                first_yield_day = interval * 2  # Simplified
                                if animal_age >= first_yield_day and animal_age % interval == 0:
                                    base_prod = 1 + tile.get("pending_care_bonus", 0)
                                    tile["yield_units"] = min(
                                        tile.get("yield_units", 0) + base_prod,
                                        acfg.get("max_held", 4)
                                    )
                                    tile["pending_care_bonus"] = 0
                            else:
                                tile["consecutive_unfed"] = tile.get("consecutive_unfed", 0) + 1
                                if tile["consecutive_unfed"] >= 2:
                                    # Animal escapes
                                    tile["animal"] = None
                                    tile["yield_units"] = 0
                                    continue

                            tile["fertilizer_available"] = True
                            tile["fed_today"] = False
                            tile["cared_today"] = False

                # Weed spawning
                for y in range(BOARD_SIZE):
                    for x in range(BOARD_SIZE):
                        if farm.is_unlocked(x, y) and farm.tiles[y][x] is None:
                            if self.rng.random() < 0.005:
                                farm.tiles[y][x] = {"kind": "WEED"}

            # Town consumption
            self._town_consumption()

    def _town_consumption(self):
        """Town shops and center consume market inventory."""
        day = self.day

        # Town center: every 12 turns = 0.5 times per day
        if day <= 10:
            tc_qty = 1
        elif day <= 20:
            tc_qty = 2
        else:
            tc_qty = 4

        for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]:
            self.market_inventory[item] = max(0, self.market_inventory.get(item, 10000) - tc_qty)

        # Shop consumption
        shop_demands = {
            "BAKERY": ["EGG", "WHEAT"],
            "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
            "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
            "YARN_STORE": ["WOOL"],
            "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
            "PET_CAFE": ["CARROT"],
            "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
            "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
        }
        for shop in self.unlocked_shops:
            demands = shop_demands.get(shop, [])
            qty = 2 if len(demands) == 1 else 1  # Single-product shops consume 2x
            for item in demands:
                self.market_inventory[item] = max(0, self.market_inventory.get(item, 10000) - qty)

    def is_done(self):
        return self.step >= 720

    def get_scores(self):
        return [self.farms[0].money, self.farms[1].money]


def pass_agent(obs):
    """Passive opponent that does nothing."""
    return {"farmer": ["PASS"], "hands": [], "market": []}


def run_simulation(agent0, agent1=None, seed=42, verbose=False):
    """Run a full 720-turn game and return final scores."""
    if agent1 is None:
        agent1 = pass_agent
    sim = KaggricultureSim(seed=seed)
    while not sim.is_done():
        obs0 = sim.get_obs(0)
        obs1 = sim.get_obs(1)
        act0 = agent0(obs0)
        act1 = agent1(obs1)
        sim.step_game([act0, act1])
        if verbose and sim.step % 24 == 0:
            d = sim.step // 24
            p = sim._get_prices()
            print(f"Day {d:2d}: P0=${sim.farms[0].money:8.0f} P1=${sim.farms[1].money:8.0f} "
                  f"Land={len(sim.farms[0].unlocked_quadrants)} "
                  f"Shed={sim.farms[0].shed_count()} "
                  f"Melon=${p.get('MELON', 0):3d} Milk=${p.get('MILK', 0):3d}")
    return sim.get_scores()


if __name__ == "__main__":
    from dynamic_agent import agent as dynamic

    print("=" * 60)
    print("Kaggriculture Simulation Benchmark v2.0")
    print("=" * 60)

    seeds = [1, 2, 3, 42, 100, 7, 13, 99, 123, 456]
    scores = []
    for s in seeds:
        score, opp = run_simulation(dynamic, pass_agent, seed=s, verbose=(s == 1))
        scores.append(score)
        print(f"Seed {s:5d}: Score = ${score:,.0f}")

    print("-" * 40)
    print(f"MEAN:  ${sum(scores) / len(scores):,.0f}")
    print(f"MIN:   ${min(scores):,.0f}")
    print(f"MAX:   ${max(scores):,.0f}")
    print(f"TOTAL: ${sum(scores):,.0f}")
