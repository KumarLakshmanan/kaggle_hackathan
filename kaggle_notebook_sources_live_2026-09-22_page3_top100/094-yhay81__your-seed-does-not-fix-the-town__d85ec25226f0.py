# Pinned so the measurements below stay reproducible as the engine moves on.
# If this cannot run (internet off, no pip) the notebook still works -- it just measures
# whatever engine is installed, and the next cell prints which one that is.
import subprocess
import sys

PIN = "kaggle-environments==1.32.6"
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", PIN],
                   check=True, capture_output=True, timeout=600)
    print("pinned:", PIN)
except Exception as exc:  # noqa: BLE001 - any failure here is non-fatal by design
    print(f"could not pin ({type(exc).__name__}); measuring the preinstalled engine instead")


import contextlib
import inspect
import io
import json
import time
import random
import statistics as st
from collections import Counter
from fractions import Fraction
from importlib.metadata import version
from math import comb

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display

# Importing kaggle_environments prints its whole OpenSpiel game registry; keep it quiet.
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.dpi": 120, "axes.titlesize": 12, "axes.titlelocation": "left",
                     "axes.titlepad": 12, "axes.labelsize": 10, "font.size": 10})
BLUE, ORANGE, VERMILION, GRAY = "#0072B2", "#E69F00", "#D55E00", "#6B7280"
GREEN = "#009E73"


def show(df, caption):
    """Render a result as a table with the question it answers written on it."""
    display(df.style.set_caption(caption).hide(axis="index")
            .set_table_styles([{"selector": "caption",
                                "props": [("caption-side", "top"), ("text-align", "left"),
                                          ("font-weight", "600"), ("padding-bottom", "6px")]}]))

print("kaggle-environments:", version("kaggle-environments"))
POST_BALANCE = hasattr(K, "MAX_SHOP_INSTANCES")
print("post-rebalance engine (shops drawn with replacement):", POST_BALANCE)
assert POST_BALANCE, "this notebook measures the 1.32.6 town; install it and re-run" 

src = inspect.getsource(K._end_of_day)
print("\n--- kaggriculture._end_of_day, the relevant lines ---")
for line in src.splitlines():
    if any(t in line for t in ("random.Random", "_spawn_weeds", "rng.choice", "unlocked_shops")):
        print("   ", line.strip())

assert "random.Random((seed * 1_000_003) ^ day)" in src, "per-day RNG construction changed"
assert src.index("_spawn_weeds") < src.index("rng.choice"), "weeds no longer precede the shop draw"
assert "rng.random()" in inspect.getsource(K._spawn_weeds)
print("\nOK: one per-day RNG, weeds consume it first, the shop draw takes what is left.")


# The counting: only None tiles consume a draw.
probe_farm = {"tiles": [[None, "LOCKED"], [{"kind": "WEED"}, None]]}
calls = {"n": 0}


class CountingRng:
    def random(self):
        calls["n"] += 1
        return 1.0  # never below weed_chance, so nothing on the board changes


K._spawn_weeds(probe_farm, 2, 0.005, CountingRng())
print(f"4 tiles, of which 2 are empty -> {calls['n']} rng.random() calls")
assert calls["n"] == 2

SHOP_TYPES = sorted(K.SHOPS)


def shop_drawn_after(seed, day, n_draws, remaining=None):
    """Reproduce the engine's draw for a given position in the per-day stream."""
    rng = random.Random((seed * 1_000_003) ^ day)
    for _ in range(n_draws):
        rng.random()
    return rng.choice(sorted(remaining if remaining is not None else SHOP_TYPES))


N_SEEDS = 2000
changed = sum(
    1 for s in range(N_SEEDS)
    if shop_drawn_after(s, 2, 48) != shop_drawn_after(s, 2, 49)
)
print(f"\nOne extra bare tile anywhere on either farm changes the day-3 shop in "
      f"{changed}/{N_SEEDS} seeds = {changed / N_SEEDS * 100:.1f}%")
clean = (len(SHOP_TYPES) - 1) / len(SHOP_TYPES) * 100
print(f"(a fully independent re-roll would change it {clean:.1f}% of the time, "
      f"so this is close to one)")


fig, ax = plt.subplots(figsize=(9.6, 3.2))
STEP, TICK_W = 1.0, 0.24


def draw_stream_row(y, n_opponent, shop_name, label):
    for i in range(6):                                    # your farm's empty tiles
        ax.add_patch(plt.Rectangle((i * STEP, y), TICK_W, 0.42, color=GRAY, alpha=0.45))
    for i in range(n_opponent):                           # the opponent's empty tiles
        ax.add_patch(plt.Rectangle(((6 + i) * STEP, y), TICK_W, 0.42, color=BLUE))
    box_x = (6 + n_opponent) * STEP + 0.3
    ax.add_patch(plt.Rectangle((box_x, y - 0.1), 2.0, 0.62, facecolor=ORANGE, alpha=0.22,
                               edgecolor=ORANGE, linewidth=1.6))
    ax.text(box_x + 1.0, y + 0.21, "shop draw", ha="center", va="center",
            fontsize=9, color=VERMILION, fontweight="bold")
    ax.text(box_x + 2.25, y + 0.21, f"→  {shop_name}", va="center", fontsize=10)
    ax.text(-0.45, y + 0.21, label, ha="right", va="center", fontsize=11, color="0.35")
    return box_x


a_x = draw_stream_row(1.55, 6, "PET_CAFE", "A")
b_x = draw_stream_row(0.15, 5, "SMOOTHIE_SHOP", "B")
ax.add_patch(plt.Circle((11 * STEP + TICK_W / 2, 1.76), 0.36, fill=False,
                        edgecolor=BLUE, linestyle=(0, (2, 2)), linewidth=1.3))
ax.annotate("", xy=(b_x + 0.15, 0.95), xytext=(a_x + 0.15, 0.95),
            arrowprops=dict(arrowstyle="->", color=VERMILION, lw=1.5))
ax.text(b_x - 1.0, 0.98,
        "one fewer empty tile on the opponent's farm\nshifts the draw one tick earlier",
        ha="right", va="center", fontsize=9, color=VERMILION)
ax.text(2.6, 2.42, "your empty tiles", fontsize=9, color="0.4", ha="center")
ax.text(8.6, 2.42, "the opponent's empty tiles", fontsize=9, color=BLUE, ha="center")
ax.annotate("", xy=(15.8, -0.38), xytext=(0, -0.38),
            arrowprops=dict(arrowstyle="->", color="0.6", lw=1))
ax.text(0, -0.68, "the day's random stream, consumed one draw at a time",
        fontsize=9, color="0.45")
ax.set_xlim(-1.5, 16.8)
ax.set_ylim(-1.0, 2.85)
ax.axis("off")
ax.set_title("Same seed, same day: the shop is drawn from whatever the weeds leave behind")
plt.tight_layout()
plt.show()


def idle(obs):
    return {"farmer": ["PASS"], "hands": [], "market": []}


def idle_plus_one_tile(obs):
    step = obs.get("step", 0)
    seeds = (obs.get("private", {}) or {}).get("seeds", {})
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "CARROT", 1]]}
    if step == 1 and seeds.get("CARROT", 0) > 0:
        return {"farmer": ["PLANT", "CARROT"], "hands": [], "market": []}
    return {"farmer": ["PASS"], "hands": [], "market": []}


def play(agents, seed, steps=720, ctx=None):
    def run():
        env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
        env.run(agents)
        last = env.steps[-1]
        obs = last[0]["observation"]
        return {
            "p0": last[0]["reward"],
            "p1": last[1]["reward"],
            "shops": list(obs["town"]["unlocked_shops"]),
            "prices": dict(obs["market"]["prices"]),
        }

    if ctx is None:
        return run()
    with ctx:
        return run()


def recording(policy):
    """Wrap an agent so we can prove afterwards that it played the same game."""
    log = []

    def wrapped(obs):
        action = policy(obs)
        log.append(repr(action))
        return action

    wrapped.log = log
    return wrapped


rows = []
for seed in range(12):
    rec_a, rec_b = recording(K.starter_agent), recording(K.starter_agent)
    a = play([rec_a, idle], seed)
    b = play([rec_b, idle_plus_one_tile], seed)
    rows.append((seed, a["p0"], b["p0"], a["shops"] == b["shops"], rec_a.log == rec_b.log))

tbl = pd.DataFrame(
    [{"seed": s, "bank vs idle": f"{a:,.0f}", "bank vs idle+1 tile": f"{b:,.0f}",
      "change": f"{b - a:+,.0f}",
      "same town?": "yes" if st_ else "NO", "same 720 actions?": "yes" if sp else "no"}
     for s, a, b, st_, sp in rows])
show(tbl, "Player 0 never changes. Only the opponent's tile count does.")

n_same_town = sum(1 for r in rows if r[3])
n_same_play = sum(1 for r in rows if r[4])
n_moved = sum(1 for r in rows if r[1] != r[2])
print(f"player 0 played the identical action sequence: {n_same_play}/{len(rows)} seeds")
print(f"identical shop schedule:                      {n_same_town}/{len(rows)} seeds")
print(f"player 0's bank changed anyway:               {n_moved}/{len(rows)} seeds")


sched_a = play(["starter", idle], 0)["shops"]
sched_b = play(["starter", idle_plus_one_tile], 0)["shops"]
palette = dict(zip(SHOP_TYPES, plt.cm.tab10.colors))

fig, ax = plt.subplots(figsize=(9.6, 2.5))
for row, (sched, label) in enumerate([(sched_b, "opponent has one extra occupied tile"),
                                      (sched_a, "opponent idle")]):
    for slot, shop in enumerate(sched):
        ax.add_patch(plt.Rectangle((slot, row), 0.94, 0.8, color=palette[shop]))
        ax.text(slot + 0.47, row + 0.4, shop.replace("_", "\n"), ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")
    ax.text(-0.25, row + 0.4, label, ha="right", va="center", fontsize=9.5)
ax.set_xticks([i + 0.47 for i in range(8)])
ax.set_xticklabels([f"day {3 * (i + 1)}" for i in range(8)], fontsize=9)
ax.set_yticks([])
ax.set_xlim(-6.2, 8.2)
ax.set_ylim(-0.15, 2.0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.grid(False)
ax.set_title("Seed 0: the same seed, two different towns")
plt.tight_layout()
plt.show()

matching = sum(1 for x, y in zip(sched_a, sched_b) if x == y)
print(f"slots holding the same shop in both runs: {matching}/8")


CROP_INFO = {
    "WHEAT": {"seed": 10, "max_yield_day": 4, "ongoing": False},
    "CARROT": {"seed": 20, "max_yield_day": 3, "ongoing": False},
    "STRAWBERRY": {"seed": 100, "max_yield_day": 10, "ongoing": True},
}
SELL_BATCH = {"STRAWBERRY": 3, "CARROT": 6, "WHEAT": 8}
SEED_BUFFER = {"STRAWBERRY": 2, "CARROT": 2, "WHEAT": 2}
ROW_CROP = ["STRAWBERRY", "STRAWBERRY", "CARROT", "CARROT", "WHEAT"]
TARGET_HANDS = 5


def _jobs(farm, seeds, day):
    """Everything the farm needs done, as (priority, tile, op)."""
    jobs = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if tile == "LOCKED":
                continue
            if tile is None:
                crop = ROW_CROP[y % 5]
                if seeds.get(crop, 0) > 0:
                    jobs.append((40, (x, y), ("PLANT", crop)))
                continue
            kind = tile.get("kind")
            if kind == "WEED":
                jobs.append((20, (x, y), ("DIG",)))
            elif kind == "PLANT":
                info = CROP_INFO.get(tile["crop"])
                age = day - tile["planted_day"]
                ready = tile["yield_units"] > 0 and (
                    info is None or info["ongoing"] or age >= info["max_yield_day"]
                )
                if ready:
                    jobs.append((60, (x, y), ("HARVEST",)))
                if not tile["watered_today"]:
                    urgent = tile["consecutive_unwatered"] >= 1
                    jobs.append((99 if urgent else 70, (x, y), ("WATER",)))
    return jobs


def _step_towards(pos, target):
    (x, y), (tx, ty) = pos, target
    if x != tx:
        return "EAST" if x < tx else "WEST"
    if y != ty:
        return "SOUTH" if y < ty else "NORTH"
    return None


def field_agent(obs):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    seeds = dict(private.get("seeds", {}) or {})
    shed = private.get("shed", {}) or {}
    day, hour, money = obs.get("day", 0), obs.get("hour", 0), farm["money"]
    units = [tuple(farm["farmer"])] + [tuple(h) for h in farm.get("hands", [])]
    n_hands = len(farm.get("hands", []))

    market = []
    if hour == 0:
        market += [["HIRE"]] * max(0, TARGET_HANDS - farm.get("hires_today", 0))
    for product, batch in SELL_BATCH.items():          # meter sales down the price curve
        if shed.get(product, 0) > 0:
            market.append(["SELL", product, min(batch, shed[product])])
    for crop, want in SEED_BUFFER.items():
        need, cost = want - seeds.get(crop, 0), CROP_INFO[crop]["seed"]
        if need > 0 and money >= cost * need:
            market.append(["BUY_SEED", crop, need])
            money -= cost * need
            seeds[crop] = seeds.get(crop, 0) + need
    if len(farm["unlocked_quadrants"]) < 3 and money >= 6000:
        market.append(["BUY_LAND"])
    market = market[:10]

    jobs = sorted(_jobs(farm, seeds, day), key=lambda j: -j[0])
    plant_budget, assigned, taken = dict(seeds), {}, set()
    for _, target, op in jobs:
        if target in taken:
            continue
        if op[0] == "PLANT" and plant_budget.get(op[1], 0) <= 0:
            continue
        free = [i for i in range(len(units)) if i not in assigned]
        if not free:
            break
        i = min(free, key=lambda i: abs(units[i][0] - target[0]) + abs(units[i][1] - target[1]))
        assigned[i] = (target, op)
        taken.add(target)
        if op[0] == "PLANT":
            plant_budget[op[1]] -= 1

    actions = []
    for i in range(len(units)):
        if i not in assigned:
            actions.append(["PASS"])
            continue
        target, op = assigned[i]
        move = _step_towards(units[i], target)
        actions.append([move] if move else list(op))
    return {"farmer": actions[0], "hands": actions[1:1 + n_hands], "market": market}


demo = play([field_agent, "starter"], seed=7)
print(f"field agent {demo['p0']:,.0f}   vs built-in starter {demo['p1']:,.0f}")


_ORIGINAL_END_OF_DAY = K._end_of_day


@contextlib.contextmanager
def pinned_shops(schedule):
    """Force the k-th shop unlock of the episode to be schedule[k]."""

    def patched(state, env, day):
        town = state[0].observation.town
        before = len(town["unlocked_shops"])
        _ORIGINAL_END_OF_DAY(state, env, day)
        if len(town["unlocked_shops"]) > before and before < len(schedule):
            town["unlocked_shops"][-1] = schedule[before]

    K._end_of_day = patched
    try:
        yield
    finally:
        K._end_of_day = _ORIGINAL_END_OF_DAY


@contextlib.contextmanager
def no_shops():
    """Unlock nothing: the town centre becomes the only demand in the game."""

    def patched(state, env, day):
        town = state[0].observation.town
        before = len(town["unlocked_shops"])
        _ORIGINAL_END_OF_DAY(state, env, day)
        del town["unlocked_shops"][before:]

    K._end_of_day = patched
    try:
        yield
    finally:
        K._end_of_day = _ORIGINAL_END_OF_DAY


SEED = 7
rng = random.Random(0)
# 1.32.6 draws eight instances with replacement, so a town is a multiset, not a permutation.
schedules = [[rng.choice(SHOP_TYPES) for _ in range(8)] for _ in range(12)]

# Two agents through the identical twelve towns: the built-in starter trades a handful of
# carrots a season, the field agent works a whole quadrant. If the town is what is moving
# the score, the one that trades more should be the one that feels it.
results = {}
for name, policy in (("starter", "starter"), ("field agent", field_agent)):
    banks = []
    for s in schedules:
        r = play([policy, "starter"], SEED, ctx=pinned_shops(s))
        assert r["shops"] == s
        banks.append(r["p0"])
    results[name] = banks

summary = []
for name, banks in results.items():
    lo_, hi_, mid_ = min(banks), max(banks), st.median(banks)
    summary.append({"agent": name, "seed": SEED, "worst draw": f"{lo_:,.0f}",
                    "median": f"{mid_:,.0f}", "best draw": f"{hi_:,.0f}",
                    "spread": f"{(hi_ - lo_) / mid_ * 100:.1f}% of median"})

# One seed could be a fluke, so repeat the field agent through the same towns on two more.
for extra in (21, 42):
    b = [play([field_agent, "starter"], extra, ctx=pinned_shops(s))["p0"] for s in schedules]
    summary.append({"agent": "field agent", "seed": extra, "worst draw": f"{min(b):,.0f}",
                    "median": f"{st.median(b):,.0f}", "best draw": f"{max(b):,.0f}",
                    "spread": f"{(max(b) - min(b)) / st.median(b) * 100:.1f}% of median"})
show(pd.DataFrame(summary),
     "Twelve towns drawn the way 1.32.6 draws them. Nothing else changed.")

banks = results["field agent"]
lo, hi, mid = min(banks), max(banks), st.median(banks)
empty_town = play([field_agent, "starter"], SEED, ctx=no_shops())["p0"]
print(f"\nfield agent, seed {SEED} fixed, only the shop ORDER varies, n={len(banks)}")
for bank, s in sorted(zip(banks, schedules)):
    print(f"  {bank:>9,.0f}   {Counter(s).most_common(3)}")
print(f"  spread {hi - lo:,.0f} = {(hi - lo) / mid * 100:.1f}% of the median season, "
      f"standard deviation {st.stdev(banks):,.0f}")
print(f"  with no shops at all: {empty_town:,.0f} — a town is worth "
      f"{mid / empty_town:.1f}x a townless season")


fig, ax = plt.subplots(figsize=(9, 4.2))
order = sorted(range(len(banks)), key=lambda i: banks[i])
ax.barh([f"{', '.join(schedules[i][:2])} ..." for i in order],
        [banks[i] for i in order], color=BLUE)
ax.axvline(mid, color=VERMILION, linestyle="--", linewidth=1.6, label=f"median {mid:,.0f}")
ax.axvline(empty_town, color=GRAY, linestyle=":", linewidth=1.6,
           label=f"no shops at all {empty_town:,.0f}")
ax.set_xlabel("final bank of the same agent, same seed, same opponent")
ax.set_ylabel("first two shops to unlock")
ax.set_title(f"Only the shop order changes: a {(hi - lo) / mid * 100:.0f}% swing "
             f"(seed {SEED}, n={len(banks)})")
ax.legend(loc="lower right")
plt.tight_layout()
plt.show()


def variant(**overrides):
    """The same policy with one module-level constant swapped for the duration of a call."""
    globals_ = globals()

    def wrapped(obs):
        saved = {k: globals_[k] for k in overrides}
        globals_.update(overrides)
        try:
            return field_agent(obs)
        finally:
            globals_.update(saved)

    return wrapped


BASE = variant()
MARKET_ONLY = variant(SELL_BATCH={**SELL_BATCH, "STRAWBERRY": 4})
LABOUR = variant(TARGET_HANDS=TARGET_HANDS - 1)


def schedule_for(seed):
    r = random.Random(seed)
    s = SHOP_TYPES[:]
    r.shuffle(s)
    return s


AB_SEEDS = list(range(100, 116))
ab = {name: {"stock": [], "pinned": [], "same_town": 0}
      for name in ("market only", "labour")}

for seed in AB_SEEDS:
    sched = schedule_for(seed)
    base_stock = play([BASE, "starter"], seed)
    base_pin = play([BASE, "starter"], seed, ctx=pinned_shops(sched))["p0"]
    for name, arm in (("market only", MARKET_ONLY), ("labour", LABOUR)):
        v_stock = play([arm, "starter"], seed)
        v_pin = play([arm, "starter"], seed, ctx=pinned_shops(sched))["p0"]
        ab[name]["stock"].append(v_stock["p0"] - base_stock["p0"])
        ab[name]["pinned"].append(v_pin - base_pin)
        ab[name]["same_town"] += v_stock["shops"] == base_stock["shops"]

n = len(AB_SEEDS)
ab_rows = []
for name, r in ab.items():
    sd_s, sd_p = st.stdev(r["stock"]), st.stdev(r["pinned"])
    se = sd_s / n ** 0.5
    effect = abs(st.mean(r["stock"]))
    need = max(1, round((2.8 * sd_p / effect) ** 2)) if effect else float("nan")
    ab_rows.append({
        "the knob": name,
        "can it move a tile?": "no" if name == "market only" else "yes",
        "same town as base": f"{r['same_town']}/{n} seeds",
        "measured effect": f"{st.mean(r['stock']):+,.0f}",
        "95% CI": f"[{st.mean(r['stock']) - 1.96 * se:+,.0f}, "
                  f"{st.mean(r['stock']) + 1.96 * se:+,.0f}]",
        "noise sd, stock": f"{sd_s:,.0f}",
        "noise sd, pinned": f"{sd_p:,.0f}",
        "seeds to call it": f"{need:,.0f}",
    })
show(pd.DataFrame(ab_rows),
     f"The same A/B procedure, {n} seeds, two different knobs on the same agent.")

for name, r in ab.items():
    sd_s, sd_p = st.stdev(r["stock"]), st.stdev(r["pinned"])
    verdict = (f"pinning cuts the noise sd by {(1 - sd_p / sd_s) * 100:.0f}%, worth "
               f"{(sd_s / sd_p) ** 2:.1f}x the episodes") if sd_p < sd_s else \
              "pinning changes nothing here; there was nothing to pin away"
    print(f"{name:>12}: {verdict}")


fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
x = range(len(AB_SEEDS))
for axis, (name, r) in zip(axes, ab.items()):
    sd_s, sd_p = st.stdev(r["stock"]), st.stdev(r["pinned"])
    axis.plot(x, r["stock"], "o-", color=ORANGE, label=f"stock engine (sd {sd_s:,.0f})")
    axis.plot(x, r["pinned"], "s--", color=BLUE, label=f"town pinned (sd {sd_p:,.0f})")
    axis.axhline(0, color=GRAY, linewidth=1)
    axis.set_title(f"{name}: {r['same_town']}/{len(AB_SEEDS)} seeds kept the same town")
    axis.set_xlabel("seed index")
    axis.legend(loc="best", fontsize=9)
axes[0].set_ylabel("paired difference in final bank")
fig.suptitle("Same agent, same seeds, two different knobs")
plt.tight_layout()
plt.show()


N = 8  # MAX_SHOP_INSTANCES, and there are 8 shop types
p_absent = Fraction(N - 1, N) ** N
fact = 1
for i in range(1, N + 1):
    fact *= i
p_all = Fraction(fact, N ** N)

print("Drawing 8 shop instances with replacement from 8 types:")
print(f"  P(a given type never appears)  = (7/8)^8 = {float(p_absent) * 100:5.1f}%")
print(f"  P(all eight types appear)      = 8!/8^8  = {float(p_all) * 100:5.2f}%"
      f"   (about 1 game in {round(1 / float(p_all))})")
print(f"  E[distinct types in a town]    = {N * (1 - float(p_absent)):.2f} of 8")
sources = {}
for shop, items in K.SHOPS.items():
    for item in items:
        sources.setdefault(item, []).append(shop)
show(pd.DataFrame([
        {"product": item,
         "shop types that want it": len(srcs),
         "P(none of them opens)": f"{float(Fraction(N - len(srcs), N) ** N) * 100:.1f}%",
         "which": ", ".join(sorted(s.replace('_', ' ').title() for s in srcs))}
        for item, srcs in sorted(sources.items(), key=lambda kv: len(kv[1]))]),
     "After the change, a product is only as safe as the number of shops that want it.")


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.6))

copies = [float(Fraction(comb(N, k) * (N - 1) ** (N - k), N ** N)) * 100 for k in range(5)]
bars = ax1.bar(range(5), copies, color=[VERMILION] + [BLUE] * 4)
for k, v in enumerate(copies):
    ax1.text(k, v + 1.2, f"{v:.1f}%", ha="center", fontsize=9)
ax1.set_xticks(range(5))
ax1.set_xlabel("copies of one specific shop in a town")
ax1.set_ylabel("share of games")
ax1.set_ylim(0, 48)
ax1.set_title("A third of towns are missing any given shop")
bars[0].set_label("absent")


# Exact distribution of the number of distinct shop types among 8 draws with replacement.
def surjections(n, k):                                   # onto-maps from n draws to k types
    return sum((-1) ** j * comb(k, j) * (k - j) ** n for j in range(k + 1))


dist = [comb(N, k) * surjections(N, k) / N ** N * 100 for k in range(1, N + 1)]
ax2.bar(range(1, N + 1), dist, color=BLUE)
ax2.axvline(sum(k * p for k, p in zip(range(1, N + 1), dist)) / 100, color=VERMILION,
            linestyle="--", linewidth=1.5, label="mean 5.25")
ax2.bar([8], [dist[-1]], color=VERMILION)
ax2.text(8, dist[-1] + 1.2, f"{dist[-1]:.2f}%", ha="center", fontsize=9, color=VERMILION)
ax2.set_xlabel("distinct shop types present")
ax2.set_ylabel("share of games")
ax2.set_title("The eight-shop town today becomes 1 game in 416")
ax2.legend(loc="upper left", fontsize=9)
plt.tight_layout()
plt.show()


TURNS_PER_DAY, SHOP_TICK = 24, 4
shop_ticks_per_day = TURNS_PER_DAY // SHOP_TICK          # unchanged by the PR
yarn_per_day = shop_ticks_per_day * 2                    # single-product shops eat 2x

old = yarn_per_day + (TURNS_PER_DAY // 12) * 4           # town centre: 4x after day 20
new_with = yarn_per_day + (TURNS_PER_DAY // 24) * 1      # town centre: flat 1, every 24 turns
new_without = (TURNS_PER_DAY // 24) * 1
wool_cases = [("before the rebalance, always", old, "no longer reachable", GRAY),
              ("now, with a yarn store", new_with,
               f"{(1 - float(p_absent)) * 100:.0f}% of games", BLUE),
              ("now, with none", new_without,
               f"{float(p_absent) * 100:.1f}% of games", VERMILION)]
show(pd.DataFrame([{"late-season wool demand (day 25)": lbl,
                    "units/day": v, "how often": how} for lbl, v, how, _ in wool_cases]),
     f"One yarn store eats {yarn_per_day} wool/day; the town centre is all that is left "
     f"without one.")

fig, ax = plt.subplots(figsize=(7.4, 2.9))
ax.barh([c[0] for c in wool_cases][::-1], [c[1] for c in wool_cases][::-1],
        color=[c[3] for c in wool_cases][::-1], height=0.55)
for i, (lbl, v, how, _) in enumerate(wool_cases[::-1]):
    ax.text(v + 0.4, i, f"{v}/day   ({how})", va="center", fontsize=9)
ax.set_xlim(0, 27)
ax.set_xlabel("units of wool the town absorbs per day")
ax.set_title(f"A {(1 - new_without / old) * 100:.0f}% cut in wool demand, "
             f"in about one game in three")
plt.tight_layout()
plt.show()

# What a herd produces, and how much glut wool tolerates -- both from engine constants.
interval = K.ANIMALS["SHEEP"]["interval"]          # a sheep produces every `interval` days
per_sheep_per_day = (1 + interval) / interval      # CARE banks +1/day, paid at production
print(f"\none cared-for sheep produces {per_sheep_per_day:.2f} wool/day; six produce "
      f"{6 * per_sheep_per_day:.1f}/day")

i0 = K.MARKET_PARAMS["WOOL"]["I0"]
glut = 0
while K.market_price("WOOL", i0 + glut) > 1 and glut < 5000:
    glut += 1
print(f"wool hits the $1 floor {glut} units above its starting inventory of {i0:,}")


OLD_TOWN_CENTER_SCHEDULE = [(20, 4), (10, 2), (0, 1)]      # deleted by the rebalance
_ORIG_TOWN_CONSUME = K._town_consume


def _old_town_consume(env, state, step):
    obs0 = state[0].observation
    market, town, cfg = obs0.market, obs0.town, env.configuration
    shop_interval = max(1, int(K.get(cfg, "townShopSellInterval", 4)))
    centre_interval = max(1, int(K.get(cfg, "townCenterSellInterval", 12)))   # 1.32.6: 24
    day = step // max(1, int(K.get(cfg, "turnsPerDay", 24)))
    if step % shop_interval == 0:
        for shop_name in town.get("unlocked_shops", []):
            products = K.SHOPS[shop_name]
            for item in products:
                market["inventory"][item] -= 2 if len(products) == 1 else 1
    if step % centre_interval == 0:
        mult = next(m for threshold, m in OLD_TOWN_CENTER_SCHEDULE if day >= threshold)
        for item in K.TOWN_CENTER_PRODUCTS:
            market["inventory"][item] -= mult                                # 1.32.6: flat 1
    K._refresh_prices(market)


def _old_end_of_day(state, env, day, schedule=None):
    obs0, cfg = state[0].observation, env.configuration
    board_size = int(K.get(cfg, "boardSize", 10))
    turns_per_day = max(1, int(K.get(cfg, "turnsPerDay", 24)))
    weed_chance = float(K.get(cfg, "weedSpawnChance", 0.005))
    shed_cap = int(K.get(cfg, "shedCapacity", 100))
    unlock_interval = max(1, int(K.get(cfg, "townShopUnlockInterval", 3)))
    rng = random.Random((env.info.get("seed", 0) * 1_000_003) ^ day)
    for pid, farm in enumerate(obs0.farms):
        private = state[pid].observation.private
        K._daily_refresh_plants(farm, day, turns_per_day)
        K._daily_refresh_animals(farm, day)
        K._spawn_weeds(farm, board_size, weed_chance, rng)
        K._drop_inventories_to_shed(private, shed_cap)
        farm["farmer"] = list(K._default_spawn(board_size))
        farm["hands"], farm["hires_today"] = [], 0
        private["inventories"] = [{}]
    town = obs0.town
    if (day + 1) % unlock_interval == 0:
        remaining = [s for s in K.SHOPS if s not in town["unlocked_shops"]]   # no replacement
        if remaining:
            k = len(town["unlocked_shops"])
            drawn = rng.choice(sorted(remaining))
            town["unlocked_shops"].append(schedule[k] if schedule and k < len(schedule) else drawn)


@contextlib.contextmanager
def pre_rebalance(schedule=None):
    K._end_of_day = lambda s, e, d: _old_end_of_day(s, e, d, schedule)
    K._town_consume = _old_town_consume
    try:
        yield
    finally:
        K._end_of_day, K._town_consume = _ORIGINAL_END_OF_DAY, _ORIG_TOWN_CONSUME


rng = random.Random(1)
old_schedules = []
for _ in range(12):
    s = SHOP_TYPES[:]
    rng.shuffle(s)                                  # the old town always had all eight
    old_schedules.append(s)

old_banks = []
for sched in old_schedules:
    r = play([field_agent, "starter"], SEED, ctx=pre_rebalance(sched))
    assert r["shops"] == sched
    old_banks.append(r["p0"])

o_lo, o_hi, o_mid = min(old_banks), max(old_banks), st.median(old_banks)
show(pd.DataFrame([
        {"town rules": "1.32.6 (live)", "median": f"{mid:,.0f}",
         "worst": f"{lo:,.0f}", "best": f"{hi:,.0f}",
         "spread": f"{(hi - lo) / mid * 100:.1f}% of median"},
        {"town rules": "before the rebalance", "median": f"{o_mid:,.0f}",
         "worst": f"{o_lo:,.0f}", "best": f"{o_hi:,.0f}",
         "spread": f"{(o_hi - o_lo) / o_mid * 100:.1f}% of median"}]),
     f"The same agent and seed through twelve towns of each kind (n={len(old_banks)} each).")
print(f"the rebalance moved the town's share of the season from "
      f"{(o_hi - o_lo) / o_mid * 100:.1f}% to {(hi - lo) / mid * 100:.1f}% of the median,")
print(f"and the median season itself from {o_mid:,.0f} to {mid:,.0f} "
      f"({(mid / o_mid - 1) * 100:+.0f}%) as town demand was cut")


SEASON_DAYS, SHOP_TICK, UNLOCK_INTERVAL = 30, 4, 3


def shop_demand(active, item):
    n = 0
    for shop in active:
        products = K.SHOPS[shop]
        if item in products:
            n += 2 if len(products) == 1 else 1   # single-product shops eat double
    return n


def centre_demand(item, day, *, old_rules=False):
    if item not in K.TOWN_CENTER_PRODUCTS:
        return 0
    if not old_rules:
        return 1                                  # 1.32.6: flat, once a day
    return 4 if day >= 20 else (2 if day >= 10 else 1)      # what the rebalance removed


def run_market(item, schedule, per_day=0.0, first_day=0, *, old_rules=False):
    """Sell `per_day` units a day from `first_day`, spread evenly across the day.

    Returns (season revenue, final inventory). With per_day=0 this is the town alone.
    """
    inv = K.MARKET_PARAMS[item]["I0"]
    centre_interval = 12 if old_rules else 24
    revenue, carry = 0.0, 0.0
    for step in range(SEASON_DAYS * 24):
        day = step // 24
        if per_day and day >= first_day:
            carry += per_day / 24
            while carry >= 1:                     # orders fill before the town consumes
                price = K.market_price(item, inv)
                revenue += price
                if price > 1:                     # the floor is sticky: no inventory added
                    inv += 1
                carry -= 1
        active = schedule[:min(len(schedule), day // UNLOCK_INTERVAL)]
        if step % SHOP_TICK == 0:
            inv -= shop_demand(active, item)
        if step % centre_interval == 0:
            inv -= centre_demand(item, day, old_rules=old_rules)
    return revenue, inv


for check_seed in (0, 3, 11):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": check_seed})
    env.run(["pass", "pass"])
    obs = env.steps[-1][0]["observation"]
    sched, real = list(obs["town"]["unlocked_shops"]), obs["market"]["inventory"]
    for item in K.PRODUCTS:
        assert run_market(item, sched)[1] == real[item], (check_seed, item)
    print(f"seed {check_seed}: model reproduces the engine's final inventory "
          f"for all {len(K.PRODUCTS)} products")


HERD, PLACED_DAY = 6, 1
herds = {}
for animal, spec in K.ANIMALS.items():
    interval = spec["interval"]
    per_animal = min(spec["max_held"], 1 + interval) / interval   # CARE banks +1/day
    herds[animal] = {
        "product": spec["product"],
        "per_day": HERD * per_animal,
        "first_day": PLACED_DAY + spec["first_yield_day"],
    }
    print(f"{HERD} {animal.lower()}: {herds[animal]['per_day']:>4.1f} "
          f"{spec['product'].lower()}/day from day {herds[animal]['first_day']}")

rng = random.Random(0)
perms = []
for _ in range(200):
    s = SHOP_TYPES[:]
    rng.shuffle(s)
    perms.append(s)
rng = random.Random(1)
baskets = [[rng.choice(SHOP_TYPES) for _ in range(8)] for _ in range(500)]

before, live = {}, {}
for animal, h in herds.items():
    before[animal] = [run_market(h["product"], s, h["per_day"], h["first_day"],
                                 old_rules=True)[0] for s in perms]
    live[animal] = [run_market(h["product"], b, h["per_day"], h["first_day"])[0]
                    for b in baskets]

winner = Counter(max(live, key=lambda x: live[x][i]) for i in range(len(baskets)))
show(pd.DataFrame([
        {"herd (6 animals)": a.lower(), "product": herds[a]["product"].lower(),
         "before the rebalance": f"{st.median(before[a]):,.0f}",
         "live 1.32.6 median": f"{st.median(live[a]):,.0f}",
         "live, worst 10%": f"{sorted(live[a])[len(live[a]) // 10]:,.0f}",
         "ranks first": f"{winner[a] / len(baskets) * 100:.1f}% of towns"}
        for a in herds]),
     f"Season revenue from the herd's product, over {len(baskets)} drawn towns. "
     f"The ranking is among these three herds only.")

with_yarn = [v for b, v in zip(baskets, live["SHEEP"]) if "YARN_STORE" in b]
without = [v for b, v in zip(baskets, live["SHEEP"]) if "YARN_STORE" not in b]
lost = (1 - st.median(without) / st.median(with_yarn)) * 100
print(f"sheep herd, with a yarn store : median ${st.median(with_yarn):>9,.0f}"
      f"  (n={len(with_yarn)})")
print(f"sheep herd, no yarn store     : median ${st.median(without):>9,.0f}"
      f"  (n={len(without)})   -> {lost:.0f}% of the season gone")


fig, ax = plt.subplots(figsize=(9.5, 4.4))
styles = {"GOOSE": (GRAY, ":"), "COW": (BLUE, "-"), "SHEEP": (VERMILION, "--")}
for animal, vals in live.items():
    colour, dash = styles[animal]
    ax.hist(vals, bins=40, histtype="step", linewidth=2, linestyle=dash, color=colour,
            label=f"6 {animal.lower()} ({herds[animal]['product'].lower()})")
    ax.axvline(st.median(vals), color=colour, linestyle=dash, linewidth=1, alpha=0.5)
ax.set_xlabel("season revenue from the herd's product, over 500 drawn towns")
ax.set_ylabel("towns")
ax.set_title("After the modelled balance change, the town picks your herd for you")
ax.legend()
plt.tight_layout()
plt.show()


SHED_TILE = (4, 4)
PASTURE_SITES = [(3, 4), (4, 3), (3, 3), (2, 4), (4, 2), (2, 3)]
TARGET_HERD = len(PASTURE_SITES)
RANCH_HANDS = 4
RANCH_SELL = {"WOOL": 3, "FERTILIZER": 4}
CASH_FLOOR = 400                      # keep enough for feed before buying another sheep


def _animals(farm):
    out = []
    for x, y in PASTURE_SITES:
        t = farm["tiles"][y][x]
        if isinstance(t, dict) and t.get("animal"):
            out.append(((x, y), t))
    return out


def _empty_pastures(farm):
    return [(x, y) for x, y in PASTURE_SITES
            if isinstance(farm["tiles"][y][x], dict)
            and farm["tiles"][y][x].get("kind") == "PASTURE"
            and not farm["tiles"][y][x].get("animal")]


def _nearest(pos, options):
    return min(options, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))


def ranch_agent(obs):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    invs = private.get("inventories", []) or [{}]
    hour, money = obs.get("hour", 0), farm["money"]
    units = [tuple(farm["farmer"])] + [tuple(h) for h in farm.get("hands", [])]
    n_hands = len(farm.get("hands", []))
    inv_of = [invs[i] if i < len(invs) else {} for i in range(len(units))]

    animals = _animals(farm)
    empty_pastures = _empty_pastures(farm)
    bare = [(x, y) for x, y in PASTURE_SITES if farm["tiles"][y][x] is None]
    carried = sum(i.get("SHEEP", 0) for i in inv_of)
    herd = len(animals) + carried + shed.get("SHEEP", 0)

    market = []
    if hour == 0:
        market += [["HIRE"]] * max(0, RANCH_HANDS - farm.get("hires_today", 0))
    for product, batch in RANCH_SELL.items():
        if shed.get(product, 0) > 0:
            market.append(["SELL", product, min(batch, shed[product])])
    want = max(0, TARGET_HERD + 2 - shed.get("WHEAT", 0))   # unfed twice and it is gone
    if want > 0 and money >= 200:
        market.append(["BUY_PRODUCT", "WHEAT", min(want, 6)])
    if herd < TARGET_HERD and money >= 500 + CASH_FLOOR:
        market.append(["BUY_ANIMAL", "SHEEP", 1])
    market = market[:10]

    unfed = [p for p, t in animals if not t["fed_today"]]
    actions, claimed = [], set()
    for i, pos in enumerate(units):
        inv, (x, y) = inv_of[i], pos
        tile = farm["tiles"][y][x]
        act = None

        if inv.get("SHEEP", 0) > 0:                 # a carried sheep earns nothing
            if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal"):
                act = ["PLACE", "SHEEP"]
            elif empty_pastures:
                free = [p for p in empty_pastures if p not in claimed] or empty_pastures
                target = _nearest(pos, free)
                claimed.add(target)
                move = _step_towards(pos, target)
                act = [move] if move else ["PASS"]

        if act is None and isinstance(tile, dict) and tile.get("animal"):
            if not tile["fed_today"] and inv.get("WHEAT", 0) > 0:
                act = ["FEED"]
            elif tile["yield_units"] > 0:
                act = ["HARVEST"]
            elif tile["fed_today"] and not tile["cared_today"]:
                act = ["CARE"]
            elif tile.get("fertilizer_available"):
                act = ["COLLECT_FERTILIZER"]
        if act is None and tile is None and (x, y) in PASTURE_SITES and bare:
            act = ["BUILD_PASTURE"]
        if act is None and pos == SHED_TILE:
            if shed.get("SHEEP", 0) > 0 and len(animals) + carried < TARGET_HERD:
                act = ["PICKUP", "SHEEP", 1]
            elif inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0 and unfed:
                act = ["PICKUP", "WHEAT", 3]

        if act is None:
            fetching = shed.get("SHEEP", 0) > 0 and len(animals) + carried < TARGET_HERD
            if fetching or (unfed and inv.get("WHEAT", 0) == 0):
                target = SHED_TILE
            else:
                todo = [p for p in unfed if p not in claimed and inv.get("WHEAT", 0) > 0]
                todo += [p for p, t in animals if p not in claimed and (
                    t["yield_units"] > 0 or not t["cared_today"] or t.get("fertilizer_available"))]
                todo += [p for p in bare if p not in claimed]
                target = _nearest(pos, todo) if todo else SHED_TILE
                if todo:
                    claimed.add(target)
            move = _step_towards(pos, target)
            act = [move] if move else ["PASS"]
        actions.append(act)

    return {"farmer": actions[0], "hands": actions[1:1 + n_hands], "market": market}


demo_ranch = play([ranch_agent, "pass"], seed=SEED)
print(f"the ranch banks {demo_ranch['p0']:,.0f} against a passing opponent on seed {SEED}")


NO_YARN = [s for s in SHOP_TYPES if s != "YARN_STORE"]
rng = random.Random(20260808)


def draw_basket(want_yarn):
    b = [rng.choice(NO_YARN) for _ in range(8)]
    if want_yarn:
        b[0] = "YARN_STORE"
        rng.shuffle(b)
    return b


played = {}
for label, want_yarn in (("no yarn store", False), ("one yarn store", True)):
    banks = []
    for _ in range(8):
        basket = draw_basket(want_yarn)
        r = play([ranch_agent, "pass"], SEED, ctx=pinned_shops(basket))
        assert r["shops"] == basket
        assert ("YARN_STORE" in basket) == want_yarn
        banks.append(r["p0"])
    played[label] = banks

played_gap = st.median(played["one yarn store"]) - st.median(played["no yarn store"])
model_gap = st.median(with_yarn) - st.median(without)
show(pd.DataFrame([
        {"town": label, "episodes": len(b), "worst": f"{min(b):,.0f}",
         "median final bank": f"{st.median(b):,.0f}", "best": f"{max(b):,.0f}"}
        for label, b in played.items()]),
     "A six-sheep ranch played in the live 1.32.6 engine, seed 7.")
show(pd.DataFrame([
        {"quantity": "gap the Section 7 market model predicts (wool revenue)",
         "value": f"{model_gap:,.0f}"},
        {"quantity": "gap the engine actually produced (final bank)",
         "value": f"{played_gap:,.0f}"},
        {"quantity": "difference between them",
         "value": f"{abs(played_gap - model_gap) / model_gap * 100:.1f}%"}]),
     "The levels are not comparable; the gap is, and it is what the model claims.")


mirror = {}
for label, want_yarn in (("no yarn store", False), ("one yarn store", True)):
    banks, prices = [], []
    for _ in range(8):
        basket = draw_basket(want_yarn)
        r = play([ranch_agent, ranch_agent], SEED, ctx=pinned_shops(basket))
        assert r["shops"] == basket
        banks.append(r["p0"])
        prices.append(r["prices"]["WOOL"])
    mirror[label] = banks
    print(f"{label:>16}: closing wool price {st.median(prices):>4.0f}")

mirror_gap = st.median(mirror["one yarn store"]) - st.median(mirror["no yarn store"])


def arm(name, banks):
    lo_, hi_ = st.median(banks["no yarn store"]), st.median(banks["one yarn store"])
    return {"the opponent": name,
            "no yarn store": f"{lo_:,.0f}", "one yarn store": f"{hi_:,.0f}",
            "gap": f"{hi_ - lo_:,.0f}", "ratio": f"{hi_ / lo_:.2f}x"}


show(pd.DataFrame([arm("sells nothing", played),
                   arm("runs the same wool ranch", mirror)]),
     "The same sixteen towns and the same ranch. Only the opponent changes.")
print(f"the absolute gap shrinks {played_gap / mirror_gap:.1f}x once someone else sells wool;")
print("the ratio between the two towns holds up far better")


fig, ax = plt.subplots(figsize=(8.4, 3.2))
for row, (label, colour) in enumerate([("no yarn store", VERMILION),
                                       ("one yarn store", BLUE)]):
    banks = played[label]
    ax.scatter(banks, [row] * len(banks), s=64, color=colour, alpha=0.65,
               edgecolor="white", linewidth=0.8, zorder=3)
    med = st.median(banks)
    ax.plot([med, med], [row - 0.22, row + 0.22], color=colour, linewidth=2.5, zorder=4)
    ax.text(med, row + 0.3, f"median {med:,.0f}", ha="center", fontsize=9, color=colour)
ax.annotate("", xy=(st.median(played["one yarn store"]), -0.42),
            xytext=(st.median(played["no yarn store"]), -0.42),
            arrowprops=dict(arrowstyle="<->", color="0.45", lw=1.2))
ax.text((st.median(played["one yarn store"]) + st.median(played["no yarn store"])) / 2,
        -0.56, f"{played_gap:,.0f}  (model predicted {model_gap:,.0f})",
        ha="center", va="top", fontsize=9.5, color="0.35")
ax.set_yticks([0, 1])
ax.set_yticklabels(["no yarn store\n(34.4% of games)", "one yarn store"], fontsize=9.5)
ax.set_ylim(-0.95, 1.6)
ax.set_xlabel("final bank after a 30-day season")
ax.set_title("One missing building, measured in the engine rather than on paper")
plt.tight_layout()
plt.show()


_orig_spawn, _orig_end = K._spawn_weeds, K._end_of_day


def instrumented_episode(seed, agents):
    """Play an episode, recording the true draw offset and the next morning's empty tiles."""
    offsets, mornings, counter = {}, {}, {"n": 0}

    def counting_spawn(farm, board_size, weed_chance, rng):
        class Wrapped:
            def random(self_inner):
                counter["n"] += 1
                return rng.random()
        return _orig_spawn(farm, board_size, weed_chance, Wrapped())

    def end_of_day(state, env, day):
        counter["n"] = 0
        K._spawn_weeds = counting_spawn
        try:
            _orig_end(state, env, day)
        finally:
            K._spawn_weeds = _orig_spawn
        offsets[day] = counter["n"]

    def watch(policy):
        def wrapped(obs):
            if obs.get("hour") == 0:                     # both farms are public
                mornings[obs["day"]] = sum(
                    1 for farm in obs["farms"] for row in farm["tiles"]
                    for tile in row if tile is None)
            return policy(obs)
        return wrapped

    K._end_of_day = end_of_day
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([watch(agents[0]), agents[1]])
        drawn = list(env.steps[-1][0]["observation"]["town"]["unlocked_shops"])
    finally:
        K._end_of_day = _orig_end
    unlock_days = [d for d in sorted(offsets) if (d + 1) % 3 == 0][: len(drawn)]
    return unlock_days, drawn, offsets, mornings


rows, exact, near = [], 0, 0
for s, pair in [(20260808, (field_agent, "starter")), (7, (field_agent, "starter")),
                (4242, (field_agent, "starter")), (11, (ranch_agent, "pass")),
                (99, (ranch_agent, ranch_agent))]:
    ud, drawn, offs, morns = instrumented_episode(s, pair)
    diffs = [offs[d] - morns[d + 1] for d in ud if (d + 1) in morns]
    exact += sum(1 for x in diffs if x == 0)
    near += sum(1 for x in diffs if x != 0)
    rows.append({"seed": s, "unlock days": len(diffs),
                 "true offset minus next-morning empty tiles": str(diffs)})
show(pd.DataFrame(rows),
     "The draw offset against what the observation shows the following morning.")
print(f"exact on {exact}/{exact + near} unlock days; the rest are off by one, which is a "
      f"weed that happened to spawn that evening")


SPACE = 2 ** 31
unlock_days, drawn, offs, _ = instrumented_episode(20260808, (field_agent, "starter"))
sample = [random.Random(i).randrange(SPACE) for i in range(400_000)]


def shop_for(seed, day, n_draws):
    rng = random.Random((seed * 1_000_003) ^ day)
    for _ in range(n_draws):
        rng.random()
    return rng.choice(SHOP_TYPES)


collapse, survivors = [], sample
for k, d in enumerate(unlock_days, start=1):
    survivors = [s for s in survivors if shop_for(s, d, offs[d]) == drawn[k - 1]]
    if not survivors:
        break
    collapse.append({"by day": d + 1, "unlocks seen": k,
                     "sample survivors": f"{len(survivors):,} of {len(sample):,}",
                     "implied candidates in 2**31":
                         f"{SPACE * len(survivors) / len(sample):,.0f}"})
show(pd.DataFrame(collapse), "How fast the seed space collapses once the offsets are known.")


TRIALS = 30_000
t0 = time.perf_counter()
for s in sample[:TRIALS]:
    shop_for(s, unlock_days[0], offs[unlock_days[0]])
rate = TRIALS / (time.perf_counter() - t0)
show(pd.DataFrame([
        {"implementation": "pure Python, one core (measured here)",
         "seeds/second": f"{rate:,.0f}",
         "one pass over 2**31": f"{SPACE / rate / 3600:.1f} hours"},
        {"implementation": "300x faster (vectorised or compiled)",
         "seeds/second": f"{rate * 300:,.0f}",
         "one pass over 2**31": f"{SPACE / (rate * 300):.0f} seconds"},
        {"implementation": "3000x faster",
         "seeds/second": f"{rate * 3000:,.0f}",
         "one pass over 2**31": f"{SPACE / (rate * 3000):.0f} seconds"}]),
     "A 720-turn game gives an agent roughly 720 seconds of its own compute.")
print("only the first pass costs this; later unlocks re-test survivors only")
print(f"pure Python covers {720 * rate / SPACE * 100:.1f}% of the space in a whole game")
