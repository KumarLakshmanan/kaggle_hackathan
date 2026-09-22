# Chart style, matched to the companion notebooks: recessive axes, a light
# horizontal grid, nothing decorative. Colour is assigned by the job it does.
import csv, math, os
import numpy as np
import matplotlib.pyplot as plt

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
    """Walk for episodes.csv rather than guessing Kaggle's mount depth, which
    is not fixed: it can appear at /kaggle/input/<slug>/ or deeper."""
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
    here = os.path.abspath(os.getcwd())
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
    raise FileNotFoundError(
        'episodes.csv not found. Attach georgymamarin/kaggriculture-episodes.')

BASE = find_data()
print('dataset:', BASE)

# Quoted from kaggle_environments/envs/kaggriculture/kaggriculture.py
MARKET_I0, PRICE_FLOOR = 10000, 1

# THE BUILD MATTERS HERE, so both parameter sets are carried and the notebook
# says which one it is using. Kaggle rebalanced carrot, tomato and egg on
# 2026-08-15 (1.32.7): their scarcity branch became a `hinge`, linear up to a
# knee at T and quadratic past it, and carrot's below_target went 0.20 -> 1.00.
# Nothing else moved. A ceiling quoted without its build is not a number.
MARKET_PARAMS = {
 'WHEAT':      dict(base= 25, T=400, below='sqrt',   below_t=0.80, above='log',    above_t=0.20),
 'CARROT':     dict(base= 35, T=450, below='hinge',  below_t=1.00, above='sqrt',   above_t=0.70),
 'TOMATO':     dict(base= 60, T=200, below='hinge',  below_t=0.40, above='sqrt',   above_t=0.60),
 'STRAWBERRY': dict(base=120, T=100, below='sqrt',   below_t=0.70, above='linear', above_t=1.60),
 'MELON':      dict(base=250, T=300, below='log',    below_t=0.20, above='sq',     above_t=3.60),
 'EGG':        dict(base= 50, T=332, below='hinge',  below_t=0.40, above='log',    above_t=0.20),
 'MILK':       dict(base=160, T=122, below='sqrt',   below_t=0.60, above='linear', above_t=1.60),
 'WOOL':       dict(base=200, T=105, below='log',    below_t=0.20, above='sq',     above_t=3.20),
 'FERTILIZER': dict(base=100, T=200, below='linear', below_t=0.40, above='linear', above_t=0.40),
}
PARAMS_1326 = {k: dict(v) for k, v in MARKET_PARAMS.items()}   # the pre-change rows
PARAMS_1326['CARROT'].update(below='log',    below_t=0.20)
PARAMS_1326['TOMATO'].update(below='linear', below_t=0.40)
PARAMS_1326['EGG'].update(below='linear',    below_t=0.40)
HINGE_GAIN = 8.0
PRODUCTS = list(MARKET_PARAMS)
TOWN_CENTER = [g for g in PRODUCTS if g != 'FERTILIZER']

SHOPS = {
 'BAKERY':         ['EGG', 'WHEAT'],
 'PIZZA_SHOP':     ['MILK', 'TOMATO', 'WHEAT'],
 'BRUNCH_SPOT':    ['EGG', 'WHEAT', 'STRAWBERRY'],
 'YARN_STORE':     ['WOOL'],
 'ICE_CREAM_SHOP': ['STRAWBERRY', 'MILK', 'WHEAT'],
 'PET_CAFE':       ['CARROT'],
 'SMOOTHIE_SHOP':  ['STRAWBERRY', 'MILK'],
 'FARMERS_MARKET': ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'],
}
CROPS = {   # seed cost, first yield day, max yield day, interval, units, ongoing
 'WHEAT':      dict(seed= 10, first=2,  maxday= 4, interval=0, yld=6, ongoing=False),
 'CARROT':     dict(seed= 20, first=2,  maxday= 3, interval=0, yld=4, ongoing=False),
 'TOMATO':     dict(seed= 50, first=8,  maxday= 8, interval=1, yld=4, ongoing=True),
 'STRAWBERRY': dict(seed=100, first=10, maxday=10, interval=2, yld=4, ongoing=True),
 'MELON':      dict(seed= 80, first=10, maxday=12, interval=0, yld=6, ongoing=False),
}
STEPS, TURNS_PER_DAY = 720, 24
DAYS = STEPS // TURNS_PER_DAY

def shape(f, x, T=None):
    x = max(0.0, x)
    if f == 'hinge':                       # added in 1.32.7
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return {'linear': x, 'sq': x * x, 'sqrt': math.sqrt(x), 'log': math.log1p(x)}[f]

def price(good, inventory, params=None):
    p = (params or MARKET_PARAMS)[good]
    if inventory < MARKET_I0:
        amp = p['below_t'] * p['base'] / shape(p['below'], p['T'], p['T'])
        v = p['base'] + amp * shape(p['below'], MARKET_I0 - inventory, p['T'])
    else:
        amp = p['above_t'] * p['base'] / shape(p['above'], p['T'], p['T'])
        v = p['base'] - amp * shape(p['above'], inventory - MARKET_I0, p['T'])
    return max(PRICE_FLOOR, int(round(v)))

# Which build is the reader actually on? A behavioural check beats a version
# string, because a string can agree while the physics differ.
try:
    from kaggle_environments.envs.kaggriculture import kaggriculture as _K
    _live = _K.market_price('CARROT', MARKET_I0 - 1000)
    _new, _old = price('CARROT', MARKET_I0 - 1000), price('CARROT', MARKET_I0 - 1000, PARAMS_1326)
    print(f"installed engine prices carrot at 1,000 short: ${_live}"
          f"   (1.32.7 says ${_new}, 1.32.6 says ${_old})")
    print("=> this session is on",
          "1.32.7 or later" if _live == _new else
          "1.32.6 or earlier" if _live == _old else "an engine neither set describes")
except Exception:
    print("no engine installed; the arithmetic below carries its own constants")

print(f'{DAYS} days of {TURNS_PER_DAY} turns.')
print(f"melon at par ${price('MELON', MARKET_I0)}, "
      f"after 100 sold ${price('MELON', MARKET_I0 + 100)}, "
      f"after 200 ${price('MELON', MARKET_I0 + 200)}")
print(f"wheat at par ${price('WHEAT', MARKET_I0)}, "
      f"after 100 ${price('WHEAT', MARKET_I0 + 100)}, "
      f"after 200 ${price('WHEAT', MARKET_I0 + 200)}")

# A shop unlocked at the end of day d becomes visible at step (d+1)*24, and the
# unlock days are those with (d+1) % 3 == 0, capped at 8 instances.
UNLOCK_STEP = [72 * (i + 1) for i in range(8)]
SHOP_TICK, CENTER_TICK = 4, 24
EVENTS = [sum(1 for s in range(STEPS) if s % SHOP_TICK == 0 and s >= u)
          for u in UNLOCK_STEP]

def demand(draw):
    """Units the town consumes over one season, given the eight shops drawn."""
    d = {g: 0 for g in PRODUCTS}
    for g in TOWN_CENTER:
        d[g] += sum(1 for s in range(STEPS) if s % CENTER_TICK == 0)
    for i, shop in enumerate(draw):
        goods = SHOPS[shop]
        mult = 2 if len(goods) == 1 else 1
        for g in goods:
            d[g] += mult * EVENTS[i]
    return d

print('shop consumption events by unlock slot:', EVENTS, '\n')

# THE CHECK. Three seeds run in the real engine with two agents that never sell,
# so the drop in inventory IS the demand. The model must reproduce them exactly.
ENGINE = {
 11: (['FARMERS_MARKET','BRUNCH_SPOT','ICE_CREAM_SHOP','YARN_STORE','YARN_STORE',
       'SMOOTHIE_SHOP','YARN_STORE','SMOOTHIE_SHOP'],
      {'WHEAT':462,'CARROT':192,'TOMATO':192,'STRAWBERRY':570,'MELON':30,
       'EGG':174,'MILK':264,'WOOL':534,'FERTILIZER':0}),
 22: (['PET_CAFE','PET_CAFE','PET_CAFE','YARN_STORE','PET_CAFE','PET_CAFE',
       'BAKERY','PET_CAFE'],
      {'WHEAT':84,'CARROT':1290,'TOMATO':30,'STRAWBERRY':30,'MELON':30,
       'EGG':84,'MILK':30,'WOOL':246,'FERTILIZER':0}),
 33: (['PET_CAFE','PIZZA_SHOP','YARN_STORE','FARMERS_MARKET','BRUNCH_SPOT',
       'FARMERS_MARKET','BAKERY','BAKERY'],
      {'WHEAT':534,'CARROT':534,'TOMATO':354,'STRAWBERRY':300,'MELON':30,
       'EGG':210,'MILK':174,'WOOL':282,'FERTILIZER':0}),
}
for seed, (draw, truth) in ENGINE.items():
    got = demand(draw)
    ok = all(got[g] == truth[g] for g in PRODUCTS)
    print(f'seed {seed}: model reproduces the engine exactly: {ok}')
    if not ok:
        print('   ', {g: (got[g], truth[g]) for g in PRODUCTS if got[g] != truth[g]})

rng = np.random.default_rng(20260814)
names = sorted(SHOPS)
draws = [[names[i] for i in rng.integers(0, len(names), 8)] for _ in range(10000)]
D = {g: np.array([demand(d)[g] for d in draws]) for g in PRODUCTS}

fig, ax = plt.subplots(figsize=(8.6, 4.6))
order = sorted(PRODUCTS, key=lambda g: -np.median(D[g]))
for i, g in enumerate(order):
    v = D[g]
    fixed = v.min() == v.max()
    col = ORANGE if fixed else BLUE
    lo, hi = np.percentile(v, [5, 95])
    # thin line for the whole range, thick for the middle 90 %, dot at the
    # median: one connected object per good, so nothing floats unattached.
    ax.plot([v.min(), v.max()], [i, i], color=col, lw=1.0, alpha=.55,
            solid_capstyle='butt', zorder=1)
    ax.plot([lo, hi], [i, i], color=col, lw=5.0, alpha=.45,
            solid_capstyle='round', zorder=2)
    ax.plot([np.median(v)], [i], 'o', color=col, ms=7, zorder=3,
            markeredgecolor='white', markeredgewidth=1.1)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([g.title() for g in order])
ax.invert_yaxis()
ax.set_xlabel('units the town buys in one season')
ax.set_xlim(-30, max(D[g].max() for g in PRODUCTS) * 1.02)
tidy(ax, None, 'How much of each good has a buyer, over 10,000 shop draws')
ax.xaxis.grid(True, color=GRID, lw=.8); ax.yaxis.grid(False)
ax.plot([], [], 'o-', color=BLUE, lw=5, alpha=.45, label='full range, middle 90 %, median')
ax.plot([], [], 'o', color=ORANGE, label='identical in every episode')
ax.legend(frameon=False, fontsize=9, loc='lower right')
plt.tight_layout(); plt.show()

for g in ('MELON', 'FERTILIZER'):
    print(f'{g:<11} demand is {D[g].min()} in all 10,000 draws: '
          f'{D[g].min() == D[g].max()}')
print(f"\nCARROT demand ranges {D['CARROT'].min():,} to {D['CARROT'].max():,}, "
      f"a factor of {D['CARROT'].max() / max(1, D['CARROT'].min()):.0f}")

def revenue_curve(good, dem, cap=200_000):
    """Price of the n-th unit sold, latest-first, and the running total."""
    per, run, tot = [], 0.0, []
    for i in range(cap):
        p = price(good, MARKET_I0 - dem + i)
        per.append(p); run += p; tot.append(run)
        if p <= PRICE_FLOOR and i > dem + 5:
            break
    return np.array(per), np.array(tot)

def land_capacity(good, tiles=100):
    """Units ONE player could grow with every tile and no labour limit.

    Deliberately generous: it ignores the farmer's movement, the 24 actions a
    day, watering, wages and the shed's ceiling. It is the agronomic bound, and
    it is here only to say which constraint binds, the market or the land."""
    if good in CROPS:
        c = CROPS[good]
        if c['ongoing']:
            return tiles * ((DAYS - c['first']) // max(1, c['interval']) + 1) * c['yld']
        return tiles * (DAYS // (c['maxday'] + 1)) * c['yld']
    animals = {'EGG': (4, 1), 'MILK': (8, 2), 'WOOL': (6, 3)}
    if good in animals:
        first, iv = animals[good]
        return tiles * ((DAYS - first) // iv + 1)
    return None

rows = []
for g in PRODUCTS:
    d = int(np.median(D[g]))
    per, tot = revenue_curve(g, d)
    floored = per[-1] <= PRICE_FLOOR
    units = int(np.argmax(per <= PRICE_FLOOR)) if floored else len(per)
    lc = land_capacity(g)
    both = 2 * lc if lc is not None else None
    rev = tot[units - 1] if units else 0.0
    if both is not None and both < units:      # land runs out before the price does
        rev = tot[min(both, len(tot)) - 1]
    rows.append(dict(good=g, demand=d, units=units, floored=floored, land=both,
                     revenue=rev,
                     binds='market' if (both and floored and units < both)
                           else ('land' if both else 'n/a')))

print(f"{'good':<12}{'demand':>8}{'units to floor':>16}{'2 farms can grow':>18}"
      f"{'binds':>8}{'revenue':>12}")
for r in rows:
    u = '{:,}'.format(r['units']) if r['floored'] else '>{:,}'.format(r['units'])
    ld = '{:,}'.format(r['land']) if r['land'] else '.'
    print(f"{r['good']:<12}{r['demand']:>8,}{u:>16}{ld:>18}"
          f"{r['binds']:>8}{r['revenue']:>12,.0f}")
PURSE = sum(r['revenue'] for r in rows)
print(f"\nTOTAL at median demand: ${PURSE:,.0f}, for both players combined")

sums = []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_PUBLIC' or r['state'] != 'COMPLETED':
            continue
        try:
            sums.append(float(r['bank_0']) + float(r['bank_1']))
        except (TypeError, ValueError):
            continue
sums = np.array(sums)
print(f'{len(sums):,} public completed episodes\n')
print(f'  purse at median demand      ${PURSE:>12,.0f}')
print(f'  best episode ever recorded  ${sums.max():>12,.0f}   '
      f'{100*sums.max()/PURSE:5.1f} % of it')
print(f'  median episode              ${np.median(sums):>12,.0f}   '
      f'{100*np.median(sums)/PURSE:5.1f} %')
print(f'  episodes above the purse    {int((sums > PURSE).sum())}')

fig, ax = plt.subplots(figsize=(8.6, 4.0))
ax.hist(sums, bins=90, color=BLUE, alpha=.85, edgecolor='white', lw=.4)
top = ax.get_ylim()[1]
ax.axvline(PURSE, color=ORANGE, lw=2.4)
ax.annotate(f'the whole purse\n${PURSE:,.0f}', xy=(PURSE, top * .62),
            xytext=(PURSE * .63, top * .82), color=ORANGE, fontsize=10,
            fontweight='bold', ha='right',
            arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.4))
ax.annotate(f'best game ever\n${sums.max():,.0f}', xy=(sums.max(), top * .10),
            xytext=(sums.max() * 1.06, top * .36), color=INK, fontsize=9,
            arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.0))
ax.xaxis.set_major_formatter(lambda v, p: f'{v/1000:,.0f}k')
ax.set_xlabel('both banks added together, one episode')
tidy(ax, 'episodes', 'Every episode ever played, against the money that exists')
plt.tight_layout(); plt.show()

# Carried past the floor on purpose, so the chart shows what the 300th melon is
# worth rather than stopping where the money does.
per_m = np.array([price('MELON', MARKET_I0 - 30 + i) for i in range(341)])
tot_m = np.cumsum(per_m, dtype=float)
floor_at = int(np.argmax(per_m <= PRICE_FLOOR))
quad = 25 * CROPS['MELON']['yld']
lifetime = tot_m[floor_at - 1]

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.3))
x = np.arange(len(per_m))

ax.plot(x, per_m, color=BLUE, lw=2.4, zorder=3)
ax.axhline(PRICE_FLOOR, color=MUTED, lw=1, ls=':')
# Staggered heights: three labels at one height collided in the first draft.
for v, col, lab, ha, y in ((30, AQUA, 'the town\nwants 30', 'left', 292),
                           (quad, ORANGE, 'one player,\none quadrant', 'right', 196),
                           (2 * quad, ORANGE, 'both\nplayers', 'right', 96)):
    ax.axvline(v, color=col, lw=1.6, ls='--' if v == 2 * quad else '-', alpha=.9)
    ax.annotate(lab, xy=(v, y), xytext=(7 if ha == 'left' else -7, 0),
                textcoords='offset points', color=col, fontsize=9,
                fontweight='bold', ha=ha, va='top')
ax.set_xlim(0, 340); ax.set_ylim(0, 300)
ax.set_xlabel('melons sold into the market')
tidy(ax, 'price of the next melon ($)', 'What the next melon is worth')

ax2.plot(x, tot_m, color=BLUE, lw=2.4, zorder=3)
ax2.axhline(lifetime, color=MUTED, lw=1, ls=':')
for v, ls in ((quad, '-'), (2 * quad, '--')):
    ax2.axvline(v, color=ORANGE, lw=1.6, ls=ls, alpha=.9)
ax2.annotate(f'everything melon will ever pay\n${lifetime:,.0f}',
             xy=(258, lifetime), xytext=(0, -16), textcoords='offset points',
             color=MUTED, fontsize=9, ha='center', va='top')
ax2.set_xlim(0, 340)
ax2.yaxis.set_major_formatter(lambda v, p: f'{v/1000:,.0f}k')
ax2.set_xlabel('melons sold into the market')
tidy(ax2, 'total paid ($)', 'And it saturates')
plt.tight_layout(); plt.show()

print(f'the price reaches the floor after {floor_at} melons')
print(f'total melon will ever pay, to BOTH players: ${lifetime:,.0f}')
print(f'one 5x5 quadrant grows up to {quad} melons per player, {2*quad} between two')
for n in (100, 150, 188, 250):
    print(f'  melon number {n:>4} sells for ${per_m[n]:>4}')