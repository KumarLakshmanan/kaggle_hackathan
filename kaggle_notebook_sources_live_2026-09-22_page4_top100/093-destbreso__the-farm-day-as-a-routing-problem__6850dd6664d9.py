# engine-exact parameters, read from kaggle_environments 1.32.7 source
CROPS = {  # first_yield_day, max_yield_day, max_yield, ongoing
 "WHEAT":      dict(open=2,  close=4,  cap=6, ongoing=False),
 "CARROT":     dict(open=2,  close=3,  cap=4, ongoing=False),
 "TOMATO":     dict(open=8,  close=8,  cap=4, ongoing=True),
 "STRAWBERRY": dict(open=10, close=10, cap=4, ongoing=True),
 "MELON":      dict(open=10, close=12, cap=6, ongoing=False)}
ANIMALS = {  # structure, first yield, interval, product
 "GOOSE": dict(home="COOP",    open=4, every=1, product="EGG"),
 "COW":   dict(home="PASTURE", open=8, every=2, product="MILK"),
 "SHEEP": dict(home="PASTURE", open=6, every=3, product="WOOL")}
RULES = dict(unwatered_death=2, unfed_escape=2, harvest_decay="1 unit / 2 turns",
             water_bonus="+1 (+2 fertilized) inside [ (close+1)//2, close ]")
print("crop windows (in-game days from planting):")
for k, v in CROPS.items():
    print(f"  {k:<11} open {v['open']:>2}  close {v['close']:>2}  cap {v['cap']}  ongoing {v['ongoing']}")
print("\nanimal production:", {k: f"{v['product']} from day {v['open']} every {v['every']}" for k, v in ANIMALS.items()})
print("hard rules:", RULES)

# The dataset for every figure below, embedded once. profiles: season
# travel, its MST bound, their ratio, the windows-relaxed re-solve and the
# slack against it, for the public script, the then-leader's engine and my
# rules dispatcher. instance: one real served-tile day. daily: per-day
# (day, travel, mst) triples per profile. fib: the hire cost sequence.
import json
import matplotlib.pyplot as plt
D = json.loads(r'''{"profiles":{"script":{"travel":3625,"mst":1415,"ratio":2.56,"solved":3000,"slack":1.21},"king":{"travel":3695,"mst":1446,"ratio":2.56,"solved":2990,"slack":1.24},"rules":{"travel":4317,"mst":927,"ratio":4.66,"solved":1924,"slack":2.24}},"instance":{"day":12,"tiles":[[0,0],[0,2],[0,4],[1,1],[1,3],[2,0],[2,1],[2,2],[2,3],[2,4],[3,0],[3,1],[3,2],[3,3],[3,4],[3,5],[3,8],[4,0],[4,1],[4,2],[4,3],[4,4],[4,5],[4,6],[4,8],[5,1],[5,2],[5,3],[5,4],[5,5],[6,0],[6,2],[6,3],[6,4],[7,1],[7,3],[7,4],[8,0],[8,2],[8,4],[9,1],[9,3],[9,4]],"travel":154,"work":91,"mst":51,"episode":"93479646"},"fib":[1,1,2,3,5,8,13,21,34,55,89,144,233,377],"daily":{"script":[[0,52,22],[1,10,3],[2,45,23],[3,48,20],[4,51,21],[5,44,19],[6,69,26],[7,104,29],[8,152,43],[9,120,40],[10,164,43],[11,156,60],[12,154,55],[13,122,63],[14,116,48],[15,171,68],[16,133,51],[17,167,62],[18,175,58],[19,156,67],[20,153,65],[21,169,65],[22,142,70],[23,165,59],[24,142,64],[25,135,59],[26,132,68],[27,144,60],[28,113,58],[29,121,26]],"king":[[0,52,22],[1,10,3],[2,45,23],[3,48,20],[4,51,21],[5,44,19],[6,69,25],[7,103,30],[8,147,43],[9,131,40],[10,164,43],[11,156,60],[12,154,51],[13,124,62],[14,117,51],[15,178,63],[16,126,58],[17,166,64],[18,155,64],[19,147,67],[20,152,66],[21,179,67],[22,149,69],[23,165,68],[24,154,59],[25,151,63],[26,148,65],[27,150,67],[28,123,55],[29,137,38]],"rules":[[0,58,22],[1,10,3],[2,63,23],[3,69,23],[4,93,23],[5,83,18],[6,68,21],[7,91,25],[8,81,23],[9,93,23],[10,186,23],[11,191,42],[12,154,44],[13,179,44],[14,130,31],[15,194,39],[16,146,33],[17,195,41],[18,192,39],[19,203,41],[20,195,31],[21,194,35],[22,191,39],[23,197,35],[24,183,35],[25,187,33],[26,188,34],[27,183,41],[28,181,32],[29,139,31]]}}''')
P = D["profiles"]
print(f"{'profile':<38}{'travel':>8}{'MST bound':>11}{'ratio':>7}")
rows = [("public script 10C4S (one run vs IDLE)", "script"),
        ("kawashigi rank 1 (one real episode)", "king"),
        ("my rules engine v8.8 (one run vs IDLE)", "rules")]
for label, k in rows:
    p = P[k]
    print(f"{label:<38}{p['travel']:>8,}{p['mst']:>11,}{p['ratio']:>7}")

COL = {"script": "#0F172A", "king": "#B45309", "rules": "#0E7490"}
LAB = {"script": "public script", "king": "kawashigi", "rules": "rules engine v8.8"}
fig, ax = plt.subplots(figsize=(9, 3.6))
for k in ("script", "king", "rules"):
    pts = [(d, tr / m) for d, tr, m in D["daily"][k] if m >= 8]
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=COL[k], lw=2, label=LAB[k])
    ax.annotate(LAB[k], (xs[-1], ys[-1]), xytext=(4, 0),
                textcoords="offset points", color=COL[k], fontsize=9,
                va="center")
ax.set_xlabel("in-game day")
ax.set_ylabel("travel paid / MST bound")
ax.set_xlim(0, 34)
ax.grid(alpha=0.25)
ax.legend(loc="upper left", fontsize=9, frameon=False)
ax.set_title("routing multiple by day: the gap is season-long, not one phase",
             fontsize=10)
plt.tight_layout(); plt.show()

P = D["profiles"]
print(f"{'profile':<26}{'paid':>7}{'solver upper':>14}{'paid/solver':>13}{'solver/MST':>12}")
for label, k in (("public script", "script"), ("kawashigi rank 1", "king"),
                 ("my rules engine v8.8", "rules")):
    p = P[k]
    print(f"{label:<26}{p['travel']:>7,}{p['solved']:>14,}{p['slack']:>13}"
          f"{p['solved']/p['mst']:>12.2f}")

P = D["profiles"]
keys = ["script", "king", "rules"]
labs = ["public script", "kawashigi", "rules engine v8.8"]
paid = [P[k]["travel"] for k in keys]
solv = [P[k]["solved"] for k in keys]
mst = [P[k]["mst"] for k in keys]
x = range(3)
fig, ax = plt.subplots(figsize=(8, 3.8))
b1 = ax.bar([i - 0.2 for i in x], paid, width=0.36, color="#0F172A",
            label="travel paid")
b2 = ax.bar([i + 0.2 for i in x], solv, width=0.36, color="#0E7490",
            label="cheap solver on the same days (upper bound)")
for i in x:
    ax.plot([i - 0.45, i + 0.45], [mst[i]] * 2, color="#B45309", lw=2.2)
    ax.annotate(f"{paid[i]:,}", (i - 0.2, paid[i]), ha="center",
                va="bottom", fontsize=9)
    ax.annotate(f"{solv[i]:,}", (i + 0.2, solv[i]), ha="center",
                va="bottom", fontsize=9)
ax.plot([], [], color="#B45309", lw=2.2, label="MST lower bound")
ax.set_xticks(list(x)); ax.set_xticklabels(labs)
ax.set_ylabel("unit-hours of travel, season total")
ax.grid(alpha=0.25, axis="y")
ax.legend(loc="upper right", fontsize=9, frameon=False)
ax.set_title("the test at a glance: the optimum lives between the amber line "
             "and the teal bar", fontsize=10)
plt.tight_layout(); plt.show()

wi = D["instance"]
tiles = [tuple(t) for t in wi["tiles"]]
depot = (4, 4)
pts = tiles + [depot]
# recompute the MST edges for the picture (Prim)
in_tree, out, edges = {pts[-1]}, set(pts[:-1]), []
while out:
    best = None
    for p in out:
        for q in in_tree:
            dd = abs(p[0]-q[0]) + abs(p[1]-q[1])
            if best is None or dd < best[0]:
                best = (dd, p, q)
    edges.append((best[1], best[2])); in_tree.add(best[1]); out.discard(best[1])
fig, ax = plt.subplots(figsize=(5.4, 5.4))
for (a, b) in edges:
    ax.plot([a[0], b[0]], [a[1], b[1]], color="#B45309", lw=1.4, zorder=1)
xs, ys = zip(*tiles)
ax.scatter(xs, ys, s=170, c="#DCEEE1", edgecolors="#0F172A", zorder=2,
           label=f"served tiles ({len(tiles)})")
ax.scatter(*depot, marker="s", s=200, c="#0F172A", zorder=3, label="depot (shed)")
ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_xlim(-0.6, 9.6); ax.set_ylim(9.6, -0.6)
ax.grid(alpha=0.25); ax.legend(loc="lower right", fontsize=9)
ax.set_title(f"one real day of rank 1 (in-game day {wi['day']}): "
             f"MST bound {wi['mst']} vs travel paid {wi['travel']}", fontsize=10)
plt.tight_layout(); plt.show()
print(f"episode {wi['episode']}: {wi['work']} work actions on {len(tiles)} tiles,")
print(f"travel {wi['travel']} against a connectivity bound of {wi['mst']}")

fib = D["fib"][:12]
fig, ax = plt.subplots(figsize=(7, 3))
ax.bar(range(1, len(fib) + 1), fib, color="#0E7490")
for n, f in enumerate(fib, 1):
    ax.annotate(str(f), (n, f), ha="center", va="bottom", fontsize=9)
ax.set_xticks(range(1, len(fib) + 1))
ax.set_xlabel("n-th hand hired that day")
ax.set_ylabel("marginal cost, units of the hire multiplier")
ax.grid(alpha=0.25, axis="y")
ax.set_title("the fleet term: convex by Fibonacci, near-free until it is not",
             fontsize=10)
plt.tight_layout(); plt.show()