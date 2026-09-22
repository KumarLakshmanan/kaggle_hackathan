import os, glob, warnings
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
mpl.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 120,
                     "font.size": 10.5, "axes.grid": True, "grid.alpha": 0.2, "axes.unicode_minus": False})
INK="#1b1b2f"; BL="#2f6df6"; GD="#e8a63c"; HL="#d1495b"; GR="#8a8a99"; GRN="#2a9d8f"

def find(fn):
    for c in ["/kaggle/input/kaggriculture-ladder-meta",
              "/kaggle/input/kaggriculture-ladder-meta/kaggriculture-ladder-meta"]:
        p = os.path.join(c, fn)
        if os.path.exists(p): return p
    hits = glob.glob("/kaggle/input/**/" + fn, recursive=True)
    if hits: return hits[0]
    loc = os.path.join("D:/kaggle/ds_kaggri_meta", fn)
    return loc if os.path.exists(loc) else None
print("episode_results:", find("episode_results.csv"), "| daily_ladder:", find("daily_ladder.csv"))

ep = pd.read_csv(find("episode_results.csv")) if find("episode_results.csv") else pd.DataFrame()
lad = pd.read_csv(find("daily_ladder.csv")) if find("daily_ladder.csv") else pd.DataFrame()
READY = len(ep) > 0
if READY:
    v = ep[ep["both_done"] == True].copy() if "both_done" in ep.columns else ep.copy()
    v["winner_reward"] = v[["reward_a","reward_b"]].max(axis=1)
    v["margin_pct"] = 100 * v["margin"] / v["winner_reward"]
    print("episodes:", len(ep), "| complete games:", len(v), "| dates:", sorted(v["date"].unique().tolist()))
    print("reward range:", int(v["winner_reward"].min()), "-", int(v["winner_reward"].max()), "| ties:", int((ep['winner']=='tie').sum()))
    print("GATE: complete games n =", len(v))
else:
    print("companion dataset not attached; add busyaprime/kaggriculture-ladder-meta and it renders")

if READY:
    m = v["margin_pct"].values
    fig, ax = plt.subplots(figsize=(9.5,4.4))
    ax.hist(m, bins=30, color=BL, alpha=0.9)
    med = float(np.median(m)); ax.axvline(med, color=HL, lw=2.5, label=f"median {med:.1f}%")
    ax.set_xlabel("winning margin (% of winner reward)"); ax.set_ylabel("games"); ax.legend()
    ax.set_title("Most Kaggriculture games are won by a thin margin", color=INK, loc="left", fontweight="bold", fontsize=11)
    plt.tight_layout(); plt.show()
    rng = np.random.default_rng(0)
    boot = [np.median(rng.choice(m, len(m), replace=True)) for _ in range(5000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    for thr in [1,2,5,10]:
        print(f"games decided by < {thr}% of winner reward: {(m<thr).mean()*100:.1f}%")
    print(f"median margin {med:.2f}% (95% bootstrap CI {lo:.2f}% to {hi:.2f}%) on n={len(m)} games")

if READY:
    fig, (a1,a2) = plt.subplots(1,2, figsize=(12,4.3))
    by = v.groupby("date")["margin_pct"].median()
    a1.plot(range(len(by)), by.values, marker="o", color=BL, lw=2)
    a1.set_xticks(range(len(by))); a1.set_xticklabels(by.index, rotation=25, ha="right", fontsize=8)
    a1.set_ylabel("median margin (% of winner)"); a1.set_title("Winning margin by day", color=INK, loc="left", fontweight="bold")
    if len(lad) and "top_median_gap" in lad.columns:
        a2.plot(range(len(lad)), lad["top_median_gap"].values, marker="o", color=GD, lw=2)
        a2.set_xticks(range(0,len(lad),max(1,len(lad)//6)))
        a2.set_xticklabels([lad["date"].iloc[i] for i in range(0,len(lad),max(1,len(lad)//6))], rotation=25, ha="right", fontsize=8)
        a2.set_ylabel("top minus median score"); a2.set_title("Ladder top-to-median gap", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
    print("median margin by day:", {d: round(float(x),2) for d,x in by.items()})
    if len(lad): print("ladder top-median gap first -> last:", round(float(lad['top_median_gap'].iloc[0]),1), "->", round(float(lad['top_median_gap'].iloc[-1]),1))

if READY:
    ps = np.arange(0.52, 0.76, 0.01)
    need = (1.96**2) * ps*(1-ps) / (ps-0.5)**2
    fig, ax = plt.subplots(figsize=(9.5,4.6))
    ax.plot((ps*100), need, marker="o", color=GRN, lw=2)
    ax.set_yscale("log"); ax.set_xlabel("true win rate of the stronger agent (%)")
    ax.set_ylabel("games needed (log) to exclude 50-50")
    for pv in [0.55,0.60,0.70]:
        nn=(1.96**2)*pv*(1-pv)/(pv-0.5)**2
        ax.annotate(f"{pv:.0%} -> {nn:.0f}", xy=(pv*100,nn), fontsize=9, color=INK,
                    xytext=(pv*100+0.4, nn*1.4))
    ax.set_title("A thin edge takes many games to prove", color=INK, loc="left", fontweight="bold", fontsize=11)
    plt.tight_layout(); plt.show()
    for pv in [0.55,0.60,0.65,0.70]:
        nn=(1.96**2)*pv*(1-pv)/(pv-0.5)**2
        print(f"win rate {pv:.0%}: about {nn:.0f} games to be 95% sure it beats a coin flip")