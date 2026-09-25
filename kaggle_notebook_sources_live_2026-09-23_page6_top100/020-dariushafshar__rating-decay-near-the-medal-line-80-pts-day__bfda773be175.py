import os, time, warnings
from collections import deque
from IPython.display import display

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
T0 = time.time()
SEARCH_ROOT = os.environ.get("SMOKE_ROOT", "/kaggle/input")


def find_file(name, root=SEARCH_ROOT, max_depth=5):
    q, hits = deque([(root, 0)]), []
    while q:
        d, depth = q.popleft()
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            continue
        for e in entries:
            try:
                if e.is_file() and e.name == name:
                    hits.append(e.path)
                elif e.is_dir() and depth < max_depth:
                    q.append((e.path, depth + 1))
            except OSError:
                continue
    if not hits:
        raise FileNotFoundError(f"{name!r} not found under {root}")
    hits.sort(key=len)
    return hits[0]


INDEX = find_file("snapshot_index.csv")
ROOT = os.path.dirname(INDEX)
idx = pd.read_csv(INDEX)
idx["captured"] = pd.to_datetime(idx.captured_utc).dt.tz_localize(None)   # all timestamps are UTC; drop tz so arithmetic stays simple
idx = idx.sort_values("captured").reset_index(drop=True)
print(f"archive: {ROOT}")
print(f"{len(idx)} snapshots, {idx.captured.min():%Y-%m-%d} -> {idx.captured.max():%Y-%m-%d}")

boards = {}
for _, r in idx.iterrows():
    b = pd.read_csv(os.path.join(ROOT, "snapshots", r.file))
    b["subm"] = b.LastSubmissionDate.astype(str)   # NOT "sub": DataFrame.sub is the subtract METHOD, and b.sub would silently hand you that
    boards[r.captured] = b
print(f"teams: {len(boards[idx.captured.iloc[0]]):,} at the first capture -> "
      f"{len(boards[idx.captured.iloc[-1]]):,} at the last")
print(f"[{time.time() - T0:.0f}s]")


show = idx[["captured_utc", "capture_basis", "teams", "top_score", "bronze_line_score", "median_score"]].copy()
show.columns = ["captured (UTC)", "capture time from", "teams", "top", "top-10% line", "median"]
display(show.style.hide(axis="index")
        .format({"teams": "{:,}", "top": "{:.1f}", "top-10% line": "{:.1f}", "median": "{:.1f}"})
        .background_gradient(cmap="Blues", subset=["teams"])
        .background_gradient(cmap="Oranges", subset=["top-10% line"])
        .set_caption("Every capture in the archive. 'capture time from' is how each timestamp was "
                     "established - see the honesty section at the end."))

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(idx.captured, idx.bronze_line_score, marker="o", lw=2, color="#d95f02", label="top-10% (bronze) line")
ax.plot(idx.captured, idx.median_score, marker="o", lw=2, color="#7570b3", label="median team")
ax2 = ax.twinx()
ax2.plot(idx.captured, idx.teams, marker="s", ls="--", lw=1.5, color="#1b9e77", label="teams")
ax2.set_ylabel("teams", color="#1b9e77")
ax.set_ylabel("score"); ax.set_title("The medal line fell 348 points while the field grew 5,185 teams", fontweight="bold")
ax.legend(loc="center left"); ax2.legend(loc="lower right"); plt.show()
print(f"[{time.time() - T0:.0f}s]")


newest = idx.captured.iloc[-1]
b = boards[newest].copy()
b["sub_dt"] = pd.to_datetime(b["subm"], errors="coerce")
b = b.dropna(subset=["sub_dt"]).sort_values("Score", ascending=False).reset_index(drop=True)
b["age_h"] = (newest - b.sub_dt).dt.total_seconds() / 3600.0
n = len(b)
bands = [("top 50", 0, 50), ("gold (top 2%)", 0, int(n * .02)), ("silver (2-5%)", int(n * .02), int(n * .05)),
         ("bronze (5-10%)", int(n * .05), int(n * .10)), ("10-20%", int(n * .10), int(n * .20)),
         ("20-40%", int(n * .20), int(n * .40)), ("bottom 60%", int(n * .40), n)]
rows = []
for lab, lo, hi in bands:
    g = b.iloc[lo:hi]
    rows.append({"band": lab, "teams": len(g), "median age (h)": g.age_h.median(),
                 "< 12 h": (g.age_h < 12).mean(), "< 24 h": (g.age_h < 24).mean(),
                 "< 48 h": (g.age_h < 48).mean(), ">= 7 d": (g.age_h >= 168).mean(),
                 "median score": g.Score.median()})
xs = pd.DataFrame(rows)
display(xs.style.hide(axis="index")
        .format({"teams": "{:,}", "median age (h)": "{:.1f}", "< 12 h": "{:.0%}", "< 24 h": "{:.0%}",
                 "< 48 h": "{:.0%}", ">= 7 d": "{:.0%}", "median score": "{:.1f}"})
        .background_gradient(cmap="RdYlGn_r", subset=["median age (h)"])
        .set_caption("Newest capture. The '>= 7 d' column is the one to look at."))

TOP10_OLD = float(b.iloc[:int(n * .10)].age_h.ge(168).mean())
print(f"\nteams in the top 10% running a submission 7+ days old: {TOP10_OLD:.1%}  "
      f"({int(b.iloc[:int(n*.10)].age_h.ge(168).sum())} of {int(n*.10)})")
rho_all = b.age_h.corr(b.Score, method="spearman")
rho_top = b.iloc[:int(n * .10)].age_h.corr(b.iloc[:int(n * .10)].Score, method="spearman")
print(f"Spearman(age, score): whole board {rho_all:+.3f} (n={n:,}); within the top 10% only {rho_top:+.3f}")
assert TOP10_OLD < 0.02, TOP10_OLD
assert rho_all < -0.4, rho_all
print("asserted: the top of the board is uniformly fresh, and age is strongly anti-correlated with score.")
print(f"[{time.time() - T0:.0f}s]")


caps = list(idx.captured)
recs = []
for t0, t1 in zip(caps, caps[1:]):
    dth = (t1 - t0).total_seconds() / 3600.0
    if not (4 <= dth <= 60):          # a 31-minute gap gives a per-hour rate dominated by one or two games
        continue
    a, bb = boards[t0], boards[t1]
    m = a[["TeamId", "Score", "subm"]].merge(bb[["TeamId", "Score", "subm"]], on="TeamId", suffixes=("_0", "_1"))
    m = m[m["subm_0"] == m["subm_1"]]
    m["sub_dt"] = pd.to_datetime(m["subm_0"], errors="coerce")
    m = m.dropna(subset=["sub_dt"])
    m["age_h"] = (t0 - m.sub_dt).dt.total_seconds() / 3600.0
    m["pts_per_h"] = (m.Score_1 - m.Score_0) / dth
    recs.append(m[["age_h", "pts_per_h", "Score_0"]])
d = pd.concat(recs, ignore_index=True)
print(f"{len(d):,} team-intervals where the same submission was active at both ends")
print(f"gaps used (h): {sorted(round((t1-t0).total_seconds()/3600, 1) for t0, t1 in zip(caps, caps[1:]) if 4 <= (t1-t0).total_seconds()/3600 <= 60)}")

def band(s):
    return ">= 2,500" if s >= 2500 else "2,000-2,500" if s >= 2000 else "1,000-2,000" if s >= 1000 else "< 1,000"

d["band"] = d.Score_0.apply(band)
order = [">= 2,500", "2,000-2,500", "1,000-2,000", "< 1,000"]
tab = (d.groupby("band")
         .agg(intervals=("pts_per_h", "size"), median_pts_per_h=("pts_per_h", "median"),
              share_falling=("pts_per_h", lambda s: (s < 0).mean()))
         .reindex(order).reset_index())
tab["per_day"] = tab.median_pts_per_h * 24
display(tab.style.hide(axis="index")
        .format({"intervals": "{:,}", "median_pts_per_h": "{:+.2f}", "per_day": "{:+.0f}", "share_falling": "{:.0%}"})
        .background_gradient(cmap="Reds_r", subset=["per_day"])
        .set_caption("Same submission, later. The agent did not change; the number did."))

MEDAL = float(tab.loc[tab.band == "2,000-2,500", "per_day"].iloc[0])
TOPBAND = float(tab.loc[tab.band == ">= 2,500", "per_day"].iloc[0])
WEAK = float(tab.loc[tab.band == "< 1,000", "per_day"].iloc[0])
print(f"\nmedal-line band: {MEDAL:+.0f} points per day;  strongest band: {TOPBAND:+.0f};  under 1,000: {WEAK:+.0f}")
assert MEDAL < -70, MEDAL
assert WEAK > -10, WEAK
print("asserted: the title's -80 is the 2,000-2,500 band, and the effect is concentrated near the top.")
print(f"[{time.time() - T0:.0f}s]")


def agebin(h):
    return "0-24 h" if h < 24 else "1-3 d" if h < 72 else "3-7 d" if h < 168 else "7-14 d" if h < 336 else "14 d +"

d["age_bin"] = d.age_h.apply(agebin)
aorder = ["0-24 h", "1-3 d", "3-7 d", "7-14 d", "14 d +"]
at = (d.groupby("age_bin")
        .agg(intervals=("pts_per_h", "size"), median_pts_per_h=("pts_per_h", "median"),
             share_falling=("pts_per_h", lambda s: (s < 0).mean()))
        .reindex(aorder).reset_index())
strong = d[d.Score_0 >= 2000]
st = (strong.groupby("age_bin").agg(strong_intervals=("pts_per_h", "size"),
                                    strong_median=("pts_per_h", "median")).reindex(aorder).reset_index())
at = at.merge(st, on="age_bin")
display(at.style.hide(axis="index")
        .format({"intervals": "{:,}", "median_pts_per_h": "{:+.2f}", "share_falling": "{:.0%}",
                 "strong_intervals": "{:,}", "strong_median": "{:+.2f}"})
        .background_gradient(cmap="Reds_r", subset=["strong_median"])
        .set_caption("By how old the submission already was. 'strong' = scoring 2,000+ at the start "
                     "of the interval - the teams the medal line actually runs through."))

fig, ax = plt.subplots(figsize=(10, 4.5))
for lab, g, c in ((">= 2,000 at start", strong, "#d95f02"), ("all teams", d, "#7570b3")):
    med = g.groupby("age_bin").pts_per_h.median().reindex(aorder)
    ax.plot(aorder, med.values, marker="o", lw=2, color=c, label=lab)
ax.axhline(0, color="black", lw=1)
ax.set_ylabel("median points per hour"); ax.set_xlabel("age of the submission at the start of the interval")
ax.set_title("The same agent, getting a lower number the longer it plays", fontweight="bold")
ax.legend(); plt.show()
print(f"[{time.time() - T0:.0f}s]")


MY_TEAM = ""      # <- your team name here, exactly as it appears on the leaderboard

def age_report(team_name, board=b, table=tab):
    hit = board[board.TeamName.str.lower() == str(team_name).strip().lower()]
    if not len(hit):
        print(f"'{team_name}' is not on the newest capture in this archive "
              f"({newest:%Y-%m-%d %H:%M} UTC). Teams that joined later will not be here.")
        return
    r = hit.iloc[0]
    pct = (board.age_h < r.age_h).mean()
    bnd = band(r.Score)
    per_day = float(table.loc[table.band == bnd, "per_day"].iloc[0])
    print(f"{r.TeamName}: rank {int(r.Rank)}, score {r.Score:.1f}")
    print(f"  submission age {r.age_h:.1f} h - fresher than {1-pct:.0%} of the board, older than {pct:.0%}")
    print(f"  score band {bnd}: teams there moved a median {per_day:+.0f} points per day while not resubmitting")

if MY_TEAM:
    age_report(MY_TEAM)
else:
    for demo in list(b.TeamName.head(3)) + ["Dariush Afshar"]:
        age_report(demo); print()
print(f"[{time.time() - T0:.0f}s]")
