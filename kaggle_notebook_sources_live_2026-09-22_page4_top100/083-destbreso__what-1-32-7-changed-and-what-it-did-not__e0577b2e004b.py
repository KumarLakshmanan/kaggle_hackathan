import json, math, os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.6,
    "font.size": 9.5, "axes.titlesize": 11.5, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
OLD_C, NEW_C, CTRL, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"

def find(name, roots=("/kaggle/input", ".", "..", "../..")):
    """Walk for the file rather than guessing Kaggle's mount depth."""
    for r in roots:
        if not os.path.isdir(r):
            continue
        for dirpath, dirnames, filenames in os.walk(r):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            if name in filenames:
                return os.path.join(dirpath, name)
    return None

# THE MEASUREMENT COMES FROM THE ATTACHED DATASET, which is the point: change the
# question and re-run it, or check it against the raw episodes next to it. It was
# produced by replaying 120 recorded episodes with BOTH seats playing their own
# recorded actions and reading market["inventory"] every turn, so nothing of any one
# agent is in the loop.
#
# The literal below is a SNAPSHOT of the same file, carried only so sections 1 to 4
# still render if you read this without attaching anything. Section 5 reads a second
# measurement and stops without the dataset, by design. If the snapshot is ever the
# one in use, the cell says so, loudly, because a hardcoded number cannot be
# re-derived and will drift from its source the moment the source moves.
#
# The snapshot holds the FIELD corpus only, already filtered, which is the same set
# of rows the attached path keeps on the next line.
MEASURED = r"""
{"engine":"1.32.7 installed, 1.32.6 rows vendored from PR 1399",
 "hinge_gain":8.0,"changed":["CARROT", "TOMATO", "EGG"],
 "dominance":{"CARROT":{"worst_delta":-2,"at_scarcity":3,"upto":3000},"TOMATO":{"worst_delta":0,"at_scarcity":null,"upto":3000},"EGG":{"worst_delta":0,"at_scarcity":null,"upto":3000}},
 "reachability":[
  {"item":"WHEAT","knee":400,"episodes":120,"deepest_scarcity":853,"median_scarcity":478,"p75_scarcity":578,"p90_scarcity":660,"episodes_past_knee":87,"frac_past_knee":0.725,"scarcity_by_episode":[225,229,273,278,286,300,300,301,304,312,313,316,317,321,323,324,326,331,340,344,348,352,363,363,364,367,380,383,386,388,388,391,396,404,404,406,411,417,417,420,421,426,426,427,429,434,436,437,439,439,439,440,442,446,452,457,457,473,476,477,479,479,492,496,499,499,500,507,509,511,514,515,515,516,517,520,523,528,529,531,537,544,545,546,555,561,561,565,569,578,579,580,581,584,587,592,593,610,612,613,620,621,622,632,634,657,660,660,681,682,687,690,697,697,704,745,778,836,852,853]},
  {"item":"CARROT","knee":450,"episodes":120,"deepest_scarcity":968,"median_scarcity":316,"p75_scarcity":468,"p90_scarcity":572,"episodes_past_knee":34,"frac_past_knee":0.2833333333333333,"scarcity_by_episode":[25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,28,28,30,55,98,105,126,141,142,144,147,152,161,164,174,177,180,192,195,195,195,198,198,203,204,213,225,231,231,231,233,242,246,249,249,252,255,262,266,267,267,285,285,303,314,318,318,322,324,335,339,339,342,342,342,342,342,348,357,357,357,359,365,386,392,413,413,429,440,444,447,452,464,464,468,468,474,479,491,498,500,504,504,505,518,519,519,552,554,555,557,572,572,573,594,607,624,627,654,662,673,699,699,717,968]},
  {"item":"TOMATO","knee":200,"episodes":120,"deepest_scarcity":660,"median_scarcity":219,"p75_scarcity":300,"p90_scarcity":390,"episodes_past_knee":66,"frac_past_knee":0.55,"scarcity_by_episode":[30,30,30,30,30,30,30,30,30,30,30,30,30,30,66,84,84,84,84,84,85,102,102,102,102,120,120,120,120,120,120,120,120,120,138,138,138,138,138,156,156,156,156,174,174,174,192,192,192,192,192,192,192,192,210,210,210,210,210,210,228,228,228,228,228,228,228,228,246,246,246,246,246,246,264,264,264,264,264,264,282,282,282,282,282,282,300,300,300,300,300,300,300,300,300,300,318,318,318,318,336,336,336,336,354,372,372,390,390,408,408,408,426,426,462,498,516,516,588,660]},
  {"item":"STRAWBERRY","knee":100,"episodes":120,"deepest_scarcity":343,"median_scarcity":129,"p75_scarcity":183,"p90_scarcity":238,"episodes_past_knee":75,"frac_past_knee":0.625,"scarcity_by_episode":[14,14,16,16,16,16,21,21,33,40,40,44,50,54,54,57,57,58,59,59,59,64,72,72,75,75,76,76,76,77,80,81,82,82,90,91,93,93,93,93,93,93,95,100,100,103,108,111,111,111,112,113,113,114,118,125,125,126,126,129,129,131,132,136,136,141,144,147,147,148,148,150,150,150,152,157,162,162,162,164,164,165,167,168,168,169,172,175,182,183,188,192,198,202,203,204,207,222,222,222,224,224,224,225,225,232,236,238,242,243,244,250,255,261,266,268,300,301,328,343]},
  {"item":"MELON","knee":300,"episodes":120,"deepest_scarcity":11,"median_scarcity":11,"p75_scarcity":11,"p90_scarcity":11,"episodes_past_knee":0,"frac_past_knee":0.0,"scarcity_by_episode":[11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]},
  {"item":"EGG","knee":332,"episodes":120,"deepest_scarcity":678,"median_scarcity":228,"p75_scarcity":336,"p90_scarcity":426,"episodes_past_knee":31,"frac_past_knee":0.25833333333333336,"scarcity_by_episode":[30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,66,66,84,102,102,102,102,102,120,120,120,120,120,120,120,120,138,138,138,156,156,156,156,156,156,156,156,174,174,174,174,174,174,192,192,192,192,192,192,210,210,210,210,228,228,228,228,228,228,228,228,228,228,228,246,246,246,246,246,246,246,264,264,264,264,264,264,282,282,282,282,300,300,300,336,336,336,336,336,336,336,336,336,336,354,372,372,390,408,408,408,408,426,426,426,426,444,462,462,480,498,516,516,552,678]},
  {"item":"MILK","knee":122,"episodes":120,"deepest_scarcity":253,"median_scarcity":29,"p75_scarcity":50,"p90_scarcity":93,"episodes_past_knee":5,"frac_past_knee":0.041666666666666664,"scarcity_by_episode":[9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,10,14,14,22,22,23,23,23,23,23,23,23,23,23,24,24,24,24,27,27,27,27,27,27,32,32,32,32,33,33,33,34,37,40,40,41,41,41,41,41,42,42,42,45,45,45,45,46,46,46,50,50,50,50,50,51,51,51,52,52,52,55,62,68,68,69,69,70,84,86,90,93,94,99,103,104,110,110,120,147,152,153,203,253]},
  {"item":"WOOL","knee":105,"episodes":120,"deepest_scarcity":608,"median_scarcity":7,"p75_scarcity":89,"p90_scarcity":250,"episodes_past_knee":28,"frac_past_knee":0.23333333333333334,"scarcity_by_episode":[7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,11,12,14,24,28,34,42,43,46,50,50,51,53,54,56,58,70,86,86,89,89,102,105,107,107,113,118,120,127,138,143,163,167,179,179,191,194,236,250,270,302,316,339,339,352,420,430,430,446,466,608]},
  {"item":"FERTILIZER","knee":200,"episodes":120,"deepest_scarcity":0,"median_scarcity":0,"p75_scarcity":0,"p90_scarcity":0,"episodes_past_knee":0,"frac_past_knee":0.0,"scarcity_by_episode":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}
 ]}
"""
path = find("engine_delta.json")
if path:
    D = json.loads(Path(path).read_text())
    D["reachability"] = [r for r in D["reachability"] if r["corpus"] == "field"]
    print("SOURCE: the attached dataset,", path)
else:
    D = json.loads(MEASURED)
    print("SOURCE: the embedded snapshot, so sections 1 to 4 render. Attach")
    print("        destbreso/kaggriculture-benchmark-matchups")
    print("        to read the measurement itself rather than a copy of it,")
    print("        and to run section 5, which needs a second file.")
print("engine it was taken on:", D["engine"])
print("HINGE_GAIN =", D["hinge_gain"], "  changed goods:", D["changed"])
print("goods measured:", len(D["reachability"]),
      " episodes per good:", D["reachability"][0]["episodes"])

# Both parameter sets, so the two curves go through ONE function and are
# comparable by construction. The 1.32.6 rows are transcribed from PR 1399's own
# diff and were verified against a real 1.32.6 install.
I0, FLOOR = 10000, 1
NEW = {
 'WHEAT':      dict(base= 25, T=400, below='sqrt',   bt=0.80),
 'CARROT':     dict(base= 35, T=450, below='hinge',  bt=1.00),
 'TOMATO':     dict(base= 60, T=200, below='hinge',  bt=0.40),
 'STRAWBERRY': dict(base=120, T=100, below='sqrt',   bt=0.70),
 'MELON':      dict(base=250, T=300, below='log',    bt=0.20),
 'EGG':        dict(base= 50, T=332, below='hinge',  bt=0.40),
 'MILK':       dict(base=160, T=122, below='sqrt',   bt=0.60),
 'WOOL':       dict(base=200, T=105, below='log',    bt=0.20),
 'FERTILIZER': dict(base=100, T=200, below='linear', bt=0.40),
}
OLD_ROWS = {'CARROT': dict(below='log', bt=0.20),
            'TOMATO': dict(below='linear', bt=0.40),
            'EGG':    dict(below='linear', bt=0.40)}
OLD = {k: dict(v) for k, v in NEW.items()}
for k, patch in OLD_ROWS.items():
    OLD[k].update(patch)
CHANGED = list(OLD_ROWS)

def shape(f, x, T):
    x = max(0.0, x)
    if f == 'linear': return x
    if f == 'sq':     return x * x
    if f == 'sqrt':   return math.sqrt(x)
    if f == 'log':    return math.log1p(x)
    if f == 'hinge':
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    raise ValueError(f)

def price(good, scarcity, P):
    """The engine's market_price, restricted to the scarcity branch."""
    p = P[good]
    amp = p['bt'] * p['base'] / shape(p['below'], p['T'], p['T'])
    return max(FLOOR, int(round(p['base'] + amp * shape(p['below'], scarcity, p['T']))))

print(f"{'good':<12}{'below_func':>22}{'below_target':>16}{'knee T':>9}")
for g in CHANGED:
    func = OLD[g]['below'] + ' -> ' + NEW[g]['below']
    tgt = "{:.2f} -> {:.2f}".format(OLD[g]['bt'], NEW[g]['bt'])
    print(f"{g:<12}{func:>22}{tgt:>16}{NEW[g]['T']:>9}")

# Which build is the reader on? A behavioural check beats a version string.
try:
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    live = K.market_price('CARROT', I0 - 1000)
    print(f"\ninstalled engine prices carrot at 1,000 short: ${live}")
    print("this notebook says 1.32.6 would be "
          f"${price('CARROT', 1000, OLD)} and 1.32.7 ${price('CARROT', 1000, NEW)}")
    print("=> you are on", "1.32.7 or later" if live == price('CARROT', 1000, NEW)
          else "1.32.6 or earlier" if live == price('CARROT', 1000, OLD) else "something else")
except Exception as e:
    print("\nno engine installed here, the arithmetic below does not need one")

moved = [(g, s) for g in NEW if g not in CHANGED
         for s in range(0, 3001)
         if price(g, s, OLD) != price(g, s, NEW)]
print(f"untouched goods that moved anyway: {len(moved)}   (expected 0)")

# And the property that decides how much old work has to be recomputed:
# is the new curve EVER below the old one?
print("\nis the new curve ever below the old one, scarcity 0..3000?")
for g in CHANGED:
    d = [(price(g, s, NEW) - price(g, s, OLD), s) for s in range(3001)]
    worst, at = min(d)
    print(f"  {g:<8} worst {worst:+d}" + (f" at scarcity {at}" if worst < 0 else ", never below"))

# Already restricted to the FIELD corpus where it was loaded, on both paths, so
# filtering again here would read a key the embedded snapshot does not carry.
reach = {r["item"]: r for r in D["reachability"]}
fig, axes = plt.subplots(1, 4, figsize=(15.0, 4.3))

for ax, g in zip(axes, CHANGED + ["MELON"]):
    r = reach[g]
    T = NEW[g]["T"]
    hi = max(int(r["deepest_scarcity"] * 1.15), T + 60)
    xs = np.arange(0, hi)
    same = g not in CHANGED          # untouched goods: the two curves coincide
    ax.plot(xs, [price(g, s, OLD) for s in xs], color=OLD_C, lw=3.0, label="1.32.6")
    ax.plot(xs, [price(g, s, NEW) for s in xs], color=NEW_C, lw=2.0,
            ls="--" if same else "-", label="1.32.7")
    ax.axvline(T, color=MUTED, lw=1.0, ls="--")
    ax.annotate(f"knee {T}", xy=(T, ax.get_ylim()[1] * 0.94), xytext=(4, 0),
                textcoords="offset points", color=MUTED, fontsize=8.5, va="top")

    # where real games got to, on a twin axis so the shapes never compete
    obs = np.array(r["scarcity_by_episode"])
    tw = ax.twinx()
    tw.hist(obs, bins=22, range=(0, hi), color=INK, alpha=0.16, lw=0)
    tw.set_yticks([]); tw.grid(False)
    for s in ("top", "right", "left"):
        tw.spines[s].set_visible(False)

    frac = 100 * r["frac_past_knee"]
    ax.set_title(f"{g.title()}\n{r['episodes_past_knee']}/{r['episodes']} games past the knee"
                 f" ({frac:.1f} %)", fontsize=10.5)
    ax.set_xlabel("how short the market is (units)")
    if g == CHANGED[0]:
        ax.set_ylabel("price of the next unit ($)")
        ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, max(price(g, hi - 1, NEW) * 1.05, 60))

axes[-1].set_title(f"Melon, the control\n0/{reach['MELON']['episodes']} games past the knee"
                   f" (deepest {reach['MELON']['deepest_scarcity']})", fontsize=10.5)
fig.suptitle("Two curves, and the shaded histogram is where 120 real games actually sat",
             y=1.03, fontsize=12, fontweight="bold")
plt.tight_layout(); plt.show()

ANNOUNCED = {"TOMATO": 50, "CARROT": 26, "EGG": 22}
rows = []
for g in ("TOMATO", "CARROT", "EGG", "MELON"):
    r = reach[g]
    rows.append((g, ANNOUNCED.get(g), 100 * r["frac_past_knee"],
                 r["episodes_past_knee"], r["episodes"]))

print(f"{'good':<12}{'announced':>11}{'measured':>10}{'games':>10}")
for g, a, m, k, n in rows:
    print(f"{g:<12}{(str(a)+' %') if a else 'untouched':>11}{m:>9.1f} %{f'{k}/{n}':>10}")

fig, ax = plt.subplots(figsize=(7.4, 3.9))
lbl = [r[0].title() for r in rows]
x = np.arange(len(rows))
ax.bar(x - 0.19, [r[1] or 0 for r in rows], 0.36, color=OLD_C, label="announced by the change")
ax.bar(x + 0.19, [r[2] for r in rows], 0.36, color=NEW_C, label="measured on 120 replayed games")
for i, r in enumerate(rows):
    if r[2] > 0.5:
        ax.annotate(f"{r[2]:.1f} %", xy=(i + 0.19, r[2]), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=9, color=INK)
ax.annotate("melon is the control:\nnot touched, never reached", xy=(3, 2),
            xytext=(3, 30), ha="center", fontsize=9, color=CTRL, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=CTRL, lw=1.3))
ax.set_xticks(x); ax.set_xticklabels(lbl)
ax.set_ylabel("share of games reaching the new branch (%)")
ax.set_title("The announced firing rates, and the same thing measured another way")
ax.legend(loc="upper right")
plt.tight_layout(); plt.show()

print(f"{'good':<12}{'curve':>9}{'knee':>7}{'games past it':>15}{'deepest':>9}")
for g in sorted(reach, key=lambda k: -reach[k]["frac_past_knee"]):
    r = reach[g]
    tag = "hinge" if g in CHANGED else NEW[g]["below"]
    hit = "{}/{} ({:.0f} %)".format(r["episodes_past_knee"], r["episodes"],
                                    100 * r["frac_past_knee"])
    print(f"{g:<12}{tag:>9}{r['knee']:>7}{hit:>15}{r['deepest_scarcity']:>9,}")

def sell(good, scarcity, n, P):
    """Engine-exact: re-quote every unit as the market fills up."""
    return sum(price(good, scarcity - k, P) if scarcity - k > 0 else P[good]['base']
               for k in range(n))

LEVELS = [("median_scarcity", "median game"), ("p75_scarcity", "p75"),
          ("p90_scarcity", "p90"), ("deepest_scarcity", "deepest of 120")]
val = {}
print(f"{'good':<10}{'at':<17}{'short':>7}{'1.32.6':>10}{'1.32.7':>10}{'x':>7}{'gain':>10}")
for g in CHANGED:
    val[g] = []
    for key, lab in LEVELS:
        s = reach[g][key]
        a, b = sell(g, s, 100, OLD), sell(g, s, 100, NEW)
        val[g].append((lab, s, a, b, b / a))
        print(f"{g:<10}{lab:<17}{s:>7,}{a:>10,}{b:>10,}{b/a:>7.2f}{b-a:>+10,}")
    print()

fig, ax = plt.subplots(figsize=(8.2, 4.2))
for g, col in zip(CHANGED, (NEW_C, OLD_C, CTRL)):
    ys = [v[4] for v in val[g]]
    ax.plot(range(len(ys)), ys, "o-", color=col, lw=2.2, ms=7, label=g.title(),
            markeredgecolor="white", markeredgewidth=1.1)
    ax.annotate(f"{ys[-1]:.1f}x", xy=(len(ys) - 1, ys[-1]), xytext=(6, 0),
                textcoords="offset points", color=col, fontsize=9.5, fontweight="bold",
                va="center")
ax.axhline(1.0, color=MUTED, lw=1.0, ls=":")
ax.axhline(2.0, color=MUTED, lw=0.8, ls=":", alpha=0.6)
# log y, because on a linear axis the deepest game squashes the median, p75 and
# p90 into one indistinguishable line at the bottom, which is the part the
# section is actually about.
ax.set_yscale("log")
ax.set_yticks([1, 1.5, 2, 3, 5, 10])
ax.get_yaxis().set_major_formatter(plt.matplotlib.ticker.FuncFormatter(
    lambda v, _: f"{v:g}x"))
ax.set_ylim(0.92, 13)
ax.set_xlim(-0.25, len(LEVELS) - 0.55)
# The 1x and 2x reference lines are labelled by the y axis itself. An annotation
# on either one lands on the data or on an x tick label, so the prose carries it.
ax.set_xticks(range(len(LEVELS))); ax.set_xticklabels([l for _, l in LEVELS])
ax.set_ylabel("revenue on 1.32.7, as a multiple of 1.32.6")
ax.set_title("What 100 units are worth, at four points of the same 120 games\n"
             "log scale, because on a linear one the deepest game flattens the rest",
             fontsize=11)
ax.legend(loc="upper left")
plt.tight_layout(); plt.show()

# COMPUTED, not quoted. Three companion measurements from the same dataset, each
# raw enough that the headline is derived here rather than retyped.
import statistics
inv_path = find("engine_invariance.json")
if not inv_path:
    raise SystemExit("attach destbreso/kaggriculture-benchmark-matchups for this section")
INV = json.loads(Path(inv_path).read_text())

# 1. Does the harness reproduce what the ladder recorded?
gate = INV["engine_gate"]["rows"]
errs = [abs(r["replayed"] - r["recorded"]) for r in gate]
exact = sum(1 for e in errs if e <= 1.0)
print("1. RECORDED EPISODES REPLAY IDENTICALLY ON EITHER BUILD")
print(f"   {exact} of {len(gate)} recorded ladder banks reproduced to the dollar,"
      f" median error ${statistics.median(errs):,.0f}")
print("   A recorded episode has both sides fixed, so nothing in it can respond")
print("   to a price it never queried.\n")

# 2. Same agent, seed and opponent; only the build differs.
# Pair on (agent, game). Two agents played the same 112 seeds, so keying on the
# game alone collapses them and silently halves the sample to 112.
A = {(r["agent"], r["game"]): r for r in INV["build_ab"]["rows_1326"]}
B = {(r["agent"], r["game"]): r for r in INV["build_ab"]["rows_1327"]}
keys = sorted(set(A) & set(B))
d = [B[k]["bank"] - A[k]["bank"] for k in keys]
rel = sorted(100 * x / A[k]["bank"] for k, x in zip(keys, d) if A[k]["bank"])

def nearest_rank(xs, q):
    """The same convention section 4 uses, so the two agree."""
    return xs[min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))]

flip = sum(1 for k in keys
           if (A[k]["bank"] > A[k]["opponent_bank"]) != (B[k]["bank"] > B[k]["opponent_bank"]))
print("2. THE COUNTERFACTUAL GAME DOES MOVE, AND CHANGES NO VERDICT")
print(f"   {len(keys)} replicas   {sum(1 for x in d if x):d} banks moved"
      f"   median {statistics.median(rel):+.2f} %"
      f"   p95 {nearest_rank(rel, 0.95):+.2f} %")
print(f"   worst {min(d):+,.0f}   best {max(d):+,.0f}"
      f"   winners flipped: {flip} of {len(keys)}\n")

# 3. The ceiling is a sum over market_price, so only its arithmetic moved.
pu = INV["purse"]
print("3. THE CLOSED-FORM CEILING ON TOTAL MONEY BARELY MOVES")
print(f"   both banks combined, same {pu['1.32.7']['seeds']} seeds:")
for lab, key in (("at median demand", "total_median"), ("at the most generous draw", "total_max")):
    o, n = pu["1.32.6"][key], pu["1.32.7"][key]
    print(f"     {lab:<26} {o:>11,.0f} -> {n:>11,.0f}   x{n/o:.3f}")
obs = pu["1.32.7"]["observed"]
print(f"   episodes above the ceiling, out of {obs['n']:,}: {obs['above_ceiling']}\n")

print("4. AND THE REASON THE LEDGERS DO NOT MOVE IS NOT THAT THE CODE IS COLD")
for g in CHANGED:
    r = reach[g]
    print(f"   {g:<8} branch reached in {100*r['frac_past_knee']:>4.1f} % of games,"
          f" and almost nobody sells it")