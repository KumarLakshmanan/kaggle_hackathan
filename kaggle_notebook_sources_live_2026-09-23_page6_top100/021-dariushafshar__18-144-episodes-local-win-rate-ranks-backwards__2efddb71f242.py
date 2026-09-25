import os, sys, math, collections, csv

# Kaggle's input mount layout is not stable: walk (bounded) for the marker file.
MARKER = "episodes.csv"
root = None
for base in ("/kaggle/input", "input", "."):
    if not os.path.isdir(base):
        continue
    for dirpath, dirnames, filenames in os.walk(base):
        if dirpath.count(os.sep) - base.count(os.sep) > 3:
            dirnames[:] = []
            continue
        if MARKER in filenames:
            root = dirpath
            break
    if root:
        break

if root is None:
    sys.exit(f"FATAL: could not find {MARKER} under /kaggle/input. "
             "Attach dariushafshar/kaggriculture-agent-benchmark-18k and rerun.")
print("dataset root:", root)

rows = []
with open(os.path.join(root, "episodes.csv")) as fh:
    for r in csv.DictReader(fh):
        r["seed"] = int(r["seed"]); r["swap"] = int(r["swap"])
        r["ours"] = float(r["ours"]); r["theirs"] = float(r["theirs"])
        r["win"] = int(r["win"])
        rows.append(r)

print(f"{len(rows):,} episodes loaded")
assert len(rows) == 18144, len(rows)
# the win column is not taken on trust
assert all(r["win"] == int(r["ours"] > r["theirs"]) for r in rows)
print("win column verified against both bank columns for every row")

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z*z/n
    c = p + z*z/(2*n)
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c-h)/d, (c+h)/d

LADDER = {"v9": 752.7, "v8": 758.6}          # Kaggle submissions API, 2026-08-08 05:57 UTC
pw = [r for r in rows if r["sweep"] == "pool_wide"]

print(f"{'agent':6s} {'local win rate (n=2880)':26s} {'vs opp_c03':>11s} {'ladder':>8s}")
for ag in ("v9", "v8"):
    rs = [r for r in pw if r["label"] == ag]
    k, n = sum(r["win"] for r in rs), len(rs)
    lo, hi = wilson(k, n)
    c03 = [r for r in rs if r["opp"] == "opp_c03"]
    print(f"{ag:6s} {k/n:6.1%} [{lo:.1%}, {hi:.1%}]{'':6s} "
          f"{sum(r['win'] for r in c03)/len(c03):10.1%} {LADDER[ag]:8.1f}")

print("\nLocal ranks v9 first. The ladder ranks v8 first.")

print(f"{'opponent':16s} {'v9':>8s} {'v8':>8s}")
seen = []
for opp in sorted({r["opp"] for r in pw}):
    cell = {}
    for ag in ("v9", "v8"):
        rs = [r for r in pw if r["opp"] == opp and r["label"] == ag]
        cell[ag] = sum(r["win"] for r in rs) / len(rs)
    seen.append((opp, cell))
for opp, cell in sorted(seen, key=lambda t: -t[1]["v9"]):
    print(f"{opp:16s} {cell['v9']:8.1%} {cell['v8']:8.1%}")

rates = [c["v9"] for _, c in seen]
print(f"\nat 0.0%: {sum(r == 0 for r in rates)} of {len(rates)}   "
      f"at 100.0%: {sum(r == 1 for r in rates)} of {len(rates)}")

def mcnemar(cand, base, key=("opp", "seed", "swap")):
    idx = {tuple(r[k] for k in key): r["win"] for r in base}
    W = L = tie = 0
    for r in cand:
        b = idx.get(tuple(r[k] for k in key))
        if b is None: continue
        if r["win"] == b: tie += 1
        elif r["win"] == 1: W += 1
        else: L += 1
    z = (W - L) / math.sqrt(W + L) if W + L else float("nan")
    return W, L, tie, z

def two_prop(cand, base):
    """The WRONG test for these arms. Shown so you can see the size of the error."""
    k1, n1 = sum(r["win"] for r in cand), len(cand)
    k2, n2 = sum(r["win"] for r in base), len(base)
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1/n1 + 1/n2))
    return (k1/n1 - k2/n2) / se if se else float("nan")

def arm(sweep, label, opp=None):
    return [r for r in rows if r["sweep"] == sweep and r["label"] == label
            and (opp is None or r["opp"] == opp)]

print(f"{'comparison':38s} {'base':>7s} {'cand':>7s} {'W':>4s} {'L':>4s} "
      f"{'ties':>5s} {'McNemar z':>10s} {'unpaired z':>11s}")
for sweep, label, opp in [
    ("mix_recheck",   "max_quadrants=2",     "opp_c03"),
    ("mix_recheck",   "wheat_late_tiles=10", "opp_c03"),
    ("mix_recheck",   "melon_tiles=18",      "opp_c03"),
    ("mix_recheck",   "care_mult=0.5",       "opp_c03"),
    ("hire_frontier", "cap12_marg100",       "opp_c03"),
]:
    base = arm(sweep, "v9-base", opp); cand = arm(sweep, label, opp)
    W, L, tie, z = mcnemar(cand, base)
    b = sum(r["win"] for r in base)/len(base); c = sum(r["win"] for r in cand)/len(cand)
    print(f"{label + ' vs ' + opp:38s} {b:7.1%} {c:7.1%} {W:4d} {L:4d} {tie:5d} "
          f"{z:+10.2f} {two_prop(cand, base):+11.2f}")

print("\nmax_quadrants=2 is the real lever: +23.9 points, z=+4.00, 28 W / 5 L.")
print("cap12_marg100 clears NEITHER test (z=+1.15 paired) -- 67 of 128 pairs are ties,")
print("so most of the sample carries no information about the comparison at all.")

for sweep in ("mix_recheck", "hire_frontier"):
    base = {(r["opp"], r["seed"], r["swap"]): r["ours"]
            for r in rows if r["sweep"] == sweep and r["label"] == "v9-base"}
    print(f"\n[{sweep}]")
    for label in sorted({r["label"] for r in rows if r["sweep"] == sweep}):
        if label == "v9-base": continue
        cand = arm(sweep, label)
        ident = sum(1 for r in cand if base.get((r["opp"], r["seed"], r["swap"])) == r["ours"])
        if ident == len(cand):
            print(f"  SHADOWED  {label:24s} bank identical on all {len(cand)} episodes")