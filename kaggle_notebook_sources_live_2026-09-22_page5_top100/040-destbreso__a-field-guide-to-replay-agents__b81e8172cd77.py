import math
import matplotlib.pyplot as plt

BLUE, ORANGE = "#2F6690", "#C8663A"
RAMP = ["#A8C3D9", "#5C8CB4", "#2F6690"]        # magnitude, light to dark
INK, MUTED, GRID = "#1F2933", "#6B7280", "#E3E7EB"

plt.rcParams.update({
    "figure.dpi": 120, "font.size": 9.5,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.axisbelow": True,                     # grid under the marks, not through

    "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": GRID, "grid.linewidth": 0.8, "figure.facecolor": "white",
})

def agent(obs):
    turn = obs["day"] * 24 + obs["hour"]         # never obs["step"], see below
    if turn < len(TAPE):
        return TAPE[turn]
    return {"farmer": ["PASS"], "hands": [], "market": []}

# Sixteen public agents, decompacted. Tape share = fraction of the payload
# that decodes to recorded actions; code lines = the visible source around it.
shares = [99, 94, 75, 75, 75, 72, 66, 65, 56, 55, 54, 42, 40, 31, 0, 0]
lines  = [26, 196, 908, 911, 911, 1059, 1076, 742, 209, 212, 219, 354, 381, 636, 2142, 246]

fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4))
y = range(len(shares))
ax = axes[0]
ax.barh(list(y), shares, color=[BLUE if s else MUTED for s in shares], height=0.65)
ax.set_yticks(list(y), [f'agent {chr(65+k)}' for k in y], fontsize=8)
ax.invert_yaxis(); ax.set_xlabel('tape share of payload, %')
ax.set_title('most of the agent is a recording', loc='left')
ax = axes[1]
ax.scatter(lines, shares, s=42, color=BLUE)
ax.set_xlabel('lines of visible code'); ax.set_ylabel('tape share, %')
ax.set_title('and code volume does not buy tape freedom', loc='left')
for ax in axes:
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.show()


# transcribed from the engine at 1.32.7, verified exact in 1,863 of 1,863
# quotes against the real market_price
PRICE_FLOOR, I0 = 1, 10_000
P = {  # base, knee T, curve below the neutral inventory, curve above it
    "WHEAT":      (25,  400, "sqrt",  0.8, "log",    0.2),
    "CARROT":     (35,  450, "hinge", 1.0, "sqrt",   0.7),
    "TOMATO":     (60,  200, "hinge", 0.4, "sqrt",   0.6),
    "STRAWBERRY": (120, 100, "sqrt",  0.7, "linear", 1.6),
    "MELON":      (250, 300, "log",   0.2, "sq",     3.6),
    "EGG":        (50,  332, "hinge", 0.4, "log",    0.2),
    "MILK":       (160, 122, "sqrt",  0.6, "linear", 1.6),
    "WOOL":       (200, 105, "log",   0.2, "sq",     3.2),
}

def shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq":     return x * x
    if f == "sqrt":   return math.sqrt(x)
    if f == "hinge":                                    # new in 1.32.7
        u = x / T
        return u if u <= 1.0 else u + 8.0 * (u - 1.0) ** 2
    return math.log(1.0 + x)

def price(item, inventory):
    base, T, bf, bt, af, at = P[item]
    if inventory < I0:
        amp = bt * base / shape(bf, T, T)
        v = base + amp * shape(bf, I0 - inventory, T)
    else:
        amp = at * base / shape(af, T, T)
        v = base - amp * shape(af, inventory - I0, T)
    return max(PRICE_FLOOR, int(round(v)))              # <-- an INTEGER

print("selling milk one unit at a time into a neutral book:")
for k in range(6):
    print(f"  unit {k + 1}: ${price('MILK', I0 + k)}")

def flat_runs(item, span=300):
    """How many units sell at the SAME quoted price, step by step."""
    runs, cur, prev = [], 1, price(item, I0)
    for k in range(1, span):
        q = price(item, I0 + k)
        if q == prev:
            cur += 1
        else:
            runs.append(cur); cur, prev = 1, q
    runs.append(cur)
    return sorted(runs)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 3.6))

# LEFT: the staircase, the thing a derivative cannot see
sold = list(range(0, 260))
ax1.step(sold, [price("WHEAT", I0 + s) for s in sold], where="post",
         color=BLUE, lw=2)
ax1.set_title("The price is a staircase, not a curve")
ax1.set_xlabel("units of wheat sold into a neutral book")
ax1.set_ylabel(r"\$ per unit")
ax1.grid(axis="y")
r = flat_runs("WHEAT")
med = r[len(r) // 2]
ax1.annotate(f"the median step is {med} units wide.\n"
             f"Sell {med} and the quote does not move.\n"
             f"Sell one more and it costs a dollar\non every unit after it.",
             xy=(140, price("WHEAT", I0 + 140)),
             xytext=(0.30, 0.62), textcoords="axes fraction",
             color=INK, fontsize=8.5, va="top",
             arrowprops=dict(arrowstyle="->", color=MUTED, lw=1))
ax1.set_ylim(price("WHEAT", I0 + 259) - 0.6, price("WHEAT", I0) + 0.6)

# RIGHT: the 1.32.7 hinge, against a same-shaped control
short = list(range(0, 600))
ax2.plot(short, [price("TOMATO", I0 - s) for s in short], color=ORANGE, lw=2)
ax2.plot(short, [price("STRAWBERRY", I0 - s) for s in short], color=BLUE, lw=2)
ax2.axvline(P["TOMATO"][1], color=MUTED, lw=1, ls=(0, (4, 3)))
ax2.set_title("And past the knee it runs away")
ax2.set_xlabel("units of scarcity below the neutral book")
ax2.set_ylabel(r"\$ per unit")
ax2.set_xlim(0, 760)
ax2.grid(axis="y")
ax2.text(612, price("TOMATO", I0 - 600), " tomato, hinge", color=ORANGE,
         fontsize=9, va="center", fontweight="bold")
ax2.text(612, price("STRAWBERRY", I0 - 600), " strawberry, sqrt", color=BLUE,
         fontsize=9, va="center", fontweight="bold")
ax2.text(216, ax2.get_ylim()[1] * 0.9, "knee, T = 200", color=MUTED, fontsize=8)
fig.tight_layout()
plt.show()

# docs/FIELD_DRIFT.md section 7: pairwise turn-by-turn agreement between two
# top-ten routes, by in-game day band. Reproduced independently by the schedule
# census, which counts byte-exact hash identity instead of pairwise agreement.
BANDS = ["0-3", "3-7", "7-14", "14-21", "21-30"]
A = [93.1, 77.1, 75.6, 61.9, 56.7]          # top-ten route pair 1
B = [90.3, 79.2, 59.5, 45.8, 40.5]          # top-ten route pair 2

fig, ax = plt.subplots(figsize=(7.4, 3.2))
x = range(len(BANDS))
ax.plot(x, A, color=BLUE, lw=2, marker="o", ms=6)
ax.plot(x, B, color=ORANGE, lw=2, marker="o", ms=6)
ax.set_xticks(list(x), BANDS)
ax.set_ylim(0, 100)
ax.set_xlabel("in-game days")
ax.set_ylabel("turn-by-turn agreement, %")
ax.set_title("Two top-ten routes agree at the start and part at the end")
ax.grid(axis="y")
ax.text(4.08, A[-1], f" {A[-1]:.0f} %  rank 4 vs rank 19", color=BLUE,
        va="center", fontsize=8.5, fontweight="bold")
ax.text(4.08, B[-1], f" {B[-1]:.0f} %  rank 4 vs route pair", color=ORANGE,
        va="center", fontsize=8.5, fontweight="bold")
ax.set_xlim(-0.2, 6.6)
# the margin is generated LATE, so the shading goes on the day axis
ax.axvspan(2.5, 4.0, color=GRID, alpha=0.55, zorder=0)
ax.text(3.25, 6, "where the margin\nis generated", color=MUTED, fontsize=8.5,
        ha="center")
fig.tight_layout()
plt.show()

# docs/GENETIC_POTENTIAL.md, 1,492 real episodes of the top ten.
# Points are labelled by RANK: two of the ten teams carry names in scripts
# matplotlib has no glyphs for, and a chart must not print a box where a name
# goes. The names are in the table below.
TEAMS = [   # rank, plan aligned %, mutable turns, medoid
    (2, 83, 142, 0.989), (8, 81, 140, 0.993), (9, 81, 35, 0.984),
    (5, 32, 19, 0.816),  (3, 25, 21, 0.914),  (4, 24, 29, 0.702),
    (1, 19, 23, 0.474),
]
OFF = {2: (0, 1.1), 8: (0, -1.4), 9: (0, 1.1), 5: (0, -1.4),
       3: (0, 1.1), 4: (0, 1.1), 1: (0, -1.4)}

fig, ax = plt.subplots(figsize=(7.8, 4.0))
for rank, plan, mut, medoid in TEAMS:
    usable = medoid >= 0.9
    y = 100 * mut / 719
    ax.scatter(plan, y, s=190 if usable else 150,
               color=BLUE if usable else ORANGE,
               marker="o" if usable else "X", zorder=3,
               edgecolor="white", linewidth=1.3)
    dx, dy = OFF[rank]
    ax.annotate(f"rank {rank}", (plan + dx, y + dy), fontsize=9,
                ha="center", color=INK, fontweight="bold", zorder=4)
ax.set_xlabel("share of turns whose PLAN repeats across the team's own episodes, %")
ax.set_ylabel("turns the source itself varied, %")
ax.set_title("Holding a plan and varying a market are two different things")
ax.grid(True)
ax.set_xlim(10, 95)
ax.set_ylim(-2.5, 24)
ax.scatter([], [], color=BLUE, s=120,
           label="medoid 0.9 or better: a fixed plan exists to take")
ax.scatter([], [], color=ORANGE, s=110, marker="X",
           label="medoid below 0.9: the method reports itself inapplicable")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
fig.tight_layout()
plt.show()

# The selection funnel that ate itself: per-world edits of a tape, measured
# at one seed, a second, and then a third the selection never touched.
stages = ['gain at the\nscreen seed', 'cleared the\nthreshold', 'survived a\nsecond seed', 'still winning\nat a third']
n      = [46, 37, 13, 3]

fig, ax = plt.subplots(figsize=(7.6, 3.4))
ax.bar(range(4), n, color=[BLUE, BLUE, BLUE, ORANGE], width=0.62)
for k, v in enumerate(n):
    ax.text(k, v + 0.8, str(v), ha='center', fontsize=11, color=INK)
ax.set_xticks(range(4), stages, fontsize=9)
ax.set_ylabel('worlds (of 64)')
ax.set_title('two seeds of selection still overfit', loc='left')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.show()


# research/texture_classes.py, the three families and their centroids
FAM = [{"win_rate": 53.67, "routes": 112, "c": {"turns that sell": 0.4015, "sell concentration": 0.4135, "land bought": 0.2057}},
       {"win_rate": 38.75, "routes": 168, "c": {"turns that sell": 0.2331, "sell concentration": 0.5349, "land bought": 0.2222}},
       {"win_rate": 23.24, "routes":  64, "c": {"turns that sell": 0.1507, "sell concentration": 0.8035, "land bought": 0.2208}}]
NAMES = ["spreads the selling", "middling", "holds, then dumps"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.6),
                               gridspec_kw={"width_ratios": [1, 1.2]})

wr = [f["win_rate"] for f in FAM]
ax1.barh(range(len(FAM)), wr, color=RAMP[::-1], height=0.6)
ax1.set_yticks(range(len(FAM)),
               [f"{n}\n{f['routes']} routes" for n, f in zip(NAMES, FAM)])
ax1.invert_yaxis()
ax1.set_xlabel("win rate against a fixed panel, %")
ax1.set_title("Texture alone splits the field by 30 points")
ax1.grid(axis="x")
for i, v in enumerate(wr):
    ax1.text(v + 1.4, i, f"{v:.1f}%", va="center", color=INK,
             fontsize=9, fontweight="bold")
ax1.set_xlim(0, 68)

keys = ["turns that sell", "sell concentration", "land bought"]
labels = ["turns that\nsell", "sell\nconcentration", "land bought\n(turn / 720)"]
w = 0.26
for k, (nm, f) in enumerate(zip(NAMES, FAM)):
    ax2.bar([i + (k - 1) * w for i in range(3)],
            [f["c"][key] for key in keys],
            width=w - 0.02, color=RAMP[::-1][k], label=nm)
ax2.set_xticks(range(3), labels)
ax2.set_ylabel("centroid value")
ax2.set_title("And the difference is entirely in the selling")
ax2.legend(frameon=False, fontsize=8.5, loc="upper left")
ax2.grid(axis="y")
fig.tight_layout()
plt.show()

# The same profile, shown as it actually is: a DISTRIBUTION per indicator,
# one dot per real episode (245 for the leader, 103 for the mid agent),
# jittered vertically, alpha so concentration reads as density. Each row is
# normalised to the LEADER'S MEDIAN, marked at 1; the tick above each cloud
# is that side's median. Points beyond 6x are drawn at the edge.
import json, random
DIST = json.loads('{"leader":{"land2":[5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],"land3":[8,8,8,8,8,8,8,8,8,8,8,8,8,9,9,8,8,8,8,10,8,8,9,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,9,8,8,8,8,8,9,9,8,8,8,9,8,8,8,8,8,9,8,9,8,8,9,8,8,8,8,9,8,8,8,8,8,8,8,9,8,8,8,8,9,8,8,8,8,8,8,8,8,8,8,8,9,8,9,8,8,9,9,8,8,8,8,9,8,8,8,9,8,8,8,8,9,8,9,8,9,8,9,8,8,9,8,10,8,9,8,8,8,9,8,8,8,9,10,10,8,8,8,8,8,8,8,8,9,8,8,10,8,8,8,8,9,9,8,8,8,8,8,8,8,8,9,9,8,8,8,8,8,8,8,8,8,8,10,8,8,8,8,8,8,8,8,9,9,8,9,8,8,9,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,9,9,8,8,9,9,8,8,8,8,9,8,9,9,8,8,8],"pass_work":[335,339,334,326,335,336,326,336,332,330,339,346,331,340,319,331,332,322,323,324,325,329,333,337,339,342,321,332,331,317,322,320,329,325,329,324,316,320,326,328,324,322,323,320,331,321,322,316,321,323,319,325,315,328,319,326,318,314,336,316,321,321,318,321,317,325,329,319,314,317,324,331,318,320,322,324,325,328,320,316,330,317,319,313,327,325,325,323,334,318,314,327,326,322,325,317,332,317,316,324,328,313,324,316,317,328,341,337,331,325,348,341,338,328,339,337,333,331,331,328,335,328,326,333,326,336,340,330,324,341,336,329,332,332,347,326,356,336,348,338,327,331,329,326,325,333,327,337,339,331,326,329,326,331,330,343,339,320,337,324,334,335,343,328,331,330,332,335,335,351,326,332,327,321,336,332,330,333,341,344,324,328,328,340,331,337,333,328,345,332,338,338,338,330,333,331,324,347,355,341,335,348,335,348,330,341,326,328,330,336,332,330,337,332,356,328,335,330,336,333,340,339,333,325,361,339,332,329,338,333,339,330,330,348,329,336,353,340,348,340,346,328,329,331,327],"fallow_late":[9.0,30.8,15.0,9.0,11.2,16.6,9.6,17.6,10.2,10.6,22.8,12.4,16.0,21.4,0,21.4,10.6,9.6,15.2,12.2,11.4,7.8,16.2,14.2,11.2,8.4,13.0,13.2,10.6,7.4,9.8,14.2,16.2,13.0,16.6,16.2,12.0,13.0,12.8,14.2,10.2,14.0,11.2,13.0,12.6,12.0,7.8,12.0,8.5,11.0,13.6,1.0,12.4,13.0,9.0,12.8,15.8,15.2,8.6,10.8,15.2,16.6,11.4,13.4,10.4,4.5,15.0,18.4,10.8,15.2,12.0,14.4,13.0,14.4,15.4,12.2,14.0,16.6,11.6,10.6,14.4,14.6,13.0,16.2,12.0,17.2,10.6,7.6,15.0,10.0,15.6,13.4,15.6,13.2,17.6,13.4,14.4,11.2,14.0,13.4,11.8,10.8,12.4,17.0,10.4,10.4,10.4,12.6,9.8,10.8,13.4,12.8,14.8,11.4,14.6,17.2,16.0,17.2,10.0,10.6,10.2,8.0,12.8,15.8,11.2,15.0,14.0,15.4,9.0,14.4,10.6,11.8,11.0,20.0,12.8,9.0,19.0,11.2,17.4,11.8,14.4,13.4,12.8,9.6,8.8,15.2,14.4,8.5,13.8,17.2,12.0,15.4,11.6,6.0,10.2,14.6,26.6,11.8,11.8,11.0,14.8,19.6,29.8,10.8,11.0,15.6,11.4,14.6,15.2,0,12.2,17.6,12.4,10.6,14.8,1.5,13.8,16.6,15.0,15.6,6.0,15.0,9.8,21.2,16.2,10.4,9.6,10.8,7.0,11.0,10.8,13.4,10.4,9.8,13.2,13.6,8.4,22.0,9.6,18.6,12.0,13.2,13.4,8.8,11.6,16.8,7.0,14.4,16.0,15.4,16.6,13.0,13.4,13.6,14.2,11.4,14.4,13.4,13.2,17.6,14.0,15.4,14.0,7.8,6.0,18.2,14.8,8.8,17.2,11.0,22.4,11.4,6.0,22.8,11.8,18.6,15.2,16.6,13.0,13.4,20.8,10.0,16.2,12.2,11.6],"stranded":[1796,0,0,1129,132,616,1124,0,231,385,442,663,369,357,0,172,803,260,0,451,242,1276,0,723,405,624,612,238,929,316,1591,1133,192,579,650,647,900,714,1125,902,17,324,285,0,451,467,1002,271,681,40,408,0,329,183,282,637,2,276,204,112,168,0,1083,0,716,336,144,0,1375,160,330,330,1,0,256,217,1878,0,4,320,301,346,0,638,0,220,64,1107,0,1477,0,197,0,148,288,1016,0,288,35,256,905,226,270,3,598,1692,0,1188,896,1448,946,1196,973,357,1071,405,810,961,1184,1136,227,1054,1047,470,7,358,1495,0,1394,682,1008,1476,1271,0,841,0,440,1155,589,750,193,156,1174,782,1157,439,1069,0,459,467,1125,32,963,408,1026,183,0,282,1346,852,30,272,0,571,632,351,364,371,1272,0,0,249,804,1517,378,635,550,710,1080,0,411,760,526,0,843,1083,972,867,84,1316,936,1420,1302,1429,297,1780,168,0,0,168,582,870,668,666,656,1130,495,1345,1053,789,219,0,1080,495,744,418,1088,0,564,0,524,0,587,862,0,720,615,936,1,1060,0,0,210,0,507,424,870,212,0,622,410,1190,599,500,551]},"mid":{"land2":[9,12,9,9,9,9,8,9,9,9,9,9,9,8,9,9,9,9,9,9,7,9,7,9,7,6,9,7,7,7,7,6,7,7,7,7,7,7,7,7,7,7,7,6,9,7,7,7,7,9,9,9,7,7,6,9,6,6,9,9,7,9,7,7,9,7,9,9,7,7,9,9,6,7,7,9,6,7,9,9,6,7,6,9,9,9,7,9,7,7,7,9,9,9,7,9,9,9,9,6,7,6,7],"land3":[13,20,15,13,13,13,12,12,13,13,13,13,13,12,13,12,14,12,13,13,13,12,12,12,13,13,13,13,12,12,12,13,13,12,13,13,12,12,13,13,13,12,12,12,13,14,13,12,15,14,15,12,12,13,13,13,9,13,12,13,13,12,12,12,12,13,12,14,12,13,13,13,13,13,12,12,9,12,12,13,13,12,13,13,15,13,13,13,12,12,13,11,12,13,13,12,13,15,12,13,13,13,13],"pass_work":[413,392,395,390,396,392,385,381,398,390,384,383,382,417,385,408,390,375,384,393,387,400,391,404,392,398,392,404,412,401,390,388,377,403,405,393,421,412,399,388,404,408,400,381,377,378,368,420,379,385,369,395,411,380,391,391,435,397,400,388,374,387,415,388,377,405,405,401,420,387,425,381,395,384,408,415,365,421,380,389,373,403,405,385,374,394,399,388,409,413,403,414,382,409,381,401,397,406,415,376,396,391,403],"fallow_late":[29.0,27.2,31.4,22.6,28.2,24.8,26.4,27.8,30.8,29.8,27.4,34.4,24.8,22.8,23.0,31.0,28.2,25.4,23.6,26.4,31.0,32.2,30.0,30.2,24.0,27.0,27.2,29.6,34.8,31.6,28.0,26.6,28.8,34.8,26.4,28.0,36.6,33.6,28.8,24.8,29.8,28.2,34.6,36.4,21.4,27.6,29.6,34.0,33.2,28.6,25.4,26.6,36.4,25.6,26.2,23.4,29.2,27.0,32.8,20.2,22.2,29.8,29.2,26.6,26.8,25.8,28.0,29.4,33.4,19.4,27.2,28.2,21.6,24.8,37.8,23.0,32.4,27.8,25.4,30.8,18.0,34.6,23.6,22.8,29.6,25.6,26.4,26.6,35.6,31.2,26.8,30.0,23.6,26.6,23.2,30.6,26.4,23.0,27.0,27.2,32.2,24.8,30.0],"stranded":[1847,4346,2730,3942,1535,4262,2197,4412,2088,5280,4100,2992,2176,1609,5506,1584,6168,2074,2146,1151,3416,3188,2115,5199,7031,1276,1141,3511,3645,1512,4736,1316,1360,2094,4022,4826,4254,1995,4032,1650,4250,2263,1866,0,5040,3005,0,110,1877,4083,2076,2640,3657,1805,2900,2007,485,1739,3123,3858,1300,4797,2460,1545,6252,5639,1918,3818,270,2052,2189,440,5953,1549,2703,1731,1615,2212,4467,7663,6094,1286,1205,6418,5779,2510,2390,5556,3027,1211,2776,4636,5408,1368,5981,1320,2303,1104,2187,2220,2331,1206,914]}}')

rows = [('2nd quadrant settles', 'land2'),
        ('3rd quadrant settles', 'land3'),
        ('idle-with-work', 'pass_work'),
        ('fallow tiles, late days', 'fallow_late'),
        ('stranded at the bell', 'stranded')]

def median(v):
    s = sorted(v); n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

rng = random.Random(11)
fig, ax = plt.subplots(figsize=(9.2, 5.2))
XMAX = 6.0
for i, (label, key) in enumerate(rows):
    lm = median(DIST['leader'][key]) or 1.0
    for side, colour, dy in (('leader', '#2a78d6', +0.16), ('mid', '#eb6834', -0.16)):
        vals = [min(v / lm, XMAX) for v in DIST[side][key]]
        ys = [i + dy + rng.uniform(-0.11, 0.11) for _ in vals]
        ax.scatter(vals, ys, s=9, color=colour, alpha=0.18, linewidths=0)
        m = min(median(DIST[side][key]) / lm, XMAX)
        ax.plot([m, m], [i + dy - 0.14, i + dy + 0.14], color=colour, lw=2.4)
ax.axvline(1.0, color='#222', lw=1.1)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9)
ax.invert_yaxis()
ax.set_xlim(-0.15, XMAX + 0.25)
ax.set_xlabel('multiple of the leader median for that indicator (1 = the leader median)')
ax.set_title('A macro profile is a distribution, never a point')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker='o', ls='', color='#2a78d6', label='leader, per episode'),
                   Line2D([], [], marker='o', ls='', color='#eb6834', label='mid-ladder agent, per episode')],
          frameon=False, loc='lower right', fontsize=8.5)
plt.tight_layout(); plt.show()
print('None of these is a constant, and the clouds correct two readings the')
print('bars invited. Idleness is a SMALL but consistent gap: both clouds are')
print('tight and clearly apart at about 1.2x, no overlap to hide behind.')
print('Fallow is the opposite: the medians sit far apart but the clouds')
print('genuinely overlap between 1.5x and 2.4x, so single episodes prove')
print('nothing there. And stranded inventory is a long one-sided tail, the')
print('mid agent reaching past six times the leader median while the leader')
print('cloud hugs zero: a structural gap, carried by the tail.')


# Day-end money of the SAME tape on the SAME world: alone, and against a
# co-selling rival. Real forensic data from one replayed pair of games.
alone   = [24, 93, 209, 282, 233, 40, 744, 285, 1410, 2960, 18497, 18437,
           24195, 26980, 31095, 35309, 42840, 46931, 56821, 62497, 71864,
           80355, 92780, 100301, 106517, 115365, 122308, 128900, 137228]
company = [19, 105, 219, 267, 190, 0, 264, 241, 0, 213, 8151, 4890, 5745,
           7110, 9708, 11498, 12953, 15481, 17790, 18395, 20528, 23401,
           24362, 26271, 27647, 29841, 31895, 33319, 37096]

fig, ax = plt.subplots(figsize=(8.6, 3.8))
d = range(len(alone))
ax.plot(d, alone, color=BLUE, lw=2, label='alone on the world')
ax.plot(d, company, color=ORANGE, lw=2, label='same tape, co-selling rival')
ax.fill_between(d, company, alone, color=GRID, alpha=0.6)
ax.set_xlabel('day'); ax.set_ylabel('money at day end')
ax.set_title('the gap opens during financing, then only accumulates', loc='left')
ax.legend(frameon=False, loc='upper left')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.show()
print('days 5-9 in company: cash pinned at zero, purchases silently refused,')
print('and by day 10 the farm is half-built. The bank at the bell differs by')
print('107,000; the decision that lost it cost about forty coins at a time.')


# research/population_control.py: name, win rate, clustered low, clustered high
POP = [("founder", 85.96, 84.21, 87.72),
       ("founder",  74.45, 72.98, 75.93),
       ("founder",    39.05, 35.33, 42.77),
       ("founder",       12.81, 10.18, 15.45)]

fig, ax = plt.subplots(figsize=(7.6, 3.1))
names = [p[0] for p in POP][::-1]
wr = [p[1] for p in POP][::-1]
lo = [p[1] - p[2] for p in POP][::-1]
hi = [p[3] - p[1] for p in POP][::-1]

upper = [p[3] for p in POP][::-1]                # label past the whisker, not the bar
ax.barh(names, wr, color=BLUE, height=0.55)
ax.errorbar(wr, names, xerr=[lo, hi], fmt="none", ecolor=INK, capsize=4, lw=1.4)
for n, v, u in zip(names, wr, upper):
    ax.text(u + 2.5, n, f"{v:.1f}%", va="center", color=INK,
            fontsize=9, fontweight="bold")
ax.set_xlim(0, 100)
ax.set_xlabel("win rate over 344 recorded ladder routes, 12 seeds, both seats")
ax.set_title("Choosing which season to record spans 73 points")
ax.grid(axis="x")
fig.tight_layout()
plt.show()

# research/market_oracle.py: mean, median, p90 and n per arm
ARMS = {"index": [2032.4, 68.0, 3387.0, 336], "quantity": [1398.5, 142.0, 2823.0, 336], "turn": [4006.5, 1419.0, 10127.0, 336]}
LAB = {"index": "permute order within the turn",
       "quantity": "change how much each order sells",
       "turn": "move an order to another turn"}

fig, ax = plt.subplots(figsize=(7.6, 2.9))
ks = ["index", "quantity", "turn"]
best = max(ks, key=lambda k: ARMS[k][0])
ax.barh([LAB[k] for k in ks], [ARMS[k][0] for k in ks],
        color=[ORANGE if k == best else BLUE for k in ks], height=0.55)
for y, k in enumerate(ks):
    ax.text(ARMS[k][0] + ARMS[best][0] * 0.04, y,
            "\\$" + f"{ARMS[k][0]:,.0f} mean, "
            + "\\$" + f"{ARMS[k][1]:,.0f} median",
            va="center", color=INK, fontsize=8.5)
ax.set_xlim(0, ARMS[best][0] * 2.0)
ax.set_xlabel(r"\$ gained per game WITH hindsight, so an upper bound")
ax.set_title(f"Even clairvoyant, the best arm is worth "
             f"{ARMS[best][0] / 85_000:.0%} of a bank")
ax.grid(axis="x")
fig.tight_layout()
plt.show()