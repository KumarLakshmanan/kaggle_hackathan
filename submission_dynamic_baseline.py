"""Kaggriculture Dynamic Strategy Agent (Self-Contained Kaggle Submission File).

Optimized multi-stage dynamic strategy targeting 3,000 - 10,000+ coins:
1. Dynamic land quadrant expansion (NW -> NE -> SW -> SE).
2. Dynamic labor scaling & unit action pathfinding.
3. High-yield Melon & Carrot cycling with mass fertilization.
4. Livestock management (Cows & Pastures for steady Milk revenue).
5. Automatic produce collection, shed unloading, and batch market selling.
"""

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

CROPS_INFO = {
    "WHEAT": {"seed": "SEED_WHEAT", "cost": 10, "value": 25, "days": 4},
    "CARROT": {"seed": "SEED_CARROT", "cost": 20, "value": 35, "days": 3},
    "MELON": {"seed": "SEED_MELON", "cost": 80, "value": 250, "days": 10},
}


def _get(data, key, default=None):
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def _dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _step_toward(curr, target):
    cx, cy = curr
    tx, ty = target
    if cx == tx and cy == ty:
        return ["PASS"]
    dx = tx - cx
    dy = ty - cy
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    else:
        return ["SOUTH"] if dy > 0 else ["NORTH"]


def agent(obs):
    try:
        step = min(max(0, int(_get(obs, "step", 0) or 0)), 719)
        day = step // 24
        turn_of_day = step % 24

        private = _get(obs, "private", {}) or {}
        coins = float(_get(private, "coins", 0) or 0)
        shed = _get(private, "inventory", {}) or {}
        inventories = _get(private, "inventories", []) or [{}]

        farms = _get(obs, "farms", []) or []
        my_farm = farms[0] if farms else {}
        unlocks = list(_get(my_farm, "unlocks", ["NW"]) or ["NW"])
        farmer_pos = list(_get(my_farm, "farmer", [4, 4]) or [4, 4])
        hands_pos = [list(p) for p in (_get(my_farm, "hands", []) or [])]
        tiles = _get(my_farm, "tiles", []) or []

        positions = [farmer_pos] + hands_pos

        # 1. Map & State Audit
        empty_tiles = []
        unwatered_crops = []
        unfed_animals = []
        harvestable_crops = []
        harvestable_animals = []
        weed_tiles = []
        cow_count = 0
        pasture_count = 0

        for y in range(10):
            for x in range(10):
                if y < len(tiles) and x < len(tiles[y]):
                    t = tiles[y][x]
                    if t == "LOCKED":
                        continue
                    if t == "WEED":
                        weed_tiles.append((x, y))
                    elif t is None:
                        empty_tiles.append((x, y))
                    elif isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PLANT":
                            if not t.get("watered_today", False):
                                unwatered_crops.append((x, y))
                            crop = t.get("crop", "")
                            age = t.get("age", 0)
                            days_needed = CROPS_INFO.get(crop, {}).get("days", 4)
                            if age >= days_needed:
                                harvestable_crops.append((x, y))
                        elif k == "PASTURE" or k == "COOP":
                            pasture_count += 1
                            if "animal" in t and t["animal"] is not None:
                                if t["animal"] == "COW":
                                    cow_count += 1
                                if not t.get("fed_today", False):
                                    unfed_animals.append((x, y))
                                if t.get("held_yield", 0) > 0:
                                    harvestable_animals.append((x, y))
                            else:
                                empty_tiles.append((x, y))

        # 2. Market Orders Priority Queue
        market_orders = []

        # Land Expansion Priority ($1,000, $2,000, $4,000)
        land_cost = 1000 if len(unlocks) == 1 else (2000 if len(unlocks) == 2 else 4000)
        if len(unlocks) < 4 and coins >= land_cost:
            market_orders.append(["BUY_LAND"])

        # Labor Scaling
        if day < 3:
            target_hands = 0
        elif day < 7:
            target_hands = 1
        elif day < 15:
            target_hands = 2
        elif day < 22:
            target_hands = 3
        else:
            target_hands = 4

        if turn_of_day == 0 and len(hands_pos) < target_hands and coins >= 50:
            market_orders.append(["HIRE"])

        # Animal Feed Supply Check
        wheat_stock = shed.get("WHEAT", 0) + shed.get("SEED_WHEAT", 0)
        if wheat_stock < 3 and coins >= 30:
            market_orders.append(["BUY_SEED", "WHEAT", 5])

        # Controlled Cow Purchase (Max 2 cows total)
        if day >= 4 and (cow_count + shed.get("COW", 0)) < 2 and coins >= 450:
            market_orders.append(["BUY_ANIMAL", "COW", 1])

        # Seed Purchasing for Empty Tiles
        total_seeds_in_shed = sum(v for k, v in shed.items() if k.startswith("SEED_"))
        needed_seeds = max(0, len(empty_tiles) - total_seeds_in_shed)

        if needed_seeds > 0 and coins >= 40:
            if day >= 6:
                melons_to_buy = min(needed_seeds, int(coins // 80))
                if melons_to_buy > 0:
                    market_orders.append(["BUY_SEED", "MELON", melons_to_buy])
                    market_orders.append(["BUY_PRODUCT", "FERTILIZER", min(melons_to_buy, 3)])
                    needed_seeds -= melons_to_buy
            if needed_seeds > 0:
                carrots_to_buy = min(needed_seeds, int(coins // 20))
                if carrots_to_buy > 0:
                    market_orders.append(["BUY_SEED", "CARROT", carrots_to_buy])

        # Sell Harvested Produce Immediately
        for item, qty in list(shed.items()):
            if qty > 0 and not item.startswith("SEED_") and item != "COW":
                market_orders.append(["SELL", item, qty])

        market_orders = market_orders[:10]

        # 3. Unit Action Dispatch (Farmer + Farm Hands)
        unit_actions = []

        for idx, pos in enumerate(positions):
            x, y = pos[0], pos[1]
            tile = tiles[y][x] if (0 <= y < len(tiles) and 0 <= x < len(tiles[y])) else None
            inv = inventories[idx] if idx < len(inventories) else {}

            has_produce = any(v > 0 for k, v in inv.items() if not k.startswith("SEED_"))

            # Immediate Actions on Current Tile
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop", "")
                age = tile.get("age", 0)
                if age >= CROPS_INFO.get(crop, {}).get("days", 4):
                    unit_actions.append(["HARVEST"])
                    continue
                if not tile.get("watered_today", False):
                    unit_actions.append(["WATER"])
                    continue
                if tile.get("fertilized_days", 0) == 0 and (inv.get("FERTILIZER", 0) > 0 or shed.get("FERTILIZER", 0) > 0):
                    unit_actions.append(["FERTILIZE"])
                    continue

            elif isinstance(tile, dict) and (tile.get("kind") in ["PASTURE", "COOP"]):
                if tile.get("animal") is None and (shed.get("COW", 0) > 0 or inv.get("COW", 0) > 0):
                    unit_actions.append(["PLACE", "COW"])
                    continue
                if tile.get("animal") is not None:
                    if not tile.get("fed_today", False) and (inv.get("WHEAT", 0) > 0 or shed.get("WHEAT", 0) > 0):
                        unit_actions.append(["FEED"])
                        continue
                    if tile.get("held_yield", 0) > 0:
                        unit_actions.append(["HARVEST"])
                        continue
                    if tile.get("fertilizer_avail", False):
                        unit_actions.append(["COLLECT_FERTILIZER"])
                        continue

            elif tile == "WEED":
                unit_actions.append(["DIG"])
                continue

            elif tile is None:
                if (shed.get("COW", 0) > 0 or inv.get("COW", 0) > 0) and pasture_count < (cow_count + shed.get("COW", 0)):
                    unit_actions.append(["BUILD_PASTURE"])
                    continue
                planted = False
                for crop_name in ["MELON", "CARROT", "WHEAT"]:
                    seed_key = CROPS_INFO[crop_name]["seed"]
                    if shed.get(seed_key, 0) > 0 or inv.get(seed_key, 0) > 0:
                        unit_actions.append(["PLANT", crop_name])
                        planted = True
                        break
                if planted:
                    continue

            # Drop produce into shed when carrying goods
            if has_produce:
                if (x, y) in SHED_TILES:
                    unit_actions.append(["DROP"])
                    continue
                nearest_shed = min(SHED_TILES, key=lambda s: _dist(pos, s))
                unit_actions.append(_step_toward(pos, nearest_shed))
                continue

            # Navigation Target Priority
            target = None
            if unwatered_crops:
                target = min(unwatered_crops, key=lambda t: _dist(pos, t))
            elif harvestable_crops:
                target = min(harvestable_crops, key=lambda t: _dist(pos, t))
            elif unfed_animals:
                target = min(unfed_animals, key=lambda t: _dist(pos, t))
            elif weed_tiles:
                target = min(weed_tiles, key=lambda t: _dist(pos, t))
            elif empty_tiles:
                target = min(empty_tiles, key=lambda t: _dist(pos, t))
            else:
                target = (4, 4)

            unit_actions.append(_step_toward(pos, target))

        farmer_action = unit_actions[0] if unit_actions else ["PASS"]
        hands_actions = unit_actions[1:] if len(unit_actions) > 1 else []

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders,
        }
    except Exception:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }


my_agent = agent
