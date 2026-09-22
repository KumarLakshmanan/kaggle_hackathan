import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.6,
    "font.size": 9.5, "axes.titlesize": 11.5, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "legend.frameon": False,
    "lines.linewidth": 1.1, "lines.markersize": 4.0,
    "lines.solid_capstyle": "round", "axes.linewidth": 0.7,
    "xtick.major.width": 0.7, "ytick.major.width": 0.7, "patch.linewidth": 0.7,
})
INK, TEAL, AMBER, GREY, RED = "#0F172A", "#0F766E", "#B45309", "#94A3B8", "#B91C1C"

def find(name):
    for root in ("/kaggle/input", ".", "..", "data"):
        r = Path(root)
        if r.exists():
            for p in r.rglob(name):
                return p
    return None

M = pd.read_parquet(find("matchups_all.parquet"),
                    columns=["episode_id", "opponent_seat", "opponent_rating",
                             "opponent_behaviour", "recorded_bank_yours",
                             "recorded_bank_opponent"])
print(f"{len(M):,} recorded matchups")

rng = np.random.default_rng(17)
E = (M.assign(_r=rng.random(len(M)))
      .sort_values("_r").drop_duplicates("episode_id"))
margin = (E.recorded_bank_yours - E.recorded_bank_opponent).to_numpy()
banks = np.concatenate([E.recorded_bank_yours.to_numpy(),
                        E.recorded_bank_opponent.to_numpy()])
print(f"{len(E):,} independent episodes, {len(banks):,} banks")

rho = float(np.corrcoef(E.recorded_bank_yours, E.recorded_bank_opponent)[0, 1])
s_bank = float(banks.std(ddof=1))
s_pred = s_bank * np.sqrt(2 * (1 - rho))
s_obs = float(margin.std(ddof=1))

print(f"  standard deviation of one bank      ${s_bank:>12,.0f}")
print(f"  correlation between the two banks    {rho:>+12.3f}")
print(f"  margin spread PREDICTED by algebra  ${s_pred:>12,.0f}")
print(f"  margin spread observed              ${s_obs:>12,.0f}")
print(f"  error                               ${s_pred - s_obs:>+12,.0f}")
print()
a = np.abs(margin)
for q in (0.05, 0.25, 0.50, 0.75, 0.95):
    print(f"  {int(q*100):>3}% of games are decided by less than ${np.quantile(a, q):>10,.0f}")

fig, ax = plt.subplots(figsize=(7.6, 4.2))
srt = np.sort(np.abs(margin))
share = np.arange(1, len(srt) + 1) / len(srt)
ax.plot(srt, 100 * share, color=TEAL, label="games decided by less than this")
ax.axvline(s_obs, color=RED, lw=1.0, ls=(0, (4, 3)))
ax.annotate(f"the noise, \\${s_obs:,.0f}", xy=(s_obs, 8), xytext=(6, 0),
            textcoords="offset points", fontsize=9, color=RED)
for amount in (3000, 10000):
    pct = 100 * (np.abs(margin) < amount).mean()
    ax.plot([amount], [pct], marker="o", ms=5, mfc="white", mec=INK, mew=1.2)
    # `pct` is the share of margins SMALLER than `amount`, which is the share a
    # win of that size beats. The complement is the share that beat IT, and
    # labelling the marker with the complement inverts the sentence.
    ax.annotate(f"a \\${amount:,} win beats\\n{pct:.0f} % of margins",
                xy=(amount, pct), xytext=(12, -18), textcoords="offset points",
                fontsize=8.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
ax.set_xscale("log")
ax.set_xlabel("margin, dollars"); ax.set_ylabel("% of games decided by less")
ax.set_title("How big does a win have to be before it means anything?",
             loc="left")
ax.legend(loc="lower right", fontsize=8.5)
plt.tight_layout(); plt.show()

BANDS = [(400, 800), (800, 1400), (1400, 2000), (2000, 2400), (2400, 2700),
         (2700, 3200)]
rows = []
for lo, hi in BANDS:
    s = E[(E.opponent_rating >= lo) & (E.opponent_rating < hi)]
    if len(s) < 100:
        continue
    d = (s.recorded_bank_yours - s.recorded_bank_opponent).abs()
    rows.append({"rating band": f"{lo}-{hi}", "games": len(s),
                 "median margin": f"${d.median():,.0f}",
                 "decided by under $5k": f"{100*(d < 5000).mean():.0f} %"})
display(pd.DataFrame(rows))

fig, ax = plt.subplots(figsize=(7.4, 3.9))
xs, ys = [], []
for lo, hi in BANDS:
    s = E[(E.opponent_rating >= lo) & (E.opponent_rating < hi)]
    if len(s) < 100:
        continue
    xs.append(f"{lo}-{hi}")
    ys.append(float((s.recorded_bank_yours - s.recorded_bank_opponent).abs().median()))
x = np.arange(len(xs))
ax.axhline(s_obs, color=RED, lw=1.0, ls=(0, (4, 3)))
ax.annotate(f"the noise: ${s_obs:,.0f}", xy=(0, s_obs), xytext=(0, 6),
            textcoords="offset points", fontsize=9, color=RED)
ax.plot(x, ys, color=TEAL, marker="o")
ax.fill_between(x, 0, ys, color=TEAL, alpha=0.10, lw=0)
ax.annotate("what a typical game\nis decided by", xy=(x[-2], ys[-2]),
            xytext=(-4, 34), textcoords="offset points", fontsize=9,
            color="#0F766E", ha="right",
            arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
ax.set_xticks(x); ax.set_xticklabels(xs, fontsize=8.5)
ax.set_ylim(0, s_obs * 1.18)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
ax.set_xlabel("rating band"); ax.set_ylabel("median absolute margin, dollars")
ax.set_title("The better the field, the more of the result is noise", loc="left")
plt.tight_layout(); plt.show()

x = banks[banks > 0]
fits = {}
for name, dist, data, back in (("normal", stats.norm, x, 0.0),
                               ("lognormal", stats.norm, np.log(x),
                                float(np.log(x).sum())),
                               ("gamma", stats.gamma, x, 0.0)):
    par = dist.fit(data, floc=0) if name == "gamma" else dist.fit(data)
    fits[name] = {
        "log-likelihood": float(dist.logpdf(data, *par).sum()) - back,
        "KS p-value": float(stats.kstest(data, dist(*par).cdf).pvalue),
    }
F = pd.DataFrame(fits).T.sort_values("log-likelihood", ascending=False)
display(pd.DataFrame({"log-likelihood": F["log-likelihood"].map("{:,.1f}".format),
                      "KS p-value": F["KS p-value"].map("{:.3g}".format)}))
print(f"skew of log(bank) {stats.skew(np.log(x)):+.2f},  "
      f"excess kurtosis {stats.kurtosis(np.log(x)):+.2f}   "
      f"(both 0 if exactly lognormal)")

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0))
for ax, (data, lab) in zip(axes, ((x, "the bank"), (np.log(x), "log of the bank"))):
    osm, osr = stats.probplot(data, dist="norm", fit=False)
    ax.plot(osm, osr, ls="none", marker="o", ms=2.0, mfc=TEAL, mec="none",
            alpha=0.30)
    mu, sd = data.mean(), data.std(ddof=1)
    lo, hi = float(osm.min()), float(osm.max())
    ax.plot([lo, hi], [mu + sd*lo, mu + sd*hi], color=GREY, lw=1.0,
            ls=(0, (4, 3)), label="exactly normal")
    ax.set_title(f"{lab} against a normal", loc="left")
    ax.set_xlabel("normal quantile"); ax.set_ylabel(lab)
    ax.legend(fontsize=8.5)
plt.tight_layout(); plt.show()

shapes = {}
for name, dist in (("normal", stats.norm), ("laplace", stats.laplace),
                   ("t", stats.t)):
    par = dist.fit(margin)
    shapes[name] = {
        "log-likelihood": float(dist.logpdf(margin, *par).sum()),
        "KS p-value": float(stats.kstest(margin, dist(*par).cdf).pvalue),
        "df": round(float(par[0]), 2) if name == "t" else None,
    }
S = pd.DataFrame(shapes).T.sort_values("log-likelihood", ascending=False)
display(S)
print(f"skew {stats.skew(margin):+.3f},  "
      f"excess kurtosis {stats.kurtosis(margin):+.2f}   (0 and 0 if normal)")

# The tails are the whole story, and on a linear axis they are invisible: they
# are rare by construction. A log density is the honest picture.
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))
lim = float(np.quantile(np.abs(margin), 0.995))
bins = np.linspace(-lim, lim, 81)
mid = 0.5 * (bins[1:] + bins[:-1])
dens, _ = np.histogram(margin, bins=bins, density=True)
pn = stats.norm(*stats.norm.fit(margin)).pdf(mid)
pt_par = stats.t.fit(margin)
pt = stats.t(*pt_par).pdf(mid)

for ax, logy in zip(axes, (False, True)):
    ax.fill_between(mid, dens, color=TEAL, alpha=0.22, lw=0, step="mid",
                    label="the margins actually recorded")
    ax.plot(mid, pn, color=RED, label="the normal that fits them best")
    ax.plot(mid, pt, color=AMBER,
            label=f"a t with {pt_par[0]:.1f} degrees of freedom")
    if logy:
        ax.set_yscale("log")
        ax.set_ylim(max(dens[dens > 0].min() * 0.5, 1e-9), dens.max() * 2)
        ax.set_title("and the tails are far too heavy", loc="left")
    else:
        ax.set_title("the peak is far too sharp for a normal", loc="left")
        ax.legend(fontsize=8.5)
    ax.set_xlabel("margin, dollars")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
plt.tight_layout(); plt.show()

def within_kurtosis(groups, floor=30):
    z = [(np.asarray(g, float) - np.mean(g)) / np.std(g, ddof=1)
         for g in groups if len(g) >= floor and np.std(g, ddof=1) > 0]
    return (float(stats.kurtosis(np.concatenate(z))), len(z)) if z else (None, 0)

k0 = float(stats.kurtosis(margin))
E2 = E.assign(margin=E.recorded_bank_yours - E.recorded_bank_opponent,
              weaker=np.minimum(E.recorded_bank_yours, E.recorded_bank_opponent))

# H1  mixing over rating bands
h1 = [g.to_numpy() for _, g in
      E2.assign(b=(E2.opponent_rating // 100) * 100).groupby("b")["margin"]]

# H2  catastrophes: agents that crash or silently do nothing
h2 = [E2[E2.weaker >= t].margin.to_numpy() for t in (0, 10_000, 20_000, 40_000)]

# H3  clones: both sides opening with a byte-identical stream
wide = M.pivot_table(index="episode_id", columns="opponent_seat",
                     values="opponent_behaviour", aggfunc="first").dropna()
wide.columns = ["b0", "b1"]
J = E2.set_index("episode_id").join((wide.b0 == wide.b1).rename("clone"),
                                    how="inner").dropna(subset=["clone"])
h3 = [g.margin.to_numpy() for _, g in J.groupby("clone")]

rows = []
for name, groups in (("H1  mixing over rating bands", h1),
                     ("H2  catastrophic games", h2),
                     ("H3  clones against non-clones", h3)):
    k1, used = within_kurtosis(groups)
    rows.append({"hypothesis": name, "groups": used,
                 "excess kurtosis, pooled": round(k0, 2),
                 "after standardising within": round(k1, 2) if k1 else None,
                 "verdict": "supported" if k1 and k1 < 0.5 * k0 else "REFUTED"})
display(pd.DataFrame(rows))
print(f"\n{100*J.clone.mean():.0f} % of episodes pair two byte-identical openings")
for v, g in J.groupby("clone"):
    print(f"  {'same' if v else 'different'} opening: {len(g):>5} games, "
          f"median absolute margin ${g.margin.abs().median():>9,.0f}")

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.0))

# left: what each hypothesis would have had to do, and what it did
ax = axes[0]
L = pd.DataFrame(rows)
y = np.arange(len(L))
after = [float(v) for v in L["after standardising within"]]
ax.barh(y, after, color=RED, height=0.32)
for yi, v in zip(y, after):
    ax.text(v + 0.7, yi, f"{v:.1f}", va="center", fontsize=9, fontweight="bold")
ax.axvline(k0, color="#475569", lw=0.9, ls=(0, (4, 3)))
ax.axvline(0, color=INK, lw=1.2)
ax.set_yticks(y)
ax.set_yticklabels([h.split("  ")[1] for h in L["hypothesis"]], fontsize=8.5)
ax.set_ylim(len(y) - 0.4, -1.15)
ax.set_xlim(0, max(after) * 1.22)
ax.annotate("if the hypothesis\nwere right", xy=(0, -0.95), xytext=(6, 0),
            textcoords="offset points", fontsize=8.5, color=INK, va="center")
ax.annotate(f"pooled: {k0:.1f}", xy=(k0, -0.95), xytext=(6, 0),
            textcoords="offset points", fontsize=8.5, color="#475569",
            va="center")
ax.annotate("past this line, the split made it WORSE",
            xy=(max(after) * 0.99, len(y) - 0.75), fontsize=8.5, color=RED,
            ha="right", va="center")
ax.set_xlabel("excess kurtosis left after standardising inside the groups")
ax.set_title("Three explanations, and what each one removed", loc="left")

# right: the half of H3 that is right
ax = axes[1]
for v, col, lab in ((True, TEAL, "same opening"), (False, AMBER, "different opening")):
    d = np.abs(J[J.clone == v].margin.to_numpy())
    d = np.sort(d)
    ax.plot(d, 100 * np.arange(1, len(d) + 1) / len(d), color=col,
            label=f"{lab}, n={len(d):,}")
floor = 100 * (J[J.clone].margin == 0).mean()
ax.annotate(f"{floor:.0f} % of clone games end in an EXACT tie,\n"
            f"to the dollar, which is the step at the left",
            xy=(1.6, floor), xytext=(10, 26), textcoords="offset points",
            fontsize=8.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
ax.set_xscale("log")
ax.set_xlabel("margin, dollars"); ax.set_ylabel("% of games decided by less")
ax.set_title("Clones really do end closer, which is the peak but not the tails",
             loc="left")
ax.legend(loc="lower right", fontsize=8.5)
plt.tight_layout(); plt.show()

counts = M.opponent_behaviour.value_counts().to_numpy().astype(float)
Ntot = counts.sum()

def expected_distinct(k):
    """E[D(k)] exactly, by inclusion over behaviours. No simulation."""
    from scipy.special import gammaln
    lp = (gammaln(Ntot - counts + 1) - gammaln(Ntot - counts - k + 1)
          - gammaln(Ntot + 1) + gammaln(Ntot - k + 1))
    miss = np.exp(np.where(Ntot - counts - k + 1 > 0, lp, -np.inf))
    return float((1 - miss).sum()), float(np.sqrt((miss * (1 - miss)).sum()))

KS = [10, 20, 40, 80, 160, 320, 640]
rows = [{"you drew": k, "you actually got": round(expected_distinct(k)[0], 1),
         "give or take": round(expected_distinct(k)[1], 1)}
        for k in KS if k <= Ntot]
display(pd.DataFrame(rows))

f1 = int((counts == 1).sum()); f2 = int((counts == 2).sum())
chao1 = len(counts) + (f1*f1/(2*f2) if f2 else f1*(f1-1)/2)
print(f"\n  behaviours observed here          {len(counts):>8,}")
print(f"  seen exactly once                 {f1:>8,}")
print(f"  Good-Turing coverage              {1 - f1/Ntot:>8.3f}")
print(f"  Chao1 lower bound on the field    {chao1:>8,.0f}")
print(f"  so at least this many unseen      {chao1 - len(counts):>8,.0f}")

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.0))

ax = axes[0]
KK = np.unique(np.round(np.logspace(1, np.log10(min(2000, Ntot)), 26)).astype(int))
ED = np.array([expected_distinct(int(k))[0] for k in KK])
SD = np.array([expected_distinct(int(k))[1] for k in KK])
ax.plot(KK, KK, color=GREY, lw=1.0, ls=(0, (4, 3)),
        label="what the size of your pool claims")
ax.fill_between(KK, ED - 1.96 * SD, ED + 1.96 * SD, color=TEAL, alpha=0.16, lw=0)
ax.plot(KK, ED, color=TEAL, label="distinct behaviours you actually drew")
k40 = float(expected_distinct(40)[0])
ax.plot([40], [k40], marker="o", ms=5.5, mfc="white", mec=INK, mew=1.3)
ax.annotate(f"a pool of 40 is {k40:.0f}", xy=(40, k40), xytext=(14, -20),
            textcoords="offset points", fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("opponents drawn"); ax.set_ylabel("distinct behaviours")
ax.set_title("The gap opens at once and never closes", loc="left")
ax.legend(loc="upper left", fontsize=8.5)

ax = axes[1]
spec = pd.Series(counts).value_counts().sort_index()
k = spec.index.to_numpy()[:12]
v = spec.to_numpy()[:12]
ax.bar(k, v, color=[RED if i == 1 else TEAL for i in k], width=0.62)
ax.set_yscale("log")
ax.set_ylim(top=v[0] * 6)
ax.annotate(f"{int(v[0]):,} behaviours seen exactly once,\n"
            f"which is what says the field is\nnot finished arriving",
            xy=(1.35, v[0]), xytext=(30, 4), textcoords="offset points",
            fontsize=8.5, color=INK, va="center",
            arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
ax.set_xlabel("times a behaviour appears in the corpus")
ax.set_ylabel("how many behaviours")
ax.set_title("The frequency spectrum, where both estimators come from",
             loc="left")
plt.tight_layout(); plt.show()

a = E[E.opponent_seat == 1]
b = E[E.opponent_seat == 0]
ma = (a.recorded_bank_yours - a.recorded_bank_opponent).to_numpy()
mb = (b.recorded_bank_yours - b.recorded_bank_opponent).to_numpy()
ks = stats.ks_2samp(margin, -margin)
boot = np.array([rng.choice(margin, len(margin), replace=True).mean()
                 for _ in range(2000)])

# EXCLUDE EXACT TIES. A sign test is defined on the non-zero differences, and
# this game produces real ties: two agents running the same code bank the same
# money to the dollar. Counting a tie as "not a win" biases the rate below one
# half and makes a sound corpus look asymmetric.
ties = int((margin == 0).sum())
nz = margin[margin != 0]

print(f"  episodes                 {len(margin):>10,}")
print(f"  exact ties               {ties:>10,}  ({100*ties/len(margin):.2f} %)")
print(f"  mean margin             ${margin.mean():>+10,.0f}")
print(f"  95 % interval           [{np.quantile(boot,.025):>+,.0f}, "
      f"{np.quantile(boot,.975):>+,.0f}]")
print(f"  win rate, ties excluded  {(nz > 0).mean():>10.4f}")
print(f"  sign test p              {stats.binomtest(int((nz>0).sum()), len(nz), 0.5).pvalue:>10.3f}")
print(f"  KS against its mirror    {ks.pvalue:>10.3f}")
print()
print(f"  and counting the ties as losses instead would give "
      f"{(margin > 0).mean():.4f}, p = "
      f"{stats.binomtest(int((margin>0).sum()), len(margin), 0.5).pvalue:.4f}")

fig, ax = plt.subplots(figsize=(7.4, 3.8))
lim = float(np.quantile(np.abs(margin), 0.98))
bins = np.linspace(-lim, lim, 71)
ax.hist(margin, bins=bins, color=TEAL, alpha=0.28, lw=0, density=True,
        label="the margin")
ax.hist(-margin, bins=bins, histtype="step", color=AMBER, lw=1.1, density=True,
        label="the same data, mirrored")
ax.axvline(0, color=GREY, lw=0.8)
ax.set_xlabel("margin, dollars"); ax.set_ylabel("density")
ax.set_title("A control: a symmetric game must look the same from either seat",
             loc="left")
ax.legend(fontsize=8.5)
plt.tight_layout(); plt.show()