"""Kaggriculture baseline agent: 'Foreman'.

Strategy in one paragraph
-------------------------
Labour is the cheapest resource in this game. A farm hand costs fib(n) coins
(1, 1, 2, 3, 5, 8, 13, 21 ...) and gives you 24 extra actions that day, so a
crew of 10 costs ~143/day and roughly 11x's your throughput. The binding
constraint is therefore tiles, not money, so we buy land early, keep every
unlocked tile planted, and treat watering as sacred (two missed days turns a
plant into a weed). Sales are throttled per crop because premium goods
(melon, strawberry, wool, milk) crash to the $1 floor on modest gluts, while
wheat absorbs almost unlimited volume.

Everything tunable lives in CONFIG.
"""

# --- Game constants (mirrored from the environment; do not edit) -----------
CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2,  "max_yield_day": 4,  "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2,  "max_yield_day": 3,  "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8,  "max_yield_day": 8,  "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "ongoing": False},
}
LAND_PRICES = [1000, 2000, 4000]
SHED_CAPACITY = 100

# --- Tunables --------------------------------------------------------------
CONFIG = {
    # Crew size. Cost of n hands/day = sum of first n Fibonacci numbers.
    "max_hands": 10,
    "hire_cash_floor": 400,      # don't hire below this bank

    # Target share of planted tiles per crop. Renormalised over whatever is
    # still plantable given the days remaining.
    "crop_mix": {"CARROT": 0.40, "WHEAT": 0.25, "MELON": 0.25, "TOMATO": 0.10},

    # Max units of each product sold per day. Premium goods are drip-fed
    # because their glut curves are quadratic.
    "sell_caps": {"WHEAT": 999, "CARROT": 999, "TOMATO": 40,
                  "STRAWBERRY": 10, "MELON": 12, "EGG": 999,
                  "MILK": 10, "WOOL": 8, "FERTILIZER": 999},
    # Never sell below this fraction of the product's opening price, unless
    # the shed is overflowing or the season is ending.
    "min_price_frac": 0.35,

    "land_reserve": 300,         # keep this much cash after buying land
    "seed_buffer": 6,            # keep this many spare seeds per active crop
    "endgame_days": 1,           # last N days: liquidate everything
}

TASK_PRIORITY = {"WATER": 100, "HARVEST": 90, "FEED": 85, "PLANT": 60, "DIG": 25}


def _fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _quadrant_of(x, y, size):
    half = size // 2
    return ("NW" if x < half else "NE") if y < half else ("SW" if x < half else "SE")


class Foreman:
    def __init__(self):
        self.day = -1
        self.sold_today = {}
        self.opening_prices = None

    # -- helpers ------------------------------------------------------------
    def _plantable(self, days_left):
        """Crops that can still reach a first harvest before the season ends."""
        return [c for c, s in CROPS.items() if days_left >= s["first_yield_day"] + 1]

    def _pick_crop(self, tiles, size, days_left, seeds, money):
        planted = {}
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    planted[t["crop"]] = planted.get(t["crop"], 0) + 1
        total = sum(planted.values()) or 1

        candidates = [c for c in self._plantable(days_left)
                      if seeds.get(c, 0) > 0 and c in CONFIG["crop_mix"]]
        if not candidates:
            return None
        mix = {c: CONFIG["crop_mix"][c] for c in candidates}
        norm = sum(mix.values()) or 1.0
        # Largest shortfall against target share wins.
        return max(candidates, key=lambda c: mix[c] / norm - planted.get(c, 0) / total)

    def _tasks(self, farm, size, step, day, days_left, seeds):
        """Every action worth taking on the board right now."""
        tasks = []
        unlocked = set(farm["unlocked_quadrants"])
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                if tile == "LOCKED" or _quadrant_of(x, y, size) not in unlocked:
                    continue
                if tile is None:
                    if seeds:
                        tasks.append((x, y, "PLANT", None))
                    continue
                kind = tile.get("kind")
                if kind == "WEED":
                    tasks.append((x, y, "DIG", None))
                elif kind == "PLANT":
                    crop = tile["crop"]
                    spec = CROPS.get(crop, {})
                    age = day - tile["planted_day"]
                    ready = False
                    if spec.get("ongoing"):
                        ready = tile.get("yield_units", 0) > 0
                    else:
                        # Take the full-yield harvest, unless the season or the
                        # plant's lifespan is about to run out.
                        dying = tile.get("max_lifespan_step") is not None and \
                            step >= tile["max_lifespan_step"] - 24
                        ripe = age >= spec.get("max_yield_day", 99)
                        early = age >= spec.get("first_yield_day", 99) and \
                            (days_left <= 1 or dying)
                        ready = (ripe or early) and tile.get("yield_units", 0) > 0
                    if ready:
                        tasks.append((x, y, "HARVEST", None))
                    elif not tile.get("watered_today"):
                        tasks.append((x, y, "WATER", None))
                elif kind in ("COOP", "PASTURE"):
                    if "animal" in tile:
                        if tile.get("yield_units", 0) > 0:
                            tasks.append((x, y, "HARVEST", None))
                        elif not tile.get("watered_today", True):
                            pass
                    # Empty structures are left alone by this baseline.
        return tasks

    # -- main ---------------------------------------------------------------
    def __call__(self, obs):
        player = obs["player"]
        farm = obs["farms"][player]
        private = obs.get("private", {}) or {}
        seeds = dict(private.get("seeds", {}))
        shed = dict(private.get("shed", {}))
        inventories = private.get("inventories", []) or [{}]
        prices = (obs.get("market", {}) or {}).get("prices", {})
        size = len(farm["tiles"])
        step, day, hour = obs.get("step", 0), obs.get("day", 0), obs.get("hour", 0)
        total_days = 30
        days_left = total_days - day
        endgame = days_left <= CONFIG["endgame_days"]

        if day != self.day:
            self.day = day
            self.sold_today = {}
        if self.opening_prices is None:
            self.opening_prices = dict(prices)

        money = farm["money"]
        market = []

        # 1. Hire the crew at first light. Each HIRE is one market order and
        #    the per-turn order cap is 10, so we spread it over three turns.
        if hour in (0, 1, 2) and money > CONFIG["hire_cash_floor"]:
            already = farm.get("hires_today", 0)
            budget = money - CONFIG["hire_cash_floor"]
            slots = 0
            while (already + slots < CONFIG["max_hands"] and slots < 5
                   and _fib_hire_cost(already + slots) <= budget):
                budget -= _fib_hire_cost(already + slots)
                slots += 1
            market.extend([["HIRE"]] * slots)

        # 2. Land. More tiles is the only way to scale, so buy as soon as we
        #    can afford it with a working reserve.
        n_extra = len(farm["unlocked_quadrants"]) - 1
        if n_extra < len(LAND_PRICES) and days_left > 6:
            cost = LAND_PRICES[n_extra]
            if money >= cost + CONFIG["land_reserve"] and len(market) < 9:
                market.append(["BUY_LAND"])

        # 3. Sell, respecting per-day caps and price floors.
        shed_total = sum(shed.values())
        overflowing = shed_total > SHED_CAPACITY * 0.8
        for item, qty in sorted(shed.items(), key=lambda kv: -prices.get(kv[0], 0)):
            if qty <= 0 or len(market) >= 10:
                continue
            price = prices.get(item, 0)
            floor = CONFIG["min_price_frac"] * self.opening_prices.get(item, price or 1)
            if price < floor and not (overflowing or endgame):
                continue
            cap = 999 if (endgame or overflowing) else CONFIG["sell_caps"].get(item, 999)
            room = cap - self.sold_today.get(item, 0)
            n = min(qty, max(0, room))
            if n > 0:
                market.append(["SELL", item, n])
                self.sold_today[item] = self.sold_today.get(item, 0) + n

        # 4. Restock seeds for whatever we still have time to grow.
        empty = sum(1 for row in farm["tiles"] for t in row if t is None)
        if empty and not endgame and len(market) < 10:
            wanted = [c for c in self._plantable(days_left) if c in CONFIG["crop_mix"]]
            wanted.sort(key=lambda c: -CONFIG["crop_mix"][c])
            spend = money * 0.5
            for crop in wanted:
                if len(market) >= 10:
                    break
                need = int(empty * CONFIG["crop_mix"][crop]) + CONFIG["seed_buffer"]
                have = seeds.get(crop, 0)
                n = min(need - have, int(spend // CROPS[crop]["seed"]))
                if n > 0:
                    market.append(["BUY_SEED", crop, n])
                    spend -= n * CROPS[crop]["seed"]
                    seeds[crop] = have + n

        # 5. Assign every unit to the best unclaimed task.
        units = [tuple(farm["farmer"])] + [tuple(h) for h in farm.get("hands", [])]
        tasks = self._tasks(farm, size, step, day, days_left, seeds)

        scored = []
        for ui, (ux, uy) in enumerate(units):
            for ti, (tx, ty, kind, _) in enumerate(tasks):
                dist = abs(tx - ux) + abs(ty - uy)
                scored.append((TASK_PRIORITY[kind] - dist, ui, ti))
        scored.sort(reverse=True)

        assigned, taken = {}, set()
        plant_budget = dict(seeds)
        for _, ui, ti in scored:
            if ui in assigned or ti in taken:
                continue
            tx, ty, kind, _ = tasks[ti]
            crop = None
            if kind == "PLANT":
                crop = self._pick_crop(farm["tiles"], size, days_left,
                                       plant_budget, money)
                if crop is None or endgame:
                    continue
                plant_budget[crop] -= 1          # never over-commit seeds
                if plant_budget[crop] <= 0:
                    plant_budget.pop(crop, None)
            assigned[ui] = (tx, ty, kind, crop)
            taken.add(ti)

        ops = []
        half = size // 2
        shed_tiles = {(half - 1, half - 1), (half, half - 1),
                      (half - 1, half), (half, half)}
        for ui, (ux, uy) in enumerate(units):
            inv = inventories[ui] if ui < len(inventories) else {}
            job = assigned.get(ui)
            if job is None:
                # Idle: dump anything carried, otherwise head home.
                if sum(inv.values()) and (ux, uy) in shed_tiles:
                    ops.append(["DROP"])
                else:
                    ops.append(self._step_toward(ux, uy, half - 1, half - 1))
                continue
            tx, ty, kind, crop = job
            if (ux, uy) == (tx, ty):
                ops.append([kind, crop] if crop else [kind])
            else:
                # Drop off a full load if we happen to be standing at the shed.
                if sum(inv.values()) >= 6 and (ux, uy) in shed_tiles:
                    ops.append(["DROP"])
                else:
                    ops.append(self._step_toward(ux, uy, tx, ty))

        return {"farmer": ops[0] if ops else ["PASS"],
                "hands": ops[1:],
                "market": market[:10]}

    @staticmethod
    def _step_toward(x, y, tx, ty):
        if x < tx:
            return ["EAST"]
        if x > tx:
            return ["WEST"]
        if y < ty:
            return ["SOUTH"]
        if y > ty:
            return ["NORTH"]
        return ["PASS"]


_foreman = Foreman()


def agent(obs):
    try:
        return _foreman(obs)
    except Exception:
        # A crashed turn is worse than a wasted one.
        return {"farmer": ["PASS"], "hands": [], "market": []}
