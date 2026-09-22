# Chart style, matched to the companion notebooks: recessive axes, a light
# horizontal grid, nothing decorative. Colour is assigned by the job it does.
import matplotlib.pyplot as plt
import numpy as np

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

import json
from itertools import combinations

def canon(a):
    return json.dumps(a, sort_keys=True, separators=(',', ':'))

def agreement(x, y):
    """Fraction of turns on which two recorded opponents act identically."""
    n = min(len(x), len(y))
    return sum(canon(x[t]) == canon(y[t]) for t in range(n)) / n

def cluster(streams, threshold=0.90):
    """Single linkage: two opponents are one behaviour if they mostly agree."""
    parent = list(range(len(streams)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, j in combinations(range(len(streams)), 2):
        if agreement(streams[i], streams[j]) >= threshold:
            a, b = find(i), find(j)
            if a != b:
                parent[a] = b
    groups = {}
    for i in range(len(streams)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())

# A pool that LOOKS like twelve opponents.
shared = [{'a': t % 5} for t in range(200)]                       # one popular route
pool, names = [], []
for k in range(7):                                                # seven copies of it,
    v = list(shared); v[10 * k] = {'a': 99}                       # each with a tiny quirk
    pool.append(v); names.append(f'copy_{k}')
for k in range(5):                                                # five genuine originals
    pool.append([{'a': (t * (k + 2)) % 7} for t in range(200)])
    names.append(f'original_{k}')

groups = cluster(pool)
print(f'names in the pool        {len(pool)}')
print(f'distinct behaviours      {len(groups)}')
print(f'cluster sizes            {sorted((len(g) for g in groups), reverse=True)}')

# Measured on the 40 real recorded opponents: all 780 pairwise agreements,
# and the cluster sizes they produce at a 90 % threshold.
HIST  = [388, 25, 22, 3, 9, 18, 15, 41, 159, 100]
SIZES = [18, 5] + [1] * 17

fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.7))

ax = axes[0]
edges = np.arange(10) * 10
cols = [ORANGE if e >= 80 else BLUE for e in edges]
ax.bar(edges + 5, HIST, width=9, color=cols)
tidy(ax, 'pairs of opponents', 'Two populations, not one')
ax.set_xlabel('turn by turn agreement, %')
ax.annotate('near duplicates\n259 of 780 pairs', (85, 159), xytext=(-14, 22),
            textcoords='offset points', fontsize=8.5, color=ORANGE,
            fontweight='bold', ha='right')
ax.annotate('median 17.5 %\nmean 40.9 %', (12, 330), fontsize=8.5, color=MUTED)

ax = axes[1]
ax.bar(range(len(SIZES)), SIZES, color=[ORANGE, ORANGE] + [BLUE] * 17, width=0.8)
tidy(ax, 'opponents in the cluster', '40 names, 19 behaviours')
ax.set_xlabel('cluster')
ax.set_xticks(range(0, len(SIZES), 3))
ax.annotate('one route,\n18 names', (0, 18), xytext=(10, -4),
            textcoords='offset points', fontsize=8.5, color=ORANGE,
            fontweight='bold')
plt.tight_layout(); plt.show()

from math import sqrt

# deff = 1 + (m - 1) * rho, with m the mean cluster size and rho the intra-cluster
# correlation. Setting rho = 1 treats members of a cluster as interchangeable, which
# makes n_eff exactly the number of clusters. That is the CONSERVATIVE end of the
# range and it is the assumption used below; at rho = 0.7 the inflation would be
# 1.33x rather than 1.45x.
def deff(n, clusters, rho=1.0):
    m = n / clusters
    return 1 + (m - 1) * rho

print(f"{'instrument':<22}{'names':>7}{'games':>8}{'behaviours':>12}{'CI inflation':>14}")
for label, names_n, behaviours in [('screen (8 opponents)', 8, 4),
                                   ('field test (40)', 40, 19)]:
    print(f'{label:<22}{names_n:>7}{2*names_n:>8}{2*behaviours:>12}'
          f'{sqrt(deff(names_n, behaviours)):>13.2f}x')

print()
print('So a 16 game screen result carries the weight of 8 games,')
print('and any interval quoted on it is too narrow by about 41 %.')
print()
print(f"at rho = 0.7 instead of 1.0 the field-test inflation is "
      f"{sqrt(deff(40, 19, 0.7)):.2f}x rather than {sqrt(deff(40, 19)):.2f}x")

import random
random.seed(7)

# Same budget, two ways of spending it: naive draw versus one per cluster.
clusters = {'popular': 18, 'common': 5, **{f'rare_{i}': 1 for i in range(17)}}
population = [name for name, k in clusters.items() for _ in range(k)]
BUDGET = 8

naive = random.sample(population, BUDGET)
stratified = list(dict.fromkeys(sorted(clusters, key=lambda c: -clusters[c])))[:BUDGET]

print(f'budget: {BUDGET} opponents, identical cost either way\n')
print(f'naive draw       {len(set(naive))} behaviours   {sorted(set(naive))}')
print(f'one per cluster  {len(set(stratified))} behaviours   {sorted(stratified)}')
print()
print('Stratifying is free. It changes which opponents you play, not how many.')