import csv, json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# every table in this notebook, stripe matrices included, comes from the companion dataset
# kaggriculture-replay-genomes; only the X-ray matrices above ride embedded,
# because they are a different representation (per-turn stripe bitmaps)
DATA = Path("/kaggle/input/kaggriculture-replay-genomes")
if not DATA.exists():
    DATA = Path(".")
T2 = json.loads((DATA / "xray_stripes.json").read_text())
G = [g for g in T2["groups"] if not g.get("missing")]

VAL = json.loads((DATA / "field_validation.json").read_text())

CORPUS = {"kawashigi PRE": 55425101, "tschinkel PRE": 55525269,
          "kawashigi KING": 55540317, "kawashigi NEW": 55579868,
          "tschinkel A": 55588572, "tschinkel B": 55601640}
episode_barcodes = {k: [] for k in CORPUS}
with (DATA / "barcodes.csv").open() as f:
    for r in csv.DictReader(f):
        for label, sub in CORPUS.items():
            if int(r["submission"]) == sub and len(episode_barcodes[label]) < 12:
                episode_barcodes[label].append(r["dna_bands"].split("-"))
consensus_barcodes = {}
with (DATA / "reference_barcodes.csv").open() as f:
    for r in csv.DictReader(f):
        consensus_barcodes[r["label"]] = r["dna_bands"].split("-")
DNA = {"consensus_barcodes": consensus_barcodes,
       "episode_barcodes": episode_barcodes}
print("corpora:", [g["label"] for g in G])
print("field validation:", VAL["teams"], "teams,", VAL["streams"], "streams")
print("barcodes loaded from:", DATA)


SAME, MUT, PLAN = "#DCEEE1", "#B45309", "#0F172A"
CMAP = ListedColormap([SAME, MUT, PLAN])

def unpack(hexes):
    m = np.zeros((len(hexes), 718), dtype=np.uint8)
    for i, hx in enumerate(hexes):
        bits = np.unpackbits(np.frombuffer(bytes.fromhex(hx), dtype=np.uint8),
                             bitorder="little")
        m[i] = bits[1:719]
    return m

show = [("kawashigi KING 55540317", "1"), ("tschinkel A 55588572", "0")]
panels = []
for label, seat in show:
    g = next(g for g in G if g["label"] == label)
    s = g["seats"][seat]
    plan = unpack(s["plan_rows_hex"])
    mkt = unpack(s["market_rows_hex"])
    panels.append((f"{label} seat {seat} (n={s['n']})",
                   np.where(plan == 1, 2, np.where(mkt == 1, 1, 0))))
heights = [max(0.6, p[1].shape[0] / 55) for p in panels]
fig, axes = plt.subplots(len(panels), 1,
                         figsize=(11, sum(heights) + 1.6),
                         gridspec_kw={"height_ratios": heights})
for ax, (title, cat) in zip(np.atleast_1d(axes), panels):
    ax.imshow(cat, aspect="auto", cmap=CMAP, vmin=0, vmax=2,
              interpolation="nearest")
    ax.set_title(title, fontsize=8, loc="left")
    ax.set_yticks([])
axes[-1].set_xlabel("turn")
fig.legend(handles=[Patch(facecolor=SAME, edgecolor="0.6", label="matches corpus mode"),
                    Patch(facecolor=MUT, label="market channel differs"),
                    Patch(facecolor=PLAN, label="plan (farmer/hands) differs")],
           fontsize=11, loc="upper center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, 1.0))
plt.tight_layout(rect=(0, 0, 1, 0.94)); plt.show()

hours = (np.arange(1, 719) % 24)
fold = np.zeros(24); cnt = np.zeros(24)
for g in G:
    for seat in ("0", "1"):
        s = g["seats"].get(seat) or {}
        if s.get("thin") or "plan_rows_hex" not in s:
            continue
        div = (unpack(s["plan_rows_hex"]) |
               unpack(s["market_rows_hex"])).astype(bool)
        for h in range(24):
            sel = div[:, hours == h]
            fold[h] += sel.sum(); cnt[h] += sel.size
rate = fold / np.maximum(1, cnt)
fig, ax = plt.subplots(figsize=(10, 2.8))
ax.bar(range(24), rate,
       color=["#2E7D32" if h in (1, 2, 3, 4) else "#0F172A" for h in range(24)])
ax.set_xticks(range(24)); ax.set_xlabel("hour of the in-game day")
ax.set_ylabel("share diverging")
ax.set_title("hours 1-4, in green, are the conserved window", fontsize=9)
plt.tight_layout(); plt.show()

# the gel: each corpus consensus barcode as thirty coloured bands
def band_color(h):
    v = int(h[:6], 16)
    return plt.cm.tab20((v % 20) / 20)

import hashlib
def genome_id(bands):
    """The accession number: eight characters of the whole-barcode hash,
    the searchable key for a sample in any dataset of barcodes."""
    return hashlib.sha1("".join(bands).encode()).hexdigest()[:8]

labels = list(DNA["consensus_barcodes"])
fig, ax = plt.subplots(figsize=(11, 0.42 * len(labels) + 1.4))
for y, k in enumerate(labels):
    for d, band in enumerate(DNA["consensus_barcodes"][k]):
        ax.add_patch(plt.Rectangle((d, y), 0.92, 0.8,
                                   color=band_color(band)))
ax.set_xlim(0, 30); ax.set_ylim(0, len(labels))
ax.set_yticks(np.arange(len(labels)) + 0.4)
ax.set_yticklabels([f"{k}  ·  {genome_id(DNA['consensus_barcodes'][k])}"
                    for k in labels], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("in-game day (locus)")
ax.set_title("the gel: same colour in a column = same allele at that locus",
             fontsize=9)
plt.tight_layout(); plt.show()

# the liveness profile: per-day self-agreement of each corpus, the
# instrument's validity range drawn as a curve
def day_agreement(episodes):
    out = []
    for d in range(30):
        c = {}
        for bc in episodes:
            c[bc[d]] = c.get(bc[d], 0) + 1
        out.append(max(c.values()) / len(episodes))
    return out

fig, ax = plt.subplots(figsize=(9.5, 3.4))
E = DNA["episode_barcodes"]
for label, key, color in (("tschinkel (12 games)", "tschinkel A", "#0F172A"),
                          ("kawashigi (12 games)", "kawashigi KING", "#B45309")):
    ys = day_agreement(E[key])
    ax.plot(range(30), ys, color=color, lw=2, label=label)
    ax.annotate(label.split(" ")[0], (29, ys[-1]), xytext=(5, 0),
                textcoords="offset points", color=color, fontsize=9,
                va="center")
ax.axhline(0.6, color="#C62828", lw=1, ls="--")
ax.annotate("below this line the kinship test refuses to rule",
            (0.5, 0.575), fontsize=8, color="#C62828", va="top")
ax.set_xlim(0, 33); ax.set_ylim(0, 1.05)
ax.set_xlabel("in-game day (locus)")
ax.set_ylabel("fraction of games on the modal band")
ax.grid(alpha=0.25)
ax.legend(loc="lower left", fontsize=9, frameon=False)
ax.set_title("the liveness profile: where in the season each agent stops "
             "being a script", fontsize=10)
plt.tight_layout(); plt.show()

labels = list(DNA["consensus_barcodes"])
n = len(labels)
M = np.zeros((n, n), dtype=int)
for i, a in enumerate(labels):
    for j, b in enumerate(labels):
        M[i, j] = sum(x == y for x, y in zip(DNA["consensus_barcodes"][a],
                                             DNA["consensus_barcodes"][b]))
fig, ax = plt.subplots(figsize=(9.5, 7.5))
im = ax.imshow(M, cmap="Greens", vmin=0, vmax=30)
ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=90, fontsize=7)
ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=7)
for i in range(n):
    for j in range(n):
        ax.text(j, i, M[i, j], ha="center", va="center", fontsize=6,
                color="white" if M[i, j] > 15 else "#0F172A")
ax.set_title("matching bands of 30", fontsize=9)
plt.colorbar(im, shrink=0.7)
plt.tight_layout(); plt.show()

labels = list(DNA["consensus_barcodes"])
B = DNA["consensus_barcodes"]

def shared(a, b):
    return sum(x == y for x, y in zip(B[a], B[b]))

def fork_day(a, b):
    for d in range(30):
        if B[a][d] != B[b][d]:
            return d
    return None

# average-linkage agglomerative clustering on distance = 30 - shared bands
clusters = [{"members": [l], "height": 30, "node": l} for l in labels]
merges = []
while len(clusters) > 1:
    best = None
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            s = np.mean([shared(a, b) for a in clusters[i]["members"]
                         for b in clusters[j]["members"]])
            if best is None or s > best[0]:
                best = (s, i, j)
    s, i, j = best
    fd = min((fork_day(a, b) if fork_day(a, b) is not None else 30)
             for a in clusters[i]["members"] for b in clusters[j]["members"])
    merged = {"members": clusters[i]["members"] + clusters[j]["members"],
              "height": s, "left": clusters[i], "right": clusters[j],
              "fork": fd}
    merges.append(merged)
    clusters = [c for k, c in enumerate(clusters) if k not in (i, j)] + [merged]

# draw the dendrogram: x = shared bands at the join (30 -> 0), y = leaves
ypos = {}
def assign_y(node, next_y=[0]):
    if "node" in node:
        ypos[id(node)] = next_y[0]; next_y[0] += 1
        return ypos[id(node)]
    ys = [assign_y(node["left"]), assign_y(node["right"])]
    ypos[id(node)] = np.mean(ys)
    return ypos[id(node)]
root = clusters[0]
assign_y(root)

fig, ax = plt.subplots(figsize=(10.5, 0.5 * len(labels) + 1.5))
def draw(node, parent_x=None):
    y = ypos[id(node)]
    if "node" in node:
        x = 30
        ax.text(30.3, y,
                f"{node['node']}  ·  {genome_id(B[node['node']])}",
                fontsize=8, va="center")
    else:
        x = node["height"]
        yl, yr = ypos[id(node["left"])], ypos[id(node["right"])]
        ax.plot([x, x], [yl, yr], color="#0F172A", lw=1.4)
        tag = "=" if node["fork"] >= 30 else f"d{node['fork']}"
        ax.annotate(tag, (x, (yl + yr) / 2),
                    textcoords="offset points", xytext=(-14, 0),
                    fontsize=7, color="#B45309")
        draw(node["left"], x)
        draw(node["right"], x)
    if parent_x is not None:
        ax.plot([parent_x, x], [y, y], color="#0F172A", lw=1.4)
draw(root)
ax.set_xlim(-1, 44)
ax.set_ylim(-0.7, len(labels) - 0.3)
ax.set_yticks([])
ax.invert_yaxis()
ax.set_xlabel("bands shared at the split (of 30); amber = in-game day of the fork")
ax.set_title("the dated phylogeny of everything on the board", fontsize=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

w = VAL["within_pairs"]; c = VAL["cross_pairs"]
fig, axes = plt.subplots(1, 2, figsize=(11, 3))
axes[0].hist(c, bins=31, color="#0F172A")
axes[0].axvline(np.median(w), color="#B45309", lw=2,
                label=f"same-team median {np.median(w):.2f}")
axes[0].set_xlabel("fraction of matching bands, cross-team pairs")
axes[0].set_ylabel("pairs"); axes[0].legend(fontsize=8)
axes[0].set_title(f"{len(c):,} cross-team pairs: 75 % match zero bands",
                  fontsize=9)
days = sorted(int(k) for k in VAL["cardinality_by_day"])
axes[1].bar(days, [VAL["cardinality_by_day"][str(d)] for d in days],
            color="#2E7D32")
axes[1].set_xlabel("in-game day"); axes[1].set_ylabel("distinct alleles")
axes[1].set_title(f"locus cardinality across {VAL['teams']} teams", fontsize=9)
plt.tight_layout(); plt.show()

FREQS = VAL["allele_freqs"]
FLOOR = VAL["floor"]

def stability(episodes):
    """A corpus's agreement with itself: mean, over the 30 loci, of the
    fraction of its episodes carrying the day's modal band. The test's
    validity range in one number."""
    out = []
    for d in range(30):
        c = {}
        for bc in episodes:
            c[bc[d]] = c.get(bc[d], 0) + 1
        out.append(max(c.values()) / len(episodes))
    return sum(out) / 30

def dna_test(bc_a, bc_b, name_a="sample A", name_b="sample B",
             stability_a=None, stability_b=None):
    m = [x == y for x, y in zip(bc_a, bc_b)]
    k = sum(m)
    # random-match probability UNDER LOCUS INDEPENDENCE: the product of the
    # shared alleles' population frequencies. Two conservative choices: the
    # 1/160 floor for unseen alleles can only WEAKEN evidence, and the
    # validation showed independence overstates chance matching here ~30x
    # (zero of 12,720 unrelated pairs share >= 2 bands against a predicted
    # mean of 4.81), so the real chance is smaller than this number says.
    log10_rmp = 0.0
    for d, ok in enumerate(m):
        if ok:
            log10_rmp += np.log10(max(FLOOR, FREQS[d].get(bc_a[d], FLOOR)))
    rmp = 10 ** log10_rmp if k else 1.0
    fork = next((d for d, ok in enumerate(m) if not ok), None)
    if k == len(m):
        verdict = "IDENTICAL / SAME SOURCE"
    elif rmp < 1e-4 and k >= 2:     # >= 2 also clears the empirical bar:
        verdict = "RELATED"          # no unrelated pair reaches 2 bands
    elif rmp < 1e-2:
        verdict = "WEAK SIGNAL"
    else:
        verdict = "UNRELATED"
    # validity guard: a verdict of UNRELATED requires both samples to BE
    # someone. A corpus that agrees with itself at 0.37 cannot be told
    # apart from a distant relative, so the test refuses rather than errs.
    stabs = [s for s in (stability_a, stability_b) if s is not None]
    if verdict == "UNRELATED" and stabs and min(stabs) < 0.6:
        verdict = f"OUT OF RANGE (sample self-agreement {min(stabs):.2f})"
    print(f"DNA TEST  {name_a} [{genome_id(bc_a)}]  x  "
          f"{name_b} [{genome_id(bc_b)}]")
    print(f"  bands matched            {k}/30  ({100*k/30:.0f} %)")
    print(f"  P(match | independence)  10^{log10_rmp:.1f}" if k else
          f"  P(match | independence)  1.0  (nothing shared)")
    print(f"  empirical bar            0 of 12,720 unrelated pairs share >= 2 bands")
    print(f"  verdict                  {verdict}"
          + (f", first observable divergence day {fork}"
             if verdict == "RELATED" else ""))
    print()
    return {"matched": k, "log10_rmp": log10_rmp, "verdict": verdict,
            "fork_day": fork, "match_vector": m}

B = DNA["consensus_barcodes"]
E = DNA["episode_barcodes"]
kaw_stab = stability(E["kawashigi KING"])

cases = [
    ("same agent, two real games",
     E["tschinkel PRE"][0], E["tschinkel PRE"][1],
     "tschinkel game 1", "tschinkel game 2", None, None),
    ("parent and mutant",
     B["route:LEGACY_10C4S_3Q"], B["stream:utkarsh#2"],
     "public legacy route", "utkarsh #2", None, None),
    ("strangers",
     B["route:10C4S_3Q"], B["stream:abdelrazik"],
     "public route", "abdelrazik", None, None),
    ("the deepest adaptive still shows its ancestor",
     B["kawashigi KING"], B["route:10C4S_3Q"],
     "kawashigi consensus", "public route", kaw_stab, None),
    ("where the test refuses to rule",
     B["kawashigi KING"], B["stream:abdelrazik"],
     "kawashigi consensus", "abdelrazik", kaw_stab, None),
]
results = [(title, a, b, dna_test(a, b, na, nb, sa, sb))
           for title, a, b, na, nb, sa, sb in cases]

fig, axes = plt.subplots(len(results), 1, figsize=(11, 2.1 * len(results)))
for ax, (title, bc_a, bc_b, r) in zip(np.atleast_1d(axes), results):
    for row, bc in ((1.35, bc_a), (0.0, bc_b)):
        for d, band in enumerate(bc):
            ax.add_patch(plt.Rectangle((d, row), 0.92, 0.8,
                                       color=band_color(band)))
    for d, ok in enumerate(r["match_vector"]):
        ax.text(d + 0.46, 1.08, "|" if ok else "x",
                ha="center", va="center", fontsize=8,
                color="#2E7D32" if ok else "#C62828",
                fontweight="bold")
    ax.set_xlim(0, 30); ax.set_ylim(-0.3, 2.5)
    ax.set_yticks([]); ax.set_xticks(range(0, 31, 5))
    ax.set_title(f"{title}: {r['matched']}/30 bands, {r['verdict']}"
                 + (f", forks day {r['fork_day']}"
                    if r['verdict'] == 'RELATED' else ""),
                 fontsize=9, loc="left")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
axes[-1].set_xlabel("locus (in-game day); green bar = band match, red x = mismatch")
plt.tight_layout(); plt.show()

# the verdict landscape: every report above, placed on the map the
# thresholds define, so a reader sees WHERE a pair landed and how far the
# nearest boundary is
import math, statistics
from matplotlib.lines import Line2D
fig, ax = plt.subplots(figsize=(10, 5.4))

ax.axhspan(0, 2, color="#E2E8F0", alpha=0.8)
ax.axhspan(2, 4, color="#FDE68A", alpha=0.45)
ax.axhspan(4, 56, color="#DCEEE1", alpha=0.35)
for y, lab, col in ((1.0, "UNRELATED", "#475569"),
                    (3.0, "WEAK SIGNAL", "#92400E"),
                    (10.5, "RELATED", "#166534")):
    ax.annotate(lab, (30.6, y), fontsize=8.5, color=col, va="center",
                annotation_clip=False)
ax.axvline(2, color="#C62828", lw=1.1, ls="--")
ax.annotate("empirical bar: no unrelated pair of 12,720 passes this line",
            (2.4, 45.5), fontsize=8, color="#C62828")

top_common = max(max(day.values()) for day in FREQS)
xs = list(range(31))
ax.fill_between(xs, [k * -math.log10(top_common) for k in xs],
                [k * -math.log10(FLOOR) for k in xs],
                color="#0E7490", alpha=0.07)
ax.plot(xs, [k * -math.log10(FLOOR) for k in xs], color="#0E7490",
        lw=0.8, ls=":")
ax.annotate("rarest-allele edge: 2.2 per band", (17.3, 41.5), fontsize=8,
            color="#0E7490", rotation=38)

COL = {"IDENTICAL / SAME SOURCE": "#0F172A", "RELATED": "#166534",
       "WEAK SIGNAL": "#92400E", "UNRELATED": "#475569"}
LAYOUT = {
    "same agent, two real games": dict(xy=(-12, -16), ha="right"),
    "parent and mutant": dict(xy=(10, 8), ha="left"),
    "the deepest adaptive still shows its ancestor": dict(xy=(-10, 12), ha="right"),
    "strangers": dict(xy=(26, -2), ha="left"),
    "where the test refuses to rule": dict(xy=(20, 26), ha="left"),
}
seen00 = 0
for title, _a, _b, r in results:
    k, lg, v = r["matched"], -r["log10_rmp"], r["verdict"]
    refused = v.startswith("OUT OF RANGE")
    x = k + (0.45 if refused and k == 0 and seen00 else 0)
    seen00 += (k == 0)
    col = "#C62828" if refused else COL.get(v, "#0F172A")
    ax.scatter([x], [lg], s=150, facecolors="none" if refused else col,
               edgecolors=col, zorder=3, linewidths=2)
    lay = LAYOUT.get(title, dict(xy=(8, 8), ha="left"))
    ax.annotate(title, (x, lg), xytext=lay["xy"], textcoords="offset points",
                fontsize=8.5, color="#0F172A", ha=lay["ha"],
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#94A3B8")
                if lay["xy"][1] > 14 or abs(lay["xy"][0]) > 18 else None)

ax.legend(handles=[
    Line2D([], [], marker="o", ls="", mfc="#0F172A", mec="#0F172A", label="identical"),
    Line2D([], [], marker="o", ls="", mfc="#166534", mec="#166534", label="related"),
    Line2D([], [], marker="o", ls="", mfc="#475569", mec="#475569", label="unrelated"),
    Line2D([], [], marker="o", ls="", mfc="none", mec="#C62828", label="refused (out of range)"),
], loc="upper left", fontsize=8.5, frameon=False, bbox_to_anchor=(0.045, 0.985))

ax.set_xlim(-0.8, 31)
ax.set_ylim(-1.5, 56)
ax.set_xlabel("bands matched (of 30)")
ax.set_ylabel("evidence, -log10 P(match | independence)")
ax.set_title("the verdict landscape: where each test above landed", fontsize=10)
ax.grid(alpha=0.12)
plt.tight_layout(); plt.show()
print("the refused circle sits where the evidence would have put it; the refusal")
print("says why the test has no right to say it. And note the two related pairs:")
print("kawashigi reaches utkarsh-level evidence with nine FEWER bands, because")
print("its shared alleles are rarer and each band weighs more.")

SUBMISSION_ID = 55540317        # <- change me (see consensus.csv for options)

rows = []
with (DATA / "barcodes.csv").open() as f:
    for r in csv.DictReader(f):
        if int(r["submission"]) == SUBMISSION_ID:
            rows.append(r)
assert rows, f"{SUBMISSION_ID} not in the dataset; consensus.csv lists the 14 available"
eps = [r["dna_bands"].split("-") for r in rows]
team = rows[0]["team"]
cons = []
for d in range(30):
    c = {}
    for bc in eps:
        c[bc[d]] = c.get(bc[d], 0) + 1
    cons.append(max(c, key=c.get))
stab = stability(eps)
print(f"{team}  (submission {SUBMISSION_ID})")
print(f"  games in dataset      {len(eps)}")
print(f"  genome accession      {genome_id(cons)}")
print(f"  self-agreement        {stab:.2f}"
      + ("   (adaptive: negative verdicts will be refused)" if stab < 0.6 else ""))
scored = sorted(((sum(x == y for x, y in zip(cons, bc)), label)
                 for label, bc in consensus_barcodes.items()), reverse=True)
print("  nearest references:")
for k, label in scored[:3]:
    print(f"    {label:<30} {k}/30 bands")
best_label = scored[0][1]
print()
_ = dna_test(cons, consensus_barcodes[best_label], team, best_label,
             stability_a=stab)

import pandas as pd
bc = pd.read_csv(DATA / "barcodes.csv")
cons = pd.read_csv(DATA / "consensus.csv")

# 1) the monoculture, quantified by a GROUP BY: how much of the elite
#    agrees on every locus through day 10
cls = cons.groupby("lineage_d10").size().sort_values(ascending=False)
print(f"submissions: {len(cons)}   largest day-10 class: "
      f"{cls.iloc[0]} submissions share {cls.index[0]}")

# 2) the same team across calendar days: lineage persistence
multi = cons[cons.team.isin(cons.team.value_counts()[lambda s: s > 1].index)]
print("\none team, several capture days:")
for team, g in multi.groupby("team"):
    tag = "  ".join(f"{r.capture_batch}:{r.genome_id}(sa {r.self_agreement:.2f})"
                    for r in g.itertuples())
    print(f"  {team[:24]:<24} {tag}")

# 3) a prefix range: everyone matching the public legacy route through day 20
legacy = pd.read_csv(DATA / "reference_barcodes.csv")
pref = "-".join(legacy[legacy.label == "route:LEGACY_10C4S_3Q"]
                .dna_bands.iloc[0].split("-")[:20])
family = bc[bc.dna_bands.str.startswith(pref)]
print(f"\nepisode rows sharing the legacy route's first 20 loci: "
      f"{len(family)} across {family.team.nunique()} teams: "
      f"{sorted(family.team.unique())[:6]}")

# the board, drawn from the same two columns
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.2),
                               gridspec_kw={"width_ratios": [1, 1.5]})

# lineage-class structure: how concentrated is the elite's ancestry?
sizes = cons.groupby("lineage_d10").size().sort_values(ascending=False)
top = sizes.head(8)
ax1.bar(range(len(top)), top.values, color="#0E7490")
ax1.bar(len(top), sizes.iloc[8:].sum(), color="#94A3B8")
ax1.set_xticks(list(range(len(top))) + [len(top)])
ax1.set_xticklabels([i[:6] for i in top.index] + ["rest"],
                    rotation=45, ha="right", fontsize=8)
for i, v in enumerate(top.values):
    ax1.annotate(str(v), (i, v), ha="center", va="bottom", fontsize=9)
ax1.set_ylabel("submissions in the class")
ax1.set_title("day-10 lineage classes: the monoculture,\nquantified",
              fontsize=10)
ax1.grid(alpha=0.2, axis="y")

# the board map: how alive each agent is vs how common its lineage is
csize = cons.lineage_d10.map(sizes)
ax2.scatter(cons.self_agreement, csize, s=55, alpha=0.75, color="#0F172A")
NAME = {"カワシギ": "#B45309", "Thomas Tschinkel": "#0E7490",
        "Kostiantyn Isaienkov": "#166534"}
for team, col in NAME.items():
    g = cons[cons.team == team]
    ax2.scatter(g.self_agreement, g.lineage_d10.map(sizes), s=90,
                color=col, label=team, zorder=3)
ax2.axvline(0.6, color="#C62828", lw=1, ls="--")
ax2.annotate("kinship test refuses\nnegative verdicts", (0.585, 20),
             fontsize=8, color="#C62828", ha="right")
ax2.set_xlabel("self-agreement (script 1.0, alive 0.0)")
ax2.set_ylabel("size of its day-10 lineage class")
ax2.set_title("every submission on the two axes this notebook reads:\n"
              "cached solutions crowd the top right, live solvers stand alone",
              fontsize=10)
ax2.legend(loc="upper left", fontsize=8, frameon=False)
ax2.grid(alpha=0.2)
plt.tight_layout(); plt.show()

import itertools, math, statistics

# alpha: distribution-free bound at the RELATED threshold (k >= 2)
fp = sum(1 for x in VAL["cross_pairs"] if x >= 2)
n = len(VAL["cross_pairs"])
print(f"alpha (false match, k>=2): {fp}/{n} observed")
print(f"  95% upper bound (rule of three):      {3/n:.1e} per comparison")
print(f"  most conservative (80 indep. pairs):  {3/80:.1e}")
q = [sum(v*v for v in day.values()) for day in FREQS]
dp = [1.0]
for qd in q:
    ndp = [0.0]*(len(dp)+1)
    for k, pk in enumerate(dp):
        ndp[k] += pk*(1-qd); ndp[k+1] += pk*qd
    dp = ndp
print(f"  (independence model would say P(k>=2) = {sum(dp[2:]):.3f}: refuted, unusable)")

# beta curve 1: power vs fork depth, median-frequency alleles
med = [statistics.median(day.values()) for day in FREQS]
print("\npower vs fork depth:")
for f in (1, 2, 3, 5, 8):
    lg = sum(math.log10(max(FLOOR, med[d])) for d in range(f))
    v = "RELATED" if (10**lg < 1e-4 and f >= 2) else ("WEAK SIGNAL" if 10**lg < 1e-2 else "undetected")
    print(f"  fork at day {f}: evidence 10^{lg:.1f} -> {v}")

# beta curve 2: measured miss rate on same-agent pairs (ground truth RELATED)
print("\nmiss rate vs instability (every pair is the same agent):")
for name in ("tschinkel A", "kawashigi KING"):
    eps = DNA["episode_barcodes"][name]
    stab = stability(eps)
    miss = tot = 0
    for a, b in itertools.combinations(range(len(eps)), 2):
        m = [x == y for x, y in zip(eps[a], eps[b])]
        k = sum(m)
        lg = sum(math.log10(max(FLOOR, FREQS[d].get(eps[a][d], FLOOR)))
                 for d, ok in enumerate(m) if ok)
        rmp = 10**lg if k else 1.0
        tot += 1
        if not (k == 30 or (rmp < 1e-4 and k >= 2) or rmp < 1e-2):
            miss += 1
    print(f"  {name:<16} self-agreement {stab:.2f}: misses {miss}/{tot} = {miss/tot:.0%}")