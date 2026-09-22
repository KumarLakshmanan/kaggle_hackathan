import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def box(ax, x, y, w, h, title, lines, fc, title_c="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                fc=fc, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h - 0.045, title, ha="center", va="top",
            fontsize=10.5, fontweight="bold", color=title_c)
    for i, ln in enumerate(lines):
        ax.text(x + 0.015, y + h - 0.095 - 0.046 * i, ln, fontsize=8.6,
                va="top", color=title_c)

def arrow(ax, x1, y1, x2, y2, label=""):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, lw=1.4, color="#333"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.018, label,
                fontsize=8.2, ha="center", style="italic")

fig, ax = plt.subplots(figsize=(11.5, 6.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("The offline verdict protocol: three samples, two engine lanes, one decision rule",
             fontsize=12.5, pad=12)

box(ax, 0.01, 0.68, 0.28, 0.27, "SAMPLE 1: your own matchups",
    ["every episode your live subs played", "rival stream + seed + seat",
     "UNCAPPED, rebuilt at decision time", "(half life of the field: 2.1 days)"],
    "#2e6b8a")
box(ax, 0.01, 0.37, 0.28, 0.26, "SAMPLE 2: live community agents",
    ["public donor dataset, credited", "17 measured behaviour families",
     "adaptive layers awake", "disjoint from sample 1 (measured)"],
    "#7a4f9d")
box(ax, 0.01, 0.06, 0.28, 0.26, "SAMPLE 3: the worlds",
    ["shop draw = 64 ordered pairs", "one seed per world, both seats",
     "closed set: counted, not estimated"],
    "#3d7a4f")

box(ax, 0.37, 0.55, 0.26, 0.33, "LANE L0: replay (C++)",
    ["both sides recorded streams", "~1.4 ms a game, 50 us batched",
     "ground truth: 286/287 recorded", "banks reproduced to the dollar",
     "-> paired counterfactuals"],
    "#b0803d")
box(ax, 0.37, 0.13, 0.26, 0.33, "LANE L1: live (C++)",
    ["both sides live policies", "150-240 ms a game",
     "reactive rivals play THEIR game", "company effects, mirrors",
     "-> the response replays lack"],
    "#a05252")

box(ax, 0.71, 0.55, 0.28, 0.33, "TEST 1: paired discordant",
    ["candidate vs incumbent,", "same rival, seed and seat",
     "McNemar exact on discordants", "power curve read at its n"],
    "#444444")
box(ax, 0.71, 0.13, 0.28, 0.33, "TEST 2: order agreement",
    ["same two agents, sample 2", "all 64 worlds, both seats",
     "must agree with test 1 in ORDER", "disagreement = the finding"],
    "#444444")

arrow(ax, 0.29, 0.80, 0.37, 0.74)
arrow(ax, 0.29, 0.50, 0.37, 0.30)
arrow(ax, 0.29, 0.19, 0.37, 0.22, "seeds")
arrow(ax, 0.63, 0.72, 0.71, 0.72)
arrow(ax, 0.63, 0.29, 0.71, 0.29)
ax.text(0.85, 0.505, "BOTH must license the verdict", ha="center",
        fontsize=9, fontweight="bold", color="#8a2e2e")
arrow(ax, 0.85, 0.55, 0.85, 0.48)
arrow(ax, 0.85, 0.46, 0.85, 0.13 + 0.33)

ax.text(0.5, 0.015, "audits riding along: Chao1 species coverage (open axis) | 64-world coverage (closed axis) | sample-power audit | THIN discipline",
        ha="center", fontsize=8.6, style="italic")
plt.tight_layout(); plt.show()

BATTERY = [
    # component, games. Every verdict game has at least one LIVE Python agent
    # in the loop (the candidate in Q1, both sides in the cross), so the whole
    # battery is lane L1; lane L0's microseconds pay elsewhere, in the wide
    # screens that choose what enters the battery at all.
    ("Q1 paired replays (535 matchups x 2 agents)", 1070),
    ("live donor cross (21 donors x 64 worlds x 2 seats x 2 agents)", 5376),
    ("robustness preflight (96 episodes)", 96),
    ("parity checks (6 games x 720 turns)", 6),
]
T_L1_CPP = 0.15                        # s/game, measured
T_L1_PY  = 3.2                        # s/game, the official env.run order
cpp = sum(g * T_L1_CPP for _, g in BATTERY)
py  = sum(g * T_L1_PY  for _, g in BATTERY)
total_games = sum(g for _, g in BATTERY)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8), width_ratios=[1.3, 1])
names = [b[0].split(" (")[0] for b in BATTERY]
g_cpp = [g * T_L1_CPP / 60 for _, g in BATTERY]
g_py  = [g * T_L1_PY  / 60 for _, g in BATTERY]
y = range(len(BATTERY))
ax1.barh([i + 0.2 for i in y], g_py,  height=0.38, color="#c0504d", label="official Python engine")
ax1.barh([i - 0.2 for i in y], g_cpp, height=0.38, color="#2e9e6b", label="C++ engine (exact)")
ax1.set_yticks(list(y)); ax1.set_yticklabels(names, fontsize=8.5)
ax1.set_xscale("log"); ax1.set_xlabel("minutes (log scale)")
ax1.set_title(f"One verdict = {total_games:,} games, component by component")
ax1.legend(fontsize=8.5)

ax2.bar(["Python engine", "C++ engine"], [py / 3600, cpp / 3600],
        color=["#c0504d", "#2e9e6b"])
for i, v in enumerate([py / 3600, cpp / 3600]):
    ax2.text(i, v * 1.05, f"{v*60:.0f} min" if v < 1 else f"{v:.1f} h", ha="center")
ax2.set_ylabel("hours per verdict")
ax2.set_ylim(0, py / 3600 * 1.3)
ax2.set_title(f"speedup x{py/cpp:.0f}: verdicts per day {24*3600/py:.1f} -> {24*3600/cpp:,.0f}")
plt.tight_layout(); plt.show()

print(f"battery: {total_games:,} games; C++ {cpp/60:.1f} min vs Python {py/3600:.1f} h "
      f"(x{py/cpp:.0f}). At 5 slots a day and a 2.1-day population half life,")
print("the slow battery cannot be re-run per decision; the fast one is re-run for every slot.")

from math import lgamma, log, exp

def _binom_pmf(n, p):
    """Binomial pmf in log space: O(n) and safe at any n (direct powers
    underflow long before n reaches the sample sizes on this page)."""
    lp, lq = log(p), log(1 - p)
    lc = 0.0
    out = [exp(n * lq)] if n * lq > -745 else [0.0]
    for i in range(1, n + 1):
        lc += log(n - i + 1) - log(i)
        x = lc + i * lp + (n - i) * lq
        out.append(exp(x) if x > -745 else 0.0)
    return out

def sign_test_power(n, p, alpha=0.05):
    """Power of the two-sided exact sign test at true win probability p."""
    null = _binom_pmf(n, 0.5)
    tail, k = 0.0, n + 1
    for i in range(n, -1, -1):
        if tail + null[i] > alpha / 2:
            break
        tail += null[i]
        k = i
    alt = _binom_pmf(n, p)
    return sum(alt[i] for i in range(k, n + 1))

def n_for_effect(p, target=0.80):
    lo, hi = 10, 2000
    while lo < hi:
        mid = (lo + hi) // 2
        if sign_test_power(mid, p) < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

for eff in (0.60, 0.575, 0.55):
    print(f"a real {eff:.1%} paired effect needs {n_for_effect(eff)} games at 80% power")
print(f"power of the OLD 40-game pool against a real 57.5% effect: "
      f"{sign_test_power(40, 0.575):.1%}")

POOLS = {"capped pool (the old default)": 40,
         "submission A, uncapped": 252,
         "submission B, uncapped": 283}
fig, ax = plt.subplots(figsize=(8, 3.2))
bars = ax.barh(list(POOLS), list(POOLS.values()),
               color=["#c0504d", "#2e9e6b", "#2e9e6b"])
bar60 = n_for_effect(0.60)
ax.axvline(bar60, ls="--", c="k", lw=1)
ax.text(bar60 - 6, 0.02, f"n for a real 60% effect ({bar60})",
        fontsize=9, ha="right")
ax.set_xlabel("paired games")
ax.set_title("The cap kept the verdict permanently under-powered")
for b, v in zip(bars, POOLS.values()):
    ax.text(v + 4, b.get_y() + b.get_height() / 2, str(v), va="center")
plt.tight_layout(); plt.show()

import base64, json, zlib

SPECIES_CURVE = json.loads(zlib.decompress(base64.b64decode(
"""eNo1l9uRZSEIRVPpALqs4wOUWKYm/zSG/Zgf19WjgIjI/TPH9/szR/3+rHHv788e+ftzxumfMRaa6p857v79uRx+Y7KtHqmR/Xt+Y3dnStbU2BqbLZbPPQI4Y24CmmZoVVDSzBHAHd8loGo+9R6MmqXVrbOxvjHZhjqQseaIbhfM6BYS1maHu1qHSw5tWTG+TQRbrs9xBPauepdbWE/yHl1V2Fy38Mr+4Kdu6b5JIxutcC8o7DbYQsze7Bzuq4FZARO73WwfPuTYAhXcsQT2HoU+emGXPrUlfWo0pFv4/0yqaBwB2s+iyxsP2Fzc4IKj3qHgE9DSLaIhJSolKuGB085hC3OPQqIBz57i0tLsouL46MsGOhMTgi4KHlbQRaEIjDZLwHbj0OQGe0FNQbsi6esG1DZet/JVA3uKx0NuHKEtj9L04iHnR2VJw1KH1zhCC8zFo2iglcca8FEeSk9Z2IDKVFwl46pbiEicS8p9Dfg+L8euBMmN+aTqUVVxQvk3nHjlxEYLvZN6Gmqh+zLeuuW0RaF3U2gDvr065KsL3oAtN+iDBu7S1WlfmduglMs9XoXglVsbhy1nlGbodr6PQp4sfrqeb2J+t5DxFvb3ePBP8fi2MouSRYODh4uUMl7wgJ4yR4OSkntqXLZUdbmlBmW8oZZyGZ5P5j6ZWx83VDK3gVU1KaN0g4o5sujhkocb0F+K1+LN7hbT5OaS1SX/lvxbyqjFoOg22GIRQ6JbWFkKidLNauB8q3BZSjerASvnx1sPKBXL1/NTLIMpPH5WWm6Eu8zP31b2/Wj+/BTSoHSEdMTg5IQTAK1xyv6uZT4+Aw3JeFpUnlX0HfjwWDCNA1zbpD39iCyBKpq0o5+TdUWDe53bw35mmpTt52Yq2sE0tSy8LBgEIH00FVDgMaXdG21u04DPpo4KlM1Pw2Ul5eGSErxfW9zup/s0bvn8lpIRSM+s5fnL8xfV9AtHb6/t1/fwEJYCEQzzkspS4Da1LLUsPZxWcm2Mn2W/ibNfwyWkoK35qFd5NpMYAEu3UsPUswmkwLWbbwNwBI363JspqKpQwgBT4Dn1s6phn/t2vaGHFuBmtqJ5a8vbh95MgcZeK3ZsNxFZeIO3KA06610y3iGOV5lVj2K8cQQe8PEBN1UbMcHMfps1rPoFlJCtEzs+6CaHj2T7wh6f89FWD4sKQCrSMlKWpERcj/qQj/d67v/PdLYfefAI2objuxmCajtl1OmHH0yPc1m//gzj0GswUQeY09xmmrTCxQHIjYbPPFRRgUdID8scx3vzCNKqsw+HezjcQ4cfTMgA/dGU6c+mK7GhqiBL/omysLIwX/h03KeL5VTBOHN63B5Jx0M69tMecSEChvvXfRiL0kTQaiXydApMuSWPv9odze1+uE9vpjJ8OgGmAiWd/1I1FnjcT0GLlf/T+T99R1DWuE9/pcv59G3J8ncVO/PaT1cJonHdxcau8sS1064fiuuHApXQFY/AnvMFaiIhBDry2lfN7X4KPHZUSSb3c50ymzTI+eOqGgWf+/x8rdrBdJVIrv/gXDurGQK/2kXNI0ijX/4uqyjzqYYFGXFP/8OeA+vZR83/n2HRs4ueihmQDu66S8vkpMZxV5+dXJshsBdepITz7KPH+nc+553HmgeQQUq1LtmmazYw3ecFePzDM1XEAWlSdGmvvnRPnnqq8UFstZSAG1vgx/IFLFXS4DZD0OfOTH//AfR+zs0=""")))
N, S_OBS, F0, TOTAL = 535, 192, 296.1, 488.1
NEED = {"0.8": 1829, "0.9": 2637, "0.95": 3444, "0.99": 5320}

fig, ax = plt.subplots(figsize=(8.5, 4))
ax.plot(range(1, N + 1), SPECIES_CURVE, c="#2e9e6b", label="observed accumulation (mean of 30 orders)")
ax.axhline(TOTAL, ls="--", c="k", lw=1)
ax.text(8, TOTAL + 6, f"Chao1 lower bound on the population: {TOTAL:.0f} species", fontsize=9)
ax.axhline(0.9 * TOTAL, ls=":", c="#c0504d", lw=1)
ax.text(8, 0.9 * TOTAL - 16, f"90% of it = {0.9*TOTAL:.0f} species -> ~{NEED['0.9']:,} games (extrapolated)", fontsize=9)
for mark in (40, N):
    yv = SPECIES_CURVE[mark - 1]
    ax.plot([mark], [yv], "o", c="#c0504d")
    ax.annotate(f"n={mark}: {yv:.0f} species", (mark, yv),
                textcoords="offset points", xytext=(8, -4), fontsize=9)
ax.set_xlabel("games in the pool")
ax.set_ylabel("distinct behaviours seen")
ax.set_title(f"Today's band: {S_OBS} species in {N} games, still climbing")
ax.legend(loc="lower right")
plt.tight_layout(); plt.show()

print(f"seen {S_OBS}, Chao1 unseen >= {F0}, population >= {TOTAL:.0f}")
for t, g in NEED.items():
    print(f"  {float(t):.0%} coverage of the estimated population: ~{g:,} games")

BEST_AGREE = json.loads(zlib.decompress(base64.b64decode(
"""eNqdU1sOhCAQu4oH2BgEFD2L8f7X8AMmLs12O/I16dB5lzPMIcT9M/2y61Ztjj1mPOW3PKwexpld8lh91rfKw95ZPMapeNWf4rP7qD2bH+t676L2paw3DvtT+XAu5mcW9WUYbGr0UlHev6GRYmnuo/TNWLLRI3v5bHk4rPe4yB/9xEp0SozsyG8/q1cc3s+u5mXzMBGj+EonqxS2ToQNplTZS1z/X+/B1w0u9hX2""")))
N1_FAM, N2_SPECIES, M = 17, 192, 0

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.6))
ax1.hist(BEST_AGREE, bins=40, color="#7a4f9d")
ax1.axvline(0.90, ls="--", c="#c0504d")
ax1.text(0.88, ax1.get_ylim()[1] * 0.85, "recapture bar (0.90)", ha="right", fontsize=9)
ax1.text(0.88, ax1.get_ylim()[1] * 0.70,
         f"control: a scripted donor matches\nITSELF across seeds at 0.993", ha="right", fontsize=8.5)
ax1.set_xlabel("best donor agreement per pool species")
ax1.set_ylabel("species")
ax1.set_title(f"max observed: {max(BEST_AGREE):.2f} -> the captures are disjoint")

ms = list(range(0, 21))
chap = [(N1_FAM + 1) * (N2_SPECIES + 1) / (mm + 1) - 1 for mm in ms]
ax2.plot(ms, chap, c="#2e6b8a")
ax2.axhline(488, ls="--", c="k", lw=1)
ax2.text(9, 520, "Chao1 floor from the pool alone (488)", fontsize=8.5)
ax2.set_xlabel("hypothetical overlap m")
ax2.set_ylabel("Chapman estimate of population size")
ax2.set_title("At m = 0 the Chapman estimate is unbounded above")
plt.tight_layout(); plt.show()

print("Chapman at the measured m=0:", (N1_FAM+1)*(N2_SPECIES+1)/(0+1)-1,
      " (read as 'unbounded above', not as a number)")

from math import comb

Q1 = {
    "pool A (252 games)": {"both won": 110, "both lost": 61,
                           "only the candidate": 69, "only the incumbent": 12},
    "pool B (283 games)": {"both won": 124, "both lost": 67,
                           "only the candidate": 81, "only the incumbent": 11},
}

def mcnemar_exact(a, b):
    """Two-sided exact McNemar on the discordant pair counts."""
    n, k = a + b, min(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)

def wilson(k, n, z=1.96):
    ph = k / n
    d = 1 + z * z / n
    c = ph + z * z / (2 * n)
    h = z * ((ph * (1 - ph) + z * z / (4 * n)) / n) ** 0.5
    return (c - h) / d, (c + h) / d

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
colors = ["#bbbbbb", "#dddddd", "#2e9e6b", "#c0504d"]
for ax, (name, q) in zip(axes, Q1.items()):
    bars = ax.bar([k.replace(" ", chr(10)) for k in q], list(q.values()), color=colors)
    for b, v in zip(bars, q.values()):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, str(v), ha="center")
    a, b = q["only the candidate"], q["only the incumbent"]
    lo, hi = wilson(a, a + b)
    ax.set_title(name, fontsize=10)
    ax.text(0.5, -0.46, f"p = {mcnemar_exact(a, b):.2e}   "
            f"discordant share {a/(a+b):.0%} [{lo:.0%}, {hi:.0%}]",
            transform=ax.transAxes, ha="center", fontsize=9)
axes[0].set_ylabel("games")
ca = sum(q["only the candidate"] for q in Q1.values())
cb = sum(q["only the incumbent"] for q in Q1.values())
lo, hi = wilson(ca, ca + cb)
fig.suptitle(f"Combined discordant {ca} to {cb}: share {ca/(ca+cb):.0%} "
             f"[{lo:.0%}, {hi:.0%}], exact p = {mcnemar_exact(ca, cb):.1e}",
             y=1.02)
plt.tight_layout(); plt.subplots_adjust(bottom=0.34); plt.show()

import numpy as np

ns = np.unique(np.geomspace(10, 800, 28).astype(int))
fig, ax = plt.subplots(figsize=(8.5, 4))
for p, c in ((0.55, "#c0504d"), (0.575, "#e69138"), (0.60, "#2e9e6b"), (0.65, "#3d85c6")):
    ax.plot(ns, [sign_test_power(int(n), p) for n in ns], c=c, label=f"true effect {p:.1%}")
ax.axhline(0.80, ls="--", c="k", lw=1)
ax.text(12, 0.815, "80% power", fontsize=9)
for n, lab in ((40, "old cap"), (173, "today's discordant n")):
    ax.axvline(n, ls=":", c="#888", lw=1)
    ax.text(n * 1.03, 0.06, f"{lab} ({n})", rotation=90, fontsize=8, va="bottom")
ax.set_xscale("log")
ax.set_xlabel("paired (discordant) games")
ax.set_ylabel("power of the exact two-sided sign test")
ax.set_title("Read every verdict against the curve its n sits on"
             " (the steps are the exact test's discrete critical values)")
ax.legend(loc="center right", fontsize=9)
plt.tight_layout(); plt.show()

DONOR_CROSS = [["OURS-v7.13_owned", 128, 98095, 128, 93072], ["boatlee-v16-rc5-r5a-recovery", 127, 19396, 124, 13676], ["boatlee-v20-adaptive-r1-multi-route", 128, 21626, 121, 16332], ["bruceqdu-route1", 128, 34828, 128, 31044], ["denizeryilmaz-v16-rc5", 127, 19407, 124, 13687], ["flexonafft-fieldbook-closeout", 127, 1565, 11, -13871], ["flexonafft-multiroute", 128, 21626, 121, 16332], ["indarkarhana-e776-latent-pasture", 125, 7023, 84, 2716], ["kaitofukami-v25-meta-reset", 128, 25438, 125, 20865], ["llccqq624-adaptive-counterbook", 128, 21626, 121, 16332], ["llccqq624-adaptive-shop-guard", 126, 12136, 108, 5364], ["llccqq624-premium-queue-split", 127, 19391, 124, 13664], ["llccqq624-shops-remember-the-route", 126, 12047, 108, 5432], ["maulikgajera-adaptive", 128, 151004, 128, 147484], ["moon_v189c", 115, 8516, 120, 7549], ["pilkwang-precomputed-schedule-policy", 128, 25994, 124, 21327], ["rayk-topmeta-consensus-route", 128, 20354, 120, 15210], ["salemali7-3000-score", 127, 19407, 124, 13687], ["v21-r1-public-state-route-portfolio", 128, 24074, 121, 16556], ["yhay81-two-shop-router", 117, 13438, 123, 1674], ["zakariajoudar-rules", 128, 160814, 128, 155190]]
# columns: donor, candidate wins of 128, candidate mean margin, incumbent wins, incumbent mean margin
DONOR_CROSS.sort(key=lambda r: r[2])
fig, ax = plt.subplots(figsize=(9.5, 7))
y = list(range(len(DONOR_CROSS)))
ax.barh([i + 0.2 for i in y], [r[2] for r in DONOR_CROSS], height=0.38,
        color="#2e9e6b", label="candidate")
ax.barh([i - 0.2 for i in y], [r[4] for r in DONOR_CROSS], height=0.38,
        color="#c0504d", label="incumbent")
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in DONOR_CROSS], fontsize=8)
ax.axvline(0, c="k", lw=0.8)
ax.set_xlabel("mean margin per game, 128 games each (64 worlds x both seats)")
n_games = 128 * len(DONOR_CROSS)
wins_c = sum(r[1] for r in DONOR_CROSS)
wins_i = sum(r[3] for r in DONOR_CROSS)
ax.set_title(f"The live cross: candidate {wins_c:,} of {n_games:,} wins, incumbent {wins_i:,}")
ax.legend(loc="lower right")
plt.tight_layout(); plt.show()

fam = next(r for r in DONOR_CROSS if r[0] == "flexonafft-fieldbook-closeout")
print(f"the family-mirror cell, {fam[0]}:")
print(f"  candidate {fam[1]}/128 at {fam[2]:+,} a game; incumbent {fam[3]}/128 at {fam[4]:+,}")
print("this cell is pure L1: the mirror's value only exists when both sides respond,")
print("while the same layer's safety (0 fires, delta exactly 0.00 on the recorded-rival pool) is pure L0.")

DONOR_BANKS = json.loads(zlib.decompress(base64.b64decode(
"""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""")))
order = sorted(DONOR_BANKS, key=lambda k: -sorted(DONOR_BANKS[k])[len(DONOR_BANKS[k])//2])
fig, ax = plt.subplots(figsize=(9.5, 6.5))
data = [DONOR_BANKS[k] for k in order]
vp = ax.violinplot(data, vert=False, showmedians=True, widths=0.85)
for body in vp["bodies"]:
    body.set_facecolor("#7a4f9d"); body.set_alpha(0.6)
ax.set_yticks(range(1, len(order) + 1))
ax.set_yticklabels(order, fontsize=8)
ax.set_xlabel("the donor's own final bank, 128 games vs the same challenger (64 worlds x both seats)")
ax.set_title("Production across the donor field: two orders of magnitude, family-tight bands")
plt.tight_layout(); plt.show()

med = {k: sorted(v)[len(v)//2] for k, v in DONOR_BANKS.items()}
print(f"median production: best {max(med.values()):,} ({max(med, key=med.get)}), "
      f"floor {min(med.values()):,} ({min(med, key=med.get)})")

SEED_SHOPS_B64 = """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"""
seed_shops = json.loads(zlib.decompress(base64.b64decode(SEED_SHOPS_B64)))
print(f"{len(seed_shops)} seeds; distinct first-two-shop worlds:",
      len({tuple(v) for v in seed_shops.values() if len(v) >= 2}))

seen, curve = set(), []
for sd, pair in seed_shops.items():
    if len(pair) >= 2:
        seen.add(tuple(pair))
    curve.append(len(seen))

fig, ax = plt.subplots(figsize=(8, 3.4))
ax.plot(range(1, len(curve) + 1), curve, c="#2e9e6b")
ax.axhline(64, ls="--", c="k", lw=1)
for n in (3, 12):
    ax.axvline(n, ls=":", c="#c0504d", lw=1)
    ax.annotate(f"{n} seeds -> {curve[n-1]} worlds", (n, curve[n-1]),
                textcoords="offset points", xytext=(8, -12), fontsize=9)
full = next(i for i, v in enumerate(curve, 1) if v == 64)
ax.annotate(f"all 64 worlds reached at seed {full}", (full, 64),
            textcoords="offset points", xytext=(8, -14), fontsize=9)
ax.set_xlabel("seeds taken from the map, in order")
ax.set_ylabel("distinct worlds reached")
ax.set_title("Random seeds accumulate worlds slowly; picking one per world needs 64")
ax.set_xlim(0, 320)
plt.tight_layout(); plt.show()

import hashlib
from pathlib import Path
import pandas as pd

roots = [Path("/kaggle/input")] if Path("/kaggle/input").exists() else []
hits = sorted(h for r in roots for h in r.rglob("donors.csv"))
hits += [Path("donors.csv")] if Path("donors.csv").exists() else []
df = pd.read_csv(hits[0]) if hits else None
if df is None:
    for r in roots:
        print("mounted under", r, ":",
              [str(x) for x in list(r.rglob("*"))[:30]] or "nothing")
    print("donors.csv not found. Attach the dataset "
          "destbreso/kaggriculture-donor-agents-20260902 or place the CSV "
          "beside the notebook; the dataset cells skip gracefully until then.")
else:
    row = df[df.donor_id == "yhay81-two-shop-router"].iloc[0]
    sha = hashlib.sha256(base64.b64decode(row.payload_b64)).hexdigest()
    assert sha == row.main_py_sha256, "payload does not match its recorded sha256"
    print(f"payload check: {row.donor_id} decodes to sha256 {sha[:16]}..., matching the CSV")

    fam = (df.groupby("behaviour_family")
             .agg(agents=("donor_id", lambda s: ", ".join(sorted(s))),
                  members=("donor_id", "size"))
             .sort_values("members", ascending=False))
    print(f"\n{len(df)} agents in {len(fam)} measured behaviour families:")
    display(fam)

    credits = df[["donor_id", "author", "license", "payload_format", "source_url"]].copy()
    credits["author"] = credits.author.str.split("(").str[0].str.strip()
    credits["license"] = credits.license.str.split(";").str[0]
    display(credits.sort_values("donor_id").reset_index(drop=True))

if df is None:
    print("dataset not mounted; genealogy skipped (see the note above)")
else:
    def ngrams(text, n=5):
        toks = text.split()
        return {" ".join(toks[i:i+n]) for i in range(len(toks) - n + 1)}

    payloads = {}
    for _, r in df.iterrows():
        if r.payload_included and r.payload_format == "py":
            payloads[r.donor_id] = ngrams(base64.b64decode(r.payload_b64).decode("utf-8", "replace"))

    names = sorted(payloads)
    import numpy as np
    Msim = np.zeros((len(names), len(names)))
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            inter = len(payloads[a] & payloads[b])
            union = len(payloads[a] | payloads[b]) or 1
            Msim[i, j] = inter / union

    fig, ax = plt.subplots(figsize=(9.5, 8))
    im = ax.imshow(Msim, cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(len(names))); ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=90, fontsize=7.5)
    ax.set_yticklabels(names, fontsize=7.5)
    fig.colorbar(im, label="token 5-gram Jaccard similarity of the source code")
    ax.set_title("Genealogy from the payload column: shared code shows as bright blocks")
    plt.tight_layout(); plt.show()

    # code clans at a 0.5 similarity bar, next to the BEHAVIOUR families
    clans, assigned = [], set()
    for i, a in enumerate(names):
        if a in assigned:
            continue
        clan = [a] + [b for j, b in enumerate(names) if j != i and Msim[i, j] >= 0.5 and b not in assigned]
        assigned.update(clan); clans.append(clan)
    famcol = dict(zip(df.donor_id, df.behaviour_family))
    print(f"{len(names)} sources -> {len(clans)} code clans at Jaccard >= 0.5:")
    for cl in sorted(clans, key=len, reverse=True):
        fams = sorted({famcol[x] for x in cl})
        print(f"  clan of {len(cl)} (families {'/'.join(fams)}): {', '.join(cl)}")
    mx = max((Msim[i, j], names[i], names[j]) for i in range(len(names)) for j in range(i))
    print(f"\nclosest cross-author pair: {mx[1]} ~ {mx[2]} at {mx[0]:.2f}")
    print("read the two partitions together: a code clan with several behaviour families")
    print("is a shared trunk with divergent tuning; one family across low-similarity code")
    print("is convergent behaviour without shared source.")

import copy, importlib.util, sys, time, os
os.environ.setdefault("MPLBACKEND", "Agg")

def load_agent(path, sibling_dir=None):
    """Kaggle's rule: the LAST callable bound at module level is the agent."""
    if sibling_dir:
        sys.path.insert(0, str(sibling_dir))
    try:
        spec = importlib.util.spec_from_file_location(f"agent_{time.time_ns()}", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if sibling_dir:
            sys.path.remove(str(sibling_dir))
    return [v for v in vars(mod).values()
            if callable(v) and getattr(v, "__module__", "") == mod.__name__][-1]

def tape_agent(stream):
    """Wrap a recorded action stream as an agent: plays turn t verbatim."""
    state = {"t": -1}
    def play(obs, cfg=None):
        state["t"] += 1
        return copy.deepcopy(stream[state["t"]]) if state["t"] < len(stream) else \
               {"farmer": ["PASS"], "hands": [], "market": []}
    return play

def one_game(agent_path, rival_stream, seed, our_seat):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": int(seed)})
    me, tape = load_agent(agent_path), tape_agent(rival_stream)
    env.run([me, tape] if our_seat == 0 else [tape, me])
    return float(env.state[our_seat].reward or 0), float(env.state[1 - our_seat].reward or 0)

def paired_verdict(cand_path, inc_path, matchups, verbose=True):
    """matchups: iterable of dicts with 'script', 'seed', 'our_seat'."""
    cells = {"both won": 0, "both lost": 0, "only the candidate": 0, "only the incumbent": 0}
    for mkp in matchups:
        wc = one_game(cand_path, mkp["script"], mkp["seed"], mkp["our_seat"])
        wi = one_game(inc_path,  mkp["script"], mkp["seed"], mkp["our_seat"])
        c, i = wc[0] > wc[1], wi[0] > wi[1]
        key = ("both won" if c and i else "both lost" if not c and not i
               else "only the candidate" if c else "only the incumbent")
        cells[key] += 1
    a, b = cells["only the candidate"], cells["only the incumbent"]
    p = mcnemar_exact(a, b) if a + b else 1.0
    if verbose:
        print(cells)
        print(f"discordant {a}-{b}, exact p = {p:.3g}"
              + ("  [THIN: read power at this n before concluding]" if a + b < 30 else ""))
    return cells, p

# --- demo: two dataset donors, one matchup each way (~4 slow official games) ---
import tempfile
assert df is not None, "the demo needs the donor dataset; attach it and rerun"
tmp = Path(tempfile.mkdtemp())
for did in ("yhay81-two-shop-router", "bruceqdu-route1"):
    r = df[df.donor_id == did].iloc[0]
    (tmp / f"{did}.py").write_bytes(base64.b64decode(r.payload_b64))
rival = load_agent(tmp / "bruceqdu-route1.py")
from kaggle_environments import make
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 11})
env.run([rival, rival])
demo_stream = [s.action for s in [step[0] for step in env.steps[1:]]]
demo_matchups = [{"script": demo_stream, "seed": 11, "our_seat": 0},
                 {"script": demo_stream, "seed": 11, "our_seat": 1}]
paired_verdict(tmp / "yhay81-two-shop-router.py", tmp / "bruceqdu-route1.py", demo_matchups)

RUN_FETCH = False          # flip locally; needs kaggle credentials + your submission id
MY_SUBMISSION_ID = 0

def fetch_pool(submission_id, out_path="my_pool.json"):
    import json, urllib.request
    base = "https://www.kaggle.com/api/i/competitions.EpisodeService/"
    body = json.dumps({"submissionId": submission_id}).encode()
    req = urllib.request.Request(base + "ListEpisodes", data=body,
                                 headers={"Content-Type": "application/json"})
    episodes = json.loads(urllib.request.urlopen(req).read())["episodes"]
    pool = []
    for ep in episodes:
        req = urllib.request.Request(base + "GetEpisodeReplay",
                                     data=json.dumps({"episodeId": ep["id"]}).encode(),
                                     headers={"Content-Type": "application/json"})
        rep = json.loads(json.loads(urllib.request.urlopen(req).read())["replay"])
        seat = next(i for i, ag in enumerate(ep["agents"])
                    if ag["submissionId"] == submission_id)
        rival = 1 - seat
        pool.append({
            "seed": rep["configuration"]["seed"],
            "our_seat": seat,
            "script": [st[rival]["action"] for st in rep["steps"][1:]],
            "recorded_result": (ep["agents"][seat].get("reward"),
                                 ep["agents"][rival].get("reward")),
        })
    json.dump(pool, open(out_path, "w"))
    print(f"{len(pool)} matchups -> {out_path}  (take ALL of them; a cap is a bias)")
    return pool

if RUN_FETCH:
    pool = fetch_pool(MY_SUBMISSION_ID)
    paired_verdict("my_candidate.py", "my_incumbent.py", pool)
else:
    print("RUN_FETCH is off: this cell documents the exact fetcher; flip it locally.")

def live_game(agent_a_path, agent_b_path, seed, sib_a=None, sib_b=None):
    from kaggle_environments import make
    a, b = load_agent(agent_a_path, sib_a), load_agent(agent_b_path, sib_b)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": int(seed)})
    env.run([a, b])
    return float(env.state[0].reward or 0), float(env.state[1].reward or 0)

def live_cross(cand_path, inc_path, donor_dir, seeds, families=None):
    """donor_dir: the dataset's agents/ folder. families: optional donor->family
    map to play one representative per family. Returns wins per agent."""
    wins = {"cand": 0, "inc": 0, "n": 0}
    picked = {}
    for f in sorted(Path(donor_dir).glob("*.py")):
        famv = (families or {}).get(f.stem, f.stem)
        if famv in picked:
            continue
        picked[famv] = f
    for f in picked.values():
        for seed in seeds:
            for us_first in (True, False):
                for tag, path in (("cand", cand_path), ("inc", inc_path)):
                    r = live_game(path, f, seed) if us_first else live_game(f, path, seed)[::-1]
                    wins[tag] += r[0] > r[1]
                    wins["n"] += 0.5
    return wins

def decide(discordant_cand, discordant_inc, cross_cand_wins, cross_inc_wins,
           alpha=0.05):
    """THE decision rule, verbatim from the protocol."""
    p = mcnemar_exact(discordant_cand, discordant_inc)
    replay_says = discordant_cand > discordant_inc
    cross_says = cross_cand_wins > cross_inc_wins
    if p >= alpha:
        return f"NO VERDICT: p={p:.3g}; read the power curve at n={discordant_cand+discordant_inc} and report THIN"
    if replay_says != cross_says:
        return "NO VERDICT: the two populations disagree in order; the disagreement is the finding"
    who = "candidate" if replay_says else "incumbent"
    return (f"VERDICT: field the {who} (p={p:.2g}, both populations agree). "
            f"Any rating delta you computed is an UPPER BOUND; date every number.")

print(decide(150, 23, 2652, 2415))
print(decide(7, 5, 900, 880))
print(decide(60, 10, 1200, 1400))

import datetime as dt

PAIRING_B64 = """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"""
series = json.loads(zlib.decompress(base64.b64decode(PAIRING_B64)))
LABEL = {"55830424": "settled over 3 days",
         "55897276": "displaced on day 1 (fed hardest while newest)",
         "55905246": "settling over 2.5 days",
         "55962203": "2 hours old at capture (the fresh burst)"}

fig, ax = plt.subplots(figsize=(9.5, 4))
for (sub, ts), col in zip(series.items(), ("#3d85c6", "#c0504d", "#2e9e6b", "#e69138")):
    t = [dt.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in ts]
    t0 = t[0]
    span_h = max(1.0, (t[-1] - t0).total_seconds() / 3600)
    import math
    nbin = max(1, math.ceil(span_h / 6))
    counts = [0] * nbin
    for x in t:
        counts[min(nbin - 1, int((x - t0).total_seconds() // (6 * 3600)))] += 1
    xs, ys = [], []
    for k in range(nbin):
        w = min(6.0, span_h - 6 * k) or 0.5
        xs += [6 * k, 6 * k + max(w, 0.5)]
        ys += [counts[k] / max(w, 0.5)] * 2
    ax.plot(xs, ys, lw=1.8, color=col, label=f"{sub}: {LABEL[sub]}")
ax.set_xlabel("hours since the submission's first episode")
ax.set_ylabel("episodes per hour (6h bins)")
ax.set_title("The matchmaker feeds uncertainty: every submission starts hot, then the rate falls as its placement settles")
ax.legend(fontsize=8.5)
plt.tight_layout(); plt.show()

for sub, ts in series.items():
    t = [dt.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in ts]
    first6 = sum(1 for x in t if (x - t[0]).total_seconds() <= 6 * 3600)
    span_h = max(1.0, (t[-1] - t[0]).total_seconds() / 3600)
    print(f"{sub}: {first6} episodes in its first 6 hours; lifetime {len(t)/span_h:.1f}/h over {span_h:.0f}h")

fig, ax = plt.subplots(figsize=(11.5, 6.4))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("Reading the instrument: one output, three exits", fontsize=12.5, pad=10)

box(ax, 0.30, 0.80, 0.40, 0.15, "THE OUTPUT",
    ["discordant a-b   exact p   share CI", "cross wins cand/inc   dates on everything"], "#2e6b8a")

box(ax, 0.02, 0.40, 0.29, 0.27, "EXIT 1: THIN",
    ["p >= alpha, or a+b small", "report smallest detectable", "effect at this n; conclude", "NOTHING, especially not 'no effect'"], "#b0803d")
box(ax, 0.355, 0.40, 0.29, 0.27, "EXIT 2: DISAGREEMENT",
    ["p < alpha but the two", "populations order differently", "no verdict; the disagreement", "IS the finding to chase"], "#a05252")
box(ax, 0.69, 0.40, 0.29, 0.27, "EXIT 3: VERDICT",
    ["p < alpha, orders agree", "field the winner; speak any", "rating delta as an UPPER", "bound; stamp the date"], "#3d7a4f")

arrow(ax, 0.42, 0.80, 0.165, 0.68)
arrow(ax, 0.50, 0.80, 0.50, 0.68)
arrow(ax, 0.58, 0.80, 0.835, 0.68)

box(ax, 0.02, 0.05, 0.46, 0.30, "RAISING POWER, cheapest first",
    ["read BOTH live slots' pools (2x discordants)", "wait: the matchmaker sets the rate (uncertainty-driven)",
     "screen wide on L0 batch (~50 us/game),", "  spend paired games on survivors only",
     "cross one representative per family"], "#444444")
box(ax, 0.52, 0.05, 0.46, 0.30, "STANDING LIMITS",
    ["recordings cannot react (bounded, expiring)", "matchup dependence unmodelled",
     "rating deltas are upper bounds", "population half life 2.1 days:",
     "  rerun per decision, never trust across days"], "#444444")
plt.tight_layout(); plt.show()