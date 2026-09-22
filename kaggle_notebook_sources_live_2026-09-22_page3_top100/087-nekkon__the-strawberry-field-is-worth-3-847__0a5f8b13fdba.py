import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BLUE, ORANGE, GREY = '#3987e5', '#d95926', '#8a8a85'
plt.rcParams.update({'figure.facecolor': 'white', 'axes.facecolor': 'white',
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#cccccc', 'font.size': 11,
                     'axes.titlesize': 14, 'axes.titleweight': 'bold',
                     'axes.titlelocation': 'left', 'axes.titlepad': 14})

# price(inv) = base + sign · amp · f(|inv − I0|),  amp = target · base / f(T)
SHAPE = {'linear': lambda x: x, 'sq': lambda x: x ** 2,
         'sqrt': lambda x: np.sqrt(x), 'log': lambda x: np.log1p(x)}

# base, T (one field's 24-day output), glut shape, glut target   — README "Price Function"
MARKET = {
    'Wheat':      (25, 400, 'log',    0.20),
    'Carrot':     (35, 450, 'sqrt',   0.70),
    'Tomato':     (60, 200, 'sqrt',   0.60),
    'Strawberry': (120, 100, 'linear', 1.60),
    'Melon':      (250, 300, 'sq',     3.60),
    'Egg':        (50, 332, 'log',    0.20),
    'Milk':       (160, 122, 'linear', 1.60),
    'Wool':       (200, 105, 'sq',     3.20),
    'Fertilizer': (100, 200, 'linear', 0.40),
}

def price(res, k):
    """Price of the (k+1)-th unit you sell, starting from an untouched market."""
    base, T, f, target = MARKET[res]
    amp = target * base / SHAPE[f](T)
    return np.maximum(np.round(base - amp * SHAPE[f](np.asarray(k, float))), 1)

def revenue(res, n):
    return float(price(res, np.arange(int(n))).sum())

# sanity check against the table printed in the README
chk = pd.DataFrame({r: [price(r, T), price(r, 2 * T)]
                    for r, (_, T, _, _) in MARKET.items()},
                   index=['P(I0+T)', 'P(I0+2T)']).T.astype(int)
chk['README P(I0+T)'] = [20, 10, 24, 1, 1, 40, 1, 1, 60]
chk['README P(I0+2T)'] = [19, 1, 9, 1, 1, 39, 1, 1, 20]
print(chk.to_string())
print('\nreproduces the README table exactly:',
      bool((chk['P(I0+T)'] == chk['README P(I0+T)']).all() and
           (chk['P(I0+2T)'] == chk['README P(I0+2T)']).all()))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for r in MARKET:
    k = np.arange(0, 600)
    prem = MARKET[r][0] > 100
    ax = axes[0] if prem else axes[1]
    ax.plot(k, price(r, k), lw=2, label=f'{r}  (base ${MARKET[r][0]})')
for ax, ttl in zip(axes, ['Premium goods: base > $100', 'Staples: base ≤ $100']):
    ax.set_xlabel('units you have sold'); ax.set_ylabel('price of the next unit')
    ax.legend(frameon=False, fontsize=10)
    ax.axhline(1, color=GREY, lw=1, ls=':')
    ax.set_title(ttl)
plt.tight_layout(); plt.show()

floor = {}
for r in MARKET:
    p = price(r, np.arange(4000))
    floor[r] = int(np.argmax(p <= 1)) if (p <= 1).any() else None
print('units you can sell before the price is $1:')
for r, v in floor.items():
    print(f'  {r:11s} {"never" if v is None else v}')

rows = []
for r, (base, T, _, _) in MARKET.items():
    got = revenue(r, T)
    rows.append({'product': r, 'base': base, 'field output T': T,
                 'naive T×base': T * base, 'actual revenue': round(got),
                 'glut tax': f'{1 - got / (T * base):.0%}',
                 '$/unit': round(got / T, 1)})
tbl = pd.DataFrame(rows).sort_values('actual revenue', ascending=False)
print(tbl.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5.4))
t = tbl.iloc[::-1]
y = np.arange(len(t))
ax.barh(y, t['naive T×base'], .62, color='#dfe6ee', label='if base price held')
ax.barh(y, t['actual revenue'], .62, color=BLUE, label='what you actually get')
for i, (a, b) in enumerate(zip(t['actual revenue'], t['naive T×base'])):
    ax.text(b + 900, i, f'−{1 - a / b:.0%}', va='center', fontsize=10, color=ORANGE)
ax.set_yticks(y, t['product'])
ax.set_xlabel('revenue from one field-season, $')
ax.set_xlim(0, tbl['naive T×base'].max() * 1.16)
ax.tick_params(left=False)
ax.legend(frameon=False, loc='lower right')
ax.set_title('One 5×5 field, fully sold')
plt.show()

for n in (100, 200, 300, 400, 500):
    print(f'{n:>4} fertilizer -> ${revenue("Fertilizer", n):>8,.0f}   '
          f'avg ${revenue("Fertilizer", n) / n:5.1f}/unit')

print('\nfor comparison, the animals\' own products:')
for r in ('Egg', 'Milk', 'Wool'):
    for n in (50, 100, 200):
        print(f'  {r:5s} {n:>4} -> ${revenue(r, n):>8,.0f}   '
              f'avg ${revenue(r, n) / n:5.1f}')

DAYS = 20          # a realistic productive window inside the 30-day season
ANIMAL = {'Goose': ('Egg', 1, 300), 'Cow': ('Milk', 2, 400), 'Sheep': ('Wool', 3, 500)}

rows = []
for a, (prod, interval, cost) in ANIMAL.items():
    n_prod = DAYS // interval
    # value each stream at its average price over a plausible season volume
    unit_prod = revenue(prod, 100) / 100
    unit_fert = revenue('Fertilizer', 300) / 300
    rows.append({'animal': a, 'buy cost': cost, 'product': prod,
                 f'units in {DAYS}d': n_prod,
                 'product $': round(n_prod * unit_prod),
                 'fertilizer units': DAYS,
                 'fertilizer $': round(DAYS * unit_fert),
                 'manure share': f'{DAYS * unit_fert / (DAYS * unit_fert + n_prod * unit_prod):.0%}'})
print(pd.DataFrame(rows).to_string(index=False))

SEASON_TURNS = 24 * 30
print(f'season budget: {SEASON_TURNS} farmer actions')
print(f'hiring n hands for a day costs fib(1..n) = '
      f'{[1, 1, 2, 3, 5, 8, 13, 21]} → 8 hands for one day costs $54 '
      f'and buys {8 * 24} extra actions')
print(f'\nso an extra action is worth roughly ${54 / (8 * 24):.2f} at the margin — '
      f'anything earning more than that per action is worth doing')