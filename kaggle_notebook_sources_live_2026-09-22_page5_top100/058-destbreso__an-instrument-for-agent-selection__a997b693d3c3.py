from collections import Counter
import json

def canon(a):
    """Exact comparison, not approximate: sorted-key JSON."""
    return json.dumps(a, sort_keys=True, separators=(',', ':')) if a else '{}'

def scripted_fraction(stream, siblings):
    """Fraction of turns matching the team's OWN modal action at that turn."""
    matched = counted = 0
    for t in range(len(stream)):
        votes = Counter(canon(s[t]) for s in siblings if t < len(s))
        if not votes:
            continue
        counted += 1
        matched += votes.most_common(1)[0][0] == canon(stream[t])
    return matched / counted if counted else 0.0

# A scripted agent: same plan every game, one improvised turn.
plan     = [{'a': i % 4} for i in range(20)]
game_1   = plan[:7]  + [{'a': 99}] + plan[8:]
game_2   = plan[:13] + [{'a': 98}] + plan[14:]
game_3   = plan[:]

# A reactive agent: the plan is only a skeleton.
react_1  = [{'a': i % 4} if i % 3 == 0 else {'a': 50 + i} for i in range(20)]
react_2  = [{'a': i % 4} if i % 3 == 0 else {'a': 70 + i} for i in range(20)]
react_3  = [{'a': i % 4} if i % 3 == 0 else {'a': 90 + i} for i in range(20)]

print(f'scripted agent  {scripted_fraction(game_1,  [game_2, game_3]):.1%}')
print(f'reactive agent  {scripted_fraction(react_1, [react_2, react_3]):.1%}')

import statistics

# Four candidates against a pool that is too weak for them.
# Wins saturate; the expected margin does not.
pool_results = {
    'candidate A': [5200, 4800, 6100, 5400, 5900, 5100, 4700, 6000],
    'candidate B': [2700, 2500, 3100, 2600, 2900, 2400, 2800, 2700],
    'candidate C': [ 300,  180,  420,  260,  350,  210,  290,  330],
    'incumbent  ': [5300, 5000, 5800, 5500, 5600, 5200, 5400, 5700],
}

print(f"{'':<13}{'wins':>7}{'mean margin':>14}")
for name, margins in pool_results.items():
    wins = sum(m > 0 for m in margins)
    print(f'{name:<13}{wins:>4}/{len(margins):<2}{statistics.mean(margins):>+14,.0f}')

print('\nEvery one wins every game. The win count cannot order them.')
print('The margin orders them, and it says C is nowhere near the incumbent.')

# One chart in this notebook, so its style lives here with it: quiet axes,
# a light horizontal grid, colour by role (blue candidates, orange incumbent).
import matplotlib.pyplot as plt
import numpy as np
BLUE, ORANGE, GRID = '#2a78d6', '#eb6834', '#e7e7e4'
plt.rcParams.update({'figure.dpi': 130, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})

def tidy(ax, ylab=None, title=None):
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.xaxis.grid(False)
    if ylab: ax.set_ylabel(ylab)
    if title: ax.set_title(title, loc='left', pad=10)
    return ax

names = list(pool_results)
wins  = [sum(m > 0 for m in pool_results[k]) for k in names]
marg  = [statistics.mean(pool_results[k]) for k in names]
col   = [ORANGE if k.strip() == 'incumbent' else BLUE for k in names]

# Two panels, never two y-axes on one chart: the scales are unrelated.
fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.5), sharey=False)
y = np.arange(len(names))[::-1]

ax = axes[0]
ax.barh(y, wins, color=col, height=0.6)
ax.set_yticks(y); ax.set_yticklabels([k.strip() for k in names], fontsize=9)
tidy(ax, None, 'Wins: nothing to rank')
ax.set_xlabel('games won of 8'); ax.set_xlim(0, 8.6)
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.yaxis.grid(False)

ax = axes[1]
ax.barh(y, marg, color=col, height=0.6)
ax.set_yticks(y); ax.set_yticklabels([])
tidy(ax, None, 'Margin: an order appears')
ax.set_xlabel('mean margin')
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.yaxis.grid(False)
plt.tight_layout(); plt.show()

import math

# A real +13.7-point gap between two candidates, measured on k seeds, when one
# tape's win rate swings with a per-seed sd near 17 points and the candidates'
# swings barely correlate. These are the measured values from the experiment
# that inverted; only k varies.
sd_paired = 17.3
for k in (3, 6, 12, 24):
    half = 1.96 * sd_paired / math.sqrt(k)
    lo, hi = 13.7 - half, 13.7 + half
    verdict = 'spans zero: INVISIBLE' if lo < 0 else 'resolved'
    print(f'{k:>3} seeds: 95% CI on a true +13.7 gap = [{lo:+6.1f}, {hi:+6.1f}]  {verdict}')

print('\nTwelve seeds is the floor, and it is arithmetic, not taste.')


from math import comb

def mcnemar_two_sided(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = max(a, b)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k, n + 1)) / 2 ** n)

def pr_better(k, n):
    # P(Beta(k+1, n-k+1) > 1/2), closed binomial form
    a, b = k + 1, n - k + 1
    m = a + b - 1
    return sum(comb(m, i) for i in range(0, a)) / 2.0 ** m

cases = [
    ('candidate P vs incumbent', 106, 11, 5),
    ('candidate R vs incumbent', 106, 53, 0),
]
print(f'{"":<26}{"games":>6}{"discordant":>11}{"split":>8}{"p":>8}{"Pr[better]":>12}')
for name, games, up, down in cases:
    p = mcnemar_two_sided(up, down)
    pr = pr_better(up, up + down)
    print(f'{name:<26}{games:>6}{up+down:>11}{f"{up}-{down}":>8}{p:>8.3f}{pr:>11.1%}')

print()
print('Same game count. The first candidate was PROBABLY better and the slot')
print('stayed unspent, because 16 discordant pairs at p = 0.21 is a lean, not')
print('a result. The second was not a close call. The game count never knew')
print('the difference; the discordant count did.')


from math import comb
import statistics

def sign_test(up, down):
    """Two-sided p on the games that actually moved."""
    n = up + down
    if n == 0:
        return 1.0
    k = max(up, down)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k, n + 1)) / 2 ** n)

def report(label, margins):
    """Never the median alone: while behind, P(win) rises with dispersion."""
    s = sorted(margins)
    print(f'{label:<12} n {len(s):>3}   median {statistics.median(s):>+9,.0f}'
          f'   sigma {statistics.pstdev(s):>9,.0f}'
          f'   p90 {s[int(0.9 * (len(s) - 1))]:>+9,.0f}')

print('the screen result that looked convincing:')
print(f'  9 of 12 head-to-head   p = {sign_test(9, 3):.3f}  -> does NOT pass\n')
print('what would pass at the same win rate, with depth:')
print(f'  30 of 40 head-to-head  p = {sign_test(30, 10):.4f} -> passes\n')

# Two candidates with the SAME median and very different risk profiles.
steady   = [100] * 20
volatile = [-4000, 4200] * 10
report('steady', steady)
report('volatile', volatile)
print('\nIdentical means. If you are behind the bank you must beat,')
print('the volatile one is the better bet and the median hides that.')

from math import comb

def sign_test_power(p_true, n, alpha=0.05):
    # exact: find the two-sided rejection threshold at alpha under p=1/2,
    # then the probability of landing beyond it when the truth is p_true
    # (detection in the direction of the true effect).
    def p2(k, n):
        m = max(k, n - k)
        return min(1.0, 2 * sum(comb(n, j) for j in range(m, n + 1)) / 2 ** n)
    k_crit = next((k for k in range(n // 2, n + 1) if p2(k, n) <= alpha), None)
    if k_crit is None:
        return 0.0
    return sum(comb(n, k) * p_true ** k * (1 - p_true) ** (n - k)
               for k in range(k_crit, n + 1))

print(f'{"n paired":>9}{"detects a true 57.5%":>22}{"a true 60%":>12}{"a true 65%":>12}')
for n in (40, 106, 199, 352, 786):
    row = [sign_test_power(p, n) for p in (0.575, 0.60, 0.65)]
    print(f'{n:>9}' + ''.join(f'{x:>12.0%}' if i else f'{x:>22.0%}'
                              for i, x in enumerate(row)))

print()
print('And the minimum detectable effect at 80 percent power, the number a')
print('THIN row prints so "not significant" cannot be quietly read as "no')
print('effect":')
for n in (40, 106, 352):
    p = 0.5
    while sign_test_power(p, n) < 0.80:
        p += 0.001
    print(f'  n = {n:>4}: smallest true rate seen 80% of the time = {p:.1%}')


from math import comb

# Expected number of DISTINCT first-two-shop pairs covered by n random seeds,
# under the uniform approximation (the real draw is measurably non-uniform,
# which only makes small panels worse: common pairs repeat, rare ones hide).
PAIRS = 64
def expected_cover(n):
    return PAIRS * (1 - (1 - 1 / PAIRS) ** n)

print(f'{"seeds":>6}{"expected pairs covered":>24}{"of 64":>8}')
for n in (3, 12, 64, 150, 300, 600):
    e = expected_cover(n)
    print(f'{n:>6}{e:>24.1f}{e/PAIRS:>8.0%}')

print()
print('Random seeds cover slowly and unevenly. A CHOSEN panel of 64 seeds,')
print('one per pair from a precomputed map, covers everything a 300-seed')
print('random panel almost covers, at a fifth of the cost. Mapping 600 seeds')
print('took minutes and found every one of the 64 pairs represented.')


# The funnel that ate itself: candidates surviving each stage of selection,
# then the out-of-selection seed. Screen and confirm both used for SELECTION
# leaves nothing held out; the third seed is the first honest reading.
stages = [('one-seed screen, gain > 0', 46),
          ('screen threshold, gain > 3k', 37),
          ('second-seed confirm', 13),
          ('third seed: still winning', 3)]
w = 46
for label, n in stages:
    bar = '#' * int(round(44 * n / w))
    print(f'{label:<30}{n:>4}  {bar}')

print()
print('The rule this argues for: a perturbation of a system validated on N')
print('seeds, selected on n << N seeds, keeps its screen gain only by luck.')
print('What survived, every time, was the change that is monotone by')
print('construction or has a provable loss floor, because those never needed')
print('the selection to be right.')
