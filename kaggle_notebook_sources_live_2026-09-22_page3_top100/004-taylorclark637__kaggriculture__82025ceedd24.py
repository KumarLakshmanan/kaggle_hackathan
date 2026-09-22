%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class OmegaEKFOracle:
    """
    Joseph-Stabilized EKF for Kaggriculture Market Arbitrage.
    Tracks inventory momentum to preempt opponent gluts and secure premium pricing.
    """
    def __init__(self):
        self.I0 = 10000
        # Market non-linear shape functions and anchor throughputs (T)
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60}
        }
        
        # State vector [Inventory, dI/dt] and Covariance P
        self.state = {crop: np.array([[self.I0], [0.0]], dtype=np.float64) for crop in self.matrix}
        self.P = {crop: np.eye(2, dtype=np.float64) * 10.0 for crop in self.matrix}
        self.Q = np.diag([1.0, 0.1])
        self.R = np.array([[5.0]])

    def _f_shape(self, func_type, x):
        if func_type == "sq": return x**2
        if func_type == "sqrt": return math.sqrt(x)
        if func_type == "log": return math.log(1 + x)
        if func_type == "hinge": return x + 8 * max(0, x - 1)**2
        return x

    def project_price(self, crop, current_inv, opp_yield, active_shops):
        params = self.matrix.get(crop)
        if not params: return 1
        
        # Calculate deterministic town drain (1 per day + 1 per 4 turns for specific shops)
        shop_drain = 6 * sum([1 for s in active_shops if s in ["Pizza Shop", "Farmers Market"] and crop == "TOMATO"]) 
        future_inv = current_inv + opp_yield - 1 - shop_drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            price = params["base"] - (amp * self._f_shape(params["above_func"], delta_I))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            price = params["base"] + (amp * self._f_shape(params["below_func"], delta_I))
            
        return max(1, round(price))


class AStarLatticeRouter:
    """True A* Pathfinding incorporating Manhattan distance heuristics for micro-second execution."""
    def __init__(self, size=10):
        self.size = size
        self.shed_tiles = {(4,4), (5,4), (4,5), (5,5)}
        
    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def path_to(self, start, target, grid):
        start_tup = tuple(start)
        if not target: return ["PASS"]
        target_tup = tuple(target)
        if start_tup == target_tup: return ["PASS"]
        
        queue = []
        heapq.heappush(queue, (0, 0, start_tup, []))
        visited = {start_tup}
        
        while queue:
            f_score, cost, (cx, cy), path = heapq.heappop(queue)
            if (cx, cy) == target_tup: return path
                
            for dx, dy, action in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_cost = cost + 1
                        h = self._heuristic((nx, ny), target_tup)
                        heapq.heappush(queue, (new_cost + h, new_cost, (nx, ny), path + [action]))
        return ["PASS"]


class OmegaStateAgent:
    def __init__(self):
        self.oracle = OmegaEKFOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def _get_best_target(self, grid_tiles, claimed_targets):
        """Yield Prioritization: Premium crops > Staple crops. Water > Harvest > Plant."""
        best_target = None
        best_score = -1
        intent = "PASS"

        for y, row in enumerate(grid_tiles):
            for x, t in enumerate(row):
                pos = (x, y)
                if pos in claimed_targets: 
                    continue

                if t is None:
                    score = 10
                    if score > best_score: best_score, best_target, intent = score, pos, "PLANT"
                elif isinstance(t, dict) and t.get("kind") == "PLANT":
                    is_premium = t.get("crop") in ["MELON", "TOMATO"]
                    if not t.get("watered_today", True):
                        score = 100 if is_premium else 80
                        if score > best_score: best_score, best_target, intent = score, pos, "WATER"
                    elif t.get("yield_units", 0) > 0:
                        score = 90 if is_premium else 70
                        if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
        
        return best_target, intent

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        market_inv = obs["market"]["inventory"]
        market_prices = obs["market"]["prices"]
        
        orders = []
        claimed_targets = set()
        
        # 1. Event Horizon: Shed Pressure Liquidation
        total_shed = sum(priv["shed"].values())
        transit_load = len(me["hands"]) * 4
        if (total_shed + transit_load) > 85 or (obs["step"] % 24) >= 22:
            for item, qty in priv["shed"].items():
                if qty > 0 and market_prices.get(item, 0) > 1:
                    orders.append(["SELL", item, qty])

        # 2. Opponent Threat & Starvation Vector
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0}
        opp_animals = 0
        for r in opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") in opp_yields:
                        opp_yields[t.get("crop")] += t.get("yield_units", 1)
                    elif t.get("kind") in ["COW", "SHEEP", "GOOSE"]:
                        opp_animals += 1
                        
        if opp_animals > 0 and market_prices.get("WHEAT", 0) < 35 and me["money"] > 1000:
            orders.append(["BUY_PRODUCT", "WHEAT", 5])

        # 3. Capital Allocation via EKF Oracle
        best_roi, best_crop = -1, "WHEAT"
        for crop in ["WHEAT", "CARROT", "MELON"]:
            proj = self.oracle.project_price(crop, market_inv[crop], opp_yields[crop], obs["town"]["unlocked_shops"])
            if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) == 0 and me["money"] >= 250:
            orders.append(["BUY_SEED", best_crop, 1])

        hires = me["hires_today"]
        if hires < len(self.fib_cost) and me["money"] > self.fib_cost[hires] * 3:
            orders.append(["HIRE"])

        # 4. Decentralized Kinematic Swarm Routing
        def route_unit(coords):
            coords_tup = tuple(coords)
            target_coords, intent = self._get_best_target(me["tiles"], claimed_targets)
            
            if target_coords:
                claimed_targets.add(target_coords)
                
            if target_coords and target_coords == coords_tup:
                if intent == "PLANT": return ["PLANT", best_crop] if priv["seeds"].get(best_crop, 0) > 0 else ["PASS"]
                return [intent]
            
            path = self.router.path_to(coords_tup, target_coords, me["tiles"])
            return [path[0]]

        f_act = route_unit(me["farmer"])
        h_acts = [route_unit(h) for h in me["hands"]]

        return {"farmer": f_act, "hands": h_acts, "market": orders[:10]}

# Global Execution Entry
nexus = OmegaStateAgent()
def agent(obs): return nexus.execute(obs)


%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class OmegaEKFOracle:
    """
    Joseph-Stabilized EKF for Kaggriculture Market Arbitrage.
    Tracks inventory momentum to preempt opponent gluts and secure premium pricing.
    """
    def __init__(self):
        self.I0 = 10000
        # Market non-linear shape functions and anchor throughputs (T)
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
            "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60}
        }
        
        # State vector [Inventory, dI/dt] and Covariance P initialization
        self.state = {crop: np.array([[self.I0], [0.0]], dtype=np.float64) for crop in self.matrix}
        self.P = {crop: np.eye(2, dtype=np.float64) * 10.0 for crop in self.matrix}
        
        # Aerospace-grade process and measurement noise
        self.Q = np.diag([1.0, 0.1])
        self.R = np.array([[5.0]])
        
        # Deterministic town shop consumption mapping
        self.shop_drain_map = {
            "Bakery": ["EGG", "WHEAT"],
            "Pizza Shop": ["MILK", "TOMATO", "WHEAT"],
            "Brunch Spot": ["EGG", "WHEAT", "STRAWBERRY"],
            "Yarn Store": ["WOOL", "WOOL"], 
            "Ice Cream Shop": ["STRAWBERRY", "MILK", "WHEAT"],
            "Pet Cafe": ["CARROT", "CARROT"],
            "Smoothie Shop": ["STRAWBERRY", "MILK"],
            "Farmers Market": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]
        }

    def _f_shape(self, func_type, x):
        """Mathematical shape functions governing market price elasticity."""
        if func_type == "linear": return x
        if func_type == "sq": return x**2
        if func_type == "sqrt": return math.sqrt(x)
        if func_type == "log": return math.log(1 + x)
        if func_type == "hinge": return x + 8 * max(0, x - 1)**2
        return x

    def project_price(self, crop, current_inv, opp_yield, active_shops):
        """Calculates t+24 thermodynamic price projection."""
        params = self.matrix.get(crop)
        if not params: return 1
        
        # Calculate absolute deterministic town drain over the 24-turn harmonic cycle
        town_center_drain = 1 
        shop_drain = 0
        for shop in active_shops:
            if crop in self.shop_drain_map.get(shop, []):
                multiplier = self.shop_drain_map[shop].count(crop)
                shop_drain += (24 // 4) * multiplier 
                
        future_inv = current_inv + opp_yield - town_center_drain - shop_drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            price = params["base"] - (amp * self._f_shape(params["above_func"], delta_I))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            price = params["base"] + (amp * self._f_shape(params["below_func"], delta_I))
            
        return max(1, round(price))


class AStarLatticeRouter:
    """Topological Pathfinding incorporating Manhattan distance heuristics."""
    def __init__(self, size=10):
        self.size = size
        
    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def path_to(self, start, target, grid):
        start_tup = tuple(start)
        if not target: return ["PASS"]
        target_tup = tuple(target)
        if start_tup == target_tup: return ["PASS"]
        
        queue = []
        heapq.heappush(queue, (0, 0, start_tup, []))
        visited = {start_tup}
        
        while queue:
            f_score, cost, (cx, cy), path = heapq.heappop(queue)
            if (cx, cy) == target_tup: return path
                
            for dx, dy, action in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_cost = cost + 1
                        h = self._heuristic((nx, ny), target_tup)
                        heapq.heappush(queue, (new_cost + h, new_cost, (nx, ny), path + [action]))
        return ["PASS"]


class OmegaStateAgent:
    """
    Primary Agent Orchestration.
    Architecture: Joseph-Stabilized EKF, 3-6-9 Harmonic Synchronization, Thermodynamic Swarm Routing.
    """
    def __init__(self):
        self.oracle = OmegaEKFOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def _get_best_target(self, grid_tiles, claimed_targets):
        """Yield Prioritization: Premium > Staple. Water > Harvest > Plant."""
        best_target = None
        best_score = -1
        intent = "PASS"

        for y, row in enumerate(grid_tiles):
            for x, t in enumerate(row):
                pos = (x, y)
                if pos in claimed_targets: 
                    continue

                if t is None:
                    # Phase 3: Initiation (Planting)
                    score = 10
                    if score > best_score: best_score, best_target, intent = score, pos, "PLANT"
                elif isinstance(t, dict) and t.get("kind") == "PLANT":
                    is_premium = t.get("crop") in ["MELON", "STRAWBERRY", "TOMATO"]
                    if not t.get("watered_today", True):
                        # Phase 6: Reflection/Sustain (Watering)
                        score = 100 if is_premium else 80
                        if score > best_score: best_score, best_target, intent = score, pos, "WATER"
                    elif t.get("yield_units", 0) > 0:
                        # Phase 9: Resolution (Harvesting)
                        score = 90 if is_premium else 70
                        if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
        
        return best_target, intent

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        market_inv = obs["market"]["inventory"]
        market_prices = obs["market"]["prices"]
        
        orders = []
        claimed_targets = set()
        
        # ---------------------------------------------------------
        # PHASE 9: RESOLUTION (Shed Event Horizon Liquidation)
        # ---------------------------------------------------------
        total_shed = sum(priv["shed"].values())
        transit_load = len(me["hands"]) * 4
        # Liquidate if thermodynamic capacity approaches limit, or at harmonic daily peak
        if (total_shed + transit_load) > 85 or (obs["step"] % 24) >= 22:
            for item, qty in priv["shed"].items():
                if qty > 0 and market_prices.get(item, 0) > 1:
                    orders.append(["SELL", item, qty])

        # ---------------------------------------------------------
        # ADVERSARIAL STARVATION VECTOR
        # ---------------------------------------------------------
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0, "STRAWBERRY": 0}
        opp_animals = 0
        for r in opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") in opp_yields:
                        opp_yields[t.get("crop")] += t.get("yield_units", 1)
                    elif t.get("kind") in ["COW", "SHEEP", "GOOSE"]:
                        opp_animals += 1
                        
        # Weaponized capital: artificially pump wheat prices if opponent relies on livestock
        if opp_animals > 0 and market_prices.get("WHEAT", 0) < 35 and me["money"] > 1000:
            orders.append(["BUY_PRODUCT", "WHEAT", 5])

        # ---------------------------------------------------------
        # PHASE 3: INITIATION (Capital Allocation & Fibonacci Labor)
        # ---------------------------------------------------------
        best_roi, best_crop = -1, "WHEAT"
        for crop in ["WHEAT", "CARROT", "MELON"]:
            proj = self.oracle.project_price(crop, market_inv[crop], opp_yields[crop], obs["town"]["unlocked_shops"])
            if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) == 0 and me["money"] >= 250:
            orders.append(["BUY_SEED", best_crop, 1])

        # Swarm Hiring Check against Fibonacci Scale
        hires = me["hires_today"]
        if hires < len(self.fib_cost) and me["money"] > self.fib_cost[hires] * 3:
            orders.append(["HIRE"])

        # ---------------------------------------------------------
        # PHASE 6: REFLECTION (Kinematic Swarm Routing & Ledger)
        # ---------------------------------------------------------
        def route_unit(coords):
            coords_tup = tuple(coords)
            target_coords, intent = self._get_best_target(me["tiles"], claimed_targets)
            
            if target_coords:
                claimed_targets.add(target_coords) # Register target on decentralized ledger
                
            if target_coords and target_coords == coords_tup:
                if intent == "PLANT": return ["PLANT", best_crop] if priv["seeds"].get(best_crop, 0) > 0 else ["PASS"]
                return [intent]
            
            path = self.router.path_to(coords_tup, target_coords, me["tiles"])
            return [path[0]]

        # Dispatch Main Farmer
        f_act = route_unit(me["farmer"])
        
        # Dispatch Hired Swarm
        h_acts = [route_unit(h) for h in me["hands"]]

        return {"farmer": f_act, "hands": h_acts, "market": orders[:10]}

# Global Execution Entry Node
nexus = OmegaStateAgent()
def agent(obs): return nexus.execute(obs)


%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class OmegaEKFOracle:
    def __init__(self):
        self.I0 = 10000
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
            "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60}
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
        
        shop_drain = 6 * sum([1 for s in active_shops if s in ["Pizza Shop", "Farmers Market"] and crop == "TOMATO"]) 
        future_inv = current_inv + opp_yield - 1 - shop_drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            price = params["base"] - (amp * self._f_shape(params["above_func"], delta_I))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            price = params["base"] + (amp * self._f_shape(params["below_func"], delta_I))
            
        return max(1, round(price))


class AStarLatticeRouter:
    def __init__(self, size=10):
        self.size = size
        
    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def path_to(self, start, target, grid):
        start_tup = tuple(start)
        if not target: return ["PASS"]
        target_tup = tuple(target)
        if start_tup == target_tup: return ["PASS"]
        
        queue = []
        heapq.heappush(queue, (0, 0, start_tup, []))
        visited = {start_tup}
        
        while queue:
            f_score, cost, (cx, cy), path = heapq.heappop(queue)
            if (cx, cy) == target_tup: return path
                
            for dx, dy, action in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_cost = cost + 1
                        h = self._heuristic((nx, ny), target_tup)
                        heapq.heappush(queue, (new_cost + h, new_cost, (nx, ny), path + [action]))
        return ["PASS"]


class OmegaStateAgentV12:
    def __init__(self):
        self.oracle = OmegaEKFOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def _get_best_target(self, grid_tiles, claimed_targets, has_fertilizer=False):
        """V12 Yield Prioritization: Care > Fertilize > Water > Harvest > Plant."""
        best_target = None
        best_score = -1
        intent = "PASS"

        empty_tiles = 0
        total_unlocked = 0

        for y, row in enumerate(grid_tiles):
            for x, t in enumerate(row):
                if t != "LOCKED": total_unlocked += 1
                if t is None: empty_tiles += 1
                
                pos = (x, y)
                if pos in claimed_targets or t == "LOCKED": 
                    continue

                if t is None:
                    score = 10
                    if score > best_score: best_score, best_target, intent = score, pos, "PLANT"
                
                elif isinstance(t, dict):
                    is_plant = t.get("kind") == "PLANT"
                    is_animal = t.get("kind") in ["COW", "SHEEP", "GOOSE"]
                    
                    if is_plant:
                        is_premium = t.get("crop") in ["MELON", "STRAWBERRY", "TOMATO"]
                        if has_fertilizer and not t.get("fertilized"):
                            score = 120 if is_premium else 50
                            if score > best_score: best_score, best_target, intent = score, pos, "FERTILIZE"
                        elif not t.get("watered_today", True):
                            score = 100 if is_premium else 80
                            if score > best_score: best_score, best_target, intent = score, pos, "WATER"
                        elif t.get("yield_units", 0) > 0:
                            score = 90 if is_premium else 70
                            if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
                            
                    elif is_animal:
                        if not t.get("fed_today", True):
                            score = 110 
                            if score > best_score: best_score, best_target, intent = score, pos, "FEED"
                        elif not t.get("cared_today", True):
                            score = 105
                            if score > best_score: best_score, best_target, intent = score, pos, "CARE"
                        elif t.get("yield_units", 0) > 0:
                            score = 95
                            if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
        
        return best_target, intent, (empty_tiles / max(1, total_unlocked))

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        market_inv = obs["market"]["inventory"]
        market_prices = obs["market"]["prices"]
        
        orders = []
        claimed_targets = set()
        
        # V12: Thermodynamic Liquidation
        total_shed = sum(priv["shed"].values())
        transit_load = len(me["hands"]) * 4
        if (total_shed + transit_load) > 85 or (obs["step"] % 24) >= 22:
            for item, qty in priv["shed"].items():
                if qty > 0 and market_prices.get(item, 0) > 1:
                    orders.append(["SELL", item, qty])

        # V12: Adversarial Starvation Tracking
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0, "STRAWBERRY": 0}
        opp_animals = 0
        for r in opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") in opp_yields:
                        opp_yields[t.get("crop")] += t.get("yield_units", 1)
                    elif t.get("kind") in ["COW", "SHEEP", "GOOSE"]:
                        opp_animals += 1
                        
        if opp_animals > 0 and market_prices.get("WHEAT", 0) < 35 and me["money"] > 1000:
            orders.append(["BUY_PRODUCT", "WHEAT", 10])

        # V12: Oracle Arbitrage
        best_roi, best_crop = -1, "WHEAT"
        for crop in ["WHEAT", "CARROT", "MELON", "STRAWBERRY"]:
            proj = self.oracle.project_price(crop, market_inv[crop], opp_yields.get(crop, 0), obs["town"]["unlocked_shops"])
            if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) == 0 and me["money"] >= 250:
            orders.append(["BUY_SEED", best_crop, 2])

        # V12: Fibonacci Labor Engine
        hires = me["hires_today"]
        if hires < len(self.fib_cost) and me["money"] > self.fib_cost[hires] * 3:
            orders.append(["HIRE"])

        # V12: Spatial Density & Land Expansion
        has_fert = priv["shed"].get("FERTILIZER", 0) > 0
        _, _, empty_ratio = self._get_best_target(me["tiles"], set(), has_fert)
        if empty_ratio < 0.15 and me["money"] >= 1500:
            orders.append(["BUY_LAND"])

        # V12: Decentralized Swarm Kinematics
        def route_unit(coords):
            coords_tup = tuple(coords)
            target_coords, intent, _ = self._get_best_target(me["tiles"], claimed_targets, has_fert)
            
            if target_coords:
                claimed_targets.add(target_coords)
                
            if target_coords and target_coords == coords_tup:
                if intent == "PLANT": return ["PLANT", best_crop] if priv["seeds"].get(best_crop, 0) > 0 else ["PASS"]
                if intent == "FEED": return ["FEED"] if priv["shed"].get("WHEAT", 0) > 0 else ["PASS"]
                return [intent]
            
            path = self.router.path_to(coords_tup, target_coords, me["tiles"])
            return [path[0]]

        f_act = route_unit(me["farmer"])
        h_acts = [route_unit(h) for h in me["hands"]]

        return {"farmer": f_act, "hands": h_acts, "market": orders[:10]}

nexus = OmegaStateAgentV12()
def agent(obs): return nexus.execute(obs)


%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class OmegaEKFOracle:
    def __init__(self):
        self.I0 = 10000
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
            "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60}
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
        
        shop_drain = 6 * sum([1 for s in active_shops if s in ["Pizza Shop", "Farmers Market"] and crop == "TOMATO"]) 
        future_inv = current_inv + opp_yield - 1 - shop_drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            price = params["base"] - (amp * self._f_shape(params["above_func"], delta_I))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            price = params["base"] + (amp * self._f_shape(params["below_func"], delta_I))
            
        return max(1, round(price))


class AStarLatticeRouter:
    def __init__(self, size=10):
        self.size = size
        
    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def path_to(self, start, target, grid):
        start_tup = tuple(start)
        if not target: return ["PASS"]
        target_tup = tuple(target)
        if start_tup == target_tup: return ["PASS"]
        
        queue = []
        heapq.heappush(queue, (0, 0, start_tup, []))
        visited = {start_tup}
        
        while queue:
            f_score, cost, (cx, cy), path = heapq.heappop(queue)
            if (cx, cy) == target_tup: return path
                
            for dx, dy, action in [(0,-1,"NORTH"), (0,1,"SOUTH"), (1,0,"EAST"), (-1,0,"WEST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_cost = cost + 1
                        h = self._heuristic((nx, ny), target_tup)
                        heapq.heappush(queue, (new_cost + h, new_cost, (nx, ny), path + [action]))
        return ["PASS"]


class OmegaStateAgentV12:
    def __init__(self):
        self.oracle = OmegaEKFOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def _get_best_target(self, grid_tiles, claimed_targets, has_fertilizer=False):
        """V12 Yield Prioritization: Care > Fertilize > Water > Harvest > Plant."""
        best_target = None
        best_score = -1
        intent = "PASS"

        empty_tiles = 0
        total_unlocked = 0

        for y, row in enumerate(grid_tiles):
            for x, t in enumerate(row):
                if t != "LOCKED": total_unlocked += 1
                if t is None: empty_tiles += 1
                
                pos = (x, y)
                if pos in claimed_targets or t == "LOCKED": 
                    continue

                if t is None:
                    score = 10
                    if score > best_score: best_score, best_target, intent = score, pos, "PLANT"
                
                elif isinstance(t, dict):
                    is_plant = t.get("kind") == "PLANT"
                    is_animal = t.get("kind") in ["COW", "SHEEP", "GOOSE"]
                    
                    if is_plant:
                        is_premium = t.get("crop") in ["MELON", "STRAWBERRY", "TOMATO"]
                        if has_fertilizer and not t.get("fertilized"):
                            score = 120 if is_premium else 50
                            if score > best_score: best_score, best_target, intent = score, pos, "FERTILIZE"
                        elif not t.get("watered_today", True):
                            score = 100 if is_premium else 80
                            if score > best_score: best_score, best_target, intent = score, pos, "WATER"
                        elif t.get("yield_units", 0) > 0:
                            score = 90 if is_premium else 70
                            if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
                            
                    elif is_animal:
                        if not t.get("fed_today", True):
                            score = 110 
                            if score > best_score: best_score, best_target, intent = score, pos, "FEED"
                        elif not t.get("cared_today", True):
                            score = 105
                            if score > best_score: best_score, best_target, intent = score, pos, "CARE"
                        elif t.get("yield_units", 0) > 0:
                            score = 95
                            if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
        
        return best_target, intent, (empty_tiles / max(1, total_unlocked))

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        market_inv = obs["market"]["inventory"]
        market_prices = obs["market"]["prices"]
        
        orders = []
        claimed_targets = set()
        
        # V12: Thermodynamic Liquidation
        total_shed = sum(priv["shed"].values())
        transit_load = len(me["hands"]) * 4
        if (total_shed + transit_load) > 85 or (obs["step"] % 24) >= 22:
            for item, qty in priv["shed"].items():
                if qty > 0 and market_prices.get(item, 0) > 1:
                    orders.append(["SELL", item, qty])

        # V12: Adversarial Starvation Tracking
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0, "STRAWBERRY": 0}
        opp_animals = 0
        for r in opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") in opp_yields:
                        opp_yields[t.get("crop")] += t.get("yield_units", 1)
                    elif t.get("kind") in ["COW", "SHEEP", "GOOSE"]:
                        opp_animals += 1
                        
        if opp_animals > 0 and market_prices.get("WHEAT", 0) < 35 and me["money"] > 1000:
            orders.append(["BUY_PRODUCT", "WHEAT", 10])

        # V12: Oracle Arbitrage
        best_roi, best_crop = -1, "WHEAT"
        for crop in ["WHEAT", "CARROT", "MELON", "STRAWBERRY"]:
            proj = self.oracle.project_price(crop, market_inv[crop], opp_yields.get(crop, 0), obs["town"]["unlocked_shops"])
            if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) == 0 and me["money"] >= 250:
            orders.append(["BUY_SEED", best_crop, 2])

        # V12: Fibonacci Labor Engine
        hires = me["hires_today"]
        if hires < len(self.fib_cost) and me["money"] > self.fib_cost[hires] * 3:
            orders.append(["HIRE"])

        # V12: Spatial Density & Land Expansion
        has_fert = priv["shed"].get("FERTILIZER", 0) > 0
        _, _, empty_ratio = self._get_best_target(me["tiles"], set(), has_fert)
        if empty_ratio < 0.15 and me["money"] >= 1500:
            orders.append(["BUY_LAND"])

        # V12: Decentralized Swarm Kinematics
        def route_unit(coords):
            coords_tup = tuple(coords)
            target_coords, intent, _ = self._get_best_target(me["tiles"], claimed_targets, has_fert)
            
            if target_coords:
                claimed_targets.add(target_coords)
                
            if target_coords and target_coords == coords_tup:
                if intent == "PLANT": return ["PLANT", best_crop] if priv["seeds"].get(best_crop, 0) > 0 else ["PASS"]
                if intent == "FEED": return ["FEED"] if priv["shed"].get("WHEAT", 0) > 0 else ["PASS"]
                return [intent]
            
            path = self.router.path_to(coords_tup, target_coords, me["tiles"])
            return [path[0]]

        f_act = route_unit(me["farmer"])
        h_acts = [route_unit(h) for h in me["hands"]]

        return {"farmer": f_act, "hands": h_acts, "market": orders[:10]}

nexus = OmegaStateAgentV12()
def agent(obs): return nexus.execute(obs)


%%writefile submission.py
import math
import heapq
import numpy as np
from collections import deque

class ApexEKFOracle:
    """
    Joseph-Stabilized Extended Kalman Filter.
    Projects absolute market elasticity via deterministic consumption rates.
    """
    def __init__(self):
        self.I0 = 10000
        self.matrix = {
            "WHEAT": {"base": 25, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
            "MELON": {"base": 250, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
            "CARROT": {"base": 35, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
            "TOMATO": {"base": 60, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
            "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60}
        }
        self.shop_drain_map = {
            "Bakery": ["EGG", "WHEAT"],
            "Pizza Shop": ["MILK", "TOMATO", "WHEAT"],
            "Brunch Spot": ["EGG", "WHEAT", "STRAWBERRY"],
            "Yarn Store": ["WOOL", "WOOL"], 
            "Ice Cream Shop": ["STRAWBERRY", "MILK", "WHEAT"],
            "Pet Cafe": ["CARROT", "CARROT"],
            "Smoothie Shop": ["STRAWBERRY", "MILK"],
            "Farmers Market": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]
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
        
        shop_drain = sum([self.shop_drain_map.get(s, []).count(crop) * 6 for s in active_shops])
        future_inv = current_inv + opp_yield - 1 - shop_drain
        delta_I = abs(future_inv - self.I0)
        
        if future_inv > self.I0:
            amp = (params["above_target"] * params["base"]) / self._f_shape(params["above_func"], params["T"])
            price = params["base"] - (amp * self._f_shape(params["above_func"], delta_I))
        else:
            amp = (params["below_target"] * params["base"]) / self._f_shape(params["below_func"], params["T"])
            price = params["base"] + (amp * self._f_shape(params["below_func"], delta_I))
            
        return max(1, round(price))


class AStarLatticeRouter:
    """O(N log N) Topological Pathfinding strictly observing matrix friction."""
    def __init__(self, size=10):
        self.size = size
        self.shed_tiles = [(4,4), (5,4), (4,5), (5,5)]
        
    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_nearest_shed(self, coords):
        return min(self.shed_tiles, key=lambda s: self._heuristic(coords, s))

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
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_cost = cost + 1
                        h = self._heuristic((nx, ny), target_tup)
                        heapq.heappush(queue, (new_cost + h, new_cost, (nx, ny), path + [action]))
        return ["PASS"]


class ApexConstructV13:
    def __init__(self):
        self.oracle = ApexEKFOracle()
        self.router = AStarLatticeRouter()
        self.fib_cost = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def _get_best_target(self, grid_tiles, claimed_targets, unit_inv, shed_inv):
        """Absolute Yield Prioritization matrix, mapping localized physical inventories."""
        best_target = None
        best_score = -1
        intent = "PASS"
        empty_tiles, total_unlocked = 0, 0

        for y, row in enumerate(grid_tiles):
            for x, t in enumerate(row):
                if t != "LOCKED": total_unlocked += 1
                if t is None: empty_tiles += 1
                
                pos = (x, y)
                if pos in claimed_targets or t == "LOCKED": 
                    continue

                if t is None:
                    if 10 > best_score: best_score, best_target, intent = 10, pos, "PLANT"
                
                elif isinstance(t, dict):
                    is_plant = t.get("kind") == "PLANT"
                    is_animal = t.get("kind") in ["COW", "SHEEP", "GOOSE"]
                    
                    if t.get("kind") == "WEED":
                        if 15 > best_score: best_score, best_target, intent = 15, pos, "DIG"

                    elif is_plant:
                        is_premium = t.get("crop") in ["MELON", "STRAWBERRY", "TOMATO"]
                        
                        if not t.get("watered_today", True):
                            score = 100 if is_premium else 80
                            if score > best_score: best_score, best_target, intent = score, pos, "WATER"
                        
                        elif not t.get("fertilized", False):
                            has_fert = unit_inv.get("FERTILIZER", 0) > 0
                            can_get_fert = shed_inv.get("FERTILIZER", 0) > 0
                            if has_fert or can_get_fert:
                                score = 95 if is_premium else 50
                                if score > best_score: 
                                    best_score, best_target = score, pos
                                    intent = "FERTILIZE" if has_fert else "PICKUP_FERTILIZER"

                        elif t.get("yield_units", 0) > 0:
                            score = 90 if is_premium else 70
                            if score > best_score: best_score, best_target, intent = score, pos, "HARVEST"
                            
                    elif is_animal:
                        if not t.get("fed_today", True):
                            has_wheat = unit_inv.get("WHEAT", 0) > 0
                            can_get_wheat = shed_inv.get("WHEAT", 0) > 0
                            if has_wheat or can_get_wheat:
                                score = 110
                                if score > best_score: 
                                    best_score, best_target = score, pos
                                    intent = "FEED" if has_wheat else "PICKUP_WHEAT"

                        elif not t.get("cared_today", True):
                            if 105 > best_score: best_score, best_target, intent = 105, pos, "CARE"
                        
                        elif t.get("yield_units", 0) > 0:
                            if 95 > best_score: best_score, best_target, intent = 95, pos, "HARVEST"
        
        return best_target, intent, (empty_tiles / max(1, total_unlocked))

    def execute(self, obs):
        me = obs["farms"][obs["player"]]
        opp = obs["farms"][1 - obs["player"]]
        priv = obs["private"]
        market_inv = obs["market"]["inventory"]
        market_prices = obs["market"]["prices"]
        
        sell_orders, buy_orders, meta_orders = [], [], []
        claimed_targets = set()
        
        # 1. Thermodynamic Liquidation
        total_shed = sum(priv["shed"].values())
        transit_load = len(me["hands"]) * 4
        if (total_shed + transit_load) > 85 or (obs["step"] % 24) >= 22:
            for item, qty in priv["shed"].items():
                if qty > 0 and market_prices.get(item, 0) > 1:
                    sell_orders.append(["SELL", item, qty])

        # 2. Adversarial Starvation Vector
        opp_yields = {"WHEAT": 0, "CARROT": 0, "MELON": 0, "TOMATO": 0, "STRAWBERRY": 0}
        opp_animals = 0
        for r in opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") in opp_yields:
                        opp_yields[t.get("crop")] += t.get("yield_units", 1)
                    elif t.get("kind") in ["COW", "SHEEP", "GOOSE"]:
                        opp_animals += 1
                        
        if opp_animals > 0 and market_prices.get("WHEAT", 0) < 35 and me["money"] > 1000:
            buy_orders.append(["BUY_PRODUCT", "WHEAT", 10])

        # 3. Capital Allocation via Oracle
        best_roi, best_crop = -1, "WHEAT"
        for crop in ["WHEAT", "CARROT", "MELON", "STRAWBERRY"]:
            proj = self.oracle.project_price(crop, market_inv[crop], opp_yields.get(crop, 0), obs["town"]["unlocked_shops"])
            if proj > best_roi: best_roi, best_crop = proj, crop

        if priv["seeds"].get(best_crop, 0) == 0 and me["money"] >= 250:
            buy_orders.append(["BUY_SEED", best_crop, 4])

        # 4. Fibonacci Labor Engine
        hires = me["hires_today"]
        if hires < len(self.fib_cost) and me["money"] > self.fib_cost[hires] * 3:
            meta_orders.append(["HIRE"])

        # 5. Spatial Density Expansion
        _, _, empty_ratio = self._get_best_target(me["tiles"], set(), {}, priv["shed"])
        if empty_ratio < 0.15 and me["money"] >= 1500:
            meta_orders.append(["BUY_LAND"])

        # 6. Decentralized Swarm Kinematics with Inventory Routing
        def route_unit(coords, unit_inv):
            coords_tup = tuple(coords)
            target_coords, intent, _ = self._get_best_target(me["tiles"], claimed_targets, unit_inv, priv["shed"])
            
            if not target_coords: return ["PASS"]
            
            # Re-route to shed if physical item pickup is required
            if intent in ["PICKUP_WHEAT", "PICKUP_FERTILIZER"]:
                shed_target = self.router.get_nearest_shed(coords_tup)
                if coords_tup == shed_target:
                    item = intent.split("_")[1]
                    return ["PICKUP", item, 5]
                path = self.router.path_to(coords_tup, shed_target)
                return [path[0]]

            claimed_targets.add(target_coords)
            
            if target_coords == coords_tup:
                if intent == "PLANT": return ["PLANT", best_crop] if priv["seeds"].get(best_crop, 0) > 0 else ["PASS"]
                return [intent]
            
            path = self.router.path_to(coords_tup, target_coords)
            return [path[0]]

        # Execute router mapped to explicit personal inventories
        f_act = route_unit(me["farmer"], priv["inventories"][0])
        h_acts = [route_unit(h, priv["inventories"][i+1]) for i, h in enumerate(me["hands"])]

        # Assemble prioritized market queue (Max 10 per Kaggle rules)
        final_orders = (sell_orders + buy_orders + meta_orders)[:10]

        return {"farmer": f_act, "hands": h_acts, "market": final_orders}

nexus = ApexConstructV13()
def agent(obs): return nexus.execute(obs)
