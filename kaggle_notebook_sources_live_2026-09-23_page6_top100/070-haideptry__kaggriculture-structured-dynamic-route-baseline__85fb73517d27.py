!pip install -q kaggle_environments

import os, sys, json, tarfile
from kaggle_environments import make

print("Kaggriculture environment ready!")


agent_code = """
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
LAST_ACT_STEP = 718

class StructuredFarmAgent:
    def __init__(self):
        self.turn = 0
        
    def act(self, observation, configuration):
        player = observation["player"]
        farm = observation["farms"][player]
        step = observation.get("step", 0)
        money = farm.get("money", 0)
        private = observation.get("private", {})
        seeds = private.get("seeds", {})
        shed = private.get("shed", {})
        
        market_orders = []
        
        # 1. Early game seed buffer (Day 1 - 5)
        if step < 120:
            if seeds.get("WHEAT", 0) < 4 and money >= 40:
                market_orders.append(["BUY", "WHEAT", 4])
            elif seeds.get("CARROT", 0) < 2 and money >= 40:
                market_orders.append(["BUY", "CARROT", 2])
        # 2. Mid to late game diversification
        elif step < 650:
            if seeds.get("CARROT", 0) < 4 and money >= 80:
                market_orders.append(["BUY", "CARROT", 4])
            if seeds.get("WHEAT", 0) < 2 and money >= 20:
                market_orders.append(["BUY", "WHEAT", 2])
                
        # 3. Market Sales: Keep shed free of excess inventory
        for item, qty in shed.items():
            if qty > 0:
                if step >= 700 or item != "WHEAT" or qty > 5:
                    market_orders.append(["SELL", item, min(qty, 20)])
                    
        # 4. Unit Actions: Farmer & Hands
        farmer_action = ["PASS"]
        hands_actions = [["PASS"] for _ in farm.get("hands", [])]
        
        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders[:10]
        }

_agent_instance = None
def agent(obs, config):
    global _agent_instance
    if _agent_instance is None or obs.get("step", 0) == 0:
        _agent_instance = StructuredFarmAgent()
    return _agent_instance.act(obs, config)
"""

with open("main.py", "w") as f:
    f.write(agent_code)

print("Agent source code saved as main.py")


with tarfile.open("submission.tar.gz", "w:gz") as tar:
    tar.add("main.py")

print("Package created: submission.tar.gz (Ready for upload!)")


env = make("kaggriculture", configuration={"seed": 42})
env.run(["main.py", "random"])

score_agent = env.steps[-1][0]["reward"]
score_random = env.steps[-1][1]["reward"]

print(f"Validation match completed successfully!")
print(f"Structured Agent Reward: {score_agent}")
print(f"Random Opponent Reward:  {score_random}")
