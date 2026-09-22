import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from scipy import stats


def find(name):
    """Locate an input, wherever this notebook is running.

    EVERY input this notebook uses comes from the attached dataset. Nothing is
    pasted into a cell, so forking it and re-running gives you the same figures
    from the same declared source rather than somebody else's numbers frozen
    into a string literal.
    """
    for root in ("/kaggle/input", ".", "..", "data"):
        r = Path(root)
        if r.exists():
            for p in r.rglob(name):
                return p
    return None


def load_input(name):
    p = find(name)
    if p is None:
        raise FileNotFoundError(
            f"{name} not found. Attach the dataset "
            f"'destbreso/kaggriculture-benchmark-matchups' with Add Input, "
            f"on the right of the editor.")
    return json.loads(Path(p).read_text())

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.6,
    "font.size": 9.5, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "legend.frameon": False,
    # Thin and soft throughout. Heavy strokes and big vertices fight the data.
    "lines.linewidth": 1.1, "lines.markersize": 4.5,
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "patch.linewidth": 0.7,
})
INK, TEAL, AMBER, GREY, RED = "#0F172A", "#0F766E", "#B45309", "#94A3B8", "#B91C1C"

# The idea, in three lines.
#
#   for m in recorded_games:
#       bank = play(my_agent, opponent=m["their_recorded_actions"], seed=m["seed"])
#       assert abs(bank - m["recorded_bank"]) <= 1
#
# Ours (research/exact_replay.py). Its run record travels with the dataset, so
# the three figures below are counted here rather than typed here: one row per
# recorded matchup, holding what the seat banked and what the replay banked.
R = load_input("exact_replay.json")
err = np.abs([r["replay"] - r["recorded"] for r in R])
exact = sum(1 for r in R if r["exact"])
outcome = sum(1 for r in R if r["recorded_won"] == r["replay_won"])

print(f"  banks reproduced exactly     {exact}/{len(R)}  "
      f"({100 * exact / len(R):.0f} %)")
print(f"  median absolute error        ${np.median(err):,.0f}")
print(f"  win/loss outcome reproduced  {outcome}/{len(R)}  "
      f"({100 * outcome / len(R):.0f} %)")

# for every turn:   assert my_agent(obs) == old_agent(obs)
#
# Ours (research/instrument.py, gate PARITY). The gate writes down what it
# checked, and that record travels with the dataset, so the count below is read
# back off the run instead of being asserted about it.
G = {g["name"]: g for g in load_input("instrument.json")["gates"]}
turns, diffs = G["PARITY"]["checked"], G["PARITY"]["diffs"]

print(f"  PARITY   {turns:,} turns, {diffs} differences")
print()
print(f"  'parity OK' is a wish. '{turns:,} turns, {diffs} differences' "
      f"is a gate.")

# The UNFILTERED file, deliberately. The other one in this dataset is stratified
# by behaviour, so measuring the collapse on it would measure the fix rather
# than the problem. This is what you get if you simply collect episodes.
BENCH = find("matchups_all.parquet") or find("matchups.parquet")
M = pd.read_parquet(BENCH, columns=["episode_id", "opponent_rating",
                                    "opponent_behaviour",
                                    "recorded_bank_yours",
                                    "recorded_bank_opponent"]).dropna(
                                        subset=["opponent_rating"])
print(f"{len(M):,} matchups, {M.opponent_behaviour.nunique():,} distinct "
      f"behaviours among them")
print(f"{100 * (M.recorded_bank_yours > M.recorded_bank_opponent).mean():.0f} % "
      f"are games the recording side had already won")

rng = np.random.default_rng(7)

def distinct(beh, k, reps=200):
    """Draw k opponents, count how many genuinely different ones came with them."""
    if k > len(beh):
        return None
    return int(np.median([len(set(rng.choice(beh, k, replace=False)))
                          for _ in range(reps)]))

# Matchmaking is rating-conditioned: it hands you opponents near your own score,
# not a random sample of the field. So the question is not "how much does a pool
# collapse", it is "how much does it collapse WHERE YOU SIT".
BANDS = [(400, 800), (800, 1400), (1400, 2000), (2000, 2400),
         (2400, 2700), (2700, 3200)]
rows = []
for lo, hi in BANDS:
    s = M[(M.opponent_rating >= lo) & (M.opponent_rating < hi)]
    b = s.opponent_behaviour.to_numpy()
    if len(b) < 120:
        continue
    rows.append({"if you sit at": f"{lo}-{hi}", "matchups here": len(b),
                 "draw 40, get": distinct(b, 40),
                 "draw 100, get": distinct(b, 100)})
B = pd.DataFrame(rows)
B["a pool of 40 is really"] = [f"{v} opponents" for v in B["draw 40, get"]]
display(B)

whole = distinct(M.opponent_behaviour.to_numpy(), 40)
print(f"drawing 40 from the whole field instead: {whole} distinct behaviours")

fig, ax = plt.subplots(figsize=(7.4, 3.9))
x = np.arange(len(B))
ax.axhline(40, color=GREY, lw=1.0, ls=(0, (4, 3)))
ax.annotate("what your table claims: 40", xy=(0, 40), xytext=(0, 6),
            textcoords="offset points", fontsize=8.5, color="#475569")
ax.axhline(whole, color=GREY, lw=0.9, ls=(0, (1, 2.5)))
ax.annotate(f"drawn from the whole field: {whole}", xy=(0, whole),
            xytext=(0, 5), textcoords="offset points", fontsize=8.5,
            color="#475569")
ax.plot(x, B["draw 40, get"], color=TEAL, marker="o",
        label="drawn from your own rating band")
for xi, v in zip(x, B["draw 40, get"]):
    ax.annotate(str(v), (xi, v), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=9, fontweight="bold", color=INK)
ax.set_xticks(x); ax.set_xticklabels(B["if you sit at"], fontsize=8.5)
ax.set_ylim(0, 45)
ax.set_xlabel("the rating band you are matched into")
ax.set_ylabel("distinct behaviours in a pool of 40")
ax.set_title("A pool of forty is worth less the better you get", loc="left")
ax.legend(loc="lower left", fontsize=8.5)
plt.tight_layout(); plt.show()

from scipy import stats
E = (M.assign(_r=np.random.default_rng(17).random(len(M)))
      .sort_values("_r").drop_duplicates("episode_id"))
mg = (E.recorded_bank_yours - E.recorded_bank_opponent).to_numpy()

# Exact ties are excluded, because a sign test is defined on the non-zero
# differences and this game produces real ties: two agents running the same code
# bank the same money to the dollar. Counting them as losses makes a sound
# corpus look asymmetric, at p < 0.001 on this data.
nz = mg[mg != 0]
print(f"  episodes                 {len(mg):>10,}")
print(f"  exact ties               {int((mg == 0).sum()):>10,}")
print(f"  win rate, ties excluded  {(nz > 0).mean():>10.4f}   (0.5 if sound)")
print(f"  sign test p              "
      f"{stats.binomtest(int((nz > 0).sum()), len(nz), 0.5).pvalue:>10.3f}")
print(f"  KS against its mirror    {stats.ks_2samp(mg, -mg).pvalue:>10.3f}")

# WRONG: two independent samples, and most of the noise survives.
#   mine  = [play(new) for _ in range(200)]
#   yours = [play(old) for _ in range(200)]
#   compare(mean(mine), mean(yours))
#
# RIGHT: the same games, differenced.
#   for g in games:
#       d = play(new, seed=g.seed, seat=g.seat, opp=g.opponent) \
#         - play(old, seed=g.seed, seat=g.seat, opp=g.opponent)
#
# then a sign test on the differences, not a t-test on the levels.
print("Ours: 40 recorded matchups, each replayed at its own seed, from its own")
print("seat, against that opponent's own recorded actions.")

def sign_power(n, p, alpha=0.05):
    """Exact power of a two-sided paired sign test against a true win rate p.

    Under the null the wins are Binomial(n, 1/2) and the test rejects outside
    the central 1-alpha region, so the power is the mass a Binomial(n, p) puts
    outside that same region. No normal approximation: at these counts it
    flatters the design by several points.
    """
    lo = stats.binom.ppf(alpha / 2, n, 0.5) - 1
    hi = stats.binom.ppf(1 - alpha / 2, n, 0.5) + 1
    return float(stats.binom.cdf(lo, n, p) + stats.binom.sf(hi - 1, n, p))

def n_for(p, target=0.80):
    return next((n for n in range(10, 2000) if sign_power(n, p) >= target), None)

SECONDS_PER_GAME = 1.13
rows = []
for p in (0.55, 0.575, 0.60, 0.65, 0.70):
    n = n_for(p)
    rows.append({"to detect a real": f"{100*p:.1f} %",
                 "you need": n,
                 "costing": f"{2*n*SECONDS_PER_GAME/60:.0f} min",
                 "power at n=40": f"{100*sign_power(40, p):.0f} %",
                 "power at n=421": f"{100*sign_power(421, p):.0f} %"})
display(pd.DataFrame(rows))

fig, ax = plt.subplots(figsize=(7.4, 4.2))
ns = np.unique(np.round(np.logspace(np.log10(20), np.log10(1200), 34)).astype(int))
for p, col in ((0.70, GREY), (0.65, AMBER), (0.60, TEAL), (0.55, RED)):
    ax.plot(ns, [sign_power(int(n), p) for n in ns], color=col,
            label=f"a real {100*p:.0f} %")
ax.axhline(0.80, color=INK, lw=0.8, ls=(0, (4, 3)))
ax.annotate("80 % power", xy=(21, 0.80), xytext=(0, 5),
            textcoords="offset points", fontsize=8.5, color=INK)
for n, lab in ((40, "the 40\nwe inherited"), (421, "the 421\nin this dataset")):
    ax.axvline(n, color=GREY, lw=0.7)
    ax.annotate(lab, xy=(n, 0.06), xytext=(4, 0), textcoords="offset points",
                fontsize=8.5, color="#475569", va="bottom")
ax.set_xscale("log"); ax.set_ylim(0, 1.02)
ax.set_xlabel("paired games"); ax.set_ylabel("chance of noticing a real effect")
ax.set_title("What your pool size can and cannot see", loc="left")
ax.legend(loc="lower right", fontsize=8.5, title="effect size")
plt.tight_layout(); plt.show()