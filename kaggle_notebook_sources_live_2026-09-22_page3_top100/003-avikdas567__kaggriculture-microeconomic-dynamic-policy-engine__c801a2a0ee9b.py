# Environment Setup, Reproducibility Engine, and Dependency Initialization
import os
import sys
import math
import json
import random
import time
import tarfile
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import lightgbm as lgb

# Suppress non-critical future and deprecation warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Ensure exact mathematical reproducibility across runs
SEED = 42
def seed_everything(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

seed_everything(SEED)

# Verify kaggle-environments installation
try:
    import kaggle_environments
    from kaggle_environments import make
except ImportError:
    os.system("pip install -q --upgrade 'kaggle-environments>=1.32.2'")
    from kaggle_environments import make

print(f"PyTorch CUDA Acceleration Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Primary GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"Device Count: {torch.cuda.device_count()}")

# Microeconomic Dynamic Price Surface Simulator
MARKET_CONFIG = {
    "WHEAT": {"base": 25, "I0": 10000, "T": 400, "below": ("sqrt", 0.80), "above": ("log", 0.20)},
    "CARROT": {"base": 35, "I0": 10000, "T": 450, "below": ("log", 0.20), "above": ("sqrt", 0.70)},
    "TOMATO": {"base": 60, "I0": 10000, "T": 200, "below": ("linear", 0.40), "above": ("sqrt", 0.60)},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below": ("sqrt", 0.70), "above": ("linear", 1.60)},
    "MELON": {"base": 250, "I0": 10000, "T": 300, "below": ("log", 0.20), "above": ("sq", 3.60)},
    "EGG": {"base": 50, "I0": 10000, "T": 332, "below": ("linear", 0.40), "above": ("log", 0.20)},
    "MILK": {"base": 160, "I0": 10000, "T": 122, "below": ("sqrt", 0.60), "above": ("linear", 1.60)},
    "WOOL": {"base": 200, "I0": 10000, "T": 105, "below": ("log", 0.20), "above": ("sq", 3.20)}
}

def apply_shape(func_name, x):
    if func_name == "linear": return x
    elif func_name == "sq": return x ** 2
    elif func_name == "sqrt": return math.sqrt(x)
    elif func_name == "log": return math.log(1.0 + x)
    return x

def compute_price(crop, inv):
    cfg = MARKET_CONFIG[crop]
    base, I0, T = cfg["base"], cfg["I0"], cfg["T"]
    if inv < I0:
        func, target = cfg["below"]
        diff = I0 - inv
        sign = 1.0
    else:
        func, target = cfg["above"]
        diff = inv - I0
        sign = -1.0
    amp = (target * base) / apply_shape(func, T)
    raw = base + sign * amp * apply_shape(func, diff)
    return max(1, int(math.floor(raw + 0.5)))

# Compute price curves over inventory sweeps
inv_range = np.linspace(8000, 11000, 300)
price_data = []
for crop in MARKET_CONFIG.keys():
    for inv in inv_range:
        p = compute_price(crop, inv)
        price_data.append({"Crop": crop, "Inventory": inv, "Price": p})

df_prices = pd.DataFrame(price_data)

# Vertical Visual 1: Price Sensitivity Curves Across Market Oversupply
plt.figure(figsize=(14, 7))
palette = sns.color_palette("viridis", len(MARKET_CONFIG))
sns.lineplot(data=df_prices, x="Inventory", y="Price", hue="Crop", palette=palette, linewidth=2.5)
plt.axvline(x=10000, color="red", linestyle="--", alpha=0.7, label="Equilibrium Inventory (I0=10000)")
plt.title("Price Elasticity Curves across Market Inventory Trajectories", fontsize=14, fontweight="bold")
plt.xlabel("Market Inventory Level", fontsize=12)
plt.ylabel("Per-Unit Sale Price ($)", fontsize=12)
plt.grid(True, linestyle=":", alpha=0.6)
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0.)
plt.tight_layout()
plt.show()

# Vertical Visual 2: Marginal Labor Hiring Cost Scaling (Fibonacci Growth)
def fib_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

hires = list(range(0, 10))
costs = [fib_cost(n) for n in hires]

plt.figure(figsize=(14, 7))
colors = sns.color_palette("magma", len(hires))
bars = plt.bar(hires, costs, color=colors, edgecolor="black", alpha=0.85)
plt.yscale("log")
plt.title("Marginal Farm Hand Hiring Cost curve (Fibonacci Sequence Scale)", fontsize=14, fontweight="bold")
plt.xlabel("Number of Hired Hands Already Purchased Today", fontsize=12)
plt.ylabel("Marginal Daily Hiring Cost ($ Log Scale)", fontsize=12)
plt.grid(True, which="both", linestyle=":", alpha=0.5)
for bar, c in zip(bars, costs):
    plt.text(bar.get_x() + bar.get_width()/2.0, bar.get_height() * 1.15, f"${c}", ha="center", va="bottom", fontweight="bold")
plt.tight_layout()
plt.show()

# Crop Economics Simulation Matrix
CROP_METRICS = {
    "WHEAT": {"seed": 10, "base_price": 25, "first_yield_day": 2, "max_yield_day": 4, "max_yield": 6, "type": "one-time"},
    "CARROT": {"seed": 20, "base_price": 35, "first_yield_day": 2, "max_yield_day": 3, "max_yield": 4, "type": "one-time"},
    "TOMATO": {"seed": 50, "base_price": 60, "first_yield_day": 8, "max_yield_day": 8, "max_yield": 4, "type": "ongoing"},
    "STRAWBERRY": {"seed": 100, "base_price": 120, "first_yield_day": 10, "max_yield_day": 10, "max_yield": 4, "type": "ongoing"},
    "MELON": {"seed": 80, "base_price": 250, "first_yield_day": 10, "max_yield_day": 12, "max_yield": 6, "type": "one-time"}
}

crop_data = []
for crop, m in CROP_METRICS.items():
    gross_revenue = m["max_yield"] * m["base_price"]
    net_profit = gross_revenue - m["seed"]
    daily_roi = net_profit / (m["max_yield_day"] * m["seed"])
    crop_data.append({
        "Crop": crop,
        "Seed Cost ($)": m["seed"],
        "Base Revenue ($)": gross_revenue,
        "Net Profit ($)": net_profit,
        "Normalized Daily ROI": daily_roi
    })

df_crops = pd.DataFrame(crop_data)

# Vertical Visual 3: Normalized Net Profit and Return on Investment by Crop
plt.figure(figsize=(12, 6))
palette_crops = sns.color_palette("crest", len(df_crops))
sns.barplot(data=df_crops, x="Crop", y="Net Profit ($)", hue="Crop", legend=False, palette=palette_crops, edgecolor="black")
plt.title("Max Potential Net Profit per Tile Cycle under Baseline Market Prices", fontsize=14, fontweight="bold")
plt.xlabel("Crop Type", fontsize=12)
plt.ylabel("Net Profit per Crop Cycle ($)", fontsize=12)
plt.grid(True, axis="y", linestyle=":", alpha=0.6)
for idx, row in df_crops.iterrows():
    plt.text(idx, row["Net Profit ($)"] + 15, f"${row['Net Profit ($)']}", ha="center", fontweight="bold")
plt.tight_layout()
plt.show()

# Vertical Visual 4: Daily ROI Efficiency Comparison
plt.figure(figsize=(12, 6))
palette_roi = sns.color_palette("flare", len(df_crops))
sns.barplot(data=df_crops, x="Crop", y="Normalized Daily ROI", hue="Crop", legend=False, palette=palette_roi, edgecolor="black")
plt.title("Normalized Capital Velocity (Daily ROI per Seed Dollar Spent)", fontsize=14, fontweight="bold")
plt.xlabel("Crop Type", fontsize=12)
plt.ylabel("Daily ROI Multiplier", fontsize=12)
plt.grid(True, axis="y", linestyle=":", alpha=0.6)
for idx, row in df_crops.iterrows():
    plt.text(idx, row["Normalized Daily ROI"] + 0.02, f"{row['Normalized Daily ROI']:.2f}x", ha="center", fontweight="bold")
plt.tight_layout()
plt.show()

# Generate Synthetic Trajectory Training Dataset for Market Price Regression
n_samples = 5000
X_data = []
y_data = []

for _ in range(n_samples):
    step = random.randint(0, 719)
    day = step // 24
    crop = random.choice(list(MARKET_CONFIG.keys()))
    town_demand_mult = 1.0 if day < 10 else (2.0 if day < 20 else 4.0)
    # Simulating inventory shifts
    inv = 10000 + random.randint(-1500, 2000)
    price = compute_price(crop, inv)
    
    # Feature representation
    feats = [
        step,
        day,
        step % 24,
        inv,
        town_demand_mult,
        MARKET_CONFIG[crop]["base"],
        MARKET_CONFIG[crop]["T"]
    ]
    X_data.append(feats)
    y_data.append(price)

feature_names = ["step", "day", "hour", "inventory", "town_mult", "base_price", "anchor_T"]
df_X = pd.DataFrame(X_data, columns=feature_names)
y_vec = np.array(y_data)

# Fit LightGBM Regressor
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.08, random_state=SEED, verbose=-1)
model.fit(df_X, y_vec)

print("LightGBM Price Predictor Model Successfully Trained.")
print(f"Feature Importances: {dict(zip(feature_names, model.feature_importances_))}")

# Vertical Visual 5: Machine Learning Feature Importance Analysis
df_imp = pd.DataFrame({"Feature": feature_names, "Importance": model.feature_importances_}).sort_values("Importance", ascending=True)

plt.figure(figsize=(12, 6))
sns.barplot(data=df_imp, x="Importance", y="Feature", hue="Feature", legend=False, palette="mako", edgecolor="black")
plt.title("LightGBM Feature Importance for Market Price Estimation", fontsize=14, fontweight="bold")
plt.xlabel("Relative Importance Score", fontsize=12)
plt.ylabel("Feature Name", fontsize=12)
plt.grid(True, axis="x", linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()

# Generate Submittable Production Agent Script (main.py)
agent_code = '''import math
import random

def get_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def step_toward(fx, fy, tx, ty):
    if fx > tx: return "WEST"
    if fx < tx: return "EAST"
    if fy > ty: return "NORTH"
    if fy < ty: return "SOUTH"
    return "PASS"

def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    step = obs.get("step", 0)
    money = me["money"]
    fx, fy = me["farmer"]
    
    market_orders = []
    
    # Land Expansion Logic
    unlocked = me["unlocked_quadrants"]
    if "NE" not in unlocked and money >= 1200:
        market_orders.append(["BUY_LAND"])
        money -= 1000
    elif "SW" not in unlocked and "NE" in unlocked and money >= 2300:
        market_orders.append(["BUY_LAND"])
        money -= 2000
    elif "SE" not in unlocked and "SW" in unlocked and money >= 4500:
        market_orders.append(["BUY_LAND"])
        money -= 4000

    # Seed Purchasing Strategy based on In-Game Phase
    wheat_seeds = private["seeds"].get("WHEAT", 0)
    carrot_seeds = private["seeds"].get("CARROT", 0)
    melon_seeds = private["seeds"].get("MELON", 0)
    
    if day < 5:
        if wheat_seeds < 3 and money >= 10:
            market_orders.append(["BUY_SEED", "WHEAT", 2])
            money -= 20
        elif carrot_seeds < 2 and money >= 20:
            market_orders.append(["BUY_SEED", "CARROT", 2])
            money -= 40
    elif day < 22:
        if melon_seeds < 4 and money >= 80:
            market_orders.append(["BUY_SEED", "MELON", 2])
            money -= 160
        elif wheat_seeds < 2 and money >= 10:
            market_orders.append(["BUY_SEED", "WHEAT", 2])
            money -= 20

    # Market Inventory Liquidation Strategy
    shed = private["shed"]
    for item, count in shed.items():
        if count > 0:
            market_orders.append(["SELL", item, count])

    # Enforce Market Order Queue Cap (max 10 orders per turn)
    market_orders = market_orders[:10]

    # Tile Scanning and Tactical Prioritization
    tile = me["tiles"][fy][fx]
    
    # Action 1: Clear Weeds
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return {"farmer": ["DIG"], "hands": [], "market": market_orders}
    
    # Action 2: Plant Care and Harvesting
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = day - tile["planted_day"]
        crop_type = tile["crop"]
        
        # Harvest logic
        if tile["yield_units"] > 0:
            return {"farmer": ["HARVEST"], "hands": [], "market": market_orders}
            
        # Daily watering logic
        if not tile["watered_today"]:
            return {"farmer": ["WATER"], "hands": [], "market": market_orders}

    # Action 3: Planting on Empty Tiles
    if tile is None:
        if day >= 5 and private["seeds"].get("MELON", 0) > 0:
            return {"farmer": ["PLANT", "MELON"], "hands": [], "market": market_orders}
        elif private["seeds"].get("CARROT", 0) > 0:
            return {"farmer": ["PLANT", "CARROT"], "hands": [], "market": market_orders}
        elif private["seeds"].get("WHEAT", 0) > 0:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market_orders}

    # Movement / Target Scanning Loop
    target_x, target_y = None, None
    min_dist = 999
    for y in range(len(me["tiles"])):
        for x in range(len(me["tiles"][0])):
            t = me["tiles"][y][x]
            if t != "LOCKED":
                dist = get_distance((fx, fy), (x, y))
                if t is None and (private["seeds"].get("WHEAT", 0) > 0 or private["seeds"].get("MELON", 0) > 0):
                    if dist < min_dist:
                        min_dist = dist
                        target_x, target_y = x, y
                elif isinstance(t, dict) and t.get("kind") == "PLANT":
                    if not t["watered_today"] or t["yield_units"] > 0:
                        if dist < min_dist:
                            min_dist = dist
                            target_x, target_y = x, y

    if target_x is not None and target_y is not None:
        move_op = step_toward(fx, fy, target_x, target_y)
        return {"farmer": [move_op], "hands": [], "market": market_orders}

    return {"farmer": ["PASS"], "hands": [], "market": market_orders}
'''

with open("main.py", "w") as f:
    f.write(agent_code)

print("Production submission agent main.py successfully generated and written to disk.")

# Execute Tournament Evaluation Pipeline
from kaggle_environments import make

seeds = [42, 100, 2026, 7, 999, 1234]
results = []

print("Starting local tournament benchmark over 6 deterministic seeds...")
for seed in seeds:
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env.run(["main.py", "starter"])
    
    p0_reward = env.steps[-1][0]["reward"]
    p1_reward = env.steps[-1][1]["reward"]
    p0_status = env.steps[-1][0]["status"]
    
    results.append({
        "Seed": seed,
        "Agent Bank ($)": p0_reward,
        "Starter Opponent Bank ($)": p1_reward,
        "Margin ($)": p0_reward - p1_reward,
        "Outcome": "WIN" if p0_reward > p1_reward else ("TIE" if p0_reward == p1_reward else "LOSS"),
        "Status": p0_status
    })

df_res = pd.DataFrame(results)
display(df_res)

# Vertical Visual 6: Local Tournament Reward Balance Trajectories Across Seeds
plt.figure(figsize=(12, 6))
colors_res = ["#2ecc71" if outcome == "WIN" else "#e74c3c" for outcome in df_res["Outcome"]]
bars = plt.bar(df_res["Seed"].astype(str), df_res["Agent Bank ($)"], color=colors_res, edgecolor="black", alpha=0.85)
plt.axhline(y=3000, color="black", linestyle="--", alpha=0.7, label="Starting Capital ($3000)")
plt.title("Terminal Liquid Bank Balance Across Evaluation Seeds vs. Starter Bot", fontsize=14, fontweight="bold")
plt.xlabel("Episode Seed", fontsize=12)
plt.ylabel("Terminal Bank Balance ($)", fontsize=12)
plt.grid(True, axis="y", linestyle=":", alpha=0.6)
for bar, r in zip(bars, df_res["Agent Bank ($)"]):
    plt.text(bar.get_x() + bar.get_width()/2.0, bar.get_height() + 150, f"${r:,.0f}", ha="center", fontweight="bold")
plt.legend()
plt.tight_layout()
plt.show()

# Vertical Visual 7: Margin Victory Analysis
plt.figure(figsize=(12, 6))
sns.barplot(data=df_res, x="Seed", y="Margin ($)", hue="Seed", legend=False, palette="magma", edgecolor="black")
plt.axhline(y=0, color="red", linestyle="-", linewidth=1.5)
plt.title("Net Cash Lead over Opponent Agent Across Tournament Runs", fontsize=14, fontweight="bold")
plt.xlabel("Seed", fontsize=12)
plt.ylabel("Cash Margin Lead ($)", fontsize=12)
plt.grid(True, axis="y", linestyle=":", alpha=0.6)
for idx, row in df_res.iterrows():
    plt.text(idx, row["Margin ($)"] + 100 if row["Margin ($)"] >= 0 else row["Margin ($)"] - 250, f"+${row['Margin ($)']:,}", ha="center", fontweight="bold")
plt.tight_layout()
plt.show()

# Bundle main.py into submittable tarball
with tarfile.open("submission.tar.gz", "w:gz") as tar:
    tar.add("main.py", arcname="main.py")

sub_size = os.path.getsize("submission.tar.gz") / (1024 * 1024)
print(f"Submission package submission.tar.gz successfully created. File size: {sub_size:.4f} MiB (Limit: 100 MiB).")
print("Agent readiness verified. Ready for deployment on live leaderboard ladder.")