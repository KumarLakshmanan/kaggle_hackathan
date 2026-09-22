import glob, time
t0 = time.time()

def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    assert hits, f"{pattern} not found under /kaggle/input -- is kaggle/meta-kaggle mounted?"
    return hits[0]

TEAMS_PATH = find("Teams.csv")
COMPS_PATH = find("Competitions.csv")
print(f"reading {TEAMS_PATH}\n reading {COMPS_PATH}")

import pandas as pd
import numpy as np

REQUIRED_TEAMS = ["CompetitionId", "PublicLeaderboardRank", "PrivateLeaderboardRank"]
REQUIRED_COMPS = ["Id", "Slug", "TotalTeams", "LeaderboardPercentage"]

teams = pd.read_csv(TEAMS_PATH, usecols=REQUIRED_TEAMS)
comps = pd.read_csv(COMPS_PATH, usecols=REQUIRED_COMPS)
print(f"{len(teams):,} team rows, {len(comps):,} competitions [{time.time()-t0:.0f}s]")

n_null_pct = comps["LeaderboardPercentage"].isna().sum()
median_pct = comps["LeaderboardPercentage"].median()
print(f"LeaderboardPercentage populated for {100*(1-n_null_pct/len(comps)):.1f}% of competitions "
      f"in this snapshot (median {median_pct:.0f})")

resolved = teams.dropna(subset=["PublicLeaderboardRank", "PrivateLeaderboardRank"])

def survival_rate(g):
    pub_top10 = set(g.loc[g["PublicLeaderboardRank"] <= 10].index)
    if len(pub_top10) < 10:
        return None
    priv_top10 = set(g.loc[g["PrivateLeaderboardRank"] <= 10].index)
    return len(pub_top10 & priv_top10) / len(pub_top10)

survival = resolved.groupby("CompetitionId", sort=False).apply(survival_rate, include_groups=False)
survival = survival.dropna()
print(f"{len(survival):,} competitions scoreable [{time.time()-t0:.0f}s]")

comps_indexed = comps.set_index("Id")
scoreable = comps_indexed.loc[survival.index, ["TotalTeams", "LeaderboardPercentage"]].copy()
scoreable["survival"] = survival
scoreable = scoreable.dropna(subset=["LeaderboardPercentage"])
scoreable["split_group"] = np.where(scoreable["LeaderboardPercentage"] <= 30, "<=30% split", ">30% split")

BUCKETS = [(0, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, np.inf)]
LABELS = ["<200", "200-500", "500-1000", "1000-2000", "2000-5000", "5000+"]
scoreable["team_bucket"] = pd.cut(scoreable["TotalTeams"], bins=[b[0] for b in BUCKETS] + [np.inf],
                                   labels=LABELS, right=False)
print(f"{len(scoreable):,} competitions have both a team-count bucket and a split percentage")

rows = []
for label in LABELS:
    sub = scoreable[scoreable["team_bucket"] == label]
    small = sub.loc[sub["split_group"] == "<=30% split", "survival"]
    large = sub.loc[sub["split_group"] == ">30% split", "survival"]
    rows.append({
        "team_bucket": label, "n_small_split": len(small), "n_large_split": len(large),
        "mean_survival_small_split": round(float(small.mean()), 3) if len(small) else None,
        "mean_survival_large_split": round(float(large.mean()), 3) if len(large) else None,
    })
split_df = pd.DataFrame(rows)
print(split_df.to_string(index=False))
split_df.to_csv("leaderboard_shakeup_by_split_size.csv", index=False)

MY_COMP_SLUG = "kaggriculture"   # <-- swap for any competition slug on Kaggle

slug_indexed = comps.set_index("Slug")
if MY_COMP_SLUG not in slug_indexed.index:
    print(f"{MY_COMP_SLUG}: not found in this Meta Kaggle snapshot")
else:
    row = slug_indexed.loc[MY_COMP_SLUG]
    total_teams = int(row["TotalTeams"])
    pct = row["LeaderboardPercentage"]
    bucket = next((lbl for (lo, hi), lbl in zip(BUCKETS, LABELS) if lo <= total_teams < hi), "5000+")
    split_group = "<=30% split" if (pd.notna(pct) and pct <= 30) else (
        ">30% split" if pd.notna(pct) else "unknown split")
    pct_label = pct if pd.notna(pct) else "not published"
    print(f"{MY_COMP_SLUG}: {total_teams:,} teams -> bucket [{bucket}], "
          f"LeaderboardPercentage = {pct_label} -> {split_group}")

    match = split_df.loc[split_df["team_bucket"] == bucket]
    if len(match):
        m = match.iloc[0]
        col = "mean_survival_small_split" if split_group == "<=30% split" else "mean_survival_large_split"
        base_rate = m[col] if col in m and pd.notna(m[col]) else None
        if base_rate is not None:
            print(f"historical base rate for this exact bucket x split combination: "
                  f"{base_rate*100:.1f}% of the public top 10 typically survives")
        if bucket in ("2000-5000", "5000+") and split_group == "<=30% split":
            print("!! both risk factors present: large field AND a small public split -- "
                  "this is the worst-measured combination on this page")