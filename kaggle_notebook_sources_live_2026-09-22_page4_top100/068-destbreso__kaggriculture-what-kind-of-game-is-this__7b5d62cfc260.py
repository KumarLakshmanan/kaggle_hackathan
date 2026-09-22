# Chart style, matched to the companion notebooks: recessive axes, a light
# horizontal grid, nothing decorative. Colour is assigned by the job it does.
import csv, math, os
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
    """Find the dataset by WALKING for episodes.csv, at whatever depth it sits.

    Kaggle does not mount an input at a fixed depth: it can appear as
    /kaggle/input/<slug>/ or as /kaggle/input/datasets/<owner>/<slug>/.
    A list of candidate paths is how the first version of this notebook failed,
    silently, with BASE = None and a TypeError three lines later."""
    def scan(root, max_depth=6):
        root = os.path.abspath(root)
        base = root.rstrip(os.sep).count(os.sep)
        hits = []
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base >= max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            if 'episodes.csv' in filenames:
                hits.append(dirpath)
        return hits

    found = []
    for r in roots:
        if os.path.isdir(r):
            found += scan(r)
    here = os.path.abspath(os.getcwd())          # local checkout: walk upward
    while not found:
        for sub in ('data', '.'):
            d = os.path.join(here, sub)
            if os.path.isdir(d):
                found += scan(d, max_depth=4)
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    if found:
        return found[0]
    # Fail loudly and say what was actually there, rather than returning None
    # and letting the error surface somewhere unrelated.
    seen = []
    for r in roots:
        if os.path.isdir(r):
            seen += [os.path.join(dp, f) for dp, _, fs in os.walk(r) for f in fs][:40]
    raise FileNotFoundError(
        'episodes.csv not found. Attach the dataset '
        'georgymamarin/kaggriculture-episodes to this notebook.\n'
        'What is mounted:\n  ' + ('\n  '.join(seen) if seen else '(nothing)'))

BASE = find_data()

# The ablation in section 2 replays one fixed route against itself. Any route
# works; this one is a recorded stream published with the competition.
ROUTE_PATH = next((p for p in ('agents/v7.6_zeddouk/main.py',
                               '../agents/v7.6_zeddouk/main.py',
                               '../../agents/v7.6_zeddouk/main.py')
                   if os.path.exists(p)), None)
N_ABLATE = 40                     # 80 episodes; offline this was run at 300

# Two cells run the simulator rather than reading the dataset. The import is
# guarded because a notebook that dies on it shows the reader nothing at all,
# and nothing else here depends on it.
try:
    from kaggle_environments import make
    ENGINE = True
except ImportError:
    ENGINE = False
    print('kaggle_environments is unavailable, so the two engine demonstrations '
          'are skipped.\nAttach the Kaggriculture competition to run them.')

# Every number below is computed from this, live. Nothing is pasted in.
rows = []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_PUBLIC' or r['state'] != 'COMPLETED':
            continue                     # validation episodes are self-play
        try:
            x, y = float(r['bank_0']), float(r['bank_1'])
        except (TypeError, ValueError):
            continue
        rows.append((r['create_time'] or '', r['sub_0'], r['sub_1'], x, y))
# Chronological, because section 5 measures a SERIAL correlation and the order
# of the file is not guaranteed to be the order the games were played in.
rows.sort(key=lambda t: t[0])            # ISO 8601, so lexicographic works
sub0 = [r[1] for r in rows]; sub1 = [r[2] for r in rows]
b0 = np.array([r[3] for r in rows]); b1 = np.array([r[4] for r in rows])
M = np.r_[b0, b1]                        # one agent's bank, pooled over seats
Dm = b0 - b1                             # the signed margin
print(f'{BASE}\n{len(b0):,} public completed episodes, {len(set(sub0)|set(sub1)):,} submissions')

# Does the randomness treat the two seats alike? Two checks, because two
# different things could break the symmetry the argument needs.
if ENGINE:
    # (a) the opening. If the farms differed at turn 0, symmetry would be dead
    #     before the first action.
    env = make('kaggriculture', configuration={'episodeSteps': 30, 'seed': 7})
    env.reset(2)
    f = env.state[0].observation['farms']
    import json as _json
    same = (_json.dumps(f[0], sort_keys=True, default=str)
            == _json.dumps(f[1], sort_keys=True, default=str))
    print(f'the two farms are byte-identical at turn 0: {same}')
    print(f"  money {f[0]['money']:.0f} / {f[1]['money']:.0f}   "
          f"farmer {f[0]['farmer']} / {f[1]['farmer']}   "
          f"land {f[0]['unlocked_quadrants']} / {f[1]['unlocked_quadrants']}")

    # (b) the weeds. Drawn seat 0 first, then seat 1, from ONE generator, so the
    #     two seats get different numbers. Symmetry needs the same DISTRIBUTION,
    #     not the same numbers, so that is what gets tested.
    def season_weeds(seed):
        e = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)})
        e.run(['pass', 'pass'])
        o = e.state[0].observation
        return [sum(1 for row in o['farms'][p]['tiles'] for t in row
                    if isinstance(t, dict) and t.get('kind') == 'WEED') for p in (0, 1)]

    W = np.array([season_weeds(s) for s in
                  np.random.default_rng(3).integers(1, 10 ** 6, 60)])
    print(f'\nweeds at the end of the season, over {len(W)} seeds:')
    print(f'  seat 0   mean {W[:, 0].mean():5.2f}   sd {W[:, 0].std():4.2f}')
    print(f'  seat 1   mean {W[:, 1].mean():5.2f}   sd {W[:, 1].std():4.2f}')
    print(f'  paired t-test on the difference   p = '
          f'{stats.ttest_rel(W[:, 0], W[:, 1]).pvalue:.3f}')
    print(f'  two-sample KS on the distributions p = '
          f'{stats.ks_2samp(W[:, 0], W[:, 1]).pvalue:.3f}')
    print('\n-> different draws, same distribution, which is what the argument needs.')

    # (c) and how different? The engine spawns weeds for seat 0 and then seat 1
    #     from ONE generator inside the same loop, so the two boards consume
    #     disjoint stretches of the same stream. Same distribution, different
    #     squares. This is why two identical routes do not always tie.
    def layout(seed):
        e = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)})
        e.run(['pass', 'pass'])
        fm = e.state[0].observation['farms']
        return [{(x, y) for y, row in enumerate(fm[p]['tiles'])
                 for x, t in enumerate(row)
                 if isinstance(t, dict) and t.get('kind') == 'WEED'} for p in (0, 1)]

    print('\nthe SAME agent in both seats, where the weeds actually landed:')
    ndiff = 0
    for i, sd in enumerate((11, 22, 33, 44, 55, 66, 77, 88)):
        a, b = layout(sd)
        ndiff += a != b
        if i < 2:
            print(f'  seed {sd}: seat 0 {sorted(a)}')
            print(f'           seat 1 {sorted(b)}')
    print(f'  layouts differ in {ndiff} of 8 seeds')

    # (d) the one structural asymmetry, tested rather than argued: seat 0's unit
    #     commits before seat 1's. If that were worth anything, identical orders
    #     would cost different amounts.
    def buyer(n):
        def a(obs, cfg=None):
            if obs['day'] == 0 and obs['hour'] == 1:
                return {'farmer': ['PASS'], 'hands': [],
                        'market': [['BUY_PRODUCT', 'WHEAT', n]]}
            return {'farmer': ['PASS'], 'hands': [], 'market': []}
        return a

    def spend(n0, n1):
        e = make('kaggriculture', configuration={'episodeSteps': 6, 'seed': 99})
        e.run([buyer(n0), buyer(n1)])
        fm = e.state[0].observation['farms']
        return 3000 - fm[0]['money'], 3000 - fm[1]['money']

    print('\nboth seats buying the same good on the same turn:')
    for n in (1, 5, 20, 60):
        a, b = spend(n, n)
        print(f'  {n:>2} units each   seat 0 spends {a:>6,.0f}   seat 1 spends {b:>6,.0f}'
              f'   {"identical" if a == b else "DIFFERENT"}')
    for n0, n1 in ((10, 2), (2, 10)):
        a, b = spend(n0, n1)
        print(f'  {n0:>2} against {n1:<2}    seat 0 {a/n0:>5.1f}/unit        '
              f'seat 1 {b/n1:>5.1f}/unit')
    print('  -> the per-unit price follows the ORDER SIZE, and swapping the sizes')
    print('     swaps the cost exactly. Committing first is worth nothing.')

# stream_hashes.csv fingerprints each seat's action stream at five prefixes, so
# two seats playing the same route in the same episode collide by construction.
import collections
HS = collections.defaultdict(dict)
with open(BASE + '/stream_hashes.csv') as f:
    for r in csv.DictReader(f):
        HS[r['episode_id']][r['seat']] = r
pub = set()
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] == 'EPISODE_TYPE_PUBLIC' and r['state'] == 'COMPLETED':
            pub.add(r['episode_id'])

COLS = [('stream_h24', 'the first day'), ('stream_h100', 'turn 100'),
        ('stream_h200', 'turn 200'), ('stream_h400', 'turn 400'),
        ('stream_h719', 'the whole game')]
n, same = 0, {c: 0 for c, _ in COLS}
for eid in pub:
    d = HS.get(eid)
    if not d or '0' not in d or '1' not in d:
        continue                       # replay coverage trails the crawl rate
    n += 1
    for c, _ in COLS:
        if d['0'][c] and d['0'][c] == d['1'][c]:
            same[c] += 1

print(f'{n:,} of {len(pub):,} public episodes have BOTH seats fingerprinted')
print(f'  ({100*n/len(pub):.0f} % coverage, set by the dataset crawler rather than by any')
print('   choice here: replays.parquet holds fewer episodes than the hashes do)\n')
print(f"{'the two seats play identically through':<40}{'episodes':>10}{'share':>9}")
for c, lab in COLS:
    print(f'{lab:<40}{same[c]:>10,}{100*same[c]/n:>8.1f} %')

# And what actually HAPPENS in a full mirror? Not a coin flip.
mir, rest = [], []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_PUBLIC' or r['state'] != 'COMPLETED':
            continue
        d = HS.get(r['episode_id'])
        if not d or '0' not in d or '1' not in d:
            continue
        try:
            a, b = float(r['bank_0']), float(r['bank_1'])
        except (TypeError, ValueError):
            continue
        h = d['0']['stream_h719']
        (mir if h and h == d['1']['stream_h719'] else rest).append(a - b)
mir, rest = np.array(mir), np.array(rest)
print(f'\n{"":<26}{"mirrors":>10}{"every other episode":>22}')
print(f'{"episodes":<26}{len(mir):>10,}{len(rest):>22,}')
print(f'{"tie to the dollar":<26}{100*(mir==0).mean():>9.0f} %{100*(rest==0).mean():>21.1f} %')
print(f'{"median absolute margin":<26}{np.median(np.abs(mir)):>10,.0f}'
      f'{np.median(np.abs(rest)):>22,.0f}')

fig, ax = plt.subplots(figsize=(8.0, 3.6))
labs = [lab for _, lab in COLS]
vals = [100 * same[c] / n for c, _ in COLS]
ax.bar(range(len(vals)), vals, color=[ORANGE] + [BLUE] * 4, width=.62)
for i, v in enumerate(vals):
    ax.text(i, v + .5, f'{v:.1f} %', ha='center', fontsize=9,
            fontweight='bold', color=ORANGE if i == 0 else INK)
ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, fontsize=9)
ax.set_ylim(0, max(vals) * 1.25)
ax.set_xlabel('identical up to')
tidy(ax, 'share of public episodes', 'How often you are playing your own route')
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

# Validation episodes are self-play. Every one is a strategy against a copy of
# itself, which is exactly the configuration the symmetry argument invokes.
v0, v1, ident, subs_seen = [], [], 0, set()
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_VALIDATION' or r['state'] != 'COMPLETED':
            continue
        try:
            x, y = float(r['bank_0']), float(r['bank_1'])
        except (TypeError, ValueError):
            continue
        ident += r['sub_0'] == r['sub_1']
        subs_seen.add(r['sub_0'])
        v0.append(x); v1.append(y)
v0, v1 = np.array(v0), np.array(v1)
dec = v0 != v1
w0 = int((v0 > v1).sum())
bt = stats.binomtest(w0, int(dec.sum()))
print(f'{len(v0)} validation episodes, {ident} of them the SAME submission on both seats')
print(f'  distinct submissions {len(subs_seen)}, so one verification game each')
print(f'  exact ties        {int((~dec).sum())}  ({100*(~dec).mean():.0f} %)')
print(f'  decided           {int(dec.sum())}')
print(f'  seat 0 wins       {w0} of {int(dec.sum())} = {100*w0/dec.sum():.1f} %')
print(f'  binomial p        {bt.pvalue:.3f}   '
      f'95 % interval [{100*bt.proportion_ci().low:.1f} %, '
      f'{100*bt.proportion_ci().high:.1f} %]')
print(f'  mean margin       {(v0-v1).mean():+,.0f} on a largest of '
      f'{np.abs(v0-v1).max():,.0f}')

# The verification game doubles as a purity test: a fixed script plays the same
# actions in both seats whatever the weeds do, so a submission whose two seats
# diverge has reacted to something.
val = []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_VALIDATION' or r['state'] != 'COMPLETED':
            continue
        d = HS.get(r['episode_id'])
        if not d or '0' not in d or '1' not in d:
            continue
        try:
            val.append((d, float(r['bank_0']) - float(r['bank_1'])))
        except (TypeError, ValueError):
            pass

print(f'{len(val)} verification games with both streams fingerprinted\n')
print(f"{'seats still identical at':<26}{'submissions':>13}{'share':>9}")
for c, lab in COLS:
    k = sum(1 for d, _ in val if d['0'][c] and d['0'][c] == d['1'][c])
    print(f'{lab:<26}{k:>13,}{100*k/len(val):>8.1f} %')

def _split(keep):
    return np.array([m for d, m in val
                     if keep(bool(d['0']['stream_h719'])
                             and d['0']['stream_h719'] == d['1']['stream_h719'])])
same_s, diff_s = _split(lambda x: x), _split(lambda x: not x)
print(f'\n{"":<34}{"episodes":>10}{"tie":>8}{"median |margin|":>18}')
for lab, v in (('seats played the same stream', same_s),
               ('seats diverged', diff_s)):
    print(f'{lab:<34}{len(v):>10,}{100*(v==0).mean():>7.0f} %'
          f'{np.median(np.abs(v)):>18,.0f}')
print(f'\n-> {100*len(diff_s)/len(val):.0f} % of submissions react to something. '
      f'The rest are effectively fixed.')

wins0, decided = int((b0 > b1).sum()), int((b0 != b1).sum())
bt = stats.binomtest(wins0, decided)
lo, hi = bt.proportion_ci()
print(f"seat 0 wins {wins0:,} of {decided:,} decided episodes = {100*wins0/decided:.2f} %")
print(f"  95 % interval  [{100*lo:.2f} %, {100*hi:.2f} %]   binomial p = {bt.pvalue:.3f}")
print(f"  ties: {len(b0)-decided:,} episodes")
print(f"\nmean margin {Dm.mean():+,.0f} on a spread of {Dm.std(ddof=1):,.0f}"
      f"   (t-test p = {stats.ttest_1samp(Dm, 0).pvalue:.3f},"
      f" Wilcoxon p = {stats.wilcoxon(Dm).pvalue:.3f})")

fig, ax = plt.subplots(figsize=(7.8, 2.4))
ax.plot([lo, hi], [0, 0], color=BLUE, lw=7, solid_capstyle='round', alpha=.55)
ax.plot([wins0/decided], [0], 'o', color=BLUE, ms=11, zorder=3)
ax.axvline(.5, color=ORANGE, lw=2)
ax.text(.5, .40, 'a coin flip', color=ORANGE, ha='center', fontsize=10, fontweight='bold')
ax.text(wins0/decided, -.42, f'{100*wins0/decided:.2f} %', color=BLUE, ha='center',
        fontsize=9, fontweight='bold')
ax.set_xlim(.485, .515); ax.set_ylim(-.7, .8); ax.set_yticks([])
ax.set_xlabel("seat 0's win rate, every decided episode on the board")
ax.spines['left'].set_visible(False)
tidy(ax, None, 'Going first is worth nothing')
ax.xaxis.grid(True, color=GRID, lw=.8); ax.yaxis.grid(False)
plt.tight_layout(); plt.show()

# Shops unlock at the end of day d when (d+1) % 3 == 0, so the first is visible
# at the start of day 3. Two different seeds draw the same shop with p = 1/8.
TURNS_PER_DAY, N_SHOPS = 24, 8
FIRST_SHOP_TURN = 3 * TURNS_PER_DAY

# Weeds: every empty unlocked tile gets an independent 0.005 chance each night.
# Only the NW quadrant starts unlocked, so at most 25 tiles are eligible, fewer
# for a route that plants them. The horizon is a property of your route too.
WEED_P, NW = 0.005, 25
days = np.arange(1, 13)

fig, ax = plt.subplots(figsize=(8.4, 4.0))
for empty, col, lab in ((NW, BLUE, 'leaves all 25 starting tiles empty'),
                        (12, AQUA, 'plants half of them'),
                        (4, ORANGE, 'plants all but four')):
    ax.plot(days * TURNS_PER_DAY, 1 - (1 - WEED_P) ** (empty * days),
            color=col, lw=2.2, marker='o', ms=4, label=f'a route that {lab}')
ax.axvline(FIRST_SHOP_TURN, color=INK, lw=1.6, ls='--')
ax.text(FIRST_SHOP_TURN + 8, .90,
        f'turn {FIRST_SHOP_TURN}: the first shop unlocks,\n'
        f'and two seeds draw a different one\n'
        f'{100*(1-1/N_SHOPS):.0f} % of the time',
        fontsize=9, color=INK, fontweight='bold', va='top')
ax.set_xlabel('turn'); ax.set_ylim(0, 1); ax.set_xlim(0, 300)
ax.legend(frameon=False, fontsize=9, loc='lower right', bbox_to_anchor=(1, .02))
tidy(ax, 'chance a weed has appeared by now',
     'The only two channels through which a seed can become visible')
plt.tight_layout(); plt.show()

print(f"the shop channel opens at turn {FIRST_SHOP_TURN}, reliably")
print(f"the weed channel opens earlier but only for a route that leaves ground bare")

# Two agents that differ ONLY in how much ground they leave bare. If the shop
# draw were a function of the seed, both would unlock the same shops.
def passer(obs, cfg=None):
    return {'farmer': ['PASS'], 'hands': [], 'market': []}

def planter(obs, cfg=None):
    priv = obs.get('private', {}) or {}
    f = obs['farms'][obs['player']]
    if (priv.get('seeds', {}) or {}).get('WHEAT', 0) > 0 \
            and f['tiles'][f['farmer'][1]][f['farmer'][0]] is None:
        return {'farmer': ['PLANT', 'WHEAT'], 'hands': [], 'market': []}
    if f['money'] >= 10:
        return {'farmer': ['EAST'], 'hands': [], 'market': [['BUY_SEED', 'WHEAT', 1]]}
    return {'farmer': ['PASS'], 'hands': [], 'market': []}

def episode(seed, a, b):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)})
    env.run([a, b])
    o = env.state[0].observation
    return list(o['town']['unlocked_shops']), 10000 - o['market']['inventory']['CARROT']

if ENGINE:
    print(f"{'seed':>6}{'shops identical?':>19}{'carrot demand, bare':>22}"
          f"{'carrot demand, planted':>25}")
    for sd in (11, 22, 33, 44):
        s_bare, d_bare = episode(sd, passer, passer)
        s_plant, d_plant = episode(sd, planter, planter)
        print(f"{sd:>6}{str(s_bare == s_plant):>19}{d_bare:>22,}{d_plant:>25,}")

r_pool = stats.pearsonr(b0, b1)

# THE CONFOUND. Matchmaking pairs on rating, so two strong agents meet and both
# bank well for reasons having nothing to do with the market they share.
# Holding the PAIR fixed is not possible here: there are 30,135 distinct
# submission pairs in 32,570 episodes and the ladder almost never repeats a
# matchup. So we subtract each submission's own mean bank and correlate the
# residuals, which removes both agents' average strength using every episode.
tot, cnt = {}, {}
for s, x in list(zip(sub0, b0)) + list(zip(sub1, b1)):
    tot[s] = tot.get(s, 0.0) + x; cnt[s] = cnt.get(s, 0) + 1
ok = {s for s, n in cnt.items() if n >= 5}
keep = np.array([a in ok and b in ok for a, b in zip(sub0, sub1)])
e0 = np.array([x - tot[s]/cnt[s] for s, x in zip(sub0, b0)])
e1 = np.array([x - tot[s]/cnt[s] for s, x in zip(sub1, b1)])
r_within = stats.pearsonr(e0[keep], e1[keep])

pairs = set()
for a, b in zip(sub0, sub1):
    pairs.add((a, b) if a <= b else (b, a))

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.7))
i = np.random.default_rng(1).choice(len(b0), 6000, replace=False)
ax.scatter(b0[i], b1[i], s=5, color=BLUE, alpha=.18, lw=0)
lim = [0, np.percentile(np.r_[b0, b1], 99.5)]
ax.plot(lim, lim, color=MUTED, lw=1, ls=':')
m, c = np.polyfit(b0, b1, 1)
ax.plot(np.array(lim), m*np.array(lim)+c, color=ORANGE, lw=2)
ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect('equal')
ax.set_xlabel("seat 0's bank")
tidy(ax, "seat 1's bank", f'Both banks move together   r = {r_pool[0]:+.3f}')

j = np.random.default_rng(2).choice(int(keep.sum()), 6000, replace=False)
ax2.scatter(e0[keep][j], e1[keep][j], s=5, color=AQUA, alpha=.18, lw=0)
L = np.percentile(np.abs(np.r_[e0[keep], e1[keep]]), 99)
ax2.plot([-L, L], [-L, L], color=MUTED, lw=1, ls=':')
mm, cc = np.polyfit(e0[keep], e1[keep], 1)
ax2.plot([-L, L], [mm*-L+cc, mm*L+cc], color=ORANGE, lw=2)
ax2.set_xlim(-L, L); ax2.set_ylim(-L, L); ax2.set_aspect('equal')
ax2.set_xlabel("seat 0's bank, minus its own average")
tidy(ax2, "seat 1's bank, minus its own average",
     f'And still do with skill removed   r = {r_within[0]:+.3f}')
plt.tight_layout(); plt.show()

print(f"{len(pairs):,} distinct submission pairs in {len(b0):,} episodes: "
      f"the ladder almost never repeats a matchup\n")
print(f"pooled            r = {r_pool[0]:+.4f}")
print(f"within-submission r = {r_within[0]:+.4f}  "
      f"({int(keep.sum()):,} episodes where both sides have 5+ games)")
print(f"-> only {100*(r_pool[0]-r_within[0])/r_pool[0]:.0f} % of it was who happened to be playing")

sig, rho = M.std(ddof=1), r_pool[0]
pred, obs = sig*math.sqrt(2*(1-rho)), Dm.std(ddof=1)
indep = sig*math.sqrt(2)
print(f"  sd of one bank                    {sig:>10,.0f}")
print(f"  predicted sd of the margin        {pred:>10,.0f}")
print(f"  observed  sd of the margin        {obs:>10,.0f}   "
      f"({100*abs(pred-obs)/obs:.1f} % apart)")
print(f"  if the two banks were independent {indep:>10,.0f}")
print(f"\n  the shared episode deletes {100*(1-obs/indep):.0f} % of the spread")

fig, ax = plt.subplots(figsize=(8.4, 3.9))
n, edges, _ = ax.hist(Dm, bins=140, color=BLUE, alpha=.85, edgecolor='white', lw=.3,
                      label=f'the margin as it actually is, sd {obs:,.0f}')
w = edges[1] - edges[0]
xs = np.linspace(Dm.min(), Dm.max(), 700)
ax.plot(xs, len(Dm)*w*stats.norm.pdf(xs, 0, indep), color=ORANGE, lw=2.2,
        label=f'if the two banks were independent, sd {indep:,.0f}')
ax.set_xlabel("seat 0's bank minus seat 1's")
ax.legend(frameon=False, fontsize=9)
tidy(ax, 'episodes', "The episode's own difficulty cancels out of the difference")
plt.tight_layout(); plt.show()

W, Lo = np.maximum(b0, b1), np.minimum(b0, b1)
g = np.random.default_rng(7)
ctrl = np.maximum(g.normal(M.mean(), M.std(), len(b0)),
                  g.normal(M.mean(), M.std(), len(b0)))

fig, axes = plt.subplots(1, 3, figsize=(11.6, 3.8))
for ax, (v, lab, col) in zip(axes, [(W, "the winner's bank", BLUE),
                                    (M, "one agent's bank", AQUA),
                                    (Dm, 'the margin', ORANGE)]):
    ax.hist(v, bins=80, color=col, alpha=.85, edgecolor='white', lw=.3)
    ax.set_xlabel(lab)
    tidy(ax, 'episodes' if ax is axes[0] else None,
         f'skew {stats.skew(v):+.2f}   excess kurtosis {stats.kurtosis(v):+.2f}')
plt.tight_layout(); plt.show()

print("CONTROL, the max of two INDEPENDENT NORMALS with this mean and spread:")
print(f"  skew {stats.skew(ctrl):+.3f}, and it fails D'Agostino at "
      f"p = {stats.normaltest(ctrl)[1]:.1e}")
print("  so a bell-shaped winner's histogram says nothing about the parent.\n")
print(f"{'':<21}{'skew':>9}{'excess kurtosis':>18}")
for v, lab in ((M, "one agent's bank"), (W, "the winner's bank"),
               (Lo, "the loser's bank"), (Dm, 'the margin')):
    print(f"{lab:<21}{stats.skew(v):>9.3f}{stats.kurtosis(v):>18.3f}")
print(f"\nstandard error of skew at n = {len(Dm):,} is {math.sqrt(6/len(Dm)):.4f},")
print("so a skew of 0.1 is ten standard errors and still invisible on a chart.")

fig, axes = plt.subplots(1, 3, figsize=(11.6, 3.9))
for ax, (v, lab) in zip(axes, [(W, "the winner's bank"), (M, "one agent's bank"),
                               (Dm, 'the margin')]):
    z = (v - v.mean()) / v.std(ddof=1)
    q = np.linspace(.0005, .9995, 900)
    ax.plot(stats.norm.ppf(q), np.quantile(z, q), color=BLUE, lw=2)
    ax.plot([-4, 4], [-4, 4], color=ORANGE, lw=1.4, ls='--')
    ax.set_xlim(-4, 4); ax.set_ylim(-4, 4); ax.set_aspect('equal')
    ax.set_xlabel('normal quantile')
    tidy(ax, 'observed quantile' if ax is axes[0] else None, lab)
plt.tight_layout(); plt.show()

import warnings
sm = np.random.default_rng(3)
print(f"{'':<21}{'D Agostino p':>15}{'Anderson A2':>14}{'Shapiro p':>13}")
with warnings.catch_warnings():
    warnings.simplefilter('ignore')      # scipy deprecation on anderson's API
    for v, lab in ((M, "one agent's bank"), (W, "the winner's bank"),
                   (Dm, 'the margin')):
        print(f"{lab:<21}{stats.normaltest(v)[1]:>15.2e}"
              f"{stats.anderson(v, 'norm').statistic:>14,.1f}"
              f"{stats.shapiro(sm.choice(v, 4500, replace=False)).pvalue:>13.2e}")
print("\nAll of them reject. That is the sample size talking, not the data.\n")

# WHERE does the heavy tail come from? The obvious guess is agents that broke.
# Test it rather than assert it: compare the loser's bank in the extreme
# margins against the loser's bank everywhere.
Lo_all = np.minimum(b0, b1)
big = np.abs(Dm) > 3 * Dm.std(ddof=1)
for thr in (1_000, 10_000):
    print(f"  loser banks under ${thr:,}:  {100*(Lo_all[big] < thr).mean():5.1f} % of the "
          f"{int(big.sum()):,} margins beyond 3 sd,  against "
          f"{100*(Lo_all < thr).mean():.1f} % of all episodes")

# Built episode by episode, NOT seat 0's games then seat 1's, so that each
# submission's series stays in the order it was played. Section 5's last chart
# measures a serial correlation and would be wrong under any other order.
per_sub = {}
for a, b, d in zip(sub0, sub1, Dm):
    per_sub.setdefault(a, []).append(d)
    per_sub.setdefault(b, []).append(-d)

MIN_EP = 40
pred, obsr, shap = [], [], []
for s, v in per_sub.items():
    a = np.array(v, dtype=float)
    if len(a) < MIN_EP or a.std(ddof=1) == 0:
        continue
    pred.append(stats.norm.cdf(a.mean() / a.std(ddof=1)))
    obsr.append((a > 0).mean())
    shap.append(stats.shapiro(a).pvalue)
pred, obsr, shap = np.array(pred), np.array(obsr), np.array(shap)
err = obsr - pred

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.3))
ax.scatter(pred, obsr, s=24, color=BLUE, alpha=.55, lw=0)
ax.plot([0, 1], [0, 1], color=ORANGE, lw=1.6, ls='--')
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
ax.set_xlabel('win rate the normal predicts')
tidy(ax, 'win rate actually achieved',
     f'{len(pred)} submissions with {MIN_EP}+ games   r = {stats.pearsonr(pred,obsr)[0]:.3f}')

ax2.hist(err, bins=34, color=AQUA, alpha=.88, edgecolor='white', lw=.4)
ax2.axvline(0, color=ORANGE, lw=1.8)
ax2.set_xlabel('observed minus predicted win rate')
tidy(ax2, 'submissions', f'Median absolute error {np.median(np.abs(err)):.3f}')
plt.tight_layout(); plt.show()

print(f"Shapiro-Wilk rejects normality for {100*(shap<0.05).mean():.1f} % of these "
      f"submissions (5 % is what an exactly normal world gives)")
print("and yet the normal approximation delivers:")
print(f"  correlation predicted vs achieved   {stats.pearsonr(pred, obsr)[0]:.3f}")
print(f"  mean signed error                   {err.mean():+.4f}")
print(f"  median absolute error               {np.median(np.abs(err)):.4f}")
print(f"  within 10 points                    {100*(np.abs(err)<.10).mean():.1f} %")

lag1, runs_p = [], []
for s, v in per_sub.items():
    a = np.array(v, dtype=float)
    if len(a) < MIN_EP or a.std() == 0:
        continue
    lag1.append(np.corrcoef(a[:-1], a[1:])[0, 1])
    sg = a > 0
    n1, n0 = int(sg.sum()), int((~sg).sum())
    if n1 > 1 and n0 > 1:
        runs = 1 + int((sg[1:] != sg[:-1]).sum())
        mu = 2*n1*n0/(n1+n0) + 1
        var = (mu-1)*(mu-2)/(n1+n0-1)
        if var > 0:
            runs_p.append(2*stats.norm.sf(abs((runs-mu)/math.sqrt(var))))
lag1, runs_p = np.array(lag1), np.array(runs_p)

fig, ax = plt.subplots(figsize=(8.4, 3.8))
ax.hist(lag1, bins=34, color=BLUE, alpha=.88, edgecolor='white', lw=.4)
ax.axvline(0, color=MUTED, lw=1.2, ls=':')
ax.axvline(np.median(lag1), color=ORANGE, lw=2.2)
ax.text(np.median(lag1)+.02, ax.get_ylim()[1]*.86, f'median {np.median(lag1):+.2f}',
        color=ORANGE, fontweight='bold', fontsize=10)
ax.text(0.01, ax.get_ylim()[1]*.28, 'independent\nwould sit here', color=MUTED,
        fontsize=9, ha='left')
ax.set_xlabel("correlation between a submission's margin and the next one")
tidy(ax, 'submissions', 'Consecutive episodes are not independent draws')
plt.tight_layout(); plt.show()

print(f"median lag-1 autocorrelation of the margin: {np.median(lag1):+.3f}")
print(f"a runs test on the sign rejects independence for {100*(runs_p<0.05).mean():.1f} % "
      f"of submissions, against the 5 % expected if they were independent")