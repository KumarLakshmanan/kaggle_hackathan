import os, glob, json, re, time, random
from collections import Counter
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams.update({"figure.dpi": 120, "font.size": 11, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False})
INK = "#1b2a4a"; ACC = "#c1440e"; ACC2 = "#1f6f8b"; GD = "#c29a22"; MUT = "#8a94a6"

ROOT = "/kaggle/input"
CAP_PER_DAY = 150      # replays sampled per day with a fixed seed; each replay is about 31 MB
MIN_DAYS = 3           # an agent enters the trajectory table with games on at least MIN_DAYS days
MIN_GAMES = 8          # and at least MIN_GAMES games in total
TOP_K = 10             # the daily top list: TOP_K agents by win rate
MIN_DAY_GAMES = 4      # among the agents with at least MIN_DAY_GAMES games that day

# Attached datasets mount two levels below /kaggle/input and keep their own folder layout, so walk the whole
# tree, keep every directory that holds numbered replay files, and read the day from the directory path.
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
def find_days(root):
    days = {}
    for d, _, fs in os.walk(root):
        js = [os.path.join(d, f) for f in fs if f.endswith(".json") and f[:-5].isdigit()]
        if not js:
            continue
        m = DATE_RE.search(os.path.relpath(d, root))
        if not m:
            print(f"skipped {len(js)} replays in {d}: no date in the path"); continue
        days.setdefault(m.group(1), []).extend(js)
    return {k: sorted(v) for k, v in days.items()}

days = find_days(ROOT)
assert days, f"no numbered replay json under {ROOT}: {os.listdir(ROOT) if os.path.isdir(ROOT) else 'missing'}"
DAYS = sorted(days)
sample = {}
for d in DAYS:
    fs = days[d]
    if len(fs) > CAP_PER_DAY:
        random.seed(0); fs = sorted(random.sample(fs, CAP_PER_DAY))
    sample[d] = fs
    print(f"{d}: {len(days[d])} replays in the dump, {len(fs)} sampled, {os.path.dirname(fs[0])}")
print("days:", len(DAYS), "| replays to parse:", sum(len(v) for v in sample.values()))

# parse_replay is copied verbatim from our earlier tracker notebook, "What actually wins on the Kaggriculture
# ladder" (busyaprime/what-actually-wins-on-the-kaggriculture-ladder), so both notebooks read a replay identically.
# each replay: rewards = [profit0, profit1] (winner = higher), info.TeamNames = the two agents,
# steps[i][seat].action = {farmer:[move], hands:[[op,...]], market:[[op,...]]} for 720 turns
CROP_KEYS = ["STRAWBERRY", "WHEAT", "MELON", "CARROT"]
def parse_replay(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return None
    rew = d.get("rewards") or []
    if len(rew) != 2 or rew[0] is None or rew[1] is None or rew[0] == rew[1]:
        return None                                   # unfinished or tied games are dropped
    names = (d.get("info") or {}).get("TeamNames") or ["?", "?"]
    winner = 0 if rew[0] > rew[1] else 1
    F = [dict(crops=Counter(), plant=0, sell=0, hire=0, buy_animal=0, buy_land=0, fert=0, harvest=0, water=0)
         for _ in range(2)]
    for st in d.get("steps", []):
        if not isinstance(st, list):
            continue
        for seat in range(min(2, len(st))):
            a = (st[seat] or {}).get("action") or {}
            for h in a.get("hands") or []:
                if not h:
                    continue
                op = h[0]
                if op == "PLANT":
                    F[seat]["plant"] += 1
                    if len(h) > 1: F[seat]["crops"][h[1]] += 1
                elif op == "COLLECT_FERTILIZER": F[seat]["fert"] += 1
                elif op == "HARVEST": F[seat]["harvest"] += 1
                elif op == "WATER": F[seat]["water"] += 1
            for mk in a.get("market") or []:
                if not mk:
                    continue
                op = mk[0]
                if op == "SELL": F[seat]["sell"] += 1
                elif op == "HIRE": F[seat]["hire"] += 1
                elif op == "BUY_ANIMAL": F[seat]["buy_animal"] += 1
                elif op == "BUY_LAND": F[seat]["buy_land"] += 1
    rows = []
    for seat in range(2):
        f = F[seat]
        rows.append(dict(agent=str(names[seat])[:28], win=int(seat == winner), score=float(rew[seat]),
                         top_crop=(f["crops"].most_common(1)[0][0] if f["crops"] else "none"),
                         plant=f["plant"], sell=f["sell"], hire=f["hire"], buy_animal=f["buy_animal"],
                         buy_land=f["buy_land"], fert=f["fert"], harvest=f["harvest"]))
    return rows

# one long table: a row per side, with the day, the episode id and the seat in front of the tracker's columns
# (score is the final bank of that side, straight from the replay rewards)
t0 = time.time(); rows = []; per_day = []
for d in DAYS:
    td = time.time(); n_ok = 0
    for k, p in enumerate(sample[d], 1):
        r = parse_replay(p)
        if r:
            n_ok += 1
            ep = os.path.basename(p)[:-5]
            for seat, row in enumerate(r):
                rows.append(dict(day=d, episode=ep, seat=seat, **row))
        if k % 50 == 0:
            print(f"  {d} {k}/{len(sample[d])} replays, {n_ok} decisive, {round(time.time()-td)}s", flush=True)
    per_day.append(dict(day=d, replays=len(sample[d]), decisive=n_ok, seconds=round(time.time()-td)))
    print(f"{d}: {len(sample[d])} replays, {n_ok} decisive games, {round(time.time()-td)}s", flush=True)
sides = pd.DataFrame(rows)
print(f"\nparsed {len(sides)//2} decisive games ({len(sides)} sides) across {len(DAYS)} days in {round(time.time()-t0)}s")
print("distinct agents seen:", sides["agent"].nunique())
non_ascii = sorted(a for a in sides["agent"].unique() if any(ord(ch) > 127 for ch in a))
print(f"agent names with non-ASCII characters: {len(non_ascii)}; the Kaggle image has no CJK font, "
      f"so these may render as boxes in the figures and are left as they are")

A = pd.DataFrame(per_day)
A["agents"] = A["day"].map(sides.groupby("day")["agent"].nunique())
seen = set(); new = []
for d in DAYS:
    today = set(sides.loc[sides["day"] == d, "agent"])
    new.append(len(today - seen)); seen |= today
A["new_agents"] = new
A["dump_replays"] = A["day"].map({d: len(days[d]) for d in DAYS})
A["sampled_pct"] = (100 * A["replays"] / A["dump_replays"]).round(1)
print(A[["day", "dump_replays", "replays", "sampled_pct", "decisive", "agents", "new_agents"]].to_string(index=False))
every = set.intersection(*[set(sides.loc[sides["day"] == d, "agent"]) for d in DAYS])
print(f"\nagents seen on every one of the {len(DAYS)} days: {len(every)} of {sides['agent'].nunique()}")

# the daily index has one row per day; the per-dump manifest.csv has a per-episode schema, so pick by columns
# and by the competition slug, and print the index rows for the days parsed here
man = None
for p in sorted(glob.glob(f"{ROOT}/**/manifest.csv", recursive=True)):
    try:
        t = pd.read_csv(p)
    except Exception:
        continue
    if not {"date", "episode_count", "median_avg_score"} <= set(t.columns):
        continue
    if "daily_dataset_slug" in t.columns and not t["daily_dataset_slug"].astype(str).str.contains("kaggriculture").any():
        continue
    man = t; break
if man is None:
    print("no daily index manifest attached")
else:
    ix = man[man["date"].astype(str).isin(DAYS)]
    cols = [c for c in ["date", "episode_count", "top_avg_score", "median_avg_score"] if c in ix.columns]
    print(f"\ndaily index ({len(man)} days, {man['date'].iloc[0]} to {man['date'].iloc[-1]}), rows for the days parsed here:")
    print(ix[cols].round(1).to_string(index=False) if len(ix) else "  none of the parsed days is in the index yet")

def wilson(w, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = w / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return p, c-h, c+h

def wls_slope(x, y, w):
    # least squares of the daily win rate on the day offset, each day weighted by its games
    x, y, w = (np.asarray(v, float) for v in (x, y, w))
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    den = (w * (x - xm) ** 2).sum()
    return (w * (x - xm) * (y - ym)).sum() / den if den > 0 else np.nan

XOFF = {d: (pd.Timestamp(d) - pd.Timestamp(DAYS[0])).days for d in DAYS}   # x axis in real calendar days
g = sides.groupby(["agent", "day"]).agg(games=("win", "size"), wins=("win", "sum")).reset_index()
g["wr"] = g["wins"] / g["games"]
tot = g.groupby("agent").agg(days=("day", "nunique"), games=("games", "sum"), wins=("wins", "sum"))
keep = tot[(tot["days"] >= MIN_DAYS) & (tot["games"] >= MIN_GAMES)].index
print(f"agents with games on at least {MIN_DAYS} days and at least {MIN_GAMES} games in total: {len(keep)} of {len(tot)}")
piv_g = g.pivot(index="agent", columns="day", values="games").reindex(keep).fillna(0).astype(int)
piv_w = g.pivot(index="agent", columns="day", values="wr").reindex(keep)
rec = []
for a in keep:
    sub = g[g["agent"] == a]
    p, lo, hi = wilson(int(tot.loc[a, "wins"]), int(tot.loc[a, "games"]))
    r = {"agent": a}
    for d in DAYS:
        n = int(piv_g.loc[a, d]) if d in piv_g.columns else 0
        r[d[5:]] = f"{100 * piv_w.loc[a, d]:.0f} ({n})" if n else "-"
    last = DAYS[-1]
    r.update(games=int(tot.loc[a, "games"]), days=int(tot.loc[a, "days"]),
             slope_pp_day=100 * wls_slope([XOFF[d] for d in sub["day"]], sub["wr"], sub["games"]),
             winrate=100 * p, lo=100 * lo, hi=100 * hi,
             last_day_wr=(100 * piv_w.loc[a, last] if last in piv_w.columns and piv_g.loc[a, last] > 0 else np.nan))
    rec.append(r)
TR = pd.DataFrame(rec)
if len(TR):
    TR = TR.sort_values(["last_day_wr", "winrate"], ascending=False, na_position="last").reset_index(drop=True)
print(f"win rate per day in per cent (games), then the games, the days, the slope in points per calendar day, "
      f"the overall win rate with its 95 per cent Wilson interval, and the win rate on {DAYS[-1]}; "
      f"sorted by the last day\n")
print(TR.round(1).to_string(index=False) if len(TR) else "no agent qualifies")

top_n = TR.sort_values("games", ascending=False)["agent"].head(8).tolist() if len(TR) else []
if len(top_n) and len(DAYS) >= 2:
    x = pd.to_datetime(DAYS)
    fig, ax = plt.subplots(figsize=(10, 5))
    palette = [INK, ACC, ACC2, GD, MUT, "#5b8c5a", "#7b4b94", "#b5651d"]
    for k, a in enumerate(top_n):
        y = [100 * piv_w.loc[a, d] if piv_g.loc[a, d] > 0 else np.nan for d in DAYS]
        ax.plot(x, y, marker="o", lw=1.8, color=palette[k % len(palette)], label=f"{a[:22]} ({int(tot.loc[a, 'games'])} games)")
    ax.axhline(50, color=MUT, lw=1, ls="--")
    ax.set_ylim(0, 100); ax.set_ylabel("win rate on the day, %")
    ax.xaxis.set_major_locator(mdates.DayLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.set_xlim(x.min() - pd.Timedelta(hours=12), x.max() + pd.Timedelta(hours=12))
    ax.set_title("win rate by day, the eight agents with the most games in the sample", color=INK, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    plt.tight_layout(); plt.savefig("fig1_trajectories.png", metadata={"Software": None}); plt.show()
else:
    print("fewer than two days or no qualifying agent, no trajectory figure")

def top_list(d):
    sub = g[(g["day"] == d) & (g["games"] >= MIN_DAY_GAMES)]
    sub = sub.sort_values(["wr", "games", "agent"], ascending=[False, False, True])
    return sub["agent"].head(TOP_K).tolist()

tops = {d: top_list(d) for d in DAYS}
for d in DAYS:
    q = int(((g["day"] == d) & (g["games"] >= MIN_DAY_GAMES)).sum())
    print(f"{d}: {q} agents with at least {MIN_DAY_GAMES} games, top {len(tops[d])} by win rate: {tops[d]}")
rec = []
for d0, d1 in zip(DAYS[:-1], DAYS[1:]):
    s0 = set(g.loc[g["day"] == d0, "agent"]); s1 = set(g.loc[g["day"] == d1, "agent"])
    kept = len(set(tops[d0]) & set(tops[d1]))
    rec.append(dict(pair=f"{d0[5:]} to {d1[5:]}", top_t=len(tops[d0]), top_kept=kept,
                    top_kept_pct=100 * kept / max(1, len(tops[d0])),
                    agents_t=len(s0), seen_next=len(s0 & s1), seen_next_pct=100 * len(s0 & s1) / max(1, len(s0)),
                    new_next=len(s1 - s0)))
TO = pd.DataFrame(rec)
print("\ntop_kept: agents of day t's top list still in day t+1's top list; seen_next: agents of day t with any game on day t+1; "
      "new_next: agents on day t+1 not seen on day t")
print(TO.round(1).to_string(index=False) if len(TO) else "fewer than two days, no turnover")

if len(TO):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].bar(TO["pair"], TO["top_kept"], color=INK, width=0.6)
    ax[0].set_ylim(0, TOP_K); ax[0].set_yticks(range(0, TOP_K + 1, max(1, TOP_K // 5)))
    ax[0].set_ylabel(f"of the top {TOP_K}, still in the next day's top {TOP_K}")
    ax[0].set_title("turnover at the top", color=INK, loc="left", fontweight="bold")
    ax[1].bar(TO["pair"], TO["seen_next_pct"], color=ACC2, width=0.6)
    ax[1].set_ylim(0, 100); ax[1].set_ylabel("agents of day t seen on day t+1, %")
    ax[1].set_title("turnover of the whole field", color=INK, loc="left", fontweight="bold")
    for a_ in ax:
        plt.setp(a_.get_xticklabels(), rotation=25, ha="right")
    plt.tight_layout(); plt.savefig("fig2_turnover.png", metadata={"Software": None}); plt.show()
else:
    print("fewer than two days, no turnover figure")

FD = sides.groupby(["day", "win"])["score"].median().unstack("win")
FD.columns = ["losing_median", "winning_median"]
FD["gap"] = FD["winning_median"] - FD["losing_median"]
FD["gap_pct"] = 100 * FD["gap"] / FD["losing_median"]
mg = sides.pivot(index=["day", "episode"], columns="seat", values="score")
FD["median_margin"] = (mg[0] - mg[1]).abs().groupby(level="day").median()
FD["games"] = sides.groupby("day")["episode"].nunique()
FD = FD.reset_index()
print("median final bank of the winning side and of the losing side per day, their gap, and the median in-game margin\n")
print(FD.round(1).to_string(index=False))
print(f"\nall days pooled: winning median {sides[sides.win == 1].score.median():.0f}, "
      f"losing median {sides[sides.win == 0].score.median():.0f}, "
      f"gap {sides[sides.win == 1].score.median() - sides[sides.win == 0].score.median():.0f}")

x = pd.to_datetime(FD["day"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].plot(x, FD["winning_median"], marker="o", lw=2, color=ACC, label="winning side, median bank")
ax[0].plot(x, FD["losing_median"], marker="o", lw=2, color=MUT, label="losing side, median bank")
ax[0].set_ylabel("final bank, coins"); ax[0].legend(frameon=False, fontsize=9)
ax[0].set_title("median final bank per day", color=INK, loc="left", fontweight="bold")
ax[1].bar(x - pd.Timedelta(hours=5), FD["gap"], width=0.35, color=ACC, label="gap of the medians")
ax[1].bar(x + pd.Timedelta(hours=5), FD["median_margin"], width=0.35, color=ACC2, label="median in-game margin")
ax[1].set_ylim(0, max(1.0, 1.2 * max(FD["gap"].max(), FD["median_margin"].max())))
ax[1].set_ylabel("coins"); ax[1].legend(frameon=False, fontsize=9)
ax[1].set_title("how close the games are", color=INK, loc="left", fontweight="bold")
for a_ in ax:
    a_.xaxis.set_major_locator(mdates.DayLocator()); a_.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    a_.set_xlim(x.min() - pd.Timedelta(hours=14), x.max() + pd.Timedelta(hours=14))
plt.tight_layout(); plt.savefig("fig3_banks.png", metadata={"Software": None}); plt.show()

# resample each day's games of an agent with replacement, keep the day counts, refit the weighted slope;
# an agent is climbing when the 95 per cent percentile interval of the slope lies above zero, falling when below
rng = np.random.default_rng(0); B = 2000
rec = []
for a in keep:
    sub = sides[sides["agent"] == a]
    per = {d: sub.loc[sub["day"] == d, "win"].to_numpy(float) for d in DAYS if (sub["day"] == d).any()}
    x = np.array([XOFF[d] for d in per], float); n = np.array([len(v) for v in per.values()], float)
    W = np.stack([rng.choice(v, size=(B, len(v)), replace=True).mean(axis=1) for v in per.values()], axis=1)
    xm = np.average(x, weights=n); ym = np.average(W, axis=1, weights=n)
    sl = 100 * ((W - ym[:, None]) * (x - xm) * n).sum(axis=1) / (n * (x - xm) ** 2).sum()
    point = 100 * wls_slope(x, [v.mean() for v in per.values()], n)
    lo, hi = np.percentile(sl, [2.5, 97.5])
    rec.append(dict(agent=a, games=int(n.sum()), days=len(per), slope_pp_day=point, boot_lo=lo, boot_hi=hi,
                    verdict="climbing" if lo > 0 else ("falling" if hi < 0 else "flat")))
BT = pd.DataFrame(rec)
if len(BT):
    BT = BT.sort_values("slope_pp_day", ascending=False).reset_index(drop=True)
print(f"slope of the daily win rate in points per calendar day, with a {B}-resample bootstrap interval\n")
print(BT.round(2).to_string(index=False) if len(BT) else "no agent qualifies")
if len(BT):
    for v in ["climbing", "falling", "flat"]:
        print(f"\n{v}: {int((BT['verdict'] == v).sum())} agents: {BT.loc[BT['verdict'] == v, 'agent'].tolist()}")