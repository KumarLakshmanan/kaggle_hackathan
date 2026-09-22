from kaggle_environments import make
import json

env = make("kaggriculture")
env.reset()
spec = env.specification
print(spec["configuration"]["boardSize"]["default"],
      spec["configuration"]["startingMoney"]["default"],
      spec["configuration"]["episodeSteps"]["default"])

obs0 = env.state[0].observation
farm0 = obs0.farms[0]
print("money:", farm0["money"], " farmer at:", farm0["farmer"])
print("prices:", dict(obs0.market["prices"]))

def naive_choose(observation):
    farm = observation.farms[int(observation.player)]
    r, c = farm["farmer"]
    here = farm["tiles"][r][c]
    if here is None:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
    return {"farmer": ["PASS"], "hands": [], "market": []}

env2 = make("kaggriculture"); env2.reset()
for _ in range(3):
    obs = env2.state[0].observation
    env2.step([naive_choose(obs), naive_choose(obs)])
after = env2.state[0].observation.farms[0]
print("tile at farmer pos after 3 PLANTs:", after["tiles"][after["farmer"][0]][after["farmer"][1]])

farm0 = env.state[0].observation.farms[0]
fx, fy = farm0["farmer"]
print("farmer field order is (fx, fy) =", (fx, fy))
print("but the interpreter indexes tiles as farm['tiles'][fy][fx], not [fx][fy]")

print("Harvested goods land in observation.private['inventories'][0], a per-farmer pouch.")
print("Only a DROP action, while standing on one of 4 shed-adjacent tiles, moves them to the shed.")
print("Shed-adjacent tiles for a 10x10 board:", {(4,4),(5,4),(4,5),(5,5)})

import starter_policy as sp
import importlib; importlib.reload(sp)

log = sp.run_and_log(720, seed=42)
print(f"Logged {len(log)} turns. Final coins: {log[-1]['money0']:.0f} / {log[-1]['money1']:.0f}")

import matplotlib.pyplot as plt

days = [l["day"] for l in log]
m0 = [l["money0"] for l in log]
m1 = [l["money1"] for l in log]

fig, ax = plt.subplots(figsize=(10, 4.3))
ax.plot(days, m0, color="#3d5a2a", linewidth=2, label="Seat 0")
ax.plot(days, m1, color="#6fae5e", linewidth=2, label="Seat 1")
ax.axhline(3000, color="#b5502c", linestyle=":", linewidth=1.3, label="Starting coins")
ax.set_xlabel("Day"); ax.set_ylabel("Coins"); ax.legend()
ax.set_title("Coins across the season — a real self-play run", fontsize=12, fontweight="bold")
plt.tight_layout(); plt.show()

products = list(log[0]["prices"].keys())
fig, ax = plt.subplots(figsize=(10, 4.3))
for p in products:
    ax.plot(days, [l["prices"][p] for l in log], linewidth=1.6, label=p)
ax.set_xlabel("Day"); ax.set_ylabel("Price")
ax.legend(fontsize=8, ncol=3)
ax.set_title("Market prices over the season", fontsize=12, fontweight="bold")
plt.tight_layout(); plt.show()

start_p, end_p = log[0]["prices"], log[-1]["prices"]
for p in products:
    chg = (end_p[p] - start_p[p]) / start_p[p] * 100
    print(f"{p:12s} {start_p[p]:>5} -> {end_p[p]:<5}  ({chg:+.0f}%)")

unlocked = [l["unlocked0"] for l in log]
print("min/max unlocked quadrants, seat 0:", min(unlocked), max(unlocked))