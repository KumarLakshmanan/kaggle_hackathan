%pip install -q "kaggle-environments==1.32.4"

import math, os, sys
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (8, 4.2), "axes.grid": True, "grid.alpha": .25,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
})

import kaggle_environments
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as K

SRC = K.__file__
SRC_LINES = open(SRC, encoding="utf-8").read().split("\n")
try:
    from importlib.metadata import version as _pkg_version
    _ver = _pkg_version("kaggle-environments")
except Exception:
    _ver = "unknown"
print("kaggle-environments", _ver)
print("referee source     ", SRC)

import inspect

def show_func(obj, title=None):
    "Print a referee function's real source, with its real line numbers."
    lines, start = inspect.getsourcelines(obj)
    name = title or obj.__name__
    print(f"--- {name}  [lines {start}-{start + len(lines) - 1}] ---")
    for i, line in enumerate(lines):
        print(f"{start + i:4d} | {line.rstrip()}")

def show_block(anchor, after=0, before=0, title=None):
    "Print the lines around the first line containing `anchor`."
    hits = [i for i, l in enumerate(SRC_LINES) if anchor in l]
    if not hits:
        print(f"!! anchor not found in this version: {anchor!r}")
        return
    i = hits[0]
    lo, hi = max(0, i - before), min(len(SRC_LINES), i + after + 1)
    print(f"--- {title or anchor}  [lines {lo + 1}-{hi}] ---")
    for j in range(lo, hi):
        print(f"{j + 1:4d} | {SRC_LINES[j].rstrip()}")

# Line numbers differ between kaggle-environments releases, so nothing below is
# hard-coded to a line range -- we look code up by symbol or by anchor text.

show_func(K.market_price)
show_func(K._refresh_prices)
show_block("price(inv) = base", after=11, before=1,
           title="the pricing model, in the source's own words")

params = pd.DataFrame(K.MARKET_PARAMS).T
params[["base", "T", "below_func", "below_target", "above_func", "above_target"]]

I0 = K.MARKET_I0
offsets = np.arange(0, 601)

fig, ax = plt.subplots()
for item, colour in [("MELON", "#c05621"), ("STRAWBERRY", "#b83280"),
                     ("MILK", "#2b6cb0"), ("WHEAT", "#2f855a")]:
    ax.plot(offsets, [K.market_price(item, I0 + int(o)) for o in offsets],
            label=item, color=colour, lw=2)
ax.set_xlabel("units sold into the market (inventory above neutral)")
ax.set_ylabel("unit price")
ax.set_title("What selling does to your own price")
ax.legend(frameon=False)
plt.tight_layout(); plt.show()

def fill_value(item, qty, inventory=None):
    "Total proceeds from selling `qty` units one at a time, and the naive figure."
    inv = K.MARKET_I0 if inventory is None else inventory
    fills = [K.market_price(item, inv + i) for i in range(qty)]
    return sum(fills), qty * fills[0], fills[0], fills[-1]

rows = []
for item in ["MELON", "STRAWBERRY", "MILK", "TOMATO", "CARROT", "WHEAT"]:
    for qty in (50, 100, 300):
        got, naive, first, last = fill_value(item, qty)
        rows.append({"product": item, "units": qty, "first unit": first,
                     "last unit": last, "actually got": got,
                     "naive (qty x first)": naive,
                     "% of naive": round(100 * got / naive)})
fills = pd.DataFrame(rows)
fills.pivot(index="product", columns="units", values="% of naive").loc[
    ["MELON", "STRAWBERRY", "MILK", "TOMATO", "CARROT", "WHEAT"]]

fills[fills["units"] == 300].set_index("product")[
    ["first unit", "last unit", "actually got", "naive (qty x first)", "% of naive"]]

fig, ax = plt.subplots()
for item, colour in [("MELON", "#c05621"), ("STRAWBERRY", "#b83280"),
                     ("MILK", "#2b6cb0"), ("WHEAT", "#2f855a")]:
    qs = np.arange(10, 401, 10)
    keep = [100 * fill_value(item, int(q))[0] / fill_value(item, int(q))[1] for q in qs]
    ax.plot(qs, keep, label=item, color=colour, lw=2)
ax.axhline(100, ls="--", color="grey", lw=1)
ax.set_xlabel("units sold in one order")
ax.set_ylabel("% of the naive value you actually receive")
ax.set_title("Big orders pay less per unit, and by wildly different amounts")
ax.set_ylim(0, 105); ax.legend(frameon=False)
plt.tight_layout(); plt.show()

show_func(K._town_consume)
show_block("SHOPS = {", after=14,
           title="SHOPS, TOWN_CENTER_PRODUCTS, TOWN_CENTER_DEMAND_SCHEDULE")

CFG = make("kaggriculture", debug=False).configuration
SHOP_SELL    = int(CFG.get("townShopSellInterval", 4))
CENTER_SELL  = int(CFG.get("townCenterSellInterval", 12))
UNLOCK_EVERY = int(CFG.get("townShopUnlockInterval", 3))
TPD          = int(CFG.get("turnsPerDay", 24))
print(f"shop sell every {SHOP_SELL} steps | town centre every {CENTER_SELL} "
      f"| a shop unlocks every {UNLOCK_EVERY} days | {TPD} turns/day")

def center_mult(day):
    return next(m for thr, m in K.TOWN_CENTER_DEMAND_SCHEDULE if day >= thr)

def absorbed_per_day(day, unlocked):
    "Units of each product the town removes on `day`, given the open shops."
    per = Counter()
    for shop in unlocked:
        products = K.SHOPS[shop]
        mult = 2 if len(products) == 1 else 1
        for p in products:
            per[p] += (TPD // SHOP_SELL) * mult
    for p in K.TOWN_CENTER_PRODUCTS:
        per[p] += (TPD // CENTER_SELL) * center_mult(day)
    return per

tiers = {label: absorbed_per_day(day, list(K.SHOPS)) for day, label in
         [(0, "day 0-9"), (10, "day 10-19"), (20, "day 20+")]}
demand = pd.DataFrame(tiers).fillna(0).astype(int)
demand.sort_values(demand.columns[-1], ascending=False)

fig, ax = plt.subplots(figsize=(8, 4.6))
demand.sort_values(demand.columns[-1]).plot.barh(
    ax=ax, width=.8, color=["#bee3f8", "#63b3ed", "#2b6cb0"])
ax.set_xlabel("units absorbed per day (all shops open)")
ax.set_title("Town demand per product, by season tier")
ax.legend(frameon=False, fontsize=9)
plt.tight_layout(); plt.show()

# What one day of town demand is worth at neutral inventory, day 20+.
per_day = absorbed_per_day(20, list(K.SHOPS))
pd.DataFrame([{"product": p, "absorbed/day": per_day[p],
               "price at I0": K.market_price(p, I0),
               "value of that drain": per_day[p] * K.market_price(p, I0)}
              for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY",
                        "MELON", "EGG", "MILK", "WOOL"]]
            ).set_index("product").sort_values("value of that drain",
                                               ascending=False)

show_block('action.get("farmer"', before=2, after=26,
           title="interpreter: how an action is unpacked")

show_block("q[:max_orders]", before=2, after=7, title="the ten-order cap")
show_func(K._parse_order, "_parse_order: orders carry a quantity")

show_block("quoted = [None, None]", before=6, after=37,
           title="_process_market: per-unit lockstep")

print("shedCapacity:", CFG.get("shedCapacity", 100))
show_func(K._shed_access_tiles, "_shed_access_tiles: the shed has four doors")
show_func(K._drop_inventories_to_shed,
          "_drop_inventories_to_shed: end of day")

# 80 units already banked, two hands carrying 30 each: what survives the night?
private = {"shed": {"WHEAT": 80},
           "inventories": [{"MELON": 30}, {"MELON": 30}],
           "seeds": {}}
before = (sum(private["shed"].values())
          + sum(n for inv in private["inventories"] for n in inv.values()))
K._drop_inventories_to_shed(private, int(CFG.get("shedCapacity", 100)))
after = sum(private["shed"].values())
print("held before the drop:", before)
print("in the shed after   :", after, private["shed"])
print("silently destroyed  :", before - after)

# How much a full shed is worth, and how quickly a day's harvest can exceed it.
rows = []
for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]:
    got, naive, first, last = fill_value(item, 100)
    rows.append({"product": item, "100 units, sold at once": got,
                 "per unit": round(got / 100, 1),
                 "% of naive": round(100 * got / naive)})
pd.DataFrame(rows).set_index("product").sort_values(
    "100 units, sold at once", ascending=False)

import glob

def find_dataset():
    "Locate whichever attached dataset carries episodes.csv (any depth)."
    for pattern in ("/kaggle/input/**/episodes.csv", "../input/**/episodes.csv",
                    "tmp/dsnew/episodes.csv", "tmp/ds/episodes.csv"):
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return os.path.dirname(hits[0])
    return None

BASE = find_dataset()
if BASE is None:
    print("episodes.csv not found. Visible inputs:")
    for p in sorted(glob.glob("/kaggle/input/*")):
        print("   ", p, sorted(os.listdir(p))[:6])
    raise SystemExit(
        "Attach georgymamarin/kaggriculture-episodes and re-run this section.")
print("dataset:", BASE)

episodes = pd.read_csv(os.path.join(BASE, "episodes.csv"))
feats    = pd.read_csv(os.path.join(BASE, "episode_features.csv"))
print(f"{len(episodes):,} episodes, {len(feats):,} agent-episode rows")
print(episodes["type"].value_counts().to_string())

public = set(episodes.loc[episodes["type"] == "EPISODE_TYPE_PUBLIC", "episode_id"])
feats  = feats[feats["episode_id"].isin(public)].copy()

ratings = pd.concat([
    episodes[["episode_id", "rating_0"]].rename(columns={"rating_0": "rating"}).assign(seat=0),
    episodes[["episode_id", "rating_1"]].rename(columns={"rating_1": "rating"}).assign(seat=1),
])
df = feats.merge(ratings, on=["episode_id", "seat"], how="inner").dropna(
    subset=["rating", "final_money"])
print(f"{len(df):,} ladder agent-episodes with both a rating and a final bank")

EDGES  = [0, 750, 1250, 1750, 2250, 2750, 10 ** 9]
LABELS = ["~500", "~1000", "~1500", "~2000", "~2500", "3000+"]
df["band"] = pd.cut(df["rating"], bins=EDGES, labels=LABELS, right=False)

bands = df.groupby("band", observed=True)["final_money"].agg(
    n="size", q1=lambda s: s.quantile(.25), median="median",
    q3=lambda s: s.quantile(.75)).round(0).astype(int)
bands

fig, ax = plt.subplots()
order = [b for b in LABELS if b in bands.index]
# NB: matplotlib renamed boxplot's `labels` to `tick_labels` in 3.9, so we set the
# tick labels ourselves and stay version-agnostic.
ax.boxplot([df.loc[df["band"] == b, "final_money"] for b in order],
           showfliers=False, widths=.6,
           medianprops=dict(color="#c05621", lw=2))
ax.set_xticks(range(1, len(order) + 1)); ax.set_xticklabels(order)
ax.set_xlabel("rating band"); ax.set_ylabel("final money (coins)")
ax.set_title("Money stops separating agents early, and then stays flat")
ax.yaxis.set_major_formatter(lambda v, p: f"{v:,.0f}")
plt.tight_layout(); plt.show()

pd.DataFrame({"median money": bands["median"],
              "gain over previous band": bands["median"].diff()}
             ).fillna(0).astype(int)