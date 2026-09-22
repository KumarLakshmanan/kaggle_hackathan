%pip install -q "kaggle-environments==1.32.4"

import glob, math, os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (8, 4.2), "axes.grid": True, "grid.alpha": .25,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
})

from kaggle_environments.envs.kaggriculture import kaggriculture as K
try:
    from importlib.metadata import version as _pkg_version
    print("kaggle-environments", _pkg_version("kaggle-environments"))
except Exception:
    pass

SRC_LINES = open(K.__file__, encoding="utf-8").read().split("\n")
import inspect

def show_func(obj, title=None):
    "Print a referee function's real source, with its real line numbers."
    lines, start = inspect.getsourcelines(obj)
    print(f"--- {title or obj.__name__}  [lines {start}-{start+len(lines)-1}] ---")
    for i, line in enumerate(lines):
        print(f"{start + i:4d} | {line.rstrip()}")

def show_block(anchor, after=0, before=0, title=None):
    "Print lines around the first line containing `anchor` (line numbers move\n"
    "between releases, so we never hard-code a range)."
    hits = [i for i, l in enumerate(SRC_LINES) if anchor in l]
    if not hits:
        print(f"!! anchor not found in this version: {anchor!r}")
        return
    i = hits[0]
    lo, hi = max(0, i - before), min(len(SRC_LINES), i + after + 1)
    print(f"--- {title or anchor}  [lines {lo+1}-{hi}] ---")
    for j in range(lo, hi):
        print(f"{j + 1:4d} | {SRC_LINES[j].rstrip()}")

def find_csv(name):
    for pattern in (f"/kaggle/input/**/{name}", f"../input/**/{name}", name):
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return hits[0]
    raise SystemExit(f"{name} not found — attach jessicali9530/honey-production")

honey = pd.read_csv(find_csv("honeyproduction.csv"))
honey = honey[(honey.totalprod > 0) & (honey.priceperlb > 0)].copy()
print(f"{len(honey)} rows | {honey.state.nunique()} states | "
      f"{honey.year.min()}-{honey.year.max()}")
honey.head()

nat = honey.groupby("year").agg(supply=("totalprod", "sum"),
                                price=("priceperlb", "mean")).reset_index()
slope_naive = np.polyfit(np.log(nat.supply), np.log(nat.price), 1)[0]
r_naive = np.corrcoef(np.log(nat.supply), np.log(nat.price))[0, 1]
print(f"naive elasticity: {slope_naive:.2f}   (r = {r_naive:.2f}, n = {len(nat)})")
nat.assign(supply_Mlb=(nat.supply / 1e6).round(1))[["year", "supply_Mlb", "price"]]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
a1.plot(nat.year, nat.supply / 1e6, "o-", color="#2b6cb0")
a1.set_title("US honey supply"); a1.set_ylabel("million lb"); a1.set_xlabel("year")
a2.plot(nat.year, nat.price, "o-", color="#c05621")
a2.set_title("average price"); a2.set_ylabel("$/lb"); a2.set_xlabel("year")
plt.tight_layout(); plt.show()

rows = []
for name, s in [("log supply", np.log(nat.supply)), ("log price", np.log(nat.price))]:
    slope = np.polyfit(nat.year, s, 1)[0]
    r = np.corrcoef(nat.year, s)[0, 1]
    rows.append({"series": name, "trend per year": round(slope, 4),
                 "r with year": round(r, 2), "R2 on year alone": round(r ** 2, 2)})
pd.DataFrame(rows).set_index("series")

def ols_fe(df, y, x, absorb=()):
    "log-log OLS with dummy fixed effects. Returns (beta, se, R2, n)."
    Y = np.log(df[y].values)
    cols = [np.ones(len(df)), np.log(df[x].values)]
    for col in absorb:
        codes = pd.Categorical(df[col]).codes
        for k in range(1, codes.max() + 1):     # first level is the reference
            cols.append((codes == k).astype(float))
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    dof = len(df) - X.shape[1]
    s2 = resid @ resid / dof
    se = math.sqrt(s2 * np.linalg.pinv(X.T @ X)[1, 1])
    r2 = 1 - (resid @ resid) / ((Y - Y.mean()) @ (Y - Y.mean()))
    return beta[1], se, r2, len(df)

specs = [("pooled (no fixed effects)", ()),
         ("year fixed effects", ("year",)),
         ("year + state fixed effects", ("year", "state"))]
out = []
for label, absorb in specs:
    b, se, r2, n = ols_fe(honey, "priceperlb", "totalprod", absorb)
    out.append({"specification": label, "elasticity": round(b, 3),
                "std err": round(se, 3),
                "95% CI": f"[{b - 1.96*se:+.2f}, {b + 1.96*se:+.2f}]",
                "R2": round(r2, 2), "n": n})
panel = pd.DataFrame(out).set_index("specification")
panel

fig, ax = plt.subplots(figsize=(8, 3.4))
labels = ["naive\n(national, no FE)"] + [s[0].replace(" ", "\n", 1) for s in specs]
vals = [slope_naive] + [float(panel.loc[s[0], "elasticity"]) for s in specs]
errs = [0] + [1.96 * float(panel.loc[s[0], "std err"]) for s in specs]
ax.bar(labels, vals, yerr=errs, capsize=4,
       color=["#a0aec0", "#90cdf4", "#2b6cb0", "#1a365d"])
ax.axhline(0, color="black", lw=1)
ax.set_ylabel("price elasticity of supply\n(d log price / d log quantity)")
ax.set_title("The naive estimate is 16x the within-year one")
plt.tight_layout(); plt.show()

show_func(K.market_price)
show_block("price(inv) = base", after=11, before=1,
           title="the model, in the source's own words")

SHAPES = {
    "linear": (lambda x: x,               lambda x: 1.0),
    "sq":     (lambda x: x * x,           lambda x: 2 * x),
    "sqrt":   (lambda x: math.sqrt(x),    lambda x: 1 / (2 * math.sqrt(x))),
    "log":    (lambda x: math.log(1 + x), lambda x: 1 / (1 + x)),
    "log10":  (lambda x: math.log10(1+x), lambda x: 1 / ((1+x) * math.log(10))),
}

def game_elasticity(item, q):
    "d log P / d log Q for q units sold above neutral, before rounding/flooring."
    p = K.MARKET_PARAMS[item]
    f, df = SHAPES[p["above_func"]]
    amp = p["above_target"] * p["base"] / f(p["T"])
    P = p["base"] - amp * f(q)
    return np.nan if P <= 0 else (-amp * df(q)) * q / P

def floor_at(item, cap=5000):
    "Units of supply at which the quoted price reaches the floor."
    for q in range(1, cap + 1):
        if K.market_price(item, K.MARKET_I0 + q) <= K.PRICE_FLOOR:
            return q
    return None

ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]
rows = []
for it in ITEMS:
    T = K.MARKET_PARAMS[it]["T"]
    rows.append({"product": it, "T (one field-season)": T,
                 "base price": K.MARKET_PARAMS[it]["base"],
                 "@ T/10": round(game_elasticity(it, T * .10), 2),
                 "@ T/4": round(game_elasticity(it, T * .25), 2),
                 "@ T/2": round(game_elasticity(it, T * .50), 2),
                 "floor hit at": floor_at(it)})
game = pd.DataFrame(rows).set_index("product")
game

fig, ax = plt.subplots()
qs = np.linspace(0.02, 0.6, 120)
for it, colour in [("MELON", "#c05621"), ("STRAWBERRY", "#b83280"),
                   ("TOMATO", "#2b6cb0"), ("WHEAT", "#2f855a")]:
    T = K.MARKET_PARAMS[it]["T"]
    ax.plot(qs, [game_elasticity(it, T * f) for f in qs], label=it,
            color=colour, lw=2)
ax.axhline(-0.128, ls="--", color="black", lw=1.4,
           label="US honey, year FE (-0.13)")
ax.set_xlabel("supply sold, as a fraction of one field-season (T)")
ax.set_ylabel("elasticity (d log P / d log Q)")
ax.set_ylim(-5, 0.2)
ax.set_title("The game's elasticity is not a constant — it detonates")
ax.legend(frameon=False, fontsize=9)
plt.tight_layout(); plt.show()

HONEY_FE = float(panel.loc["year fixed effects", "elasticity"])
HONEY_STRICT = float(panel.loc["year + state fixed effects", "elasticity"])

verdict = []
for label, frac in [("a tenth of a field-season", .10),
                    ("a quarter", .25), ("half", .50)]:
    es = [game_elasticity(it, K.MARKET_PARAMS[it]["T"] * frac) for it in ITEMS]
    med = float(np.nanmedian(es))
    verdict.append({"volume sold": label, "game (median)": round(med, 2),
                    "US honey (year FE)": HONEY_FE,
                    "game / honey": round(med / HONEY_FE, 1)})
pd.DataFrame(verdict).set_index("volume sold")

n_floor = sum(1 for it in ITEMS
              if (floor_at(it) or 10 ** 9) <= K.MARKET_PARAMS[it]["T"])
print(f"products whose price hits the floor within one field-season: "
      f"{n_floor} of {len(ITEMS)}")
for it in ITEMS:
    q, T = floor_at(it), K.MARKET_PARAMS[it]["T"]
    if q and q <= T:
        print(f"   {it:<11} floor at {q} units = {100*q/T:.0f}% of T")