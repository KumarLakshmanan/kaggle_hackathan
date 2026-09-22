# Works on Kaggle with Internet on. The engine is PINNED rather than left floating, because the
# package and the competition ladder move on their own schedules and a floating pin once broke this
# page outright: an upstream release dropped a constant the notebook imports, mid-run. 1.32.7 is
# what the ladder scored on from 2026-08-15 onward, checked again on 2026-09-15. Check it yourself
# before you trust any number here: open any episode in the daily replay dataset and read
# module_version. This matters more than it sounds: a Kaggle image ships an older engine by default
# (1.29.3 at the time of writing), and that one will not sell you fertilizer at all.
LADDER_ENGINE = "1.32.7"
import contextlib, glob, io, os, subprocess, sys
from importlib import metadata

def _pinned():
    try:  # checked without importing, so the install below actually takes effect
        return metadata.version("kaggle-environments") == LADDER_ENGINE
    except Exception:
        return False

if not _pinned():
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--progress-bar", "off",
                        f"kaggle-environments=={LADDER_ENGINE}"], check=True, capture_output=True)
    except Exception as e:
        raise RuntimeError(f"This guide pins kaggle-environments {LADDER_ENGINE} to match the "
                           "ladder — turn Internet ON in the notebook settings and rerun.") from e

import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import logging
logging.disable(logging.INFO)  # other bundled envs log noise on import; mute it
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import kaggle_environments
    from kaggle_environments import make
logging.disable(logging.NOTSET)
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    CROPS, ANIMALS, MARKET_PARAMS, MARKET_I0, SHOPS, LAND_ORDER, LAND_PRICES,
    PRODUCTS, market_price,
)

plt.rcParams.update({
    "figure.dpi": 90, "savefig.dpi": 90, "font.size": 11, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.grid": True, "grid.alpha": 0.25,
})

# Colorblind-safe palette (validated: CVD ΔE and lightness checks pass)
CROP_C = {"WHEAT": "#C99700", "CARROT": "#B84A00", "TOMATO": "#9E2B72",
          "STRAWBERRY": "#DB6FA9", "MELON": "#00795F"}
PROD_C = {**CROP_C, "EGG": "#56A8D8", "MILK": "#0059A1", "WOOL": "#A8641A",
          "FERTILIZER": "#6B4F9E"}
P0, P1 = "#0072B2", "#D55E00"          # our bot / opponent
# Surface tones lifted from the visualizer that ships with the environment, so the
# farms here look like the farms in the official replay player.
SOIL, TILLED, WILD = "#efe7ce", "#e8d2a6", "#c2caa4"
WOOD, WOOD_DARK, INK = "#8b6f44", "#3a2412", "#3c3b37"
BASE = {p: MARKET_PARAMS[p]["base"] for p in PRODUCTS}

def one_shot_units(crop):
    # Watering during the bonus window adds +1/day (+2 if fertilized), capped at max_yield.
    c = CROPS[crop]
    window = range((c["max_yield_day"] + 1) // 2, c["max_yield_day"] + 1)
    return min(c["max_yield"], 1 + len(list(window)))

def one_shot_days(crop):
    # The tile is free once the plant is BOTH harvestable and done growing. Watering adds +1/day
    # from a base of 1, starting at the window, so the cap can bind before max_yield_day: a melon
    # is finished on day 10, not 12. Wheat and carrot never reach their cap, so nothing changes.
    c = CROPS[crop]
    cap_day = (c["max_yield_day"] + 1) // 2 + c["max_yield"] - 2
    return max(c["first_yield_day"], min(cap_day, c["max_yield_day"]))

def ongoing_days(crop):
    # The days a fruit can be picked up. _daily_refresh_plants runs with next_day = day + 1, so the
    # unit that forms overnight is in your hands on the morning of first_yield_day, then every
    # `interval` days after that, max_yield times.
    c = CROPS[crop]
    return [c["first_yield_day"] + k * c["interval"] for k in range(c["max_yield"])]

def crop_econ():
    # Profit per tile-day at base prices, daily watering, no fertilizer.
    rows = []
    for crop, c in CROPS.items():
        if c["ongoing"]:
            days = ongoing_days(crop)
            units, occupied = c["max_yield"], days[-1]       # DIG frees the tile the same day
        else:
            units, occupied = one_shot_units(crop), one_shot_days(crop)
        revenue = units * BASE[crop]
        profit = revenue - c["seed"]
        rows.append({"crop": crop, "seed $": c["seed"], "tile-days": occupied, "units": units,
                     "base price": BASE[crop], "revenue $": revenue, "profit $": profit,
                     "profit / tile-day": round(profit / occupied, 1)})
    return pd.DataFrame(rows).sort_values("profit / tile-day", ascending=False).reset_index(drop=True)

def draw_farm(ax, farm, title=""):
    # One farm, drawn in the environment's own colours; tiles[y][x] with row 0 on top.
    from matplotlib.patches import FancyBboxPatch

    def tile(x, y, fc, ec="white", lw=1.0, alpha=1.0):
        ax.add_patch(FancyBboxPatch((x + .07, n - 1 - y + .07), .86, .86,
                                    boxstyle="round,pad=0,rounding_size=0.16",
                                    fc=fc, ec=ec, lw=lw, alpha=alpha))

    n = len(farm["tiles"])
    ax.add_patch(plt.Rectangle((-.15, -.15), n + .3, n + .3, fc=SOIL, ec="none", zorder=0))
    for y in range(n):
        for x in range(n):
            t = farm["tiles"][y][x]
            if t == "LOCKED":                       # wild land, not bought yet
                tile(x, y, WILD, ec="#b3bd94", lw=.8)
                continue
            tile(x, y, TILLED, ec=SOIL, lw=.8)      # ground you own and work
            if not isinstance(t, dict):
                continue
            k = t.get("kind")
            if k == "PLANT":
                ripe = t.get("yield_units", 0) > 0
                tile(x, y, CROP_C[t["crop"]], alpha=1.0 if ripe else .45)
                if ripe:                            # a dot means there is something to harvest
                    ax.plot(x + .5, n - 1 - y + .5, "o", ms=3.4, mfc="white", mec="none", zorder=6)
            elif k == "WEED":
                tile(x, y, "#6E7351", alpha=.55)
            elif "animal" in t:
                tile(x, y, PROD_C[ANIMALS[t["animal"]]["product"]])
            elif k in ("COOP", "PASTURE"):
                tile(x, y, WOOD, alpha=.5)
    ax.plot([n/2, n/2], [0, n], color=WOOD_DARK, lw=2.4, alpha=.85, zorder=4)
    ax.plot([0, n], [n/2, n/2], color=WOOD_DARK, lw=2.4, alpha=.85, zorder=4)
    ax.add_patch(FancyBboxPatch((n/2 - .62, n/2 - .62), 1.24, 1.24,
                                boxstyle="round,pad=0,rounding_size=0.18",
                                fc=WOOD_DARK, ec=SOIL, lw=1.6, zorder=5))
    ax.text(n/2, n/2, "shed", ha="center", va="center", fontsize=6.5, color=SOIL, zorder=6)
    fx, fy = farm["farmer"]
    ax.plot(fx + .5, n - 1 - fy + .5, "o", ms=8.5, mfc=P0, mec="white", mew=1.4, zorder=7)
    for hx, hy in farm.get("hands", []):
        ax.plot(hx + .5, n - 1 - hy + .5, "o", ms=5.5, mfc=P0, mec="white", mew=1.1, zorder=7)
    ax.set_xlim(-.2, n + .2); ax.set_ylim(-.2, n + .2)
    ax.set_aspect("equal"); ax.axis("off"); ax.grid(False)
    if title:
        ax.set_title(title, fontsize=11, color=INK)


def day_frames(steps):
    # Index of the last turn of every in-game day, so one frame is one day.
    days = sorted({s[0]["observation"]["day"] for s in steps})
    return days, [max(i for i, s in enumerate(steps) if s[0]["observation"]["day"] == d)
                  for d in days]


def season_gif(steps, out="season.gif", fps=5):
    # One frame per in-game day: the farm on the left, the money race on the right.
    from matplotlib.animation import FuncAnimation, PillowWriter
    days, last = day_frames(steps)
    money = [[s[0]["observation"]["farms"][p]["money"] for s in steps] for p in (0, 1)]
    top = max(max(money[0]), max(money[1])) * 1.08

    fig, (axF, axM) = plt.subplots(1, 2, figsize=(7.8, 3.6),
                                   gridspec_kw={"width_ratios": [1.05, 1.05]})
    def frame(i):
        k = last[i]
        axF.clear(); axM.clear()
        draw_farm(axF, steps[k][0]["observation"]["farms"][0])
        axF.set_title(f"Day {days[i]} of {days[-1]}", fontsize=11.5, color=INK, weight="bold")
        axM.plot(money[0][:k + 1], color=P0, lw=2.4, label="Carrot Crew")
        axM.plot(money[1][:k + 1], color=P1, lw=2.4, label="built-in starter")
        axM.set_xlim(0, len(steps)); axM.set_ylim(0, top)
        axM.set_title("Coins in the bank", fontsize=11.5, color=INK, weight="bold")
        axM.set_xlabel("turn", fontsize=9)
        axM.legend(fontsize=8.5, frameon=False, loc="upper left")

    FuncAnimation(fig, frame, frames=len(last)).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)
    return out


import glob, os, functools

DATA_DIRS = ["/kaggle/input/kaggriculture-episodes", *glob.glob("/kaggle/input/*"),
             "episodes", "../episodes"]

def data_file(name):
    # The attached dataset on Kaggle, a differently-named copy of it, or a local checkout.
    for d in DATA_DIRS:
        if os.path.exists(f"{d}/{name}"):
            return f"{d}/{name}"
    raise FileNotFoundError(
        f"{name} not found. Attach the dataset: Add Input -> Datasets -> search "
        "'kaggriculture-episodes' (georgymamarin/kaggriculture-episodes)."
    )

def data_files(pattern):
    # Replays no longer live in one file. The corpus passed ten gigabytes, so it ships as
    # monthly shards (replays_2026-08.parquet, replays_2026-08b.parquet, ...). This glob
    # matches both layouts, which is why nothing here names a replay file directly.
    for d in DATA_DIRS:
        hits = sorted(glob.glob(f"{d}/{pattern}"))
        if hits:
            return hits
    raise FileNotFoundError(
        f"no {pattern} found. Attach the dataset: Add Input -> Datasets -> search "
        "'kaggriculture-episodes' (georgymamarin/kaggriculture-episodes)."
    )

@functools.lru_cache(maxsize=None)
def load_table(stem):
    for ext, reader in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
        try:
            return reader(data_file(f"{stem}{ext}"))
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"no {stem}.csv or {stem}.parquet in the attached dataset")

@functools.lru_cache(maxsize=None)
def episodes_with_replays():
    # Which games the dataset says it holds a replay for. Reading one column of the features
    # CSV costs a second; opening seventeen gigabytes of parquet to ask the same question
    # costs a minute and a half, which is a bad thing to put in the first cell of a page.
    try:
        return set(pd.read_csv(data_file("episode_features.csv"), usecols=["episode_id"]).episode_id)
    except FileNotFoundError:
        ids = set()
        for path in data_files("replays*.parquet"):
            ids |= set(pd.read_parquet(path, columns=["episode_id"]).episode_id)
        return ids

def load_replay(episode_id, when=None):
    # One row group holds twenty replays and decompresses to a few hundred megabytes, so
    # read_parquet(filters=...) pulls all twenty in to hand back one and killed this kernel
    # once the corpus passed a gigabyte. Scanning with batch_size=1 keeps one replay in memory.
    # Shards are named by the month they cover (plus a small "b" shard for games that arrived
    # late), so knowing when the game ended narrows the search to one file.
    import json, gc
    import pyarrow.dataset as pads
    shards = data_files("replays*.parquet")
    if when is not None:
        tag = pd.Timestamp(when).strftime("%Y-%m")
        shards = [p for p in shards if tag in os.path.basename(p)] or shards
    for path in shards:
        scanner = pads.dataset(path, format="parquet").scanner(
            filter=pads.field("episode_id") == int(episode_id),
            columns=["replay_json"], batch_size=1)
        hit = scanner.head(1)
        if hit.num_rows:
            blob = hit.column("replay_json")[0].as_py()
            del scanner, hit; gc.collect()
            steps = json.loads(blob)["steps"]
            del blob; gc.collect()
            return steps
        del scanner, hit
    raise KeyError(f"episode {episode_id} has no replay in the attached dataset")

@functools.lru_cache(maxsize=None)
def biggest_ladder_game():
    # The richest finished ladder game we hold a replay for. Both animations below show this
    # same game, and which game that is changes as the dataset grows: the cells print it.
    ladder = load_table("episodes")
    ladder = ladder[ladder["type"].eq("EPISODE_TYPE_PUBLIC")
                    & ladder["state"].eq("COMPLETED")].copy()
    ladder["top"] = ladder[["bank_0", "bank_1"]].max(axis=1)
    ladder = ladder[ladder.episode_id.isin(episodes_with_replays()) & ladder.top.gt(0)]
    ladder = ladder.sort_values("top", ascending=False)
    if ladder.empty:
        raise FileNotFoundError("no finished ladder game with a replay in the attached dataset")
    # The features table is a cheap filter, not a guarantee: coverage of the newest games runs
    # a little behind, so it can list a game whose replay has not landed in a shard yet. Walk
    # down from the richest until one actually opens; on a healthy dataset that is the first try.
    for _, row in ladder.head(50).iterrows():
        try:
            steps = load_replay(row.episode_id, when=row.end_time)
        except KeyError:
            continue
        return row, (0 if row.bank_0 >= row.bank_1 else 1), steps
    raise FileNotFoundError("none of the richest ladder games has a replay in the attached dataset")


def hero_gif(out="hero.gif", fps=5):
    # A real ladder season: the farm fills up while the town's appetite lifts prices.
    from matplotlib.animation import FuncAnimation, PillowWriter

    row, seat, steps = biggest_ladder_game()

    days, last = day_frames(steps)
    watch = ["MILK", "STRAWBERRY", "MELON", "WHEAT"]
    series = {p: [steps[k][0]["observation"]["market"]["prices"][p] for k in last] for p in watch}
    ceiling = max(max(v) for v in series.values()) * 1.12

    fig = plt.figure(figsize=(8.0, 3.7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.22], left=.02, right=.9, top=.8, bottom=.14,
                          wspace=.12)
    axF, axP = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    def frame(i):
        axF.clear(); axP.clear()
        farm = steps[last[i]][0]["observation"]["farms"][seat]
        draw_farm(axF, farm)
        axF.set_title(f"Day {days[i]}   ${farm['money']:,.0f}", fontsize=12, color=INK, weight="bold")
        spread = sorted(watch, key=lambda p: -series[p][i])
        placed = None
        for prod in spread:
            axP.plot(days[:i + 1], series[prod][:i + 1], lw=2.6, color=PROD_C[prod])
            y = series[prod][i]
            if placed is not None and y > placed - ceiling * .07:
                y = placed - ceiling * .07                          # stack labels, never overlap
            placed = y
            axP.text(days[i] + .6, y, f"{prod.title()} ${series[prod][i]}",
                     fontsize=8.5, color=PROD_C[prod], va="center", weight="bold")
        axP.set_xlim(0, days[-1] * 1.34); axP.set_ylim(0, ceiling)
        axP.set_title("What the town pays", fontsize=12, color=INK, weight="bold")
        axP.set_xlabel("day", fontsize=9)
        axP.tick_params(labelsize=8.5)

    FuncAnimation(fig, frame, frames=len(days)).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)

    stock = [steps[k][0]["observation"]["market"]["inventory"]["MELON"] for k in last]
    jump = max(range(1, len(stock)), key=lambda i: stock[i] - stock[i - 1])
    print(f"Biggest melon dump in this game: {stock[jump] - stock[jump - 1]} sold into the market "
          f"on day {days[jump]}, price ${series['MELON'][jump - 1]} -> ${series['MELON'][jump]}.")
    return out


def dump_gif(item="MELON", n=200, out="dump.gif", fps=10):
    # Sell one unit at a time into an untouched market and watch the price walk down.
    from matplotlib.animation import FuncAnimation, PillowWriter
    prices = [market_price(item, MARKET_I0 + k) for k in range(n)]
    earned = np.cumsum(prices)
    dream = np.arange(1, n + 1) * prices[0]          # if the price never moved
    shed = 100                                       # shedCapacity: one dump can be this big
    step = 5

    fig, (axP, axR) = plt.subplots(1, 2, figsize=(8.0, 3.4))
    def frame(f):
        k = min((f + 1) * step, n) - 1
        axP.clear(); axR.clear()
        axP.plot(range(n), prices, lw=2.6, color=CROP_C[item], alpha=.3)
        axP.plot(range(k + 1), prices[:k + 1], lw=3, color=CROP_C[item])
        axP.plot(k, prices[k], "o", ms=9, color=CROP_C[item], mec="white", mew=1.6)
        axP.text(.97, .92, f"unit {k + 1}: ${prices[k]}", transform=axP.transAxes, ha="right",
                 fontsize=12, weight="bold", color=CROP_C[item])
        axP.set_title(f"{item.title()} price while you sell", fontsize=11.5, color=INK)
        axP.set_xlabel("units sold in one go"); axP.set_ylabel("price $")
        axP.axvline(shed, color="#8A7F6B", lw=1.4, ls="--")
        axP.text(shed - 3, prices[0] * .12, "one shed ", fontsize=8.5, color="#8A7F6B", ha="right")
        axP.set_xlim(0, n); axP.set_ylim(0, prices[0] * 1.1)

        axR.plot(range(k + 1), dream[:k + 1], lw=2.4, ls="--", color="#8A7F6B")
        axR.plot(range(k + 1), earned[:k + 1], lw=3, color=CROP_C[item])
        axR.text(.04, .93, f"kept ${earned[k]:,.0f}", transform=axR.transAxes, fontsize=12,
                 weight="bold", color=CROP_C[item], va="top")
        axR.text(.04, .78, f"hoped ${dream[k]:,.0f}", transform=axR.transAxes, fontsize=11,
                 color="#8A7F6B", va="top")
        axR.set_title("What the sale actually pays", fontsize=11.5, color=INK)
        axR.set_xlabel("units sold in one go"); axR.set_ylabel("coins so far")
        axR.axvline(shed, color="#8A7F6B", lw=1.4, ls="--")
        axR.set_xlim(0, n); axR.set_ylim(0, dream[-1] * 1.05)
        plt.tight_layout()

    FuncAnimation(fig, frame, frames=n // step).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)
    return out, {"shed": (int(earned[shed - 1]), int(dream[shed - 1])),
                 "all": (int(earned[-1]), int(dream[-1])), "last": prices[-1]}


def versus_gif(my_steps, out="versus.gif", fps=5):
    # Our farm next to the biggest ladder farm in the dataset, day for day.
    from matplotlib.animation import FuncAnimation, PillowWriter

    row, seat, their_steps = biggest_ladder_game()

    my_days, my_last = day_frames(my_steps)
    their_days, their_last = day_frames(their_steps)
    n = min(len(my_days), len(their_days))

    fig = plt.figure(figsize=(8.0, 4.7))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.1, 1], hspace=.3, wspace=.06,
                          left=.09, right=.97, top=.88, bottom=.14)
    axL, axR, axB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])

    def frame(i):
        axL.clear(); axR.clear(); axB.clear()
        mine = my_steps[my_last[i]][0]["observation"]["farms"][0]
        theirs = their_steps[their_last[i]][0]["observation"]["farms"][seat]
        draw_farm(axL, mine); draw_farm(axR, theirs)
        axL.set_title(f"Carrot Crew   ${mine['money']:,.0f}", fontsize=11, color=P0, weight="bold")
        axR.set_title(f"a ladder leader   ${theirs['money']:,.0f}", fontsize=11, color=INK,
                      weight="bold")
        scale = max(theirs["money"], mine["money"], 1) * 1.35
        axB.barh([1, 0], [mine["money"], theirs["money"]], color=[P0, "#8A7F6B"], height=.55)
        a, b = max(mine["money"], 1), max(theirs["money"], 1)
        lead = f"leader ×{b / a:.1f}" if b >= a else f"us ×{a / b:.1f}"
        axB.text(scale * .99, .5, lead,
                 ha="right", va="center", fontsize=12, weight="bold", color=INK)
        axB.set_yticks([1, 0], ["mine", "theirs"], fontsize=9)
        axB.set_xlim(0, scale); axB.set_xlabel("coins in the bank", fontsize=9)
        for sp in ("top", "right", "left"):
            axB.spines[sp].set_visible(False)
        fig.suptitle(f"Same rules, same day {my_days[i]} of {my_days[n - 1]}",
                     fontsize=12.5, color=INK, weight="bold", y=.97)

    FuncAnimation(fig, frame, frames=n).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)

    final = their_steps[-1][0]["observation"]["farms"][seat]
    beasts = sum(1 for r in final["tiles"] for t in r if isinstance(t, dict) and "animal" in t)
    print(f"Their farm ended on {len(final['unlocked_quadrants'])} of 4 quadrants "
          f"with {beasts} animals; ours on 1 quadrant with none.")
    return out


def timing_gif(item="CARROT", lot=60, out="timing.gif", fps=9):
    # The same basket, sold into markets in different states. Nothing here is simulated:
    # every price is market_price() at that inventory, and the lot is sold unit by unit.
    from matplotlib.animation import FuncAnimation, PillowWriter
    shorts = list(range(700, -301, -20))                 # short market -> glutted market
    first = [market_price(item, MARKET_I0 - s) for s in shorts]
    takes = [sum(market_price(item, MARKET_I0 - s + k) for k in range(lot)) for s in shorts]
    resting = takes[shorts.index(0)]
    curve_x = list(range(700, -301, -5))
    curve_y = [market_price(item, MARKET_I0 - s) for s in curve_x]
    top = max(curve_y) * 1.1

    fig, (axP, axT) = plt.subplots(1, 2, figsize=(8.4, 3.5),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    def frame(i):
        axP.clear(); axT.clear()
        axP.plot(curve_x, curve_y, lw=2.4, color=CROP_C[item], alpha=.30)
        upto = [x for x in curve_x if x >= shorts[i]]
        axP.plot(upto, curve_y[:len(upto)], lw=3, color=CROP_C[item])
        axP.plot(shorts[i], first[i], "o", ms=10, color=CROP_C[item], mec="white", mew=1.6)
        axP.axvline(0, color="#4A3F35", lw=1, ls=":")
        axP.text(-14, top * .60, "resting\nstock", fontsize=8, color="#4A3F35", ha="right")
        # A fixed corner, not a label chasing the marker: it can never collide with the curve.
        axP.text(.97, .92, f"next unit ${first[i]:,}", transform=axP.transAxes, ha="right",
                 fontsize=11, weight="bold", color=CROP_C[item])
        axP.set_xlim(720, -320); axP.set_ylim(0, top)
        axP.set_xlabel(f"units of {item.lower()} the town is SHORT", fontsize=9)
        axP.set_ylabel("price of the next unit, $", fontsize=9)
        axP.set_title(f"{item.title()}: what the market pays", fontsize=10.5, color=INK)

        # One coordinate system on the right, so nothing lands outside the panel.
        axT.barh([-.60], [takes[i]], height=.40, color=CROP_C[item])
        axT.axvline(resting, color="#4A3F35", lw=1.5, ls="--")
        axT.text(resting * 1.06, -1.02, f"${resting:,.0f} at rest", fontsize=8.5, color="#4A3F35")
        axT.text(max(takes) * .5, .62, f"${takes[i]:,.0f}", ha="center", va="center",
                 fontsize=21, weight="bold", color=CROP_C[item])
        axT.text(max(takes) * .5, .22, f"for the same {lot} {item.lower()}s, sold now",
                 ha="center", va="center", fontsize=9.5, color=INK)
        ratio = takes[i] / resting
        axT.text(max(takes) * .5, -.12, f"{ratio:.1f}x what a resting market pays",
                 ha="center", va="center", fontsize=10, weight="bold",
                 color=CROP_C[item] if ratio >= 1 else "#B04A3A")
        axT.set_xlim(0, max(takes) * 1.05); axT.set_ylim(-1.1, 1.0); axT.set_yticks([])
        axT.set_xlabel("coins for the whole basket", fontsize=9)
        for sp in ("top", "right", "left"):
            axT.spines[sp].set_visible(False)
        plt.tight_layout()

    FuncAnimation(fig, frame, frames=len(shorts)).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)
    return out, {"best": max(takes), "worst": min(takes), "rest": resting,
                 "spread": max(takes) / max(min(takes), 1)}


def crew_gif(steps_a, steps_b, label_a, label_b, patch_a, patch_b, out="crew.gif", fps=5):
    # Two farms, same seed, same engine: the only difference is who works which tile.
    from matplotlib.animation import FuncAnimation, PillowWriter
    days_a, last_a = day_frames(steps_a)
    days_b, last_b = day_frames(steps_b)
    n = min(len(days_a), len(days_b))

    def growing(farm):
        return sum(1 for row in farm["tiles"] for t in row
                   if isinstance(t, dict) and t.get("kind") == "PLANT")

    fig = plt.figure(figsize=(8.0, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.5, .9], hspace=.36, wspace=.06,
                          left=.13, right=.97, top=.84, bottom=.16)
    axL, axR, axB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])

    def frame(i):
        axL.clear(); axR.clear(); axB.clear()
        a = steps_a[last_a[i]][0]["observation"]["farms"][0]
        b = steps_b[last_b[i]][0]["observation"]["farms"][0]
        draw_farm(axL, a); draw_farm(axR, b)
        axL.set_title(f"{label_a}\n${a['money']:,.0f}  ·  {growing(a)} of {patch_a} tiles growing",
                      fontsize=9.5, color="#B04A3A", weight="bold")
        axR.set_title(f"{label_b}\n${b['money']:,.0f}  ·  {growing(b)} of {patch_b} tiles growing",
                      fontsize=9.5, color=P0, weight="bold")
        scale = max(a["money"], b["money"], 1) * 1.25
        axB.barh([1, 0], [a["money"], b["money"]], color=["#B04A3A", P0], height=.6)
        axB.set_yticks([1, 0], ["one farmer", "a crew of 3"], fontsize=8.5)
        axB.set_xlim(0, scale); axB.set_xlabel("coins in the bank", fontsize=9)
        axB.tick_params(axis="x", labelsize=8)
        for sp in ("top", "right", "left"):
            axB.spines[sp].set_visible(False)
        fig.suptitle(f"Day {days_a[i]} of {days_a[n - 1]}: same seed, same engine",
                     fontsize=11.5, color=INK, weight="bold", y=.965)

    FuncAnimation(fig, frame, frames=n).save(out, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)
    return out

def show_gif(path, alt, caption=None):
    import base64, html
    from IPython.display import HTML, display
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    tag = (f'<img src="data:image/gif;base64,{b64}" alt="{html.escape(alt)}" '
           'style="width:100%;max-width:760px;height:auto;border-radius:10px;"/>')
    if caption:
        tag += (f'<div style="font-size:12px;color:#6B6152;margin-top:4px;">'
                f'{html.escape(caption)}</div>')
    display(HTML(tag))


# ---- hero: a real season, animated, before any prose ----
try:
    _row, _seat, _ = biggest_ladder_game()
    show_gif(hero_gif(out="hero.gif"),
             alt="One ladder season animated: a farm filling up beside the prices the town pays.",
             caption=f"Ladder episode {int(_row.episode_id)}, "
                     f"finished {str(_row.end_time)[:10]}, "
                     f"top bank ${_row.top:,.0f}. Redrawn from the dataset every run.")
except FileNotFoundError as e:      # the guide still works without the ladder dataset
    print(e)

print(f"Engine loaded (kaggle-environments {kaggle_environments.__version__}).",
      "Crops:", ", ".join(CROPS), "| Products:", len(PRODUCTS))

env = make("kaggriculture", configuration={"seed": 42})
env.reset()
farm0 = env.state[0].observation["farms"][0]

fig, ax = plt.subplots(figsize=(6.8, 6.8))
draw_farm(ax, farm0, "Day 0: your whole world is one quadrant")
labels = {"NW": (2.5, 7.5, "NW\nyours from the start"),
          "NE": (7.5, 7.5, f"NE\n1st unlock  ${LAND_PRICES[0]:,}"),
          "SW": (2.5, 2.5, f"SW\n2nd unlock  ${LAND_PRICES[1]:,}"),
          "SE": (7.5, 2.5, f"SE\n3rd unlock  ${LAND_PRICES[2]:,}")}
for q, (x, y, txt) in labels.items():
    ax.text(x, y, txt, ha="center", va="center", fontsize=10.5, color="#4A3F35", weight="bold")
ax.annotate("farmer spawns here\n(shed-adjacent)", xy=(4.55, 5.4), xytext=(1.1, 5.9),
            fontsize=9, color=P0, weight="bold",
            arrowprops=dict(arrowstyle="->", color=P0, shrinkA=4, shrinkB=6))
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(8.2, 2.9))
ax.set_xlim(-.6, 40); ax.set_ylim(-.8, 3.4); ax.axis("off"); ax.grid(False)
ax.plot([0, 23], [1, 1], color="#4A3F35", lw=2, zorder=1)
for h in range(24):
    ax.plot(h, 1, "|", ms=10, color="#4A3F35")
shop_hours = [h for h in range(24) if h % 4 == 0]
center_hours = [h for h in range(24) if h % 24 == 0]
ax.plot(shop_hours, [1.55] * len(shop_hours), "v", ms=7, color=PROD_C["EGG"], mec="white")
ax.plot(center_hours, [2.15] * len(center_hours), "v", ms=9, color=PROD_C["MILK"], mec="white")
ax.text(21.2, 1.55, "shops: every 4", fontsize=8.5, va="center", color=PROD_C["EGG"], weight="bold")
ax.text(1.2, 2.15, "town center: once a day", fontsize=8.5, va="center", color=PROD_C["MILK"], weight="bold")
ax.text(0, .35, "hour 0", fontsize=9); ax.text(23, .35, "hour 23", fontsize=9, ha="right")
ax.text(0, 3.0, "One day = 24 turns; every unit acts once per turn", fontsize=11, weight="bold")
ax.text(31.6, 1.0, "END OF DAY:\n• unwatered check (2 misses = weed)\n• unfed check (2 misses = escape)\n• crops/animals produce\n• inventories dumped to shed (cap 100)\n• hands leave, farmer walks home\n• weeds may spawn",
        fontsize=8.4, va="center", ha="left",
        bbox=dict(boxstyle="round,pad=0.45", fc="#F6F0E2", ec="#4A3F35"))
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(8.2, 3.6))
order = ["CARROT", "WHEAT", "TOMATO", "STRAWBERRY", "MELON"]
for i, crop in enumerate(order):
    c, col = CROPS[crop], CROP_C[crop]
    if c["ongoing"]:
        days = ongoing_days(crop)
        ax.barh(i, days[-1] + 1.4, left=0, height=.16, color=col, alpha=.25)
        ax.plot(days, [i] * len(days), "o", ms=8, color=col, mec="white")
        note = f"+1 fruit each dot (max {c['max_yield']})"
    else:
        w0, done = (c["max_yield_day"] + 1) // 2, one_shot_days(crop)
        ax.barh(i, done, left=0, height=.16, color=col, alpha=.25)
        ax.barh(i, done - w0 + 1, left=w0 - .5, height=.34, color=col, alpha=.55)
        ax.plot(done, i, "D", ms=9, color=col, mec="white")
        note = f"harvest once on day {done}: up to {one_shot_units(crop)} units watered daily"
    ax.text(17.2, i, f"seed ${c['seed']}  ·  {note}", fontsize=9.5, va="center")
ax.set_yticks(range(len(order)), order)
for lbl in ax.get_yticklabels():
    lbl.set_color(CROP_C[lbl.get_text()]); lbl.set_weight("bold")
ax.set_xlim(0, 17); ax.set_xlabel("days after planting")
ax.set_title("Crop schedules: darker band = watering bonus window, ♦ = harvest, ● = ongoing fruit")
plt.tight_layout(); plt.show()

econ = crop_econ()

fig, ax = plt.subplots(figsize=(8.2, 3.2))
bars = ax.barh(econ["crop"][::-1], econ["profit / tile-day"][::-1],
               color=[CROP_C[c] for c in econ["crop"][::-1]], height=.62)
for b, v in zip(bars, econ["profit / tile-day"][::-1]):
    ax.text(b.get_width() + 1.5, b.get_y() + b.get_height() / 2, f"${v}/day", va="center",
            fontsize=10, weight="bold")
ax.set_xlim(0, econ["profit / tile-day"].max() * 1.22)
ax.set_title("Profit per tile-day at base prices (daily watering, no fertilizer)")
ax.set_xlabel("coins per tile-day")
plt.tight_layout(); plt.show()
econ.style.hide(axis="index").format(precision=1).set_properties(**{"font-size": "13px"}) \
    .set_table_styles([{"selector": "th", "props": [("font-size", "13px")]}])

def yield_curve(crop, water=True, fert=False):
    # Day-by-day harvestable units for a one-shot crop (engine WATER logic, per day).
    c, units, curve = CROPS[crop], 1, []
    w0 = (c["max_yield_day"] + 1) // 2
    for age in range(0, c["max_yield_day"] + 1):
        if water and w0 <= age <= c["max_yield_day"]:
            units = min(c["max_yield"], units + (2 if fert else 1))
        curve.append(units)
    return curve

fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1), sharey=True)
for ax, crop in zip(axes, ["WHEAT", "MELON"]):
    c = CROPS[crop]
    for fert, style, lbl in [(False, "-", "watered daily"), (True, "--", "watered + fertilized")]:
        curve = yield_curve(crop, fert=fert)
        ax.step(range(len(curve)), curve, style, where="post", color=CROP_C[crop],
                lw=2.2, label=lbl)
    ax.axhline(c["max_yield"], color="#4A3F35", lw=1, ls=":")
    ax.text(0.1, c["max_yield"] + .12, f"max {c['max_yield']}", fontsize=9)
    ax.set_title(crop.title()); ax.set_xlabel("days after planting")
    ax.legend(fontsize=9, loc="upper left", frameon=False)
axes[0].set_ylabel("units at harvest")
fig.suptitle("Fertilizer is the only road to max wheat; melon maxes out on water alone",
             fontsize=12, weight="bold", y=1.04)
plt.tight_layout(); plt.show()

CAL_CROP, CAL_DAYS = "STRAWBERRY", 20
cal = {}
for habit in (True, False):
    c, dry, held, waters, days_w, days_f = CROPS[CAL_CROP], 0, 0, 0, [], []
    for day in range(CAL_DAYS):
        watering = habit or dry >= 1
        waters += watering
        if watering: days_w.append(day)
        dry = 0 if watering else dry + 1
        if dry >= 2: break
        since = day + 1 - c["first_yield_day"]
        if since >= 0 and c["interval"] and since % c["interval"] == 0 \
                and since // c["interval"] + 1 <= c["max_yield"]:
            days_f.append(day)
    cal[habit] = (days_w, days_f)

fig, ax = plt.subplots(figsize=(8.2, 2.1))
rows = [(True, "watered every day", 1), (False, "watered every other day", 0)]
for habit, label, y in rows:
    days_w, days_f = cal[habit]
    for d in range(CAL_DAYS):
        wet = d in days_w
        ax.add_patch(plt.Rectangle((d + .08, y + .12), .84, .76, lw=.8,
                                   fc="#9CC3E0" if wet else "#EFE7D8", ec="white"))
    for d in days_f:
        ax.plot(d + .5, y + .5, "o", ms=9, mfc=CROP_C[CAL_CROP], mec="white", mew=1.4, zorder=3)
    ax.text(-.5, y + .5, label, ha="right", va="center", fontsize=9.5, color=INK)
    ax.text(CAL_DAYS + .4, y + .5, f"{len(days_w)} trips", ha="left", va="center",
            fontsize=10, weight="bold", color=P0 if habit else "#00795F")
ax.set_xlim(-7.5, CAL_DAYS + 4.5); ax.set_ylim(-.15, 2.05)
ax.set_xticks([d + .5 for d in range(0, CAL_DAYS, 5)], [f"day {d}" for d in range(0, CAL_DAYS, 5)],
              fontsize=8.5)
ax.set_yticks([]); ax.tick_params(length=0)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_title(f"One {CAL_CROP.lower()} tile: blue is a trip with the watering can, "
             f"a dot is fruit appearing", fontsize=10.5, color=INK)
plt.tight_layout(); plt.show()

for habit, label, _ in rows:
    days_w, days_f = cal[habit]
    print(f"{label:<24} {len(days_w):>2} waterings, {len(days_f)} fruit")
print("\nSame fruit, half the turns. On a farm where the binding constraint is worker-turns"
      "\n(section 8), that is the cheapest labor you will ever find.")

import matplotlib.patheffects as pe

FEED_COST = BASE["WHEAT"]     # optimistic: base price, the market quotes higher as you buy
season = np.arange(0, 30)          # 720 steps / 24 turns = days 0..29

def payback(a, prod, cared):
    # Mirrors _daily_refresh_animals: a cared+fed day adds 1 to a pending counter, and a production
    # day pays out 1 + whatever has accumulated, capped by max_held.
    cash, pending = [-a["cost"]], 0
    for d in season[1:]:
        units = 0
        if d >= a["first_yield_day"] and (d - a["first_yield_day"]) % a["interval"] == 0:
            units, pending = min(a["max_held"], 1 + pending), 0
        if cared:
            pending += 1
        cash.append(cash[-1] + units * BASE[prod] - FEED_COST)
    return cash

fig, ax = plt.subplots(figsize=(8.2, 3.6))
for animal, a in ANIMALS.items():
    prod = a["product"]
    for cared, style, width, alpha in ((False, ":", 1.6, .55), (True, "-", 2.2, 1.0)):
        cash = payback(a, prod, cared)
        ax.plot(season, cash, style, lw=width, color=PROD_C[prod], alpha=alpha,
                label=(f"{animal.title()} cared, {prod.lower()} x{1 + a['interval']} per pickup"
                       if cared else None))
        be = next((int(d) for d, v in zip(season, cash) if v >= 0), None)
        if be and cared:
            # goose and cow break even a day apart, so separate their labels sideways
            dx, dy, ha = {"GOOSE": (-.4, -560, "right"), "COW": (.4, -560, "left"),
                          "SHEEP": (0, 320, "center")}[animal]
            ax.plot(be, cash[be], "o", ms=9, color=PROD_C[prod], mec="white", zorder=5)
            ax.text(be + dx, cash[be] + dy, f"day {be}", fontsize=9.5, color=PROD_C[prod],
                    weight="bold", ha=ha,
                    path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])
ax.axhline(0, color="#4A3F35", lw=1)
ax.set_xlabel("season day (animal bought on day 0)"); ax.set_ylabel("cumulative coins")
ax.set_title("Care changes the ranking: solid is fed and cared, dotted is fed only")
ax.legend(fontsize=9.5, frameon=False, loc="upper left")
plt.tight_layout(); plt.show()

for animal, a in ANIMALS.items():
    end_c, end_f = payback(a, a["product"], True)[-1], payback(a, a["product"], False)[-1]
    print(f"{animal.title():6s} end of season: {end_c:+8,.0f} cared   {end_f:+8,.0f} fed only")

def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

n_hands = np.arange(1, 11)
costs = [fib(int(n) - 1) for n in n_hands]
cum = np.cumsum(costs)

fig, ax = plt.subplots(figsize=(8.2, 3.2))
bars = ax.bar(n_hands, costs, color="#4A3F35", width=.62, label="cost of n-th hire")
ax.plot(n_hands, cum, "-o", color=P1, lw=2.2, ms=7, mec="white", label="full crew, cumulative")
for x, c in zip(n_hands, cum):
    ax.text(x, c + 3.5, str(int(c)), ha="center", fontsize=9, color=P1, weight="bold")
ax.set_xticks(n_hands)
ax.set_xlabel("hands hired in one day"); ax.set_ylabel("coins")
ax.set_title("Five hands cost 12 coins a day and buy 115 turns; ten cost 143 and buy 230")
ax.legend(fontsize=9.5, frameon=False, loc="upper left")
plt.tight_layout(); plt.show()

HOME = (4, 4)          # the shed-access tile inside the quadrant you start with

def crowded_hires(batched=True, avoid_locked=False):
    # Hire three hands, then send each one home. avoid_locked = your bot refuses unbought tiles.
    def bot(obs):
        farm, step = obs["farms"][obs["player"]], obs["step"]
        hires = ([["HIRE"]] * 3 if step == 0 else []) if batched else ([["HIRE"]] if step < 3 else [])
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": hires}
        moves = []
        for (x, y) in farm["hands"]:
            if (x, y) == HOME:
                moves.append(["PASS"]); continue
            d = "WEST" if x > HOME[0] else "EAST" if x < HOME[0] else \
                "NORTH" if y > HOME[1] else "SOUTH"
            dx, dy = {"NORTH": (0, -1), "SOUTH": (0, 1), "WEST": (-1, 0), "EAST": (1, 0)}[d]
            if avoid_locked and farm["tiles"][y + dy][x + dx] == "LOCKED":
                d = "PASS"
            moves.append([d])
        return {"farmer": ["PASS"], "hands": moves, "market": hires}

    env = make("kaggriculture", configuration={"seed": 0})
    env.run([bot, "starter"])
    idle = sum(1 for s in env.steps[:24]
               for (x, y) in s[0]["observation"]["farms"][0]["hands"]
               if s[0]["observation"]["farms"][0]["tiles"][y][x] == "LOCKED")
    end = env.steps[23][0]["observation"]["farms"][0]
    stuck = sum(1 for (x, y) in end["hands"] if end["tiles"][y][x] == "LOCKED")
    return idle, stuck

for avoid in (False, True):
    label = "refuses unbought tiles" if avoid else "walks across anything"
    for batched, how in ((True, "hired together"), (False, "hired one per turn")):
        idle, stuck = crowded_hires(batched=batched, avoid_locked=avoid)
        print(f"hands that {label:22s}, {how:18s}: {idle:2d} of 69 worker-turns "
              f"spent on land you do not own, {stuck} still there at nightfall")

rates = [10, 25, 50]
fig, ax = plt.subplots(figsize=(8.2, 3.0))
width = .22
shade = ["#B7A88A", "#8A6E4B", "#4A3F35"]
for i, rate in enumerate(rates):
    payback = [p / (25 * rate) for p in LAND_PRICES]
    bars = ax.bar(np.arange(3) + (i - 1) * width, payback, width * .92, color=shade[i],
                  label=f"tiles earn ${rate}/day")
    for b, v in zip(bars, payback):
        ax.text(b.get_x() + b.get_width() / 2, v + .06, f"{v:.1f}d", ha="center", fontsize=8.6)
ax.set_xticks(range(3), [f"{q}  ${p:,}" for q, p in zip(LAND_ORDER, LAND_PRICES)])
ax.set_ylabel("days to pay back")
ax.set_title("Days for a quadrant to pay for itself (25 tiles × your per-tile rate)")
ax.legend(fontsize=9.5, frameon=False)
plt.tight_layout(); plt.show()

from pathlib import Path
NW = sorted([(x, y) for x in range(5) for y in range(5)],
            key=lambda t: (abs(t[0] - 4) + abs(t[1] - 4), t))          # nearest the shed first
NE = sorted([(x, y) for x in range(5, 10) for y in range(5)],
            key=lambda t: (abs(t[0] - 5) + abs(t[1] - 4), t))

CREW_BOT = '''
CARROT, MAX_YIELD_DAY = "CARROT", 3
PATCH, CREW, BUY_LAND = {patch}, {crew}, {buy_land}
SHED = (4, 4)

def step_toward(pos, target):
    (x, y), (tx, ty) = pos, target
    if x < tx: return ["EAST"]
    if x > tx: return ["WEST"]
    if y < ty: return ["SOUTH"]
    if y > ty: return ["NORTH"]
    return ["PASS"]

def tile_needs(tile, seeds, day):
    if isinstance(tile, dict) and tile.get("kind") == "WEED": return ["DIG"]
    if tile is None:
        return ["PLANT", CARROT] if seeds.get(CARROT, 0) > 0 else None
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        if not tile.get("watered_today"): return ["WATER"]
        if day - tile["planted_day"] >= MAX_YIELD_DAY and tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
    return None

def unit_act(pos, mine, me, seeds, day, held):
    fx, fy = pos
    here = me["tiles"][fy][fx]
    if (fx, fy) in mine and here is not None:
        act = tile_needs(here, seeds, day)
        if act: return act
    for (x, y) in mine:
        t = me["tiles"][y][x]
        if (x, y) != (fx, fy) and t is not None and tile_needs(t, seeds, day):
            return step_toward((fx, fy), (x, y))
    if held.get(CARROT, 0) >= 9:
        return ["DROP"] if (fx, fy) == SHED else step_toward((fx, fy), SHED)
    if (fx, fy) in mine and here is None and seeds.get(CARROT, 0) > 0:
        return ["PLANT", CARROT]
    for (x, y) in mine:
        if (x, y) != (fx, fy) and me["tiles"][y][x] is None and seeds.get(CARROT, 0) > 0:
            return step_toward((fx, fy), (x, y))
    if held.get(CARROT, 0) > 0:
        return ["DROP"] if (fx, fy) == SHED else step_toward((fx, fy), SHED)
    return ["PASS"]

def agent(obs):
    me = obs["farms"][obs["player"]]
    private = obs.get("private", {{}})
    seeds = private.get("seeds", {{}})
    invs = private.get("inventories") or [{{}}]
    hands = me["hands"]
    units = 1 + len(hands)

    market = []
    shed_stock = private.get("shed", {{}}).get(CARROT, 0)
    if shed_stock > 0: market.append(["SELL", CARROT, shed_stock])
    empty = sum(1 for (x, y) in PATCH if me["tiles"][y][x] is None)
    need = empty - seeds.get(CARROT, 0)
    if need > 0 and me["money"] >= 20 * need:
        market.append(["BUY_SEED", CARROT, need])
    if BUY_LAND and "NE" not in me["unlocked_quadrants"] and me["money"] >= 1400:
        market.append(["BUY_LAND"])
    # The crew goes home at nightfall, so a bot that wants hands re-hires every morning. One
    # order per hand: six HIRE entries in a single turn really do put six hands on the board.
    if len(hands) < CREW and me["money"] >= 300:
        market.append(["HIRE"])

    shares = [PATCH[i::units] for i in range(units)]      # nobody walks to another unit's plant
    acts = [unit_act(me["farmer"], shares[0], me, seeds, obs["day"], invs[0])]
    for i, h in enumerate(hands):
        pos = h["pos"] if isinstance(h, dict) else h
        acts.append(unit_act(pos, shares[i + 1], me, seeds, obs["day"],
                             invs[i + 1] if len(invs) > i + 1 else {{}}))
    return {{"farmer": acts[0], "hands": acts[1:], "market": market}}
'''

def crew_bot(path, tiles, crew, buy_land=False, split=True):
    pool = NW + NE if buy_land else NW
    src = CREW_BOT.format(patch=pool[:tiles], crew=crew, buy_land=buy_land)
    if not split:                       # every worker chases the same job list, as I first tried
        src = src.replace("shares = [PATCH[i::units] for i in range(units)]",
                          "shares = [PATCH for _ in range(units)]")
    Path(path).write_text(src)
    return path

def bank_of(agent_file, seed):
    # The town each run drew comes back too: section 10 shows the shop draw follows how much
    # ground you plant, and these five arms plant very different amounts.
    env = make("kaggriculture", configuration={"seed": int(seed)})
    env.run([agent_file, "starter"])
    town = tuple(env.steps[-1][0]["observation"]["town"].get("unlocked_shops") or [])
    return env.steps[-1][0]["reward"], town

LAND_SEEDS = range(12)          # section 14's list: twelve is about a minute
ARMS = [("6 tiles\nno hands\n(as shipped)", 6, 0, False, True),
        ("25 tiles\nno hands\n(all free land)", 25, 0, False, True),
        ("12 tiles, 3 hands\nsharing one\njob list", 12, 3, False, False),
        ("12 tiles, 3 hands\neach with its\nown tiles", 12, 3, False, True),
        ("50 tiles, 6 hands\nown tiles\n(+$1,000 for NE)", 50, 6, True, True)]
banks, towns = {}, {}
for label, tiles, crew, land, split in ARMS:
    bot = crew_bot(f"land_{tiles}_{crew}_{int(split)}.py", tiles, crew, land, split)
    got = [bank_of(bot, s) for s in LAND_SEEDS]
    banks[label] = [b for b, _ in got]
    towns[label] = [t for _, t in got]

base = np.array(banks[ARMS[0][0]])
fig, ax = plt.subplots(figsize=(8.4, 3.6))
means = [np.mean(banks[a[0]]) for a in ARMS]
cols = ["#8A7F6B", "#B04A3A", "#B04A3A", P0, "#8A6E4B"]
bars = ax.bar(range(len(ARMS)), means, .62, color=cols)
for i, (b, a) in enumerate(zip(bars, ARMS)):
    d = np.array(banks[a[0]]) - base
    tag = "the baseline" if i == 0 else f"{d.mean():+,.0f} ± {d.std(ddof=1) / len(d) ** .5:,.0f}"
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + max(means) * .02, tag, ha="center",
            fontsize=9, weight="bold", color=cols[i])
ax.set_xticks(range(len(ARMS)), [a[0] for a in ARMS], fontsize=8.5)
ax.set_ylabel("final bank, coins")
ax.set_title(f"Ground, hands, and who works which tile ({len(list(LAND_SEEDS))} paired seeds)")
ax.set_ylim(0, max(means) * 1.28)
plt.tight_layout(); plt.show()

shared, owned = (np.array(banks[ARMS[i][0]]) for i in (2, 3))
gap = owned - shared
print(f"Same twelve tiles, same three hands, same everything else: giving each worker its own "
      f"tiles\nis worth {gap.mean():+,.0f} coins ± {gap.std(ddof=1) / len(gap) ** .5:,.0f}, "
      f"ahead on {(gap > 0).sum()} of {len(gap)} seeds.")
agree = sum(len({towns[a[0]][i] for a in ARMS}) == 1 for i in range(len(list(LAND_SEEDS))))
print(f"\nOne caveat this guide has to hold itself to (section 10): the seed does NOT pin the town "
      f"here.\nAll five arms drew the same shops on {agree} of {len(list(LAND_SEEDS))} seeds, because "
      f"each arm plays differently and\nthe shop draw follows play. The seed still pins the opponent "
      f"and the weather of the season, and averaging\n{len(list(LAND_SEEDS))} of them absorbs the "
      f"rest — but this is a weaker control than section 14's one-constant test.")

# The same two farms, one season, one frame a day. The counter in each title is how many tiles
# are actually holding a plant at that moment, which is the whole argument in one number.
SHOW_SEED = 3
shown = []
for tiles, crew in ((25, 0), (12, 3)):
    e = make("kaggriculture", configuration={"seed": SHOW_SEED})
    e.run([crew_bot(f"show_{tiles}_{crew}.py", tiles, crew), "starter"])
    shown.append(e.steps)

def ever_planted(steps):
    seen = set()
    for st in steps:
        for y, row in enumerate(st[0]["observation"]["farms"][0]["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    seen.add((x, y))
    return len(seen)

show_gif(crew_gif(shown[0], shown[1], "25 tiles, one farmer", "12 tiles, a crew of three",
                  25, 12, out="crew.gif"),
         alt="Two farms side by side: a lone farmer on 25 tiles beside a crew of three on 12.",
         caption=f"Seed {SHOW_SEED}, the built-in starter on the other side of the board in both.")
for steps, total, who in zip(shown, (25, 12), ("One farmer on 25 tiles", "A crew of 3 on 12 tiles")):
    print(f"{who:<26} planted {ever_planted(steps)} of its {total} tiles at some point.")

fig, axes = plt.subplots(3, 3, figsize=(8.2, 7.6), sharex=True)
span = np.arange(-900, 901, 10)   # wide enough to show carrot/tomato/egg past the hinge knee
for ax, item in zip(axes.flat, PRODUCTS):
    prices = [market_price(item, MARKET_I0 + int(d)) for d in span]
    ax.plot(span, prices, lw=2.2, color=PROD_C[item])
    ax.axvline(0, color="#4A3F35", lw=.8, ls=":")
    ax.axhline(1, color="#4A3F35", lw=.6, ls=":")
    p = MARKET_PARAMS[item]
    ax.set_title(f"{item.title()}  base ${p['base']}", fontsize=10, color=PROD_C[item])
    ax.text(.03, .09, f"↓{p['below_func']}  ↑{p['above_func']}", transform=ax.transAxes,
            fontsize=8.2, color="#4A3F35")
    ax.tick_params(labelsize=8)
for ax in axes[-1]:
    ax.set_xlabel("units net-sold into market", fontsize=9)
for ax in axes[:, 0]:
    ax.set_ylabel("price $", fontsize=9)
fig.suptitle("Price vs net supply, per product (0 = resting inventory I0)",
             fontsize=12.5, weight="bold", y=1.0)
plt.tight_layout(); plt.show()

melon_crash = next(d for d in range(1, 1000) if market_price("MELON", MARKET_I0 + d) <= 1)
print(f"Reality check: melon hits the $1 floor after {melon_crash} units net-sold.",
      f"Wheat after 400 units still sells at ${market_price('WHEAT', MARKET_I0 + 400)}.")

gif, take = timing_gif("CARROT", lot=60, out="timing.gif")
show_gif(gif, alt="The same basket of sixty carrots fetching wildly different sums as the market fills.",
         caption="Every price read from the engine's market_price(); the basket never changes size.")
print(f"The same 60 carrots: ${take['best']:,} into a market 700 units short, "
      f"${take['rest']:,} at resting stock, ${take['worst']:,} once it is 300 over.")
print(f"Best to worst, that is a {take['spread']:.0f}x spread on a basket one farm can grow in a week — "
      f"and nothing about the carrots changed.")

import matplotlib.dates as mdates
feat = load_table("episode_features")
eps = load_table("episodes").query("type == 'EPISODE_TYPE_PUBLIC' and state == 'COMPLETED'").copy()
eps["end"] = pd.to_datetime(eps.end_time, format="mixed", utc=True)
seats = pd.concat([
    eps[["episode_id", "end", "rating_0"]].rename(columns={"rating_0": "rating"}).assign(seat=0),
    eps[["episode_id", "end", "rating_1"]].rename(columns={"rating_1": "rating"}).assign(seat=1)])
seats["day"] = seats.end.dt.normalize().dt.tz_localize(None)   # one row per calendar day
seen = feat.merge(seats, on=["episode_id", "seat"])
covered = (seen.groupby("day").size() / seats.groupby("day").size())
full = covered[covered >= .5].index                            # drop the day still being collected
if len(full):
    seen = seen[seen.day.isin(full)]

PATCH_DAY = pd.Timestamp("2026-08-15")
games = seen.drop_duplicates("episode_id")
before, after = games[games.day < PATCH_DAY], games[games.day >= PATCH_DAY]
# A partial copy of the dataset prints nothing here rather than a row of nan.
ENOUGH = len(before) >= 500 and len(after) >= 500

print("What the engine pays when the market runs short, per crop (base price = 1.0):")
for crop in ("CARROT", "TOMATO"):
    base = MARKET_PARAMS[crop]["base"]
    s600, s1000 = (market_price(crop, MARKET_I0 - n) for n in (600, 1000))
    print(f"  {crop.title():<7} base ${base:>3}  |  600 short ${s600:>5} ({s600 / base:>4.1f}x)"
          f"  |  1,000 short ${s1000:>5} ({s1000 / base:>4.1f}x)"
          f"  |  knee at {MARKET_PARAMS[crop]['T']} units")

if not ENOUGH:
    print(f"\nThis copy of the dataset does not straddle {PATCH_DAY:%d %B %Y} with enough games "
          f"({len(before):,} before, {len(after):,} after),\nso the chart and the before-and-after "
          f"numbers are not drawn. Attach the full kaggriculture-episodes\ndataset and re-run.")
else:
    # A fixed rating line would quietly select a different crowd every day, because the field's
    # rating spread moves on its own. Take the top 4% OF THAT DAY instead.
    seen = seen.assign(cut=seen.groupby("day").rating.transform(lambda r: r.quantile(.96)))
    top = seen[seen.rating >= seen.cut]
    adopt = top.assign(carrot=top.plants_carrot.fillna(0) > 0,
                       tomato=top.plants_tomato.fillna(0) > 0).groupby("day").agg(
        share=("carrot", "mean"), tom=("tomato", "mean"), n=("carrot", "size"))
    peaks = games.groupby("day").price_carrot_max.agg(
        median="median", p90=lambda v: v.quantile(.9), n="size")

    fig, (axA, axP) = plt.subplots(1, 2, figsize=(8.4, 3.4), sharex=True)
    axA.plot(adopt.index, adopt.share * 100, color=CROP_C["CARROT"], lw=2.4, label="carrot")
    axA.plot(adopt.index, adopt.tom * 100, color=CROP_C["TOMATO"], lw=2.0, ls="--", label="tomato")
    axA.set_title("Top 4% of seats planting it", fontsize=10.5)
    axA.set_ylabel("% of that day's top seats", fontsize=9); axA.set_ylim(0, 105)
    axA.legend(fontsize=8.5, frameon=False, loc="center left")
    axP.plot(peaks.index, peaks["median"], color=CROP_C["CARROT"], lw=2.4, label="median game")
    axP.plot(peaks.index, peaks.p90, color=CROP_C["CARROT"], lw=1.6, ls=":", label="9th game in 10")
    axP.set_title("Highest carrot price reached in a game", fontsize=10.5)
    axP.set_ylabel("$", fontsize=9); axP.legend(fontsize=8.5, frameon=False, loc="lower right")
    for ax in (axA, axP):
        ax.axvline(PATCH_DAY, color="#B04A3A", lw=1.4, ls="--")
        # AutoDateLocator, not a fixed day interval: a shorter span would otherwise draw a tick
        # per day and turn the axis into a smear.
        loc = mdates.AutoDateLocator(minticks=3, maxticks=6)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
        ax.tick_params(axis="x", labelsize=8.5)
    axA.annotate("engine 1.32.7", xy=(PATCH_DAY, 52), xytext=(6, 0), textcoords="offset points",
                 color="#B04A3A", fontsize=8.5, rotation=90, va="center")
    plt.tight_layout(); plt.show()

    print(f"\nBefore {PATCH_DAY:%d %B %Y}: carrot never once passed $43 — in all {len(before):,} "
          f"ladder games, {(before.price_carrot_max <= 43).mean():.1%} stopped at or under it.")
    print(f"After:  {(after.price_carrot_max > 43).mean():.0%} of {len(after):,} games go past it, "
          f"the median game peaks at ${after.price_carrot_max.median():,.0f}, one in ten clears "
          f"${after.price_carrot_max.quantile(.9):,.0f},\n        and the highest in the dataset is "
          f"${after.price_carrot_max.max():,.0f}.")
    print(f"Tomato's curve was bent the same day and its ceiling moved too — "
          f"${before.price_tomato_max.max():,.0f} before, "
          f"${after.price_tomato_max.max():,.0f} after — and the field ignored it: over the last "
          f"30 days\n        of this dataset, {adopt.tom.tail(30).mean():.1%} of top seats planted "
          f"tomato against {adopt.share.tail(30).mean():.1%} planting carrot.")
    print(f"\nCohort is the top 4% of each day ({adopt.n.min()}-{adopt.n.max()} seats), recomputed "
          f"daily. Data through {seen.day.max():%d %b %Y}.")

gif, take = dump_gif("MELON", n=200, out="dump.gif")
show_gif(gif, alt="Melon price falling unit by unit as one shed is sold into the market.")
kept, hoped = take["shed"]
print(f"A full shed of 100 melons, sold in one go: ${kept:,} kept out of the ${hoped:,} the first "
      f"price promised ({kept / hoped:.0%}).")
kept2, hoped2 = take["all"]
print(f"Keep going to 200 and it is ${kept2:,} of ${hoped2:,} ({kept2 / hoped2:.0%}); "
      f"melon number 200 sells for ${take['last']}.")

import random as _rnd

def _season_shop_demand(shops):
    per = {}
    for k, name in enumerate(shops):                      # shop k unlocks on day 3*(k+1)
        menu = SHOPS[name]
        per_tick = 2 if len(menu) == 1 else 1
        for item in menu:
            per[item] = per.get(item, 0) + per_tick * 6 * (30 - 3 * (k + 1))
    return per

_r = _rnd.Random(7)
_names, _items = sorted(SHOPS), sorted(set().union(*[set(m) for m in SHOPS.values()]))
draws = [_season_shop_demand([_r.choice(_names) for _ in range(8)]) for _ in range(20000)]
dist = {it: sorted(d.get(it, 0) for d in draws) for it in _items}
q = lambda v, f: v[int(f * (len(v) - 1))]

order = sorted(_items, key=lambda i: -q(dist[i], .5))
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4), gridspec_kw={"width_ratios": [1.35, 1]})
for y, it in enumerate(order):
    v = dist[it]
    axes[0].plot([q(v, .05), q(v, .95)], [y, y], lw=6, alpha=.30, color=PROD_C[it],
                 solid_capstyle="butt")
    axes[0].plot(q(v, .5), y, "o", ms=8, color=PROD_C[it])
    axes[0].text(q(v, .95) + 18, y, f"{q(v, .5):.0f}", va="center", fontsize=9, weight="bold")
axes[0].axvline(30, color="#4A3F35", ls="--", lw=1.6)
axes[0].text(.04, .04, "dashed line: the town\ncenter's 30, always",
             transform=axes[0].transAxes, fontsize=8.5, color="#4A3F35", va="bottom")
axes[0].set_yticks(range(len(order)), [i.title() for i in order], fontsize=9)
axes[0].set_title("A season's shop demand (dot = median, bar = 5-95%)", fontsize=10.5)
axes[0].set_xlabel("units bought over 30 days"); axes[0].invert_yaxis()

zero = {it: 100 * sum(1 for x in dist[it] if x == 0) / len(dist[it]) for it in _items}
zs = sorted(_items, key=lambda i: -zero[i])
axes[1].barh([i.title() for i in zs], [zero[i] for i in zs],
             color=[PROD_C[i] for i in zs], height=.62)
for y, i in enumerate(zs):
    axes[1].text(zero[i] + .8, y, f"{zero[i]:.0f}%", va="center", fontsize=9, weight="bold")
axes[1].set_title("Seasons with no shop buying it", fontsize=10.5)
axes[1].set_xlabel("% of seasons"); axes[1].set_xlim(0, 46); axes[1].invert_yaxis()
plt.tight_layout(); plt.show()

print(f"Melon appears on {sum('MELON' in m for m in SHOPS.values())} of the {len(SHOPS)} shop menus.")

import random as _r2
_pairs = {}
_gen = _r2.Random(11)
for _ in range(40000):
    shops = [_gen.choice(_names) for _ in range(8)]
    _pairs.setdefault(tuple(sorted(shops[:2])), []).append(_season_shop_demand(shops))
def _band(item):
    med = {p: np.median([d.get(item, 0) for d in v]) for p, v in _pairs.items() if len(v) >= 200}
    lo, hi = min(med, key=med.get), max(med, key=med.get)
    allv = np.median([d.get(item, 0) for v in _pairs.values() for d in v])
    return med[lo], allv, med[hi], lo, hi

show = ["CARROT", "STRAWBERRY", "WHEAT", "WOOL", "MILK"]
fig, ax = plt.subplots(figsize=(8.2, 3.4))
for y, item in enumerate(show):
    lo, mid, hi, plo, phi = _band(item)
    ax.plot([lo, hi], [y, y], lw=7, alpha=.28, color=PROD_C[item], solid_capstyle="butt")
    ax.plot(mid, y, "o", ms=9, color=PROD_C[item], zorder=3)
    ax.text(lo - 14, y, f"{lo:.0f}", ha="right", va="center", fontsize=9, color="#6B6152")
    ax.text(hi + 14, y, f"{hi:.0f}", va="center", fontsize=9, weight="bold", color=PROD_C[item])
ax.set_yticks(range(len(show)), [i.title() for i in show], fontsize=9.5)
ax.set_xlabel("units the shops buy over the season")
ax.set_title("What day 6 already tells you (dot = typical season, bar = worst to best opening pair)")
ax.invert_yaxis(); ax.set_xlim(-60, 900)
plt.tight_layout(); plt.show()

for item in ("CARROT", "WOOL"):
    lo, mid, hi, plo, phi = _band(item)
    nice = lambda p: " + ".join(x.replace("_", " ").title() for x in p)
    print(f"{item.title():<11} typical season {mid:>5.0f} units | {nice(phi)} -> {hi:>5.0f}"
          f" | {nice(plo)} -> {lo:>4.0f}")

env = make("kaggriculture", configuration={"seed": 42})
env.run(["starter", "starter"])
obs = env.steps[30][0]["observation"]          # a real observation from early day 1

print(f"day={obs['day']}  hour={obs['hour']}  player={obs['player']}")
me = obs["farms"][0]
print(f"\nfarms[0]:  money=${me['money']:.0f}  farmer={me['farmer']}  "
      f"hands={me['hands']}  unlocked={me['unlocked_quadrants']}  hires_today={me['hires_today']}")
print("tiles[y][x] — one row:", [("~" if t is None else "LOCKED" if t == "LOCKED"
      else t.get("crop", t.get("kind", "?"))) for t in me["tiles"][4][:6]], "...")
plant = next((t for row in me["tiles"] for t in row
              if isinstance(t, dict) and t.get("kind") == "PLANT"), None)
print("a plant tile:", plant)
print("\nprivate:  shed:", {k: v for k, v in obs["private"]["shed"].items() if v},
      " seeds:", {k: v for k, v in obs["private"]["seeds"].items() if v},
      " carrying:", obs["private"]["inventories"])
print("market prices:", obs["market"]["prices"])
print("town:", obs["town"])

%%writefile main.py
# Carrot Crew — a deliberately simple Kaggriculture starter bot.
# Six carrot tiles around the shed spawn, watered daily, sold on harvest.

CARROT = "CARROT"
MAX_YIELD_DAY = 3                                   # CROPS["CARROT"]["max_yield_day"]
PATCH = [(4, 4), (3, 4), (2, 4), (2, 3), (3, 3), (4, 3)]
SHED_TILE = (4, 4)                                  # shed-adjacent: DROP works here


def step_toward(pos, target):
    (x, y), (tx, ty) = pos, target
    if x < tx: return ["EAST"]
    if x > tx: return ["WEST"]
    if y < ty: return ["SOUTH"]
    if y > ty: return ["NORTH"]
    return ["PASS"]


def tile_needs(tile, seeds, day):
    # What this patch tile wants right now, or None.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return ["DIG"]
    if tile is None:
        return ["PLANT", CARROT] if seeds.get(CARROT, 0) > 0 else None
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        if not tile.get("watered_today"):
            return ["WATER"]                        # simple, and wasteful: see section 5
        if day - tile["planted_day"] >= MAX_YIELD_DAY and tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
    return None


def agent(obs):
    me = obs["farms"][obs["player"]]
    private = obs.get("private", {})
    seeds = private.get("seeds", {})
    carrying = (private.get("inventories") or [{}])[0]
    fx, fy = me["farmer"]

    market = []
    in_shed = private.get("shed", {}).get(CARROT, 0)
    if in_shed > 0:
        market.append(["SELL", CARROT, in_shed])    # naive: sell on sight (flaw #5, section 15)
    empty = sum(1 for (x, y) in PATCH if me["tiles"][y][x] is None)
    need = empty - seeds.get(CARROT, 0)
    if need > 0 and me["money"] >= 20 * need:
        market.append(["BUY_SEED", CARROT, need])

    # Priorities, in order: tend the living, deliver the harvest, then plant.
    # Watering and harvesting outrank replanting because a seed can wait an
    # hour, while a crop past its window decays into a weed — flip the order
    # and watch the far row die before the farmer reaches it.

    # 1. Living plants and weeds: the tile underfoot first, then walk to one.
    here = me["tiles"][fy][fx]
    if (fx, fy) in PATCH and here is not None:
        act = tile_needs(here, seeds, obs["day"])
        if act:
            return {"farmer": act, "hands": [], "market": market}
    for (x, y) in PATCH:
        tile = me["tiles"][y][x]
        if (x, y) != (fx, fy) and tile is not None and tile_needs(tile, seeds, obs["day"]):
            return {"farmer": step_toward((fx, fy), (x, y)), "hands": [], "market": market}

    # 2. Full basket (a whole row's worth): walk home and drop it so it can sell.
    if carrying.get(CARROT, 0) >= 9:
        if (fx, fy) == SHED_TILE:
            return {"farmer": ["DROP"], "hands": [], "market": market}
        return {"farmer": step_toward((fx, fy), SHED_TILE), "hands": [], "market": market}

    # 3. Planting: the tile underfoot first, then walk to an empty one.
    if (fx, fy) in PATCH and here is None and seeds.get(CARROT, 0) > 0:
        return {"farmer": ["PLANT", CARROT], "hands": [], "market": market}
    for (x, y) in PATCH:
        if (x, y) != (fx, fy) and me["tiles"][y][x] is None and seeds.get(CARROT, 0) > 0:
            return {"farmer": step_toward((fx, fy), (x, y)), "hands": [], "market": market}

    # 4. Nothing else to do: deliver whatever we hold.
    if carrying.get(CARROT, 0) > 0:
        if (fx, fy) == SHED_TILE:
            return {"farmer": ["DROP"], "hands": [], "market": market}
        return {"farmer": step_toward((fx, fy), SHED_TILE), "hands": [], "market": market}
    return {"farmer": ["PASS"], "hands": [], "market": market}

env = make("kaggriculture", configuration={"seed": 42}, debug=True)
env.run(["main.py", "starter"])

money = {i: [step[0]["observation"]["farms"][i]["money"] for step in env.steps] for i in (0, 1)}
final = {i: env.steps[-1][i]["reward"] for i in (0, 1)}
print(f"Final banks — Carrot Crew: ${final[0]:,.0f}   built-in starter: ${final[1]:,.0f}")

fig, ax = plt.subplots(figsize=(8.2, 3.4))
turns = np.arange(len(money[0]))
ax.plot(turns, money[0], color=P0, lw=2.4, label=f"Carrot Crew  (${final[0]:,.0f})")
ax.plot(turns, money[1], color=P1, lw=2.4, label=f"built-in starter  (${final[1]:,.0f})")
for d in range(0, 31, 5):
    ax.axvline(d * 24, color="#4A3F35", lw=.5, alpha=.25)
ax.set_xlabel("turn (gridline every 5 days)"); ax.set_ylabel("bank, coins")
ax.set_title("The number that decides the game: coins in the bank")
ax.legend(fontsize=10, frameon=False, loc="upper left")
plt.tight_layout(); plt.show()

show_gif(season_gif(env.steps, out="season.gif"),
         alt="Carrot Crew's thirty-day season: its six tiles and its farmer walking the loop.")

MY_AGENT = "main.py"          # TWEAK THIS: every cell in this section reads this one name

def play(agent_file, seed, opponent="starter", seat=0):
    env = make("kaggriculture", configuration={"seed": int(seed)})
    env.run([agent_file, opponent] if seat == 0 else [opponent, agent_file])
    banks = [s["reward"] for s in env.steps[-1]]
    return banks[seat], banks[1 - seat]                    # mine, theirs

here = play(MY_AGENT, 0)[0]
spoken = subprocess.run(             # a fresh interpreter, so set order and hash seeds differ too
    [sys.executable, "-c", "from kaggle_environments import make; "
     f"e = make('kaggriculture', configuration={{'seed': 0}}); e.run(['{MY_AGENT}', 'starter']); "
     "print(e.steps[-1][0]['reward'])"], capture_output=True, text=True).stdout.split()
elsewhere = float(spoken[-1]) if spoken else math.nan      # the engine logs first, the bank last

if math.isnan(elsewhere):
    verdict = "the fresh process gave no answer, so skip this one"
elif elsewhere == here:
    verdict = "identical, so a repeat is the same game again"
else:
    verdict = "DIFFERENT, so your bot carries randomness of its own and repeats do help"
print(f"seed 0 here and in a fresh process: {here:>9,.0f} and {elsewhere:>9,.0f}  ->  {verdict}")

seats = [(s, play(MY_AGENT, s)[0], play(MY_AGENT, s, seat=1)[0]) for s in (0, 1, 2)]
print("seeds 0-2, seat 0 against seat 1: "
      + ", ".join(f"{a:,.0f} vs {b:,.0f}" for _, a, b in seats) + "  ->  "
      + ("same both ways, so one seat is enough" if all(a == b for _, a, b in seats)
         else "DIFFERENT, so keep playing both seats"))

SEEDS = range(12)             # four times the seeds halves the band; twelve is about a minute

def compare(version_a, version_b, seeds=SEEDS):
    # Every seed is played by BOTH versions, so whatever luck that seed carries cancels out.
    rows = []
    for s in seeds:
        a, starter = play(version_a, s)
        b, _ = play(version_b, s)
        rows.append({"seed": int(s), "a": a, "b": b, "starter": starter})
    df = pd.DataFrame(rows)
    return df.assign(diff=df.a - df.b)

from pathlib import Path

OLD, NEW = "CARROT, 0) >= 9:", "CARROT, 0) >= 6:"     # v2 delivers at 6 carrots instead of 9
src = Path(MY_AGENT).read_text()
assert OLD in src, f"{MY_AGENT} has no {OLD!r}. Point OLD at a constant your own file contains."
Path("main_v2.py").write_text(src.replace(OLD, NEW))

VERSION_A, VERSION_B = MY_AGENT, "main_v2.py"         # TWEAK THIS: your own two versions
pairs = compare(VERSION_A, VERSION_B)                 # two games per seed; slow bots, slow cell

n_seeds, mean_diff = len(pairs), pairs["diff"].mean()
paired_se = pairs["diff"].std() / n_seeds ** .5                  # one shared seed list
lone_se = (pairs.a.var() + pairs.b.var()) ** .5 / n_seeds ** .5  # a fresh list for each version

print(f"Sanity first: A beat the built-in starter on {(pairs.a > pairs.starter).sum()} of {n_seeds}"
      f" seeds, by {(pairs.a - pairs.starter).mean():+,.0f} coins on average.")
print(f"A minus B: {mean_diff:+,.1f} coins per seed, "
      f"A ahead on {(pairs['diff'] > 0).sum()} of {n_seeds} seeds.")
if paired_se == 0:
    print("  the two versions scored identically on every seed: is B really a different file?")
else:
    print(f"  one shared seed list  -> standard error {paired_se:7.2f}")
    print(f"  fresh seeds for each  -> standard error {lone_se:7.2f}"
          f"   ({lone_se / paired_se:.1f}x wider)")
    print("  verdict: " + ("clears two standard errors on shared seeds"
                           if abs(mean_diff) > 2 * paired_se else "inside the noise even paired"))
    print("           " + ("and would survive fresh seeds too" if abs(mean_diff) > 2 * lone_se
                           else "and on fresh seeds it would vanish"))
print(f"  (scoring the lead instead: spread {pairs.a.std():,.0f} -> "
      f"{(pairs.a - pairs.starter).std():,.0f} coins, because the starter's own bank "
      f"only moves {pairs.starter.std():,.0f})")

import statistics, time, importlib
sys.path.insert(0, ".")
my_bot = importlib.import_module(MY_AGENT.removesuffix(".py"))   # written in section 12
importlib.reload(my_bot)

turn_ms = []                                     # one extra game, played only to time the turn
def timed_agent(obs):
    t0 = time.perf_counter()
    action = my_bot.agent(obs)
    turn_ms.append((time.perf_counter() - t0) * 1000)
    return action

env = make("kaggriculture", configuration={"seed": 42})
env.run([timed_agent, "starter"])
median_ms = statistics.median(turn_ms)
budget_s = env.configuration.actTimeout
overage_s = env.steps[0][0]["observation"]["remainingOverageTime"]

fig, (axS, axP) = plt.subplots(1, 2, figsize=(8.2, 3.5))
x = np.arange(n_seeds)

axS.plot(x, pairs.a / 1000, "o-", color=P0, ms=5, lw=1.6)
axS.plot(x, pairs.b / 1000, "o--", color=P0, ms=4, lw=1.2, alpha=.55, mfc="white")
lo = min(pairs.a.min(), pairs.b.min()) / 1000
hi = max(pairs.a.max(), pairs.b.max()) / 1000
axS.set_ylim(lo - (hi - lo) * .40, hi + (hi - lo) * .06)     # room under the curves for the note
axS.text(.02, .05, f"solid is version A, dashed is version B:\n"
         f"they differ by {abs(mean_diff) / pairs.a.mean():.1%}, too small to read off here",
         transform=axS.transAxes, ha="left", va="bottom", fontsize=10, color="#6C6353")
axS.set_xticks(x, pairs.seed.astype(str), fontsize=10)
axS.set_xlabel("seed", fontsize=10); axS.set_ylabel("final bank, thousands", fontsize=10)
axS.set_title(f"Seed to seed, the bank moves "
              f"{(pairs.a.max() - pairs.a.min()) / pairs.a.mean():.0%}")

span = max(pairs["diff"].abs().max(), 2 * paired_se, abs(mean_diff)) * 1.45
axP.axhspan(-2 * paired_se, 2 * paired_se, color=P0, alpha=.22, ec=P0, lw=1)
axP.bar(x, pairs["diff"], color="#8A7F6B", width=.62, zorder=3)
axP.axhline(mean_diff, color=INK, lw=1.8, zorder=5)
axP.axhline(0, color=INK, lw=.8, alpha=.5, zorder=4)
axP.text(-.45, -2 * paired_se, f" shared seeds: ±{2*paired_se:.0f}",
         ha="left", va="top", fontsize=10, color=P0)
axP.text(-.45, span * .93, f"black line: average {mean_diff:+,.0f}", ha="left", va="top",
         fontsize=10, color=INK, weight="bold")          # kept off the bars, wherever they land
axP.set_ylim(-span, span)
axP.set_xticks(x, pairs.seed.astype(str), fontsize=10)
axP.set_xlabel("seed", fontsize=10); axP.set_ylabel("A minus B, coins", fontsize=10)
axP.set_title("The same games, read as pairs")

ins = axP.inset_axes([.60, .06, .38, .30])                  # the same bars at fresh-seed scale
ins.axhspan(-2 * lone_se, 2 * lone_se, color=P0, alpha=.22)      # the same band, same colour
ins.bar(x, pairs["diff"], color="#8A7F6B", width=.62)
ins.axhline(mean_diff, color=INK, lw=1)                          # the average, landing on zero
ins.set_ylim(-2.3 * lone_se, 2.3 * lone_se)
ins.set_xticks([]); ins.set_yticks([])
ins.text(.04, .94, f"fresh seeds: ±{2*lone_se:.0f}", transform=ins.transAxes, va="top",
         fontsize=10, color=P0)

plt.tight_layout(); plt.show()
print(f"Median turn: {median_ms:.3f} ms against a {budget_s:.0f} s actTimeout plus {overage_s:.0f} s"
      f" of overage. Wall clock, so unlike the banks above this one moves between runs.")

episodes, agents = load_table("episodes"), load_table("agents")

ladder = episodes[episodes["type"] == "EPISODE_TYPE_PUBLIC"]          # ladder games, not self-play
runs = (agents[agents.episode_id.isin(ladder.episode_id)]
        .merge(ladder[["episode_id", "end_time"]], on="episode_id"))
runs["end_time"] = pd.to_datetime(runs["end_time"])
assert len(runs) > 20, f"only {len(runs)} ladder results found; the data looks wrong"

MINE, THEIRS = final[0], final[1]                                     # the single game in section 13
pct = lambda v: (runs.final_bank < v).mean() * 100

fig, (axH, axS) = plt.subplots(1, 2, figsize=(8.2, 3.6))

axH.hist(runs.final_bank / 1000, bins=40, color="#8A7F6B")
med = runs.final_bank.median()
for i, (bank, color, label) in enumerate([(THEIRS, P1, "starter"), (MINE, P0, "Carrot Crew")]):
    axH.axvline(bank / 1000, color=color, lw=2.2)
    axH.text(.34, .93 - i * .12, f"{label} {bank/1000:.1f}k: {med / max(bank, 1):.0f}x under median",
             transform=axH.transAxes, fontsize=8.5, color=color, weight="bold", va="top")
axH.text(.34, .64, "both from our local duel,\nnot from the ladder", transform=axH.transAxes,
         fontsize=8.5, color="#4A3F35", va="top")
axH.set_title("Where a farm lands", fontsize=10.5)
axH.set_xlabel(f"final bank, thousands   ({len(runs):,} games to {runs.end_time.max():%d %b})",
               fontsize=9)
axH.set_ylabel("results")

teams = pd.DataFrame({
    "rating": runs.sort_values("end_time").groupby("team_id").rating_after.last(),
    "bank": runs.groupby("team_id").final_bank.median(),
})
rho = teams.bank.corr(teams.rating, method="spearman")
axS.scatter(teams.bank / 1000, teams.rating, s=48, color="#00795F", alpha=.75,
            edgecolor="white", linewidth=1.2)
axS.set_title(f"Bank vs rating, {len(teams):,} teams (rho {rho:.2f})", fontsize=10.5)
axS.set_xlabel("team's median bank, thousands", fontsize=9)
axS.set_ylabel("rating after its latest game", fontsize=9)

plt.tight_layout(); plt.show()

print(f"Ladder median bank: {runs.final_bank.median():,.0f} coins, "
      f"across {teams.shape[0]} teams.")

_row, _seat, _ = biggest_ladder_game()
show_gif(versus_gif(env.steps, out="versus.gif"),
         alt="Carrot Crew and the richest ladder farm side by side, day for day.",
         caption=f"Ladder episode {int(_row.episode_id)}, finished {str(_row.end_time)[:10]}. "
                 f"The dataset grows, so this is whichever game is biggest when you run it.")

from pathlib import Path
big = crew_bot("dose_all.py", 25, 6)                      # sells its whole shed on sight
Path("dose_trickle.py").write_text(Path(big).read_text().replace(
    'market.append(["SELL", CARROT, shed_stock])',
    'market.append(["SELL", CARROT, min(3, shed_stock)])'))   # at most three units a turn
Path("dose_idle.py").write_text(
    "def agent(obs):\n    return {'farmer': ['PASS'], 'hands': [], 'market': []}\n")

def duel(a, b, seed):
    env = make("kaggriculture", configuration={"seed": int(seed)})
    env.run([a, b])
    return [s["reward"] for s in env.steps[-1]]

DOSE_SEEDS = range(8)
alone = [(duel("dose_trickle.py", "dose_idle.py", s)[0],
          duel("dose_all.py", "dose_idle.py", s)[0]) for s in DOSE_SEEDS]
facing = [duel("dose_trickle.py", "dose_all.py", s) for s in DOSE_SEEDS]

def band(pairs):
    d = np.array([a - b for a, b in pairs])
    return d.mean(), d.std(ddof=1) / len(d) ** .5, int((d > 0).sum()), len(d)

m, se, won, n = band(alone)
print(f"Nobody else selling:  trickling earns {m:+,.0f} +- {se:,.0f} coins, ahead on {won}/{n} seeds")
m, se, won, n = band(facing)
print(f"The two of them, one market: trickling earns {m:+,.0f} +- {se:,.0f} coins, "
      f"wins {won}/{n} games")
print(f"\nSame farm, same season, same order book. Alone, patience pays. Against someone who does "
      f"not\nreturn it, patience is a donation.")

crop_rows = []
for crop, c in CROPS.items():
    crop_rows.append({
        "crop": crop.title(), "seed $": c["seed"], "base $": BASE[crop],
        "type": "ongoing" if c["ongoing"] else "one-shot",
        "first harvest, day": c["first_yield_day"],
        "schedule": (f"fruit every {c['interval']}d × {c['max_yield']}" if c["ongoing"]
                     else f"done on day {one_shot_days(crop)}, up to {one_shot_units(crop)}u watered"),
    })
animal_rows = []
for animal, a in ANIMALS.items():
    animal_rows.append({
        "animal": animal.title(), "cost $": a["cost"], "home": a["structure"].lower(),
        "product": a["product"].title(), "base $": BASE[a["product"]],
        "first product, day": a["first_yield_day"], "then every": f"{a['interval']}d",
        "holds": a["max_held"],
    })
sty = [{"selector": "th", "props": [("font-size", "13px")]}]
display(pd.DataFrame(crop_rows).style.hide(axis="index").set_properties(**{"font-size": "13px"})
        .set_table_styles(sty))
display(pd.DataFrame(animal_rows).style.hide(axis="index").set_properties(**{"font-size": "13px"})
        .set_table_styles(sty))

runs = load_table("agents").merge(
    load_table("episodes").query("type == 'EPISODE_TYPE_PUBLIC' and state == 'COMPLETED'")
    [["episode_id", "end_time"]], on="episode_id")
runs["end"] = pd.to_datetime(runs.end_time, format="mixed", utc=True)
runs = runs.sort_values("end")
runs["nth"] = runs.groupby("submission_id").cumcount() + 1
played = runs.groupby("submission_id").size()
LONG, TAIL = 40, 10
# The settling window must not overlap the games being measured against it, or the right-hand
# end of the curve is pushed down by construction: a submission with exactly LONG games would be
# compared against its own last ten. Require LONG + 20 games so the target sits clear of the plot.
steady = played[played >= LONG + 20].index
long_runs = runs[runs.submission_id.isin(steady)].copy()
settled = (long_runs[long_runs.nth > long_runs.submission_id.map(played) - TAIL]
           .groupby("submission_id").rating_after.mean())
long_runs["gap"] = (long_runs.rating_after - long_runs.submission_id.map(settled)).abs()

curve = long_runs.groupby("nth").gap.quantile([.25, .5, .75]).unstack()
curve = curve.loc[:LONG]
fig, ax = plt.subplots(figsize=(8.2, 3.2))
ax.fill_between(curve.index, curve[.25], curve[.75], color=P0, alpha=.18,
                label="half of submissions fall in here")
ax.plot(curve.index, curve[.5], color=P0, lw=2.6, label="median submission")
ax.set_xlabel("ladder games played by that submission")
ax.set_ylabel("points from the rating\nit ends up at")
ax.set_title(f"How long a rating takes to mean anything ({len(steady):,} submissions, "
             f"{len(long_runs):,} games)")
ax.legend(fontsize=9, frameon=False)
plt.tight_layout(); plt.show()

for k in (5, 10, 20, 40):
    print(f"after {k:>2} games the median submission is still {curve[.5].get(k, float('nan')):>5.0f} "
          f"points from where it settles")
print(f"\nRead this as a floor, not a forecast: a submission only gets this far if nothing newer "
      f"retired it,\nso these are the ones that were left alone. The settling level is each "
      f"submission's last {TAIL} games,\nand only submissions with at least {LONG + 20} games are "
      f"counted, so the target never overlaps the\ncurve. Data through {runs.end.max():%d %b %Y}.")

# Ties are scored as half a win each in the final tournament, so they are worth counting.
duels = load_table("episodes").query("type == 'EPISODE_TYPE_PUBLIC' and state == 'COMPLETED'")
level = duels.bank_0 == duels.bank_1
strong = duels[(duels.rating_0 >= 2400) & (duels.rating_1 >= 2400)]
print(f"\nExact ties: {level.mean():.1%} of {len(duels):,} ladder games, and "
      f"{(strong.bank_0 == strong.bank_1).mean():.1%} when both seats are rated 2400+.")