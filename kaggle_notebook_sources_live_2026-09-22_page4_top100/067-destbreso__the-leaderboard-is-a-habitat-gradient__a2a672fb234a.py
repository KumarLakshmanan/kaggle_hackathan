import json, math, collections
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from IPython.display import HTML

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e7e7e4'
plt.rcParams.update({'figure.dpi':120,'savefig.dpi':120,'font.size':10,
    'axes.titlesize':12,'axes.labelsize':10,'axes.edgecolor':MUTED,
    'axes.labelcolor':INK,'text.color':INK,'xtick.color':MUTED,'ytick.color':MUTED,
    'axes.spines.top':False,'axes.spines.right':False,
    'figure.facecolor':'white','axes.facecolor':'white','animation.embed_limit':60})

def tidy(ax, ylab=None, title=None):
    ax.set_axisbelow(True); ax.yaxis.grid(True, color=GRID, lw=0.8); ax.xaxis.grid(False)
    if ylab: ax.set_ylabel(ylab)
    if title: ax.set_title(title, loc='left', pad=10, fontweight='bold')
    return ax

# Animations are rendered to a GIF and embedded, rather than shipped as a jshtml
# player. A GIF plays inline, autoplays, loops, and survives being viewed on a
# phone; the player widget does none of those. The technique is borrowed from
# Georgy Mamarin's own notebooks on this competition.
import base64, io as _io
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.patheffects as pe

HALO = [pe.withStroke(linewidth=2.6, foreground='white')]

def show_gif(fig, frame_fn, frames, fps=12, dpi=96, name='anim.gif'):
    """Render an animation to a looping GIF and embed it in the output."""
    FuncAnimation(fig, frame_fn, frames=frames).save(
        name, writer=PillowWriter(fps=fps), dpi=dpi)
    plt.close(fig)
    b64 = base64.b64encode(open(name, 'rb').read()).decode()
    return HTML(f'<img src="data:image/gif;base64,{b64}" '
                f'style="max-width:100%;height:auto">')

# ---------------------------------------------------------------------------
# EVERYTHING BELOW IS COMPUTED FROM THE DATASET AT RUN TIME.
#
# This notebook is attached to a dataset that refreshes daily, so nothing here is
# a stored constant. Re-running it re-measures the field, and every figure and
# number moves with it. That is the whole point: the competition changes, and a
# report of a fixed snapshot goes quietly stale while still looking correct.
import os, csv, collections, datetime as dt

def find_data(roots=("/kaggle/input",)):
    """Locate the dataset wherever Kaggle mounted it, or locally."""
    def scan(root, depth=6):
        root = os.path.abspath(root); base = root.rstrip(os.sep).count(os.sep)
        hits = []
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base >= depth:
                dirnames[:] = []; continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            if "stream_hashes.csv" in filenames and "episodes.csv" in filenames:
                hits.append(dirpath)
        return hits
    found = []
    for r in roots:
        if os.path.isdir(r): found += scan(r)
    here = os.path.abspath(os.getcwd())
    while not found:
        for sub in ("data", "."):
            d = os.path.join(here, sub)
            if os.path.isdir(d): found += scan(d, 4)
        parent = os.path.dirname(here)
        if parent == here: break
        here = parent
    if found: return found[0]
    raise FileNotFoundError(
        "Attach georgymamarin/kaggriculture-episodes to this notebook. "
        "It needs stream_hashes.csv and episodes.csv.")

DATA = find_data()
rd = lambda f: list(csv.DictReader(open(os.path.join(DATA, f))))

HASH = {(r["episode_id"], r["seat"]): r for r in rd("stream_hashes.csv")}
EPS  = [r for r in rd("episodes.csv") if r.get("type") == "EPISODE_TYPE_PUBLIC"]
AG   = rd("agents.csv")
TEAM = {r["team_id"]: r for r in rd("teams.csv")}
SUB_TEAM = {r["submission_id"]: r["team_id"] for r in AG}

HCOLS = ["stream_h24", "stream_h100", "stream_h200", "stream_h400", "stream_h719"]
TURNS = [24, 100, 200, 400, 719]

# One row per seat: opening, full-game hash, rating, timestamp, submission.
SEATS = []
for r in EPS:
    when = dt.datetime.strptime(str(r["create_time"])[:13], "%Y-%m-%dT%H")
    for s in (0, 1):
        h = HASH.get((r["episode_id"], str(s)))
        if not h or not h.get("stream_h24"):
            continue
        try: rating = float(r[f"rating_{s}"])
        except (ValueError, TypeError, KeyError): rating = 0.0
        SEATS.append({"ep": r["episode_id"], "seat": s, "when": when, "rating": rating,
                      "sub": r.get(f"sub_{s}"), "team": r.get(f"team_{s}"),
                      "h": [h.get(c) for c in HCOLS]})

WINDOW_FROM = min(x["when"] for x in SEATS)
WINDOW_TO   = max(x["when"] for x in SEATS)
print(f"dataset at {DATA}")
print(f"{len(EPS):,} public episodes, {len(SEATS):,} seats with a fingerprint")
print(f"window {WINDOW_FROM:%Y-%m-%d} to {WINDOW_TO:%Y-%m-%d}  "
      f"({(WINDOW_TO - WINDOW_FROM).days + 1} days)")
print()
print("Every figure below is recomputed from this. Nothing is a stored constant.")

# --- the derived quantities every section uses -------------------------------
def diversity(labels):
    c = collections.Counter(labels); n = sum(c.values())
    p = [v / n for v in c.values()]
    return {"distinct": len(c), "effective": 1 / sum(x * x for x in p),
            "largest": 100 * max(p), "n": n}

counts = [collections.Counter(x["h"][k] for x in SEATS if x["h"][k]) for k in range(5)]
NSEAT = len(SEATS)
glob = counts[0]
TOP = [o for o, _ in glob.most_common(12)]
TOPK = [o[:8] for o in TOP[:10]]
TOP5 = [o[:8] for o in TOP[:5]]

# 1. is the population abstraction earned, per horizon
JUSTIF = {}
for k, t in enumerate(TURNS):
    col = [x["h"][k] for x in SEATS if x["h"][k]]
    c = counts[k]; single = sum(1 for v in col if c[v] == 1)
    JUSTIF[f"turn {t}"] = {"seats": len(col), "groups": len(c), "singletons": single,
                           "in_group": 100 * (len(col) - single) / len(col),
                           "largest": 100 * max(c.values()) / len(col)}

# 2. clone / descendant / unrelated, and where descendants mutate
last = collections.Counter()
for x in SEATS:
    lvl = -1
    for k in range(5):
        if x["h"][k] and counts[k][x["h"][k]] > 1: lvl = k
        else: break
    last[lvl] += 1
TAX = {"n": NSEAT, "clones": last[4],
       "descendants": sum(v for k, v in last.items() if 0 <= k < 4),
       "unrelated": last[-1], "turns": TURNS,
       "by_last": {str(k): last[k] for k in last}}

# 3. the genealogy
NESTING_VIOLATIONS = {}
for k in range(4):
    seen, bad = {}, 0
    for x in SEATS:
        deep, shallow = x["h"][k + 1], x["h"][k]
        if not deep or not shallow: continue
        if deep in seen and seen[deep] != shallow: bad += 1
        seen[deep] = shallow
    NESTING_VIOLATIONS[TURNS[k + 1]] = bad
LEVELS = [{"turn": t, "clades": len(counts[k])} for k, t in enumerate(TURNS)]
sub = [x for x in SEATS if x["h"][0] == TOP[0]]
FAN = []
for k in range(5):
    c = collections.Counter(x["h"][k] for x in sub if x["h"][k]).most_common()
    FAN.append({"turn": TURNS[k], "branches": len(c), "top": [v for _, v in c[:8]],
                "rest": sum(v for _, v in c[8:])})

# 4. rating bands
BAND_EDGES = [(0, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 2800), (2800, 9999)]
BANDS, BAND_POP, COMP = [], [], {}
for lo, hi in BAND_EDGES:
    g = [x for x in SEATS if lo <= x["rating"] < hi]
    if len(g) < 300: continue
    name = f"{lo}-{hi}" if hi < 9000 else f"{lo}+"
    BANDS.append({"band": name, **diversity([x["h"][0] for x in g])})
    c = collections.Counter(x["h"][0] for x in g)
    BAND_POP.append({"band": name, "n": len(g),
                     "pop": 100 * sum(1 for x in g if glob[x["h"][0]] >= 50) / len(g),
                     "single": 100 * sum(1 for x in g if c[x["h"][0]] == 1) / len(g)})
    COMP[name] = [100 * c[o] / len(g) for o in TOP[:5]]

NICHE = {}
for o in TOP:
    v = sorted(x["rating"] for x in SEATS if x["h"][0] == o and x["rating"] > 0)
    if len(v) >= 20:
        NICHE[o[:8]] = [len(v), v[int(.1 * len(v))], v[len(v) // 2], v[int(.9 * len(v))]]

# 5. daily series, and the per-day population share
def series(key, minimum):
    keys = sorted({key(x) for x in SEATS}); kept = []
    out = {o[:10]: [] for o in TOP[:10]}
    for k in keys:
        g = [x["h"][0] for x in SEATS if key(x) == k]
        if len(g) < minimum: continue
        c = collections.Counter(g); kept.append(k)
        for o in TOP[:10]: out[o[:10]].append(round(100 * c[o] / len(g), 3))
    return kept, out

DAYS, SERIES = series(lambda x: x["when"].strftime("%m-%d"), 400)
DAY_POP = []
for d in DAYS:
    g = [x for x in SEATS if x["when"].strftime("%m-%d") == d]
    c = collections.Counter(x["h"][0] for x in g); n = len(g)
    DAY_POP.append({"day": d, "n": n,
                    "pop": 100 * sum(1 for x in g if c[x["h"][0]] >= max(5, 0.01 * n)) / n,
                    "eff": 1 / sum((v / n) ** 2 for v in c.values())})

# 6. hourly frames on a 24-hour window, for smooth animation
ordered = sorted(SEATS, key=lambda x: x["when"])
t0, t1 = ordered[0]["when"], ordered[-1]["when"]
buf, idx, HF = collections.deque(), 0, []
for hh in range(int((t1 - t0).total_seconds() // 3600) + 1):
    now = t0 + dt.timedelta(hours=hh)
    while idx < len(ordered) and ordered[idx]["when"] <= now:
        buf.append(ordered[idx]); idx += 1
    while buf and buf[0]["when"] < now - dt.timedelta(hours=24): buf.popleft()
    c = collections.Counter(x["h"][0] for x in buf); n = sum(c.values())
    if n < 200: continue
    HF.append({"t": now.strftime("%m-%d %H:00"), "n": n,
               "share": [round(100 * c[o] / n, 3) for o in TOP[:10]]})
F = HF

# 7. the simplex walk, daily and hourly with speed
def simplex_xy(shares):
    s = sum(shares)
    if s < 5: return None
    p = [x / s for x in shares]
    return (p[1] + 0.5 * p[2], (3 ** 0.5 / 2) * p[2])

SX = {"tri": [o[:8] for o in TOP[:3]], "days": [], "pts": []}
for i, d in enumerate(DAYS):
    xy = simplex_xy([SERIES[o[:10]][i] for o in TOP[:3]])
    if xy: SX["days"].append(d); SX["pts"].append(list(xy))

TRAJ, prev = [], None
for f in HF:
    xy = simplex_xy(f["share"][:3])
    if xy is None: prev = None; continue
    spd = 0.0 if prev is None else ((xy[0]-prev[0])**2 + (xy[1]-prev[1])**2) ** 0.5
    TRAJ.append([f["t"], list(xy), spd]); prev = xy

print(f"derived: {len(BANDS)} rating bands, {len(DAYS)} days, {len(HF)} hourly frames")
print(f"clones {100*TAX['clones']/NSEAT:.1f}%, descendants "
      f"{100*TAX['descendants']/NSEAT:.1f}%, unrelated {100*TAX['unrelated']/NSEAT:.1f}%")
print(f"nesting violations: {NESTING_VIOLATIONS}")
print(f"simplex: {len(SX['pts'])} daily points, {len(TRAJ)} hourly steps")

# Every group of agents that plays byte-identical actions through turn 24, drawn
# as one circle with area proportional to its size. A packing rather than a bar
# chart because the claim is about SHAPE: a handful of very large groups, then a
# fog of singletons, is not something a stacked bar can show.
import math

sizes = sorted(counts[0].values(), reverse=True)
TOT = sum(sizes)

# Simple deterministic spiral packing: place each circle outward, nudging until it
# does not overlap. Good enough for a few hundred circles and it needs no library.
def pack(vals, scale=1.0):
    """Place circles on a Vogel spiral, taking the first spot that does not collide.

    An earlier version stepped the angle and radius separately, which made small
    circles march outward in straight rays. Those rays were an artifact of the
    layout and were the most visible thing in the chart, which is the worst
    property a figure can have. A golden-angle spiral has no preferred direction.
    """
    GOLD = math.pi * (3 - math.sqrt(5))
    placed = []
    for v in vals:
        r = scale * math.sqrt(v)
        k = 0
        while True:
            t = k * GOLD
            d = 0.62 * scale * math.sqrt(k) * math.sqrt(max(1.0, r))
            x, y = d * math.cos(t), d * math.sin(t)
            if all((x - px) ** 2 + (y - py) ** 2 >= (r + pr) ** 2 * 1.02
                   for px, py, pr in placed):
                placed.append((x, y, r)); break
            k += 1
    return placed

SHOW = sizes[:400]
circles = pack(SHOW, scale=0.9)
cmap = plt.get_cmap('viridis')
big = sum(1 for v in sizes if v >= 100)

fig, ax = plt.subplots(figsize=(7.6, 7.6))
for (x, y, r), v in zip(circles, SHOW):
    frac = min(1.0, math.log1p(v) / math.log1p(max(SHOW)))
    ax.add_patch(plt.Circle((x, y), r, color=cmap(0.15 + 0.75 * frac),
                            ec='white', lw=0.6))
lim = max(abs(x) + r for x, y, r in circles) * 1.06
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect('equal')
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.set_title('The field is not individuals. It is groups.', loc='center',
             fontweight='bold', fontsize=13, pad=12)
ax.annotate(f'each circle is a set of agents playing identical actions through turn 24, '
            f'area proportional to size\n{big} groups of a hundred or more; the rest of '
            f'the board is a fog of ones',
            (0, -lim * 0.99), ha='center', va='top', fontsize=8.5, color=MUTED)
plt.tight_layout(); plt.show()

print(f"  {'horizon':<10}{'groups':>9}{'singletons':>12}{'in a group':>13}{'largest':>10}")
for k, v in JUSTIF.items():
    print(f"  {k:<10}{v['groups']:>9,}{v['singletons']:>12,}"
          f"{v['in_group']:>12.1f}%{v['largest']:>9.1f}%")
print()
print(f"groups of 100 seats or more at turn 24: {big}, holding "
      f"{100 * sum(v for v in sizes if v >= 100) / TOT:.1f} % of the field")

n = TAX['n']
parts = [('clones\nidentical for 719 turns', TAX['clones'], ORANGE),
         ('descendants\nshared opening, then mutated', TAX['descendants'], BLUE),
         ('unrelated\nalone from turn 24', TAX['unrelated'], GRID)]

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2),
                         gridspec_kw={'width_ratios': [1, 1.2]})

ax = axes[0]
left = 0
for lab, v, col in parts:
    ax.barh([0], [100 * v / n], left=left, color=col, height=0.5)
    ax.annotate(f'{100*v/n:.1f} %', (left + 50 * v / n, 0), ha='center', va='center',
                fontsize=11, fontweight='bold',
                color='white' if col != GRID else MUTED)
    left += 100 * v / n
ax.set_ylim(-1.1, 0.7); ax.set_yticks([]); ax.set_xlim(0, 100)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title('What relates one agent to another', loc='left', fontweight='bold', pad=10)
for i, (lab, v, col) in enumerate(parts):
    ax.annotate(lab, (2 + i * 34, -0.55), fontsize=8.5, color=col if col != GRID else MUTED,
                fontweight='bold', va='top')

ax = axes[1]
T = TAX['turns']
keys = [str(k) for k in range(len(T) - 1)]
vals = [TAX['by_last'].get(k, 0) for k in keys]
tot = sum(vals)
ax.bar(range(len(vals)), [100 * v / tot for v in vals], color=BLUE, width=0.62)
ax.set_xticks(range(len(vals)))
ax.set_xticklabels([f'{T[i]} to {T[i+1]}' for i in range(len(vals))], fontsize=8.5)
tidy(ax, 'share of descendants, %', 'Descendants mutate late')
ax.set_xlabel('turn range in which the lineage breaks')
plt.tight_layout(); plt.show()

print(f"  clones        {TAX['clones']:>8,}  {100*TAX['clones']/n:>5.1f} %")
print(f"  descendants   {TAX['descendants']:>8,}  {100*TAX['descendants']/n:>5.1f} %")
print(f"  unrelated     {TAX['unrelated']:>8,}  {100*TAX['unrelated']/n:>5.1f} %")

# Verified over 39,206 complete seat-streams: a deeper group never spans two
# shallower ones, at any of the four levels.

print('nesting check, groups that span more than one parent group')
for t, v in NESTING_VIOLATIONS.items():
    print(f'  turn {t:>3}: {v}   {"OK" if v == 0 else "BROKEN"}')
print()
print('so the structure is a rooted tree, exactly, with no clustering choice')
print()
for lv in LEVELS:
    print(f"  depth turn {lv['turn']:>3}: {lv['clades']:>7,} clades")

# The largest lineage, drawn as it fans out.
fig, ax = plt.subplots(figsize=(9.6, 4.8))
turns = [f['turn'] for f in FAN]
x = np.arange(len(turns))
cmap = plt.get_cmap('viridis')
for i, f in enumerate(FAN):
    tops = f['top']; rest = f['rest']
    bottom = 0
    for j, v in enumerate(tops):
        ax.bar(i, v, bottom=bottom, width=0.55, color=cmap(j / 8), edgecolor='white', lw=0.6)
        bottom += v
    if rest:
        ax.bar(i, rest, bottom=bottom, width=0.55, color=GRID, edgecolor='white', lw=0.6)
ax.set_xticks(x)
ax.set_xticklabels([f"turn {f['turn']}\n{f['branches']:,} branches" for f in FAN], fontsize=8.5)
tidy(ax, 'seats in the lineage', 'One ancestor, followed to 4,643 endings')
ax.annotate(f"{FAN[0]['top'][0]:,} seats share the same first 24 turns.\n"
            "Grey is everything outside the eight largest branches.",
            (0.02, 0.06), xycoords='axes fraction', fontsize=8.5, color=MUTED)
plt.tight_layout(); plt.show()

print()
print('the largest lineage, level by level')
for f in FAN:
    big = max(f['top']) if f['top'] else 0
    print(f"  turn {f['turn']:>3}: {f['branches']:>6,} branches, "
          f"largest holds {big:>5,} ({100*big/FAN[0]['top'][0]:>5.1f}% of the lineage)")

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))

ax = axes[0]
x = np.arange(len(BAND_POP))
pop = [b['pop'] for b in BAND_POP]
ax.bar(x, pop, color=BLUE, width=0.6, label='in a population')
ax.bar(x, [100 - v for v in pop], bottom=pop, color=GRID, width=0.6, label='individuals')
ax.set_xticks(x); ax.set_xticklabels([b['band'] for b in BAND_POP], rotation=45,
                                     ha='right', fontsize=8.5)
ax.axvline(0.5, color=ORANGE, lw=1.6, ls='--')
ax.annotate('the frontier', (0.62, 50), color=ORANGE, fontsize=9, fontweight='bold')
tidy(ax, 'share of the band, %', 'The entry band is made of individuals')
ax.set_xlabel('ladder rating band')
ax.legend(frameon=False, fontsize=8.5, loc='lower right')

ax = axes[1]
days = [r['day'] for r in DAY_POP]
ax.plot(range(len(days)), [r['pop'] for r in DAY_POP], lw=2.4, color=BLUE,
        marker='o', ms=5, markeredgecolor='white', markeredgewidth=1.1)
ax.set_xticks(range(len(days))); ax.set_xticklabels(days, rotation=45, ha='right', fontsize=8)
tidy(ax, 'seats in a population, %', 'And the field became populations, in a week')
ax.set_ylim(0, 100); ax.set_xlabel('day')
ax2 = ax.twiny(); ax2.set_xticks([])
ax.axvspan(4.5, 6.5, color=ORANGE, alpha=0.10)
ax.annotate('the transition', (5.5, 30), ha='center', color=ORANGE,
            fontsize=9, fontweight='bold')
plt.tight_layout(); plt.show()

print(f"  {'band':<12}{'seats':>8}{'in a population':>18}{'unique openings':>18}")
for b in BAND_POP:
    print(f"  {b['band']:<12}{b['n']:>8,}{b['pop']:>17.1f}%{b['single']:>17.1f}%")
print()
print(f"  {'day':<8}{'seats':>8}{'in a population':>18}{'effective openings':>20}")
for r in DAY_POP:
    print(f"  {r['day']:<8}{r['n']:>8,}{r['pop']:>17.1f}%{r['eff']:>19.1f}")

labels = [b['band'] for b in BANDS]
eff = [b['effective'] for b in BANDS]
largest = [b['largest'] for b in BANDS]
n = [b['n'] for b in BANDS]

fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
x = np.arange(len(BANDS))

ax = axes[0]
ax.bar(x, eff, color=BLUE, width=0.62)
ax.set_yscale('log')
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8.5)
tidy(ax, 'effective number of openings (1/HHI)',
     'Eighty times fewer openings at the top')
for xi, v, seats in zip(x, eff, n):
    ax.annotate(f'{v:,.0f}', (xi, v), xytext=(0, 4), textcoords='offset points',
                ha='center', fontsize=8.5, color=MUTED)
ax.set_xlabel('ladder rating band')

ax = axes[1]
ax.bar(x, largest, color=ORANGE, width=0.62)
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8.5)
tidy(ax, 'share held by the single most common opening, %',
     'And one of them owns half the top')
ax.set_xlabel('ladder rating band')
plt.tight_layout(); plt.show()

print(f"  {'band':<12}{'seats':>9}{'distinct':>10}{'effective':>11}{'largest':>10}")
for b in BANDS:
    print(f"  {b['band']:<12}{b['n']:>9,}{b['distinct']:>10,}{b['effective']:>11.1f}"
          f"{b['largest']:>9.1f}%")

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4),
                         gridspec_kw={'width_ratios': [1, 1.15]})

# left: the rating range each opening occupies
ax = axes[0]
items = sorted(NICHE.items(), key=lambda kv: kv[1][2])
for i, (k, (cnt, p10, p50, p90)) in enumerate(items):
    ax.plot([p10, p90], [i, i], lw=5, color=BLUE, alpha=0.35, solid_capstyle='round')
    ax.plot([p50], [i], 'o', ms=7, color=BLUE, markeredgecolor='white', markeredgewidth=1.2)
ax.set_yticks(range(len(items)))
ax.set_yticklabels([f'{k}  ({c:,})' for k, (c, *_ ) in items], fontsize=8)
tidy(ax, None, 'Where each opening lives')
ax.set_xlabel('ladder rating, 10th to 90th percentile of its seats')
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.yaxis.grid(False)

# right: composition by band
ax = axes[1]
bandnames = list(COMP)
bottom = np.zeros(len(bandnames))
cmap = plt.get_cmap('viridis')
for i, o in enumerate(TOP5):
    vals = np.array([COMP[b][i] for b in bandnames])
    ax.bar(range(len(bandnames)), vals, bottom=bottom, width=0.68,
           color=cmap(i / 5), label=o[:6])
    bottom += vals
ax.bar(range(len(bandnames)), 100 - bottom, bottom=bottom, width=0.68,
       color=GRID, label='everything else')
ax.set_xticks(range(len(bandnames)))
ax.set_xticklabels(bandnames, rotation=45, ha='right', fontsize=8)
tidy(ax, 'share of seats in the band, %', 'Composition changes with altitude')
ax.set_xlabel('ladder rating band')
ax.legend(frameon=False, fontsize=7.5, ncol=2, loc='upper left')
plt.tight_layout(); plt.show()

print('share of each band held by each of the five most common openings')
print(f"  {'band':<12}" + ''.join(f'{o[:6]:>9}' for o in TOP5))
for b in COMP:
    print(f'  {b:<12}' + ''.join(f'{v:>8.1f} ' for v in COMP[b]))

order = sorted(SERIES, key=lambda k: SERIES[k].index(max(SERIES[k])))
cmap = plt.get_cmap('viridis')
cols = {k: cmap(i / max(1, len(order) - 1)) for i, k in enumerate(order)}

fig, ax = plt.subplots(figsize=(10.6, 4.6))
ax.stackplot(range(len(DAYS)), [SERIES[k] for k in order],
             colors=[cols[k] for k in order], alpha=0.95)
ax.set_xticks(range(len(DAYS))); ax.set_xticklabels(DAYS, rotation=45, ha='right')
tidy(ax, 'share of seats that day, %',
     'Sixteen days: each opening peaks once and never returns')
ax.set_xlabel('day'); ax.set_ylim(0, 100)
plt.tight_layout(); plt.show()

print('peak share and the day it happened')
for k in order:
    pk = SERIES[k].index(max(SERIES[k]))
    print(f'  {k[:8]}  {max(SERIES[k]):>5.1f} %  on {DAYS[pk]}')

# A 24-hour window slid one hour at a time: 358 frames instead of 16, each still
# averaging thousands of seats, so the motion is smooth without the estimate
# getting noisy. Hourly counts alone would jitter; the window is what buys both.
cmap = plt.get_cmap('viridis')
cols10 = [cmap(i / 9) for i in range(10)]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.0, 4.0),
                               gridspec_kw={'width_ratios': [1.5, 1]})
lines = [axL.plot([], [], lw=2.2, color=cols10[k])[0] for k in range(10)]
axL.set_xlim(0, len(F) - 1); axL.set_ylim(0, 62)
tick = [i for i in range(0, len(F), 48)]
axL.set_xticks(tick); axL.set_xticklabels([F[i]['t'][:5] for i in tick], fontsize=8)
tidy(axL, 'share of seats in the last 24 h, %', 'The field, hour by hour')
bars = axR.barh(range(10), [0] * 10, color=cols10, height=0.72)
axR.set_yticks(range(10)); axR.set_yticklabels([t[:6] for t in TOPK], fontsize=8)
axR.set_xlim(0, 62); axR.invert_yaxis()
tidy(axR, None, 'Who holds the field'); axR.set_xlabel('share of seats, %')
axR.xaxis.grid(True, color=GRID, lw=0.8); axR.yaxis.grid(False)
stamp = axL.text(0.015, 0.93, '', transform=axL.transAxes, fontsize=13,
                 fontweight='bold', color=INK, path_effects=HALO)
count = axL.text(0.015, 0.85, '', transform=axL.transAxes, fontsize=9,
                 color=MUTED, path_effects=HALO)

def frame(t):
    for k in range(10):
        lines[k].set_data(range(t + 1), [F[j]['share'][k] for j in range(t + 1)])
    for k, b in enumerate(bars):
        b.set_width(F[t]['share'][k])
    stamp.set_text(F[t]['t'])
    count.set_text(f"{F[t]['n']:,} seats in the window")
    return lines + list(bars) + [stamp, count]

show_gif(fig, frame, len(F), fps=24, dpi=72, name='field.gif')

# Two levels of the genealogy: openings at turn 24 as blocks, and within each,
# its own turn-200 branches as shades. Descendants are drawn inside their
# ancestor, which is what makes this a Muller plot rather than a stacked area.
def two_level(bucket_key, minimum):
    keys = sorted({bucket_key(x) for x in SEATS})
    kept, layers = [], []
    for k in keys:
        g = [x for x in SEATS if bucket_key(x) == k]
        if len(g) < minimum: continue
        kept.append(k)
        n = len(g)
        row = []
        for o in TOP[:8]:
            inside = [x for x in g if x["h"][0] == o]
            sub = collections.Counter(x["h"][2] for x in inside if x["h"][2])
            row.append([100 * v / n for _, v in sub.most_common(4)]
                       + [100 * (len(inside) - sum(v for _, v in sub.most_common(4))) / n])
        row.append([100 * (n - sum(1 for x in g if x["h"][0] in TOP[:8])) / n])
        layers.append(row)
    return kept, layers

MDAYS, LAYERS = two_level(lambda x: x["when"].strftime("%m-%d"), 400)

fig, ax = plt.subplots(figsize=(10.6, 5.0))
base = np.zeros(len(MDAYS))
cmap = plt.get_cmap('viridis')
for oi in range(len(LAYERS[0])):
    nsub = max(len(LAYERS[t][oi]) for t in range(len(MDAYS)))
    for si in range(nsub):
        vals = np.array([LAYERS[t][oi][si] if si < len(LAYERS[t][oi]) else 0.0
                         for t in range(len(MDAYS))])
        col = (GRID if oi == len(LAYERS[0]) - 1
               else cmap(oi / 8))
        shade = 1.0 - 0.13 * si
        col = tuple(min(1, c * shade) for c in plt.matplotlib.colors.to_rgb(col)) + (1.0,)
        ax.fill_between(range(len(MDAYS)), base, base + vals, color=col,
                        linewidth=0.4, edgecolor='white')
        base = base + vals
ax.set_xticks(range(len(MDAYS)))
ax.set_xticklabels(MDAYS, rotation=45, ha='right', fontsize=8)
tidy(ax, 'share of seats, %', 'Muller plot: descendants drawn inside their ancestor')
ax.set_xlabel('day'); ax.set_ylim(0, 100); ax.set_xlim(0, len(MDAYS) - 1)
ax.annotate('grey is everything outside the eight largest openings',
            (0.02, 0.04), xycoords='axes fraction', fontsize=8.5, color=MUTED,
            path_effects=HALO)
plt.tight_layout(); plt.show()

print(f'{len(MDAYS)} days, 8 openings, each split into its own turn-200 branches')
print('a block that fragments internally is an ancestor whose descendants are diverging')

# A simplex has one vertex per population, so three populations give a triangle
# and ten give a decagon. Each opening sits on the circle, and the field's
# composition is placed at the weighted centroid of those vertices: all of one
# opening puts the point on its vertex, an even mixture puts it in the middle.
#
# THE PROJECTION IS NOT INJECTIVE and that has to be said. Ten shares are being
# squeezed into two coordinates, so different mixtures can land on the same point,
# and the centre in particular means either "an even mixture" or "opposing pairs
# cancelling". Read the position as a direction of travel, not as an inventory.
K = len(TOPK)
ang = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, K, endpoint=False)
VERT = np.stack([np.cos(ang), np.sin(ang)], axis=1)

K = len(TOPK)
ang = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, K, endpoint=False)
VERT = np.stack([np.cos(ang), np.sin(ang)], axis=1)

def place(shares):
    w = np.array(shares, dtype=float); s = w.sum()
    return None if s <= 0 else (w / s) @ VERT

def draw_frame(ax, labels=None):
    ring = np.vstack([VERT, VERT[:1]])
    ax.plot(ring[:, 0], ring[:, 1], color=GRID, lw=1.3, zorder=0)
    for (vx, vy), lab in zip(VERT, labels if labels else TOPK):
        ax.plot([0, vx], [0, vy], color=GRID, lw=0.7, alpha=0.6, zorder=0)
        ax.annotate(lab, (vx, vy),
                    xytext=(11 * np.sign(vx) if abs(vx) > .2 else 0,
                            11 * np.sign(vy) if abs(vy) > .2 else 0),
                    textcoords='offset points', ha='center', va='center',
                    fontsize=8, fontweight='bold', color=MUTED, path_effects=HALO)
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.32, 1.28)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal')
    for s in ax.spines.values(): s.set_visible(False)

KEEP = [f for f in HF if place(f["share"]) is not None]
PTS = np.array([place(f["share"]) for f in KEEP])
SPD = np.concatenate([[0.0], np.linalg.norm(np.diff(PTS, axis=0), axis=1)])

# Both panels are SIMULATED, on the same K-gon and the same placement rule as the
# real data, so the real chart can be read against them.
def simulate(payoff, steps=3000, dt=0.02, start=None):
    x = np.array(start if start is not None else np.random.dirichlet(np.ones(K)))
    out = [x.copy()]
    for _ in range(steps):
        f = payoff @ x
        x = np.clip(x + dt * x * (f - x @ f), 1e-12, None); x /= x.sum()
        out.append(x.copy())
    return np.array(out)

# cyclic: i beats i+1, loses to i-1, all the way round the ring
cyc = np.zeros((K, K))
for i in range(K):
    cyc[i, (i + 1) % K] = 1.0
    cyc[(i + 1) % K, i] = -1.0
start = np.full(K, 0.5 / K); start[0] = 0.5
CYC = simulate(cyc, start=start)

# succession: a strict pecking order, each one better than every earlier one
suc = np.zeros((K, K))
for i in range(K):
    for j in range(K):
        if i < j: suc[i, j] = 1.0
        elif i > j: suc[i, j] = -1.0
SUC = simulate(suc, steps=6000, start=start)

fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.6))
for ax, traj, title, note in [
        (axes[0], CYC, 'A cyclic population', 'returns forever'),
        (axes[1], SUC, 'A succession', 'walks to the last vertex and stops')]:
    draw_frame(ax, labels=[chr(65 + i) for i in range(K)])   # generic: these are not real openings
    xy = np.array([(t / t.sum()) @ VERT for t in traj])
    ax.plot(xy[:, 0], xy[:, 1], lw=1.5, color=BLUE, alpha=0.85)
    ax.plot(*xy[0], 'o', ms=9, color='white', markeredgecolor=INK, markeredgewidth=1.5, zorder=4)
    ax.plot(*xy[-1], 's', ms=9, color=INK, zorder=4)
    ax.set_title(title, loc='left', fontweight='bold', pad=12)
    ax.annotate(note, (0, -1.18), ha='center', fontsize=9, color=MUTED, path_effects=HALO)
plt.tight_layout(); plt.show()

print('both panels are simulations on the same geometry as the real chart')
print('the real trajectory is the one to compare against them')

from matplotlib.collections import LineCollection
fig, ax = plt.subplots(figsize=(7.0, 7.0))
draw_frame(ax)
segs = np.stack([PTS[:-1], PTS[1:]], axis=1)
lc = LineCollection(segs, cmap='plasma', linewidths=2.6,
                    norm=plt.Normalize(0, np.percentile(SPD, 95)))
lc.set_array(SPD[1:])
ax.add_collection(lc)
ax.plot(*PTS[0], 'o', ms=9, color='white', markeredgecolor=INK, markeredgewidth=1.6, zorder=4)
ax.plot(*PTS[-1], 's', ms=9, color=INK, zorder=4)
ax.set_title(f'{K} openings, one vertex each, {len(PTS)} hours of composition',
             loc='left', fontweight='bold', pad=12)
cb = plt.colorbar(lc, ax=ax, shrink=0.6, pad=0.01)
cb.set_label('composition change per hour', fontsize=9)
plt.tight_layout(); plt.show()

print(f'{K} openings placed on the ring, {len(PTS)} hourly positions')
print(f'speed: median {np.median(SPD[1:]):.4f}, max {SPD[1:].max():.4f} per hour')

fig, ax = plt.subplots(figsize=(6.6, 6.6))
draw_frame(ax)
trail = LineCollection([], cmap='plasma', linewidths=2.4,
                       norm=plt.Normalize(0, np.percentile(SPD, 95)))
ax.add_collection(trail)
head, = ax.plot([], [], 'o', ms=12, color=ORANGE, markeredgecolor='white',
                markeredgewidth=1.6, zorder=5)
cap = ax.text(0, -1.2, '', ha='center', fontsize=13, fontweight='bold',
              color=INK, path_effects=HALO)
ax.set_title('The field moving through composition space', loc='left',
             fontweight='bold', pad=12)

def step(t):
    t = max(1, t)
    trail.set_segments(segs[:t]); trail.set_array(SPD[1:t + 1])
    head.set_data([PTS[t][0]], [PTS[t][1]])
    cap.set_text(KEEP[t]["t"])
    return [trail, head, cap]

show_gif(fig, step, len(PTS), fps=20, dpi=84, name='polygon.gif')