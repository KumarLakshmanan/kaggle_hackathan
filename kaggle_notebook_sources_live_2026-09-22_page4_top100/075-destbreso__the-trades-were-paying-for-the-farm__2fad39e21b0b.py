import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

warnings.filterwarnings("ignore")
plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 120,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
})

# One palette for the series. Checked for monotone lightness so the three stay
# separable in greyscale and under the common colour-vision deficiencies.
SELL  = "#0F766E"   # the trading channel
INPUT = "#B45309"   # seeds and bought goods
STRUCT= "#0F172A"   # hire, land, animals: the channel that is really plan
NULL  = "#94A3B8"   # the shuffled baseline
ACC   = "#B91C1C"

def find_dir(marker, roots=("/kaggle/input", ".", "..", "data")):
    hits = []
    for r in roots:
        p = Path(r)
        if p.exists():
            hits += [q.parent for q in p.rglob(marker)]
    if not hits:
        raise SystemExit(f"could not find {marker}")
    return sorted(hits, key=lambda q: len(str(q)))[0]

DATA = find_dir("streams.parquet")
print("dataset:", DATA)

streams = pd.read_parquet(DATA / "streams.parquet")
episodes = pd.read_csv(DATA / "episodes.csv")
print(f"{len(streams):,} turns, {streams.episode_id.nunique():,} episodes, "
      f"{streams.submission.nunique()} submissions")

# Rank and team name, so the figures can be read without a lookup table.
RANK = (episodes.drop_duplicates("submission")
        .set_index("submission")[["rank", "team"]].to_dict("index")
        if {"rank", "team"} <= set(episodes.columns) else {})

def has_cjk(s):
    return any("⺀" <= ch <= "鿿" or "가" <= ch <= "힯" for ch in str(s))

def label(sub):
    meta = RANK.get(sub) or RANK.get(int(sub)) or {}
    r, t = meta.get("rank"), str(meta.get("team", sub))
    # Kaggle's images carry no CJK font, so a name that would render as tofu is
    # replaced by its submission id rather than by four empty boxes.
    if has_cjk(t) or not t or t == "nan":
        t = f"team {sub}"
    return f"{r}. {t[:18]}" if r else t[:20]

# The table above, as data. One definition, so the panels and the table cannot
# disagree; the highlight under the milk panel is computed from it.
PHENO = [('quadrants unlocked', 3, 2), ('LOCKED tiles at the end', 25, 50), ('MILK units sold', 320, 70), ('board tiles differing from the parent', 0, 32)]
P = {q: (a, b) for q, a, b in PHENO}
milk_lost = 1 - P["MILK units sold"][1] / P["MILK units sold"][0]

fig, axes = plt.subplots(1, 3, figsize=(11, 3.1))
for ax, (title, key, hi) in zip(axes, [
        ("LOCKED tiles", "LOCKED tiles at the end", "a whole quadrant, all season"),
        ("MILK units sold", "MILK units sold", f"{milk_lost:.0%} of the herd's output"),
        ("board tiles wrong", "board tiles differing from the parent",
         "the plan was replayed verbatim")]):
    a, b = P[key]
    ax.bar([0, 1], [a, b], color=[STRUCT, ACC], width=0.55)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["route", "knockout"])
    ax.set_title(title); ax.set_ylabel("")
    ax.text(0.5, max(a, b) * 1.02, hi, ha="center", va="bottom",
            fontsize=8, color="#475569")
    ax.set_ylim(0, max(a, b) * 1.28)
fig.suptitle("Deleting the trades broke the construction, not the trading",
             y=1.06, fontsize=12, fontweight="bold")
plt.tight_layout(); plt.show()

STRUCTURAL = {"BUY_LAND", "BUY_ANIMAL"}
PURCHASE   = {"BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "HIRE"}

def ops_of(s):
    if not s or s == "null":
        return []
    try:
        o = json.loads(s)
    except Exception:
        return []
    return [x[0] for x in o if isinstance(x, list) and x] if isinstance(o, list) else []

rows = []
for sub, g in streams.groupby("submission"):
    n = ns = a = b = 0
    for s in g["market"]:
        ops = ops_of(s)
        n += 1
        sell = "SELL" in ops
        ns += sell
        if STRUCTURAL & set(ops):
            a += 1; b += sell
    if a:
        rows.append({"submission": sub, "turns": n, "p_sell": ns / n,
                     "struct_turns": a, "p_sell_given_struct": b / a,
                     "lift": (b / a) / (ns / n)})
cond = pd.DataFrame(rows).sort_values("lift", ascending=False).reset_index(drop=True)
cond["agent"] = cond.submission.map(label)
display(cond[["agent", "turns", "p_sell", "struct_turns",
              "p_sell_given_struct", "lift"]]
        .style.format({"turns": "{:,}", "struct_turns": "{:,}",
                       "p_sell": "{:.1%}", "p_sell_given_struct": "{:.1%}",
                       "lift": "{:.2f}x"}))

tot_turns = cond.turns.sum()
tot_sell  = (cond.p_sell * cond.turns).sum()
tot_st    = cond.struct_turns.sum()
tot_stsell= (cond.p_sell_given_struct * cond.struct_turns).sum()
print(f"\nALL TEN: {tot_sell/tot_turns:.1%} of {tot_turns:,} turns carry a sell, "
      f"against {tot_stsell/tot_st:.1%} of the {tot_st:,} turns that buy land or an animal")

d = cond.sort_values("p_sell_given_struct")
y = np.arange(len(d))
fig, ax = plt.subplots(figsize=(8.4, 4.2))
ax.hlines(y, d.p_sell, d.p_sell_given_struct, color="#CBD5E1", lw=3, zorder=1)
ax.scatter(d.p_sell, y, s=70, color=NULL, zorder=3, label="any turn")
ax.scatter(d.p_sell_given_struct, y, s=70, color=SELL, zorder=3,
           label="a turn that buys land or an animal")
for yy, (lo, hi) in enumerate(zip(d.p_sell, d.p_sell_given_struct)):
    ax.text(hi + 0.015, yy, f"{hi/lo:.1f}x", va="center", fontsize=8.5,
            color=SELL, fontweight="bold")
ax.set_yticks(y); ax.set_yticklabels([label(s) for s in d.submission], fontsize=8.5)
ax.set_xlim(0, 1.0)
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
ax.set_xlabel("share of turns carrying at least one SELL order")
ax.set_title("Every one of the ten sells about twice as often on the turns it buys",
             loc="left")
ax.legend(loc="lower right", frameon=False, fontsize=9)
plt.tight_layout(); plt.show()

import random
random.seed(7)

rows = []
for sub, g in streams.groupby("submission"):
    n = first = null_n = null_hit = 0
    for s in g["market"]:
        ops = ops_of(s)
        if "SELL" not in ops:
            continue
        st = [i for i, o in enumerate(ops) if o in STRUCTURAL]
        if not st:
            continue
        sells = [i for i, o in enumerate(ops) if o == "SELL"]
        n += 1
        first += min(sells) < max(st)
        p = list(ops); random.shuffle(p)
        ps = [i for i, o in enumerate(p) if o == "SELL"]
        pb = [i for i, o in enumerate(p) if o in STRUCTURAL]
        if ps and pb:
            null_n += 1; null_hit += min(ps) < max(pb)
    if n:
        rows.append({"submission": sub, "turns": n, "sell_first": first / n,
                     "exceptions": n - first,
                     "shuffled": null_hit / null_n if null_n else np.nan})
order = pd.DataFrame(rows).sort_values("turns", ascending=False).reset_index(drop=True)
order["agent"] = order.submission.map(label)
display(order[["agent", "turns", "sell_first", "exceptions", "shuffled"]]
        .style.format({"turns": "{:,}", "sell_first": "{:.1%}",
                       "shuffled": "{:.1%}"}))
print(f"\nALL TEN: {order.sell_first.mul(order.turns).sum():,.0f} of "
      f"{order.turns.sum():,} turns place the sell first. "
      f"Exceptions: {order.exceptions.sum()}.")

d = order.sort_values("turns")
y = np.arange(len(d))
fig, ax = plt.subplots(figsize=(8.4, 4.2))
ax.barh(y, d.sell_first, height=0.55, color=SELL, zorder=3,
        label="observed: sell before the purchase")
ax.scatter(d.shuffled, y, marker="|", s=280, linewidths=2.4, color=ACC, zorder=4,
           label="same orders, shuffled")
for yy, (v, nn) in enumerate(zip(d.sell_first, d.turns)):
    ax.text(v + 0.012, yy, f"{v:.1%}  (n={nn:,})", va="center", fontsize=8.5,
            color="#334155")
ax.set_yticks(y); ax.set_yticklabels([label(s) for s in d.submission], fontsize=8.5)
ax.set_xlim(0, 1.22); ax.set_xticks(np.arange(0, 1.01, 0.25))
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}" if v <= 1 else "")
ax.set_xlabel("share of mixed turns in which the SELL is ordered first")
ax.set_title("Ten teams, 9,208 opportunities, zero exceptions", loc="left")
ax.legend(loc="lower right", frameon=False, fontsize=9)
plt.tight_layout(); plt.show()

CLASS = {**{k: "structure" for k in ("HIRE", "BUY_LAND", "BUY_ANIMAL")},
         **{k: "inputs" for k in ("BUY_SEED", "BUY_PRODUCT")},
         "SELL": "trading"}
COLOR = {"structure": STRUCT, "inputs": INPUT, "trading": SELL}

# Per episode, how many of each operation. Then: across episodes of one agent,
# how many DISTINCT totals does each channel take? One means it never moves.
per_ep = {}
for (sub, eid), g in streams.groupby(["submission", "episode_id"]):
    c = {"structure": 0, "inputs": 0, "trading": 0}
    for s in g["market"]:
        for o in ops_of(s):
            k = CLASS.get(o)
            if k:
                c[k] += 1
    per_ep.setdefault(sub, []).append(c)

rows = []
for sub, eps in per_ep.items():
    if len(eps) < 5:
        continue
    r = {"submission": sub, "episodes": len(eps)}
    for k in ("structure", "inputs", "trading"):
        vals = [e[k] for e in eps]
        r[f"{k}_median"] = int(np.median(vals))
        r[f"{k}_distinct"] = len(set(vals))
    rows.append(r)
chan = pd.DataFrame(rows).sort_values("structure_distinct").reset_index(drop=True)
chan["agent"] = chan.submission.map(label)
display(chan[["agent", "episodes", "structure_median", "structure_distinct",
              "inputs_distinct", "trading_distinct"]])

d = chan.sort_values("trading_distinct")
y = np.arange(len(d)); w = 0.26
fig, ax = plt.subplots(figsize=(8.4, 4.4))
for i, k in enumerate(("structure", "inputs", "trading")):
    ax.barh(y + (i - 1) * w, d[f"{k}_distinct"], height=w, color=COLOR[k],
            label=k, zorder=3)
ax.axvline(1, color="#0F172A", lw=1.2, ls=":", zorder=4)
ax.text(1.15, len(d) - 0.4, "1 = the total never changes,\nin any episode",
        fontsize=8.5, color="#334155", va="top")
ax.set_yticks(y); ax.set_yticklabels([label(s) for s in d.submission], fontsize=8.5)
ax.set_xlabel("distinct per-episode totals across this agent's episodes")
ax.set_title("The structural half of the market channel is as fixed as the board",
             loc="left")
ax.legend(frameon=False, fontsize=9, loc="lower right")
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

# Measured margins from the 2026-08-26 reorder ablation, log row 203bc. They
# are data typed into this cell; the cell draws them and computes nothing.
ABLATION = [('shop-guard', 10637, 2855, 2842), ('morita tape', -9449, -92429, -61375), ('v21-r1', 1783, -88410, -60628)]

names = [a[0] for a in ABLATION]
pub = [a[1] / 1000 for a in ABLATION]
srt = [a[2] / 1000 for a in ABLATION]
rev = [a[3] / 1000 for a in ABLATION]
x = list(range(len(names)))

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.bar([i - 0.26 for i in x], pub, width=0.24, color="#2f6fb2",
       label="as published")
ax.bar([i for i in x], srt, width=0.24, color="#c2571f",
       label="market list sorted")
ax.bar([i + 0.26 for i in x], rev, width=0.24, color="#9aa3ad",
       label="market list reversed (control)")
ax.axhline(0, color="#40484f", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
ax.set_ylabel("margin against the adaptive rival\n(thousands of $)")
ax.set_title("destroying the order of the market list, three published agents",
             fontsize=10)
ax.legend(frameon=False, fontsize=9, loc="lower left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()