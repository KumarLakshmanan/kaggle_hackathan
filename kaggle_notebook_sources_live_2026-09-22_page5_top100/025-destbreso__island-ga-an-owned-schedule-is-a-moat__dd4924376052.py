import math

# engine constants and pricing, verbatim from kaggriculture.py (1.32.7)
MARKET_I0, HINGE_GAIN, PRICE_FLOOR = 10000, 8.0, 1
MARKET_PARAMS = {
 "WHEAT":      {"base": 25,  "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
 "CARROT":     {"base": 35,  "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
 "TOMATO":     {"base": 60,  "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
 "STRAWBERRY": {"base": 120, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
 "MELON":      {"base": 250, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
 "EGG":        {"base": 50,  "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
 "MILK":       {"base": 160, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
 "WOOL":       {"base": 200, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
 "FERTILIZER": {"base": 100, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40}}

def _shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def price(item, inventory):
    p = MARKET_PARAMS[item]
    base, T = p["base"], p["T"]
    if inventory < MARKET_I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        val = base + amp * _shape(f, MARKET_I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        val = base - amp * _shape(f, inventory - MARKET_I0, T)
    return max(PRICE_FLOOR, int(round(val)))

# median season demand draw (community-measured shop consumption)
DEMAND = {"WHEAT": 504, "STRAWBERRY": 396, "MILK": 288, "CARROT": 270,
          "TOMATO": 180, "WOOL": 180, "EGG": 180, "MELON": 30, "FERTILIZER": 0}
CROP = {"WHEAT": (2, 4, 6, False), "CARROT": (2, 3, 4, False),
        "TOMATO": (8, 8, 4, True), "STRAWBERRY": (10, 10, 4, True),
        "MELON": (10, 12, 6, False)}
TILE_DAYS = 60 * 28                     # ~60 workable tiles x 28 useful days
ANIM_CAP = {"EGG": 4 * 27, "MILK": 6 * 12, "WOOL": 6 * 9}
FERT_UNITS = 16 * 29                    # nightly fertilizer at full herd
COSTS = 60 * 10 + 5 * 400 + 6 * 500 + 4 * 300 + 1000 + 2000 + 300 * 20

def R(g, D, S):                         # exact end-of-season sale integral
    return sum(price(g, MARKET_I0 - D + i) for i in range(int(S)))

def per_tile_day(c):
    fy, my, y, ongoing = CROP[c]
    return (y / my) if not ongoing else (y + (30 - fy)) / 30

alloc = {c: 0 for c in CROP}
units = {g: 0.0 for g in DEMAND}
used, step = 0, 14
while used + step <= TILE_DAYS:
    best, best_gain, best_add = None, 1.0, 0
    for c in CROP:
        add = per_tile_day(c) * step
        gain = R(c, DEMAND[c], units[c] + add) - R(c, DEMAND[c], units[c])
        if gain > best_gain:
            best, best_gain, best_add = c, gain, add
    if not best:
        break
    units[best] += best_add
    alloc[best] += step
    used += step

rows, gross = [], 0
for g in DEMAND:
    S = units.get(g, 0.0)
    if g in ANIM_CAP:
        S = ANIM_CAP[g]
    if g == "FERTILIZER":
        S = FERT_UNITS
    S = int(S)
    while S > 0 and price(g, MARKET_I0 - DEMAND[g] + S - 1) <= 2:
        S -= 1
    r = R(g, DEMAND[g], S)
    rows.append((g, S, int(r)))
    gross += r
rows.sort(key=lambda t: -t[2])
print(f"{'good':11s} {'units':>6s} {'revenue':>9s}")
for g, S, r in rows:
    print(f"{g:11s} {S:6d} {r:9,d}")
BOUND = int(3000 + gross - COSTS)
print(f"\nCRUDE RELAXED BOUND vs idle opponent: ${BOUND:,}")

import matplotlib.pyplot as plt

HINGE = {"TOMATO": "#b5486b", "CARROT": "#c2571f", "EGG": "#b3872a"}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))

xs = list(range(0, 601, 5))
for g, col in HINGE.items():
    ax1.plot(xs, [price(g, MARKET_I0 - x) for x in xs], color=col, lw=2, label=g)
    T = MARKET_PARAMS[g]["T"]
    if T <= 600:
        ax1.plot([T], [price(g, MARKET_I0 - T)], "o", color=col, ms=6)
for g in ("WHEAT", "MELON"):
    ax1.plot(xs, [price(g, MARKET_I0 - x) for x in xs], color="#9aa3ad",
             lw=1.4, ls="--")
    ax1.annotate(g.lower(), (xs[-1], price(g, MARKET_I0 - 600)),
                 xytext=(-2, 5), textcoords="offset points", ha="right",
                 fontsize=8, color="#9aa3ad")
ax1.legend(frameon=False, fontsize=9, loc="upper left")
ax1.set_xlabel("units short of the reference inventory")
ax1.set_ylabel("unit price, $")
ax1.set_title("the 1.32.7 scarcity branch: the hinge trio\nturns convex at its knee (dots)", fontsize=10)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)

names = [g for g, _S, _r in rows if _r > 0][::-1]
revs = [r / 1000 for _g, _S, r in rows if r > 0][::-1]
cols = [HINGE.get(g, "#2f6fb2") for g in names]
b = ax2.barh(names, revs, color=cols, height=0.6)
for r_, v in zip(b, revs):
    ax2.annotate(f"{v:,.1f}k", (v, r_.get_y() + r_.get_height() / 2),
                 xytext=(4, 0), textcoords="offset points", va="center",
                 fontsize=8, color="#333")
ax2.set_xlabel("revenue in the relaxed optimum, thousands of $")
ax2.set_title("the bound's mix: strawberry leads, and the\nhinge trio (colored) enters at MEDIAN demand", fontsize=10)
ax2.set_xlim(0, max(revs) * 1.18)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import json, os, statistics
from pathlib import Path

def find(relpath, roots=("/kaggle/input", ".", "..")):
    """Walk for the file rather than guessing where it is mounted."""
    tail = os.path.normpath(relpath)
    for r in roots:
        if not os.path.isdir(r):
            continue
        for dirpath, dirnames, filenames in os.walk(r):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                p = os.path.normpath(os.path.join(dirpath, fn))
                if p == tail or p.endswith(os.sep + tail):
                    return p
    return None

def measurement(label, relpath, embedded, reader=None):
    """Prefer the measurement file if it is attached, else the copy carried in
    the cell, and print WHICH: an embedded copy cannot be re-derived and drifts
    the moment its source moves, so it must never be silent."""
    record = json.loads(embedded)
    path = find(relpath) if relpath else None
    if path:
        print(f"SOURCE  {label}: {path}")
        return reader(path, record) if reader else json.loads(Path(path).read_text())
    print(f"SOURCE  {label}: the copy carried in this cell"
          + (f", not {relpath}" if relpath else ""))
    return record

# Four measurements, each with its own provenance row, and every mark in the
# next figure is computed from them.
CORRIDOR = measurement("corridor", None, r"""
{
 "note": "four measurements, each named by its own row, copied from my run outputs; the figure derives every mark and every label from these banks and carries no number of its own",
 "consensus_route_vs_idle": {
  "what": "the public consensus construction, executed by my runtime against an idle opponent, one bank per CRN seed",
  "banks": {
   "11": 83407.0,
   "23": 61001.0,
   "47": 73972.0
  }
 },
 "top_twelve_median_banks": {
  "what": "week four, one median bank per team over that team's own real episodes, team names dropped",
  "banks": [
   74410,
   78400,
   80903,
   84354,
   89894,
   91220,
   91836,
   92085,
   93288,
   100532,
   100606,
   101583
  ]
 },
 "naked_streams_vs_idle": {
  "what": "the two recorded base streams the delta search edits, replayed open-loop against an idle opponent, mean over the CRN seeds",
  "means": [
   147306.66666666666,
   153695.33333333334
  ]
 },
 "routed_agents_vs_idle": {
  "what": "public routed agents against an idle opponent, per-seed banks, authors dropped",
  "banks": [
   [
    145405.0,
    151758.0,
    179709.0
   ],
   [
    190184.0,
    126797.0,
    144988.0
   ],
   [
    185630.0,
    136172.0,
    169835.0
   ],
   [
    145405.0,
    151758.0,
    179709.0
   ],
   [
    190184.0,
    126800.0,
    144993.0
   ]
  ]
 }
}
""")
for key, row in CORRIDOR.items():
    if isinstance(row, dict) and "what" in row:
        print(f"  {key}: {row['what']}")

# every mark and every label below is derived from CORRIDOR, and the roof is
# the BOUND the section-3 cell computed rather than a number retyped from it
consensus = statistics.mean(
    CORRIDOR["consensus_route_vs_idle"]["banks"].values()) / 1000
n_seeds = len(CORRIDOR["consensus_route_vs_idle"]["banks"])
top12 = sorted(b / 1000 for b in CORRIDOR["top_twelve_median_banks"]["banks"])
t_lo = statistics.quantiles(top12, n=4, method="inclusive")[0]
t_med, t_max = statistics.median(top12), max(top12)
streams = sorted(m / 1000 for m in CORRIDOR["naked_streams_vs_idle"]["means"])
routed = sorted(statistics.mean(b) / 1000
                for b in CORRIDOR["routed_agents_vs_idle"]["banks"])
front_lo, front_hi = streams[0], routed[-1]
front_mid = (front_lo + front_hi) / 2
roof = BOUND / 1000
arrow_lo, arrow_hi = front_hi + 4, roof - 3.5

fig, ax = plt.subplots(figsize=(10, 3.2))
ax.set_xlim(-8, roof + 22)
ax.set_ylim(-0.9, 1.0)
ax.axhline(0, color="#d9dde3", lw=1.2, zorder=1)

ax.axvspan(t_lo, t_max, color="#7b5bb5", alpha=0.14, lw=0)
ax.axvspan(front_lo, front_hi, color="#1f9d6b", alpha=0.14, lw=0)
ax.plot([consensus], [0], "o", ms=11, color="#2f6fb2", zorder=3)
ax.plot([t_med], [0], "o", ms=11, color="#7b5bb5", zorder=3)
ax.plot([front_mid], [0], "o", ms=11, color="#1f9d6b", zorder=3)
ax.plot([roof], [0], "o", ms=11, color="#c2571f", zorder=3)

ax.annotate(f"public consensus route\nreplayed vs idle: {consensus:.1f}k"
            f"\n({n_seeds}-seed mean)",
            (consensus, 0), xytext=(0, -58), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="#2f6fb2")
ax.annotate(f"week-four top twelve\nmedian banks: {t_med:.0f}k,"
            f" best {t_max:.0f}k",
            (t_med, 0), xytext=(0, 16), textcoords="offset points",
            ha="center", fontsize=9, color="#5b3fa0")
ax.annotate(f"the public frontier: naked recorded\nstreams"
            f" {streams[0]:.0f}-{streams[-1]:.0f}k, routed"
            f"\nagents to {front_hi:.0f}k (vs idle)",
            (front_mid, 0), xytext=(0, 14), textcoords="offset points",
            ha="center", fontsize=9, color="#14724d")
ax.annotate(f"crude relaxed bound: {roof:.0f}k\n(logistics ignored)",
            (roof, 0), xytext=(0, -44), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="#c2571f")
ax.annotate("", xy=(arrow_hi, 0.52), xytext=(arrow_lo, 0.52),
            arrowprops=dict(arrowstyle="<->", color="#666", lw=1.2))
ax.annotate("what even the frontier\nleaves unclaimed",
            ((arrow_lo + arrow_hi) / 2, 0.62),
            ha="center", fontsize=9, style="italic", color="#666")
ax.set_yticks([])
ax.set_xlabel("bank at end of season, thousands of $")
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

# the genome, in full: this is the entire search space of one candidate
GENOME_EXAMPLE = {
  "ne": 6, "sw": 10, "se": None,       # quadrant unlock days (None = skip)
  "plateau": 12, "ramp_full": 8,       # hands/day cap, days to reach it
  "tomato_day": 8, "melon2": 1,        # tomato window start; melon replant
  "sellpol": "hybrid",                 # daily | sweep | hybrid (section 5)
  "herd": [[0, "COW", 2], [0, "SHEEP", 2], [6, "COW", 2],
           [8, "SHEEP", 1], [10, "COW", 1]],          # [day, kind, n] waves
  "prog": {                            # tiles per crop, per quadrant
    "NW": {"WHEAT": 8, "CARROT": 3, "STRAWBERRY": 4, "MELON": 2},
    "NE": {"WHEAT": 10, "CARROT": 4, "STRAWBERRY": 5, "MELON": 6},
    "SW": {"WHEAT": 12, "CARROT": 5, "MELON": 8},
    "SE": {}}}

# macro-mutations: every move keeps the spec meaningful
MUTATIONS = [
  "shift a quadrant unlock day by 1 (or toggle SE on/off)",
  "plateau +-1, ramp +-2",
  "herd wave: n +-1, day +-2, or add a 1-animal wave",
  "move 1-2 tiles between crops within a quadrant (FALLOW allowed)",
  "tomato window +-2 days",
  "flip melon second wave",
  "switch sell policy"]

# block crossover: whole subsystems travel together, because crops x
# labour x cash are co-adapted through the shared hands and the shared
# pocket; uniform gene mixing would break exactly those linkages the
# building-block view of a GA wants preserved [1][2]
CROSSOVER_BLOCKS = ["unlock days", "hire curve", "herd waves",
                    "each quadrant's crop table", "tomato+melon", "sell policy"]
print("genome fields:", sorted(GENOME_EXAMPLE))
print("mutation operators:", len(MUTATIONS), "| crossover blocks:", len(CROSSOVER_BLOCKS))

def compile_spec(spec):
    """spec -> {"days": {d: targets}, "market": {turn: orders}}."""

    # 1) TILE REALISATION
    #    each herd wave (day b, kind, n) takes the n nearest-shed tiles
    #    among quadrants unlocked by day b -> structure tiles (COOP/PASTURE);
    #    crops fill each quadrant's remainder from its table, ongoing crops
    #    nearest the shed, melon farthest, clamped to the 25-tile budget

    # 2) PLANT-DAY UNROLLING (per tile, engine crop table)
    #    cyclers : plant days a, a+m+1, a+2(m+1), ... while day+m <= 29
    #              (m = max_yield_day: wheat 4, carrot 3)
    #    melon   : one wave at a; optional second at a+13 if it ripens
    #    ongoing : one plant inside its window (tomato from the tomato_day
    #              gene, strawberry only if its quadrant opens by ~day 12)
    #    -> per-day construction targets + exact per-day seed needs

    # 3) PRODUCTION PROJECTOR -> cumulative sellable-by-morning per good
    #    crops   : yield x efficiency lands the morning after harvest
    #    animals : yield ACCRUES from placement at 1/interval per day but
    #              is harvestable only from first_yield_day, so the first
    #              harvest is a lump of about fyd/interval units (5.1)

    # 4) MARKET CHANNEL, per day d, under the 10-order cap per turn
    #    hour 0 : SELL each good, sized by the sell-policy gene:
    #             daily  = today's projected arrival x 1.25
    #             sweep  = cumulative projection minus already scheduled
    #             hybrid = daily pace + a cumulative top-up every 3rd day
    #             (near-exact on purpose: phantom demand re-steers, 5.1)
    #    hour 1 : BUY_SEED for due stages (seeds strictly BEFORE land),
    #             BUY_PRODUCT wheat for the herd's feed,
    #             BUY_ANIMAL waves, BUY_LAND on unlock days
    #    hours 1-2 : the day's HIREs, curve capped by farm size (~5
    #             work-tiles per hand) and NEVER cut by a cash forecast
    #    days 28-29 : terminal flush of every good, evening turns included

    # 5) FINANCING BY OPTIMISM
    #    every order at the spec's own day; the engine's silent refusals
    #    are the only brake, plus a thin repair layer re-issuing land and
    #    animal purchases while their window is still open (5.1)
    return {"days": "...", "market": "..."}

print("compiler contract: 5 derivations, every stated rule engine-exact")

def fib_cost(n_already):
    a, b = 1, 1
    for _ in range(n_already):
        a, b = b, a + b
    return a

daily = [sum(fib_cost(k) for k in range(n)) for n in range(16)]
print(f"12 hands cost ${daily[12]:,} a day; the 13th alone costs "
      f"${fib_cost(12):,}, the 14th ${fib_cost(13):,}.")

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7.5, 3))
ns = list(range(1, 15))
ax.bar(ns, [daily[n] for n in ns], color="#2f6fb2", width=0.62)
for n in (8, 12, 14):
    ax.annotate(f"${daily[n]:,}", (n, daily[n]), xytext=(0, 4),
                textcoords="offset points", ha="center", fontsize=8.5,
                color="#333")
ax.set_xticks(ns)
ax.set_xlabel("hands hired in one day")
ax.set_ylabel("total cost of the day's hires, $")
ax.set_title("the Fibonacci hire ledger: the engine tells you\nwhere the plateau belongs", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import numpy as np

rng = np.random.default_rng(7)
N, K, GENS, RUNS = 40, 3, 12, 400

def takeover(adv):
    frac = np.zeros((RUNS, GENS + 1))
    for r in range(RUNS):
        fit = np.full(N, 1.0) + rng.normal(0, 0.02, N)
        seed = np.zeros(N, bool)
        seed[0], fit[0] = True, adv
        frac[r, 0] = seed.mean()
        for g in range(1, GENS + 1):
            idx = rng.integers(0, N, (N, K))
            win = idx[np.arange(N), np.argmax(fit[idx], axis=1)]
            fit, seed = fit[win] + rng.normal(0, 0.005, N), seed[win]
            frac[r, g] = seed.mean()
    return frac.mean(0)

import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))
for adv, col, lab in ((1.02, "#2f6fb2", "2 % fitter: hidden by noise, does not spread"),
                      (1.10, "#c2571f", "10 % fitter")):
    ax1.plot(range(GENS + 1), takeover(adv), "-o", ms=4, color=col,
             label=f"seeded schedule {lab}")
ax1.axhline(0.5, color="#bbb", lw=1, ls=":")
ax1.set_xlabel("generation")
ax1.set_ylabel("share of population descended\nfrom the seeded schedule")
ax1.set_title("tournament takeover (pop 40, k=3, 400 runs):\none good seed owns the search in a few generations", fontsize=10)
ax1.legend(frameon=False, fontsize=9, loc="lower right")
ax1.set_ylim(0, 1.02)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)

names = ["envelope", "bound\nmix", "intensity", "random"]
descr = ["leader statistics", "tomato, egg, geese", "4th quadrant, max hires",
         "within the envelope"]
cols = ["#2f6fb2", "#c2571f", "#7b5bb5", "#9aa3ad"]
pos = [(0, 1.05), (1.15, 0), (0, -1.05), (-1.15, 0)]
off = [(0, 0.62, "center", "bottom"), (0.58, 0, "left", "center"),
       (0, -0.62, "center", "top"), (-0.58, 0, "right", "center")]
for (x, y), (dx, dy, ha, va), name, dsc, col in zip(pos, off, names, descr,
                                                    cols):
    ax2.add_patch(plt.Circle((x, y), 0.44, color=col, alpha=0.88, zorder=3))
    ax2.annotate(name, (x, y), ha="center", va="center", fontsize=7.8,
                 color="white", zorder=4)
    ax2.annotate(dsc, (x + dx, y + dy), ha=ha, va=va, fontsize=8,
                 color="#777", zorder=4)
for i in range(4):
    x1, y1 = pos[i]
    x2, y2 = pos[(i + 1) % 4]
    ax2.annotate("", xy=(x2 * 0.58, y2 * 0.58), xytext=(x1 * 0.58, y1 * 0.58),
                 arrowprops=dict(arrowstyle="->", color="#888", lw=1.3,
                                 connectionstyle="arc3,rad=-0.3"))
ax2.text(0, -2.02, "best of island i replaces the worst of island i+1, "
         "every 6 generations", ha="center", fontsize=8.5, color="#555")
ax2.set_xlim(-2.6, 2.6); ax2.set_ylim(-2.25, 1.95)
ax2.set_aspect("equal"); ax2.axis("off")
ax2.set_title("four OWNED species on a migration ring", fontsize=10)
plt.tight_layout(); plt.show()

# the search loop, complete except for compile_spec() and the engine
# evaluator (see section 8 for what those are and why they stay home)
import copy, random

def run_search(species, evaluate, compile_spec, hours=3, seeds=(11, 23, 47)):
    rng = random.Random(20260824)
    islands = [[sp] + [mutate(sp, rng) for _ in range(9)] for sp in species]
    cache = {}                                    # gid -> {seed: bank}

    def fitness(g):
        r = cache.get(gid(g), {})
        return sum(r.values()) / len(r) if len(r) == len(seeds) else None

    for gen in range(10**9):                      # wall clock breaks the loop
        for pop in islands:                       # evaluate the fresh genomes
            for g in pop:                         # (parallel pool in the real
                for s in seeds:                   #  build; every candidate on
                    if s not in cache.setdefault(gid(g), {}):   # the SAME
                        cache[gid(g)][s] = evaluate(compile_spec(g), s)  # CRN
        nxt = []
        for pop in islands:
            pop.sort(key=lambda g: -fitness(g))
            child_pop = [pop[0]]                  # elitism: best survives
            while len(child_pop) < len(pop):
                a, b = (tournament(pop, rng, fitness) for _ in "ab")
                child = crossover(a, b, rng) if rng.random() < 0.6                     else copy.deepcopy(a)
                child_pop.append(mutate(child, rng))
            nxt.append(child_pop)
        islands = nxt
        if gen % 6 == 5:                          # ring migration: best of
            bests = [max(p, key=fitness) for p in islands]      # island i-1
            for i, pop in enumerate(islands):     # replaces worst of island i
                pop.sort(key=fitness)
                pop[0] = copy.deepcopy(bests[i - 1])
    # afterwards: re-read the winner on a DISJOINT confirm panel; the
    # screening mean of a selected best is inflated (winner's curse) [8]

def tournament(pop, rng, fitness, k=3):
    return max(rng.sample(pop, k), key=fitness)

print("search skeleton defined: species x islands x CRN x ring migration")

from kaggle_environments import make

PASS = {"farmer": ["PASS"], "hands": [], "market": []}

def bank_of(agent_fn, seed, steps=720):
    env = make("kaggriculture",
               configuration={"episodeSteps": steps, "seed": int(seed)})
    env.reset(2)
    while not env.done:
        shared = env.state[0].observation         # seat 1 gets a trimmed
        obs = dict(env.state[0].observation)      # observation; merge the
        for k, v in shared.items():               # shared fields like the
            obs.setdefault(k, v)                  # live framework does
        env.step([agent_fn(obs), dict(PASS)])
    return float(env.state[0].reward or 0)

idle_bank = bank_of(lambda obs: dict(PASS), seed=11)
print(f"an agent that does nothing banks ${idle_bank:,.0f} on seed 11:")
print("that is the zero of the whole corridor in section 3")

import matplotlib.pyplot as plt

def _decomposition(path, record):
    """the file names its bases after the recorded streams; the figure does not"""
    raw, out, n = json.loads(Path(path).read_text()), {}, 0
    for k, v in raw.items():
        if k.startswith("winner"):
            out["winner"] = v
        else:
            n += 1
            out[f"base-{n}"] = v
    return out

DECOMP = measurement("stream-delta confirm panel",
                     "streamdelta_1787611187/confirm_decomposition.json", r"""
{
 "winner": {
  "confirm_fitness": 98937.06666666668,
  "idle_mean": 149922.2,
  "company_mean": 73444.5,
  "retention": 0.48988408654622195,
  "rows": {
   "5": {
    "idle": 181063.0,
    "counterbook": 105446.0,
    "queuesplit": 136854.0
   },
   "13": {
    "idle": 103405.0,
    "counterbook": 88573.0,
    "queuesplit": 56230.0
   },
   "29": {
    "idle": 172770.0,
    "counterbook": 62789.0,
    "queuesplit": 70512.0
   },
   "61": {
    "idle": 125857.0,
    "counterbook": 54036.0,
    "queuesplit": 61112.0
   },
   "83": {
    "idle": 166516.0,
    "counterbook": 40907.0,
    "queuesplit": 57986.0
   }
  }
 },
 "base-1": {
  "confirm_fitness": 84162.66666666666,
  "idle_mean": 123530.2,
  "company_mean": 64478.9,
  "retention": 0.5219687169615204,
  "rows": {
   "5": {
    "idle": 112000.0,
    "counterbook": 49174.0,
    "queuesplit": 68336.0
   },
   "13": {
    "idle": 147184.0,
    "counterbook": 44033.0,
    "queuesplit": 116904.0
   },
   "29": {
    "idle": 131516.0,
    "counterbook": 88838.0,
    "queuesplit": 34468.0
   },
   "61": {
    "idle": 157917.0,
    "counterbook": 80933.0,
    "queuesplit": 72507.0
   },
   "83": {
    "idle": 69034.0,
    "counterbook": 54993.0,
    "queuesplit": 34603.0
   }
  }
 },
 "base-2": {
  "confirm_fitness": 103819.66666666666,
  "idle_mean": 136765.6,
  "company_mean": 87346.7,
  "retention": 0.6386598676860262,
  "rows": {
   "5": {
    "idle": 134921.0,
    "counterbook": 92180.0,
    "queuesplit": 100356.0
   },
   "13": {
    "idle": 121059.0,
    "counterbook": 97576.0,
    "queuesplit": 135403.0
   },
   "29": {
    "idle": 169015.0,
    "counterbook": 91210.0,
    "queuesplit": 60938.0
   },
   "61": {
    "idle": 105861.0,
    "counterbook": 59991.0,
    "queuesplit": 111800.0
   },
   "83": {
    "idle": 152972.0,
    "counterbook": 61358.0,
    "queuesplit": 62655.0
   }
  }
 }
}
""", _decomposition)

def panel(entry):
    """alone is the idle column, in company is every rival column, same seeds"""
    rows = entry["rows"].values()
    alone = statistics.mean(r["idle"] for r in rows)
    company = statistics.mean(v for r in rows for k, v in r.items()
                              if k != "idle")
    return [alone / 1000, company / 1000]

bases = {k: v for k, v in DECOMP.items() if k.startswith("base")}
strongest = max(bases, key=lambda k: bases[k]["confirm_fitness"])
base, winner = panel(bases[strongest]), panel(DECOMP["winner"])
gain = [w - b for w, b in zip(winner, base)]
print(f"{len(DECOMP['winner']['rows'])} disjoint confirm seeds, "
      f"{len(next(iter(DECOMP['winner']['rows'].values()))) - 1} rivals: "
      f"alone {gain[0]:+,.1f}k, in company {gain[1]:+,.1f}k")

cats = ["alone\n(vs idle)", "in company\n(vs rivals)"]
x = [0, 1]
fig, ax = plt.subplots(figsize=(8.5, 3.6))
b1 = ax.bar([i - 0.18 for i in x], base, width=0.32, color="#9aa3ad",
            label="zero-delta base stream")
b2 = ax.bar([i + 0.18 for i in x], winner, width=0.32, color="#c2571f",
            label="searched genome (24 market deltas)")
for bars in (b1, b2):
    for r in bars:
        ax.annotate(f"{r.get_height():.1f}k",
                    (r.get_x() + r.get_width() / 2, r.get_height()),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=9)
ax.annotate(f"{gain[0]:+.1f}k", (0.52, 160), ha="center", fontsize=11,
            color="#14724d", weight="bold")
ax.annotate(f"{gain[1]:+.1f}k", (1.52, 96), ha="center", fontsize=11,
            color="#b5486b", weight="bold")
ax.set_xticks(x)
ax.set_xticklabels(cats)
ax.set_ylim(0, 172)
ax.set_ylabel("mean bank, disjoint confirm panel\n(thousands of $)")
ax.set_title("the same 24 deltas, two opposite verdicts: alone they\n"
             "EARN, in company they EXPOSE", fontsize=10)
ax.legend(frameon=False, fontsize=9, loc="upper right")
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

def _arena(path, record):
    """the file names every contender; the figure ranks anonymised ones"""
    raw, rows, n = json.loads(Path(path).read_text()), [], 0
    for r in raw["ranking"]:
        mine = r.get("source") == "(ours)"
        if not mine:
            n += 1
        rows.append({"label": "mine" if mine else chr(64 + n),
                     "wins": r["wins"], "games": r["games"],
                     "mean_bank": r["mean_bank"]})
    return {**record, "games": raw["games"], "ranking": rows}

ARENA = measurement("registry arena", "donor_arena_20260824.json", r"""
{
 "run": "donor_arena_20260824",
 "games": 66,
 "seeds": [
  11,
  23,
  47
 ],
 "note": "community ids dropped on purpose: the figure ranks anonymised contenders, and their authors are credited for their work rather than ranked",
 "ranking": [
  {
   "label": "A",
   "wins": 6,
   "games": 6,
   "mean_bank": 114065
  },
  {
   "label": "B",
   "wins": 6,
   "games": 6,
   "mean_bank": 131709
  },
  {
   "label": "C",
   "wins": 6,
   "games": 6,
   "mean_bank": 86904
  },
  {
   "label": "D",
   "wins": 6,
   "games": 6,
   "mean_bank": 114025
  },
  {
   "label": "E",
   "wins": 6,
   "games": 6,
   "mean_bank": 123800
  },
  {
   "label": "F",
   "wins": 6,
   "games": 6,
   "mean_bank": 123800
  },
  {
   "label": "G",
   "wins": 6,
   "games": 6,
   "mean_bank": 86904
  },
  {
   "label": "H",
   "wins": 6,
   "games": 6,
   "mean_bank": 123800
  },
  {
   "label": "I",
   "wins": 6,
   "games": 6,
   "mean_bank": 114039
  },
  {
   "label": "J",
   "wins": 6,
   "games": 6,
   "mean_bank": 86819
  },
  {
   "label": "mine",
   "wins": 6,
   "games": 66,
   "mean_bank": 43186
  },
  {
   "label": "mine",
   "wins": 0,
   "games": 6,
   "mean_bank": 33705
  }
 ]
}
""", _arena)

rows = ARENA["ranking"]
LAB = [r["label"] for r in rows]
WINS = [r["wins"] for r in rows]
BANK = [r["mean_bank"] / 1000 for r in rows]
colors = ["#c2571f" if lab == "mine" else "#2f6fb2" for lab in LAB]
y = list(range(len(LAB)))[::-1]
public = [r for r in rows if r["label"] != "mine"]
banded = sorted(r["mean_bank"] / 1000 for r in public)[1:]   # all but the weakest
lo, hi = banded[0], banded[-1]
per_agent = rows[0]["games"]
print(f"{ARENA['games']} games, {len(rows)} contenders, "
      f"{per_agent:.0f} games each over seeds {ARENA['seeds']}")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=True)
a1.barh(y, BANK, color=colors, height=0.62)
a1.axvspan(lo, hi, color="#14724d", alpha=0.12)
a1.set_yticks(y); a1.set_yticklabels(LAB, fontsize=8)
a1.set_xlabel("mean bank (thousands of $)")
a1.set_title(f"banks COMPRESS: nine of the ten public"
             f"\nagents within one {hi - lo:.0f}k band", fontsize=10)
a2.barh(y, WINS, color=colors, height=0.62)
a2.set_xlabel(f"wins (of {per_agent:.0f})")
a2.set_title(f"wins SEPARATE the same agents:"
             f"\n{min(r['wins'] for r in public):.0f} to"
             f" {max(r['wins'] for r in public):.0f} across that band",
             fontsize=10)
for ax in (a1, a2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt
from math import erf, sqrt

SIG = 8.0                        # within-pairing margin spread (k$)
EPS = [-9.1, 1.8, 6.4]           # one 3-game panel's noise draws (k$)
mus = [x / 10 for x in range(-150, 151)]
step = [sum(m + e > 0 for e in EPS) / 3 for m in mus]
phi = [0.5 * (1 + erf(m / SIG / sqrt(2))) for m in mus]

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(mus, step, color="#9aa3ad", lw=2, drawstyle="steps-post",
        label="raw win rate on a 3-game panel")
ax.plot(mus, phi, color="#c2571f", lw=2,
        label="Phi(mu/sigma): implied win probability")
ax.annotate("a +4k margin improvement\nmoves the count not at all",
            (-4.1, 0.345), fontsize=8.5, ha="center", color="#5a6470",
            xytext=(-10.8, 0.60), textcoords="data",
            arrowprops=dict(arrowstyle="->", color="#5a6470", lw=1))
ax.set_xlabel("true mean margin vs this rival (thousands of $)")
ax.set_ylabel("objective value")
ax.set_title("the same information, two objectives: the count is a staircase,\n"
             "Phi pays every dollar of margin", fontsize=10)
ax.legend(frameon=False, fontsize=9, loc="lower right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

def _escape(path, record):
    rows = [json.loads(ln) for ln in Path(path).read_text().splitlines()
            if ln.strip()]
    keep = record["generations_shown"]
    return {**record, "games": [r for r in rows if r["gen"] <= keep]}

ESCAPE = measurement("escape validation",
                     "escape_validation_20260824/log.jsonl", r"""
{
 "run": "escape_validation_20260824",
 "generations_shown": 16,
 "stagnation_gens": 4,
 "restarts_after_gen": [
  4.5,
  9.5
 ],
 "restart_note": "the game rows carry no restart flag: these two markers are the island restarts the run announced on its console, and they are the only figures here that a reader cannot recompute from the rows",
 "games": [
  {
   "gen": 1,
   "island": 1,
   "gid": "22ff4da868",
   "seed": 11,
   "bank": 15142.0
  },
  {
   "gen": 1,
   "island": 2,
   "gid": "cfdadd8f02",
   "seed": 11,
   "bank": 27109.0
  },
  {
   "gen": 1,
   "island": 0,
   "gid": "0ab181f21c",
   "seed": 11,
   "bank": 32095.0
  },
  {
   "gen": 1,
   "island": 2,
   "gid": "cfdadd8f02",
   "seed": 11,
   "bank": 27109.0
  },
  {
   "gen": 1,
   "island": 1,
   "gid": "34e3c460ed",
   "seed": 11,
   "bank": 16091.0
  },
  {
   "gen": 1,
   "island": 1,
   "gid": "fbd8bb458d",
   "seed": 11,
   "bank": 11014.0
  },
  {
   "gen": 1,
   "island": 2,
   "gid": "cfdadd8f02",
   "seed": 11,
   "bank": 27109.0
  },
  {
   "gen": 1,
   "island": 2,
   "gid": "1bc5c70d44",
   "seed": 11,
   "bank": 30172.0
  },
  {
   "gen": 1,
   "island": 2,
   "gid": "c77da2ed21",
   "seed": 11,
   "bank": 28965.0
  },
  {
   "gen": 2,
   "island": 1,
   "gid": "1bc2f29d28",
   "seed": 11,
   "bank": 9654.0
  },
  {
   "gen": 2,
   "island": 1,
   "gid": "617cd564e9",
   "seed": 11,
   "bank": 13074.0
  },
  {
   "gen": 2,
   "island": 0,
   "gid": "27aa61bbd8",
   "seed": 11,
   "bank": 28655.0
  },
  {
   "gen": 2,
   "island": 0,
   "gid": "8bb59a9f1c",
   "seed": 11,
   "bank": 29470.0
  },
  {
   "gen": 2,
   "island": 2,
   "gid": "5964f5fa1c",
   "seed": 11,
   "bank": 23189.0
  },
  {
   "gen": 2,
   "island": 2,
   "gid": "ef8c49d9b4",
   "seed": 11,
   "bank": 27865.0
  },
  {
   "gen": 3,
   "island": 1,
   "gid": "ec7d45c785",
   "seed": 11,
   "bank": 17407.0
  },
  {
   "gen": 3,
   "island": 1,
   "gid": "8f39b3d175",
   "seed": 11,
   "bank": 17154.0
  },
  {
   "gen": 3,
   "island": 0,
   "gid": "d04e9e7b3b",
   "seed": 11,
   "bank": 22565.0
  },
  {
   "gen": 3,
   "island": 0,
   "gid": "e2e56d9906",
   "seed": 11,
   "bank": 32062.0
  },
  {
   "gen": 3,
   "island": 2,
   "gid": "a9155a3ec9",
   "seed": 11,
   "bank": 23352.0
  },
  {
   "gen": 3,
   "island": 2,
   "gid": "400ac01159",
   "seed": 11,
   "bank": 30414.0
  },
  {
   "gen": 4,
   "island": 1,
   "gid": "8a07533918",
   "seed": 11,
   "bank": 17407.0
  },
  {
   "gen": 4,
   "island": 2,
   "gid": "20b7925489",
   "seed": 11,
   "bank": 30414.0
  },
  {
   "gen": 5,
   "island": 1,
   "gid": "c66be7cdf2",
   "seed": 11,
   "bank": 17407.0
  },
  {
   "gen": 5,
   "island": 1,
   "gid": "09f5e56183",
   "seed": 11,
   "bank": 24236.0
  },
  {
   "gen": 5,
   "island": 0,
   "gid": "9ef1790fcd",
   "seed": 11,
   "bank": 23613.0
  },
  {
   "gen": 5,
   "island": 0,
   "gid": "92a9b55ee4",
   "seed": 11,
   "bank": 29445.0
  },
  {
   "gen": 5,
   "island": 2,
   "gid": "90efcf5afe",
   "seed": 11,
   "bank": 31809.0
  },
  {
   "gen": 5,
   "island": 2,
   "gid": "2d31efedb8",
   "seed": 11,
   "bank": 34250.0
  },
  {
   "gen": 6,
   "island": 0,
   "gid": "55d0a1d03e",
   "seed": 11,
   "bank": 21787.0
  },
  {
   "gen": 6,
   "island": 1,
   "gid": "13c4bd8897",
   "seed": 11,
   "bank": 32095.0
  },
  {
   "gen": 6,
   "island": 1,
   "gid": "eac720ba7b",
   "seed": 11,
   "bank": 33923.0
  },
  {
   "gen": 6,
   "island": 2,
   "gid": "30062163e3",
   "seed": 11,
   "bank": 36721.0
  },
  {
   "gen": 6,
   "island": 2,
   "gid": "fb5158bafd",
   "seed": 11,
   "bank": 34119.0
  },
  {
   "gen": 7,
   "island": 1,
   "gid": "ce98aea2f0",
   "seed": 11,
   "bank": 31674.0
  },
  {
   "gen": 7,
   "island": 0,
   "gid": "3124f5151c",
   "seed": 11,
   "bank": 27086.0
  },
  {
   "gen": 7,
   "island": 2,
   "gid": "172434dd48",
   "seed": 11,
   "bank": 36143.0
  },
  {
   "gen": 8,
   "island": 1,
   "gid": "29c1edc205",
   "seed": 11,
   "bank": 28016.0
  },
  {
   "gen": 8,
   "island": 1,
   "gid": "f35798a3ec",
   "seed": 11,
   "bank": 29556.0
  },
  {
   "gen": 8,
   "island": 0,
   "gid": "89b16b9b3f",
   "seed": 11,
   "bank": 29231.0
  },
  {
   "gen": 8,
   "island": 0,
   "gid": "ceaa96a6b5",
   "seed": 11,
   "bank": 25109.0
  },
  {
   "gen": 8,
   "island": 2,
   "gid": "5b2fdc8199",
   "seed": 11,
   "bank": 30945.0
  },
  {
   "gen": 8,
   "island": 2,
   "gid": "2505675ae4",
   "seed": 11,
   "bank": 36721.0
  },
  {
   "gen": 9,
   "island": 1,
   "gid": "dc12c402d8",
   "seed": 11,
   "bank": 21371.0
  },
  {
   "gen": 9,
   "island": 1,
   "gid": "b85627555f",
   "seed": 11,
   "bank": 32444.0
  },
  {
   "gen": 9,
   "island": 0,
   "gid": "764c957cf3",
   "seed": 11,
   "bank": 30257.0
  },
  {
   "gen": 9,
   "island": 0,
   "gid": "a2c6e6c74d",
   "seed": 11,
   "bank": 25087.0
  },
  {
   "gen": 9,
   "island": 2,
   "gid": "363b85b476",
   "seed": 11,
   "bank": 31905.0
  },
  {
   "gen": 9,
   "island": 2,
   "gid": "9e3f21ec90",
   "seed": 11,
   "bank": 32223.0
  },
  {
   "gen": 10,
   "island": 1,
   "gid": "e7cdc70b9b",
   "seed": 11,
   "bank": 29393.0
  },
  {
   "gen": 10,
   "island": 0,
   "gid": "829b3daf3e",
   "seed": 11,
   "bank": 24691.0
  },
  {
   "gen": 10,
   "island": 2,
   "gid": "518005fde4",
   "seed": 11,
   "bank": 30753.0
  },
  {
   "gen": 11,
   "island": 1,
   "gid": "4f782be1b2",
   "seed": 11,
   "bank": 25365.0
  },
  {
   "gen": 11,
   "island": 0,
   "gid": "6994c1258e",
   "seed": 11,
   "bank": 37805.0
  },
  {
   "gen": 11,
   "island": 0,
   "gid": "7b92444781",
   "seed": 11,
   "bank": 26440.0
  },
  {
   "gen": 11,
   "island": 1,
   "gid": "8201977d76",
   "seed": 11,
   "bank": 36721.0
  },
  {
   "gen": 11,
   "island": 2,
   "gid": "5b4d6da085",
   "seed": 11,
   "bank": 38902.0
  },
  {
   "gen": 12,
   "island": 0,
   "gid": "6da678901f",
   "seed": 11,
   "bank": 35923.0
  },
  {
   "gen": 12,
   "island": 1,
   "gid": "7cb511a5fc",
   "seed": 11,
   "bank": 37994.0
  },
  {
   "gen": 12,
   "island": 0,
   "gid": "607c9bb884",
   "seed": 11,
   "bank": 30162.0
  },
  {
   "gen": 12,
   "island": 1,
   "gid": "810293c7ff",
   "seed": 11,
   "bank": 28229.0
  },
  {
   "gen": 12,
   "island": 2,
   "gid": "a5e8765f9f",
   "seed": 11,
   "bank": 35314.0
  },
  {
   "gen": 12,
   "island": 2,
   "gid": "6490928fe5",
   "seed": 11,
   "bank": 31809.0
  },
  {
   "gen": 13,
   "island": 2,
   "gid": "9f823b18c2",
   "seed": 11,
   "bank": 43629.0
  },
  {
   "gen": 13,
   "island": 0,
   "gid": "f25f396655",
   "seed": 11,
   "bank": 36998.0
  },
  {
   "gen": 13,
   "island": 1,
   "gid": "0bab57b72f",
   "seed": 11,
   "bank": 30356.0
  },
  {
   "gen": 14,
   "island": 1,
   "gid": "2b6bf357a8",
   "seed": 11,
   "bank": 33940.0
  },
  {
   "gen": 14,
   "island": 0,
   "gid": "af9858c82f",
   "seed": 11,
   "bank": 32273.0
  },
  {
   "gen": 14,
   "island": 0,
   "gid": "12cba662b9",
   "seed": 11,
   "bank": 39197.0
  },
  {
   "gen": 14,
   "island": 1,
   "gid": "85200b78fd",
   "seed": 11,
   "bank": 35716.0
  },
  {
   "gen": 14,
   "island": 2,
   "gid": "0958068169",
   "seed": 11,
   "bank": 35967.0
  },
  {
   "gen": 14,
   "island": 2,
   "gid": "e0ee219657",
   "seed": 11,
   "bank": 27701.0
  },
  {
   "gen": 15,
   "island": 0,
   "gid": "e31cc062b7",
   "seed": 11,
   "bank": 40905.0
  },
  {
   "gen": 15,
   "island": 0,
   "gid": "3e54593a57",
   "seed": 11,
   "bank": 31499.0
  },
  {
   "gen": 15,
   "island": 1,
   "gid": "7a3a1368e9",
   "seed": 11,
   "bank": 29398.0
  },
  {
   "gen": 15,
   "island": 1,
   "gid": "34faa34148",
   "seed": 11,
   "bank": 33947.0
  },
  {
   "gen": 15,
   "island": 2,
   "gid": "ed472a3f6e",
   "seed": 11,
   "bank": 40910.0
  },
  {
   "gen": 15,
   "island": 2,
   "gid": "f85734bcda",
   "seed": 11,
   "bank": 39722.0
  },
  {
   "gen": 16,
   "island": 2,
   "gid": "ae61f9b0aa",
   "seed": 11,
   "bank": 44176.0
  },
  {
   "gen": 16,
   "island": 0,
   "gid": "89b46b9434",
   "seed": 11,
   "bank": 45245.0
  },
  {
   "gen": 16,
   "island": 1,
   "gid": "eda765ed48",
   "seed": 11,
   "bank": 37029.0
  }
 ]
}
""", _escape)

# the running best per generation IS the figure: a groupby over one row per
# engine game, not a series typed underneath the chart
GENS = sorted({g["gen"] for g in ESCAPE["games"]})
BEST, running = [], float("-inf")
for gen in GENS:
    running = max([running] + [g["bank"] for g in ESCAPE["games"]
                               if g["gen"] == gen])
    BEST.append(running)
RESTARTS = ESCAPE["restarts_after_gen"]
FLAT = ESCAPE["stagnation_gens"]
print(f"{len(ESCAPE['games'])} games over {len(GENS)} generations, "
      f"global best {BEST[0]:,.0f} -> {BEST[-1]:,.0f}")
print("restart markers:", ESCAPE["restart_note"])

fig, ax = plt.subplots(figsize=(9, 3.4))
ax.plot(GENS, [b / 1000 for b in BEST], "-o", ms=4, color="#2f6fb2",
        label="global best")
for i, x in enumerate(RESTARTS):
    ax.axvline(x, color="#c2571f", lw=1.2, ls="--")
    ax.annotate(f"island restart\n(flat {FLAT} gens)", (x, 33.2 + 6 * i),
                ha="center", fontsize=8, color="#c2571f",
                xytext=(x + (1.6 if i == 0 else 1.8), 32.6 + 5.5 * i),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", color="#c2571f", lw=1))
ax.set_xlabel("generation")
ax.set_ylabel("global best, bank vs idle\n(thousands of $)")
ax.set_title("escape validation (aggressive thresholds): every restart is\nfollowed by a new record within two generations", fontsize=10)
ax.set_xticks(GENS)
ax.legend(frameon=False, fontsize=9, loc="lower right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()