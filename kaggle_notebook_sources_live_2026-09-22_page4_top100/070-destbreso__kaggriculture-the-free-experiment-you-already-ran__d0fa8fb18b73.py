# Chart style, matched to the companion notebooks: recessive axes, a light
# horizontal grid, nothing decorative.
import csv, math, os, statistics as st
from collections import Counter, defaultdict
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e7e7e4'
plt.rcParams.update({
    'figure.dpi': 130, 'savefig.dpi': 130,
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
    'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': 'white', 'axes.facecolor': 'white'})

def tidy(ax, ylab=None, title=None):
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.xaxis.grid(False)
    if ylab: ax.set_ylabel(ylab)
    if title: ax.set_title(title, loc='left', pad=10, fontweight='bold')
    return ax

def find_data(roots=('/kaggle/input',)):
    """Walk for episodes.csv rather than guessing Kaggle's mount depth."""
    def scan(root, max_depth=6):
        root = os.path.abspath(root); base = root.rstrip(os.sep).count(os.sep)
        hits = []
        for dp, dn, fn in os.walk(root):
            if dp.count(os.sep) - base >= max_depth:
                dn[:] = []; continue
            dn[:] = [d for d in dn if not d.startswith('.')]
            if 'episodes.csv' in fn: hits.append(dp)
        return hits
    found = []
    for r in roots:
        if os.path.isdir(r): found += scan(r)
    here = os.path.abspath(os.getcwd())
    while not found:
        for sub in ('data', '.'):
            d = os.path.join(here, sub)
            if os.path.isdir(d): found += scan(d, max_depth=4)
        parent = os.path.dirname(here)
        if parent == here: break
        here = parent
    if found: return found[0]
    raise FileNotFoundError('episodes.csv not found. Attach '
                            'georgymamarin/kaggriculture-episodes.')

BASE = find_data()

# One cell runs the simulator. Guarded, because a notebook that dies on an
# import shows the reader nothing and the rest of this does not need it.
try:
    from kaggle_environments import make
    ENGINE = True
except ImportError:
    ENGINE = False
    print('kaggle_environments unavailable; the ablation is skipped.')

HS = defaultdict(dict)
with open(BASE + '/stream_hashes.csv') as f:
    for r in csv.DictReader(f):
        HS[str(r['episode_id'])][r['seat']] = r

VAL = []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_VALIDATION' or r['state'] != 'COMPLETED':
            continue
        try:
            b0, b1 = float(r['bank_0']), float(r['bank_1'])
        except (TypeError, ValueError):
            continue
        VAL.append({'ep': str(r['episode_id']), 'sub': r['sub_0'],
                    'team': r['team_0'], 'b0': b0, 'b1': b1,
                    'h': HS.get(str(r['episode_id']))})

per_team = Counter(v['team'] for v in VAL)
HAVE = [v for v in VAL if v['h'] and '0' in v['h'] and '1' in v['h']]
print(f'{len(VAL)} validation episodes')
print(f'  distinct submissions {len({v["sub"] for v in VAL})}, teams {len(per_team)}')
print(f'  submissions per team {dict(sorted(Counter(per_team.values()).items()))}')
print(f'  with both action streams fingerprinted: {len(HAVE)}')

m = np.array([v['b0'] - v['b1'] for v in VAL])
dec = int((m != 0).sum()); w0 = int((m > 0).sum())
bt = stats.binomtest(w0, dec)
lo, hi = bt.proportion_ci()

# Design effect: episodes cluster by team, so an interval computed as though
# they were independent is too narrow. Estimate the intracluster correlation
# by ANOVA and widen accordingly.
grp = defaultdict(list)
for v in VAL:
    if v['b0'] != v['b1']:
        grp[v['team']].append(1 if v['b0'] > v['b1'] else 0)
sizes = [len(x) for x in grp.values()]
mbar, k = st.mean(sizes), len(grp)
grand = st.mean(x for g in grp.values() for x in g)
msb = sum(len(g)*(st.mean(g)-grand)**2 for g in grp.values())/(k-1) if k > 1 else 0
msw = sum(sum((x-st.mean(g))**2 for x in g) for g in grp.values())/(dec-k) if dec > k else 0
den = msb + (mbar-1)*msw
icc = (msb-msw)/den if den > 0 else 0.0
deff = 1 + (mbar-1)*icc
half = (hi-lo)/2 * max(deff, 1)**.5

print(f'exact ties   {len(m)-dec} of {len(m)}  ({100*(len(m)-dec)/len(m):.0f} %)')
print(f'decided      {dec}')
print(f'seat 0 wins  {w0} of {dec} = {100*w0/dec:.1f} %   binomial p = {bt.pvalue:.3f}')
print(f'mean margin  {m.mean():+,.1f}   Wilcoxon p = {stats.wilcoxon(m).pvalue:.3f}')
print(f'\nclustered in {k} teams, mean {mbar:.2f} episodes each')
print(f'  intracluster correlation {icc:+.3f}   design effect {deff:.3f}')
print(f'  effective n {dec/deff:.0f} of {dec} nominal')
print(f'  naive 95 % interval      [{100*lo:.1f} %, {100*hi:.1f} %]')
print(f'  design-corrected         [{100*(w0/dec-half):.1f} %, {100*(w0/dec+half):.1f} %]')

fig, ax = plt.subplots(figsize=(7.8, 2.5))
ax.plot([w0/dec-half, w0/dec+half], [0, 0], color=BLUE, lw=7,
        solid_capstyle='round', alpha=.5)
ax.plot([w0/dec], [0], 'o', color=BLUE, ms=11, zorder=3)
ax.axvline(.5, color=ORANGE, lw=2)
ax.text(.5, .42, 'a coin flip', color=ORANGE, ha='center', fontsize=10, fontweight='bold')
ax.text(w0/dec, -.45, f'{100*w0/dec:.1f} %', color=BLUE, ha='center',
        fontsize=9, fontweight='bold')
ax.set_xlim(.35, .68); ax.set_ylim(-.75, .8); ax.set_yticks([])
ax.set_xlabel("seat 0's share of the decided verification games")
ax.spines['left'].set_visible(False)
tidy(ax, None, 'Going first is worth nothing, in the place it would show')
ax.xaxis.grid(True, color=GRID, lw=.8); ax.yaxis.grid(False)
plt.tight_layout(); plt.show()

COLS = [('stream_h24', 'the first day'), ('stream_h100', 'turn 100'),
        ('stream_h200', 'turn 200'), ('stream_h400', 'turn 400'),
        ('stream_h719', 'the whole game')]
surv = []
for c, lab in COLS:
    kk = sum(1 for v in HAVE if v['h']['0'][c] and v['h']['0'][c] == v['h']['1'][c])
    surv.append(100*kk/len(HAVE))
    print(f'seats still identical through {lab:<16}{kk:>4} of {len(HAVE)}'
          f'{100*kk/len(HAVE):>8.1f} %')

fixed = [v for v in HAVE if v['h']['0']['stream_h719']
         and v['h']['0']['stream_h719'] == v['h']['1']['stream_h719']]
react = [v for v in HAVE if v not in fixed]
print(f'\n-> {100*len(react)/len(HAVE):.0f} % of submissions reacted to something.')
print(f'   The other {100*len(fixed)/len(HAVE):.0f} % are effectively fixed scripts.')

fig, ax = plt.subplots(figsize=(8.2, 4.0))
x = [24, 100, 200, 400, 719]
ax.plot(x, surv, color=BLUE, lw=2.6, marker='o', ms=7,
        markeredgecolor='white', markeredgewidth=1.3, zorder=3)
ax.fill_between(x, surv, color=BLUE, alpha=.10)
for xi, yi in zip(x, surv):
    ax.annotate(f'{yi:.0f} %', (xi, yi), xytext=(0, 10),
                textcoords='offset points', ha='center', fontsize=9,
                fontweight='bold', color=INK)
ax.set_ylim(0, 108); ax.set_xlim(0, 760)
ax.set_xlabel('turn')
tidy(ax, 'submissions still identical to themselves',
     'A script cannot diverge from itself. Most of the field does')
plt.tight_layout(); plt.show()

f_m = np.array([v['b0'] - v['b1'] for v in fixed])
r_m = np.array([v['b0'] - v['b1'] for v in react])
print(f"{'':<32}{'episodes':>10}{'tie':>8}{'median |margin|':>18}")
for lab, v in (('both seats played the same stream', f_m),
               ('the seats diverged', r_m)):
    print(f'{lab:<32}{len(v):>10,}{100*(v==0).mean():>7.0f} %'
          f'{np.median(np.abs(v)):>18,.0f}')

fig, ax = plt.subplots(figsize=(8.2, 3.4))
labs = ['same stream\n(effectively fixed)', 'diverged\n(reactive)']
ties = [100*(f_m == 0).mean(), 100*(r_m == 0).mean()]
ax.barh(labs, ties, color=[BLUE, ORANGE], height=.5)
for i, t in enumerate(ties):
    ax.text(t+1.5, i, f'{t:.0f} % tie', va='center', fontsize=10,
            fontweight='bold', color=BLUE if i == 0 else ORANGE)
ax.set_xlim(0, 110); ax.set_xlabel('share of episodes ending in an exact tie')
tidy(ax, None, 'Most of the separation is agents diverging from themselves')
ax.xaxis.grid(True, color=GRID, lw=.8); ax.yaxis.grid(False)
plt.tight_layout(); plt.show()


# THE ROUTE COMES FROM THE DATASET, not from a file next to the notebook. An
# earlier version read one out of the author's repository, which exists in
# exactly one place on earth, so on Kaggle it resolved to None and the cell
# raised. replays.parquet is already attached, so lift a real 719-turn action
# stream out of it and replay that in both seats.
import json as _json

N_ABLATE = 40          # 80 episodes; offline this was run at 300

def load_route():
    import pyarrow.parquet as pq
    best = None
    with open(BASE + '/episodes.csv') as f:
        for r in csv.DictReader(f):
            if r['type'] != 'EPISODE_TYPE_PUBLIC' or r['state'] != 'COMPLETED':
                continue
            try:
                b = float(r['bank_0'])
            except (TypeError, ValueError):
                continue
            if best is None or b > best[1]:
                best = (r['episode_id'], b)
    t = pq.read_table(BASE + '/replays.parquet',
                      filters=[('episode_id', '==', int(best[0]))],
                      columns=['replay_json'])
    steps = _json.loads(t.column('replay_json')[0].as_py())['steps']
    return [None] + [(s[0].get('action') if s else None) for s in steps], best

PASS = {'farmer': ['PASS'], 'hands': [], 'market': []}

def mirror(route, seed, weed):
    e = make('kaggriculture', configuration={'episodeSteps': 720,
                                             'seed': int(seed),
                                             'weedSpawnChance': weed})
    e.reset(2)
    st = 0
    while not e.done:
        a = route[st + 1] if st + 1 < len(route) else None
        act = a if isinstance(a, dict) else dict(PASS)
        e.step([dict(act), dict(act)])        # the SAME stream in both seats
        st += 1
    o = e.state[0].observation
    w = [sum(1 for row in o['farms'][p]['tiles'] for t in row
             if isinstance(t, dict) and t.get('kind') == 'WEED') for p in (0, 1)]
    return float(e.state[0].reward or 0) - float(e.state[1].reward or 0), w

if ENGINE and os.path.exists(BASE + '/replays.parquet'):
    ROUTE, src = load_route()
    print(f"replaying the stream from episode {src[0]}, which banked "
          f"${src[1]:,.0f}, against itself\n")
    sds = [int(x) for x in np.random.default_rng(20260815).integers(1, 10**6, N_ABLATE)]
    for lab, wc in (('the random spawn at its default, 0.005', 0.005),
                    ('the random spawn switched off, 0.0', 0.0)):
        out = [mirror(ROUTE, s, wc) for s in sds]
        v = np.array([o[0] for o in out])
        w = np.array([o[1] for o in out])
        print(f'  {lab:<40} ties {int((v==0).sum()):>3}/{len(v)}'
              f'  ({100*(v==0).mean():5.1f} %)   weeds '
              f'{w[:,0].mean():.2f}/{w[:,1].mean():.2f}')
    print('\n  with the spawn off the weeds that remain are the deterministic ones,')
    print('  and both farms get exactly the same ones.')
else:
    print('the engine or replays.parquet is unavailable, so the ablation is skipped')