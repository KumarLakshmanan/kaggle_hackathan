import hashlib, os
from pathlib import Path

WANT = {"v54_main": "5fbb75c9c40e6d9e26d95272ace47329b1ca319b3b2118232404de30806e7e9c", "v13_main": "9d63494603f88219857a3101d7dc19cc750ded04e5886732ee428580326967d9"}
found = {}
for root, _, files in os.walk("/kaggle/input"):
    for f in files:
        if f.endswith(".py"):
            b = Path(root, f).read_bytes()
            for name, sha in WANT.items():
                if hashlib.sha256(b).hexdigest() == sha:
                    found[name] = b
for name, sha in WANT.items():
    if name not in found and Path(name + ".py").exists():  # local runs
        found[name] = Path(name + ".py").read_bytes()
    assert name in found and hashlib.sha256(found[name]).hexdigest() == sha, "missing " + name
    Path(name + ".py").write_bytes(found[name])
src = found["v54_main"]

LAYER = b"""

# busyaprime fork of V54, 2026-09-21. Apache-2.0 like everything above.
# The RACE layer (from Thomas Tschinkel's v9) pre-sells a planned lot when the tape plans it within V9_RACE_DEFAULT
# turns (40), and stretches that to V9_RACE_MAX (48) when it sees the rival sell ahead of it. The fork starts at 72.
# The cap of 96 never binds: the stretch is the rival's lead plus 12, and the layer searches 30 turns for a lead.
V9_RACE_DEFAULT = 72
V9_RACE_MAX = 96
"""
Path("main.py").write_bytes(src + LAYER)
fork = Path("main.py").read_bytes()
assert fork.startswith(src) and len(fork) == len(src) + len(LAYER)
print("V54 main.py", len(src), "bytes, sha256", WANT["v54_main"])
print("fork main.py", len(fork), "bytes, sha256", hashlib.sha256(fork).hexdigest())
print("fork = V54 byte for byte, plus these lines at the end:")
print(fork[len(src):].decode())

import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "kaggle-environments==1.32.7"], check=True)

import contextlib, csv, io, math, time
import importlib.metadata as imd
import multiprocessing as mp
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
print("kaggle-environments", imd.version("kaggle-environments"), "| CPUs", os.cpu_count())
assert imd.version("kaggle-environments") == "1.32.7", "restart the kernel after the pip cell"

def play(job):
    seed, a0, a1 = job
    t = time.time()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        env.run([a0 + ".py", a1 + ".py"])
    last = env.steps[-1]
    return dict(seed=seed, agent0=a0, agent1=a1, bank0=last[0].reward, bank1=last[1].reward,
                status0=last[0].status, status1=last[1].status, secs=round(time.time() - t, 1))

SEED0, NSEEDS = 64000, 20
PAIRS = [("main", "v54_main"), ("main", "v13_main"), ("v54_main", "v13_main")]
jobs = [(s, p, q) for x, y in PAIRS for s in range(SEED0, SEED0 + NSEEDS) for p, q in ((x, y), (y, x))]
T0 = time.time()
with mp.get_context("fork").Pool(os.cpu_count()) as pool:
    rows = pool.map(play, jobs, chunksize=1)
print(len(rows), "games in", round(time.time() - T0), "s")
assert all(r["status0"] == "DONE" and r["status1"] == "DONE" for r in rows)
with open("arena.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

import pandas as pd

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d

NAMES = {"main": "fork", "v54_main": "V54", "v13_main": "v13"}
out = []
for x, y in PAIRS:
    m = {}
    for r in rows:
        if {r["agent0"], r["agent1"]} != {x, y}:
            continue
        d = r["bank0"] - r["bank1"] if r["agent0"] == x else r["bank1"] - r["bank0"]
        m.setdefault(r["seed"], []).append(d)
    ds = [d for v in m.values() for d in v]
    w, l, t = sum(d > 0 for d in ds), sum(d < 0 for d in ds), sum(d == 0 for d in ds)
    lo, hi = wilson(w + 0.5 * t, len(ds))
    both = sum(all(d > 0 for d in v) for v in m.values()); lost = sum(all(d < 0 for d in v) for v in m.values())
    out.append({"agent": NAMES[x], "opponent": NAMES[y], "games": len(ds), "W-L-T": f"{w}-{l}-{t}",
                "winrate": round((w + 0.5 * t) / len(ds), 3), "wilson95": f"[{lo:.3f}, {hi:.3f}]",
                "mean margin $": round(sum(ds) / len(ds)),
                "seeds won both / split / lost both": f"{both}/{len(m) - both - lost}/{lost}"})
table = pd.DataFrame(out)
table

def ledger_game(job):
    seed, seats = job
    log, ctx = [], {}
    _commit, _market = K._commit_unit, K._process_market
    def market_logged(state, env):
        ctx["farms"] = state[0].observation.farms
        return _market(state, env)
    def commit_logged(op, item, price, farm, *rest):
        ok = _commit(op, item, price, farm, *rest)
        if ok and op == "SELL":
            seat = next(i for i, f in enumerate(ctx["farms"]) if f is farm)
            log.append((seed, seats[seat], item, price))
        return ok
    K._process_market, K._commit_unit = market_logged, commit_logged
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            env.run([x + ".py" for x in seats])
    finally:
        K._process_market, K._commit_unit = _market, _commit
    return log

ljobs = [(s, seats) for s in range(SEED0, SEED0 + NSEEDS) for seats in (("main", "v54_main"), ("v54_main", "main"))]
with mp.get_context("fork").Pool(os.cpu_count()) as pool:
    LOG = [x for part in pool.map(ledger_game, ljobs, chunksize=1) for x in part]
sold = pd.DataFrame(LOG, columns=["seed", "agent", "item", "price"]).replace({"agent": NAMES})
per = sold.groupby(["item", "agent"])["price"].agg(units="count", revenue="sum", avg_price="mean").round(1).unstack("agent")
per[("revenue", "fork - V54")] = per[("revenue", "fork")] - per[("revenue", "V54")]
print("sales revenue, fork minus V54, over", len(ljobs), "games:", int(per[("revenue", "fork - V54")].sum()))
per

import gzip, tarfile
data = open("main.py", "rb").read()
with open("submission.tar.gz", "wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as z:
        with tarfile.open(fileobj=z, mode="w", format=tarfile.GNU_FORMAT) as tar:
            info = tarfile.TarInfo("main.py"); info.size = len(data); info.mtime = 0; info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
for f in ("v54_main.py", "v13_main.py"):
    os.remove(f)
print("submission.tar.gz written, main.py sha256", hashlib.sha256(data).hexdigest())
print("whole notebook:", round(time.time() - T0), "s after the arena started")