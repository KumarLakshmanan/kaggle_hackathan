import kaggle_environments as ke
from kaggle_environments import make

print("kaggle-environments version:", ke.__version__)
env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
print("env ready:", env.name)

import json, pandas as pd, matplotlib.pyplot as plt

with open("/kaggle/input/datasets/rakhansyah/kaggriculture-trace-results/trace_veg.json") as f:
    trace = json.load(f)

BASE_MIX = {"STRAWBERRY": 0.6, "WHEAT": 0.1, "CARROT": 0.15, "TOMATO": 0.15}
MIX_CROPS = list(BASE_MIX.keys())
PLANT_CROPS = MIX_CROPS + ["MELON"]

rows = []
for gi, g in enumerate(trace["games"]):
    for d in g["per_day"]:
        rows.append({
            "game": gi, "day": d["day"],
            **{f"mix_{c}": d["dynamic_mix"].get(c, 0.0) for c in MIX_CROPS},
            **{f"planted_{c}": d["planted_counts"].get(c, 0) for c in PLANT_CROPS},
        })
df = pd.DataFrame(rows)

avg_dyn = df[df.game == 0][[f"mix_{c}" for c in MIX_CROPS]].mean()
x = range(len(MIX_CROPS)); w = 0.38
plt.figure(figsize=(9, 5))
plt.bar([i - w/2 for i in x], [BASE_MIX[c] for c in MIX_CROPS], w, label="base recipe")
plt.bar([i + w/2 for i in x], [avg_dyn[f"mix_{c}"] for c in MIX_CROPS], w,
        label="dynamic mix (avg planned)")
plt.xticks(list(x), MIX_CROPS); plt.ylabel("share of plantable tiles")
plt.legend(); plt.title("Recipe vs what the mix formula plans")
plt.tight_layout()

g0 = df[df.game == 0].set_index("day")
cols = [f"planted_{c}" for c in PLANT_CROPS]
frac = g0[cols].div(g0[cols].sum(axis=1), axis=0).fillna(0)
frac.plot.area(stacked=True, figsize=(9, 5),
               title="Realized crop mix over days (Hinge heavy game)")
plt.ylabel("share of occupied tiles"); plt.xlabel("day")
plt.tight_layout()


with open("/kaggle/input/datasets/rakhansyah/kaggriculture-trace-results/trace_ani.json") as f:
    trace = json.load(f)

rows = []
for gi, g in enumerate(trace["games"]):
    for d in g["per_day"]:
        rows.append({
            "game": gi, "day": d["day"],
            **{f"mix_{c}": d["dynamic_mix"].get(c, 0.0) for c in MIX_CROPS},
            **{f"planted_{c}": d["planted_counts"].get(c, 0) for c in PLANT_CROPS},
        })
df = pd.DataFrame(rows)

avg_dyn = df[df.game == 0][[f"mix_{c}" for c in MIX_CROPS]].mean()
x = range(len(MIX_CROPS)); w = 0.38
plt.figure(figsize=(9, 5))
plt.bar([i - w/2 for i in x], [BASE_MIX[c] for c in MIX_CROPS], w, label="base recipe")
plt.bar([i + w/2 for i in x], [avg_dyn[f"mix_{c}"] for c in MIX_CROPS], w,
        label="dynamic mix (avg planned)")
plt.xticks(list(x), MIX_CROPS); plt.ylabel("share of plantable tiles")
plt.legend(); plt.title("Recipe vs what the mix formula plans")
plt.tight_layout()

g0 = df[df.game == 0].set_index("day")
cols = [f"planted_{c}" for c in PLANT_CROPS]
frac = g0[cols].div(g0[cols].sum(axis=1), axis=0).fillna(0)
frac.plot.area(stacked=True, figsize=(9, 5),
               title="Realized crop mix over days (Animal heavy game)")
plt.ylabel("share of occupied tiles"); plt.xlabel("day")
plt.tight_layout()

import json, numpy as np, matplotlib.pyplot as plt

MARKET_PARAMS = {
    "WHEAT": {"base": 25, "I0": 10000, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
    "CARROT": {"base": 35, "I0": 10000, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
    "TOMATO": {"base": 60, "I0": 10000, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON": {"base": 250, "I0": 10000, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
    "EGG": {"base": 50, "I0": 10000, "T": 332, "below_func": "hinge", "below_target": 0.40, "above_func": "log", "above_target": 0.20},
    "MILK": {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt", "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL": {"base": 200, "I0": 10000, "T": 105, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

def hinge_price(crop, inv):
    P = MARKET_PARAMS[crop]
    I0, T, base, tgt = 10000, P["T"], P["base"], P["below_target"]
    u = (I0 - inv) / T
    return base + base * tgt * (u + 8.0 * max(0.0, u - 1.0) ** 2)

with open("/kaggle/input/datasets/rakhansyah/kaggriculture-trace-results/trace_veg.json") as f:
    trace = json.load(f)

CROPS = {"CARROT": "tab:orange", "TOMATO": "tab:red"}
I0 = 10000

fig, ax = plt.subplots(figsize=(12, 6))

ax.set_xlim(9400, I0)
ax.set_ylim(0, 250)

for crop, color in CROPS.items():
    P = MARKET_PARAMS[crop]; T = P["T"]
    trigger, knee = I0 - 0.35*T, I0 - T
    inv = np.linspace(9400, I0, 400)
    ax.plot(inv, [hinge_price(crop, v) for v in inv], color=color, lw=2,
            label=f"{crop} price curve")
    ax.axvline(trigger, color=color, ls="--", lw=1.2,
               label=f"{crop} hinge trigger ({trigger:.0f})")
    ax.axvline(knee, color=color, ls=":", lw=1.2,
               label=f"{crop} knee ({knee:.0f})")
    ax.axvspan(9400, trigger, color=color, alpha=0.05)

for crop, color in CROPS.items():
    for gi, g in enumerate(trace["games"]):
        xs_on, ys_on = [], []
        for i, d in enumerate(g["per_day"]):
            if crop not in d["inventory"]:
                continue
            if bool(d["hinge_triggered"][crop]):
                xs_on.append(d["inventory"][crop]); ys_on.append(d["prices"][crop])
            if xs_on:
                xs_on, ys_on = xs_on[:1], ys_on[:1]
        ax.scatter(xs_on, ys_on, s=70, c=color, edgecolor="k",
                   linewidths=0.4, alpha=0.85, label=f"{crop} hinge ON" if gi == 0 else None)


for crop, color in CROPS.items():
    for gi, g in enumerate(trace["games"]):
        ev = [e for e in g.get("sales", []) if e.get("crop") == crop]
        if not ev:
            continue
        base_y = [hinge_price(crop, e["inventory"]) for e in ev]
        sales_x = [e["inventory"] for e in ev]
        sales_y = [b + 15 for b in base_y]
        sizes   = [min(40 + 2.2 * e["qty"], 220) for e in ev]
        ax.vlines(sales_x, base_y, sales_y, colors=color, lw=0.8, alpha=0.45, zorder=5)
        ax.scatter(sales_x, sales_y, s=sizes, facecolors="white",
                   edgecolors=color, linewidths=2.2, zorder=10,
                   label=f"{crop} SALES (n={sum(e['qty'] for e in ev)})" if gi == 0 else None)

ax.set_xlabel("market inventory (shared, I0 = 10000)")
ax.set_ylabel("sale price ($)")
ax.set_title("CARROT & TOMATO hinge curve")
ax.legend(fontsize=8); ax.grid(alpha=0.3); plt.tight_layout()
plt.show()

import math


def _shape(func, value, T=None):
    if func == "linear": return value
    if func == "sqrt":   return math.sqrt(value)
    if func == "log":    return math.log1p(value)
    if func == "sq":     return value * value
    if func == "log10":  return math.log10(1.0 + value)
    if func == "hinge":
        u = value / T if T else value
        return u + 8.0 * max(0.0, u - 1.0) ** 2

def price_at(crop, inv):
    P = MARKET_PARAMS[crop]; I0, base, T = 10000, P["base"], P["T"]
    if inv < I0:
        f = _shape(P["below_func"], I0 - inv, T)
        amp = P["below_target"] * base / _shape(P["below_func"], T, T)
        return max(1, round(base + amp * f))
    if inv > I0:
        f = _shape(P["above_func"], inv - I0, T)
        amp = P["above_target"] * base / _shape(P["above_func"], T, T)
        return max(1, round(base - amp * f))
    return base

SEED  = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
YIELD = {"WHEAT": 4,  "CARROT": 3,  "TOMATO": 4,  "STRAWBERRY": 4,   "MELON": 6}
CYCLE = {"WHEAT": 5,  "CARROT": 4,  "TOMATO": 12, "STRAWBERRY": 17,  "MELON": 11}

def profit_per_tileday(crop, price):
    return (YIELD[crop] * price - SEED[crop]) / CYCLE[crop]

scenarios = [10000, 9800, 9500]
rows = []
for c in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
    row = {"crop": c, "seed": SEED[c], "yield": YIELD[c], "cycle": CYCLE[c]}
    for inv in scenarios:
        row[f"price@{inv}"] = price_at(c, inv)
        row[f"profit@{inv}"] = round(profit_per_tileday(c, price_at(c, inv)), 1)
    rows.append(row)
profit_df = pd.DataFrame(rows)

order = profit_df.sort_values("profit@10000", ascending=False)["crop"].tolist()
fig, ax = plt.subplots(figsize=(9, 5.5))
y = np.arange(len(order)); h = 0.36
ax.barh(y + h/2, profit_df.set_index("crop").loc[order, "profit@10000"], height=h,
        color="#8e9aaf", label="base (inv 10000)")
ax.barh(y, profit_df.set_index("crop").loc[order, "profit@9800"], height=h,
        color="#e9c46a", label="mild scarcity (inv 9800)")
ax.barh(y - h/2, profit_df.set_index("crop").loc[order, "profit@9500"], height=h,
        color="#2a9d8f", label="deep scarcity (inv 9500)")
ax.set_yticks(y, order); ax.set_xlabel("profit per tile-day (coins)")
ax.set_title("profit per tile-day by crop — base vs deep scarcity")
ax.legend(); ax.grid(axis="x", alpha=0.3); plt.tight_layout(); plt.show()


import json, pandas as pd, matplotlib.pyplot as plt

with open("/kaggle/input/datasets/rakhansyah/kaggriculture-trace-results/results.json") as f:
    res = json.load(f)

df = pd.DataFrame(res["games"])
order = ["market_system", "queue_rewrite", "v1_greedy"]
summary = df.groupby("era").agg(
    mean=("margin", "mean"), median=("margin", "median"), std=("margin", "std"),
    wins=("win", "sum"), n=("margin", "size"),
)
summary["win_rate"] = summary["wins"] / summary["n"]

fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#c0392b", "#e67e22", "#27ae60"]
df.boxplot(column="margin", by="era", ax=ax, positions=range(3),
           return_type="axes")
fig.suptitle("")
ax.scatter(range(3), summary.loc[order, "mean"], color=colors, s=80, zorder=3,
           label="mean margin", )
means = summary.loc[order, "mean"]

for i in enumerate(means):
    ax.annotate(f"{i[1]:.0f}", (i[0], i[1]), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=9, fontweight="bold", color=colors[i[0]])

ax.axhline(0, color="k", lw=0.8)
ax.set_title("Margin vs Frontier per era")
ax.set_ylabel("final money − frontier money")
plt.tight_layout()