%pip install -q "kaggle-environments==1.32.4"

import glob, math, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (8, 4.2), "axes.grid": True, "grid.alpha": .25,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
})

from kaggle_environments.envs.kaggriculture import kaggriculture as K
SRC_LINES = open(K.__file__, encoding="utf-8").read().split("\n")

def show_block(anchor, after=0, before=0, title=None):
    "Print lines around the first line containing `anchor`. Line numbers move\n"
    "between releases, so we look code up by text rather than by range."
    hits = [i for i, l in enumerate(SRC_LINES) if anchor in l]
    if not hits:
        print(f"!! anchor not found in this version: {anchor!r}")
        return
    i = hits[0]
    lo, hi = max(0, i - before), min(len(SRC_LINES), i + after + 1)
    print(f"--- {title or anchor}  [lines {lo+1}-{hi}] ---")
    for j in range(lo, hi):
        print(f"{j + 1:4d} | {SRC_LINES[j].rstrip()}")

show_block('s.reward = float', before=4, after=1,
           title="the reward is the bank balance, nothing else")

def find_csv(name):
    for pattern in (f"/kaggle/input/**/{name}", f"../input/**/{name}",
                    f"tmp/dsnew/{name}", name):
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return hits[0]
    raise SystemExit(f"{name} not found — attach georgymamarin/kaggriculture-episodes")

episodes = pd.read_csv(find_csv("episodes.csv"), low_memory=False)
feats    = pd.read_csv(find_csv("episode_features.csv"), low_memory=False)

# The dataset mixes ladder games with self-play validation runs; its README says to
# drop the latter for anything about strength.
episodes = episodes[episodes["type"] == "EPISODE_TYPE_PUBLIC"]

long = []
for seat in (0, 1):
    other = 1 - seat
    part = episodes[["episode_id", f"sub_{seat}", f"bank_{seat}",
                     f"rating_{seat}", f"bank_{other}", f"rating_{other}"]].copy()
    part.columns = ["episode_id", "sub", "money", "rating",
                    "opp_money", "opp_rating"]
    part["seat"] = seat
    long.append(part)
long = pd.concat(long)
df = long.merge(feats, on=["episode_id", "seat"], how="inner").dropna(
    subset=["rating", "money", "opp_money"])
df["margin"] = df.money - df.opp_money
df["won"] = (df.money > df.opp_money).astype(float)
print(f"{len(df):,} ladder agent-episodes | {df['sub'].nunique():,} submissions")

EDGES = [0, 750, 1250, 1750, 2250, 2750, 10 ** 9]
LABELS = ["~500", "~1000", "~1500", "~2000", "~2500", "3000+"]
df["band"] = pd.cut(df.rating, bins=EDGES, labels=LABELS, right=False)
bands = df.groupby("band", observed=True)["money"].agg(
    n="size", median="median").astype(int)
bands["gain over previous"] = bands["median"].diff().fillna(0).astype(int)
bands

fig, ax = plt.subplots()
ax.plot(range(len(bands)), bands["median"], "o-", lw=2, color="#2b6cb0")
ax.set_xticks(range(len(bands))); ax.set_xticklabels(bands.index)
ax.set_xlabel("rating band"); ax.set_ylabel("median final money")
ax.yaxis.set_major_formatter(lambda v, p: f"{v:,.0f}")
ax.set_title("Money buys the first thousand rating points, then stops")
ax.annotate("everything after here is flat", xy=(1.1, bands["median"].iloc[1]),
            xytext=(2.3, bands["median"].iloc[1] * .72), fontsize=10,
            arrowprops=dict(arrowstyle="->", color="grey"))
plt.tight_layout(); plt.show()

FIELDS = ["money", "opp_money", "margin", "won", "peak_crew", "total_hires",
          "first_land_day", "elbow_day", "tiles_planted",
          "plants_wheat", "plants_melon", "plants_strawberry"]

def by_submission(sub_df, min_games=8):
    "One row per submission: mean rating, mean features, and money dispersion."
    g = sub_df.groupby("sub")
    out = g[FIELDS].mean()
    out["rating"] = g["rating"].mean()
    out["games"] = g.size()
    out["money_sd"] = g["money"].std()
    out["money_cv"] = out.money_sd / out.money
    return out[out.games >= min_games]

def ranked_corr(agg, target="rating"):
    rows = []
    for c in agg.columns:
        if c in (target, "games"):
            continue
        s = agg[[target, c]].dropna()
        if len(s) < 10:
            continue
        rows.append({"field": c, "r": round(s[target].corr(s[c]), 3),
                     "submissions": len(s)})
    return pd.DataFrame(rows).reindex(
        pd.DataFrame(rows).r.abs().sort_values(ascending=False).index
    ).set_index("field")

high = by_submission(df[df.rating >= 750])
print(f"{len(high)} submissions with 8+ games above the ~1000 band")
ranked_corr(high)

low = by_submission(df[(df.rating >= 500) & (df.rating < 1000)])
print(f"{len(low)} submissions with 8+ games in the 500-1000 band")
ranked_corr(low).head(6)

def zs(s):
    return (s - s.mean()) / s.std(ddof=0)

def fit(agg, cols, target="rating"):
    d = agg[[target] + cols].dropna()
    X = np.column_stack([np.ones(len(d))] + [zs(d[c]).values for c in cols])
    y = zs(d[target]).values
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    r2 = 1 - resid @ resid / (y @ y)
    return {"model": " + ".join(cols), "R2": round(r2, 3),
            **{c: round(b, 3) for c, b in zip(cols, beta[1:])}}

specs = [["money"], ["peak_crew"], ["money", "peak_crew"],
         ["money", "peak_crew", "plants_strawberry"],
         ["money", "peak_crew", "plants_strawberry", "opp_money"]]
pd.DataFrame([fit(high, s) for s in specs]).set_index("model")

high2 = by_submission(df[df.rating >= 750].assign(
    opp_rating=df[df.rating >= 750].opp_rating))
high2["opp_rating"] = df[df.rating >= 750].groupby("sub")["opp_rating"].mean()
pd.DataFrame([fit(high2, ["opp_rating"]),
              fit(high2, ["opp_rating", "money"]),
              fit(high2, ["opp_rating", "peak_crew"])]).set_index("model")

print(f"corr(own rating, opponent rating) = "
      f"{high2[['rating','opp_rating']].dropna().corr().iloc[0,1]:.4f}")
print(f"mean win rate among these submissions = {high.won.mean():.3f}")
print(f"corr(own rating, win rate)            = "
      f"{high[['rating','won']].corr().iloc[0,1]:+.3f}")