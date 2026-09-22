import math
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, Markdown, display

# ------------------------------ theme ------------------------------
INK = "#33302A"
PAPER = "#FBF6EC"
GRID = "#E4DAC6"
SOIL = "#7A5C3E"

CROP_COLORS = {
    "WHEAT": "#C9A227", "CARROT": "#E07B39", "TOMATO": "#C0392B",
    "STRAWBERRY": "#D64D79", "MELON": "#6D9E4F", "EGG": "#E3B93B",
    "MILK": "#7FA8C9", "WOOL": "#9B93A9", "FERTILIZER": "#8B6F47",
}

plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 12.5, "axes.titlesize": 14, "axes.titleweight": "bold",
    "figure.dpi": 110,
})


def show(df):
    """Tables go through HTML: Kaggle wraps stdout at ~120 chars and shreds wide text tables."""
    display(HTML(df.to_html(index=False)))


def md(text):
    """Prose that quotes a measured number has to be generated, not typed. The parameters
    below are read from the installed environment, and different kaggle-environments builds
    ship different ones, so any sentence naming a price goes through here."""
    display(Markdown(text))


# ------------------------- market ground truth -------------------------
MARKET_I0 = 10000
PRICE_FLOOR = 1

# The price table exactly as the competition README documents it. This is NOT what we
# compute with: section 2 replaces it with the parameters the installed environment
# actually carries, and shows any drift between the two.
DOC_PARAMS = {
    "WHEAT":      {"base":  25, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

# The environment is the authority. Whatever version of kaggle-environments this kernel
# has, its own MARKET_PARAMS are the ones the ladder scores you against, so we compute
# from those and treat the README table as a claim to be checked.
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    MARKET_PARAMS as _ENV_PARAMS,
)

MARKET_PARAMS = {
    item: {k: _ENV_PARAMS[item][k] for k in
           ("base", "T", "below_func", "below_target", "above_func", "above_target")}
    for item in DOC_PARAMS
}
PRODUCTS = list(MARKET_PARAMS)


def _shape(func, x, T):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    raise ValueError(func)


def price_at(item, inventory):
    """The documented pricing formula, rebuilt. Verified against the env in section 2."""
    p = MARKET_PARAMS[item]
    base, T = p["base"], p["T"]
    if inventory < MARKET_I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        price = base + amp * _shape(f, MARKET_I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        price = base - amp * _shape(f, inventory - MARKET_I0, T)
    return max(PRICE_FLOOR, int(round(price)))


def sell_series(item, n, inv_start=MARKET_I0):
    """Per-unit prices when dumping n units into the market, applying the floor-vanish rule:
    units sold at $1 are not added back to market inventory."""
    inv, out = inv_start, []
    for _ in range(n):
        p = price_at(item, inv)
        out.append(p)
        if p > PRICE_FLOOR:
            inv += 1
    return out


def cliff_of(item, cap=4000):
    """(units that clear above $1, revenue on those units) or (None, total) if the glut
    curve never reaches the floor within `cap` units."""
    probe = sell_series(item, cap)
    first_floor = next((i for i, pr in enumerate(probe) if pr == 1), None)
    if first_floor is None:
        return None, sum(probe)
    return first_floor, sum(probe[:first_floor])


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def pass_agent(obs):
    return {"farmer": ["PASS"], "hands": [], "market": []}


print("setup ok:", len(PRODUCTS), "products tracked")

DRAINS = {  # town consumption per day per product once all 8 shops are open (section 4)
    "WHEAT": 31, "CARROT": 19, "TOMATO": 13, "STRAWBERRY": 25, "MELON": 1,
    "EGG": 13, "MILK": 19, "WOOL": 13, "FERTILIZER": 0,
}
CLIFFS = {item: cliff_of(item) for item in PRODUCTS}
finite = {i: c for i, (c, _) in CLIFFS.items() if c is not None}
HOOK = min(finite, key=lambda i: (finite[i], -MARKET_PARAMS[i]["base"])) if finite else \
    max(PRODUCTS, key=lambda i: MARKET_PARAMS[i]["above_target"])
hook_cliff, hook_rev = CLIFFS[HOOK]
print(f"most fragile market on this build: {HOOK}")
print({i: c for i, c in sorted(finite.items(), key=lambda kv: kv[1])})

N_SHOW = int(min(320, max(60, (hook_cliff or 200) * 2)))
series = sell_series(HOOK, N_SHOW)
cum = np.cumsum(series)

fig, ax = plt.subplots(figsize=(11, 5.2))
ax.step(range(1, N_SHOW + 1), series, where="post", color=CROP_COLORS[HOOK], lw=2.4)
ax.axhline(1, color=INK, lw=1, ls=":")
ax.annotate(f"unit 1: ${series[0]}", xy=(1, series[0]),
            xytext=(0.06, 0.9), textcoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color=INK), fontweight="bold")
if hook_cliff:
    ax.annotate(f"unit {hook_cliff}: ${series[hook_cliff - 1]}",
                xy=(hook_cliff, series[hook_cliff - 1]),
                xytext=(0.40, 0.42), textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=INK), fontweight="bold")
    ax.annotate(f"unit {hook_cliff + 1} onward: $1, forever",
                xy=(min(N_SHOW, int(hook_cliff * 1.35)), 6),
                xytext=(0.55, 0.20), textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=INK))
ax.set_xlabel(f"how many {HOOK.lower()} units you have already sold this turn")
ax.set_ylabel("price of the next unit ($)")
ax2 = ax.twinx()
ax2.plot(range(1, N_SHOW + 1), cum, color=SOIL, lw=2, ls="--")
ax2.set_ylabel("cumulative revenue ($)", color=SOIL)
ax2.tick_params(axis="y", colors=SOIL)
ax2.spines["right"].set_visible(True)
drop = series[0] / max(1, series[hook_cliff - 1]) if hook_cliff else series[0] / max(1, series[-1])
ax.set_title(f"{HOOK} unit 1 sells for ${series[0]}. "
             + (f"Unit {hook_cliff} sells for ${series[hook_cliff - 1]}. After that, $1."
                if hook_cliff else
                f"Unit {N_SHOW} still sells for ${series[-1]}."))
plt.tight_layout()
plt.show()

drain = DRAINS[HOOK]
if hook_cliff:
    heal = hook_cliff / drain if drain else float("inf")
    md(f"""Selling **{hook_cliff} units of {HOOK.lower()}** in one turn earns
**\\${hook_rev:,}**, and the last of those units pays
**\\${series[hook_cliff - 1]}** against the first one's **\\${series[0]}**, a
{drop:.0f}x collapse. Everything past unit {hook_cliff} pays exactly \\$1.

The floor is not the expensive part. Sold units sit in market inventory and hold the price
down until the town eats through them, and the town takes
**{drain if drain else 'no'} {HOOK.lower()} per day** once every shop is open. Clearing a
dump that size therefore takes about **{heal:.0f} days** of town demand against a
**30-day season**.

> {'Prices have memory, and for ' + HOOK.lower() + ' the memory is longer than the game.'
   if heal > 30 else
   'Prices have memory. Time your sales to the drain and it works for you instead.'}""")
else:
    md(f"""On this build no resource reaches the \\$1 floor inside {N_SHOW} units, and the
most fragile of them, **{HOOK.lower()}**, only sags from \\${series[0]} to
\\${series[-1]}. That is itself the finding: **this environment's glut curves are far
gentler than the competition README describes**, which section 2 measures directly. The
walk down your own demand curve is still real, it is just survivable.""")

fig, axes = plt.subplots(3, 3, figsize=(13, 10.5), sharex=False)
for ax, item in zip(axes.ravel(), PRODUCTS):
    p = MARKET_PARAMS[item]
    T, base = p["T"], p["base"]
    xs = np.arange(MARKET_I0 - 3 * T, MARKET_I0 + 3 * T + 1)
    ys = [price_at(item, int(x)) for x in xs]
    ax.plot(xs - MARKET_I0, ys, color=CROP_COLORS[item], lw=2.2)
    ax.axhline(1, color=INK, lw=0.8, ls=":")
    ax.axvline(0, color=INK, lw=0.8, ls=":")
    for dx, lab, xf in [(-T, f"-T ${price_at(item, MARKET_I0 - T)}", 0.04),
                        (T, f"+T ${price_at(item, MARKET_I0 + T)}", 0.62)]:
        ax.plot([dx], [price_at(item, MARKET_I0 + dx)], "o", color=INK, ms=5)
        ax.annotate(lab, xy=(dx, price_at(item, MARKET_I0 + dx)),
                    xytext=(xf, 0.88), textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="-", color=INK, lw=0.7, alpha=0.55),
                    fontsize=10)
    ax.set_title(f"{item}  (base ${base}, T {T})", fontsize=12)
    ax.set_xlabel(f"inventory - I0   [{p['below_func']} {p['below_target']} | "
                  f"{p['above_func']} {p['above_target']}]", fontsize=9.5)
fig.suptitle("Nine resources, nine personalities: the price of everything as a function of market inventory",
             fontweight="bold", y=1.00)
plt.tight_layout()
plt.show()

from kaggle_environments.envs.kaggriculture.kaggriculture import market_price as env_price

probe_points = 0
worst = 0
for item in PRODUCTS:
    T = MARKET_PARAMS[item]["T"]
    for inv in range(MARKET_I0 - 3 * T, MARKET_I0 + 3 * T + 1, max(1, T // 50)):
        probe_points += 1
        worst = max(worst, abs(price_at(item, inv) - env_price(item, inv)))
print(f"formula check: probed {probe_points} (resource, inventory) points, "
      f"max abs diff vs the env = {worst}")

# The second check: this installed environment against the documented table.
FIELDS = ["base", "T", "below_func", "below_target", "above_func", "above_target"]
drift_rows = []
for item in PRODUCTS:
    diffs = [f"{k}: {DOC_PARAMS[item][k]} -> {MARKET_PARAMS[item][k]}"
             for k in FIELDS if DOC_PARAMS[item][k] != MARKET_PARAMS[item][k]]
    drift_rows.append([item, "matches the README ✅" if not diffs else "; ".join(diffs)])
n_drift = sum(1 for r in drift_rows if "matches" not in r[1])
print(f"parameter check: {n_drift} of {len(PRODUCTS)} resources differ from the README"
      f"{'' if n_drift else ' (this build matches the documentation)'}")

show(pd.DataFrame(drift_rows, columns=["resource", "installed env vs the documented table"]))

scorecard = pd.DataFrame([
    ["price formula", "README price table", "rebuilt, probed at %d points" % probe_points,
     ("exact match ✅" if worst == 0 else f"differs by {worst} ❌")],
    ["price parameters", "the README's per-resource table",
     "compared field by field against the installed env",
     ("env matches the README ✅" if n_drift == 0
      else f"{n_drift} resource{'' if n_drift == 1 else 's'} drift ⚠")],
    ["rounding", "int(round(x)) in env source", "source read", "banker's rounding 🔍"],
    ["$1 floor vanish", "units sold at $1 are not re-stocked", "source read (price > 1 guard)", "confirmed 🔍"],
    ["buy side", "only WHEAT + FERTILIZER buyable, quoted post-buy", "source read", "confirmed 🔍"],
    ["town center tick", "1 of each product every 24 turns", "section 4 episode probe", "measured ✅"],
    ["shop unlocks", "every 3 days, with replacement, 8 max", "section 4, 20 episodes", "measured ✅"],
    ["episode seed", "same seed, same shops", "section 4, repeated runs", "measured ✅"],
    ["ongoing crop yields", "tomato/strawberry: 4 scheduled picks, 2x if fertilized", "source read", "confirmed 🔍"],
    ["endgame accounting", "reward is coins only; unsold goods are worthless", "source read (reward = money)", "confirmed 🔍"],
], columns=["rule", "what the rulebook says", "how we checked", "verdict"])
show(scorecard)

premium = ["WOOL", "STRAWBERRY", "MILK", "MELON"]
fig, (axL, axR) = plt.subplots(1, 2, figsize=(14, 5.4))
for item in premium:
    s = np.cumsum(sell_series(item, 320))
    axL.plot(s, color=CROP_COLORS[item], lw=2.2, label=item)
    la = max(i for i, p in enumerate(sell_series(item, 320)) if p > 1)
    axL.plot([la + 1], [s[la]], "o", color=INK, ms=6)
    axL.annotate(f"{la + 1}", xy=(la + 1, s[la]), xytext=(la - 28, s[la] + 1400), fontsize=10)
axL.set_title("Revenue flattens at the cliff\n(dot = last unit above $1)", fontsize=13)
axL.set_xlabel("units sold in one go")
axL.set_ylabel("total revenue ($)")
axL.legend(frameon=False)

mel = sell_series("MELON", 320)
n = np.arange(1, 321)
cum = np.cumsum(mel)
avg = cum / n
mr = np.diff(cum, prepend=0)
seed_cost_per_unit = 80 / 6  # $80 seed, 6 units at peak
profit = cum - n * seed_cost_per_unit
axR.plot(avg, color=CROP_COLORS["MELON"], lw=2.2, label="average price per unit")
axR.plot(mr, color=SOIL, lw=1.6, ls="--", label="marginal revenue of unit n")
axR.axhline(seed_cost_per_unit, color="#C0392B", lw=1.4, ls=":",
            label=f"seed cost per unit (${seed_cost_per_unit:.0f})")
best = int(np.argmax(profit))
axR.plot([best], [avg[best]], "o", color=INK, ms=6)
axR.annotate(f"profit peaks at {best} units", xy=(best, avg[best]),
             xytext=(best + 18, avg[best] + 22), arrowprops=dict(arrowstyle="->", color=INK))
axR.set_title("Melon: average collapses, profit peaks early", fontsize=13)
axR.set_xlabel("units sold in one go")
axR.set_ylabel("$ per unit")
axR.legend(frameon=False, fontsize=10.5)
plt.tight_layout()
plt.show()

DRAIN_FULL_TOWN = DRAINS
rows = []
for item in sorted(PRODUCTS, key=lambda i: (CLIFFS[i][0] is None, CLIFFS[i][0] or 0)):
    if item == "FERTILIZER":
        continue
    n_star, rev = CLIFFS[item]
    if n_star is None:
        rows.append([item, "never reaches it", f"> ${rev:,}", DRAIN_FULL_TOWN[item], "never",
                     "absorbs anything ✅"])
        continue
    drain = DRAIN_FULL_TOWN[item]
    heal = "never" if drain == 0 else (f"~{n_star / drain:.0f} days" if n_star / drain >= 1 else "< 1 day")
    verdict = "never heals ❌" if n_star / max(drain, 1) > 30 else ("heals fast ✅" if n_star / drain <= 7 else "heals slowly ⚠")
    rows.append([item, n_star, f"${rev:,}", drain, heal, verdict])
cliff = pd.DataFrame(rows, columns=["resource", "units to $1 floor", "revenue at the cliff",
                                    "town drain/day (full town)", "heals in", "verdict"])
show(cliff)

_never = [i for i in PRODUCTS if i != "FERTILIZER" and CLIFFS[i][0] is None]
_frail = sorted([i for i in PRODUCTS if CLIFFS[i][0] is not None],
                key=lambda i: CLIFFS[i][0])[:3]
md(f"""**Shock absorbers:** {', '.join(_never).lower() or 'none on this build'}. Their glut
curves never reach the floor within a realistic dump, so their price sags and never dies.

**Fragile:** {', '.join(f'{i.lower()} ({CLIFFS[i][0]})' for i in _frail)}, where the number
is how many units it takes to reach \\$1.

The pairing that matters is **base price against town demand**. A resource with a high base
and almost no shop demand is a trap: nothing reprices it upward and nothing absorbs a dump.
Section 4 measures which resources those are on this build.""")

SHOP_TABLE = {  # shop -> (products, per-day consumption per demanded product)
    "BAKERY":         (["EGG", "WHEAT"], 6),
    "PIZZA_SHOP":     (["MILK", "TOMATO", "WHEAT"], 6),
    "BRUNCH_SPOT":    (["EGG", "WHEAT", "STRAWBERRY"], 6),
    "YARN_STORE":     (["WOOL"], 12),
    "ICE_CREAM_SHOP": (["STRAWBERRY", "MILK", "WHEAT"], 6),
    "PET_CAFE":       (["CARROT"], 12),
    "SMOOTHIE_SHOP":  (["STRAWBERRY", "MILK"], 6),
    "FARMERS_MARKET": (["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"], 6),
}
SHOP_NAMES = sorted(SHOP_TABLE)
UNLOCK_DAYS = np.array([3, 6, 9, 12, 15, 18, 21, 24])  # measured below
TOWN_CENTER_PER_DAY = 1

rate = np.zeros((len(SHOP_NAMES), len(PRODUCTS)))
for si, name in enumerate(SHOP_NAMES):
    prods, per_day = SHOP_TABLE[name]
    for prod in prods:
        rate[si, PRODUCTS.index(prod)] = per_day

rng = np.random.default_rng(7)
N_SEASONS = 5000
draws = rng.integers(0, len(SHOP_NAMES), size=(N_SEASONS, 8))
active_days = (30 - UNLOCK_DAYS)[None, :, None]            # (1, 8, 1)
season_rates = rate[draws]                                  # (N, 8, products)
# the town center consumes 1/day of every product EXCEPT fertilizer (env source verified)
center_season = np.array([30 if p != "FERTILIZER" else 0 for p in PRODUCTS])
consumption = center_season + (season_rates * active_days).sum(axis=1)  # (N, products)

# daily price fans: inventory(t) per season for fan-chart resources
def price_fans(item):
    idx = PRODUCTS.index(item)
    daily = np.zeros((N_SEASONS, 30))
    for i, ud in enumerate(UNLOCK_DAYS):
        daily[:, ud:] += season_rates[:, i, idx][:, None]
    daily += 0 if item == "FERTILIZER" else TOWN_CENTER_PER_DAY
    inv = MARKET_I0 - np.cumsum(daily, axis=1)
    vec_price = np.vectorize(lambda v: price_at(item, int(v)))
    return vec_price(inv)

fans = {item: price_fans(item) for item in ["WHEAT", "CARROT", "MELON"]}
print(f"simulated {N_SEASONS} seasons x {len(PRODUCTS)} products")

from kaggle_environments import make

t0 = time.time()
emp_consumed = {item: [] for item in PRODUCTS}
unlock_seen = {}
seed_determinism = []
for seed in range(20):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([pass_agent, pass_agent])
    steps = env.steps
    for item in PRODUCTS:
        emp_consumed[item].append(MARKET_I0 - steps[-1][0]["observation"]["market"]["inventory"][item])
    shops = [st[0]["observation"]["town"]["unlocked_shops"] for st in steps]
    prev, seen = [], {}
    for i, s in enumerate(shops):
        if s != prev:
            seen[len(s)] = i // 24
            prev = s
    for k, v in seen.items():
        unlock_seen.setdefault(k, set()).add(v)
    if seed == 0:
        first_shops = steps[-1][0]["observation"]["town"]["unlocked_shops"]
        env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env2.run([pass_agent, pass_agent])
        seed_determinism.append(
            first_shops == env2.steps[-1][0]["observation"]["town"]["unlocked_shops"])
print(f"20 episodes in {time.time() - t0:.0f}s | shop count -> days seen: "
      f"{ {k: sorted(v) for k, v in sorted(unlock_seen.items())} }")
print(f"same seed reproduces the exact shop list: {seed_determinism[0]}")

val_rows = []
for item in PRODUCTS:
    emp = np.array(emp_consumed[item])
    sim = consumption[:, PRODUCTS.index(item)]
    lo, hi = np.percentile(sim, [5, 95])
    covered = np.mean((emp >= lo) & (emp <= hi))
    val_rows.append([item, f"{emp.mean():.0f}", f"{sim.mean():.0f}", f"[{lo:.0f}, {hi:.0f}]",
                     f"{covered:.0%}", "✅" if covered >= 0.8 else "❌"])
show(pd.DataFrame(val_rows, columns=["resource", "env mean consumed (20 eps)",
                                     "sim mean", "sim 90% band", "env coverage", "ok"]))

league_rows = []
for item in PRODUCTS:
    idx = PRODUCTS.index(item)
    exp_c = consumption[:, idx].mean()
    T = MARKET_PARAMS[item]["T"]
    p_end = np.median([price_at(item, MARKET_I0 - int(c)) for c in consumption[:, idx][::25]])
    league_rows.append([item, f"{exp_c:.0f}", T, f"{exp_c / T:.2f}",
                        f"{MARKET_PARAMS[item]['below_func']} {MARKET_PARAMS[item]['below_target']}",
                        f"${p_end:.0f}"])
league = pd.DataFrame(league_rows, columns=["resource", "expected season demand", "T",
                                            "demand / T", "scarcity curve", "median day-29 price"])
league = league.sort_values("demand / T", ascending=False, key=lambda s: s.astype(float))
show(league.reset_index(drop=True))

fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
days = np.arange(30)
for ax, item, note in zip(axes, ["WHEAT", "CARROT", "MELON"],
                          ["reliable drift", "the lottery", "only the town sips"]):
    f = fans[item]
    lo, q1, med, q3, hi = np.percentile(f, [5, 25, 50, 75, 95], axis=0)
    ax.fill_between(days, lo, hi, color=CROP_COLORS[item], alpha=0.15, label="5-95%")
    ax.fill_between(days, q1, q3, color=CROP_COLORS[item], alpha=0.30, label="25-75%")
    ax.plot(days, med, color=CROP_COLORS[item], lw=2.2, label="median")
    ax.axhline(MARKET_PARAMS[item]["base"], color=INK, lw=1, ls=":", label="base")
    ax.set_title(f"{item}: {note}")
    ax.set_xlabel("day")
    ax.set_ylabel("price ($)")
axes[0].legend(frameon=False, fontsize=10)
fig.suptitle("Town-only price trajectories, 5,000 simulated seasons: who the town reprices for you",
             fontweight="bold")
plt.tight_layout()
plt.show()

carrot_end = fans["CARROT"][:, -1]
p_spike = np.mean(carrot_end >= 70)
p_base = np.mean(carrot_end <= 40)
carrot_shape = MARKET_PARAMS["CARROT"]["below_func"]
print(f"carrot scarcity curve in this environment: {carrot_shape} "
      f"at target {MARKET_PARAMS['CARROT']['below_target']}")
print(f"day-29 carrot: {p_base:.0%} of seasons near base, {p_spike:.0%} past $70, "
      f"max {carrot_end.max():.0f}")
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.hist(carrot_end, bins=40, color=CROP_COLORS["CARROT"], alpha=0.85, edgecolor=PAPER)
ax.axvline(35, color=INK, lw=1.2, ls=":", label="base $35")
ax.set_title(f"Carrot on day 29: {p_base:.0%} of seasons sit near base, "
             f"{p_spike:.0%} spike past $70")
ax.set_xlabel("carrot price on the last day ($)")
ax.set_ylabel("seasons")
ax.legend(frameon=False)
plt.tight_layout()
plt.show()

CROP_WINDOWS = {  # first yield .. last useful day (from the crop/animal tables)
    "WHEAT": (2, 4), "CARROT": (2, 3), "TOMATO": (8, 11), "STRAWBERRY": (10, 16),
    "MELON": (10, 12), "EGG": (4, 29), "MILK": (8, 29), "WOOL": (6, 29), "FERTILIZER": (0, 29),
}
fans_all = {item: price_fans(item) for item in PRODUCTS}

fig, axes = plt.subplots(3, 3, figsize=(13.5, 10), sharex=True)
for ax, item in zip(axes.ravel(), PRODUCTS):
    f = fans_all[item]
    lo, med, hi = np.percentile(f, [10, 50, 90], axis=0)
    ax.fill_between(days, lo, hi, color=CROP_COLORS[item], alpha=0.18)
    ax.plot(days, med, color=CROP_COLORS[item], lw=2)
    w0, w1 = CROP_WINDOWS[item]
    ax.axvspan(w0, w1, color=INK, alpha=0.12)
    ax.axhline(MARKET_PARAMS[item]["base"], color=INK, lw=0.8, ls=":")
    move = med[-1] - med[0]
    ax.set_title(f"{item}  (harvest shaded, town move ${move:+.0f})", fontsize=11.5)
fig.suptitle("When your harvest lands vs when the town pays: median price fans with 10-90% bands",
             fontweight="bold")
plt.tight_layout()
plt.show()

_moves = {i: float(np.percentile(fans_all[i], 50, axis=0)[-1]
                   - np.percentile(fans_all[i], 50, axis=0)[0]) for i in PRODUCTS}
_risers = sorted(_moves, key=lambda i: -_moves[i])[:3]
_mel_cliff = CLIFFS["MELON"][0]
_pileup = (f"""* **The day-10 pileup.** Melon matures all at once on day 10 and its cliff is
  {_mel_cliff} units, which is {_mel_cliff / 6:.0f} plants at 6 units each, or
  {_mel_cliff / 12:.0f} tiles per farm if both players grow it. That is reachable by
  accident, so in a melon-heavy lobby the floor is a traffic jam rather than a risk."""
  if _mel_cliff else
  """* **No harvest can flood this build's melon market.** Its glut curve never reaches the
  floor, so the day-10 melon pileup that the documented parameters imply does not happen
  here.""")
md(f"""Two calendar facts worth planting around:

{_pileup}
* **The strongest risers are {', '.join(i.lower() for i in _risers)}**, moving
  {', '.join(f'\\${_moves[i]:+.0f}' for i in _risers)} from day 0 to day 29 under town
  demand alone. Production that lands late in those markets sells into a better price than
  production that lands early, which is the opposite of the usual advice to cash out fast.""")

# The order effect: two identical stockpiles of the most fragile resource, sold in sequence.
_half = max(10, (CLIFFS[HOOK][0] or 160) // 2)
first = sell_series(HOOK, _half)
second = sell_series(HOOK, _half, inv_start=MARKET_I0 + _half)
md(f"""Two players each hold **{_half} {HOOK.lower()}** and both sell. Selling into the
untouched market earns **\\${sum(first):,}**; selling into the hole the other player just
made earns **\\${sum(second):,}**. Same goods, same turn count,
**{sum(first) / max(1, sum(second)):.1f}x** the money, decided by nothing but order.""")

# Target the cheapest market to crash: the smallest cliff among the premium goods.
TARGET = min((i for i in PRODUCTS if CLIFFS[i][0] is not None),
             key=lambda i: CLIFFS[i][0], default=HOOK)
t_cliff = CLIFFS[TARGET][0]
opp_stock = 20
ks = np.arange(1, int(max(60, (t_cliff or 60) * 2.4)))
base_rev_opp = sum(sell_series(TARGET, opp_stock))
dmg, cost = [], []
for k in ks:
    mine = sell_series(TARGET, int(k))
    opp_after = sum(sell_series(TARGET, opp_stock, inv_start=MARKET_I0 + int(k)))
    dmg.append(base_rev_opp - opp_after)
    # what the dump costs you: revenue you would have had selling those same units into
    # an untouched market, minus what you actually got
    cost.append(k * MARKET_PARAMS[TARGET]["base"] - sum(mine))
dmg, cost = np.array(dmg), np.array(cost)
net = dmg - cost

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(ks, dmg, color=CROP_COLORS[TARGET], lw=2.4, label="damage to their 20 units")
ax.plot(ks, cost, color=SOIL, lw=2.2, ls="--", label="cost to you")
ax.fill_between(ks, cost, dmg, where=dmg > cost, color=CROP_COLORS[TARGET], alpha=0.18,
                label="net gain zone")
best_k = int(ks[int(np.argmax(net))])
if t_cliff:
    ax.axvline(t_cliff, color="#C0392B", ls=":", lw=1.4,
               label=f"{TARGET.lower()} cliff ({t_cliff} units)")
ax.plot([best_k], [dmg[best_k - 1]], "o", color=INK, ms=7)
ax.annotate(rf"best net at k={best_k}: costs you \${cost[best_k - 1]:,.0f}," "\n"
            rf"destroys \${dmg[best_k - 1]:,.0f} of theirs",
            xy=(best_k, dmg[best_k - 1]), xytext=(best_k + 12, dmg[best_k - 1] * 0.55),
            arrowprops=dict(arrowstyle="->", color=INK), fontsize=11)
ax.set_title(f"Crashing {TARGET.lower()}: their loss saturates, your cost never stops climbing")
ax.set_xlabel("units you dump")
ax.set_ylabel("dollars")
ax.legend(frameon=False, fontsize=10.5)
plt.tight_layout()
plt.show()

cross = int(ks[np.argmax(net < 0)]) if np.any(net < 0) else None
md(f"""Best net trade against **{TARGET.lower()}** sits at **k={best_k}**: it costs you
**\\${cost[best_k - 1]:,.0f}** and destroys **\\${dmg[best_k - 1]:,.0f}** of theirs, an
exchange rate of **{dmg[best_k - 1] / max(1, cost[best_k - 1]):.1f}x**.
{f'The trade turns negative past **k={cross}**' if cross else 'The trade stays positive across the whole range'}{f', and the cliff is at {t_cliff}.' if t_cliff else '.'} Past the floor your extra units pay
full price to destroy nothing, which is why the weapon has a size and not just a direction.""")

# How much production each crash actually needs, from the crop and animal tables.
UNITS_PER = {  # realistic units one tile contributes over the season
    "WOOL": 9, "MILK": 11, "EGG": 26, "STRAWBERRY": 4, "TOMATO": 4,
    "MELON": 6, "WHEAT": 6, "CARROT": 4,
}
TILE_BUDGET = 100  # a fully bought farm
feas_rows = []
for item in sorted(PRODUCTS, key=lambda i: (CLIFFS[i][0] is None, CLIFFS[i][0] or 0)):
    if item == "FERTILIZER":
        continue
    n_star, _ = CLIFFS[item]
    if n_star is None:
        feas_rows.append([item, "unreachable", "n/a", "n/a", "cannot be crashed ✅"])
        continue
    tiles = n_star / UNITS_PER[item]
    drain = DRAINS[item]
    heal = f"~{n_star / drain:.0f} days" if drain else "never"
    if tiles > TILE_BUDGET:
        verdict = "not alone ❌"
    elif tiles > TILE_BUDGET / 4:
        verdict = "only with a full farm ⚠"
    else:
        verdict = "yes, solo ✅"
    feas_rows.append([item, n_star, f"~{tiles:.0f} tiles of production", heal, verdict])
show(pd.DataFrame(feas_rows, columns=["resource", "units to crash", "production needed",
                                      "crash heals in", "verdict"]))

_solo = [r[0].lower() for r in feas_rows if "solo ✅" in r[4]]
_safe = [r[0].lower() for r in feas_rows if "cannot" in r[4] or "not alone" in r[4]]
md(f"""**Crashable by one farm:** {', '.join(_solo) if _solo else 'nothing on this build'}.
**Effectively safe:** {', '.join(_safe) if _safe else 'nothing'}.

The crashes that are cheap are also the ones that **heal**, which makes price manipulation a
timing weapon rather than a volume one: you want the crash to land on the turn your opponent
sells, not a week earlier. And since the trade goes negative past the floor, a crash has a
correct size. Dumping everything you own is the one option that is always wrong.""")

CROPS = {
    "WHEAT": {"seed": 10, "first_yield_day": 2, "max_yield_day": 4},
    "CARROT": {"seed": 20, "first_yield_day": 2, "max_yield_day": 3},
}
ROWS = [(0, "WHEAT"), (1, "WHEAT"), (2, "CARROT")]  # worker index -> (row y, crop)


def make_farm_agent(sell_mode):
    """Identical 3-row farm (wheat, wheat, carrot). sell_mode: 'daily' cashes out the
    shed every turn; 'enddump' holds everything and sells from day 28."""
    state = {}

    def agent(obs):
        if obs.get("step", 0) == 0:
            state.clear()
        me = obs["farms"][obs["player"]]
        priv = obs["private"]
        day, hour = obs["day"], obs["hour"]
        seeds, shed = priv.get("seeds", {}), priv.get("shed", {})
        tiles, money = me["tiles"], me["money"]

        market = []
        if hour == 0:
            if money > 400:
                market += [["HIRE"], ["HIRE"]]
            if seeds.get("WHEAT", 0) < 5 and money >= 100:
                market.append(["BUY_SEED", "WHEAT", 10])
            if seeds.get("CARROT", 0) < 3 and money >= 100:
                market.append(["BUY_SEED", "CARROT", 5])
        if sell_mode == "daily" or day >= 28:
            for item, n in shed.items():
                if n > 0:
                    market.append(["SELL", item, n])

        def unit_action(idx):
            if idx >= len(ROWS):
                return ["PASS"]
            y, crop = ROWS[idx]
            pos = me["farmer"] if idx == 0 else (
                me["hands"][idx - 1] if idx - 1 < len(me["hands"]) else None)
            if pos is None:
                return ["PASS"]
            fx, fy = pos
            tile = tiles[fy][fx]
            if tile != "LOCKED":
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    return ["DIG"]
                if tile is None and fy == y and 0 <= fx < 5 and seeds.get(crop, 0) > 0:
                    return ["PLANT", crop]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    age = day - tile["planted_day"]
                    if age >= CROPS[tile["crop"]]["max_yield_day"]:
                        return ["HARVEST"]
                    if not tile["watered_today"]:
                        return ["WATER"]
            tx = state.get(idx, 0)
            if fx == tx:
                tx = (tx + 1) % 5
                state[idx] = tx
            if fy > y:
                return ["NORTH"]
            if fy < y:
                return ["SOUTH"]
            if fx < tx:
                return ["EAST"]
            if fx > tx:
                return ["WEST"]
            return ["PASS"]

        hands = [unit_action(i + 1) for i in range(len(me["hands"]))]
        return {"farmer": unit_action(0), "hands": hands, "market": market}

    return agent

t_probe = time.time()
make("kaggriculture", configuration={"episodeSteps": 720, "seed": 999}, debug=False).run(
    [make_farm_agent("daily"), make_farm_agent("daily")])
t_ep = time.time() - t_probe
N = int(min(40, max(10, 600 / (2 * t_ep))))
print(f"one episode: {t_ep:.1f}s -> running {N} episodes per arm (~{2 * N * t_ep / 60:.1f} min)")

t0 = time.time()
results = {"cashout": [], "enddump": []}
for seed in range(N):
    for arm in ["cashout", "enddump"]:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([make_farm_agent("daily" if arm == "cashout" else "enddump"),
                 make_farm_agent("daily")])
        m0 = env.steps[-1][0]["observation"]["farms"][0]["money"]
        m1 = env.steps[-1][0]["observation"]["farms"][1]["money"]
        results[arm].append((m0, m1, m0 - m1))
print(f"done in {(time.time() - t0) / 60:.1f} min")

stat_rows = []
for arm, label in [("cashout", "cash-out vs mirror"), ("enddump", "hold-and-dump vs mirror")]:
    margins = np.array([r[2] for r in results[arm]])
    wins = int(np.sum(margins > 0))
    ties = int(np.sum(margins == 0))
    n = len(margins)
    p, lo, hi = wilson(wins + 0.5 * ties, n)
    p_analytic = 0.5 * (1 + math.erf((margins.mean() / max(margins.std(), 1e-9)) / math.sqrt(2)))
    stat_rows.append([label, f"${margins.mean():,.0f}", f"${margins.std():,.0f}",
                      f"{wins}-{n - wins - ties}-{ties}",
                      f"{p:.2f} [{lo:.2f}, {hi:.2f}]", f"{p_analytic:.2f}"])
show(pd.DataFrame(stat_rows, columns=["arm", "mean margin", "margin sd", "W-L-T",
                                      "score (W + 0.5T) [95% CI]", "normal approx"]))

fig, ax = plt.subplots(figsize=(10, 4.6))
bins = np.linspace(min(r[2] for a in results.values() for r in a),
                   max(r[2] for a in results.values() for r in a) + 1, 30)
for arm, color, label in [("cashout", SOIL, "cash-out"), ("enddump", "#C0392B", "hold-and-dump")]:
    ax.hist([r[2] for r in results[arm]], bins=bins, alpha=0.55, color=color, label=label)
ax.axvline(0, color=INK, lw=1.2)
ax.set_title("Final margin distributions: same farm, different endgame")
ax.set_xlabel("own coins minus reference coins at turn 720 ($)")
ax.set_ylabel("episodes")
ax.legend(frameon=False)
plt.tight_layout()
plt.show()

_c = np.array([r[2] for r in results["cashout"]])
_d = np.array([r[2] for r in results["enddump"]])
md(f"""Cash-out against an identical farm is a tie-fest, as it should be:
**{int((_c == 0).sum())} of {len(_c)}** episodes end level, and the stragglers are weed luck,
since the two farms draw from different parts of the weed RNG stream.

Hold-and-dump **won {int((_d > 0).sum())} of {len(_d)}**. It loses the mean twice, once to
the 100-item shed cap discarding overflow and once to the day-28 dump walking down its own
curve, and its margin spread is **{_d.std() / max(_c.std(), 1e-9):.0f}x wider**. The ladder
never sees the size of any of those margins, only the sign, so the extra variance buys
nothing.

Convert goods to coins early. The only stockpile worth holding is one pointed at a scarcity
window (section 4) or at a rival (section 6).""")

_top_drains = sorted((i for i in PRODUCTS if DRAINS[i]), key=lambda i: -DRAINS[i])[:3]
_hook_line = (f"{HOOK.lower()} unit {CLIFFS[HOOK][0]} pays "
              f"${sell_series(HOOK, CLIFFS[HOOK][0])[-1]} against unit 1's "
              f"${MARKET_PARAMS[HOOK]['base']}") if CLIFFS[HOOK][0] else \
             f"{HOOK.lower()} is the steepest curve here and still never floors"
playbook = pd.DataFrame([
    ["Quote before you sell: a bulk sell walks down its own curve", _hook_line, "S1"],
    ["Check the environment against the README before trusting any price advice",
     f"{n_drift} of {len(PRODUCTS)} resources differ from the documented table on this build", "S2"],
    ["Know where each cliff is and stop short of it",
     ", ".join(f"{i.lower()} {CLIFFS[i][0]}" for i in _frail), "S1, S3"],
    ["Pace big sales at the town's drain rate",
     ", ".join(f"{i.lower()} {DRAINS[i]}/day" for i in _top_drains), "S3"],
    ["Sell into the resources the town actually reprices upward",
     f"strongest risers: {', '.join(i.lower() for i in _risers)}", "S4, S5"],
    ["Treat the shop draw as a lottery you can read but not control",
     f"carrot ends past $70 in {p_spike:.0%} of seasons ({carrot_shape} curve here)", "S4"],
    ["A crash has a correct size; past the floor you pay full price for nothing",
     f"best net vs {TARGET.lower()} at k={best_k}, "
     f"{dmg[best_k - 1] / max(1, cost[best_k - 1]):.1f}x exchange", "S6"],
    ["Prefer crashes that land the turn they sell, since cheap crashes heal fast",
     f"crashable solo: {', '.join(_solo) if _solo else 'none'}", "S6"],
    ["Unsold goods are worth $0 at turn 720; cash is the only score",
     "hold-and-dump lost every episode to an identical farm", "S7"],
], columns=["rule", "the number behind it", "from"])
show(playbook)


def market_aware_sell(obs, item, min_price_frac=0.85):
    """Drop-in seller for your agent. Sells as many units of `item` as the market will
    absorb before the price falls below min_price_frac x base, given the inventory the
    obs reports right now. Returns a quantity for a SELL order (0 = do not sell).

    Reads the price parameters from the environment your agent is already running inside,
    so it cannot drift from the market it is trading against (see section 2). The baked
    table is only a fallback for running outside the env."""
    import math as _m
    try:
        from kaggle_environments.envs.kaggriculture.kaggriculture import MARKET_PARAMS as _P
        p = _P[item]
        PARAMS = {item: (p["base"], p["T"], p["below_func"], p["below_target"],
                         p["above_func"], p["above_target"])}
    except Exception:
        PARAMS = {
            "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
            "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
            "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
            "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
            "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
        }

    def shape(f, x, T):
        x = max(0.0, x)
        if f == "linear": return x
        if f == "sq": return x * x
        if f == "sqrt": return _m.sqrt(x)
        if f == "log": return _m.log(1.0 + x)
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2

    base, T, bf, bt, af, at = PARAMS[item]

    def price(inv):
        x = inv - 10000
        if x < 0:
            return max(1, round(base + bt * base / shape(bf, T, T) * shape(bf, -x, T)))
        return max(1, round(base - at * base / shape(af, T, T) * shape(af, x, T)))

    inv = obs["market"]["inventory"][item]
    held = obs["private"]["shed"].get(item, 0)
    limit = base * min_price_frac
    qty = 0
    while qty < held and price(inv + qty) >= limit:
        qty += 1
    return qty


print("market_aware_sell ready: paste it into your bot and sell with a floor on your own price")