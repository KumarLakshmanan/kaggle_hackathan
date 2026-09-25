import sys, io, contextlib, subprocess

def _quiet_import():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        import kaggle_environments
        from kaggle_environments import make
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
    return kaggle_environments, make, K

try:
    kaggle_environments, make, K = _quiet_import()
except Exception:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-U', 'kaggle-environments'])
    kaggle_environments, make, K = _quiet_import()

print('kaggle-environments', getattr(kaggle_environments, '__version__', 'unknown'))
print('engine file:', K.__file__)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 110
BLUE = '#2a78d6'
GREY = '#b8c4d0'

crops = pd.DataFrame(K.CROPS).T
crops.index.name = 'crop'
crops

animals = pd.DataFrame(K.ANIMALS).T
animals.index.name = 'animal'
print(animals.to_string())
print()
print('starting money      :', 3000)
print('season              :', '24 turns/day x 30 days = 720 turns')
print('shed access tiles   :', K._shed_access_tiles(10))
print('land prices (NE/SW/SE):', K.LAND_PRICES)
print('hire cost sequence  :', [K._fib(n) for n in range(9)])

import inspect
src = inspect.getsource(K._new_plant)
print(src)

ref = inspect.getsource(K._daily_refresh_plants)
print('\n'.join(ref.splitlines()[:22]))

def observe_tile(obs):
    me = obs['farms'][obs['player']]
    fx, fy = me['farmer']
    return me['tiles'][fy][fx]

def play(policy, days=20, seed=7, log_fn=None):
    """Run one episode; player 1 passes. Returns the log list."""
    log = []
    buf = io.StringIO()
    def p0(obs, cfg):
        if log_fn: log_fn(obs, log)
        return policy(obs)
    def p1(obs, cfg):
        return {'farmer': ['PASS'], 'hands': [], 'market': []}
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        env = make('kaggriculture',
                   configuration={'episodeSteps': days * 24, 'seed': seed}, debug=True)
        env.run([p0, p1])
    return log

def log_tile(obs, log):
    t = observe_tile(obs)
    rec = {'step': obs['step'], 'day': obs['day']}
    if isinstance(t, dict):
        rec.update({k: t.get(k) for k in
                    ('kind', 'crop', 'yield_units', 'consecutive_unwatered', 'watered_today')})
    else:
        rec['kind'] = t
    log.append(rec)

def pol_never_water(obs):
    me, priv = obs['farms'][obs['player']], obs['private']
    tile = observe_tile(obs)
    mk = []
    if priv['seeds'].get('WHEAT', 0) == 0 and me['money'] >= 10:
        mk.append(['BUY_SEED', 'WHEAT', 1])
    act = ['PASS']
    if tile is None and priv['seeds'].get('WHEAT', 0) > 0 and obs['day'] == 0:
        act = ['PLANT', 'WHEAT']
    return {'farmer': act, 'hands': [], 'market': mk}

log = play(pol_never_water, days=4, log_fn=log_tile)
df = pd.DataFrame(log)
planted = df[df.kind == 'PLANT']
weeded  = df[df.kind == 'WEED']
print(f"planted at step {planted.step.min()} (day {planted.day.min()})")
print(f"survived {len(planted)} turns")
print(f"became a WEED at step {weeded.step.min()} (day {weeded.day.min()})")
df.head(3)

step_src = inspect.getsource(K)
i = step_src.index('if op == "WATER"')
print(step_src[i:i + 640])

rows = []
for c, cd in K.CROPS.items():
    if cd['ongoing']:
        continue
    ws = (cd['max_yield_day'] + 1) // 2
    we = cd['max_yield_day']
    n_water = we - ws + 1
    rows.append({
        'crop': c,
        'first_yield_day': cd['first_yield_day'],
        'max_yield_day': we,
        'window': f'days {ws}-{we}',
        'waterings_in_window': n_water,
        'engine max_yield': cd['max_yield'],
        'reachable by watering': min(cd['max_yield'], 1 + n_water),
        'reachable +fertilizer': min(cd['max_yield'], 1 + 2 * n_water),
    })
win = pd.DataFrame(rows).set_index('crop')
win

def single_tile(crop, harvest_age, water=True, fertilize=False, days=20, seed=7):
    """Farm one tile for `days` days; return units harvested and per-cycle yields."""
    st = {'units': 0, 'prev': 0, 'cycles': 0, 'yields': []}
    def pol(obs):
        me, priv = obs['farms'][obs['player']], obs['private']
        tile = observe_tile(obs)
        inv = (priv['inventories'][0] or {}).get(crop, 0)
        if inv > st['prev']:
            st['units'] += inv - st['prev']; st['yields'].append(inv - st['prev']); st['cycles'] += 1
        st['prev'] = inv
        mk = []
        if priv['seeds'].get(crop, 0) == 0 and me['money'] >= 200:
            mk.append(['BUY_SEED', crop, 1])
        if fertilize and priv['shed'].get('FERTILIZER', 0) == 0 and me['money'] >= 200:
            mk.append(['BUY_PRODUCT', 'FERTILIZER', 1])
        act = ['PASS']
        fert_inv = (priv['inventories'][0] or {}).get('FERTILIZER', 0)
        if inv >= 12:
            act = ['DROP']; st['prev'] = 0
        elif tile is None and priv['seeds'].get(crop, 0) > 0:
            act = ['PLANT', crop]
        elif isinstance(tile, dict) and tile.get('kind') == 'WEED':
            act = ['DIG']
        elif isinstance(tile, dict) and tile.get('kind') == 'PLANT':
            age = obs['day'] - tile['planted_day']
            if age >= harvest_age and tile.get('yield_units', 0) > 0:
                act = ['HARVEST']
            elif fertilize and fert_inv == 0 and priv['shed'].get('FERTILIZER', 0) > 0:
                act = ['PICKUP', 'FERTILIZER', 1]
            elif fertilize and fert_inv > 0 and tile.get('fertilized_until_day', -1) < obs['day']:
                act = ['FERTILIZE']
            elif water and not tile['watered_today']:
                act = ['WATER']
        return {'farmer': act, 'hands': [], 'market': mk}
    play(pol, days=days, seed=seed)
    return st

res = {}
for age in (2, 3, 4, 5, 6):
    s = single_tile('WHEAT', age, days=20)
    per = s['yields'][1:] or s['yields']
    res[age] = {'cycles': s['cycles'],
                'units_per_cycle': round(np.mean(per), 2) if per else 0.0,
                'total_units_20d': s['units']}
harvest_df = pd.DataFrame(res).T
harvest_df.index.name = 'harvest at age >='
harvest_df

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
ages = list(harvest_df.index)
cols = [BLUE if a != 2 else '#d9534f' for a in ages]
axes[0].bar([str(a) for a in ages], harvest_df.units_per_cycle, color=cols)
axes[0].set_title('Units per harvest'); axes[0].set_xlabel('harvest at crop age >=')
axes[1].bar([str(a) for a in ages], harvest_df.total_units_20d, color=cols)
axes[1].set_title('Total units over 20 days'); axes[1].set_xlabel('harvest at crop age >=')
for ax in axes:
    ax.spines[['top', 'right']].set_visible(False)
fig.suptitle('Wheat, one tile, no movement   (red = what the docs example does)', y=1.04)
plt.tight_layout(); plt.show()

a2, a3 = harvest_df.total_units_20d[2], harvest_df.total_units_20d[3]
print(f'harvest at age 2 (docs): {a2} units / 20 days')
print(f'harvest at age 3       : {a3} units / 20 days   ->  {(a3/a2-1)*100:+.0f}%')

print(inspect.getsource(K._decay_plants))

decay_log = []
def pol_watch_decay(obs):
    me, priv = obs['farms'][obs['player']], obs['private']
    tile = observe_tile(obs)
    mk = []
    if priv['seeds'].get('WHEAT', 0) == 0 and me['money'] >= 10:
        mk.append(['BUY_SEED', 'WHEAT', 1])
    act = ['PASS']
    if tile is None and priv['seeds'].get('WHEAT', 0) > 0 and obs['day'] == 0:
        act = ['PLANT', 'WHEAT']
    elif isinstance(tile, dict) and tile.get('kind') == 'PLANT':
        if not tile['watered_today']:
            act = ['WATER']          # water forever, never harvest
    if isinstance(tile, dict):
        decay_log.append({'step': obs['step'], 'day': obs['day'],
                          'kind': tile.get('kind'), 'units': tile.get('yield_units')})
    return {'farmer': act, 'hands': [], 'market': mk}

play(pol_watch_decay, days=7)
dd = pd.DataFrame(decay_log)
peak = dd.units.max()
fig, ax = plt.subplots(figsize=(10, 3.4))
ax.plot(dd.step, dd.units.fillna(0), color=BLUE, lw=2)
ax.axvline(120, color='#d9534f', ls='--', lw=1.2)
ax.text(122, peak * 0.6, 'max_lifespan_step = 120\n(start of day 5)', color='#d9534f', fontsize=9)
ax.set_title('A wheat plant that is watered forever and never harvested')
ax.set_xlabel('step'); ax.set_ylabel('yield_units')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(); plt.show()
rot = dd[dd.kind == 'WEED']
print(f'peak units held        : {peak:.0f}')
print(f'tile became a WEED at  : step {rot.step.min()} (day {rot.day.min()})')
print(f'units salvaged         : 0  -- the whole harvest rotted on the tile')

plain = single_tile('WHEAT', 4, water=True, fertilize=False, days=20)
fert  = single_tile('WHEAT', 4, water=True, fertilize=True,  days=20)
dry   = single_tile('WHEAT', 4, water=False, days=20)

comp = pd.DataFrame({
    'watered only':        [plain['units'], plain['cycles']],
    'watered + fertilized':[fert['units'],  fert['cycles']],
    'never watered':       [dry['units'],   dry['cycles']],
}, index=['units in 20 days', 'harvests']).T
print(comp.to_string())
print(f"\nfertilizer effect: {plain['units']} -> {fert['units']} units "
      f"({(fert['units']/plain['units']-1)*100:+.0f}%)")

print('shed access tiles :', K._shed_access_tiles(10))
print('farmer spawn      :', K._default_spawn(10))
print()
print(inspect.getsource(K._initial_tile))
print(inspect.getsource(K._quadrant_of))

costs = [K._fib(n) for n in range(10)]
cum = np.cumsum(costs)
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.bar(range(1, 11), costs, color=BLUE, label='cost of the n-th hire')
ax.plot(range(1, 11), cum, color='#d9534f', marker='o', ms=4, label='cumulative cost that day')
ax.set_xlabel('n-th hire of the day'); ax.set_ylabel('$')
ax.set_title('Hiring is nearly free, then suddenly is not')
ax.legend(frameon=False); ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(); plt.show()
for n in (4, 6, 8, 10):
    print(f'{n:2d} hands in one day costs ${cum[n-1]:,d}')

rows = []
for c, cd in K.CROPS.items():
    base = K.MARKET_PARAMS[c]['base']
    if cd['ongoing']:
        units = cd['max_yield']
        span  = cd['first_yield_day'] + cd['interval'] * (cd['max_yield'] - 1) + 1
        note  = 'ongoing'
    else:
        ws    = (cd['max_yield_day'] + 1) // 2
        units = min(cd['max_yield'], 1 + (cd['max_yield_day'] - ws + 1))
        span  = cd['max_yield_day'] + 1
        note  = 'one-time'
    rev  = units * base
    prof = rev - cd['seed']
    rows.append({'crop': c, 'type': note, 'seed $': cd['seed'], 'tile-days': span,
                 'units (reachable)': units, 'base $/unit': base,
                 'gross $': rev, 'profit $': prof,
                 '$ per tile-day': round(prof / span, 1)})
econ = pd.DataFrame(rows).sort_values('$ per tile-day', ascending=False).set_index('crop')
econ

fig, ax = plt.subplots(figsize=(9, 3.6))
e = econ.sort_values('$ per tile-day')
ax.barh(e.index, e['$ per tile-day'], color=BLUE)
ax.set_title('Profit per tile-day at base prices (reachable yield, seed cost deducted)')
ax.set_xlabel('$ per tile-day')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(); plt.show()

mp = pd.DataFrame(K.MARKET_PARAMS).T[['base', 'T', 'below_func', 'below_target',
                                       'above_func', 'above_target']]
mp.index.name = 'product'
print('How hard the price falls when you oversupply (above_* columns):')
mp.sort_values('above_target', ascending=False)