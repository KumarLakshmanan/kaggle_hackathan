import os, glob, json, re, time, random
from collections import Counter
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.dpi": 120, "font.size": 11, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False})
# agent names on this ladder include Japanese, Korean and Cyrillic. DejaVu Sans has no CJK glyphs, so
# look for any installed face that does and put it first; if the image ships none, say so once and move on.
import matplotlib.font_manager as _fm
_KEYS = ("CJK", "Gothic", "Mincho", "Droid Sans Fallback", "Arial Unicode", "Unifont",
         "Noto Sans JP", "Noto Sans KR", "Noto Sans SC", "Noto Serif CJK", "WenQuanYi")
_cjk = sorted({f.name for f in _fm.fontManager.ttflist if any(k in f.name for k in _KEYS)})
plt.rcParams["font.family"] = _cjk[:1] + ["DejaVu Sans"]
print("CJK capable fonts on this image:", _cjk if _cjk else "none, non latin agent names will show as boxes")

INK = "#1b2a4a"; ACC = "#c1440e"; ACC2 = "#1f6f8b"; GD = "#c29a22"; MUT = "#8a94a6"

def find_dir(must_digit_json=True):
    for d in sorted(glob.glob("/kaggle/input/*")):
        js = [p for p in glob.glob(os.path.join(d, "*.json")) if os.path.basename(p)[:-5].isdigit()]
        if not js:
            js = [p for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True)
                  if os.path.basename(p)[:-5].isdigit()]
        if js:
            return os.path.dirname(js[0])
    return None
def find_one(name):
    for p in glob.glob(f"/kaggle/input/**/{name}", recursive=True):
        return p
    return None

epdir = find_dir()
assert epdir is not None, "no numbered replay json folder found under /kaggle/input"
files = sorted(p for p in glob.glob(os.path.join(epdir, "*.json")) if os.path.basename(p)[:-5].isdigit())
CAP = 300                       # replays are ~25MB each; a seeded sample of the day keeps the run tractable
if len(files) > CAP:
    random.seed(0); files = sorted(random.sample(files, CAP))
_m = re.search(r"(\d{4}-\d{2}-\d{2})", epdir or ""); DAY = _m.group(1) if _m else "unknown"
print("replay dir:", epdir, "| day:", DAY, "| games to parse:", len(files))
print("mean replay size: %.1f MB" % (np.mean([os.path.getsize(p) for p in files]) / 1e6))

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

t0 = time.time(); rows = []
for k, p in enumerate(files, 1):
    r = parse_replay(p)
    if r: rows.extend(r)
    if k % 50 == 0:
        print(f"  {k}/{len(files)} replays, {len(rows)//2} decisive, {round(time.time()-t0)}s", flush=True)
sides = pd.DataFrame(rows)
games = len(sides) // 2
print(f"parsed {games} decisive games ({len(sides)} sides) in {round(time.time()-t0)}s")
print("distinct agents seen:", sides["agent"].nunique())
_steps = json.load(open(files[0], encoding="utf-8")).get("steps", [])
print("turns per game:", len(_steps)); del _steps

def wilson(w, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = w/n; d = 1 + z*z/n; c = (p + z*z/(2*n))/d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return p, c-h, c+h
MIN_G = 1 if games < 50 else max(6, len(sides)//200)
FEAT = ["plant", "sell", "hire", "harvest", "fert", "buy_animal", "buy_land"]
_gg = sides.groupby("agent"); _hr = []
for a, sub in _gg:
    n = len(sub)
    if n < MIN_G: continue
    p, lo, hi = wilson(int(sub.win.sum()), n); _hr.append((a, p, n))
H = pd.DataFrame(_hr, columns=["agent", "winrate", "games"]).sort_values("winrate").tail(12)
if len(H):
    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.42*len(H))))
    ax.hlines(range(len(H)), 50, H.winrate*100, color=MUT, lw=2)
    ax.plot(H.winrate*100, range(len(H)), "o", color=ACC, ms=9)
    ax.axvline(50, color=INK, lw=1, ls="--")
    ax.set_yticks(range(len(H)), [f"{a[:24]} (n={n})" for a, n in zip(H.agent, H.games)], fontsize=8)
    ax.set_xlabel("win rate (%)")
    ax.set_title(f"Kaggriculture ladder at a glance, {DAY}", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
else:
    print("too few games in this sample for the at-a-glance view (renders on the full daily dump)")

def wilson(w, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = w / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return p, c-h, c+h
g = sides.groupby("agent")
rec = []
for a, sub in g:
    w, n = int(sub["win"].sum()), len(sub)
    p, lo, hi = wilson(w, n)
    rec.append(dict(agent=a, games=n, winrate=p, lo=lo, hi=hi, avg_score=sub["score"].mean()))
T = pd.DataFrame(rec)
T = T[T["games"] >= max(8, T["games"].quantile(0.5))].sort_values("winrate")
fig, ax = plt.subplots(figsize=(9, max(4, 0.42*len(T))))
ax.errorbar(T["winrate"]*100, range(len(T)), xerr=[(T.winrate-T.lo)*100, (T.hi-T.winrate)*100],
            fmt="o", color=INK, ecolor=MUT, capsize=3)
ax.axvline(50, color=ACC, lw=1, ls="--")
ax.set_yticks(range(len(T)), [f"{a[:24]} (n={n})" for a, n in zip(T.agent, T.games)], fontsize=8)
ax.set_xlabel("win rate (%)  with 95% Wilson interval")
ax.set_title(f"Kaggriculture agent tier list, {DAY}", color=INK, loc="left", fontweight="bold")
plt.tight_layout(); plt.show()
print(T.sort_values("winrate", ascending=False).round(3).to_string(index=False))

feat = ["plant", "sell", "hire", "harvest", "fert", "buy_animal", "buy_land"]
win_mean = sides[sides.win == 1][feat].mean()
los_mean = sides[sides.win == 0][feat].mean()
fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(feat)); w = 0.4
ax.bar(x - w/2, win_mean.values, w, label="winning side", color=ACC)
ax.bar(x + w/2, los_mean.values, w, label="losing side", color=MUT)
ax.set_xticks(x, feat, rotation=20, ha="right")
ax.set_ylabel("actions per game (mean)")
ax.set_title("What winning farms do more of (and less of)", color=INK, loc="left", fontweight="bold")
ax.legend(frameon=False)
plt.tight_layout(); plt.show()
cmp = pd.DataFrame({"winning": win_mean, "losing": los_mean})
cmp["ratio"] = (cmp["winning"] / cmp["losing"].replace(0, np.nan)).round(2)
print(cmp.round(1).to_string())
print("\nmean final profit: winners", round(sides[sides.win==1].score.mean()),
      "| losers", round(sides[sides.win==0].score.mean()))

cw = sides[sides.win == 1]["top_crop"].value_counts()
cl = sides[sides.win == 0]["top_crop"].value_counts()
order = [c for c in (CROP_KEYS + ["none"]) if c in set(cw.index) | set(cl.index)]
wv = [cw.get(c, 0) for c in order]; lv = [cl.get(c, 0) for c in order]
fig, ax = plt.subplots(figsize=(8.5, 4))
x = np.arange(len(order)); w = 0.4
ax.bar(x - w/2, wv, w, label="primary crop of winners", color=ACC2)
ax.bar(x + w/2, lv, w, label="primary crop of losers", color=MUT)
ax.set_xticks(x, order, rotation=15); ax.set_ylabel("sides")
ax.set_title("Primary crop, winners vs losers", color=INK, loc="left", fontweight="bold")
ax.legend(frameon=False)
plt.tight_layout(); plt.show()
wr = {c: (cw.get(c,0) / (cw.get(c,0)+cl.get(c,0)) if (cw.get(c,0)+cl.get(c,0)) else 0) for c in order}
print("win rate when a crop is the primary crop:")
for c in order: print(f"  {c:12s} {wr[c]*100:.0f}%  (n={cw.get(c,0)+cl.get(c,0)})")

# The daily index manifest is the one with median_avg_score. A daily episode dump also ships a manifest.csv
# with a completely different per-episode schema, so pick by columns rather than by filename.
cands = [p for p in glob.glob("/kaggle/input/**/manifest.csv", recursive=True)]
man = None
for p in cands:
    try:
        t = pd.read_csv(p)
    except Exception:
        continue
    if not {"date", "median_avg_score", "top_avg_score"} <= set(t.columns):
        continue
    # Kaggle publishes a daily index for several simulation competitions and they share
    # the filename AND this exact header, so columns alone cannot separate them. The
    # slug column names the competition, and that can.
    slug = t["daily_dataset_slug"] if "daily_dataset_slug" in t.columns else None
    if slug is not None and not slug.astype(str).str.contains("kaggriculture").any():
        continue
    man = t.sort_values("date").reset_index(drop=True); mpath = p; break

if man is not None and len(man) >= 8:
    print("index manifest:", mpath, "| days:", len(man), "|", man["date"].iloc[0], "to", man["date"].iloc[-1])
    med = man["median_avg_score"].to_numpy(float)
    top = man["top_avg_score"].to_numpy(float)
    gap = top - med
    day = np.arange(len(man), dtype=float)
    peak = int(np.argmax(med))

    from scipy.stats import linregress
    gro = linregress(day[:peak + 1], med[:peak + 1])
    aft = linregress(day[peak:], med[peak:])
    lo, hi = aft.slope - 1.96 * aft.stderr, aft.slope + 1.96 * aft.stderr

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4))
    a1.plot(day, med, "o-", color=ACC, ms=4, lw=1.6, label="median agent score")
    a1.plot(day, top, "o-", color=ACC2, ms=3, lw=1.2, alpha=.75, label="top agent score")
    a1.axvline(peak, color=MUT, ls="--", lw=1)
    a1.annotate("peak " + str(man["date"].iloc[peak]), xy=(peak, med[peak]),
                xytext=(peak - 5.5, med[peak] * .82), color=INK, fontsize=9)
    xs = day[peak:]
    a1.plot(xs, aft.intercept + aft.slope * xs, color="black", lw=2, ls=":")
    a1.set_xticks(day[::3]); a1.set_xticklabels([man["date"].iloc[int(i)][5:] for i in day[::3]], fontsize=8)
    a1.set_ylabel("season profit"); a1.legend(frameon=False, fontsize=9)
    a1.set_title("Median climbed, peaked, and turned down", color=INK, loc="left", fontweight="bold")

    a2.plot(day, gap, "o-", color=GD, ms=4, lw=1.6)
    a2.set_xticks(day[::3]); a2.set_xticklabels([man["date"].iloc[int(i)][5:] for i in day[::3]], fontsize=8)
    a2.set_ylabel("top minus median")
    a2.set_title("The field converged on the leader", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()

    print("growth phase : days", peak + 1, "| slope", round(gro.slope, 1),
          "points per day | p", format(gro.pvalue, ".2e"), "| R2", round(gro.rvalue ** 2, 3))
    print("after peak   : days", len(day) - peak, "| slope", round(aft.slope, 2),
          "points per day | p", round(aft.pvalue, 4), "| R2", round(aft.rvalue ** 2, 3))
    print("95 percent interval for the recent slope: [", round(lo, 2), ",", round(hi, 2), "]")
    print("zero inside that interval:", bool(lo < 0 < hi), " (False means the decline is real)")
    print("median peaked", round(med[peak], 1), "on", man["date"].iloc[peak],
          "| latest", round(med[-1], 1), "| change", round(med[-1] - med[peak], 1))
    print("top minus median compressed", round(gap[0], 1), "->", round(gap[-1], 1),
          "= narrower by a factor of", round(gap[0] / gap[-1], 1))
    print("games per day", int(man["episode_count"].iloc[0]), "->", int(man["episode_count"].iloc[-1]))
    print("total growth over the whole index:", round(med[0], 1), "->", round(med[-1], 1),
          "= x" + str(round(med[-1] / med[0], 2)))
else:
    print("attach kaggle/kaggriculture-episodes-index to see whether the ladder is still climbing")

prof_all = sides.groupby("agent")[FEAT]
counts = sides.groupby("agent").size()
keep = counts[counts >= MIN_G].index
prof = prof_all.mean().loc[keep]
wr_by = sides.groupby("agent")["win"].mean().loc[keep]
prof = prof.loc[wr_by.sort_values(ascending=False).index].head(12)
if len(prof) >= 2:
    pn = (prof - prof.min()) / (prof.max() - prof.min() + 1e-9)
    fig, ax = plt.subplots(figsize=(9, max(4, 0.5*len(prof))))
    im = ax.imshow(pn.values, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(FEAT)), FEAT, rotation=25, ha="right")
    ax.set_yticks(range(len(prof)), [a[:22] for a in prof.index], fontsize=8)
    for i in range(len(prof)):
        for j in range(len(FEAT)):
            ax.text(j, i, f"{prof.values[i,j]:.0f}", ha="center", va="center", color="w", fontsize=6)
    fig.colorbar(im, ax=ax, label="normalized per column")
    ax.set_title(f"Action profile of the top agents by win rate, {DAY}", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
else:
    print("too few qualifying agents for the fingerprint (renders on the full daily dump)")

ws = sides[sides.win == 1].score; los = sides[sides.win == 0].score
if len(ws) and len(los):
    bins = np.linspace(min(ws.min(), los.min()), max(ws.max(), los.max()), 40)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.hist(los, bins=bins, alpha=0.6, label="losing side", color=MUT)
    ax.hist(ws, bins=bins, alpha=0.6, label="winning side", color=ACC)
    ax.axvline(ws.median(), color=ACC, ls="--"); ax.axvline(los.median(), color=MUT, ls="--")
    ax.set_xlabel("final season profit"); ax.set_ylabel("sides"); ax.legend(frameon=False)
    ax.set_title("Final profit, winners vs losers", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
    print("median profit  winners", round(ws.median()), " losers", round(los.median()),
          " gap", round(ws.median()-los.median()))

C = sides[FEAT + ["score", "win"]].corr()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.2))
im = a1.imshow(C.values, cmap="coolwarm", vmin=-1, vmax=1)
a1.set_xticks(range(len(C)), C.columns, rotation=45, ha="right", fontsize=8)
a1.set_yticks(range(len(C)), C.columns, fontsize=8)
for i in range(len(C)):
    for j in range(len(C)):
        a1.text(j, i, f"{C.values[i,j]:.2f}", ha="center", va="center", fontsize=6,
                color="w" if abs(C.values[i,j]) > 0.5 else "k")
fig.colorbar(im, ax=a1, label="correlation")
a1.set_title("Action, profit, win correlation", color=INK, loc="left", fontweight="bold")
a2.scatter(sides.sell, sides.score, c=sides.win, cmap="coolwarm", s=12, alpha=0.6, edgecolor="none")
a2.set_xlabel("sell actions"); a2.set_ylabel("final profit")
a2.set_title("Selling vs profit (color = win)", color=INK, loc="left", fontweight="bold")
plt.tight_layout(); plt.show()

keep = counts[counts >= MIN_G].index
wr3 = sides[sides.agent.isin(keep)].groupby("agent")["win"].mean().sort_values(ascending=False)
top3 = wr3.head(3).index.tolist()
prof2 = sides.groupby("agent")[FEAT].mean()
mx = prof2.max() + 1e-9
if len(top3) >= 1:
    ang = np.linspace(0, 2*np.pi, len(FEAT), endpoint=False).tolist(); ang += ang[:1]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    cols = [ACC, ACC2, GD]
    for k, a in enumerate(top3):
        v = (prof2.loc[a] / mx).values.tolist(); v += v[:1]
        ax.plot(ang, v, color=cols[k % 3], label=a[:20]); ax.fill(ang, v, color=cols[k % 3], alpha=0.12)
    ax.set_xticks(ang[:-1], FEAT, fontsize=8); ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.1), frameon=False, fontsize=8)
    ax.set_title(f"Top agents action fingerprint, {DAY}", color=INK)
    plt.tight_layout(); plt.show()
    print("top 3 by win rate:", top3)