%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class BiosphereOracle:
    """Joseph-Stabilized EKF with Temporal Pruning and Biological Yield multipliers."""
    def __init__(self):
        self.I0 = 10000
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20, "growth": 2},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60, "growth": 10},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70, "growth": 2},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60, "growth": 8},
            "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60, "growth": 10}
        }
        self.shop_drain = {
            "Bakery": ["EGG", "WHEAT"], "Pizza Shop": ["MILK", "TOMATO", "WHEAT"],
            "Brunch Spot": ["EGG", "WHEAT", "STRAWBERRY"], "Yarn Store": ["WOOL", "WOOL"], 
            "Ice Cream Shop": ["STRAWBERRY", "MILK", "WHEAT"], "Pet Cafe": ["CARROT", "CARROT"],
            "Smoothie Shop": ["STRAWBERRY", "MILK"], "Farmers Market": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]
        }

    def _f_shape(self, func_type, x):
        if func_type == "linear": return x
        if func_type == "sq": return x**2
        if func_type == "sqrt": return math.sqrt(x)
        if func_type == "log": return math.log(1 + x)
        if func_type == "hinge": return x + 8 * max(0, x - 1)**2
        return x

    def project_price(self, crop, current_inv, opp_yield, active_shops):
        params = self.matrix.get(crop)
        if not params: return 1
        drain = sum([self.shop_drain.get(s, []).count(crop) * 6 for s in active_shops])
        future_inv = current_inv + opp_yield - 1 - drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            return max(1, round(params["base"] - (amp * self._f_shape(params["above_func"], delta_I))))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            return max(1, round(params["base"] + (amp * self._f_shape(params["below_func"], delta_I))))

    def temporal_viability(self, crop, current_step):
        return ((720 - current_step) / 24) > (self.matrix.get(crop, {}).get("growth", 99) + 1)


class AStarLatticeRouter:
    """Manhattan distance heuristic pathfinding across topological friction nodes."""
    def __init__(self, size=10):
        self.size = size
        self.shed_tiles = [(4,4), (5,4), (4,5), (5,5)]
        
    def heuristic(self, a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
    def get_nearest_shed(self, coords): return min(self.shed_tiles, key=lambda s: self.heuristic(coords, s))

    def path_to(self, start, target):
        start_tup, target_tup = tuple(start), tuple(target)
        if start_tup == target_tup: return ["PASS"]
        queue = [(0, 0, start_tup, [])]
        visited = {start_tup}
        
        while queue:
            _, cost, (cx, cy), path = heapq.heappop(queue)
            if (cx, cy) == target_tup: return path
            for dx, dy, action in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    heapq.heappush(queue, (cost + 1 + self.heuristic((nx, ny), target_tup), cost + 1, (nx, ny), path + [action]))
        return ["PASS"]


class BiosphereConstructV22:
    def __init__(self):
        self.oracle = BiosphereOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        step = obs["step"]
        hour = step % 24
        
        sell_orders, buy_orders, meta_orders = [], [], []
        
        # 1. Thermodynamic Liquidation
        if (sum(priv["shed"].values()) + len(me["hands"]) * 4) > 85 or hour >= 22 or step > 700:
            for item, qty in priv["shed"].items():
                if qty > 0 and obs["market"]["prices"].get(item, 0) > 1:
                    sell_orders.append(["SELL", item, qty])

        # 2. Capital & Seed Allocation
        best_roi, best_crop = -1, "WHEAT"
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0, "STRAWBERRY": 0}
        
        for crop in ["WHEAT", "CARROT", "MELON", "STRAWBERRY"]:
            if self.oracle.temporal_viability(crop, step):
                proj = self.oracle.project_price(crop, obs["market"]["inventory"][crop], opp_yields.get(crop, 0), obs["town"]["shops"])
                if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) < 3 and me["money"] >= 250 and step < 650:
            buy_orders.append(["BUY_SEED", best_crop, 3])

        # Animal Husbandry & Fertilizer Infrastructure
        if priv["shed"].get("FERTILIZER", 0) == 0 and me["money"] > 500:
            buy_orders.append(["BUY_PRODUCT", "FERTILIZER", 2])
            
        if me["money"] > 2000 and priv["shed"].get("GOOSE", 0) == 0:
            buy_orders.append(["BUY_ANIMAL", "GOOSE", 1])

        # 3. Fibonacci Labor Optimization
        if step < 680 and me["hires_today"] < len(self.fib_cost) and me["money"] > self.fib_cost[me["hires_today"]] * 4:
            meta_orders.append(["HIRE"])

        # 4. Swarm Intelligence & Concurrency Ledger
        units = [(me["farmer"], priv["inventories"][0], "farmer")]
        for i, h in enumerate(me["hands"]):
            units.append((h, priv["inventories"][i+1], f"hand_{i}"))
            
        claimed_targets = set()
        allocated_seeds = {best_crop: 0} # Strict Concurrency Lock
        actions_out = {"farmer": ["PASS"], "hands": [["PASS"] for _ in me["hands"]]}

        for u_coords, u_inv, u_id in units:
            targets = []
            
            # Terminal Inventory Overflow Protection
            if sum(u_inv.values()) > 0 and hour >= 20:
                shed_pos = self.router.get_nearest_shed(u_coords)
                targets.append((1000 - self.router.heuristic(u_coords, shed_pos), shed_pos, "DROP"))

            for y, row in enumerate(me["tiles"]):
                for x, t in enumerate(row):
                    if t == "LOCKED": continue
                    pos = (x, y)
                    dist = self.router.heuristic(u_coords, pos)
                    
                    if t is None:
                        # Build infrastructure if we hold an animal
                        if u_inv.get("GOOSE", 0) > 0:
                            targets.append((50 - dist, pos, "BUILD_COOP"))
                        else:
                            targets.append((10 - dist, pos, "PLANT"))
                    
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        
                        if kind == "WEED" or t.get("age", 0) > 20:
                            targets.append((15 - dist, pos, "DIG"))
                            
                        elif kind == "COOP" and t.get("occupant") is None:
                            if u_inv.get("GOOSE", 0) > 0:
                                targets.append((60 - dist, pos, "PLACE_GOOSE"))
                            elif priv["shed"].get("GOOSE", 0) > 0:
                                targets.append((55 - dist, pos, "PICKUP_GOOSE"))
                                
                        elif kind == "PLANT":
                            is_premium = t.get("crop") in ["MELON", "STRAWBERRY"]
                            if not t.get("fertilized", False) and is_premium:
                                if u_inv.get("FERTILIZER", 0) > 0: targets.append((120 - dist, pos, "FERTILIZE"))
                                elif priv["shed"].get("FERTILIZER", 0) > 0: targets.append((115 - dist, pos, "PICKUP_FERTILIZER"))
                            elif not t.get("watered_today", True):
                                targets.append((100 - dist, pos, "WATER"))
                            elif t.get("yield_units", 0) > 0:
                                targets.append((90 - dist, pos, "HARVEST"))
                                
                        elif kind in ["COW", "SHEEP", "GOOSE"]:
                            # Biosphere Husbandry Integration
                            if not t.get("fed_today", True):
                                if u_inv.get("WHEAT", 0) > 0: targets.append((110 - dist, pos, "FEED"))
                                elif priv["shed"].get("WHEAT", 0) > 0: targets.append((105 - dist, pos, "PICKUP_WHEAT"))
                            elif not t.get("cared_today", True):
                                targets.append((105 - dist, pos, "CARE"))
                            elif t.get("yield_units", 0) > 0:
                                targets.append((95 - dist, pos, "HARVEST"))
                            if t.get("has_fertilizer", False):
                                targets.append((92 - dist, pos, "COLLECT_FERTILIZER"))

            targets.sort(key=lambda x: x[0], reverse=True)
            
            assigned_intent = "PASS"
            target_pos = None
            
            for score, pos, intent in targets:
                # Seed Deadlock Prevention Check
                if intent == "PLANT" and allocated_seeds[best_crop] >= priv["seeds"].get(best_crop, 0):
                    continue
                    
                if pos not in claimed_targets or intent.startswith("PICKUP") or intent == "DROP":
                    claimed_targets.add(pos)
                    assigned_intent = intent
                    target_pos = pos
                    if intent == "PLANT":
                        allocated_seeds[best_crop] += 1
                    break
            
            if target_pos:
                if tuple(u_coords) == target_pos:
                    if assigned_intent == "PLANT": action = ["PLANT", best_crop]
                    elif assigned_intent == "DROP": action = ["DROP"]
                    elif assigned_intent.startswith("PICKUP_"): action = ["PICKUP", assigned_intent.split("_")[1], 1]
                    elif assigned_intent.startswith("PLACE_"): action = ["PLACE", assigned_intent.split("_")[1], 1]
                    else: action = [assigned_intent]
                else:
                    if assigned_intent.startswith("PICKUP") or assigned_intent == "DROP":
                        shed_pos = self.router.get_nearest_shed(u_coords)
                        if tuple(u_coords) == shed_pos:
                            action = ["DROP"] if assigned_intent == "DROP" else ["PICKUP", assigned_intent.split("_")[1], 1]
                        else:
                            action = [self.router.path_to(u_coords, shed_pos)[0]]
                    else:
                        action = [self.router.path_to(u_coords, target_pos)[0]]
            else:
                action = ["PASS"]
                
            if u_id == "farmer": actions_out["farmer"] = action
            else: actions_out["hands"][int(u_id.split("_")[1])] = action

        final_orders = (sell_orders + buy_orders + meta_orders)[:10]
        return {"farmer": actions_out["farmer"], "hands": actions_out["hands"], "market": final_orders}

nexus = BiosphereConstructV22()
def agent(obs): return nexus.execute(obs)


%%writefile submission.py
import math, heapq
import numpy as np

class Oracle:
    """Minimized EKF Matrix & Temporal Pruning"""
    def __init__(self):
        self.I0 = 10000
        # Matrix: {crop: (base, T, below_func, below_tgt, above_func, above_tgt, growth_time)}
        self.M = {
            "WHEAT": (25, 400, "sqrt", 0.8, "log", 0.2, 2),
            "MELON": (250, 300, "log", 0.2, "sq", 3.6, 10),
            "CARROT": (35, 450, "hinge", 1.0, "sqrt", 0.7, 2),
            "TOMATO": (60, 200, "hinge", 0.4, "sqrt", 0.6, 8),
            "STRAWBERRY": (120, 100, "sqrt", 0.7, "linear", 1.6, 10)
        }
        self.shops = {
            "Bakery": ["EGG", "WHEAT"], "Pizza Shop": ["MILK", "TOMATO", "WHEAT"],
            "Brunch Spot": ["EGG", "WHEAT", "STRAWBERRY"], "Yarn Store": ["WOOL", "WOOL"], 
            "Ice Cream Shop": ["STRAWBERRY", "MILK", "WHEAT"], "Pet Cafe": ["CARROT", "CARROT"],
            "Smoothie Shop": ["STRAWBERRY", "MILK"], "Farmers Market": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]
        }

    def _f(self, fn, x):
        return x**2 if fn=="sq" else math.sqrt(x) if fn=="sqrt" else math.log(1+x) if fn=="log" else x+8*max(0,x-1)**2 if fn=="hinge" else x

    def proj(self, c, c_inv, opp_y, act_shops):
        if c not in self.M: return 1
        b, T, b_fn, b_t, a_fn, a_t, _ = self.M[c]
        drain = sum([self.shops.get(s, []).count(c) * 6 for s in act_shops])
        f_inv = c_inv + opp_y - 1 - drain
        d_I = abs(f_inv - self.I0)
        
        if f_inv > self.I0: return max(1, round(b - ((a_t * b) / self._f(a_fn, T)) * self._f(a_fn, d_I)))
        return max(1, round(b + ((b_t * b) / self._f(b_fn, T)) * self._f(b_fn, d_I)))

    def viable(self, c, step): return ((720 - step) / 24) > (self.M.get(c, [0]*7)[6] + 1)

class Router:
    """O(N log N) A* Pathfinding compacted."""
    def __init__(self):
        self.sz = 10
        self.sheds = [(4,4), (5,4), (4,5), (5,5)]
    def h(self, a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
    def near_shed(self, c): return min(self.sheds, key=lambda s: self.h(c, s))
    
    def path(self, st, tgt):
        st, tgt = tuple(st), tuple(tgt)
        if st == tgt: return ["PASS"]
        q, vis = [(0, 0, st, [])], {st}
        while q:
            _, cost, (x, y), p = heapq.heappop(q)
            if (x, y) == tgt: return p
            for dx, dy, act in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.sz and 0 <= ny < self.sz and (nx, ny) not in vis:
                    vis.add((nx, ny))
                    heapq.heappush(q, (cost + 1 + self.h((nx,ny), tgt), cost + 1, (nx, ny), p+[act]))
        return ["PASS"]

class Agent:
    def __init__(self):
        self.o, self.r = Oracle(), Router()
        self.fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def execute(self, obs):
        me, opp, priv = obs["farms"][obs["player"]], obs["farms"][1-obs["player"]], obs["private"]
        step, hour, mk = obs["step"], obs["step"] % 24, obs["market"]
        s_ord, b_ord, m_ord = [], [], []
        
        # 1. Thermodynamics
        if sum(priv["shed"].values()) + len(me["hands"])*4 > 85 or hour >= 22 or step > 700:
            s_ord = [["SELL", k, v] for k, v in priv["shed"].items() if v > 0 and mk["prices"].get(k, 0) > 1]

        # 2. Capital & Seed Allocation
        best_roi, best_c = -1, "WHEAT"
        opp_y = {"WHEAT":0, "CARROT":0, "MELON":0, "TOMATO":0, "STRAWBERRY":0}
        for row in opp["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in opp_y: opp_y[t["crop"]] += t.get("yield_units", 1)
        
        for c in opp_y.keys():
            if self.o.viable(c, step):
                proj = self.o.proj(c, mk["inventory"][c], opp_y[c], obs["town"]["shops"])
                if proj > best_roi: best_roi, best_c = proj, c

        if priv["seeds"].get(best_c, 0) < 3 and me["money"] >= 250 and step < 650: b_ord.append(["BUY_SEED", best_c, 3])
        if priv["shed"].get("FERTILIZER", 0) == 0 and me["money"] > 500: b_ord.append(["BUY_PRODUCT", "FERTILIZER", 2])
        if priv["shed"].get("GOOSE", 0) == 0 and me["money"] > 2000: b_ord.append(["BUY_ANIMAL", "GOOSE", 1])
        if step < 680 and me["hires_today"] < len(self.fib) and me["money"] > self.fib[me["hires_today"]] * 4: m_ord.append(["HIRE"])

        # 3. Decentralized Swarm Kinematics
        units = [(me["farmer"], priv["inventories"][0], "farmer")] + [(h, priv["inventories"][i+1], f"h_{i}") for i, h in enumerate(me["hands"])]
        claimed, alloc_s = set(), {best_c: 0}
        acts_out = {"farmer": ["PASS"], "hands": [["PASS"] for _ in me["hands"]]}

        for u_pos, u_inv, u_id in units:
            tgts = []
            if sum(u_inv.values()) > 0 and hour >= 20: tgts.append((1000 - self.r.h(u_pos, self.r.near_shed(u_pos)), self.r.near_shed(u_pos), "DROP"))

            for y, row in enumerate(me["tiles"]):
                for x, t in enumerate(row):
                    if t == "LOCKED": continue
                    pos, d = (x, y), self.r.h(u_pos, (x, y))
                    
                    if t is None:
                        tgts.append((50-d if u_inv.get("GOOSE",0)>0 else 10-d, pos, "BUILD_COOP" if u_inv.get("GOOSE",0)>0 else "PLANT"))
                    elif isinstance(t, dict):
                        k = t.get("kind")
                        if k == "WEED" or t.get("age", 0) > 20: tgts.append((15-d, pos, "DIG"))
                        elif k == "COOP" and not t.get("occupant"):
                            tgts.append((60-d if u_inv.get("GOOSE",0)>0 else 55-d, pos, "PLACE_GOOSE" if u_inv.get("GOOSE",0)>0 else "PICKUP_GOOSE" if priv["shed"].get("GOOSE",0)>0 else "PASS"))
                        elif k == "PLANT":
                            if not t.get("fertilized") and t.get("crop") in ["MELON", "STRAWBERRY"]:
                                if u_inv.get("FERTILIZER",0)>0: tgts.append((120-d, pos, "FERTILIZE"))
                                elif priv["shed"].get("FERTILIZER",0)>0: tgts.append((115-d, pos, "PICKUP_FERTILIZER"))
                            elif not t.get("watered_today", True): tgts.append((100-d, pos, "WATER"))
                            elif t.get("yield_units", 0) > 0: tgts.append((90-d, pos, "HARVEST"))
                        elif k in ["COW", "SHEEP", "GOOSE"]:
                            if not t.get("fed_today", True):
                                if u_inv.get("WHEAT",0)>0: tgts.append((110-d, pos, "FEED"))
                                elif priv["shed"].get("WHEAT",0)>0: tgts.append((105-d, pos, "PICKUP_WHEAT"))
                            elif not t.get("cared_today", True): tgts.append((105-d, pos, "CARE"))
                            elif t.get("yield_units", 0) > 0: tgts.append((95-d, pos, "HARVEST"))
                            if t.get("has_fertilizer"): tgts.append((92-d, pos, "COLLECT_FERTILIZER"))

            tgts.sort(key=lambda x: x[0], reverse=True)
            tgt_pos, intent = None, "PASS"
            
            for score, pos, intnt in tgts:
                if intnt == "PASS" or (intnt == "PLANT" and alloc_s[best_c] >= priv["seeds"].get(best_c, 0)): continue
                if pos not in claimed or intnt.startswith("PICKUP") or intnt == "DROP":
                    claimed.add(pos); tgt_pos, intent = pos, intnt
                    if intnt == "PLANT": alloc_s[best_c] += 1
                    break
            
            act = ["PASS"]
            if tgt_pos:
                if tuple(u_pos) == tgt_pos:
                    if intent == "PLANT": act = ["PLANT", best_c]
                    elif intent == "DROP": act = ["DROP"]
                    elif intent.startswith("PICKUP_"): act = ["PICKUP", intent.split("_")[1], 1]
                    elif intent.startswith("PLACE_"): act = ["PLACE", intent.split("_")[1], 1]
                    else: act = [intent]
                else:
                    if intent.startswith("PICKUP") or intent == "DROP":
                        shed = self.r.near_shed(u_pos)
                        act = ["DROP"] if intent == "DROP" else ["PICKUP", intent.split("_")[1], 1] if tuple(u_pos) == shed else [self.r.path(u_pos, shed)[0]]
                    else: act = [self.r.path(u_pos, tgt_pos)[0]]
            
            if u_id == "farmer": acts_out["farmer"] = act
            else: acts_out["hands"][int(u_id.split("_")[1])] = act

        return {"farmer": acts_out["farmer"], "hands": acts_out["hands"], "market": (s_ord + b_ord + m_ord)[:10]}

nexus = Agent()
def agent(obs): return nexus.execute(obs)
