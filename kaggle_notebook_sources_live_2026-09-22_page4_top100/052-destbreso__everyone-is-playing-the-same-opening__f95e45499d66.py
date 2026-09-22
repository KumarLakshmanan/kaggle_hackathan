import glob, hashlib, json, os, random
from collections import Counter

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# pandas, numpy, pyarrow and matplotlib only. Nothing here pip-installs, because
# a Kaggle notebook runs with the internet switched off by default and a missing
# package would be fatal rather than slow.


def find_data(roots=("/kaggle/input",)):
    """Find the dataset by WALKING for episodes.csv, at whatever depth it sits.

    Kaggle does not mount an input at a fixed depth. Depending on how it was
    attached it can appear as /kaggle/input/<slug>/ or, as it does here, at
    /kaggle/input/datasets/<owner>/<slug>/. Guessing the depth is how the first
    two versions of this function failed, so this one does not guess.
    """
    def scan(root, max_depth=6):
        root = os.path.abspath(root)
        base = root.rstrip(os.sep).count(os.sep)
        hits = []
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base >= max_depth:
                dirnames[:] = []            # do not descend further
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            if "episodes.csv" in filenames:
                hits.append(dirpath)
        return hits

    found = []
    for r in roots:
        if os.path.isdir(r):
            found += scan(r)
    here = os.path.abspath(os.getcwd())         # local checkout: walk upward
    while not found:
        for sub in ("data", "."):
            d = os.path.join(here, sub)
            if os.path.isdir(d):
                found += scan(d, max_depth=4)
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent

    # A directory holding BOTH files wins. One with only the CSV is a trap:
    # it would fail later, in section 3, after the expensive part.
    found.sort(key=lambda d: not os.path.exists(os.path.join(d, "replays.parquet")))
    if found:
        return found[0]

    listing = []
    for r in roots:
        if os.path.isdir(r):
            for dirpath, dirnames, filenames in os.walk(r):
                if dirpath.count(os.sep) - r.count(os.sep) > 3:
                    dirnames[:] = []
                    continue
                if filenames:
                    listing.append(f"    {dirpath}/  ->  {sorted(filenames)[:6]}")
    mounted = "\n".join(listing[:25]) or "    nothing is mounted under " + ", ".join(roots)
    raise FileNotFoundError(
        "Could not find episodes.csv.\n\n"
        "ON KAGGLE the dataset has to be attached to this notebook. In the\n"
        "editor, open the right-hand panel, click '+ Add Input', switch to the\n"
        "Datasets tab, search for\n"
        "    georgymamarin/kaggriculture-episodes\n"
        "and click the plus. Nothing downloads; it is mounted read-only, so the\n"
        "session does not need the internet enabled.\n\n"
        "Files visible right now:\n" + mounted + "\n\n"
        "LOCALLY: put the dataset in <repo>/data/kaggriculture-episodes/.")


DATA = find_data()
print("data:", DATA)
missing = [f for f in ("episodes.csv", "replays.parquet")
           if not os.path.exists(os.path.join(DATA, f))]
for f in ("episodes.csv", "replays.parquet"):
    q = os.path.join(DATA, f)
    print(f"  ok      {f:<18}{os.path.getsize(q) / 1e6:>10,.1f} MB" if os.path.exists(q)
          else f"  MISSING {f}")
if missing:
    raise FileNotFoundError(
        f"{DATA} is missing {missing}. Attach the FULL dataset, not a subset: "
        "replays.parquet is 2.7 GB and everything after section 3 needs it.")

# create_time is read as TEXT on purpose. The column carries timezone offsets,
# and depending on the pandas version those parse to a tz-aware column, to an
# object column, or to a warning. The day is a fixed slice of the string, so
# take it from the string and remove the version from the equation.
ep = pd.read_csv(os.path.join(DATA, "episodes.csv"))
pub = ep[ep["type"] == "EPISODE_TYPE_PUBLIC"].copy()
pub["day"] = pub["create_time"].astype(str).str[5:10]

print(f"\n{len(ep):,} episodes, {len(pub):,} public, "
      f"{pub.day.min()} to {pub.day.max()}")

class ReplayStore:
    """Random access into replays.parquet without ever loading it.

    The file is 2.7 GB compressed and roughly 635 GB of JSON decompressed, so it
    can never be read whole. Parquet stores rows in groups (about nine each
    here) and a group is the smallest unit that can be decompressed, so we index
    once which group holds each episode, reading only the id column, and then
    touch only the groups we actually want. Peak memory is one group, about
    550 MB in the worst case.
    """

    def __init__(self, path):
        self.f = pq.ParquetFile(path)
        self.group_of = {}
        for gi in range(self.f.num_row_groups):
            col = self.f.read_row_group(gi, columns=["episode_id"])["episode_id"]
            for e in col.to_pylist():
                self.group_of[e] = gi

    def fetch(self, ids):
        """Yield (episode_id, replay_json) for ids, one row group at a time."""
        want = set(int(i) for i in ids)
        for gi in sorted({self.group_of[e] for e in want if e in self.group_of}):
            tb = self.f.read_row_group(gi, columns=["episode_id", "replay_json"])
            eids = tb["episode_id"].to_pylist()
            blob = tb["replay_json"]
            for k, e in enumerate(eids):
                if e in want:
                    yield e, blob[k].as_py()
            del tb, blob


_store = None


def store():
    """Built on first use, not on import.

    Indexing 23,000 row groups costs about ten seconds, and with the
    precomputed fingerprints attached the only cell that needs a replay is the
    one in section 7 that decodes a single stream. Paying for the index at the
    top would be the largest single cost of an otherwise instant notebook.
    """
    global _store
    if _store is None:
        _store = ReplayStore(os.path.join(DATA, "replays.parquet"))
        print(f"{len(_store.group_of):,} replays indexed across "
              f"{_store.f.num_row_groups:,} row groups")
    return _store

# Chart style: recessive axes, a light horizontal grid, nothing decorative.
# Colours are assigned by the job they do. An ordered quantity such as a horizon
# or a quantile gets one hue stepped light to dark. Unordered series get
# distinct hues in a fixed order, never cycled.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e7e7e4"

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def ramp(n, base=BLUE):
    """One hue stepped light to dark, for series that have a natural order."""
    import matplotlib.colors as mc
    r, g, b = mc.to_rgb(base)
    return [(r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)
            for f in np.linspace(0.62, 0.0, n)]


def tidy(ax, ylab=None, title=None):
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.xaxis.grid(False)
    if ylab:
        ax.set_ylabel(ylab)
    if title:
        ax.set_title(title, loc="left", pad=10, fontweight="bold")
    return ax

seats = pd.concat([
    pub[["day", "rating_0"]].rename(columns={"rating_0": "rating"}),
    pub[["day", "rating_1"]].rename(columns={"rating_1": "rating"})])

frame = (seats.groupby("day").rating
         .agg(seats="size", floor="min",
              p10=lambda r: r.quantile(0.10), median="median")
         .reset_index())

display(frame.style.format({"seats": "{:,.0f}", "floor": "{:,.0f}",
                            "p10": "{:,.0f}", "median": "{:,.0f}"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(8, 3.4))
for (c, lab), col in zip([("floor", "lowest rating seen"), ("p10", "10th percentile"),
                          ("median", "median")], ramp(3)):
    ax.plot(frame.day, frame[c], lw=2, color=col, marker="o", ms=5)
    ax.annotate(lab, (len(frame) - 1, frame[c].iloc[-1]), xytext=(7, 0),
                textcoords="offset points", va="center", color=col, fontsize=9)
tidy(ax, "rating of sampled seats", "Who the crawler catches changes over the window")
ax.set_xlim(-0.4, len(frame) + 2.2)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:,.0f}"))
plt.tight_layout(); plt.show()

# The horizons we hash ourselves. When the fingerprints come from the dataset's
# stream_hashes.csv the available set is narrower, so anything downstream reads
# HORIZONS_AVAILABLE rather than this list.
LENGTHS = [24, 48, 100, 200, 300, 400, 500, 600, 719]

SAMPLE_EPISODES = 2670   # about 12 minutes. 800 takes 4 and changes no conclusion.
SEED = 20260812


def canon(action):
    """One action as a canonical string. Anything that is not a dict is empty."""
    if not isinstance(action, dict):
        return "{}"
    return json.dumps(action, sort_keys=True, separators=(",", ":"))


def fingerprints(steps, seat):
    """Prefix hashes plus a full-stream hash, in a single pass.

    steps[0] is the initial state and carries no action, so the stream starts at 1.
    """
    h, out, k, want = hashlib.sha256(), {}, 0, set(LENGTHS)
    for t in range(1, len(steps)):
        st = steps[t]
        h.update(canon(st[seat].get("action") if len(st) > seat else None).encode())
        h.update(b"\x00")
        k += 1
        if k in want:
            out[f"h{k}"] = h.hexdigest()[:16]
    out["full_sha"], out["turns"] = h.hexdigest()[:16], k
    return out

FIELDS = ["episode_id", "team_0", "team_1", "bank_0", "bank_1",
          "rating_0", "rating_1", "create_time", "sub_0", "sub_1"]

FIELDS = ["episode_id", "team_0", "team_1", "bank_0", "bank_1",
          "rating_0", "rating_1", "create_time", "sub_0", "sub_1"]

# Read this row by NAME below, never by position. A positional read is the kind
# of off-by-one that produces a plausible wrong answer instead of an exception.
COL = {k: i for i, k in enumerate(FIELDS)}
absent = [c for c in FIELDS if c not in pub.columns]
if absent:
    raise KeyError(
        f"episodes.csv is missing {absent}. This notebook was written against "
        f"the columns {FIELDS}. The dataset is maintained by someone else and "
        f"refreshed daily, so a schema change is possible; what it has now is "
        f"{list(pub.columns)}.")
meta = {int(r[0]): r for r in pub[FIELDS].itertuples(index=False, name=None)}


def harvest(ids, label=""):
    """Fingerprint both seats of every episode in ids."""
    rows, done = [], 0
    for eid, js in store().fetch(ids):
        done += 1
        blob = json.loads(js)
        steps = blob.get("steps") or []
        if len(steps) >= 700:
            info, m = blob.get("info") or {}, meta[eid]
            for seat in (0, 1):
                row = fingerprints(steps, seat)
                row.update(episode_id=eid, seat=seat,
                           team=m[COL[f"team_{seat}"]], bank=m[COL[f"bank_{seat}"]],
                           rating=m[COL[f"rating_{seat}"]], sub=m[COL[f"sub_{seat}"]],
                           seed=info.get("seed"),
                           opponent=m[COL[f"team_{1 - seat}"]],
                           team_name=(info.get("TeamNames") or [None, None])[seat],
                           day=str(m[COL["create_time"]])[5:10])
                rows.append(row)
        del blob, steps, js
        if done % 400 == 0:
            print(f"  {label}{done}/{len(ids)} episodes", flush=True)
    return pd.DataFrame(rows)


def precomputed(*names):
    """Load a fingerprint table if one is attached, else return None.

    Hashing 2,670 replays takes about ten minutes and produces 0.7 MB, so the
    result is published as a small dataset. Attaching it makes this notebook
    run in seconds. NOT attaching it changes nothing except the wait: the cell
    below computes exactly the same table from the replays, with the same seed.
    The precomputed file is a convenience, never a dependency.
    """
    for root in ("/kaggle/input", os.getcwd(), os.path.dirname(os.getcwd())):
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - root.count(os.sep) > 4:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in names:
                if name in filenames:
                    return pd.read_parquet(os.path.join(dirpath, name))
    return None


# ---------------------------------------------------------------------------
# Fingerprints now come from the SOURCE dataset, not from a side table of ours.
#
# When this notebook was first written it hashed the replays itself, ten minutes
# for 2,670 episodes, and published the result as a small companion dataset so
# readers would not have to wait. Georgy Mamarin, who maintains
# georgymamarin/kaggriculture-episodes, took that suggestion and now ships
# stream_hashes.csv in the dataset itself: one sha256 per (episode, seat), cut at
# turns 24, 100, 200, 400 and 719, for every episode he holds.
#
# That is a much better arrangement than ours and it changes three things.
# The sample stops being 2,670 episodes and becomes every public episode in the
# dataset. The companion dataset is no longer needed at all. And the snapshot
# hazard disappears: a side table froze while episodes.csv refreshed daily, so
# the two could describe different windows with nothing saying so. Hashes and
# metadata now refresh together, by construction.

HORIZONS = [24, 100, 200, 400, 719]     # what stream_hashes.csv carries

def from_stream_hashes():
    """Build the seat-level fingerprint frame from the dataset's own hashes."""
    path = os.path.join(DATA, 'stream_hashes.csv')
    if not os.path.exists(path):
        return None
    sh = pd.read_csv(path)
    need = {'episode_id', 'seat', 'turns'} | {f'stream_h{h}' for h in HORIZONS}
    if not need.issubset(sh.columns):
        print(f'  stream_hashes.csv lacks {sorted(need - set(sh.columns))}; '
              'falling back to hashing')
        return None
    sh = sh.rename(columns={f'stream_h{h}': f'h{h}' for h in HORIZONS})
    sh['full_sha'] = sh['h719']

    # Attach the per-seat metadata by joining on the seat, never by position.
    long = []
    for seat in (0, 1):
        cols = {'episode_id': 'episode_id', f'team_{seat}': 'team',
                f'bank_{seat}': 'bank', f'rating_{seat}': 'rating',
                f'sub_{seat}': 'sub', f'team_{1-seat}': 'opponent'}
        part = pub[list(cols)].rename(columns=cols)
        part['seat'] = seat
        part['day'] = pub['create_time'].astype(str).str[5:10].values
        long.append(part)
    side = pd.concat(long, ignore_index=True)
    out = sh.merge(side, on=['episode_id', 'seat'], how='inner')
    return out

fp = from_stream_hashes()
if fp is not None:
    print(f'using the dataset\'s own stream_hashes.csv: {len(fp):,} seats, '
          f'{fp.episode_id.nunique():,} public episodes, {fp.team.nunique():,} teams')
else:
    fp = precomputed('seat_fingerprints_random.parquet')
    if fp is None:
        print('hashing the replays (about 10 minutes)')
        ids = sorted(random.Random(SEED).sample(sorted(meta),
                                                min(SAMPLE_EPISODES, len(meta))))
        fp = harvest(ids, 'random ')
    if 'day' not in fp.columns:
        fp = fp.assign(day=fp['create_time'].astype(str).str[5:10])

print(f'\n{len(fp):,} seats, {fp.episode_id.nunique():,} episodes, '
      f'{fp.team.nunique():,} teams')

# Which horizons are usable depends on where the fingerprints came from.
HORIZONS_AVAILABLE = [h for h in (24, 48, 100, 200, 300, 400, 500, 600, 719)
                      if f'h{h}' in fp.columns]
print(f'horizons available: {HORIZONS_AVAILABLE}')

STRATIFIED_TEAMS = 600        # roughly 8 more minutes
EPISODES_PER_TEAM = 4

seatrows = pd.concat([
    pub[["team_0", "episode_id", "create_time"]].rename(columns={"team_0": "team"}),
    pub[["team_1", "episode_id", "create_time"]].rename(columns={"team_1": "team"})])

active = seatrows.groupby("team").size()
active = active[active >= 2]                       # a team seen once proves nothing
band = pd.qcut(active.rank(method="first"), 4, labels=False)

rng2 = random.Random(SEED)
pick = []
for b in range(4):                                 # equal numbers from each activity band
    teams = list(active.index[band == b])
    rng2.shuffle(teams)
    pick += teams[:STRATIFIED_TEAMS // 4]

sel = seatrows[seatrows.team.isin(set(pick))].sort_values("create_time")
sids = (sel.groupby("team").head(EPISODES_PER_TEAM).episode_id.drop_duplicates().tolist())

# With stream_hashes.csv attached every episode is already fingerprinted, so the
# stratified draw is a SELECTION out of `fp` rather than a second hashing pass.
if "h24" in fp.columns and len(fp) > 20000:
    sfp = fp[fp.episode_id.isin(set(int(i) for i in sids))].copy()
else:
    sfp = precomputed("seat_fingerprints_teams.parquet", "seat_fingerprints.parquet")
    if sfp is None:
        print("no precomputed table found, hashing the replays (about 8 minutes)")
        sfp = harvest(sorted(sids), "stratified ")
sfp = sfp[sfp["type"] == "EPISODE_TYPE_PUBLIC"] if "type" in sfp else sfp
print(f"\n{len(sfp):,} seats, {sfp.episode_id.nunique():,} episodes, "
      f"{sfp.team.nunique():,} teams")

# For within-team comparisons only. Never for a frequency.
pool = pd.concat([fp, sfp], ignore_index=True).drop_duplicates(["episode_id", "seat"])
print(f"pooled for within-team work: {len(pool):,} seats, "
      f"{pool.team.nunique():,} teams")

def diversity(labels):
    c = pd.Series(labels).value_counts()
    n = int(c.sum())
    p = c / n
    f1 = int((c == 1).sum())                 # schedules seen exactly once
    return {"schedules": len(c),
            "seen once %": 100 * f1 / len(c),
            "largest %": 100 * p.max(),
            "effective (1/HHI)": 1 / (p ** 2).sum(),
            "coverage %": 100 * (1 - f1 / n)}


tab = pd.DataFrame({h: diversity(fp[f"h{h}"]) for h in [24, 100, 200, 400, 719]}).T
tab.index.name = "agree to turn"
display(tab.style.format({"schedules": "{:,.0f}", "seen once %": "{:.0f}",
                          "largest %": "{:.1f}", "effective (1/HHI)": "{:,.0f}",
                          "coverage %": "{:.0f}"}))

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
axes[0].plot(tab.index, tab["schedules"], lw=2, color=BLUE, marker="o", ms=6)
axes[0].plot(tab.index, tab["effective (1/HHI)"], lw=2, color=ORANGE, marker="o", ms=6)
axes[0].annotate("schedules seen", (tab.index[-1], tab["schedules"].iloc[-1]),
                 xytext=(-6, 8), textcoords="offset points", ha="right",
                 color=BLUE, fontsize=9, fontweight="bold")
axes[0].annotate("effective (1/HHI)", (tab.index[-1], tab["effective (1/HHI)"].iloc[-1]),
                 xytext=(-6, -14), textcoords="offset points", ha="right",
                 color=ORANGE, fontsize=9, fontweight="bold")
axes[0].set_yscale("log")
tidy(axes[0], "count (log)", "Diversity, against how much of the game you look at")
axes[0].set_xlabel("agree to turn")

axes[1].plot(tab.index, tab["coverage %"], lw=2, color=BLUE, marker="o", ms=6)
axes[1].axhline(50, color=MUTED, lw=1, ls=":")
axes[1].annotate("half the next draws land on\nsomething never seen", (200, 50),
                 xytext=(0, 12), textcoords="offset points", fontsize=8.5, color=MUTED)
tidy(axes[1], "coverage, %", "How much of the field we have actually seen")
axes[1].set_xlabel("agree to turn"); axes[1].set_ylim(0, 100)
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(8, 3.8))
shared = [100 * fp[f"h{h}"].map(fp[f"h{h}"].value_counts()).gt(1).mean() for h in HORIZONS_AVAILABLE]
largest = [100 * fp[f"h{h}"].value_counts().iloc[0] / len(fp) for h in HORIZONS_AVAILABLE]
ax.plot(HORIZONS_AVAILABLE, shared, lw=2, color=BLUE, marker="o", ms=6)
ax.plot(HORIZONS_AVAILABLE, largest, lw=2, color=ORANGE, marker="o", ms=6)
for y, lab, col in ((shared, "seats sharing their stream\nwith at least one other seat", BLUE),
                    (largest, "seats on the single\nmost played stream", ORANGE)):
    ax.annotate(lab, (HORIZONS_AVAILABLE[-1], y[-1]), xytext=(-14, 22), textcoords="offset points",
                ha="right", fontsize=9, color=col, fontweight="bold")
tidy(ax, "percent of all seats", "Agreement is a curve, and it falls away fast after turn 200")
ax.set_xlabel("required to agree up to turn")
ax.set_ylim(0, 100)
plt.tight_layout(); plt.show()

by_day = []
for d, g in fp.groupby("day"):
    if len(g) < 60:                       # a day too thin to summarise
        continue
    s = diversity(g["h24"])
    by_day.append({"day": d, "seats": len(g),
                   "effective": s["effective (1/HHI)"], "largest %": s["largest %"]})
by_day = pd.DataFrame(by_day)

fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(by_day.day, by_day.effective, lw=2, color=BLUE, marker="o", ms=6)
for pos in (0, len(by_day) // 2, len(by_day) - 1):
    r = by_day.iloc[pos]
    ax.annotate(f"{r.effective:.0f}", (r.day, r.effective), xytext=(0, 10),
                textcoords="offset points", ha="center", color=BLUE, fontweight="bold")
tidy(ax, "effective number of openings at turn 24",
     "The field stopped being an ecology and became a monoculture")
ax.set_ylim(0, None)
plt.tight_layout(); plt.show()
display(by_day.style.format({"seats": "{:,.0f}", "effective": "{:.1f}",
                             "largest %": "{:.1f}"}).hide(axis="index"))

# The windows are DERIVED, never written down. This dataset is refreshed daily,
# so hard-coded dates would quietly stop selecting anything a week from now and
# the panel test would return an empty comparison instead of an error.
days = sorted(fp.day.unique())
w = max(1, len(days) // 3)
EARLY, LATE = days[:w], days[-w:]
print(f"early window {EARLY[0]} to {EARLY[-1]}   "
      f"late window {LATE[0]} to {LATE[-1]}   ({len(days)} days observed)")
assert len(days) >= 6, "too few days in this dataset to split into windows"

DOM = fp[fp.day.isin(LATE)].h24.value_counts().index[0]
is_dom = fp.h24 == DOM
share = pd.DataFrame({"share": is_dom.groupby(fp.day).mean(),
                      "teams": fp[is_dom].groupby("day").team.nunique()}).fillna(0)

# Error bars, because a bar chart without them invites reading the wiggles.
# The sampling unit is the episode and each contributes two seats that are each
# other's opponent, so the seats are not independent: the design effect is
# 1 + ICC, with the ICC measured between the two seats of an episode.
a_ = fp[fp.seat == 0].set_index("episode_id")["h24"].eq(DOM)
b_ = fp[fp.seat == 1].set_index("episode_id")["h24"].eq(DOM)
pair = pd.concat([a_.rename("x"), b_.rename("y")], axis=1).dropna()
ICC = float(np.corrcoef(pair.x.astype(float), pair.y.astype(float))[0, 1])
DEFF = 1 + ICC
FPC = np.sqrt(max(0.0, 1 - fp.episode_id.nunique() / len(meta)))
n_day = fp.groupby("day").size().reindex(share.index).fillna(1)
err = 100 * 1.96 * np.sqrt(np.maximum(share.share * (1 - share.share), 1e-12)
                           / n_day) * np.sqrt(DEFF) * FPC

fig, ax = plt.subplots(figsize=(8, 3.4))
ax.bar(share.index, 100 * share.share, color=BLUE, width=0.62,
       yerr=err, error_kw=dict(ecolor=MUTED, lw=1, capsize=3))
first_day = fp.loc[is_dom, "day"].min()
ax.annotate(f"first appears\n{first_day}", (first_day, 2), xytext=(0, 42),
            textcoords="offset points", ha="center", fontsize=9, color=MUTED,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
tidy(ax, "percent of all seats played that day",
     f"One opening ({DOM[:8]}) takes the field in about 48 hours")
plt.tight_layout(); plt.show()

g = fp[is_dom]
print(f"{len(g):,} seats, {g.team.nunique():,} teams, median bank {g.bank.median():,.0f}")
print(f"intraclass correlation between the two seats of an episode: {ICC:.2f}, "
      f"so the design effect is {DEFF:.2f}")
print(f"effective sample size: {len(fp) / DEFF:,.0f} rather than {len(fp):,}")
display(share.assign(**{"share %": 100 * share.share}).drop(columns="share")
        .style.format({"share %": "{:.1f}", "teams": "{:.0f}"}))

wts = precomputed("coverage_weights.parquet")
if wts is None:
    print("coverage_weights.parquet not attached, skipping the correction.")
else:
    wf = fp.merge(wts[["sub", "w"]], on="sub", how="left")
    wf["w"] = wf["w"].fillna(wf["w"].median())

    def concentration(g, weight=None):
        c = g.groupby("h24")[weight].sum() if weight else g["h24"].value_counts()
        q = c / c.sum()
        return 1 / (q ** 2).sum(), 100 * q.max()

    rows = []
    for d, g in wf.groupby("day"):
        if len(g) < 60:
            continue
        raw_eff, raw_top = concentration(g)
        adj_eff, adj_top = concentration(g, "w")
        rows.append({"day": d, "effective": raw_eff, "effective, weighted": adj_eff,
                     "top %": raw_top, "top %, weighted": adj_top})
    corr = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.5))
    axes[0].plot(corr.day, corr["effective"], lw=2, color=GRID, marker="o", ms=5)
    axes[0].plot(corr.day, corr["effective, weighted"], lw=2, color=BLUE, marker="o", ms=6)
    axes[0].annotate("as sampled", (corr.day.iloc[1], corr["effective"].iloc[1]),
                     xytext=(6, -14), textcoords="offset points", color=MUTED, fontsize=9)
    axes[0].annotate("weighted", (corr.day.iloc[1], corr["effective, weighted"].iloc[1]),
                     xytext=(6, 6), textcoords="offset points", color=BLUE,
                     fontsize=9, fontweight="bold")
    tidy(axes[0], "effective openings at turn 24", "The collapse survives the correction")
    axes[0].set_ylim(0, None)

    axes[1].plot(corr.day, corr["top %"], lw=2, color=GRID, marker="o", ms=5)
    axes[1].plot(corr.day, corr["top %, weighted"], lw=2, color=ORANGE, marker="o", ms=6)
    tidy(axes[1], "share of the most played opening, %",
         "But the raw numbers overstate how dominant it was")
    plt.tight_layout(); plt.show()

    for lab, wcol in (("as sampled", None), ("weighted", "w")):
        e, t = concentration(wf, wcol)
        print(f"  over the whole window, {lab:>10}: "
              f"{e:>5.1f} effective openings, top holds {t:.1f}%")

# POOLED, deliberately. This compares each team with itself, so how the teams
# were sampled cannot bias it, and pooling roughly doubles the panel.
panel = set(pool[pool.day.isin(EARLY)].team) & set(pool[pool.day.isin(LATE)].team)
pe = pool[pool.day.isin(EARLY) & pool.team.isin(panel)]
pl = pool[pool.day.isin(LATE) & pool.team.isin(panel)]


def dom_share(frame_):
    # No groupby.apply here. `include_groups=` only exists on pandas 2.2+, and
    # without it the same call warns on 2.2 and errors on some 2.1 builds. A
    # boolean mean per team needs neither.
    return frame_.assign(_dom=frame_["h24"] == DOM).groupby("team")["_dom"].mean()


j = pd.concat([dom_share(pe).rename("early"), dom_share(pl).rename("late")], axis=1).dropna()

print(f"teams observed in both windows        {len(j):,}")
print(f"  share of their EARLY seats on it    {100 * j.early.mean():.1f}%")
print(f"  share of their LATE  seats on it    {100 * j.late.mean():.1f}%")
print(f"  teams that adopted it               {int(((j.early == 0) & (j.late > 0)).sum())}")
print(f"  teams that abandoned it             {int(((j.early > 0) & (j.late == 0)).sum())}")
print(f"\nwithin that fixed panel, effective openings at turn 24: "
      f"{diversity(pe.h24)['effective (1/HHI)']:.1f} early "
      f"to {diversity(pl.h24)['effective (1/HHI)']:.1f} late")

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
moved = j[(j.early == 0) & (j.late > 0)].shape[0]
kept = j[(j.early > 0) & (j.late == 0)].shape[0]
other = len(j) - moved - kept

axes[0].bar(["adopted it", "dropped it", "did neither"], [moved, kept, other],
            color=[BLUE, ORANGE, GRID], width=0.6)
for x, v in enumerate([moved, kept, other]):
    axes[0].annotate(str(v), (x, v), xytext=(0, 4), textcoords="offset points",
                     ha="center", fontweight="bold", color=MUTED)
tidy(axes[0], f"teams, of {len(j)} in the panel", "Traffic is one way")

for y, lab in ((diversity(pe.h24)["effective (1/HHI)"], "early"),
               (diversity(pl.h24)["effective (1/HHI)"], "late")):
    axes[1].bar(lab, y, color=BLUE, width=0.5)
    axes[1].annotate(f"{y:.1f}", (lab, y), xytext=(0, 4), textcoords="offset points",
                     ha="center", fontweight="bold", color=MUTED)
tidy(axes[1], "effective openings at turn 24", "The same teams, before and after")
plt.tight_layout(); plt.show()

fan = pd.DataFrame({
    "agree to turn": HORIZONS_AVAILABLE,
    "distinct continuations": [g[f"h{h}"].nunique() for h in HORIZONS_AVAILABLE],
    "seats in the largest": [g[f"h{h}"].value_counts().iloc[0] for h in HORIZONS_AVAILABLE]})

fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(fan["agree to turn"], fan["distinct continuations"], lw=2, color=ORANGE,
        marker="o", ms=6, label="distinct continuations")
ax.plot(fan["agree to turn"], fan["seats in the largest"], lw=2, color=BLUE,
        marker="o", ms=6, label="seats still in the largest group")
tidy(ax, f"among the {len(g):,} seats sharing this opening",
     "Identical up to turn 100, then it comes apart")
ax.set_xlabel("agree to turn")
ax.legend(frameon=False, loc="upper left")
plt.tight_layout(); plt.show()
display(fan.style.hide(axis="index"))

rng = np.random.default_rng(SEED)     # one generator, constructed once
HS = [24, 100, 200, 400, 719]
# sorted(set(...)): if len(fp) lands on a preset size the list gets a duplicate,
# the final elasticity divides by zero, and the cell quietly reports nan.
sizes = sorted({s for s in (250, 500, 1000, 2000, 4000, len(fp)) if s <= len(fp)})
cols = {h: fp[f"h{h}"].to_numpy() for h in HS}

curve = {h: [] for h in HS}
for m in sizes:
    for h in HS:
        vals = []
        for _ in range(12):
            take = rng.choice(len(fp), size=m, replace=False)
            c = pd.Series(cols[h][take]).value_counts().to_numpy()
            p = c / c.sum()
            vals.append(1 / (p ** 2).sum())
        curve[h].append(float(np.mean(vals)))

fig, ax = plt.subplots(figsize=(8, 4.2))
for (h, ys), col in zip(curve.items(), ramp(len(HS))):
    ax.plot(sizes, ys, lw=2, color=col, marker="o", ms=5)
    ax.annotate(f"turn {h}", (sizes[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                va="center", color=col, fontsize=9, fontweight="bold")
tidy(ax, "effective number of schedules (1/HHI)",
     "Only the opening horizon has stopped moving")
ax.set_xlabel("seats drawn")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(200, sizes[-1] * 2.6)
plt.tight_layout(); plt.show()

lo, hi = sizes[-2], sizes[-1]
print("How much of the last increase in sample size showed up in the statistic")
print("1.0 means it is purely counting the sample, 0.0 means it has converged\n")
for h in HS:
    a, b = curve[h][-2], curve[h][-1]
    e = ((b - a) / a) / ((hi - lo) / lo)
    verdict = "ARTEFACT" if e > 0.5 else "converged" if e < 0.2 else "partial"
    print(f"  turn {h:>3}   {e:>5.2f}   {verdict}")

proven = []
for team, gt in sfp.groupby("team"):             # keyed on team ID, never the display name
    if gt.episode_id.nunique() < 2:
        continue
    for sha, gg in gt.groupby("full_sha"):
        # The seed lives in the replay, not in stream_hashes.csv, so when the
        # hashes come from the CSV the seed clause is carried by the episode
        # clause instead. That substitution is measured rather than assumed: over
        # 80 recorded matchups where we hold both, every distinct episode carried
        # a distinct seed, which is what the engine's per-episode seed derivation
        # implies. Where the seed IS available the original three-clause test runs.
        seeds_ok = (gg.seed.nunique() >= 2 if "seed" in gg.columns
                    else gg.episode_id.nunique() >= 2)
        if (gg.episode_id.nunique() >= 2          # two different games
                and seeds_ok                       # at two different seeds
                and gg.opponent.nunique() >= 2):  # against two different rivals
            proven.append({"team": team, "schedule": sha,
                           "identical_games": gg.episode_id.nunique(),
                           "median_bank": gt.bank.median()})
            break
proven = pd.DataFrame(proven)
testable = int((sfp.groupby("team").episode_id.nunique() >= 2).sum())

START_CASH = 3000
alive = proven[proven.median_bank > 3 * START_CASH]
print(f"teams with at least 2 episodes (testable)      {testable:,}")
print(f"teams PROVEN to be replaying a recording       {len(proven):,}")
print(f"  after excluding teams banking under ${3 * START_CASH:,}    {len(alive):,}")
print(f"distinct schedules among the proven teams      {proven.schedule.nunique():,}")

fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.6))
bars = [("teams with 2+\nepisodes", testable),
        ("provably\nreplaying", len(proven)),
        ("...and banking\nabove $9,000", len(alive))]
axes[0].bar([b[0] for b in bars], [b[1] for b in bars],
            color=[GRID, ORANGE, BLUE], width=0.6)
for x, (_, v) in enumerate(bars):
    axes[0].annotate(f"{v:,}", (x, v), xytext=(0, 4), textcoords="offset points",
                     ha="center", fontweight="bold", color=MUTED)
tidy(axes[0], "teams", "Each filter costs teams, and the last one matters")

banks = proven.median_bank if len(proven) else pd.Series([0.0])
axes[1].hist(banks, bins=30, color=BLUE)
axes[1].axvline(3 * START_CASH, color=ORANGE, lw=2)
axes[1].annotate("the $9,000 cut", (3 * START_CASH, axes[1].get_ylim()[1] * 0.8),
                 xytext=(8, 0), textcoords="offset points", color=ORANGE,
                 fontsize=9, fontweight="bold")
tidy(axes[1], "teams", "Median bank of the teams we just proved")
axes[1].set_xlabel("median bank")
axes[1].xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v/1000:,.0f}k"))
plt.tight_layout(); plt.show()

dead = sfp[sfp.bank <= START_CASH]
big = dead.full_sha.value_counts().index[0]
d = sfp[sfp.full_sha == big]

rank = list(sfp.full_sha.value_counts().index).index(big) + 1
print(f"{len(d)} seats across {d.team.nunique()} teams, every one of them banking "
      f"${d.bank.min():,} to ${d.bank.max():,}")
print(f"rank of this schedule among all full-game schedules, by seats: {rank}\n")

_, one = next(iter(store().fetch([int(d.iloc[0].episode_id)])))
steps = json.loads(one)["steps"]
acts = [st[int(d.iloc[0].seat)].get("action") for st in steps[1:]]
print("distinct actions across all 719 turns:", len(Counter(map(canon, acts))))
print("the action, every single turn:", canon(acts[0]))

from math import comb

pool = pd.concat([fp, sfp], ignore_index=True).drop_duplicates(["episode_id", "seat"])
pool["opening"] = pool["h24"]

MIN_SEATS, MIN_GAMES, ALPHA = 40, 15, 0.10
counts = pool.opening.value_counts()
openings = list(counts[counts >= MIN_SEATS].index)
oi = {o: k for k, o in enumerate(openings)}
n = len(openings)


def binom_p(k, m, _p=0.5):
    """Two-sided exact binomial tail. m is small here, so no approximation."""
    if m == 0:
        return 1.0
    lo = min(k, m - k)
    return min(1.0, 2 * sum(comb(m, i) for i in range(lo + 1)) / 2 ** m)


d = pool[pool.opening.isin(openings)]
a = d[d.seat == 0].set_index("episode_id")[["opening", "bank"]]
b = d[d.seat == 1].set_index("episode_id")[["opening", "bank"]]
h2h = a.join(b, how="inner", lsuffix="_0", rsuffix="_1").dropna()

wins, games = np.zeros((n, n)), np.zeros((n, n))
for o0, b0, o1, b1 in zip(h2h.opening_0, h2h.bank_0, h2h.opening_1, h2h.bank_1):
    i, j = oi[o0], oi[o1]
    if i == j:
        continue
    games[i, j] += 1; games[j, i] += 1
    w = 1.0 if b0 > b1 else 0.0 if b1 > b0 else 0.5
    wins[i, j] += w; wins[j, i] += 1 - w

beats = np.zeros((n, n), bool)
oriented = 0
for i in range(n):
    for j in range(i + 1, n):
        g_ = int(games[i, j])
        if g_ < MIN_GAMES:
            continue
        w = int(round(wins[i, j]))
        if binom_p(w, g_) > ALPHA:
            continue
        oriented += 1
        beats[i, j] = w * 2 > g_
        beats[j, i] = not beats[i, j]

pairs = n * (n - 1) // 2
print(f"{n} openings with at least {MIN_SEATS} seats "
      f"({100 * pool.opening.isin(openings).mean():.0f}% of the field)")
print(f"  pairs of openings                 {pairs}")
print(f"  pairs that ever meet              {int((games[np.triu_indices(n, 1)] > 0).sum())}")
print(f"  pairs meeting {MIN_GAMES}+ times          "
      f"{int((games[np.triu_indices(n, 1)] >= MIN_GAMES).sum())}")
print(f"  pairs we can orient               {oriented}  "
      f"({100 * oriented / pairs:.0f}% of the tournament)")

tri = [(i, j, k) for i in range(n) for j in range(n) for k in range(n)
       if i < j and i < k and beats[i, j] and beats[j, k] and beats[k, i]]
complete = sum(1 for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n)
               if (beats[i, j] or beats[j, i]) and (beats[j, k] or beats[k, j])
               and (beats[i, k] or beats[k, i]))

print(f"triples with all three edges oriented   {complete}")
print(f"rock-paper-scissors triples found       {len(tri)}")
print(f"expected if each were oriented by coin  {complete / 4:.1f}")
print(f"P(finding zero | every triple a coin)   {(3 / 4) ** complete:.3f}")

def tourney(frame_, horizon, min_seats=40, min_games=15, alpha=0.10):
    """The tournament at one horizon. Returns counts, not the matrix."""
    f2 = frame_.copy()
    f2["opening"] = f2[f"h{horizon}"]
    cnt = f2.opening.value_counts()
    ops = list(cnt[cnt >= min_seats].index)
    m = len(ops)
    if m < 3:
        return {"horizon": horizon, "species": m, "covered": np.nan,
                "meet": 0, "oriented": 0, "triples": 0, "cycles": 0}
    ix = {o: k for k, o in enumerate(ops)}
    dd = f2[f2.opening.isin(ops)]
    l0 = dd[dd.seat == 0].set_index("episode_id")[["opening", "bank"]]
    l1 = dd[dd.seat == 1].set_index("episode_id")[["opening", "bank"]]
    mm = l0.join(l1, how="inner", lsuffix="_0", rsuffix="_1").dropna()
    W, G = np.zeros((m, m)), np.zeros((m, m))
    for o0, b0, o1, b1 in zip(mm.opening_0, mm.bank_0, mm.opening_1, mm.bank_1):
        u, v = ix[o0], ix[o1]
        if u == v:
            continue
        G[u, v] += 1; G[v, u] += 1
        w = 1.0 if b0 > b1 else 0.0 if b1 > b0 else 0.5
        W[u, v] += w; W[v, u] += 1 - w
    B = np.zeros((m, m), bool)
    orient = 0
    for u in range(m):
        for v in range(u + 1, m):
            gg = int(G[u, v])
            if gg < min_games:
                continue
            w = int(round(W[u, v]))
            if binom_p(w, gg) > alpha:
                continue
            orient += 1
            B[u, v] = w * 2 > gg
            B[v, u] = not B[u, v]
    cyc = sum(1 for u in range(m) for v in range(m) for z in range(m)
              if u < v and u < z and B[u, v] and B[v, z] and B[z, u])
    trip = sum(1 for u in range(m) for v in range(u + 1, m) for z in range(v + 1, m)
               if (B[u, v] or B[v, u]) and (B[v, z] or B[z, v]) and (B[u, z] or B[z, u]))
    return {"horizon": horizon, "species": m,
            "covered": 100 * f2.opening.isin(ops).mean(),
            "meet": int((G[np.triu_indices(m, 1)] > 0).sum()),
            "oriented": orient, "triples": trip, "cycles": cyc}


swept = pd.DataFrame([tourney(pool, h) for h in HORIZONS_AVAILABLE])
display(swept.style.format({"covered": "{:.0f}%"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(8, 3.9))
for y, lab, col in ((swept.oriented, "pairs we can orient", BLUE),
                    (swept.triples, "triples we can test", ORANGE),
                    (swept.cycles, "cycles found", AQUA)):
    ax.plot(swept.horizon, y, lw=2, color=col, marker="o", ms=6, zorder=3)
    k = int(np.argmax(y.to_numpy()))
    ax.annotate(lab, (swept.horizon[k], y[k]), xytext=(10, 8),
                textcoords="offset points", fontsize=9, color=col, fontweight="bold")
tidy(ax, "count", "The window in which this question can be asked at all")
ax.set_xlabel("species defined by agreement up to turn")
plt.tight_layout(); plt.show()

exact = pool[pool.team.isin(set(proven.team))] if len(proven) else pool.iloc[:0]
print(f"{proven.team.nunique() if len(proven) else 0} teams proven open-loop, "
      f"{len(exact):,} of their seats ({100 * len(exact) / len(pool):.0f}% of the pool)\n")
display(pd.DataFrame([tourney(exact, h, min_seats=5, min_games=5) for h in HORIZONS_AVAILABLE])
        .style.format({"covered": "{:.0f}%"}).hide(axis="index"))

off = ~np.eye(n, dtype=bool)
raw = np.array([wins[i][off[i]].sum() / max(1, games[i][off[i]].sum()) for i in range(n)])

# Bradley-Terry by MM iteration. Raw win rate is confounded by WHO you met: an
# opening whose only recorded opponents were the do-nothing agents scores 1.00
# and means nothing by it.
bt = np.ones(n)
for _ in range(500):
    new = np.empty(n)
    for i in range(n):
        den = sum(games[i, j] / (bt[i] + bt[j]) for j in range(n)
                  if j != i and games[i, j] > 0)
        new[i] = wins[i][off[i]].sum() / den if den > 0 else bt[i]
    new = np.where(np.isfinite(new) & (new > 0), new, bt)
    new /= np.exp(np.mean(np.log(new)))          # BT is scale-free; fix the scale
    if np.max(np.abs(np.log(new / bt))) < 1e-9:
        bt = new
        break
    bt = new

rat = pool[pool.opening.isin(openings)].groupby("opening").rating.median()
strength = pd.DataFrame({
    "opening": openings, "seats": [counts[o] for o in openings],
    "raw win rate": raw, "BT strength": bt,
    "median rating": [rat.get(o, np.nan) for o in openings]}).dropna()

fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.scatter(strength["BT strength"].clip(lower=1e-3), strength["median rating"],
           s=18 + 62 * strength.seats / strength.seats.max(),
           color=BLUE, alpha=0.75, edgecolor="white", lw=1.2, zorder=3)
worst = strength.nsmallest(1, "BT strength").iloc[0]
best = strength.nlargest(1, "BT strength").iloc[0]
top_rated = strength.nlargest(1, "median rating").iloc[0]
for r, lab, dx in ((best, "strongest opening", -10), (top_rated, "highest rated seats", -10)):
    ax.annotate(lab, (max(r["BT strength"], 1e-3), r["median rating"]),
                xytext=(dx, 16), textcoords="offset points", ha="right", fontsize=9,
                color=MUTED, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
tidy(ax, "median ladder rating of the seats playing it",
     "Winning against other openings does not put you up the ladder")
ax.set_xlabel("Bradley-Terry strength among openings (log scale)")
ax.set_xscale("log")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:,.0f}"))
plt.tight_layout(); plt.show()

for lab, col in (("raw win rate", "raw win rate"), ("BT strength", "BT strength")):
    rho = strength[col].corr(strength["median rating"], method="spearman")
    print(f"Spearman({lab}, median rating of its seats) = {rho:+.2f}   "
          f"n = {len(strength)} openings")
display(strength.sort_values("BT strength", ascending=False)
        .style.format({"seats": "{:,.0f}", "raw win rate": "{:.2f}",
                       "BT strength": "{:,.2f}", "median rating": "{:,.0f}"})
        .hide(axis="index"))

rows = []
for thr in (20, 30, 40, 60, 80, 120):
    ops = list(counts[counts >= thr].index)
    if len(ops) < 4:
        continue
    sub = strength[strength.opening.isin(ops)]
    if len(sub) < 4:
        continue
    rows.append({"min seats": thr, "openings": len(sub),
                 "Spearman(raw, rating)": sub["raw win rate"].corr(
                     sub["median rating"], method="spearman"),
                 "Spearman(BT, rating)": sub["BT strength"].corr(
                     sub["median rating"], method="spearman")})
sens = pd.DataFrame(rows)

fig, ax = plt.subplots(figsize=(7.6, 3.4))
ax.axhline(0, color=MUTED, lw=1)
ax.plot(sens["min seats"], sens["Spearman(BT, rating)"], lw=2, color=BLUE, marker="o", ms=6)
ax.plot(sens["min seats"], sens["Spearman(raw, rating)"], lw=2, color=ORANGE, marker="o", ms=6)
ax.annotate("BT strength", (sens["min seats"].iloc[-1], sens["Spearman(BT, rating)"].iloc[-1]),
            xytext=(8, 0), textcoords="offset points", va="center", color=BLUE,
            fontsize=9, fontweight="bold")
ax.annotate("raw win rate", (sens["min seats"].iloc[-1], sens["Spearman(raw, rating)"].iloc[-1]),
            xytext=(8, 0), textcoords="offset points", va="center", color=ORANGE,
            fontsize=9, fontweight="bold")
tidy(ax, "Spearman correlation with median rating",
     "The same question, answered differently by an arbitrary threshold")
ax.set_xlabel("minimum seats for an opening to enter the scatter")
ax.set_ylim(-1, 1); ax.set_xlim(sens["min seats"].min() - 8, sens["min seats"].max() + 34)
plt.tight_layout(); plt.show()
display(sens.style.format({"Spearman(raw, rating)": "{:+.2f}",
                           "Spearman(BT, rating)": "{:+.2f}"}).hide(axis="index"))

strength_of = dict(zip(strength.opening, strength["BT strength"]))
rows = []
for team, gt in pool.dropna(subset=["rating"]).groupby("team"):
    if gt.opening.nunique() < 2:
        continue
    by = gt.groupby("opening").agg(rating=("rating", "median"), day=("day", "min"),
                                   k=("rating", "size"))
    by = by[by.k >= 2].sort_values("day")
    if len(by) < 2 or by.index[0] == by.index[-1]:
        continue
    first, last = by.iloc[0], by.iloc[-1]
    rows.append({"d_rating": last.rating - first.rating,
                 "d_strength": (strength_of.get(by.index[-1], np.nan)
                                - strength_of.get(by.index[0], np.nan))})
sw = pd.DataFrame(rows)
ok = sw.dropna()
print(f"teams that switched opening, with 2+ rated games each side   {len(sw):,}")
print(f"median rating change on switching                            {sw.d_rating.median():+,.0f}")
print(f"Spearman(change in opening strength, change in own rating)   "
      f"{ok.d_strength.corr(ok.d_rating, method='spearman'):+.2f}   n = {len(ok)}")

e_ = pool[pool.day.isin(EARLY)].dropna(subset=["rating"])
l_ = pool[pool.day.isin(LATE)].dropna(subset=["rating"])
both = set(e_.team) & set(l_.team)

groups = {"adopted the dominant one": set(), "changed to something else": set(),
          "did not change opening": set()}
for t in both:
    eo, lo = set(e_[e_.team == t].opening), set(l_[l_.team == t].opening)
    key = ("adopted the dominant one" if DOM in lo and DOM not in eo
           else "changed to something else" if lo - eo
           else "did not change opening")
    groups[key].add(t)

rows = []
for lab, grp in groups.items():
    ch = [l_[l_.team == t].rating.median() - e_[e_.team == t].rating.median() for t in grp]
    ch = [x for x in ch if pd.notna(x)]
    if ch:
        rows.append({"group": lab, "teams": len(ch), "median rating change": np.median(ch)})
adoption = pd.DataFrame(rows)
display(adoption.style.format({"median rating change": "{:+,.0f}"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(7.6, 3.6))
lab = [r["group"].replace(" the ", "\nthe ").replace(" to ", "\nto ") for r in rows]
val = [r["median rating change"] for r in rows]
ax.bar(lab, val, color=[BLUE, AQUA, GRID], width=0.55)
for x, (v, r) in enumerate(zip(val, rows)):
    ax.annotate(f"{v:+,.0f}\nn={r['teams']}", (x, v),
                xytext=(0, 6 if v > 0 else -22), textcoords="offset points",
                ha="center", fontweight="bold", color=MUTED, fontsize=9)
ax.axhline(0, color=MUTED, lw=1)
tidy(ax, "median change in rating", "Iterating beat picking the right line")
plt.tight_layout(); plt.show()