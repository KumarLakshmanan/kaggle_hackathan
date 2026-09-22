%matplotlib inline
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def _find_data():
    # On Kaggle the dataset mounts under /kaggle/input/<slug>; find it by content
    # rather than by assuming the directory name.
    kin = Path('/kaggle/input')
    if kin.exists():
        hits = sorted(kin.rglob('board_history.csv'))
        if hits:
            return hits[0].parent
        raise FileNotFoundError(
            'Dataset not attached. Click "Add Input" and attach '
            'kaggle.com/datasets/dariushafshar/kaggriculture-ladder-telemetry')
    return Path('/Users/dariush/Desktop/College Counselor Vault/Personal Projects/'
                'kaggriculture/datasets/kaggriculture-ladder-telemetry')


DATA = _find_data()
hist = pd.read_csv(DATA / 'board_history.csv')
hist['score'] = pd.to_numeric(hist['score'], errors='coerce')

# One descending score list per archived board. Descending because every question here
# is "who is ahead of this number", and rank 1 is the top.
boards = {d: sorted(g['score'].dropna().tolist(), reverse=True)
          for d, g in hist.groupby('snapshot_date')}
dates = sorted(boards)


def score_at_rank(k, desc):
    """Score held by the team standing k-th (1-based) on a descending board."""
    return desc[min(len(desc) - 1, max(0, k - 1))]


def rank_at_percentile(pct, n):
    """The rank that the pct cutoff sits on in a field of n teams."""
    return max(1, int(round(pct * n)))


def score_at_percentile(pct, desc):
    return score_at_rank(rank_at_percentile(pct, len(desc)), desc)


def standing_of(score, desc):
    """Rank a team holding exactly `score` would hold on this board.

    Ties are resolved against the newcomer -- everyone already at or above the score is
    counted as ahead -- because Kaggle breaks equal scores in favour of the earlier
    submission. This costs at most one rank and never flatters the result.
    """
    return sum(1 for s in desc if s >= score) + 1


span = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days
print(f"rows         {len(hist)} in board_history.csv")
print(f"boards       {len(dates)}: {', '.join(dates)}")
print(f"span         {span} days, {dates[0]} -> {dates[-1]}")
print(f"field        {len(boards[dates[0]])} -> {len(boards[dates[-1]])} teams "
      f"({100 * (len(boards[dates[-1]]) / len(boards[dates[0]]) - 1):+.0f}%)")
print(f"team_ids     {hist['team_id'].nunique()} distinct across all six boards")
print(f"missing      {int(hist['score'].isna().sum())} rows with no score")

FIXED = 2000.0

rows = []
for d in dates:
    b = boards[d]
    st = standing_of(FIXED, b)
    rows.append({'snapshot': d, 'teams': len(b),
                 'top1%': round(score_at_percentile(0.01, b), 1),
                 'top5%': round(score_at_percentile(0.05, b), 1),
                 'top10%': round(score_at_percentile(0.10, b), 1),
                 'median': round(score_at_percentile(0.50, b), 1),
                 f'rank@{FIXED:.0f}': st,
                 'standing': f"top {100 * st / len(b):.1f}%"})
table = pd.DataFrame(rows)
print(table.to_string(index=False))

first, last = boards[dates[0]], boards[dates[-1]]
s0, s1 = standing_of(FIXED, first), standing_of(FIXED, last)
p0, p1 = 100 * s0 / len(first), 100 * s1 / len(last)
print(f"\na flat {FIXED:.0f}: rank {s0}/{len(first)} (top {p0:.1f}%) on {dates[0]}"
      f"  ->  rank {s1}/{len(last)} (top {p1:.1f}%) on {dates[-1]}"
      f"   = {p0 - p1:+.1f} percentage points of standing in {span} days")

print(f"\n{'window':<26}{'days':>6}{'top5%/day':>12}{'top10%/day':>12}{'teams+':>9}")
for a, b in zip(dates, dates[1:]):
    days = (pd.Timestamp(b) - pd.Timestamp(a)).days
    d5 = (score_at_percentile(0.05, boards[b]) - score_at_percentile(0.05, boards[a])) / days
    d10 = (score_at_percentile(0.10, boards[b]) - score_at_percentile(0.10, boards[a])) / days
    print(f"{a + ' -> ' + b:<26}{days:>6}{d5:>12.1f}{d10:>12.1f}"
          f"{len(boards[b]) - len(boards[a]):>9}")
print("\nThe windows are 11, 1, 3, 3 and 1 days wide. The two one-day windows divide a small")
print("score change by a small number of days, so their rates are the noisiest cells in the")
print("table -- read the 11-day and 3-day rows first.")
print("\nConvention: a cutoff here is the score held by the team at rank round(pct x teams).")
print("Neighbouring conventions (floor, or a linear-interpolated quantile) move these numbers")
print("by well under a point and change nothing below; the ranks are the load-bearing part.")

x = pd.to_datetime(dates)
cut5 = [score_at_percentile(0.05, boards[d]) for d in dates]
cut10 = [score_at_percentile(0.10, boards[d]) for d in dates]
med = [score_at_percentile(0.50, boards[d]) for d in dates]

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(x, cut5, marker='o', color='C0', label='top 5% cutoff (left)')
ax.plot(x, cut10, marker='o', color='C1', label='top 10% cutoff (left)')
ax.set_ylabel('cutoff score — left axis')
ax.set_xlabel('snapshot date')
ax.grid(True)

ax2 = ax.twinx()
ax2.plot(x, med, marker='s', color='C2', label='median team (right)')
ax2.set_ylabel('median score — right axis')

ax.set_title('Cutoffs falling while the middle rises — 6 archived boards\n'
             '(separate axes, each zoomed to its own data; markers are the real snapshots)')
lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [ln.get_label() for ln in lines], loc='center left', fontsize=8)
fig.autofmt_xdate()
plt.show()

print("Each axis is zoomed to its own data, which makes the median's rise look comparable")
print("to the cutoffs' fall. It is not, and here are the real sizes:")
print(f"  top 5%   {cut5[0]:.1f} -> {cut5[-1]:.1f}  ({cut5[-1] - cut5[0]:+.1f})")
print(f"  top 10%  {cut10[0]:.1f} -> {cut10[-1]:.1f}  ({cut10[-1] - cut10[0]:+.1f})")
print(f"  median   {med[0]:.1f} -> {med[-1]:.1f}  ({med[-1] - med[0]:+.1f})")
print(f"The median moved about one {abs(cut10[-1] - cut10[0]) / (med[-1] - med[0]):.0f}th "
      f"as far as the top-10% cutoff did. Lines between markers are drawn for readability;")
print("only the six markers were observed.")

trace = pd.read_csv(DATA / 'rating_trace.csv')
trace['score'] = pd.to_numeric(trace['score'], errors='coerce')

MOON = 55687996  # main_v21moon.py -- evicted, so its rating is frozen by the platform
moon = trace[(trace['ref'] == MOON) & trace['score'].notna()].sort_values('utc')
FROZEN = round(float(moon['score'].iloc[-1]), 1)
print(f"frozen exhibit  {moon['filename'].iloc[0]} [{MOON}] "
      f"peaked {moon['score'].max():.1f}, evicted, frozen at {FROZEN} "
      f"and constant over its last "
      f"{int(moon['evicted_at_poll_time'].astype(bool).sum())} polls")

# the byte-identical re-fire, for the "score fixed != agent fixed" caveat
L1, L2 = 55368156, 55608474
m1 = trace[(trace['ref'] == L1) & trace['score'].notna()]
m2 = trace[(trace['ref'] == L2) & trace['score'].notna()]
a1 = m1[m1['age_hours'] <= 3]['score'].mean()
a2 = m2[m2['age_hours'] <= 3]['score'].mean()
print(f"live agent      main_v14.py, byte-identical re-fire: 0-3h mean {a1:.1f} -> {a2:.1f} "
      f"({a2 - a1:+.1f}) over 9.7 days -- a live score does NOT stay put")

TRACKED = [1500.0, 2000.0, 2500.0]
fig, ax = plt.subplots(figsize=(9, 4.5))
for i, s in enumerate(TRACKED):
    pct = [100 * standing_of(s, boards[d]) / len(boards[d]) for d in dates]
    ax.plot(x, pct, marker='o', color=f'C{i}', label=f'fixed score {s:.0f}')
pct_frozen = [100 * standing_of(FROZEN, boards[d]) / len(boards[d]) for d in dates]
ax.plot(x, pct_frozen, marker='s', ls='--', color='C3',
        label=f'frozen submission {FROZEN}')
ax.set_xlabel('snapshot date')
ax.set_ylabel('standing (top %) — lower is better')
ax.set_title('The same number, six boards: standing improves without the score moving\n'
             '(y is a percentile, so downward = better placed)')
ax.grid(True)
ax.legend(fontsize=8)
fig.autofmt_xdate()
plt.show()

rows = []
for s in TRACKED + [FROZEN]:
    row = {'fixed score': f"{s:.1f}"}
    for d in dates:
        st = standing_of(s, boards[d])
        row[d[5:]] = f"{st} ({100 * st / len(boards[d]):.1f}%)"
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))
print("\ncell = rank (standing) on that board. Read across: rank often gets WORSE before it")
print("gets better, while standing improves nearly throughout.")
for s in TRACKED + [FROZEN]:
    f0 = 100 * standing_of(s, first) / len(first)
    f1 = 100 * standing_of(s, last) / len(last)
    print(f"  {s:>7.1f}: top {f0:.1f}% -> top {f1:.1f}%   ({f0 - f1:+.1f} points of standing)")
print("\nThe gain is not uniform: a mid-table score barely moves, a near-elite score moves a")
print("lot. Whatever is happening is happening at the top of the board, not the middle.")

n0, n1 = len(first), len(last)
r0, r1 = rank_at_percentile(0.10, n0), rank_at_percentile(0.10, n1)
print(f"teams            {n0} -> {n1}   ({n1 - n0:+d}, {100 * (n1 / n0 - 1):+.0f}%)")
print(f"top-10% rank     {r0} -> {r1}   (10% of the field, so it moves with the field)")
print(f"top-10% score    {score_at_rank(r0, first):.1f} -> {score_at_rank(r1, last):.1f}   "
      f"({score_at_rank(r1, last) - score_at_rank(r0, first):+.1f})")
print(f"top-5%  rank     {rank_at_percentile(0.05, n0)} -> {rank_at_percentile(0.05, n1)}")
print(f"top-5%  score    {score_at_percentile(0.05, first):.1f} -> "
      f"{score_at_percentile(0.05, last):.1f}   "
      f"({score_at_percentile(0.05, last) - score_at_percentile(0.05, first):+.1f})")

print("\nSplitting the fall into its two causes, for the top-10% line:")
same_rank = score_at_rank(r0, last)
print(f"  {score_at_rank(r0, first):.1f}  cutoff on {dates[0]} (rank {r0} of {n0})")
print(f"  {same_rank:.1f}  what rank {r0} is worth on {dates[-1]} "
      f"({same_rank - score_at_rank(r0, first):+.1f}: the board itself changed shape)")
print(f"  {score_at_rank(r1, last):.1f}  cutoff on {dates[-1]} (rank {r1} of {n1}) "
      f"({score_at_rank(r1, last) - same_rank:+.1f}: the extra depth field growth bought)")
print("\nSo growth explains part of the fall and something else explains the rest. Holding")
print(f"the rank fixed at {r0}, the score attached to it still dropped "
      f"{abs(same_rank - score_at_rank(r0, first)):.1f} points. That is not dilution --")
print("dilution adds teams below you and leaves the teams above you alone. Section four.")

THRESH = [2400.0, 2000.0, 1500.0]
counts = {t: [sum(1 for s in boards[d] if s >= t) for d in dates] for t in THRESH}

fig, ax = plt.subplots(figsize=(9, 4.5))
for i, t in enumerate(THRESH):
    ax.plot(x, counts[t], marker='o', color=f'C{i}', label=f'teams scoring >= {t:.0f}')
ax.plot(x, [len(boards[d]) for d in dates], marker='^', color='C3', label='teams in the field')
ax.set_xlabel('snapshot date')
ax.set_ylabel('number of teams')
ax.set_title('The field doubled; the top of it emptied out\n'
             '(one linear axis — the field line is on the same scale as the rest)')
ax.grid(True)
ax.legend(fontsize=8)
fig.autofmt_xdate()
plt.show()

rows = []
for d in dates:
    b = boards[d]
    rows.append({'snapshot': d, 'teams': len(b),
                 '>=2400': sum(1 for s in b if s >= 2400),
                 '>=2000': sum(1 for s in b if s >= 2000),
                 '>=1500': sum(1 for s in b if s >= 1500),
                 '<1500': sum(1 for s in b if s < 1500),
                 'top 1': round(score_at_rank(1, b), 1),
                 'rank 10': round(score_at_rank(10, b), 1),
                 'rank 100': round(score_at_rank(100, b), 1),
                 'rank 300': round(score_at_rank(300, b), 1)})
shape = pd.DataFrame(rows)
print(shape.to_string(index=False))

f, l = shape.iloc[0], shape.iloc[-1]
print(f"\nfield        {f['teams']} -> {l['teams']}  ({100 * (l['teams'] / f['teams'] - 1):+.0f}%)")
for col in ('>=2400', '>=2000', '>=1500', '<1500'):
    print(f"{col:<12} {f[col]} -> {l[col]}  ({100 * (l[col] / f[col] - 1):+.0f}%)")
for col in ('top 1', 'rank 10', 'rank 100', 'rank 300'):
    print(f"{col:<12} {f[col]:.1f} -> {l[col]:.1f}  ({l[col] - f[col]:+.1f})")
print("\nA purely diluting field grows the low band and leaves the high band intact. This one")
print("grew the low band AND emptied the high band, and it compressed from the top down:")
print(f"the leader lost {abs(l['top 1'] - f['top 1']):.1f} points while rank 100 lost "
      f"{abs(l['rank 100'] - f['rank 100']):.1f} and rank 300 lost "
      f"{abs(l['rank 300'] - f['rank 300']):.1f}.")

D_OLD, D_NEW = '2026-08-23', dates[-1]
old, new = boards[D_OLD], boards[D_NEW]

t5_old, t5_new = score_at_percentile(0.05, old), score_at_percentile(0.05, new)
t10_old, t10_new = score_at_percentile(0.10, old), score_at_percentile(0.10, new)
print(f"the top-5% line   {D_OLD}: {t5_old:.1f}   {D_NEW}: {t5_new:.1f}   "
      f"({t5_new - t5_old:+.1f} in {(pd.Timestamp(D_NEW) - pd.Timestamp(D_OLD)).days} days)")
print(f"the top-10% line  {D_OLD}: {t10_old:.1f}   {D_NEW}: {t10_new:.1f}   "
      f"({t10_new - t10_old:+.1f})")

st = standing_of(t5_old, new)
print(f"\naiming at the stale target: {t5_old:.1f} now ranks {st}/{len(new)} = "
      f"top {100 * st / len(new):.1f}%, i.e. {t5_old - t5_new:.1f} points of overshoot past "
      f"today's top-5% line")

for s in (2400.0, 2254.1, 2000.0):
    a, b = standing_of(s, old), standing_of(s, new)
    print(f"a score of {s:>7.1f}: {D_OLD} rank {a}/{len(old)} (top {100 * a / len(old):.1f}%)"
          f"   ->   {D_NEW} rank {b}/{len(new)} (top {100 * b / len(new):.1f}%)")
print(f"\nonly {sum(1 for s in new if s >= 2400)} teams of {len(new)} still hold 2,400 or "
      f"better, against {sum(1 for s in old if s >= 2400)} of {len(old)} on {D_OLD}.")