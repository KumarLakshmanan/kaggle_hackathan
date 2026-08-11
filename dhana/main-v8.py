import math

class UnbeatableKaggricultureMaster:
    def __init__(self):
        self.day = 0
        self.hour = 0
        self.step = 0

    def get_action(self, observation, configuration):
        self.day = observation.get('day', 0)
        self.hour = observation.get('hour', 0)
        self.step = observation.get('step', 0)
        total_steps = configuration.get('episodeSteps', 720)
        
        player_id = observation['player']
        opp_id = 1 - player_id
        
        my_farm = observation['farms'][player_id]
        opp_farm = observation['farms'][opp_id]
        my_private = observation['private']
        market = observation['market']
        
        my_money = my_farm['money']
        opp_money = opp_farm['money']
        
        farmer_pos = my_farm['farmer']
        hands_pos = my_farm.get('hands', [])
        my_tiles = my_farm['tiles']
        
        shed = my_private.get('shed', {})
        seeds = my_private.get('seeds', {})
        prices = market.get('prices', {})
        
        market_actions = []
        
        # -------------------------------------------------------------
        # 1. MARKET TIMING & END-GAME LIQUIDATION
        # -------------------------------------------------------------
        is_end_game = self.step >= (total_steps - 48)  # Final 2 Days
        
        # Dump all inventory if end-game or market prices hit peak
        for item, qty in shed.items():
            if qty > 0 and item in prices:
                price = prices[item]
                if price >= 45 or is_end_game or opp_money < 300:
                    market_actions.append(["SELL", item, qty])
                    
        # Buy high-ROI seeds when safe and not in end-game
        if not is_end_game and my_money > 250 and sum(seeds.values()) < 6:
            if my_money >= prices.get('MELON', 250):
                market_actions.append(["BUY_SEED", "MELON", 2])
            elif my_money >= prices.get('STRAWBERRY', 120):
                market_actions.append(["BUY_SEED", "STRAWBERRY", 3])

        # Strict Need-Based Hiring Rule
        unwatered_crops = sum(
            1 for r in range(5) for c in range(5)
            if isinstance(my_tiles[r][c], dict) and not my_tiles[r][c].get('watered_today', False)
        )
        empty_tiles = sum(1 for r in range(5) for c in range(5) if my_tiles[r][c] is None)
        workload = unwatered_crops + empty_tiles
        total_workers = 1 + len(hands_pos)

        if not is_end_game and my_money > 800 and (workload / total_workers) > 3.0:
            if my_farm.get('hires_today', 0) < 2:
                market_actions.append(["HIRE"])

        # -------------------------------------------------------------
        # 2. WORKER CASCADE (HARVEST -> WATER -> CARE -> PLANT)
        # -------------------------------------------------------------
        def resolve_worker_action(w_r, w_c):
            # Priority 1: HARVEST (Zero unharvested crops)
            for r in range(5):
                for c in range(5):
                    tile = my_tiles[r][c]
                    if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                        if tile.get('yield_units', 0) > 0:
                            if w_r == r and w_c == c:
                                return ["HARVEST"]
                            return move_towards(w_r, w_c, r, c)

            # Priority 2: WATER
            for r in range(5):
                for c in range(5):
                    tile = my_tiles[r][c]
                    if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                        if not tile.get('watered_today', False):
                            if w_r == r and w_c == c:
                                return ["WATER"]
                            return move_towards(w_r, w_c, r, c)

            # Priority 3: PLANT
            if not is_end_game:
                avail_seeds = [k for k, v in seeds.items() if v > 0]
                if avail_seeds:
                    best_seed = "MELON" if "MELON" in avail_seeds else avail_seeds[0]
                    for r in range(5):
                        for c in range(5):
                            if my_tiles[r][c] is None:
                                if w_r == r and w_c == c:
                                    return ["PLANT", best_seed]
                                return move_towards(w_r, w_c, r, c)

            return ["PASS"]

        def move_towards(c_r, c_c, t_r, t_c):
            if c_r < t_r: return ["SOUTH"]
            if c_r > t_r: return ["NORTH"]
            if c_c < t_c: return ["EAST"]
            if c_c > t_c: return ["WEST"]
            return ["PASS"]

        farmer_action = resolve_worker_action(farmer_pos[0], farmer_pos[1])
        hands_actions = [resolve_worker_action(h[0], h[1]) for h in hands_pos]

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_actions[:10]
        }

agent_obj = UnbeatableKaggricultureMaster()

def agent(observation, configuration):
    return agent_obj.get_action(observation, configuration)
