# Install/verify kaggle_environments and plotting libs
!pip install -q kaggle_environments matplotlib pandas

import os, sys, json, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kaggle_environments import make

print("Environment initialized successfully!")


def greedy_farmer_agent(obs, config):
    """A simple deterministic agent that plants and waters crops consistently."""
    player = obs["player"]
    farm = obs["farms"][player]
    money = farm.get("money", 0)
    tiles = farm.get("tiles", [])
    seeds = obs.get("private", {}).get("seeds", {})
    shed = obs.get("private", {}).get("shed", {})
    
    orders = []
    # Buy wheat seeds if empty and have money
    if seeds.get("WHEAT", 0) < 2 and money >= 20:
        orders.append(["BUY", "WHEAT", 2])
    
    # Sell produce in shed if any
    for item, qty in shed.items():
        if qty > 0:
            orders.append(["SELL", item, qty])
            
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in farm.get("hands", [])],
        "market": orders[:10]
    }

print("Greedy baseline defined!")


def run_match_with_pnl(agent0, agent1, seed=42):
    env = make("kaggriculture", configuration={"seed": seed})
    env.reset()
    
    history = {"step": [], "money_p0": [], "money_p1": []}
    
    env.run([agent0, agent1])
    for state in env.steps:
        step = state[0]["observation"].get("step", 0)
        p0_m = state[0]["observation"]["farms"][0].get("money", 0)
        p1_m = state[1]["observation"]["farms"][1].get("money", 0)
        history["step"].append(step)
        history["money_p0"].append(p0_m)
        history["money_p1"].append(p1_m)
        
    reward0 = env.steps[-1][0].get("reward", 0)
    reward1 = env.steps[-1][1].get("reward", 0)
    return pd.DataFrame(history), reward0, reward1

df_history, r0, r1 = run_match_with_pnl(greedy_farmer_agent, "random", seed=100)
print(f"Match finished! Reward P0: {r0} | Reward P1: {r1}")


plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, ax = plt.subplots(figsize=(12, 6), dpi=120)

ax.plot(df_history["step"], df_history["money_p0"], label="Greedy Baseline (P0)", color="#2ca02c", lw=2)
ax.plot(df_history["step"], df_history["money_p1"], label="Random Agent (P1)", color="#d62728", lw=1.5, ls="--")

ax.set_title("Kaggriculture Cashflow Curve (Steps 0 - 718)", fontsize=14, fontweight="bold")
ax.set_xlabel("Game Step", fontsize=12)
ax.set_ylabel("Farm Money (Gold)", fontsize=12)
ax.legend(frameon=True, facecolor="white", loc="upper left")
plt.tight_layout()
plt.show()


def run_arena(agent_a, agent_b, n_rounds=3):
    results = []
    for round_idx in range(n_rounds):
        seed = 1000 + round_idx
        # Match 1: A as P0
        _, r_a, r_b = run_match_with_pnl(agent_a, agent_b, seed=seed)
        results.append({"seed": seed, "agent_a_seat": 0, "score_a": r_a, "score_b": r_b, "margin": r_a - r_b})
        
        # Match 2: A as P1 (Swap seats)
        _, r_b, r_a = run_match_with_pnl(agent_b, agent_a, seed=seed)
        results.append({"seed": seed, "agent_a_seat": 1, "score_a": r_a, "score_b": r_b, "margin": r_a - r_b})
        
    df_res = pd.DataFrame(results)
    wins = (df_res["margin"] > 0).sum()
    losses = (df_res["margin"] < 0).sum()
    ties = (df_res["margin"] == 0).sum()
    mean_margin = df_res["margin"].mean()
    
    print(f"=== ARENA RESULTS (Total Matches: {len(df_res)}) ===")
    print(f"Wins: {wins} | Losses: {losses} | Ties: {ties} | Winrate: {wins/len(df_res)*100:.1f}%")
    print(f"Mean Margin for Agent A: {mean_margin:+.1f} Gold")
    return df_res

df_arena = run_arena(greedy_farmer_agent, "random", n_rounds=2)
df_arena
