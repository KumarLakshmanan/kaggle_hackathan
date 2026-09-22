import json, sys, warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

warnings.filterwarnings("ignore")

def find_dir(marker, roots=("/kaggle/input", ".", "..", "data")):
    hits = []
    for r in roots:
        p = Path(r)
        if p.exists():
            hits += [q.parent for q in p.rglob(marker)]
    if not hits:
        raise FileNotFoundError(f"could not find {marker!r} under {roots}")
    return sorted(hits, key=lambda q: len(str(q)))[0]

FIELD = find_dir("stream_hashes.csv")     # georgymamarin/kaggriculture-episodes
TOP = find_dir("streams.parquet")         # destbreso/kaggriculture-top10-replay-streams
print("field  :", FIELD)
print("top ten:", TOP)

hashes = pd.read_csv(FIELD / "stream_hashes.csv",
                     dtype={"episode_id": str, "seat": str})
eps = pd.read_csv(FIELD / "episodes.csv",
                  dtype={"episode_id": str, "sub_0": str, "sub_1": str,
                         "team_0": str, "team_1": str})
eps = eps[(eps.type == "EPISODE_TYPE_PUBLIC") & (eps.state == "COMPLETED")].copy()
eps["day"] = eps.create_time.str[:10]
print(f"\n{len(eps):,} public completed episodes, "
      f"{len(hashes):,} hashed seats, {eps.day.min()} to {eps.day.max()}")

h = hashes.set_index(["episode_id", "seat"])
PREF = ["stream_h24", "stream_h100", "stream_h200", "stream_h400", "stream_h719"]

per_sub = defaultdict(list)
for seat in ("0", "1"):
    m = eps[["episode_id", f"sub_{seat}", "day"]].copy()
    m["seat"] = seat
    m = m.merge(hashes, on=["episode_id", "seat"], how="inner")
    for sub, g in m.groupby(f"sub_{seat}"):
        per_sub[sub].append(g)

groups = {s: pd.concat(v) for s, v in per_sub.items()}
big = {s: g for s, g in groups.items() if len(g) >= 10}
print(f"{len(groups):,} submissions with hashed seats, "
      f"{len(big):,} with at least ten\n")

rows = []
for p in PREF:
    frac, ones = [], 0
    for s, g in big.items():
        d = g[p].nunique(dropna=True)
        if d:
            frac.append(d / len(g))
            ones += d == 1
    rows.append({"prefix": p.replace("stream_", ""),
                 "median distinct per seat": round(float(np.median(frac)), 3),
                 "agents with exactly one": f"{100*ones/len(big):.1f} %"})
marker = pd.DataFrame(rows)
display(marker.style.hide(axis="index"))

# Lightness separated and monotone, so every figure below survives colour vision
# deficiency, greyscale printing and a bad projector.
LINE = ["#B45309", "#1D4ED8", "#1B7F5F", "#7C2D12", "#6D28D9", "#0E7490"]
GOOD, BAD, INK, PALE = "#1B7F5F", "#0F172A", "#334155", "#E7E4DE"

fig, ax = plt.subplots(figsize=(10, 4.6))
x = np.arange(len(PREF))
y = [float(v) for v in marker["median distinct per seat"]]
cols = [GOOD if v < 0.2 else ("#B45309" if v < 0.8 else BAD) for v in y]
ax.bar(x, y, color=cols, width=0.62)
ax.axhline(1.0, color=BAD, lw=1.2, ls="--")
ax.text(-0.44, 1.04, "a new hash every single game: identifies the EPISODE",
        fontsize=9.5, color=BAD)
ax.axhline(0.1, color=GOOD, lw=1.2, ls="--")
ax.text(-0.44, 0.13, "one hash per ten games: identifies the AGENT",
        fontsize=9.5, color=GOOD)
for i, v in enumerate(y):
    ax.text(i, v + 0.04, f"{v:.3f}", ha="center", fontsize=10, color=INK)
ax.set_xticks(x)
ax.set_xticklabels([p.replace("stream_h", "hashed to turn ") for p in PREF],
                   fontsize=9.5)
ax.set_ylabel("distinct hashes per recorded seat, median", fontsize=9.5)
ax.set_ylim(0, 1.22)
ax.set_title("A longer hash is not a better marker. It is a worse one.",
             loc="left", fontsize=13, pad=10)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
plt.show()

allseats = []
for seat in ("0", "1"):
    m = eps[["episode_id"]].copy()
    m["seat"] = seat
    allseats.append(m)
allseats = pd.concat(allseats).merge(hashes, on=["episode_id", "seat"], how="inner")

rows = []
for p in ("stream_h24", "stream_h400"):
    v = allseats[p].dropna()
    c = v.value_counts()
    pairs = len(v) * (len(v) - 1) / 2
    same = (c * (c - 1) / 2).sum()
    rows.append({
        "prefix": p.replace("stream_", ""),
        "seats": f"{len(v):,}",
        "distinct schedules": f"{len(c):,}",
        "seats sharing with at least one other": f"{100*c[c>=2].sum()/len(v):.1f} %",
        "the single most common schedule": f"{100*c.iloc[0]/len(v):.1f} %",
        "PAIRS of seats that agree": f"{100*same/pairs:.1f} %"})
display(pd.DataFrame(rows).set_index("prefix").T)

top = pd.read_parquet(TOP / "streams.parquet")
top["episode_id"] = top["episode_id"].astype(str)
top["submission"] = top["submission"].astype(str)
top["plan"] = top["farmer"] + "|" + top["hands_h"]
tmeta = pd.read_csv(TOP / "episodes.csv",
                    dtype={"episode_id": str, "submission": str})

# key on the PAIR: an episode between two of the ten appears once per seat
by_ep = {k: g.sort_values("turn").plan.tolist()
         for k, g in top.groupby(["submission", "episode_id"])}

floors = []
for sub, g in tmeta.groupby("submission"):
    seat = g.seat.value_counts().idxmax()
    ids = g[g.seat == seat].sort_values("episode_id").episode_id.head(8).tolist()
    runs = [by_ep[(sub, e)] for e in ids if (sub, e) in by_ep]
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            a, b = runs[i], runs[j]
            n = min(len(a), len(b))
            d = next((t for t in range(n) if a[t] != b[t]), n)
            floors.append(d)
floors = np.array(floors)
print(f"{len(floors)} pairs of episodes from the SAME agent\n")
for q in (0, 10, 50, 90, 100):
    print(f"  p{q:<4} first disagreement at turn {int(np.percentile(floors, q)):>4}")
FLOOR = int(np.percentile(floors, 50))
print(f"\n  An agent splits from ITSELF at turn {FLOOR}, half the time.")
print("  Any between-agent split shallower than that is not evidence of "
      "separate ancestry.")

fig, ax = plt.subplots(figsize=(11.5, 4.3))
ax.hist(floors, bins=np.arange(0, 745, 24), color=LINE[2],
        label="two episodes of the SAME agent")
top_y = ax.get_ylim()[1]
ax.axvspan(0, FLOOR, color=BAD, alpha=0.07)
ax.axvline(FLOOR, color=BAD, lw=1.7)
ax.text(FLOOR + 12, top_y * 0.92,
        f"median: an agent splits from itself at turn {FLOOR}",
        fontsize=10.5, color=BAD, va="center")
ax.text(10, top_y * 0.55,
        "a split between two DIFFERENT\nagents anywhere in here is\ninside the "
        "noise one lineage\nmakes on its own",
        fontsize=9.5, color=INK, va="top")
ax.set_xlim(0, 720)
ax.set_xlabel("turn at which the two episodes first disagree", fontsize=9.5)
ax.set_ylabel("pairs of episodes", fontsize=9.5)
ax.set_title("The floor, without which no split depth means anything",
             loc="left", fontsize=13, pad=10)
ax.legend(frameon=False, fontsize=9.5, loc="upper right")
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
plt.show()

MIN_SEATS = 3
USABLE = ["stream_h24", "stream_h100", "stream_h200"]

placed, seats_of, born = {}, {}, {}
for sub, g in groups.items():
    if len(g) < MIN_SEATS:
        continue
    key = []
    for p in USABLE:
        c = g[p].dropna()
        if c.empty:
            break
        key.append(c.mode().iloc[0])
    if len(key) == len(USABLE):
        placed[sub] = tuple(key)
        seats_of[sub] = g
        born[sub] = g.day.min()

print(f"{len(placed):,} submissions placed into a nested lineage\n")
for lvl, p in enumerate(USABLE):
    n = len({v[:lvl+1] for v in placed.values()})
    top3 = Counter(v[:lvl+1] for v in placed.values()).most_common(3)
    print(f"  {p.replace('stream_',''):<6} {n:>5} lineages   largest "
          + ", ".join(f"{c} ({100*c/len(placed):.0f} %)" for _, c in top3))

by_day = defaultdict(Counter)
for sub, g in seats_of.items():
    k = placed[sub][0]
    for d, n in g.day.value_counts().items():
        by_day[d][k] += n
for d in sorted(set(eps.day)):
    tot = int((eps.day == d).sum()) * 2
    if d not in by_day:
        by_day[d] = Counter()

days = sorted(d for d in by_day if sum(by_day[d].values()) >= 400)
size = Counter()
for d in days:
    size.update(by_day[d])
keep = [k for k, _ in size.most_common(5)]

share = {k: [100 * by_day[d][k] / sum(by_day[d].values()) for d in days]
         for k in keep}
other = [100 - sum(share[k][i] for k in keep) for i in range(len(days))]

# order the bands by when each lineage first appears, so the picture reads left
# to right as succession rather than as an arbitrary stack
birth_i = {k: next((i for i, d in enumerate(days) if by_day[d][k] > 0), 0)
           for k in keep}
keep = sorted(keep, key=lambda k: birth_i[k])
share = {k: [100 * by_day[d][k] / sum(by_day[d].values()) for d in days]
         for k in keep}
other = [100 - sum(share[k][i] for k in keep) for i in range(len(days))]

fig, ax = plt.subplots(figsize=(13.5, 6.2))
X = np.arange(len(days))
ax.stackplot(X, other, *[share[k] for k in keep],
             colors=[PALE] + LINE[:len(keep)], edgecolor="white", linewidth=0.8)

# direct labels at each lineage's own peak, so identity never rests on colour
base = np.array(other, dtype=float)
for n, k in enumerate(keep):
    v = np.array(share[k], dtype=float)
    mid = base + v / 2
    i = int(v.argmax())
    if v[i] > 8:
        ax.text(X[i], mid[i], f"{k[:6]}\n{v[i]:.0f}%", ha="center", va="center",
                fontsize=10, color="white", weight="bold", linespacing=1.15)
    base = base + v

ax.set_xticks(X)
ax.set_xticklabels([d[5:] for d in days], fontsize=9)
ax.set_ylim(0, 100)
ax.set_xlim(0, len(days) - 1)
ax.set_ylabel("share of every seat played that day, %", fontsize=10)
ax.set_xlabel("day, 2026", fontsize=10)
ax.set_title("The field does not drift. It turns over by sweeps.",
             loc="left", fontsize=14.5, pad=12)
ax.text(0, 104, "each band is one lineage, ordered by when it first appears; "
                "the pale band is everything else",
        fontsize=10, color=INK)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
plt.show()

print(f"{'day':<12}" + "".join(f"{k[:6]:>10}" for k in keep) + f"{'other':>10}"
      + f"{'seats':>9}")
for i, d in enumerate(days):
    print(f"{d:<12}" + "".join(f"{share[k][i]:>9.0f}%" for k in keep)
          + f"{other[i]:>9.0f}%{sum(by_day[d].values()):>9,}")

from datetime import date

POOL, REPS = 400, 40                 # seats per sample, and independent draws
rng2 = np.random.default_rng(11)
seats_of_day = {d: np.array([k for k, n in by_day[d].items() for _ in range(n)])
                for d in days}

cov, ctrl = defaultdict(list), []
for _ in range(REPS):
    samp = {d: v[rng2.permutation(len(v))[:POOL]]
            for d, v in seats_of_day.items()}
    for i, a in enumerate(days):
        seen = set(samp[a])
        for b in days[i + 1:]:
            lag = (date.fromisoformat(b) - date.fromisoformat(a)).days
            cov[lag].append(float(np.mean([k in seen for k in samp[b]])))
    for d, v in seats_of_day.items():        # the control, inside one day
        p = rng2.permutation(len(v))
        h = min(POOL, len(v) // 2)
        A, B = set(v[p[:h]]), v[p[len(v) // 2:len(v) // 2 + h]]
        ctrl.append(float(np.mean([k in A for k in B])))

print(f"a pool of {POOL} seats drawn on one day, matched against a later day:")
print(f"  what share of the later day it covers, mean of {REPS} draws\n")
print(f"  same day, two disjoint halves   {np.mean(ctrl):.2f}   <- the control")
lags = [l for l in sorted(cov) if l <= 7 and len(cov[l]) >= 3 * REPS]
ys = [float(np.mean(cov[l])) for l in lags]
for l, y in zip(lags, ys):
    print(f"  {l} day{'s' if l > 1 else ' '} later{'':<19}{y:.2f}"
          f"   ({len(cov[l]) // REPS} pairs of days)")

prev_l, prev_y, half = 0, float(np.mean(ctrl)), None
for l, y in zip(lags, ys):
    if y < 0.5:
        half = prev_l + (prev_y - 0.5) / (prev_y - y) * (l - prev_l)
        break
    prev_l, prev_y = l, y
print(f"\n  it falls through one half at {half:.1f} days")

from matplotlib import animation
from IPython.display import HTML

WINDOW = 18      # hours in the rolling window
STEP = 4         # hours between frames
MINSEATS = 120   # a window thinner than this is noise, not a measurement

ep_hour = eps.set_index("episode_id").create_time.str[:13].to_dict()
hourly = defaultdict(Counter)
for sub, g in seats_of.items():
    k = placed[sub][0]
    for e in g.episode_id:
        h = ep_hour.get(e)
        if h:
            hourly[h][k] += 1
for e, h in ep_hour.items():
    hourly[h]["__all__"] += 2

hours = sorted(hourly)
idx = {h: i for i, h in enumerate(hours)}
K = keep
cnt = np.zeros((len(hours), len(K)))
tot = np.zeros(len(hours))
for h, c in hourly.items():
    i = idx[h]
    tot[i] = c["__all__"]
    for j, k in enumerate(K):
        cnt[i, j] = c[k]

roll_c = np.array([cnt[max(0, i - WINDOW + 1):i + 1].sum(axis=0)
                   for i in range(len(hours))])
roll_t = np.array([tot[max(0, i - WINDOW + 1):i + 1].sum()
                   for i in range(len(hours))])
ok = np.flatnonzero(roll_t >= MINSEATS)
frames = list(range(ok[0], ok[-1] + 1, STEP))
S = np.zeros((len(hours), len(K)))
S[ok] = 100 * roll_c[ok] / roll_t[ok, None]
print(f"{len(frames)} frames, {WINDOW} hour window stepped every {STEP} hours, "
      f"{hours[frames[0]]} to {hours[frames[-1]]}")

fig = plt.figure(figsize=(11, 6.1), dpi=72)
gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1], hspace=0.42)
axT, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

xs = np.arange(len(hours))
axT.stackplot(xs[ok], *[S[ok, j] for j in range(len(K))],
              colors=LINE[:len(K)], alpha=0.9)
axT.set_ylim(0, 100)
axT.set_xlim(ok[0], ok[-1])
tick = [i for i in ok if hours[i].endswith("T00")]
axT.set_xticks(tick)
axT.set_xticklabels([hours[i][5:10] for i in tick], fontsize=8.5)
axT.set_ylabel("share of seats, %", fontsize=9)
for sp in ("top", "right"):
    axT.spines[sp].set_visible(False)
cursor = axT.axvline(frames[0], color=BAD, lw=1.8)

bars = axB.bar(range(len(K)), [0] * len(K), color=LINE[:len(K)], width=0.62)
axB.set_xticks(range(len(K)))
axB.set_xticklabels([k[:6] for k in K], fontsize=9.5)
axB.set_ylim(0, 65)
axB.set_ylabel("share of seats in the window, %", fontsize=9)
for sp in ("top", "right"):
    axB.spines[sp].set_visible(False)
labels = [axB.text(i, 0, "", ha="center", va="bottom", fontsize=9.5, color=INK)
          for i in range(len(K))]
title = fig.suptitle("", y=0.97, fontsize=13.5)

def draw(i):
    cursor.set_xdata([i, i])
    for j, b in enumerate(bars):
        b.set_height(S[i, j])
        labels[j].set_position((j, S[i, j] + 1.0))
        labels[j].set_text(f"{S[i, j]:.0f}%" if S[i, j] >= 1 else "")
    title.set_text(f"A sweep arriving and leaving, hour by hour"
                   f"      {hours[i].replace('T', '  ')}:00 UTC")
    return [cursor, title, *bars, *labels]

anim = animation.FuncAnimation(fig, draw, frames=frames, interval=110, blit=False)
plt.close(fig)
HTML(anim.to_jshtml(default_mode="loop"))

agents = pd.read_csv(FIELD / "agents.csv", dtype={"submission_id": str})
best = agents.groupby("submission_id").rating_after.max()
STRONG = 2900
# only submissions that COULD be attributed to a lineage belong in the
# denominator; counting unplaced ones would make every lineage look small
placed_strong = [s for s in placed if best.get(s, 0) >= STRONG]

rows = []
for k, subs in sorted(Counter(v[0] for v in placed.values()).items(),
                      key=lambda kv: -kv[1])[:8]:
    members = [s for s, v in placed.items() if v[0] == k]
    r = [best.get(s, np.nan) for s in members]
    r = [x for x in r if x == x]
    rows.append({"lineage": k[:6], "submissions": len(members),
                 "first seen": min(born[s] for s in members),
                 "best rating": round(max(r), 1) if r else None,
                 "rated 2900+": sum(1 for x in r if x >= STRONG),
                 "sub-lineages": len({placed[s] for s in members})})
lin = pd.DataFrame(rows)
total_strong = len(placed_strong)
print(f"{int((best >= STRONG).sum())} submissions have ever been rated at or "
      f"above {STRONG}; {total_strong} of them are placed in a lineage\n")
display(lin.style.hide(axis="index"))
print(f"\nthe top lineage holds {lin['rated 2900+'].max()} of the {total_strong} "
      f"placed strong submissions, {100*lin['rated 2900+'].max()/total_strong:.0f} %")
print(f"the LARGEST lineage, {lin.iloc[0]['lineage']} with "
      f"{lin.iloc[0]['submissions']} submissions, holds "
      f"{lin.iloc[0]['rated 2900+']}")

use = [s for s in placed if len(seats_of[s]) >= 5]
K = [placed[s] for s in use]
n = len(use)
print(f"{n:,} lineages with at least five recorded seats\n")

shared = np.zeros((n, n), dtype=np.int8)
for i in range(n):
    for j in range(n):
        d = 0
        for t in range(len(USABLE)):
            if K[i][t] != K[j][t]:
                break
            d += 1
        shared[i, j] = d
v = shared[np.triu_indices(n, 1)]

print(f"  {'how deep two lineages still agree':<38}{'pairs':>12}{'share':>9}")
for d, name in ((0, "not at all, apart by turn 24"),
                (1, "the turn 24 opening"),
                (2, "through turn 100"),
                (3, "through turn 200")):
    print(f"  {name:<38}{int((v == d).sum()):>12,}{100*(v == d).mean():>8.1f}%")
print(f"\n  for scale, the SAME agent splits from itself at turn {FLOOR}, "
      f"half the time")

from matplotlib.colors import ListedColormap

# the 150 largest lineages, ordered so that anything related sits together
order = sorted(range(n), key=lambda i: (K[i][0], K[i][1], K[i][2]))
big_i = sorted(order, key=lambda i: -len(seats_of[use[i]]))[:150]
big_i = sorted(big_i, key=lambda i: (K[i][0], K[i][1], K[i][2]))
M = shared[np.ix_(big_i, big_i)]

fig, ax = plt.subplots(figsize=(7.6, 7.2))
cm = ListedColormap([PALE, "#F2C879", "#B45309", "#0F172A"])
ax.imshow(M, cmap=cm, vmin=0, vmax=3, interpolation="nearest")
ax.set_xticks([]); ax.set_yticks([])
ax.set_xlabel("150 largest lineages, sorted so relatives sit together",
              fontsize=9.5)
ax.set_title("The field, as a matrix. It is almost empty.",
             loc="left", fontsize=13.5, pad=10)
handles = [Patch(facecolor=c, label=l) for c, l in
           ((PALE, "share nothing, apart by turn 24"),
            ("#F2C879", "share the turn 24 opening"),
            ("#B45309", "identical through turn 100"),
            ("#0F172A", "identical through turn 200"))]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.06),
          ncol=2, frameon=False, fontsize=9)
plt.show()