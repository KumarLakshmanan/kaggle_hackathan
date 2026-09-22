import glob, time
t0 = time.time()

def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    assert hits, f"{pattern} not found under /kaggle/input -- is kaggle/meta-kaggle mounted?"
    return hits[0]

KERNELS_PATH = find("Kernels.csv")
KVCS_PATH = find("KernelVersionCompetitionSources.csv")
COMPS_PATH = find("Competitions.csv")
print(f"reading {KERNELS_PATH}\n reading {KVCS_PATH}\n reading {COMPS_PATH}")

import pandas as pd
import numpy as np

kernels = pd.read_csv(KERNELS_PATH, usecols=["Id", "CurrentKernelVersionId", "TotalViews", "TotalVotes"])
kvcs = pd.read_csv(KVCS_PATH, usecols=["KernelVersionId", "SourceCompetitionId"])
comps = pd.read_csv(COMPS_PATH, usecols=["Id", "Slug", "Title", "TotalTeams"])

merged = kernels.merge(kvcs, left_on="CurrentKernelVersionId", right_on="KernelVersionId", how="inner")
merged = merged.merge(comps, left_on="SourceCompetitionId", right_on="Id", how="left", suffixes=("", "_comp"))
print(f"{len(merged):,} competition-attributed kernels, {merged['SourceCompetitionId'].nunique():,} "
      f"distinct competitions [{time.time()-t0:.0f}s]")

MY_VENUES = {
    "playground-series-s6e8": "S6E8",
    "kaggriculture": "Kaggriculture",
    "biohub-cell-tracking-during-development": "Biohub",
    "rsna-knee-abnormality-detection": "RSNA",
    "pokemon-tcg-ai-battle-challenge-strategy": "Pokemon",
}

def venue_votes(slug):
    return merged.loc[merged["Slug"] == slug, "TotalVotes"].dropna().sort_values(ascending=False).to_numpy()

rows = []
for slug, label in MY_VENUES.items():
    v = venue_votes(slug)
    if len(v) == 0:
        continue
    rows.append({
        "venue": label, "n_notebooks": len(v),
        "top20_median": np.median(v[:20]) if len(v) >= 20 else np.median(v),
        "top20_pct_of_venue": round(100 * 20 / len(v), 1),
    })
df = pd.DataFrame(rows).sort_values("top20_median", ascending=False)
print(df.to_string(index=False))

rows2 = []
for slug, label in MY_VENUES.items():
    v = venue_votes(slug)
    if len(v) == 0:
        continue
    n = len(v)
    k5 = max(1, round(n * 0.05))
    k10 = max(1, round(n * 0.10))
    rows2.append({
        "venue": label, "n_notebooks": n,
        "top5pct_median": round(float(np.median(v[:k5])), 1),
        "top10pct_median": round(float(np.median(v[:k10])), 1),
        "mean": round(float(v.mean()), 2),
        "p75": round(float(np.percentile(v, 75)), 1),
        "p90": round(float(np.percentile(v, 90)), 1),
    })
df2 = pd.DataFrame(rows2)
print(df2.sort_values("top5pct_median", ascending=False).to_string(index=False))
print()
print("Rank by top-5%-median:", " > ".join(df2.sort_values("top5pct_median", ascending=False)["venue"]))
print("Rank by mean:         ", " > ".join(df2.sort_values("mean", ascending=False)["venue"]))

def trimmed_means(slug):
    v = venue_votes(slug)
    n = len(v)
    k1pct = max(1, round(n * 0.01))
    return {
        "mean_full": round(v.mean(), 2),
        "mean_drop_top1": round(v[1:].mean(), 2) if n > 1 else None,
        "mean_drop_top5": round(v[5:].mean(), 2) if n > 5 else None,
        "mean_drop_top1pct": round(v[k1pct:].mean(), 2) if n > k1pct else None,
        "max_share_of_total_votes_pct": round(100 * v[0] / v.sum(), 1) if v.sum() else None,
    }

for slug, label in [("kaggriculture", "Kaggriculture"), ("biohub-cell-tracking-during-development", "Biohub")]:
    t = trimmed_means(slug)
    print(f"{label:15s} {t}")

VENUE_A = "kaggriculture"       # <-- replace with any competition slug
VENUE_B = "biohub-cell-tracking-during-development"  # <-- replace with any competition slug

for slug in (VENUE_A, VENUE_B):
    v = venue_votes(slug)
    if len(v) == 0:
        print(f"{slug}: no competition-attributed kernels found in this snapshot")
        continue
    n = len(v)
    k5 = max(1, round(n * 0.05))
    print(f"{slug}: n={n}  mean={v.mean():.2f}  top-5%-median={np.median(v[:k5]):.1f}  "
          f"top-20-median={np.median(v[:20]) if n>=20 else np.median(v):.1f} (={100*min(20,n)/n:.1f}% of venue)")