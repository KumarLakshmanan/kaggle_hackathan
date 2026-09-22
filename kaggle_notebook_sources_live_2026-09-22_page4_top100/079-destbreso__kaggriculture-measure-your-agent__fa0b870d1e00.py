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

import sys
sys.path.insert(0, str(find("instrument.py").parent))
import instrument as I

print("gates and measures declared:", ", ".join(I.SPEC))
print()
print("what each one says it needs, which is the half that is usually implicit:")
for name in ("POPULATION", "SYMMETRY", "PAIRED"):
    s = I.SPEC[name]
    print(f"  {name:<12} at least {s['min_n']:<5} {s['needs'][:58]}")

# Feed it the published benchmark. This adapter is the whole interface: if your
# own results can be shaped like this, every check below runs on them unchanged.
B = pd.read_parquet(find("matchups_top.parquet"))
pool = [{"episode_id": r.episode_id, "seed": int(r.seed),
         "our_seat": int(r.your_seat), "opp_seat": int(r.opponent_seat),
         "opponent": r.opponent_team,
         "our_bank": float(r.recorded_bank_yours),
         "their_bank": float(r.recorded_bank_opponent),
         "we_won": bool(r.recorded_bank_yours > r.recorded_bank_opponent),
         "script": json.loads(r.opponent_actions)}
        for r in B.itertuples()]
print(f"{len(pool)} matchups from the strong half of the field")

# POPULATION clusters every pair of action streams, which is quadratic, so this
# runs it on a slice. The full pool takes a few minutes rather than seconds.
SLICE = 150
pop = I.gate_population(None, pool[:SLICE])
sym = I.gate_symmetry(pool)

# Effective n and the already-won share mean the same thing on any pool, so they
# are what this prints. The gate also estimates field coverage and unseen
# richness; both are defined on a pool collected AS IT CAME and this one is
# stratified, so they belong to a different kind of pool than this.
print(f"POPULATION on {SLICE} matchups")
print(f"  nominal {pop['nominal']}, EFFECTIVE {pop['effective']}")
print(f"  already won by the recording side: {pop['already_won']}")
print()
print(f"SYMMETRY on all {len(pool)}")
print(f"  seats {sym['seat0']}/{sym['seat1']}, p = {sym['p']:.3f} -> "
      f"{'pass' if sym['pass'] else 'FAIL'}")
print()
print("SAMPLE AUDIT")
for r in I.audit_samples([pop, sym], pool):
    print(f"  {r['measure']:<12}{str(r['have']):>7} need {str(r['need']):<6}"
          f"{'ok' if r['ok'] else 'THIN':<5} {r['note'][:64]}")

# Everything below is loaded from the attached dataset, not pasted into a cell.
OC = pd.DataFrame([{k: r[k] for k in ("opponent", "n", "mu", "sigma", "z",
                                      "predicted", "observed", "se")}
                   for r in load_input("objective_calibration.json")])
FC = load_input("ladder_forecast.json")
ST = pd.DataFrame(load_input("instrument_selftest.json")["tests"])
IV = load_input("instrument_validation.json")
print(f"{len(OC)} calibration opponents, {len(ST)} self-tests, "
      f"{len(IV['instruments'])} historical instruments, "
      f"{len(FC['forecast']['band'])} forecast horizons")

OC["abs_err"] = (OC.predicted - OC.observed).abs()
OC["inside"] = OC.abs_err <= 1.96 * OC.se

def flabel(s):
    """Kaggle images carry no CJK font, so such a name would render as tofu."""
    s = str(s)
    return "a top-10 team" if any("⺀" <= c <= "鿿" or
                                  "가" <= c <= "힯" for c in s) else s[:16]

fig, ax = plt.subplots(figsize=(6.4, 5.2))
ax.plot([0, 1], [0, 1], color=GREY, lw=0.8, ls=(0, (4, 3)), zorder=1,
        label="if the rule were exact")
ax.errorbar(OC.predicted, OC.observed, yerr=1.96 * OC.se, fmt="o", ms=4.5,
            mfc="white", mec=TEAL, mew=1.1, ecolor=GREY, elinewidth=0.7,
            capsize=2, capthick=0.7, zorder=3, label="one opponent, 20 games")
for _, r in OC.iterrows():
    if r.abs_err > 0.11:
        ax.annotate(flabel(r.opponent), (r.predicted, r.observed),
                    textcoords="offset points", xytext=(7, -3), fontsize=7.5,
                    color="#475569")
ax.set_xlim(0.25, 1.0); ax.set_ylim(0.25, 1.0); ax.set_aspect("equal")
ax.set_xlabel("win rate the rule predicts, from margin / wobble")
ax.set_ylabel("win rate actually observed")
ax.set_title("Wins really are margin divided by wobble", loc="left")
ax.legend(loc="upper left", fontsize=8.5)
plt.tight_layout(); plt.show()

print(f"  mean error            {OC.abs_err.mean():.3f}")
print(f"  inside the interval   {int(OC.inside.sum())}/{len(OC)} opponents")

band = pd.DataFrame(FC["forecast"]["band"])
now = FC["now"]
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ax.fill_between(band.episode, band.p10, band.p90, color=TEAL, alpha=0.16,
                label="80 % of comparable submissions")
ax.fill_between(band.episode, band.p25, band.p75, color=TEAL, alpha=0.30,
                label="the middle half")
ax.plot(band.episode, band.p50, color=TEAL, lw=1.3, label="median path")
ax.scatter([now["episodes"]], [now["score"]], s=42, facecolor="white",
           edgecolor=RED, linewidth=1.3, zorder=5, label="where ours is now")
ax.set_xlabel("episodes played")
ax.set_ylabel("ladder rating")
ax.set_title("Rating is a trajectory, so the honest answer is a band", loc="left")
ax.legend(loc="lower left", fontsize=8.5)
plt.tight_layout(); plt.show()

print(f"  built from the {FC['forecast']['peers']} submissions that sat within")
print(f"  250 rating points of ours at the same episode number")

show = ST[["test", "expected", "got", "pass", "wins", "n", "paired_median",
           "paired_p"]].copy()
show["result"] = np.where(show["pass"], "pass", "FAIL")
display(show[["test", "expected", "got", "result", "wins", "n",
              "paired_median", "paired_p"]])

truth, inst = IV["truth"], IV["instruments"]
RG = pd.DataFrame([{"agent": a, "ladder": truth[a], "score": inst[a]["beat_history"]}
                   for a in truth if a in inst and "beat_history" in inst[a]])

fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9),
                         gridspec_kw={"width_ratios": [1.05, 1]})
ax = axes[0]
ax.scatter(RG.score, RG.ladder, s=42, facecolor="white", edgecolor=TEAL,
           linewidth=1.1, zorder=3)
ax.set_xlabel("what the offline test said")
ax.set_ylabel("what the ladder said")
ax.set_title("Validated here: nine weak agents, 307 points apart", loc="left")

ax = axes[1]
for i, (lab, lo, hi, c) in enumerate([
        ("validated" + chr(10) + "on this range", 354, 662, TEAL),
        ("USED" + chr(10) + "on this range", 2400, 2850, RED)]):
    ax.add_patch(Rectangle((i - 0.32, lo), 0.64, hi - lo, color=c, alpha=0.80, linewidth=0))
    ax.text(i, hi + 110, lab, ha="center", fontsize=9, color=c, fontweight="bold")
    ax.text(i, (lo + hi) / 2, f"{hi - lo} pts" + chr(10) + "wide", ha="center",
            va="center", color="white", fontsize=9, fontweight="bold")
ax.set_xlim(-0.7, 1.7); ax.set_ylim(0, 3250); ax.set_xticks([])
ax.set_ylabel("ladder rating")
ax.set_title("The gap it was never asked to cross", loc="left")
plt.tight_layout(); plt.show()