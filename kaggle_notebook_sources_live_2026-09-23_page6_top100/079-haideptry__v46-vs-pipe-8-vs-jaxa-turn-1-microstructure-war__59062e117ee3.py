!pip install -q kaggle_environments matplotlib pandas

import os, sys, json, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kaggle_environments import make

print("Simulator environment loaded successfully!")


def simulate_microstructure(opening_p0, opening_p1):
    """Simulates market quotes and cash balances across the first 4 steps."""
    env = make("kaggriculture", configuration={"seed": 42})
    env.reset()
    
    price_history = []
    for step in range(4):
        p0_orders = opening_p0.get(step, [])
        p1_orders = opening_p1.get(step, [])
        act0 = {"farmer": ["PASS"], "hands": [], "market": p0_orders}
        act1 = {"farmer": ["PASS"], "hands": [], "market": p1_orders}
        env.step([act0, act1])
        
        obs = env.state[0]["observation"]
        wheat_price = obs.get("market", {}).get("prices", {}).get("WHEAT", 10)
        p0_gold = obs["farms"][0].get("money", 0)
        p1_gold = obs["farms"][1].get("money", 0)
        price_history.append({
            "step": step,
            "wheat_price": wheat_price,
            "p0_cash": p0_gold,
            "p1_cash": p1_gold
        })
    return pd.DataFrame(price_history)

print("Microstructure simulation engine compiled!")


v46_opening = {
    0: [["BUY_PRODUCT", "WHEAT", 7], ["SELL", "WHEAT", 2]],
    1: [["BUY_PRODUCT", "WHEAT", 30]],
    2: [["SELL", "WHEAT", 30]]
}

pipe7_opening = {
    0: [["BUY_PRODUCT", "WHEAT", 5]],
    1: [], # Stays dark! Zero orders placed.
    2: []
}

df_sim = simulate_microstructure(v46_opening, pipe7_opening)
df_sim


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=120)

ax1.plot(df_sim["step"], df_sim["wheat_price"], marker="o", color="#1f77b4", lw=2.5, label="Wheat Town Price")
ax1.set_title("Market Quote Spike (Steps 0 - 3)", fontsize=13, fontweight="bold")
ax1.set_xlabel("Game Step", fontsize=11)
ax1.set_ylabel("Price per Unit (Gold)", fontsize=11)
ax1.set_xticks(range(4))
ax1.legend(frameon=True, facecolor="white")
ax1.grid(True, linestyle="--", alpha=0.6)

ax2.plot(df_sim["step"], df_sim["p0_cash"], marker="s", color="#d62728", lw=2, label="P0: Ahmed V46 (Lift)")
ax2.plot(df_sim["step"], df_sim["p1_cash"], marker="^", color="#2ca02c", lw=2, label="P1: Nathan Pipe-7 (Dark)")
ax2.set_title("Cash Capital Lockup Comparison", fontsize=13, fontweight="bold")
ax2.set_xlabel("Game Step", fontsize=11)
ax2.set_ylabel("Available Cash (Gold)", fontsize=11)
ax2.set_xticks(range(4))
ax2.legend(frameon=True, facecolor="white")
ax2.grid(True, linestyle="--", alpha=0.6)

plt.tight_layout()
plt.show()


agent_code = """
class AntiLiftAgent:
    def __init__(self):
        self.feed_secured = False
        
    def act(self, obs, config):
        step = obs.get("step", 0)
        player = obs["player"]
        farm = obs["farms"][player]
        money = farm.get("money", 0)
        private = obs.get("private", {})
        seeds = private.get("seeds", {})
        shed = private.get("shed", {})
        
        orders = []
        # Turn 0: Clean early feed purchase at index 0
        if step == 0 and not self.feed_secured:
            orders.append(["BUY_PRODUCT", "WHEAT", 5])
            self.feed_secured = True
        # Turn 1: Stay dark to evade predatory price lifts
        elif step == 1:
            pass
        # Core farming loop
        elif step < 650:
            if seeds.get("WHEAT", 0) < 2 and money >= 20:
                orders.append(["BUY", "WHEAT", 2])
            if seeds.get("CARROT", 0) < 2 and money >= 40:
                orders.append(["BUY", "CARROT", 2])
                
        # Terminal liquidation
        if step >= 710:
            for item, qty in shed.items():
                if qty > 0:
                    orders.append(["SELL", item, min(qty, 20)])
                    
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in farm.get("hands", [])],
            "market": orders[:10]
        }

_agent = None
def agent(obs, config):
    global _agent
    if _agent is None or obs.get("step", 0) == 0:
        _agent = AntiLiftAgent()
    return _agent.act(obs, config)
"""

with open("main.py", "w") as f:
    f.write(agent_code)

import tarfile
with tarfile.open("submission.tar.gz", "w:gz") as tar:
    tar.add("main.py")

print("Package created: submission.tar.gz (Fork -> Submit -> Done!)")
