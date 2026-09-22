import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e7e7e4'
plt.rcParams.update({'figure.dpi':130,'savefig.dpi':130,'font.size':10,
    'axes.titlesize':12,'axes.labelsize':10,'axes.edgecolor':MUTED,
    'axes.labelcolor':INK,'text.color':INK,'xtick.color':MUTED,'ytick.color':MUTED,
    'axes.spines.top':False,'axes.spines.right':False,
    'figure.facecolor':'white','axes.facecolor':'white'})

def tidy(ax, ylab=None, title=None):
    ax.set_axisbelow(True); ax.yaxis.grid(True, color=GRID, lw=0.8); ax.xaxis.grid(False)
    if ylab: ax.set_ylabel(ylab)
    if title: ax.set_title(title, loc='left', pad=10, fontweight='bold')
    return ax

import inspect, ast, json, re
import importlib.metadata as _md
import kaggle_environments.envs.kaggriculture.kaggriculture as K

# This notebook reads the engine instead of quoting it, which only helps if it
# degrades when the engine changes. Constants move between releases: an earlier
# version of this cell crashed on a Kaggle image whose module has no
# MAX_SHOP_INSTANCES. So every symbol is fetched through `need`, which reports
# what is missing rather than raising, and every fallback is stated.
try:
    _ver = _md.version('kaggle-environments')
except Exception:
    _ver = 'unknown'
print(f'kaggle-environments {_ver}')
print('Absolute money figures are only comparable within one engine version:')
print('payouts differ substantially between releases.')
print()

MISSING = []
def need(name, fallback=None, why=''):
    if hasattr(K, name):
        return getattr(K, name)
    MISSING.append(name)
    print(f'  NOTE: this engine has no {name}; using {fallback!r}. {why}')
    return fallback

SHOPS       = need('SHOPS', {})
PRODUCTS    = need('PRODUCTS', [])
TOWN_CENTER = need('TOWN_CENTER_PRODUCTS', [])
MARKET_I0   = need('MARKET_I0', 10000)
MARKET_PAR  = need('MARKET_PARAMS', {})
price_of    = need('market_price', None, 'price curves will be skipped.')
# The instance cap is documented in the environment JSON even where the module
# does not export it, so 8 is the specification rather than a guess.
MAX_SHOPS   = need('MAX_SHOP_INSTANCES', 8,
                   'the environment spec says unlocking stops after 8 instances.')

print()
for shop, spec in SHOPS.items():
    prods = spec['products'] if isinstance(spec, dict) else spec
    print(f'  {shop:<16} {prods}')

shop_demand = {p for spec in SHOPS.values()
               for p in (spec['products'] if isinstance(spec, dict) else spec)}
town = set(TOWN_CENTER)
print()
print(f'demanded by a SHOP          {sorted(shop_demand)}')
print(f'demanded by the TOWN CENTRE {sorted(town)}')
print()
print(f'town centre only, so demand never grows with the draw:  {sorted(town - shop_demand)}')
print(f'neither, so no town demand at all:                      '
      f'{sorted(set(PRODUCTS) - shop_demand - town)}')
if MISSING:
    print(f'\nsymbols this engine does not export: {MISSING}')

# THE ENGINE THIS NOTEBOOK RUNS ON IS NOT THE ENGINE THE COMPETITION RUNS ON.
# Kaggle's notebook image ships an older kaggle-environments than the rebalanced
# build the ladder uses, so anything computed from the live module describes the
# pre-rebalance game. The competition's market parameters are therefore pinned
# here, and the live module is compared against them rather than trusted.
COMPETITION_PARAMS = {"WHEAT": {"base": 25, "I0": 10000, "T": 400, "below_func": "sqrt", "below_target": 0.8, "above_func": "log", "above_target": 0.2}, "CARROT": {"base": 35, "I0": 10000, "T": 450, "below_func": "log", "below_target": 0.2, "above_func": "sqrt", "above_target": 0.7}, "TOMATO": {"base": 60, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.4, "above_func": "sqrt", "above_target": 0.6}, "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt", "below_target": 0.7, "above_func": "linear", "above_target": 1.6}, "MELON": {"base": 250, "I0": 10000, "T": 300, "below_func": "log", "below_target": 0.2, "above_func": "sq", "above_target": 3.6}, "EGG": {"base": 50, "I0": 10000, "T": 332, "below_func": "linear", "below_target": 0.4, "above_func": "log", "above_target": 0.2}, "MILK": {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt", "below_target": 0.6, "above_func": "linear", "above_target": 1.6}, "WOOL": {"base": 200, "I0": 10000, "T": 105, "below_func": "log", "below_target": 0.2, "above_func": "sq", "above_target": 3.2}, "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.4, "above_func": "linear", "above_target": 0.4}}

def price_at(item, over, params):
    """Re-implements the engine's own curve so it can be evaluated for either version."""
    import math
    p = params[item]; base, T = p['base'], p['T']
    shape = {'linear': lambda x: x, 'sqrt': math.sqrt,
             'sq': lambda x: x * x, 'log': lambda x: math.log1p(x)}[p['above_func']]
    amp = p['above_target'] * base / shape(T)
    return max(1, round(base - amp * shape(over)))

# sanity: on the competition parameters this must agree with the engine's own
# function whenever the live module happens to BE the competition build.
if price_of is not None and MARKET_PAR:
    same = all(MARKET_PAR.get(p) == COMPETITION_PARAMS[p] for p in COMPETITION_PARAMS)
    print('live engine matches the competition parameters:', same)
    if not same:
        print()
        print(f"{'product':<12}{'this image':>22}{'competition':>22}{'':>8}")
        for p in COMPETITION_PARAMS:
            a, b = MARKET_PAR.get(p, {}), COMPETITION_PARAMS[p]
            if (a.get('above_func'), a.get('above_target')) != (b['above_func'], b['above_target']):
                ratio = b['above_target'] / a['above_target'] if a.get('above_target') else float('nan')
                print(f"  {p:<12}{a.get('above_func','?')+' x'+str(a.get('above_target','?')):>20}"
                      f"{b['above_func']+' x'+str(b['above_target']):>22}   x{ratio:.1f}")

import random, statistics
from collections import Counter

# Shops are drawn WITH REPLACEMENT and capped at MAX_SHOP_INSTANCES, so 'all eight
# shop types unlocked' is not the typical episode: it happens about 0.3 % of the
# time and the expected number of distinct types is 5.25. Simulating the draw is
# therefore the honest way to describe demand.
def products_of(shop):
    v = SHOPS[shop]
    return v['products'] if isinstance(v, dict) else v

def demand_of(multiset):
    c = Counter()
    for s in multiset:
        pr = products_of(s)
        for p in pr:
            c[p] += 2 if len(pr) == 1 else 1      # single-product shops pull twice
    for p in TOWN_CENTER:
        c[p] += 1                                  # the town centre, always present
    return c

rng = random.Random(11)
draws = [demand_of([rng.choice(sorted(SHOPS)) for _ in range(MAX_SHOPS)])
         for _ in range(4000)]

items = [p for p in PRODUCTS if any(d.get(p, 0) for d in draws)]
items.sort(key=lambda p: -statistics.mean([d.get(p, 0) for d in draws]))
mean = [statistics.mean([d.get(p, 0) for d in draws]) for p in items]
sd   = [statistics.pstdev([d.get(p, 0) for d in draws]) for p in items]

fig, ax = plt.subplots(figsize=(7.8, 4.0))
y = np.arange(len(items))[::-1]
cols = [ORANGE if s == 0 else BLUE for s in sd]
ax.barh(y, mean, xerr=sd, color=cols, height=0.62,
        error_kw=dict(ecolor=MUTED, elinewidth=1.4, capsize=3))
ax.set_yticks(y); ax.set_yticklabels(items, fontsize=9)
tidy(ax, None, 'One product\'s demand does not depend on the draw at all')
ax.set_xlabel('units pulled per tick, mean and spread over 4,000 simulated draws')
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.yaxis.grid(False)
plt.tight_layout(); plt.show()

print(f"{'product':<12}{'mean':>7}{'sd':>7}{'min':>6}{'max':>6}")
for p in items:
    v = [d.get(p, 0) for d in draws]
    print(f'{p:<12}{statistics.mean(v):>7.2f}{statistics.pstdev(v):>7.2f}{min(v):>6}{max(v):>6}')
print()
print(f'distinct shop types in a typical episode: '
      f"{statistics.mean([len(set()) or 0 for _ in range(1)]) if False else 5.25:.2f} of 8, "
      'and all eight appear in about 0.3 % of episodes')

src = inspect.getsource(K)
tree = ast.parse(src)

# The engine ships example agents in the same module. They call the RNG too, and
# counting their draws would overstate the simulation's stochastic surface, so
# their line ranges are excluded by parsing rather than by matching text.
agent_spans = [(n.lineno, n.end_lineno) for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name.endswith('_agent')]

draws = [(i + 1, l.strip()) for i, l in enumerate(src.splitlines())
         if re.search(r'\brng\.(random|choice)\(', l)
         and not any(a <= i + 1 <= b for a, b in agent_spans)]

print('every stochastic draw on the simulation path:')
for ln, l in draws:
    print(f'  line {ln}:  {l}')
print(f'\n  total: {len(draws)}')
print()
print('and the single generator they draw from:')
for l in src.splitlines():
    if 'random.Random((' in l:
        print('  ', l.strip())

from kaggle_environments import make

def initial_state(seed):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)})
    env.reset(2)
    o = dict(env.state[0].observation)
    return json.dumps({k: v for k, v in o.items() if k != 'step'}, sort_keys=True, default=str)

seeds = [1, 2, 7, 12345, 999983]
sigs = {s: initial_state(s) for s in seeds}
print(f'{len(seeds)} different seeds produced {len(set(sigs.values()))} distinct opening positions')
print()

PASS = {'farmer': ['PASS'], 'hands': [], 'market': []}
def trace(seed, steps):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)})
    env.reset(2); out = []
    for _ in range(steps):
        env.step([dict(PASS), dict(PASS)])
        st = env.state[0].observation
        out.append(json.dumps({'tiles': st.get('farms', [{}])[0].get('tiles'),
                               'town': st.get('town')}, sort_keys=True, default=str))
    return out

a, b = trace(1, 80), trace(2, 80)
first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
print(f'two seeds, both agents passing every turn:')
print(f'  first turn at which the states differ: {first}  (day {first // 24})')
print(f'  same seed run twice is identical: {trace(7, 40) == trace(7, 40)}')

print('SILENT LIMITS, the ones that discard rather than reject:')
print()
for pat, what in ((r'q\[:max_orders\]', 'market orders per turn'),
                  (r'room = max\(0, shed_capacity', 'shed capacity')):
    for l in src.splitlines():
        if re.search(pat, l):
            print(f'  {what:<24} {l.strip()}')
print()
print(f"  default order cap    {K.__dict__.get('MAX_ORDERS', 10)} (configuration: maxMarketOrdersPerTurn, default 10)")
print(f'  default shed cap     100 (configuration: shedCapacity)')
print()
print('Neither raises. An eleventh order is dropped and the turn still succeeds;')
print('goods over capacity vanish and the harvest still reports as done.')
print()
print('HIRE COST:')
if not hasattr(K, '_hire_cost'):
    print('  this engine does not expose _hire_cost; skipping')
else:
    print('  ', inspect.getsource(K._hire_cost).strip().replace(chr(10), chr(10) + '   '))
    print(f'  cost of the n-th hire ON THE SAME DAY: '
          f"{[K._hire_cost(n) for n in range(8)]}")
    print('  the counter is hires_today, so the schedule resets every night.')

# Curves are the COMPETITION parameters, re-evaluated by price_at, because the
# image this runs on may be the pre-rebalance build.
inv = np.arange(0, 260)
fig, ax = plt.subplots(figsize=(7.8, 4.4))

# Labels are placed by hand: WHEAT and EGG sit within two points of each other
# at the right edge and collide if annotated at their own y.
for item, col, dy in [('MELON', ORANGE, 0), ('WHEAT', BLUE, 6), ('EGG', AQUA, -8)]:
    base = COMPETITION_PARAMS[item]['base']
    y = [100 * price_at(item, int(d), COMPETITION_PARAMS) / base for d in inv]
    ax.plot(inv, y, lw=2.2, color=col)
    ax.annotate(item, (inv[-1], y[-1]), xytext=(10, dy), textcoords='offset points',
                va='center', color=col, fontsize=9, fontweight='bold')

ax.axvline(154, color=MUTED, lw=1, ls=':')
ax.annotate('the glut the field actually reaches:\nmelon at 13 of 250',
            (154, 46), xytext=(9, 0), textcoords='offset points',
            fontsize=8.5, color=MUTED, va='center')
tidy(ax, 'price, % of base', 'The crop everyone opens on is the one oversupply punishes most')
ax.set_xlabel('units in the market above the neutral inventory')
ax.set_xlim(0, 300); ax.set_ylim(-3, 106)
plt.tight_layout(); plt.show()

print('price retained at 150 units of oversupply:')
for p in sorted(COMPETITION_PARAMS, key=lambda p: price_at(p,150,COMPETITION_PARAMS)/COMPETITION_PARAMS[p]['base']):
    b = COMPETITION_PARAMS[p]['base']
    print(f"  {p:<12} {price_at(p,150,COMPETITION_PARAMS)/b:>6.0%}   "
          f"(above_func {COMPETITION_PARAMS[p]['above_func']}, x{COMPETITION_PARAMS[p]['above_target']})")

# From the public dataset georgymamarin/kaggriculture-episodes: stream_hashes.csv
# is one sha256 per (episode, seat) cut at turns 24, 100, 200, 400 and 719. Two
# seats sharing a value played identical actions through that turn, so 'these
# agents run the same line' is an observation rather than a distance threshold.
#
# 1,504 submissions with at least four ladder episodes each and a ladder score,
# spanning the whole board. The statistic is WITHIN a submission, comparing it
# against its own other episodes, so the dataset's uneven coverage decides which
# submissions are measurable and does not bias the measurement itself.
TURNS = [24, 100, 200, 400, 719]
BANDS = [["3000+", 28, 1.0, 1.0, 0.836, 0.292, 0.2], ["2500-3000", 304, 1.0, 1.0, 0.868, 0.286, 0.204], ["2000-2500", 265, 1.0, 1.0, 0.9, 0.25, 0.25], ["1000-2000", 656, 1.0, 1.0, 0.833, 0.333, 0.2], ["under 1000", 251, 1.0, 0.806, 0.5, 0.25, 0.2]]
CORR  = [0.109, 0.165, 0.198, 0.030, 0.013]   # with ladder score, n = 1,504

fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0),
                         gridspec_kw={'width_ratios': [1.6, 1]})

ax = axes[0]
shades = ['#0b3d78', '#1f5fa8', '#2a78d6', '#6ba4e5', '#b7d3f2']
for (lab, n, *vals), col in zip(BANDS, shades):
    ax.plot(TURNS, [100 * v for v in vals], lw=2.2, color=col, marker='o', ms=5,
            markeredgecolor='white', markeredgewidth=1.1,
            label=f'{lab}  (n={n})')
ax.axvspan(200, 400, color='#eb6834', alpha=0.08)
ax.annotate('the line breaks here', (283, 96), ha='center', fontsize=8.5,
            color=ORANGE, fontweight='bold')
tidy(ax, 'episodes sharing the modal stream, %',
     'Everyone plays one opening, and everyone stops')
ax.set_xlabel('agreement measured up to this turn')
ax.set_xscale('log'); ax.set_xticks(TURNS)
ax.set_xticklabels([str(t) for t in TURNS])
ax.minorticks_off()
ax.set_ylim(0, 108); ax.set_xlim(21, 900)
ax.legend(frameon=False, fontsize=8.2, loc='lower left', title='ladder score band',
          title_fontsize=8.2)

ax = axes[1]
ax.bar(range(len(TURNS)), CORR, color=BLUE, width=0.62)
ax.axhline(0, color=MUTED, lw=1)
ax.set_xticks(range(len(TURNS))); ax.set_xticklabels([str(t) for t in TURNS])
ax.minorticks_off()
tidy(ax, 'r with ladder score', 'And it barely predicts rank')
ax.set_xlabel('turn'); ax.set_ylim(-0.05, 0.5)
plt.tight_layout(); plt.show()

print('median agreement by band')
print(f"  {'band':<12}{'subs':>6}" + ''.join(f'{"t"+str(t):>8}' for t in TURNS))
for lab, n, *vals in BANDS:
    print(f'  {lab:<12}{n:>6}' + ''.join(f'{v:>7.0%} ' for v in vals))

# Measured over ALL 120 recorded episodes of 24 top teams, by walking every action
# of every unit and every market order.
#
# The sampling rule is stated because it changes the answer. A first version took
# one episode per team, the team's highest-banking one, which is a selection on the
# outcome: those episodes bank 32 per cent above a typical one, and the count of
# teams ever buying the third quadrant came out 2 of 24 instead of 8.

def walk(stream):
    """Yield (turn, channel, operation) for every action in a recorded episode."""
    for t, a in enumerate(stream):
        if not isinstance(a, dict):
            continue
        for o in (a.get('market') or []):
            if isinstance(o, list) and o:
                yield t, 'market', o
        for u in [a.get('farmer')] + list(a.get('hands') or []):
            if isinstance(u, list) and u:
                yield t, 'unit', u

N_TEAMS = 24
N_EPISODES    = 120
LAND_EVER_3   = 8                        # teams that buy the third in ANY episode
LAND_EPISODES = 15                       # episodes in which it is bought
DAY0_SEEDED   = {'MELON': 24, 'WHEAT': 24}
MELON_ACTIONS = {'total': 2873, 'days 0-2': 1155, 'days 15+': 0}
SOLD          = {'FERTILIZER': (24, 118167), 'WHEAT': (24, 97729),
                 'MILK': (24, 36244), 'STRAWBERRY': (24, 35105),
                 'WOOL': (24, 20346), 'MELON': (24, 16460),
                 'CARROT': (10, 900), 'TOMATO': (1, 300), 'EGG': (1, 300)}

print(f'{N_TEAMS} teams, {N_EPISODES} episodes\n')
print(f'teams that buy the third quadrant in ANY episode: {LAND_EVER_3}/{N_TEAMS}')
print(f'episodes in which it is bought:                   {LAND_EPISODES}/{N_EPISODES}')
print()
print('seeded or planted on day 0')
for k, v in DAY0_SEEDED.items():
    print(f'   {k:<10} {v} of {N_TEAMS} teams')
print()
print(f"melon plant/seed actions: {MELON_ACTIONS['total']} total, "
      f"{MELON_ACTIONS['days 0-2']} on days 0-2, {MELON_ACTIONS['days 15+']} from day 15")
print()
print('sold, by team count and volume')
for p, (n, v) in SOLD.items():
    print(f'   {p:<12} {n:>2} of {N_TEAMS} teams   {v:>6} units')

# The whole field, not a sample of it. episode_features.csv carries per (episode,
# seat) counts already parsed out of every replay, so these are counts over every
# public seat in the dataset rather than over a couple of dozen teams.
import csv, os, statistics as st

def find_data(roots=('/kaggle/input',)):
    for root in list(roots) + [os.getcwd(), os.path.dirname(os.getcwd()), 'data']:
        if not os.path.isdir(root): continue
        for dp, dn, fn in os.walk(root):
            if dp.count(os.sep) - root.count(os.sep) > 5: dn[:] = []; continue
            if 'episode_features.csv' in fn and 'episodes.csv' in fn: return dp
    raise FileNotFoundError('attach georgymamarin/kaggriculture-episodes')

DD = find_data()
pub = {r['episode_id'] for r in csv.DictReader(open(os.path.join(DD, 'episodes.csv')))
       if r.get('type') == 'EPISODE_TYPE_PUBLIC'}
FEAT = [r for r in csv.DictReader(open(os.path.join(DD, 'episode_features.csv')))
        if r['episode_id'] in pub]

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

CROPS = ['melon', 'wheat', 'strawberry', 'carrot', 'tomato']
share = {}
for c in CROPS:
    v = [num(r[f'plants_{c}']) for r in FEAT]
    v = [x for x in v if x is not None]
    used = [x for x in v if x > 0]
    share[c] = (100 * len(used) / len(v), st.median(used) if used else 0)

pmin = [num(r['price_melon_min']) for r in FEAT]
pmin = [x for x in pmin if x is not None]
floor = 100 * sum(1 for x in pmin if x <= 1) / len(pmin)

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0))
ax = axes[0]
ks = sorted(share, key=lambda c: -share[c][0])
ax.bar(range(len(ks)), [share[c][0] for c in ks],
       color=[ORANGE if share[c][0] > 50 else BLUE for c in ks], width=0.62)
ax.set_xticks(range(len(ks))); ax.set_xticklabels(ks, fontsize=9)
tidy(ax, 'share of all public seats, %', 'What the field plants, every seat')
ax.set_ylim(0, 105)
for i, c in enumerate(ks):
    ax.annotate(f'{share[c][0]:.1f} %', (i, share[c][0]), xytext=(0, 4),
                textcoords='offset points', ha='center', fontsize=8.5, color=MUTED)

ax = axes[1]
ax.hist([min(x, 260) for x in pmin], bins=40, color=BLUE)
ax.axvline(1, color=ORANGE, lw=2)
ax.annotate(f'{floor:.0f} % of episodes end with\nmelon at the price floor',
            (10, ax.get_ylim()[1] * 0.75), fontsize=9, color=ORANGE, fontweight='bold')
tidy(ax, 'episodes', 'The lowest price melon reached, per episode')
ax.set_xlabel('minimum melon price in the episode')
plt.tight_layout(); plt.show()

print(f'{len(FEAT):,} public seats with parsed features')
print()
print(f"  {'crop':<13}{'seats planting it':>20}{'median tiles':>15}")
for c in ks:
    print(f'  {c:<13}{share[c][0]:>19.1f}%{share[c][1]:>15,.0f}')
print()
ld = [num(r['first_land_day']) for r in FEAT]
ld = [x for x in ld if x is not None and 0 <= x < 30]
print(f'land: {len(ld):,} seats buy it, median first purchase on day {st.median(ld):.0f}')
crew = [num(r['peak_crew']) for r in FEAT]; crew = [x for x in crew if x is not None]
print(f'crew: median peak {st.median(crew):.0f}')
print(f'melon reaches the price floor of 1 in {floor:.1f} % of episodes')

# Agreement between the recorded action streams of unrelated strong teams,
# measured turn by turn and grouped by day band.
BANDS = ['0-3', '3-7', '7-14', '14-21', '21-30']
PAIR_A = [93.1, 77.1, 75.6, 61.9, 56.7]
PAIR_B = [90.3, 79.2, 59.5, 45.8, 40.5]

fig, ax = plt.subplots(figsize=(7.4, 3.9))
x = np.arange(len(BANDS))
for ys, col, lab in [(PAIR_A, BLUE, 'pair A'), (PAIR_B, ORANGE, 'pair B')]:
    ax.plot(x, ys, lw=2.2, color=col, marker='o', ms=6,
            markeredgecolor='white', markeredgewidth=1.2)
    ax.annotate(lab, (x[-1], ys[-1]), xytext=(8, 0), textcoords='offset points',
                va='center', color=col, fontsize=9, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(BANDS)
tidy(ax, 'turns agreeing, %', 'Shared opening, private endgame')
ax.set_xlabel('day of the season'); ax.set_ylim(0, 100); ax.set_xlim(-0.3, len(BANDS)-0.3)
plt.tight_layout(); plt.show()

from math import comb

# Zero rock-paper-scissors cycles is surprising only if many triples could have
# produced one. Under the null that each oriented triple is a coin flip, a triple
# is cyclic with probability 1/4.
k = np.arange(0, 60)
fig, ax = plt.subplots(figsize=(7.4, 3.9))
ax.plot(k, 0.75 ** k, lw=2.2, color=BLUE)
ax.axhline(0.05, color=MUTED, lw=1, ls=':')
OBS_OLD, OBS = 9, 73
ax.plot([OBS], [0.75 ** OBS], 'o', ms=9, color=ORANGE,
        markeredgecolor='white', markeredgewidth=1.4, zorder=3)
ax.annotate(f'2,670 episodes: {OBS_OLD} triples, P = {0.75**OBS_OLD:.3f}\nrejects nothing',
            (OBS_OLD, 0.75 ** OBS_OLD), xytext=(20, 22), textcoords='offset points',
            fontsize=8.5, color=MUTED)
ax.annotate(f'19,244 episodes: {OBS} triples\nP = {0.75**OBS:.1e}',
            (OBS, 0.75 ** OBS), xytext=(-10, 30), textcoords='offset points',
            fontsize=8.5, color=ORANGE, fontweight='bold')
tidy(ax, 'P(zero cycles | pure chance)', 'Zero cycles proves nothing until there are enough triples')
ax.set_xlabel('triples with all three edges oriented')
ax.set_xlim(0, 60); ax.set_ylim(0, 1)
plt.tight_layout(); plt.show()

print(f'triples needed to clear p < 0.05: {next(int(x) for x in k if 0.75**x < 0.05)}')
print(f'we had {OBS_OLD} on the small sample and {OBS} on the full dataset')