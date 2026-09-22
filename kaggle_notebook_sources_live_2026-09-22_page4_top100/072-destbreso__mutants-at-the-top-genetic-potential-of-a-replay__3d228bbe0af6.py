import json, sys, warnings
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

warnings.filterwarnings("ignore")

# Team names here are Japanese, Cyrillic and Latin. Matplotlib's default font
# covers Cyrillic and draws empty boxes for CJK, which is how the first version
# of this notebook published its most interesting agent with no readable name.
# Use a CJK capable font if the image has one, and label by rank and submission
# when it does not, rather than printing tofu.
from matplotlib import font_manager

def _cjk_font():
    have = {f.name for f in font_manager.fontManager.ttflist}
    for n in ("Noto Sans CJK JP", "Noto Sans JP", "IPAGothic", "TakaoGothic",
              "Hiragino Sans", "Arial Unicode MS", "Noto Sans CJK SC"):
        if n in have:
            return n
    return None

CJK = _cjk_font()
if CJK:
    plt.rcParams["font.sans-serif"] = [CJK] + list(
        plt.rcParams.get("font.sans-serif", []))
print("CJK capable font:", CJK or "none, falling back to rank and submission id")

def flabel(team, rank, sub):
    """A label that will actually render in a figure."""
    if CJK or all(ord(c) < 0x2E80 for c in str(team)):
        return str(team)
    return f"team {sub}"

# Find the data by looking for it, never by hardcoding a path. A previous
# notebook in this series died at cell one because an input was mounted under a
# different directory than the one written into the code.
def find_dir(marker, roots=("/kaggle/input", ".", "..", "data")):
    hits = []
    for r in roots:
        p = Path(r)
        if p.exists():
            hits += [q.parent for q in p.rglob(marker)]
    if not hits:
        raise FileNotFoundError(
            f"could not find {marker!r} under {roots}. Attach the dataset.")
    return sorted(hits, key=lambda q: len(str(q)))[0]

BASE = find_dir("streams.parquet")
print("reading from", BASE)

episodes = pd.read_csv(BASE / "episodes.csv",
                       dtype={"episode_id": str, "submission": str})
streams = pd.read_parquet(BASE / "streams.parquet")
streams["episode_id"] = streams["episode_id"].astype(str)
streams["submission"] = streams["submission"].astype(str)

print(f"{len(episodes):,} episodes, {len(streams):,} turns, "
      f"{episodes.submission.nunique()} submissions")

per_sub = (episodes.groupby(["submission", "rank_at_snapshot", "team", "ladder_score"])
           .agg(episodes=("episode_id", "size"),
                opponents=("opponent", "nunique"),
                seat0=("seat", lambda s: int((s == 0).sum())),
                median_bank=("bank", "median"))
           .reset_index().sort_values("rank_at_snapshot"))
per_sub["seat1"] = per_sub.episodes - per_sub.seat0
display(per_sub[["rank_at_snapshot", "team", "ladder_score", "submission",
                 "episodes", "opponents", "seat0", "seat1", "median_bank"]]
        .rename(columns={"rank_at_snapshot": "rank"})
        .style.hide(axis="index").format({"median_bank": "{:,.0f}"}))

PER_SUB = 90     # episodes considered per submission, before the seat split

streams["plan"] = streams["farmer"] + "|" + streams["hands_h"]
# Key on the PAIR: an episode played between two of these ten submissions
# appears twice, once per seat, and grouping on the episode id alone silently
# concatenates them into one 1,440 turn stream.
by_ep = {k: g.sort_values("turn")
         for k, g in streams.groupby(["submission", "episode_id"])}

def pool_for(sub):
    e = episodes[episodes.submission == sub].sort_values("episode_id").head(PER_SUB)
    seat = int(e.seat.value_counts().idxmax())
    e = e[e.seat == seat]
    out = []
    for _, r in e.iterrows():
        g = by_ep[(sub, r.episode_id)]
        out.append({"episode": r.episode_id, "seat": seat, "opponent": r.opponent,
                    "bank": r.bank, "plan": list(g.plan), "market": list(g.market)})
    return out

def medoid(pool):
    score = []
    for i, a in enumerate(pool):
        s = sum(SequenceMatcher(a=a["plan"], b=b["plan"], autojunk=False).ratio()
                for j, b in enumerate(pool) if i != j)
        score.append((s / (len(pool) - 1), i))
    score.sort(reverse=True)
    return pool[score[0][1]], score[0][0], score[0][0] - score[1][0]

pools = {s: pool_for(s) for s in per_sub.submission}
bases = {s: medoid(p) for s, p in pools.items()}

tab = []
for _, r in per_sub.iterrows():
    b, sc, mg = bases[r.submission]
    tab.append({"rank": r.rank_at_snapshot, "team": r.team, "seat": b["seat"],
                "episodes used": len(pools[r.submission]),
                "baseline episode": b["episode"],
                "medoid score": round(sc, 4), "margin over runner up": round(mg, 5)})
display(pd.DataFrame(tab).style.hide(axis="index"))

SAME, MUT, PLAN = "#DCEEE1", "#B45309", "#0F172A"
CMAP = ListedColormap([SAME, MUT, PLAN])
STATE = {"G": 0, "Y": 1, "R": 2}

def align(a, b):
    m = {}
    for i, j, n in SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(n):
            m[i + k] = j + k
    return m

def classify(sub):
    base, _, _ = bases[sub]
    rows, shifts, moved, unaligned = [], [], 0, 0
    for o in pools[sub]:
        if o is base:
            continue
        m = align(base["plan"], o["plan"])
        st = []
        for i in range(len(base["plan"])):
            j = m.get(i)
            if j is None:
                st.append("R")
            else:
                shifts.append(j - i)
                st.append("G" if base["market"][i] == o["market"][j] else "Y")
        rows.append("".join(st))
        used = set(m.values())
        left = Counter(base["plan"][i] for i in range(len(base["plan"])) if i not in m)
        right = Counter(o["plan"][j] for j in range(len(o["plan"])) if j not in used)
        moved += sum((left & right).values())
        unaligned += sum(left.values())
    n = len(base["plan"])
    per_turn = [Counter(r[i] for r in rows) for i in range(n)]
    empty = (json.dumps(None), json.dumps([]))
    free = [i for i, c in enumerate(per_turn) if c["R"] == 0 and c["Y"] > 0]
    frozen = [i for i, c in enumerate(per_turn) if c["R"] == 0 and c["Y"] == 0]
    broken = [i for i, c in enumerate(per_turn) if c["R"] > 0]
    traded = [i for i in frozen if base["market"][i] not in empty]
    return {"base": base, "rows": rows, "per_turn": per_turn, "turns": n,
            "free": free, "frozen": frozen, "broken": broken,
            "frozen_traded": traded, "shifts": shifts,
            "moved": moved, "unaligned": unaligned}

surf = {s: classify(s) for s in per_sub.submission}
print("classified", sum(len(v["rows"]) for v in surf.values()),
      "episode comparisons against 10 baselines")

order = per_sub.sort_values("rank_at_snapshot")
name = {sub: flabel(t, r, sub) for sub, t, r
        in zip(order.submission, order.team, order.rank_at_snapshot)}
rank = dict(zip(order.submission, order.rank_at_snapshot))

show = [order.submission.iloc[1], order.submission.iloc[7],
        order.submission.iloc[8], order.submission.iloc[0]]

fig, axes = plt.subplots(len(show), 1, figsize=(13.5, 9.2),
                         gridspec_kw={"hspace": 0.55})
for ax, sub in zip(axes, show):
    v = surf[sub]
    M = np.array([[STATE[c] for c in r] for r in v["rows"]], dtype=np.int8)
    ax.imshow(M, aspect="auto", cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
    pct = 100 * len(v["free"]) / v["turns"]
    ax.set_title(f"#{rank[sub]}  {name[sub]}      "
                 f"{len(v['rows'])} episodes against baseline {v['base']['episode']}"
                 f"      mutable on {len(v['free'])} turns ({pct:.0f}% of the episode)",
                 loc="left", fontsize=10.5, pad=6)
    ax.set_ylabel("episode", fontsize=9)
    ax.set_xlim(0, v["turns"])
    for d in range(0, 721, 120):
        ax.axvline(d, color="white", lw=0.6, alpha=0.35)
    ax.tick_params(labelsize=8)
axes[-1].set_xlabel("turn  (720 turns = 30 in game days, gridlines every 5 days)",
                    fontsize=9)
fig.legend(handles=[Patch(facecolor=SAME, label="same as baseline"),
                    Patch(facecolor=MUT, label="market mutation observed"),
                    Patch(facecolor=PLAN, label="plan differs, off limits")],
           loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=3, frameon=False,
           fontsize=10)
fig.suptitle("Every episode of an agent, aligned against one of its own",
             y=1.055, fontsize=13.5)
plt.show()

rows = []
for _, r in order.iterrows():
    v = surf[r.submission]
    n = v["turns"]
    trading = len(v["free"]) + len(v["frozen_traded"])
    rows.append({
        "rank": r.rank_at_snapshot, "team": r.team,
        "medoid": round(bases[r.submission][1], 3),
        "plan aligned everywhere": len(v["free"]) + len(v["frozen"]),
        "mutable turns": len(v["free"]),
        "mutable % of episode": round(100 * len(v["free"]) / n, 1),
        "turns the baseline trades": trading,
        "mutable % of trading turns": round(100 * len(v["free"]) / trading, 1) if trading else 0.0,
        "off limits": len(v["broken"]),
    })
gen = pd.DataFrame(rows)
display(gen.sort_values("mutable turns", ascending=False)
        .style.hide(axis="index")
        .background_gradient(subset=["mutable % of episode"], cmap="Oranges"))

fig, ax = plt.subplots(figsize=(11.5, 5.0))
o = gen.sort_values("mutable turns")
y = np.arange(len(o))
free = o["mutable turns"].values
froz = o["plan aligned everywhere"].values - free
off = o["off limits"].values

ax.barh(y, free, color=MUT, label="market mutation observed", height=0.66)
ax.barh(y, froz, left=free, color=SAME, label="plan held, market never varied",
        height=0.66, edgecolor="white", linewidth=0.8)
ax.barh(y, off, left=free + froz, color=PLAN, label="plan differs, off limits",
        height=0.66, edgecolor="white", linewidth=0.8)
ax.set_yticks(y)
ax.set_yticklabels([f"#{r}  {t[:26]}" for r, t in zip(o["rank"], o["team"])],
                   fontsize=9)
for i, f in enumerate(free):
    ax.text(f + 8, i, f"{f}", va="center", fontsize=9, color="#0F172A")
ax.set_xlabel("turns of the 720 turn episode", fontsize=9.5)
ax.set_xlim(0, 760)
ax.set_title("How much of each route is free for a market only change",
             loc="left", fontsize=12.5, pad=10)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(left=False, labelsize=9)
plt.show()

boards = pd.read_csv(BASE / "boards.csv", dtype={"episode_id": str, "submission": str})

def worst_board_gap(sub):
    """Largest tile disagreement between any two final boards, within a seat.

    Distance rather than identity, because "two distinct boards" is a blunt
    test: a hundred tiles differing in one is the same plan with a weed in the
    way, and a hundred differing in forty is a different farm.
    """
    b = boards[boards.submission == sub].merge(
        episodes[["submission", "episode_id", "seat"]],
        on=["submission", "episode_id"], suffixes=("", "_e"))
    worst = 0
    for seat, g in b.groupby("seat"):
        keys = [str(x).split("/")[0].replace("|", ",").split(",") for x in g.board]
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if len(keys[i]) == len(keys[j]):
                    worst = max(worst, sum(1 for a, c in zip(keys[i], keys[j]) if a != c))
    return worst

gen["worst board gap (tiles of 100)"] = [worst_board_gap(s) for s in order.submission]

# the plan axis: fixed if the farms it builds barely move between episodes
gen["plan fixed"] = gen["worst board gap (tiles of 100)"] <= 15
gen["market reactive"] = gen["mutable turns"] > 100

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3))
panels = [("medoid", "medoid score of the baseline", (0.4, 1.02)),
          ("worst board gap (tiles of 100)", "worst final board gap, tiles", None),
          ("mutable % of episode", "mutable share of the episode, %", None)]
for k, (ax, (col, lab, xlim)) in enumerate(zip(axes, panels)):
    v = gen.sort_values(col)
    colours = [MUT if a else (SAME if b else PLAN)
               for a, b in zip(v["market reactive"], v["plan fixed"])]
    ax.scatter(v[col], np.linspace(-0.2, 0.2, len(v)), c=colours, s=115,
               edgecolor="#334155", linewidth=0.7, zorder=3)
    for x, yy, r in zip(v[col], np.linspace(-0.2, 0.2, len(v)), v["rank"]):
        ax.annotate(f"#{r}", (x, yy), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8.5, color="#334155")
    ax.set_xlabel(lab, fontsize=9.5)
    ax.set_yticks([])
    ax.set_ylim(-0.55, 0.55)
    if xlim:
        ax.set_xlim(*xlim)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9)
axes[0].set_ylabel("the ten agents", fontsize=9)
fig.legend(handles=[Patch(facecolor=MUT, label="plan fixed, market reactive"),
                    Patch(facecolor=SAME, label="plan fixed, market near constant"),
                    Patch(facecolor=PLAN, label="plan moves")],
           loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=3, frameon=False,
           fontsize=9.5)
fig.suptitle("Two of these three agree on a partition. The third splits it again.",
             y=1.02, fontsize=13)
plt.tight_layout()
plt.show()

fixed = gen[gen["plan fixed"]].sort_values("rank")
moves = gen[~gen["plan fixed"]].sort_values("rank")

# The two axes crossed, printed rather than asserted, because which of the four
# cells is the empty one is the whole claim of this section.
cells = pd.crosstab(gen["plan fixed"], gen["market reactive"])
print("the two axes crossed, agents per cell")
print(cells.rename_axis(index="plan fixed", columns="market reactive"), "\n")

for label, grp in (("plan FIXED", fixed), ("plan MOVES", moves)):
    print(f"{label} ({len(grp)}): ranks {list(grp['rank'])}")
    print(f"   medoid         {sorted(grp['medoid'])}")
    print(f"   board gap      {sorted(grp['worst board gap (tiles of 100)'])}")
    print(f"   mutable turns  {sorted(grp['mutable turns'])}\n")
odd = fixed[~fixed["market reactive"]]
for _, r in odd.iterrows():
    print(f"the exception: #{r['rank']} {r['team']} holds its plan to "
          f"{r['worst board gap (tiles of 100)']} tiles and a medoid of {r['medoid']}, "
          f"yet varies its market on only {r['mutable turns']} turns, "
          f"{r['mutable % of trading turns']} % of the turns it trades on.")

top = gen[gen["rank"] == 1].iloc[0]
rest = gen[gen["rank"] != 1]
scores = per_sub.set_index("rank_at_snapshot")["ladder_score"].astype(float)
distinct = (boards.groupby(["submission", "seat"]).board_h.nunique()
            .rename("distinct boards").reset_index()
            .merge(per_sub[["submission", "rank_at_snapshot", "team"]], on="submission"))

print(f"rank 1 is {scores.loc[1] - scores.loc[2]:,.1f} rating points clear of rank 2, "
      f"which is more than ranks 2 to 10 span between them "
      f"({scores.loc[2] - scores.loc[10]:,.1f}).\n")
for col in ("medoid", "plan aligned everywhere", "mutable % of episode",
            "worst board gap (tiles of 100)"):
    print(f"  {col:<32} rank 1 = {top[col]:>8}   "
          f"rest of the field {rest[col].min()} to {rest[col].max()}")
print()
d1 = distinct[distinct.rank_at_snapshot == 1]
print("distinct final boards, rank 1 by seat:",
      ", ".join(f"seat {int(r.seat)}: {int(r['distinct boards'])}"
                for _, r in d1.iterrows()))
print("the same figure for everyone else ranges "
      f"{distinct[distinct.rank_at_snapshot != 1]['distinct boards'].min()} to "
      f"{distinct[distinct.rank_at_snapshot != 1]['distinct boards'].max()}")

rows = []
for _, r in order.iterrows():
    v = surf[r.submission]
    sh = Counter(v["shifts"])
    tot = sum(sh.values())
    rows.append({
        "rank": r.rank_at_snapshot, "team": r.team,
        "matched positions": tot,
        "at zero offset": sh.get(0, 0),
        "% at zero offset": round(100 * sh.get(0, 0) / tot, 2) if tot else 0.0,
        "largest offset seen": max([abs(k) for k in sh if k != 0], default=0),
        "unaligned plan actions": v["unaligned"],
        "explainable as a move": v["moved"],
        "% explainable as a move": round(100 * v["moved"] / v["unaligned"], 2)
                                   if v["unaligned"] else 0.0,
    })
sh = pd.DataFrame(rows)
display(sh.style.hide(axis="index"))

print(f"across all ten agents, {sh['at zero offset'].sum():,} of "
      f"{sh['matched positions'].sum():,} matched positions "
      f"({100*sh['at zero offset'].sum()/sh['matched positions'].sum():.2f} %) "
      f"sit at the same index")
print(f"and {sh['explainable as a move'].sum():,} of "
      f"{sh['unaligned plan actions'].sum():,} unaligned plan actions "
      f"({100*sh['explainable as a move'].sum()/sh['unaligned plan actions'].sum():.2f} %) "
      f"could be explained by a block having moved")

VISIBLE_AT = 136   # the turn at which the opponent first becomes observable

fig, ax = plt.subplots(figsize=(13.5, 4.6))
for k, (_, r) in enumerate(order.iterrows()):
    v = surf[r.submission]
    marks = np.array(v["free"])
    y = len(order) - k
    ax.scatter(marks, np.full(len(marks), y), s=9, marker="|",
               color=MUT if len(v["free"]) > 100 else "#94A3B8")
ax.axvline(VISIBLE_AT, color=PLAN, lw=1.4, ls="--")
ax.text(VISIBLE_AT + 6, len(order) + 0.45,
        "opponent first observable", fontsize=9, color=PLAN)
ax.set_yticks(range(1, len(order) + 1))
ax.set_yticklabels([f"#{r}  {name[s][:24]}" for r, s in
                    zip(order.rank_at_snapshot[::-1], order.submission[::-1])],
                   fontsize=9)
ax.set_xlim(0, 720)
ax.set_xlabel("turn", fontsize=9.5)
ax.set_title("Where the mutable turns sit in the episode",
             loc="left", fontsize=12.5, pad=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(left=False, labelsize=9)
plt.show()

for _, r in order.iterrows():
    v = surf[r.submission]
    f = np.array(v["free"])
    if len(f) == 0:
        continue
    print(f"#{r.rank_at_snapshot:>2} {r.team[:26]:<28} "
          f"{len(f):>3} mutable turns | "
          f"{int((f < VISIBLE_AT).sum()):>3} before the opponent is visible | "
          f"first at turn {int(f.min()):>3}, last at turn {int(f.max()):>3}")