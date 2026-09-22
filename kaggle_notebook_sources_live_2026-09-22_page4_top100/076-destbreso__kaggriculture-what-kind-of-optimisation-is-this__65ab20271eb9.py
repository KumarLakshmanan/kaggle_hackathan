# The engine's own unit operations, from kaggriculture.py. Quantities and
# legality are ignored, so this is a floor on the branching factor rather than
# an estimate of it.
MOVES = ["N", "S", "E", "W"]
TILE_OPS = ["PASS", "WATER", "HARVEST", "FERTILIZE", "DIG", "BUILD_COOP",
            "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE", "DROP"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
CARRIABLE = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
             "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]

per_unit = (len(MOVES) + len(TILE_OPS) + len(CROPS)          # PLANT x crop
            + len(CARRIABLE) + len(CARRIABLE))               # PICKUP, PLACE
UNITS = 13          # the farmer plus up to twelve hands
TURNS = 720

print(f"distinct operations for ONE unit, ignoring quantities : {per_unit}")
print(f"units acting on the same turn                          : {UNITS}")
print(f"joint unit-action space per turn                       : {per_unit}^{UNITS}"
      f" = {per_unit**UNITS:.2e}")
print(f"turns in a season                                      : {TURNS}")
print(f"\nand the market list is a further choice of up to 10 orders on top of that.")

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 120,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
})
TEAL, AMBER, INK, GREY, RED = "#0F766E", "#B45309", "#0F172A", "#94A3B8", "#B91C1C"

# Engine constants, kaggriculture.py. The glut branch, which is where a season
# spends almost all of itself: inventory only rises when someone sells.
I0, FLOOR = 10_000, 1
CURVE = {"WHEAT": ("log", 0.20, 400, 25), "CARROT": ("sqrt", 0.70, 450, 35),
         "TOMATO": ("sqrt", 0.60, 200, 60), "STRAWBERRY": ("linear", 1.60, 100, 120),
         "MELON": ("sq", 3.60, 300, 250), "EGG": ("log", 0.20, 332, 50),
         "MILK": ("linear", 1.60, 122, 160), "WOOL": ("sq", 3.20, 105, 200),
         "FERTILIZER": ("linear", 0.40, 200, 100)}

def shape(f, x):
    x = np.maximum(x, 0.0)
    return {"linear": x, "sq": x * x, "sqrt": np.sqrt(x),
            "log": np.log1p(x)}[f]

def price(item, sold):
    f, target, T, base = CURVE[item]
    amp = target * base / shape(f, T)
    return np.maximum(FLOOR, np.round(base - amp * shape(f, sold)))

sold = np.arange(0, 401)
rows = []
for item in CURVE:
    p = price(item, sold)
    floored = np.argmax(p <= FLOOR) if (p <= FLOOR).any() else len(sold)
    rows.append({"good": item, "base price": CURVE[item][3],
                 "units to reach the $1 floor": int(floored) if floored else None,
                 "total revenue to the floor": int(p[:floored].sum()) if floored else None})
purse = pd.DataFrame(rows).sort_values("units to reach the $1 floor")
display(purse)

fig, ax = plt.subplots(figsize=(8.6, 4.6))
order = purse.good.tolist()
cmap = plt.cm.viridis(np.linspace(0.05, 0.9, len(order)))
for c, item in zip(cmap, order):
    p = price(item, sold)
    ax.plot(sold, p, lw=2, color=c, label=item)
    k = int(np.argmax(p <= FLOOR)) if (p <= FLOOR).any() else None
    if k:
        ax.plot([k], [p[k]], "o", ms=5, color=c)
        ax.annotate(f"{item.title()} {k}", (k, 6), rotation=90, fontsize=7.5,
                    color=c, ha="center", va="bottom")
ax.set_xlim(0, 400); ax.set_ylim(0, 265)
ax.set_xlabel("units of this good sold into the market, by BOTH farms together")
ax.set_ylabel("price of the next unit ($)")
ax.set_title("Every good has a cliff, and it is closer than it looks", loc="left")
ax.legend(ncol=3, frameon=False, fontsize=8, loc="upper right")
plt.tight_layout(); plt.show()

OBJ = pd.DataFrame([{"mean": -4075.9, "wins": 3, "tanh": -0.5392740557869817}, {"mean": -6906.85, "wins": 2, "tanh": -0.6432665052125875}, {"mean": -7390.35, "wins": 2, "tanh": -0.6772425796233669}, {"mean": -13200.35, "wins": 1, "tanh": -0.8946506471351393}, {"mean": -13343.5, "wins": 1, "tanh": -0.897597841295033}, {"mean": -8845.15, "wins": 1, "tanh": -0.8302435253947179}, {"mean": -40574.05, "wins": 0, "tanh": -0.9999611832310247}, {"mean": -10230.45, "wins": 2, "tanh": -0.8155852456880346}, {"mean": -36197.5, "wins": 0, "tanh": -0.9999939161436711}, {"mean": -597.7, "wins": 9, "tanh": -0.11903997368828956}, {"mean": -4943.5, "wins": 2, "tanh": -0.5907181549802462}, {"mean": -18449.85, "wins": 0, "tanh": -0.9673898133324619}, {"mean": -1355.9, "wins": 8, "tanh": -0.22294735011614933}, {"mean": -8256.6, "wins": 1, "tanh": -0.8563702797329981}, {"mean": -28071.2, "wins": 0, "tanh": -0.9988248570932896}, {"mean": -2944.15, "wins": 4, "tanh": -0.42312083324289995}, {"mean": -1259.6, "wins": 4, "tanh": -0.2829884182228754}, {"mean": -27679.3, "wins": 0, "tanh": -0.9995003169068444}, {"mean": -1962.4, "wins": 4, "tanh": -0.38765268375253936}, {"mean": -3527.4, "wins": 4, "tanh": -0.48587379932920516}, {"mean": -4760.1, "wins": 3, "tanh": -0.5909031877149981}, {"mean": -23052.2, "wins": 0, "tanh": -0.9917945068309176}, {"mean": -409.05, "wins": 9, "tanh": -0.11101672737786183}, {"mean": -12882.4, "wins": 0, "tanh": -0.9482381626922576}, {"mean": -17111.65, "wins": 0, "tanh": -0.9694602738739686}, {"mean": -3920.7, "wins": 4, "tanh": -0.4936473193639254}, {"mean": -25997.5, "wins": 0, "tanh": -0.9983283432885589}, {"mean": -1709.15, "wins": 5, "tanh": -0.2985202191703994}, {"mean": -27587.75, "wins": 0, "tanh": -0.998063799184284}, {"mean": -2343.0, "wins": 3, "tanh": -0.42345032921799186}, {"mean": -7676.65, "wins": 2, "tanh": -0.7004562956294178}, {"mean": -3522.25, "wins": 4, "tanh": -0.48577496084318766}, {"mean": -9153.05, "wins": 1, "tanh": -0.8465678616434168}, {"mean": -9474.85, "wins": 1, "tanh": -0.8496683095507775}, {"mean": -13912.65, "wins": 1, "tanh": -0.8993191989795124}, {"mean": -30346.75, "wins": 0, "tanh": -0.9998064794264749}, {"mean": -5140.95, "wins": 2, "tanh": -0.6115730396928061}, {"mean": -7822.6, "wins": 2, "tanh": -0.6638833769919779}, {"mean": -24920.75, "wins": 0, "tanh": -0.99853099281872}, {"mean": -11688.65, "wins": 1, "tanh": -0.8846306158308239}, {"mean": -78749.95, "wins": 0, "tanh": -0.9999999957732989}, {"mean": -13926.8, "wins": 1, "tanh": -0.9074578244627409}, {"mean": -77702.1, "wins": 0, "tanh": -0.9999999999146999}, {"mean": -17437.4, "wins": 1, "tanh": -0.9405878729080202}, {"mean": -9380.35, "wins": 1, "tanh": -0.8814431835261136}, {"mean": -3611.0, "wins": 4, "tanh": -0.469621748189416}, {"mean": -1382.35, "wins": 8, "tanh": -0.23054810397633885}, {"mean": -5044.55, "wins": 2, "tanh": -0.6014933965430938}, {"mean": -4889.25, "wins": 2, "tanh": -0.6264356743571782}, {"mean": -8327.6, "wins": 1, "tanh": -0.8535303934982542}, {"mean": -3697.45, "wins": 4, "tanh": -0.47849240184060315}, {"mean": -5364.2, "wins": 2, "tanh": -0.676222882958947}, {"mean": -9388.45, "wins": 1, "tanh": -0.8348178770580004}, {"mean": -7820.25, "wins": 2, "tanh": -0.7251463507046024}, {"mean": -10538.65, "wins": 1, "tanh": -0.857710063113853}, {"mean": -4391.0, "wins": 2, "tanh": -0.5552462588995428}, {"mean": -16447.95, "wins": 0, "tanh": -0.9734476806504062}, {"mean": -21604.6, "wins": 0, "tanh": -0.9836424702944113}, {"mean": -20041.35, "wins": 0, "tanh": -0.9708281087609445}, {"mean": -1355.05, "wins": 8, "tanh": -0.21965509988862494}, {"mean": -27981.1, "wins": 0, "tanh": -0.9988264100538131}, {"mean": -26618.9, "wins": 0, "tanh": -0.9979148887723877}, {"mean": -26466.6, "wins": 0, "tanh": -0.9993754032538895}, {"mean": -306.55, "wins": 9, "tanh": -0.08974057961681874}, {"mean": -22053.55, "wins": 0, "tanh": -0.9914687072770432}, {"mean": -4540.55, "wins": 2, "tanh": -0.575419720373231}, {"mean": -930.3, "wins": 8, "tanh": -0.20596912561935107}, {"mean": -864.75, "wins": 6, "tanh": -0.21371128376026358}, {"mean": -26879.95, "wins": 0, "tanh": -0.994213232582767}, {"mean": -495.35, "wins": 8, "tanh": -0.1336900668336121}, {"mean": -23862.75, "wins": 0, "tanh": -0.9905994186088739}, {"mean": -22480.3, "wins": 0, "tanh": -0.9886702535938247}, {"mean": -10900.45, "wins": 1, "tanh": -0.8624228434313336}, {"mean": -7642.15, "wins": 2, "tanh": -0.6982351752124989}, {"mean": -6819.1, "wins": 2, "tanh": -0.6869407328214823}, {"mean": -13483.75, "wins": 1, "tanh": -0.9026269790743466}, {"mean": -11684.05, "wins": 1, "tanh": -0.8847816164688673}, {"mean": -13387.15, "wins": 1, "tanh": -0.8980139154803023}, {"mean": -6667.45, "wins": 2, "tanh": -0.7182777987133069}, {"mean": -37150.3, "wins": 0, "tanh": -0.9999445041313757}])
SCALE = 4000.0
N_MATCH = 20
print(f"{len(OBJ)} configurations, {N_MATCH} matchups each "
      f"(research/objective_disagreement.py)")

def spearman(a, b):
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(ra.corr(rb))

print(f"\nSpearman rank correlation with the win rate")
print(f"  mean margin     {spearman(OBJ['mean'], OBJ['wins']):+.3f}")
print(f"  tanh surrogate  {spearman(OBJ['tanh'], OBJ['wins']):+.3f}")

pick_mean = OBJ['mean'].idxmax(); pick_tanh = OBJ['tanh'].idxmax()
pick_wins = OBJ['wins'].idxmax()
print(f"\nThe configuration each objective would choose")
for name, i in [("mean margin", pick_mean), ("tanh surrogate", pick_tanh),
                ("win rate", pick_wins)]:
    print(f"  by {name:<15} {OBJ.wins[i]:>2}/{N_MATCH} wins, "
          f"mean margin {OBJ['mean'][i]:>+9,.0f}")
print(f"\n  optimising the mean instead of the win rate costs "
      f"{OBJ.wins[pick_wins] - OBJ.wins[pick_mean]} wins")

fig, ax = plt.subplots(figsize=(8.2, 4.6))
sc = ax.scatter(OBJ["mean"], OBJ["wins"], s=44, c=OBJ["tanh"], cmap="viridis",
                edgecolor="white", linewidth=0.5, zorder=3)
for i, col, name in [(pick_mean, RED, "picked by mean margin"),
                     (pick_wins, TEAL, "picked by win rate")]:
    ax.scatter([OBJ["mean"][i]], [OBJ["wins"][i]], s=220, facecolor="none",
               edgecolor=col, linewidth=2.4, zorder=4)
    ax.annotate(name, (OBJ["mean"][i], OBJ["wins"][i]),
                textcoords="offset points", xytext=(8, 10), fontsize=8.5,
                color=col, fontweight="bold")
ax.set_xlabel("mean paired margin over the matchups ($)")
ax.set_ylabel(f"games won of {N_MATCH}")
ax.set_title("The two objectives order the same configurations after all", loc="left")
cb = fig.colorbar(sc, ax=ax); cb.set_label("tanh surrogate", fontsize=9)
plt.tight_layout(); plt.show()

SWEEP = pd.DataFrame([{"label": "MODE=greedy", "wins": 8, "n": 20, "median_margin": -1761.0, "median_bank": 75098.0, "median_theirs": 77603.5}, {"label": "MODE=mpc", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "PROJECT=0", "wins": 0, "n": 20, "median_margin": -80435.5, "median_bank": 53726.0, "median_theirs": 134610.5}, {"label": "PROJECT=1", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND=0", "wins": 1, "n": 20, "median_margin": -4786.5, "median_bank": 78071.5, "median_theirs": 84949.5}, {"label": "FUND=1", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_H=1", "wins": 1, "n": 20, "median_margin": -4791.5, "median_bank": 78111.5, "median_theirs": 84947.5}, {"label": "FUND_H=4", "wins": 2, "n": 20, "median_margin": -3571.5, "median_bank": 78345.0, "median_theirs": 84572.5}, {"label": "FUND_H=24", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_H=72", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_H=240", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75349.5, "median_theirs": 78389.0}, {"label": "HORIZON=12", "wins": 3, "n": 20, "median_margin": -2089.5, "median_bank": 75322.5, "median_theirs": 78602.5}, {"label": "HORIZON=24", "wins": 3, "n": 20, "median_margin": -1944.0, "median_bank": 75346.0, "median_theirs": 78494.5}, {"label": "HORIZON=48", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "HORIZON=96", "wins": 3, "n": 20, "median_margin": -1575.0, "median_bank": 75339.5, "median_theirs": 78316.5}, {"label": "HORIZON=240", "wins": 3, "n": 20, "median_margin": -1575.0, "median_bank": 75323.0, "median_theirs": 78316.0}, {"label": "PRESSURE_W=0.03", "wins": 4, "n": 20, "median_margin": -1613.0, "median_bank": 75317.5, "median_theirs": 78390.0}, {"label": "PRESSURE_W=0.1", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "PRESSURE_W=0.3", "wins": 3, "n": 20, "median_margin": -1419.5, "median_bank": 75374.5, "median_theirs": 78170.5}, {"label": "RESERVE_H=12", "wins": 0, "n": 20, "median_margin": -35448.0, "median_bank": 61594.5, "median_theirs": 98385.0}, {"label": "RESERVE_H=24", "wins": 6, "n": 20, "median_margin": -2383.0, "median_bank": 76378.0, "median_theirs": 79667.5}, {"label": "RESERVE_H=48", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "RESERVE_H=96", "wins": 1, "n": 20, "median_margin": -14233.5, "median_bank": 79576.5, "median_theirs": 94646.0}, {"label": "SHED_MARGIN=4", "wins": 3, "n": 20, "median_margin": -1879.5, "median_bank": 75348.5, "median_theirs": 78398.0}, {"label": "SHED_MARGIN=12", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "SHED_MARGIN=30", "wins": 8, "n": 20, "median_margin": -986.0, "median_bank": 75437.5, "median_theirs": 78093.5}, {"label": "ROUTE_TURNS_ONLY=0", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "ROUTE_TURNS_ONLY=1", "wins": 5, "n": 20, "median_margin": -1709.0, "median_bank": 75610.0, "median_theirs": 78120.0}, {"label": "SELLS_FIRST=0", "wins": 0, "n": 20, "median_margin": -95852.0, "median_bank": 40150.5, "median_theirs": 138161.5}, {"label": "SELLS_FIRST=1", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FLUSH_AT=648", "wins": 3, "n": 20, "median_margin": -2490.5, "median_bank": 74287.5, "median_theirs": 78500.0}, {"label": "FLUSH_AT=696", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FLUSH_AT=999", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75305.0, "median_theirs": 78389.0}, {"label": "CASH_MIN=0", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "CASH_MIN=400", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "CASH_MIN=2000", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_MARGIN=1.0", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_MARGIN=1.3", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}, {"label": "FUND_MARGIN=2.0", "wins": 3, "n": 20, "median_margin": -1699.0, "median_bank": 75348.5, "median_theirs": 78389.0}])
res = SWEEP[SWEEP.label.str.startswith("RESERVE_H")].copy()
res["turns"] = res.label.str.split("=").str[1].astype(int)
display(res[["label", "wins", "n", "median_margin"]])

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0),
                         gridspec_kw={"width_ratios": [1.15, 1]})

ax = axes[0]
d = res.sort_values("turns")
ax.plot(d.turns, d.wins, "-o", color=TEAL, lw=2.2, ms=8, zorder=3)
for _, r in d.iterrows():
    ax.annotate(f"{int(r.wins)}/{int(r.n)}", (r.turns, r.wins),
                textcoords="offset points", xytext=(0, 10), ha="center",
                fontsize=8.5, color=INK)
ax.axhspan(-0.4, 1.5, color=RED, alpha=0.07)
ax.text(60, 0.6, "the plan starves / nothing is ever free to sell",
        fontsize=8.5, color=RED, ha="center")
ax.set_xlabel("reserve horizon (turns of the plan's own demand held back)")
ax.set_ylabel("games won of 20")
ax.set_ylim(-0.5, 15)
ax.set_title("Two cliffs, not a slope", loc="left")

ax = axes[1]
# The parent's own row is in this table at 20/20 and is not a configuration of
# the seller. Excluding it is the difference between "the best a single axis
# reaches" and "the number we are trying to beat".
best_axis = SWEEP[~SWEEP.label.str.startswith("parent")].wins.max()

# The left bar is computed from the sweep table. The right one is a single
# measured evaluation, the search's eighth: a Latin-hypercube point at
# RESERVE_H=26, SHED_MARGIN=22, HORIZON=77, 12/20 at a mean margin of +572,
# written up in docs/MARKET_EXECUTION.md section 4. It is stated rather than
# computed, because results/data/seller_search.json keeps only the Nelder-Mead
# stage of the history and the hypercube stage that produced it is not in there.
LHS_BEST = 12
bars = [("best any single\naxis reaches", int(best_axis), GREY),
        ("one hypercube point\nmoving three at once", LHS_BEST, TEAL)]
ax.bar([0, 1], [b[1] for b in bars], color=[b[2] for b in bars], width=0.55)
ax.set_xticks([0, 1]); ax.set_xticklabels([b[0] for b in bars], fontsize=9)
for i, b in enumerate(bars):
    ax.text(i, b[1] + 0.25, f"{b[1]}/20", ha="center", fontweight="bold")
ax.set_ylim(0, 15); ax.set_ylabel("games won of 20")
ax.set_title("A ridge a coordinate sweep cannot see", loc="left")
plt.tight_layout(); plt.show()

curse = pd.DataFrame([
    ("parent, screen",  20, 5991),
    ("best, screen",    14, 786),
    ("parent, CONFIRM", 19, 3840),
    ("best, CONFIRM",   10, -308),
], columns=["", "wins of 20", "mean margin"])
display(curse)
drop = 100 * (14 - 10) / 20
print(f"screen-to-confirm drop: {drop:.0f} points, over 259 evaluations")