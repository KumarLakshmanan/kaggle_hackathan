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
REQUIRED_COMPS = ["Id", "Slug", "TotalTeams"]

teams = pd.read_csv(TEAMS_PATH, usecols=REQUIRED_TEAMS)
comps = pd.read_csv(COMPS_PATH, usecols=REQUIRED_COMPS)
n_comps_in_teams = teams["CompetitionId"].nunique()
print(f"{len(teams):,} team rows across {n_comps_in_teams:,} competitions [{time.time()-t0:.0f}s]")

resolved = teams.dropna(subset=["PublicLeaderboardRank", "PrivateLeaderboardRank"])
n_comps_resolved = resolved["CompetitionId"].nunique()
print(f"{len(resolved):,} team rows have both ranks populated, across {n_comps_resolved:,} competitions")

def survival_rate(g):
    pub_top10 = set(g.loc[g["PublicLeaderboardRank"] <= 10].index)
    if len(pub_top10) < 10:
        return None
    priv_top10 = set(g.loc[g["PrivateLeaderboardRank"] <= 10].index)
    return len(pub_top10 & priv_top10) / len(pub_top10)

survival = resolved.groupby("CompetitionId", sort=False).apply(survival_rate, include_groups=False)
survival = survival.dropna()
print(f"{len(survival):,} competitions have a full public top-10 AND resolved private ranks "
      f"[{time.time()-t0:.0f}s]")

comps_indexed = comps.set_index("Id")
sizes = comps_indexed.loc[survival.index, "TotalTeams"]

BUCKETS = [(0, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, np.inf)]
LABELS = ["<200", "200-500", "500-1000", "1000-2000", "2000-5000", "5000+"]

rows = []
for (lo, hi), label in zip(BUCKETS, LABELS):
    mask = (sizes >= lo) & (sizes < hi)
    vals = survival.loc[mask.index[mask]]
    rows.append({
        "bucket": label, "n_competitions": len(vals),
        "mean_survival": round(float(vals.mean()), 3) if len(vals) else None,
        "median_survival": round(float(vals.median()), 3) if len(vals) else None,
    })

bucket_df = pd.DataFrame(rows)
print(bucket_df.to_string(index=False))
bucket_df.to_csv("leaderboard_shakeup_by_size.csv", index=False)

MY_COMP_SLUG = "kaggriculture"   # <-- swap for any competition slug on Kaggle

slug_to_id = comps.set_index("Slug")["Id"].to_dict()
comp_id = slug_to_id.get(MY_COMP_SLUG)
if comp_id is None:
    print(f"{MY_COMP_SLUG}: not found in this Meta Kaggle snapshot")
else:
    live_row = comps_indexed.loc[comp_id] if comp_id in comps_indexed.index else None
    total_teams = int(live_row["TotalTeams"]) if live_row is not None else None
    bucket = None
    if total_teams is not None:
        for (lo, hi), lbl in zip(BUCKETS, LABELS):
            if lo <= total_teams < hi:
                bucket = lbl
                break
    own_survival = survival.get(comp_id)
    print(f"{MY_COMP_SLUG}: {total_teams:,} teams -> size bucket [{bucket}]"
          if total_teams is not None else f"{MY_COMP_SLUG}: team count unavailable")
    expected = bucket_df.loc[bucket_df["bucket"] == bucket, "mean_survival"]
    if len(expected):
        print(f"historical base rate for this bucket: {float(expected.iloc[0])*100:.1f}% of the "
              f"public top 10 typically survives to the private top 10")
    print(f"this competition's own resolved history in this snapshot: "
          f"{own_survival if own_survival is not None else 'not resolved yet, or not previously run'}")