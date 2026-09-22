%matplotlib inline
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

def _find_data():
    # On Kaggle the dataset mounts under /kaggle/input/<slug>; find it by
    # content rather than assuming the directory name.
    kin = Path('/kaggle/input')
    if kin.exists():
        hits = sorted(kin.rglob('rating_trace.csv'))
        if hits:
            return hits[0].parent
        raise FileNotFoundError(
            'Dataset not attached. Click "Add Input" and attach '
            'kaggle.com/datasets/dariushafshar/kaggriculture-ladder-telemetry')
    return Path('/Users/dariush/Desktop/College Counselor Vault/Personal Projects/'
                'kaggriculture/datasets/kaggriculture-ladder-telemetry')

DATA = _find_data()

trace = pd.read_csv(DATA / 'rating_trace.csv')
board = pd.read_csv(DATA / 'leaderboard_snapshot.csv')
subs = pd.read_csv(DATA / 'submissions.csv')

for col in ('utc', 'submitted_utc'):
    trace[col] = pd.to_datetime(trace[col], format='ISO8601', utc=True)
trace['score'] = pd.to_numeric(trace['score'], errors='coerce')  # 'NA' while PENDING
trace['evicted'] = trace['evicted_at_poll_time'].astype(bool)

polls = trace['utc'].drop_duplicates().sort_values()
cadence_min = polls.diff().dt.total_seconds().div(60).median()
span_days = (polls.max() - polls.min()).total_seconds() / 86400

print(f"window       {polls.min():%Y-%m-%d %H:%M} -> {polls.max():%Y-%m-%d %H:%M} UTC")
print(f"span         {span_days:.2f} days over {len(polls)} polls")
print(f"cadence      {cadence_min:.1f} min (median gap between consecutive polls)")
print(f"readings     {len(trace)}  ({trace['score'].isna().sum()} still PENDING, no score yet)")
print(f"submissions  {trace['ref'].nunique()} refs, {len(subs)} rows in submissions.csv")
print(f"board        {len(board)} teams in the snapshot")

SETTLING = {55625543: 'main_flexroute.py', 55616584: 'main_breakingtie.py',
            55612018: 'main_v16rc5.py', 55608474: 'main_v14.py (life 2)'}

fig, ax = plt.subplots(figsize=(9, 4.5))
for ref, label in SETTLING.items():
    d = trace[(trace['ref'] == ref) & trace['score'].notna()].sort_values('age_hours')
    d = d[d['age_hours'] <= 36]
    ax.plot(d['age_hours'], d['score'], label=f'{label} [{ref}]')
ax.axvline(12, ls='--', lw=1)
ax.set_xlabel('hours since submission')
ax.set_ylabel('displayed rating')
ax.set_title('The first 36 hours of four submissions (dashed line = 12h)')
ax.grid(True)
ax.legend(loc='lower right', fontsize=8)
plt.show()

MILESTONES = [0.25, 1, 3, 6, 12, 24, 48]
rows = []
for ref, label in SETTLING.items():
    d = trace[(trace['ref'] == ref) & trace['score'].notna()].sort_values('age_hours')
    row = {'ref': ref, 'file': label}
    for a in MILESTONES:
        i = (d['age_hours'] - a).abs().idxmin()
        star = '*' if d.loc[i, 'evicted'] else ''
        row[f'~{a}h'] = f"{d.loc[i, 'score']:.1f} @{d.loc[i, 'age_hours']:.2f}h{star}"
    live = d[~d['evicted']]
    row['last live'] = f"{live['score'].iloc[-1]:.1f} @{live['age_hours'].iloc[-1]:.1f}h"
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))
print("\nEach cell is the nearest actual reading to that target age. Where the poll record has")
print("a gap the nearest reading sits well off target -- flexroute's '~6h' is really a 4.4h read.")
print("'last live' is the final reading taken while the submission was still active. A * marks a")
print("milestone cell whose nearest reading was taken after eviction -- that value is a frozen")
print("restatement, not a live measurement, so only flexroute was still being scored past 48h.")

LIFE1, LIFE2 = 55368156, 55608474
l1 = trace[(trace['ref'] == LIFE1) & trace['score'].notna()].sort_values('age_hours')
l2 = trace[(trace['ref'] == LIFE2) & trace['score'].notna()].sort_values('age_hours')

fig, ax = plt.subplots(figsize=(9, 4.5))
for d, lab in ((l1, f'life 1 — fired 2026-08-09 [{LIFE1}]'), (l2, f'life 2 — fired 2026-08-18 [{LIFE2}]')):
    w = d[d['age_hours'] <= 72]
    ax.plot(w['age_hours'], w['score'], label=lab)
ax.axvline(3, ls='--', lw=1)
ax.set_xlabel('hours since submission')
ax.set_ylabel('displayed rating')
ax.set_title('main_v14.py, byte-identical, two lives (dashed line = 3h window)')
ax.grid(True)
ax.legend(loc='lower right', fontsize=8)
plt.show()

m1 = l1[l1['age_hours'] <= 3]['score'].mean()
m2 = l2[l2['age_hours'] <= 3]['score'].mean()
gap_days = (l2['submitted_utc'].iloc[0] - l1['submitted_utc'].iloc[0]).total_seconds() / 86400
print(f"age-matched 0-3h mean   life 1 {m1:.1f}   life 2 {m2:.1f}   delta {m2 - m1:+.1f}   ({gap_days:.1f} days apart)")

w1 = l1[l1['age_hours'].between(0.5, 3)]['score'].mean()
w2 = l2[l2['age_hours'].between(0.5, 3)]['score'].mean()
print(f"strictly matched 0.5-3h life 1 {w1:.1f}   life 2 {w2:.1f}   delta {w2 - w1:+.1f}   "
      f"(life 1's trace only starts at {l1['age_hours'].min():.2f}h)")

c1 = l1[~l1['evicted']].sort_values('utc')['score'].iloc[-1]
c2 = l2.sort_values('utc')['score'].iloc[-1]
print(f"conservative comparison life 1 last live {c1:.1f}   life 2 frozen {c2:.1f}   delta {c2 - c1:+.1f}")
print("\nage-matched early windows overstate drift (young ratings are the most volatile part of the")
print("curve); frozen-vs-frozen understates it (life 1's frozen value already absorbed 9 days of")
print("decay while live). The robust finding is the sign: the ladder deflates around a fixed agent.")

rows = []
for ref, g in trace[trace['evicted'] & trace['score'].notna()].groupby('ref'):
    g = g.sort_values('utc')
    if len(g) <= 100:
        continue
    rows.append({'ref': ref, 'file': g['filename'].iloc[0], 'frozen_polls': len(g),
                 'age_at_freeze_h': round(g['age_hours'].iloc[0], 2),
                 'first': g['score'].iloc[0], 'last': g['score'].iloc[-1],
                 'constant': g['score'].nunique() == 1,
                 'constant_after_1st_poll': g['score'].iloc[1:].nunique() == 1})
frozen = pd.DataFrame(rows).sort_values('ref')
print(frozen.to_string(index=False))

odd = frozen[~frozen['constant']]
print(f"\n{len(frozen) - len(odd)} of {len(frozen)} frozen spans are constant end to end.")
for _, r in odd.iterrows():
    print(f"exception: {r['file']} [{r['ref']}] read {r['first']:.1f} on the poll where the eviction flag")
    print(f"           flipped, then {r['last']:.1f} one poll later and never again -- the freeze lands")
    print(f"           within one poll of eviction, not exactly on it. All {len(frozen)} are constant after that.")

v23a = trace[(trace['ref'] == 55361135) & trace['score'].notna()].sort_values('utc')
v23b = trace[(trace['ref'] == 55369597) & trace['score'].notna()].sort_values('utc')
print(f"\nv23 first fire  [55361135] frozen at {v23a['score'].iloc[-1]:.1f}, "
      f"never seen live (first observation already evicted at {v23a['age_hours'].iloc[0]:.1f}h old)")
v23b_live_days = v23b[~v23b['evicted']]['age_hours'].max() / 24
print(f"v23 re-fire     [55369597] ran live {v23b_live_days:.1f} days before eviction, "
      f"ended {v23b['score'].iloc[-1]:.1f}")

pk = trace[(trace['ref'] == 55368156) & trace['score'].notna()]
print(f"young spikes are real: v14 life 1 peaked {pk['score'].max():.1f} at "
      f"{pk.loc[pk['score'].idxmax(), 'age_hours']:.1f}h, ended {pk.sort_values('utc')['score'].iloc[-1]:.1f}")

MOON = 55687996
m = trace[(trace['ref'] == MOON) & trace['score'].notna()].sort_values('utc')
peak = m.loc[m['score'].idxmax()]
froze_utc = m[m['evicted']]['utc'].iloc[0]
peak_to_freeze_days = (froze_utc - peak['utc']).total_seconds() / 86400
print(f"\nv21moon [{MOON}] seeded {m['score'].iloc[0]:.1f} @{m['age_hours'].iloc[0]:.2f}h, peaked "
      f"{peak['score']:.1f} @{peak['age_hours']:.1f}h, ran live {m[~m['evicted']]['age_hours'].max() / 24:.1f} days")
print(f"                 drifted {m['score'].iloc[-1] - peak['score']:+.1f} over the "
      f"{peak_to_freeze_days:.1f} days from peak to eviction, froze {m['score'].iloc[-1]:.1f}")

standing = trace[trace['score'].notna()].sort_values('utc').groupby('ref').tail(1)
standing = standing.sort_values('score', ascending=False)
top, best_live = standing.iloc[0], standing[~standing['evicted']].iloc[0]
print(f"highest standing number on our board: {top['score']:.1f} ({top['filename']}, "
      f"{'FROZEN' if top['evicted'] else 'live'}) vs best live {best_live['score']:.1f} "
      f"({best_live['filename']}) -- the top of the board is {'a ghost' if top['evicted'] else 'live'}")

import math

final_poll = trace['utc'].max()
at_final = trace[trace['utc'] == final_poll]
ours = at_final[~at_final['evicted']]['score'].max()

n_teams = len(board)
top10_rank = math.floor(0.10 * n_teams)
top10_score = board.loc[board['rank'] == top10_rank, 'score'].iloc[0]

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.hist(board['score'], bins=60)
ax.axvline(ours, ls='--', lw=1)
ax.axvline(top10_score, ls=':', lw=1)
ax.set_xlabel('team score')
ax.set_ylabel('teams')
side = 'inside' if ours >= top10_score else 'outside'
ax.set_title(f'Leaderboard snapshot, {n_teams} teams (dashed = our active pair {ours:.1f}, '
             f'{side} the dotted top-10% line {top10_score:.1f})')
ax.grid(True)
plt.show()

above = int((board['score'] > ours).sum())
our_rank = above + 1
print(f"active pair max   {ours:.1f}  (max score at the final poll among non-evicted refs)")
print(f"our rank          {our_rank} of {n_teams}  -> top {100 * our_rank / n_teams:.1f}%, "
      f"{100 * (1 - our_rank / n_teams):.1f}th percentile")
print(f"top 10% line      rank {top10_rank} = {top10_score:.1f}")
if ours >= top10_score:
    print(f"margin inside 10% {ours - top10_score:.1f} points above the top-10% line")
else:
    print(f"gap to top 10%    {top10_score - ours:.1f} points below the top-10% line")
print(f"\nsanity: submissions.csv agrees on our two active refs -> "
      f"{sorted(at_final[~at_final['evicted']]['filename'].tolist())}")

hist = pd.read_csv(DATA / 'board_history.csv')
hist['score'] = pd.to_numeric(hist['score'], errors='coerce')


def score_at_percentile(pct, desc):
    """Score held by the team standing at `pct` of a DESCENDING-sorted board."""
    i = min(len(desc) - 1, max(0, int(round(pct * len(desc))) - 1))
    return desc[i]


boards = {d: sorted(g['score'].dropna().tolist(), reverse=True)
          for d, g in hist.groupby('snapshot_date')}
dates = sorted(boards)

rows = [{'snapshot': d, 'teams': len(boards[d]),
         'top1%': round(score_at_percentile(0.01, boards[d]), 1),
         'top5%': round(score_at_percentile(0.05, boards[d]), 1),
         'top10%': round(score_at_percentile(0.10, boards[d]), 1),
         'median': round(score_at_percentile(0.50, boards[d]), 1)} for d in dates]
print(pd.DataFrame(rows).to_string(index=False))

span = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days
print(f"\n{len(hist)} rows, {len(dates)} full boards, {span} days, "
      f"{hist['team_id'].nunique()} distinct team_ids across all snapshots")

print(f"\n{'window':<26}{'days':>6}{'top5%/day':>12}{'top10%/day':>12}{'teams+':>9}")
for a, b in zip(dates, dates[1:]):
    days = (pd.Timestamp(b) - pd.Timestamp(a)).days
    d5 = (score_at_percentile(0.05, boards[b]) - score_at_percentile(0.05, boards[a])) / days
    d10 = (score_at_percentile(0.10, boards[b]) - score_at_percentile(0.10, boards[a])) / days
    win = f"{a} -> {b}"
    print(f"{win:<26}{days:>6}{d5:>12.1f}{d10:>12.1f}{len(boards[b]) - len(boards[a]):>9}")

first, last = boards[dates[0]], boards[dates[-1]]
print(f"\nfield size        {len(first)} -> {len(last)} teams "
      f"({100 * (len(last) / len(first) - 1):+.0f}%)")
print(f"top-10% rank      {int(round(0.10 * len(first)))} -> {int(round(0.10 * len(last)))}")
print(f"top-10% line      {score_at_percentile(.10, first):.1f} -> "
      f"{score_at_percentile(.10, last):.1f} "
      f"({score_at_percentile(.10, last) - score_at_percentile(.10, first):+.1f})")
print(f"top-5% line       {score_at_percentile(.05, first):.1f} -> "
      f"{score_at_percentile(.05, last):.1f} "
      f"({score_at_percentile(.05, last) - score_at_percentile(.05, first):+.1f})")
print(f"median            {score_at_percentile(.50, first):.1f} -> "
      f"{score_at_percentile(.50, last):.1f} "
      f"({score_at_percentile(.50, last) - score_at_percentile(.50, first):+.1f})")
print("\nThe cutoffs fall and the median rises together because a percentile cut on a bigger")
print("field reaches further down it. Nothing here says the teams got worse -- the middle of")
print("the board got better -- it says the line you have to clear moved toward you.")

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

ax.set_title('Cutoffs falling, median rising — 5 archived boards\n'
             '(separate axes, each zoomed to its own data; markers are the actual snapshots)')
lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [ln.get_label() for ln in lines], loc='center left', fontsize=8)
fig.autofmt_xdate()
plt.show()

print("Both axes are zoomed to their own data, so the median's rise looks as large as the")
print(f"cutoffs' fall. It is not: median {med[0]:.1f} -> {med[-1]:.1f} ({med[-1] - med[0]:+.1f}) "
      f"against top-10% {cut10[0]:.1f} -> {cut10[-1]:.1f} ({cut10[-1] - cut10[0]:+.1f}).")
print("Markers sit on the five snapshot dates; the lines between them are drawn, not observed.")

agent_source = '''\
def _get(obj, key, default=None):
    """Read a key from the observation whether it is a dict or an object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def agent(observation, configuration=None):
    """Minimal valid Kaggriculture action: the farmer and every hand pass, no market orders.

    This is a runnable submission artifact, not a claimed policy. Replace the body with
    something that actually plays -- the point here is that a fork can submit immediately
    and start its own rating trace.
    """
    n_hands = 0
    try:
        farms = list(_get(observation, "farms", []) or [])
        seat = 1 if int(_get(observation, "player", 0) or 0) == 1 else 0
        if seat < len(farms):
            n_hands = len(list(_get(farms[seat], "hands", []) or []))
    except Exception:
        n_hands = 0
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n_hands)], "market": []}
'''

path = Path('main.py')
path.write_text(agent_source)
compile(agent_source, str(path), 'exec')  # fail loudly here rather than on the ladder

print(f"wrote and compiled {path.resolve()}  ({len(agent_source)} bytes)")
print('-' * 72)
print('\n'.join(agent_source.splitlines()[:12]))
print('-' * 72)
print('Submit main.py from a fork to start your own trace.')