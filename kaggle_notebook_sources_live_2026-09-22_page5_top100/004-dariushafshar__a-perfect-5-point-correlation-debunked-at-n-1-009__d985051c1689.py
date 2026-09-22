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

kernels = pd.read_csv(KERNELS_PATH, usecols=["Id", "CurrentKernelVersionId", "TotalVotes"])
kvcs = pd.read_csv(KVCS_PATH, usecols=["KernelVersionId", "SourceCompetitionId"])
comps = pd.read_csv(
    COMPS_PATH,
    usecols=["Id", "Slug", "TotalTeams", "EnabledDate", "DeadlineDate"],
    parse_dates=["EnabledDate", "DeadlineDate"],
)

# A kernel is attributed to a competition through its CURRENT version's declared source -- the
# same thing the live Code tab shows today. Same join used by this series' population-median
# notebook (search "the real median kaggle notebook" if you haven't forked that one).
merged = kernels.merge(kvcs, left_on="CurrentKernelVersionId", right_on="KernelVersionId", how="inner")
print(f"{len(merged):,} competition-attributed kernels, {merged['SourceCompetitionId'].nunique():,} "
      f"distinct competitions [{time.time()-t0:.0f}s]")

agg = merged.groupby("SourceCompetitionId").agg(
    n_kernels=("Id", "count"),
    median_votes=("TotalVotes", "median"),
).reset_index()
full = agg.merge(comps, left_on="SourceCompetitionId", right_on="Id", how="left")

SNAPSHOT_DATE = pd.Timestamp("2026-08-21")  # the date this Meta Kaggle snapshot was generated
MIN_KERNELS = 10

sub = full[(full["n_kernels"] >= MIN_KERNELS) & (full["TotalTeams"] > 0)].copy()
closed = sub[
    sub["DeadlineDate"].notna() & (sub["DeadlineDate"] < SNAPSHOT_DATE) & sub["EnabledDate"].notna()
].copy()
closed["duration_days"] = (closed["DeadlineDate"] - closed["EnabledDate"]).dt.total_seconds() / 86400
closed = closed[closed["duration_days"] > 0]
closed["growth_rate"] = closed["TotalTeams"] / closed["duration_days"]

print(f"{len(sub):,} competitions clear the >= {MIN_KERNELS}-kernel bar")
print(f"{len(closed):,} of those are closed with a valid duration -- this is the fit population")

def spearman(x, y):
    xr, yr = x.rank(), y.rank()
    n = len(x)
    rho = ((xr - xr.mean()) * (yr - yr.mean())).sum() / (
        ((xr - xr.mean()) ** 2).sum() ** 0.5 * ((yr - yr.mean()) ** 2).sum() ** 0.5
    )
    t = rho * (n - 2) ** 0.5 / max(1e-12, (1 - rho ** 2)) ** 0.5
    return rho, t, n

rho, t, n = spearman(closed["growth_rate"], closed["median_votes"])
print(f"n={n} competitions")
print(f"Spearman rho = {rho:.4f}, t = {t:.2f} (df={n-2})")
print(f"my original 5-competition read: r=-0.982 (n=4, excl. one outlier) / r=-0.535 (n=5)")

import numpy as np

logsize = np.log(closed["TotalTeams"])
rho_size, t_size, _ = spearman(logsize, closed["median_votes"])
print(f"context -- log(TotalTeams) alone vs median votes: rho={rho_size:.4f}, t={t_size:.2f}")

# Rank-based partial correlation: residualize both growth_rate and median_votes against
# log(TotalTeams), then correlate what's left.
def resid_rank(y_rank, x_rank):
    X = np.vstack([np.ones(len(x_rank)), x_rank]).T
    beta, *_ = np.linalg.lstsq(X, y_rank, rcond=None)
    return y_rank - X @ beta

gr_rank = closed["growth_rate"].rank().to_numpy()
mv_rank = closed["median_votes"].rank().to_numpy()
size_rank = logsize.rank().to_numpy()

gr_resid = resid_rank(gr_rank, size_rank)
mv_resid = resid_rank(mv_rank, size_rank)
partial_rho = np.corrcoef(gr_resid, mv_resid)[0, 1]
n = len(closed)
partial_t = partial_rho * (n - 3) ** 0.5 / max(1e-12, (1 - partial_rho ** 2)) ** 0.5
print(f"partial (controlling for log(TotalTeams)): rho={partial_rho:.4f}, t={partial_t:.2f} (df={n-3})")

# Not driven by a handful of degenerate short-duration competitions.
for min_days, label in [(0, "no floor"), (14, ">=14 days"), (30, ">=30 days")]:
    r = closed[closed["duration_days"] >= min_days]
    rho_r, t_r, n_r = spearman(r["growth_rate"], r["median_votes"])
    print(f"duration {label:>10}: n={n_r:>5}, rho={rho_r:+.4f}, t={t_r:+.2f}")

print()
# Not an artifact of the >=10-kernel cutoff.
for mk in [5, 10, 20, 30]:
    s = full[(full["n_kernels"] >= mk) & (full["TotalTeams"] > 0)].copy()
    c = s[s["DeadlineDate"].notna() & (s["DeadlineDate"] < SNAPSHOT_DATE) & s["EnabledDate"].notna()].copy()
    c["duration_days"] = (c["DeadlineDate"] - c["EnabledDate"]).dt.total_seconds() / 86400
    c = c[c["duration_days"] > 0]
    c["growth_rate"] = c["TotalTeams"] / c["duration_days"]
    rho_m, t_m, n_m = spearman(c["growth_rate"], c["median_votes"])
    print(f"MIN_KERNELS={mk:>3}: n={n_m:>5}, rho={rho_m:+.4f}, t={t_m:+.2f}")

def test_candidate(series, name):
    """Drop in any competition-level Series (indexed like `closed`, e.g. closed["SomeColumn"])
    and get its Spearman correlation against median votes, at real n -- the same check this
    notebook just ran on growth rate."""
    valid = closed.loc[series.notna()]
    rho_c, t_c, n_c = spearman(series.loc[valid.index], valid["median_votes"])
    print(f"{name}: n={n_c}, rho={rho_c:+.4f}, t={t_c:+.2f}")
    return rho_c, t_c, n_c

# Example: does a competition's max team size predict votes?
test_candidate(closed["TotalTeams"], "TotalTeams (raw, no size control)")