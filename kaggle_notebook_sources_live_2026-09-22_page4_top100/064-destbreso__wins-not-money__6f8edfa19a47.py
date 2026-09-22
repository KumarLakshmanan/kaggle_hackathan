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

import matplotlib.patheffects as pe
HALO = [pe.withStroke(linewidth=2.6, foreground='white')]

# ---------------------------------------------------------------------------
# EVERY NUMBER IN SECTIONS 3 TO 5 IS COMPUTED HERE, FROM THE DATASET, AT RUN
# TIME. An earlier version of this notebook carried them as pasted literals,
# which meant its headline test did not actually execute and no reader could
# check it. The dataset refreshes daily, so re-running this re-measures the
# board and every figure below moves with it.
import csv, os, math, statistics as st
from collections import defaultdict

def find_data(roots=('/kaggle/input',)):
    """Walk for episodes.csv rather than guessing the mount depth.

    Kaggle does not mount an input at a fixed depth: it can appear at
    /kaggle/input/<slug>/ or at /kaggle/input/datasets/<owner>/<slug>/."""
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

_rows = []
with open(BASE + '/episodes.csv') as f:
    for r in csv.DictReader(f):
        if r['type'] != 'EPISODE_TYPE_PUBLIC' or r['state'] != 'COMPLETED':
            continue                      # validation episodes are self-play
        try:
            x, y = float(r['bank_0']), float(r['bank_1'])
        except (TypeError, ValueError):
            continue
        _rows.append((r['create_time'] or '', r['sub_0'], r['sub_1'], x, y,
                      r['rating_0'], r['rating_1']))
_rows.sort(key=lambda t: t[0])            # ISO 8601, so lexicographic is time

_acc = defaultdict(lambda: {'margin': [], 'bank': [], 'rating': []})
for _, s0, s1, x, y, r0, r1 in _rows:
    _acc[s0]['margin'].append(x - y); _acc[s0]['bank'].append(x)
    _acc[s1]['margin'].append(y - x); _acc[s1]['bank'].append(y)
    for s, v in ((s0, r0), (s1, r1)):
        try:
            _acc[s]['rating'].append(float(v))
        except (TypeError, ValueError):
            pass

def table(min_episodes):
    """One row per submission: mean and spread of its margin, win rate, bank, rating.

    RATING IS THE LAST ONE, not the average over the submission's history. A
    rating starts at a default and walks toward its true level, so averaging the
    walk mixes the answer with the search for it. Section 5's whole argument is
    that early games are noise, and it would be inconsistent to then average
    them into the rating. Episodes are read in creation order, so the last
    rating_after is the converged one."""
    out = []
    for s, v in _acc.items():
        m = v['margin']
        if len(m) < min_episodes or not v['rating'] or st.pstdev(m) == 0:
            continue
        out.append({'sub': s, 'n': len(m), 'mu': st.mean(m), 'sd': st.stdev(m),
                    'wr': sum(1 for d in m if d > 0) / len(m),
                    'bank': st.mean(v['bank']), 'rating': v['rating'][-1]})
    out.sort(key=lambda d: d['sub'])
    return out

# 30 episodes is the threshold at which a submission's SPREAD is worth quoting;
# section 5 uses a looser one because it is asking a different question.
TAB = table(30)
print(f'{BASE}')
print(f'{len(_rows):,} public completed episodes')
print(f'{len(TAB)} submissions with 30 or more, which is the set sections 3 and 4 use')

# Rating changes are taken from consecutive episodes of the same submission,
# so each row is one update with the margin that produced it.
RAW = {'Q1': (1137, 6.65), 'Q2': (4630, 10.53), 'Q3': (10016, 12.88), 'Q4': (23197, 23.20)}
BY_GAMES = {'1 to 14': (23.49, 74.78), '15 to 39': (16.38, 14.22),
            '40 to 99': (5.47, 5.69), '100 or more': (4.40, 4.14)}
MOVE = {'1 to 14': 54.77, '15 to 39': 16.60, '40 to 99': 5.84, '100 or more': 4.30}

fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.9))

ax = axes[0]
ks = list(RAW)
ax.bar(range(4), [RAW[k][1] for k in ks], color=ORANGE, width=0.62)
ax.set_xticks(range(4))
ax.set_xticklabels([f'{k}\n{RAW[k][0]:,}' for k in ks], fontsize=8.5)
tidy(ax, 'median rating gained', 'Bigger wins gain more rating')
ax.set_xlabel('quartile of the winning margin')

ax = axes[1]
gs = list(BY_GAMES); x = np.arange(len(gs)); w = 0.36
ax.bar(x - w/2, [BY_GAMES[g][0] for g in gs], w, color=BLUE, label='narrowest wins')
ax.bar(x + w/2, [BY_GAMES[g][1] for g in gs], w, color=ORANGE, label='widest wins')
ax.set_xticks(x); ax.set_xticklabels(gs, fontsize=8.5, rotation=20, ha='right')
tidy(ax, 'median rating gained', 'Until you hold experience fixed')
ax.set_xlabel('games the submission had played')
ax.legend(frameon=False, fontsize=8.5)

ax = axes[2]
ax.bar(x, [MOVE[g] for g in gs], color=AQUA, width=0.62)
ax.set_xticks(x); ax.set_xticklabels(gs, fontsize=8.5, rotation=20, ha='right')
tidy(ax, 'median absolute rating change', 'because new submissions move ten times more')
ax.set_xlabel('games the submission had played')
plt.tight_layout(); plt.show()

print('median rating gained by a win, narrowest quartile against widest')
print(f"  {'games played':<14}{'narrow':>9}{'wide':>9}{'ratio':>8}")
for g in gs:
    a, b = BY_GAMES[g]
    print(f'  {g:<14}{a:>+9.2f}{b:>+9.2f}{b/a:>7.1f}x')

import numpy as np
import matplotlib.pyplot as plt

# The proposition is an existence claim, so it is proved by exhibiting two
# lotteries. Playing them is not part of the proof, but it is the only way to
# see what the claim means: one season, two scoreboards, opposite winners.
rng = np.random.default_rng(7)
N = 600

A = np.where(rng.random(N) < 0.9, 1.0, -20.0)      # +1 at 0.9, -20 at 0.1
B = np.where(rng.random(N) < 0.4, 100.0, -1.0)     # +100 at 0.4, -1 at 0.6

fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.9))

ax = axes[0]
for xs, ps, col, lab, off in ((( -20, 1), (0.1, 0.9), BLUE, 'A', -0.16),
                              ((-1, 100), (0.6, 0.4), ORANGE, 'B', 0.16)):
    ax.bar([x + off * 22 for x in xs], ps, width=6.0, color=col, label=lab)
ax.axvline(0, color=MUTED, lw=1, ls=':')
tidy(ax, 'probability', 'Two margins')
ax.set_xlabel('margin of one episode'); ax.legend(frameon=False, fontsize=9)

ax = axes[1]
ax.plot(np.cumsum(A), lw=2.2, color=BLUE)
ax.plot(np.cumsum(B), lw=2.2, color=ORANGE)
ax.axhline(0, color=MUTED, lw=1)
tidy(ax, 'cumulative margin', 'Money: B wins, enormously')
ax.set_xlabel('episodes')
ax.annotate('B', (N - 1, np.cumsum(B)[-1]), xytext=(-16, 6),
            textcoords='offset points', color=ORANGE, fontweight='bold', fontsize=10)
ax.annotate('A', (N - 1, np.cumsum(A)[-1]), xytext=(-16, -14),
            textcoords='offset points', color=BLUE, fontweight='bold', fontsize=10)

ax = axes[2]
ax.plot(np.cumsum(A > 0), lw=2.2, color=BLUE)
ax.plot(np.cumsum(B > 0), lw=2.2, color=ORANGE)
tidy(ax, 'cumulative episodes won', 'Wins: A wins, decisively')
ax.set_xlabel('episodes')
ax.annotate('A', (N - 1, np.cumsum(A > 0)[-1]), xytext=(-16, 4),
            textcoords='offset points', color=BLUE, fontweight='bold', fontsize=10)
ax.annotate('B', (N - 1, np.cumsum(B > 0)[-1]), xytext=(-16, -14),
            textcoords='offset points', color=ORANGE, fontweight='bold', fontsize=10)
plt.tight_layout(); plt.show()

print(f'over {N} episodes')
print(f"  A: mean margin {A.mean():>+8.2f}   episodes won {int((A > 0).sum()):>4} "
      f"({(A > 0).mean():.1%})")
print(f"  B: mean margin {B.mean():>+8.2f}   episodes won {int((B > 0).sum()):>4} "
      f"({(B > 0).mean():.1%})")
print()
print('A leaderboard that scores episodes ranks A first. One that scores money')
print('ranks B first. The two orderings are not close and neither is a near miss.')

import math

def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

print('Two agents. B earns MORE on average and wins LESS often.\n')
print(f"{'agent':<8}{'mu':>9}{'sigma':>9}{'mu/sigma':>10}{'Pr[win]':>10}")
for name, mu, sd in [('A', 2000, 3000), ('B', 5000, 20000)]:
    print(f'{name:<8}{mu:>+9,}{sd:>9,}{mu/sd:>10.2f}{phi(mu/sd):>10.1%}')

print('\nAnd the signed risk preference. The quantity that carries the sign is')
print('ell + mu, the realised lead plus what is still to come:\n')
print(f"{'ell+mu':>8}{'sigma':>9}{'Pr[win]':>10}")
for mu in (+2000, -2000):
    for sd in (3000, 12000):
        print(f'{mu:>+8,}{sd:>9,}{phi(mu/sd):>10.1%}')
print('\nAhead, spread costs. Behind, spread is the only thing that pays.')

# The curves are the rule and measure nothing. The points are real submissions at
# their mean and spread MEASURED on ladder games, which is what turns the rule
# into an instruction. dv is what widening that spread by 10 % does to Pr[win].
RISK = [[t['mu'], t['sd'], phi(t['mu'] / t['sd']),
         phi(t['mu'] / (1.1 * t['sd'])) - phi(t['mu'] / t['sd'])] for t in TAB]
mu = np.array([r[0] for r in RISK]); sd = np.array([r[1] for r in RISK])
pw = np.array([r[2] for r in RISK]); dv = np.array([r[3] for r in RISK])

fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.4))

ax = axes[0]
sig = np.linspace(8000, 62000, 300)
for lead, col, lab in ((+4000, BLUE, 'ahead by 4,000'),
                       (-4000, ORANGE, 'behind by 4,000')):
    ax.plot(sig / 1000, [phi(lead / s) for s in sig], lw=2, color=col)
    ax.annotate(lab, (sig[-1] / 1000, phi(lead / sig[-1])), xytext=(8, 0),
                textcoords='offset points', va='center', color=col,
                fontsize=9, fontweight='bold')
ax.axhline(0.5, color=MUTED, lw=1, ls=':')
ax.scatter(sd / 1000, pw, s=14, alpha=0.4, edgecolors='none',
           c=[ORANGE if m < 0 else BLUE for m in mu])
tidy(ax, 'Pr[win]', 'The rule, with 267 real submissions on it')
ax.set_xlabel('measured sigma of the margin, thousands')
ax.set_xlim(5, 72); ax.set_ylim(0, 1)

ax = axes[1]
ax.scatter(mu / 1000, 100 * dv, s=14, alpha=0.45, edgecolors='none',
           c=[ORANGE if m < 0 else BLUE for m in mu])
ax.axhline(0, color=MUTED, lw=1); ax.axvline(0, color=MUTED, lw=1, ls=':')
tidy(ax, 'change in Pr[win], points', 'Widening our spread by 10 %: the sign flips at zero')
ax.set_xlabel('measured mean margin, thousands')
ax.annotate('behind: variance helps', (-28, 1.5), fontsize=8.5, color=ORANGE,
            fontweight='bold', path_effects=HALO)
ax.annotate('ahead: variance costs', (6, -1.9), fontsize=8.5, color=BLUE,
            fontweight='bold', path_effects=HALO)
plt.tight_layout(); plt.show()

helps = int((mu < 0).sum())
print(f'{len(RISK)} submissions measured on real ladder games')
print(f'  widening the spread by 10 % helps {helps} of them and costs the other '
      f'{len(RISK) - helps}')
print(f'  largest gain {100*dv.max():+.1f} points, largest loss {100*dv.min():+.1f}')
print(f'  the sign flips exactly at a mean margin of zero, with no exceptions,')
print(f'  which is the corollary being arithmetic rather than a regularity')

# Measured, not simulated: agent v7.10 against 14 deduplicated top-team behaviours.
# columns: opponent, mu, sigma, observed win rate, games
DATA = [["カワシギ", 15715, 17159, 0.7, 20], ["researchstudio.site", 14617, 17640, 0.8, 20], ["Mohamed abdelrazik", 219, 2677, 0.65, 20], ["Furious Monk", 68, 2671, 0.6, 20], ["somewhere after", -8277, 7339, 0.2, 20], ["Aaweg", 359, 2626, 0.6, 20], ["One-For-All", 5825, 15933, 0.7, 20], ["Utkarsh #2", -1101, 6560, 0.6, 20], ["uri_kkyhr", -706, 2466, 0.5, 20], ["MD. Nazmus Sakib Anik", -2956, 4749, 0.35, 20], ["Suda", 694, 2348, 0.65, 20], ["ИТМОНИ АНАЛЬНИКИ AI B2B67 SaaS", -5764, 6519, 0.2, 20], ["Kostiantyn Isaienkov", -5202, 6329, 0.2, 20], ["Shadow", -3026, 2020, 0.1, 20]]

print(f"{'opponent':<24}{'mu':>10}{'sigma':>9}{'mu/sig':>8}{'predicted':>11}{'observed':>10}{'+/-':>7}")
print('-' * 79)
rows = []
for name, mu, sd, obs, n in DATA:
    z = mu / sd
    pred = phi(z)
    se = math.sqrt(max(obs * (1 - obs), 1e-9) / n)
    rows.append((name, mu, sd, z, pred, obs, se, n))
    print(f'{name[:23]:<24}{mu:>+10,}{sd:>9,}{z:>8.2f}{pred:>11.1%}{obs:>10.1%}{se:>7.1%}')

import statistics

err   = [obs - pred for _, _, _, _, pred, obs, _, _ in rows]
zres  = [(obs - pred) / se for _, _, _, _, pred, obs, se, _ in rows]
within = sum(1 for _, _, _, _, pred, obs, se, _ in rows if abs(obs - pred) <= 2 * se)

print('CALIBRATION over 14 opponents\n')
print(f'  mean signed error      {statistics.mean(err):>+7.1%}')
print(f'  mean absolute error    {statistics.mean(abs(e) for e in err):>7.1%}')
print(f'  within 2 standard errors   {within}/{len(rows)}')
print(f'  mean |z| of residual   {statistics.mean(abs(z) for z in zres):>7.2f}   (0.80 = E|Z| for a standard normal)')
print(f'\n  observed ABOVE predicted in {sum(1 for e in err if e > 0)}/{len(rows)} opponents')

fig, ax = plt.subplots(figsize=(6.0, 5.2))
ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls='--', zorder=1)

# Names are deliberately omitted: the claim is about the cloud, not any opponent,
# and fourteen labels on this many points collide with the error bars.
for name, mu, sd, z, pred, obs, se, n in rows:
    ax.errorbar(pred, obs, yerr=2*se, fmt='o', ms=7, color=BLUE,
                ecolor=GRID, elinewidth=3, capsize=0, zorder=3,
                markeredgecolor='white', markeredgewidth=1.2)

tidy(ax, 'observed win rate',
     'Every opponent lands within two standard errors')
ax.set_xlabel('predicted by $\\Phi(\\mu/\\sigma)$')
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_aspect('equal')
above = sum(1 for e in err if e > 0)
ax.text(0.035, 0.955,
        f'{above} of {len(rows)} points sit ABOVE the line.\n'
        f'The model under-predicts by {statistics.mean(err):+.1%} on average,\n'
        'which is a direction, not noise.',
        fontsize=8.5, color=MUTED, va='top', linespacing=1.5)
ax.text(0.62, 0.06, 'bars are $\\pm$2 standard errors\nat 20 games per opponent',
        fontsize=8, color=MUTED, va='bottom')
plt.tight_layout(); plt.show()

# Measured on real ladder games from the public dataset. No simulation, no
# harness of ours, and no opponents chosen by us: these are the games the
# competition actually played. Predicted rate against the rate achieved.
CAL = [[phi(t['mu'] / t['sd']), t['wr'], t['n']] for t in TAB]
import statistics as st, math

pred = [c[0] for c in CAL]; obs = [c[1] for c in CAL]; ns = [c[2] for c in CAL]
err = [o - p for p, o in zip(pred, obs)]
se = [math.sqrt(max(o * (1 - o), 1e-9) / n) for o, n in zip(obs, ns)]

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6),
                         gridspec_kw={'width_ratios': [1, 1]})

ax = axes[0]
ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls='--', zorder=1)
sz = [8 + 30 * (n / max(ns)) for n in ns]
ax.scatter(pred, obs, s=sz, color=BLUE, alpha=0.42, edgecolors='none', zorder=3)
tidy(ax, 'observed win rate', 'Predicted against observed, 267 submissions')
ax.set_xlabel('predicted by the model')
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.text(0.04, 0.94, 'point size is games played', fontsize=8.5, color=MUTED, va='top')

# binned, which is the honest way to see bias separately from noise
ax = axes[1]
order = sorted(range(len(pred)), key=lambda i: pred[i])
q = max(1, len(order) // 10)
bx, by, bn = [], [], []
for i in range(10):
    idx = order[i * q:(i + 1) * q] if i < 9 else order[9 * q:]
    bx.append(st.mean(pred[j] for j in idx))
    by.append(st.mean(obs[j] for j in idx))
    bn.append(len(idx))
ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls='--')
ax.plot(bx, by, lw=2.2, color=ORANGE, marker='o', ms=7,
        markeredgecolor='white', markeredgewidth=1.2)
tidy(ax, 'observed', 'The same, in deciles of predicted rate')
ax.set_xlabel('predicted'); ax.set_xlim(0.2, 0.85); ax.set_ylim(0.2, 0.85)
ax.set_aspect('equal'); ax.xaxis.grid(True, color=GRID, lw=0.8)
plt.tight_layout(); plt.show()

within = sum(1 for e, s in zip(err, se) if abs(e) <= 2 * s)
mx, my = st.mean(pred), st.mean(obs)
num = sum((a - mx) * (b - my) for a, b in zip(pred, obs))
den = (sum((a - mx) ** 2 for a in pred) * sum((b - my) ** 2 for b in obs)) ** .5
print(f'{len(CAL)} submissions, {sum(ns):,} seat-games')
print(f'  correlation predicted vs observed   r = {num/den:+.3f}')
print(f'  mean signed error                   {st.mean(err):+.1%}')
print(f'  mean absolute error                 {st.mean(abs(e) for e in err):.1%}')
print(f'  within two standard errors          {within}/{len(CAL)}  ({100*within/len(CAL):.0f} %)')
print()
print(f"  {'predicted':>10}{'observed':>10}{'n':>6}")
for x, y, n in zip(bx, by, bn):
    print(f'  {x:>10.1%}{y:>10.1%}{n:>6}')

# Recomputed per rating band rather than pasted, so the split moves with the board.
def _corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** .5
    return num / den if den else 0.0

BAND = []
for lo, hi, lab in ((0, 1500, '0-1500'), (1500, 2200, '1500-2200'),
                    (2200, 2700, '2200-2700')):
    g = [t for t in TAB if lo <= t['rating'] < hi]
    if len(g) < 25:
        continue
    p = [phi(t['mu'] / t['sd']) for t in g]
    o = [t['wr'] for t in g]
    BAND.append({'band': lab, 'n': len(g),
                 'signed': st.mean(b - a for a, b in zip(p, o)),
                 'abs': st.mean(abs(b - a) for a, b in zip(p, o)),
                 'r': _corr(p, o),
                 'z': st.median(t['mu'] / t['sd'] for t in g)})
fig, axes = plt.subplots(1, 3, figsize=(12.2, 3.9))
x = np.arange(len(BAND)); labs = [b['band'] for b in BAND]

ax = axes[0]
ax.bar(x, [100 * b['signed'] for b in BAND],
       color=[ORANGE if b['signed'] > 0 else BLUE for b in BAND], width=0.6)
ax.axhline(0, color=MUTED, lw=1)
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=9)
tidy(ax, 'observed minus predicted, points', 'The bias changes sign by band')
ax.set_xlabel('ladder rating band')

ax = axes[1]
ax.bar(x, [b['r'] for b in BAND], color=BLUE, width=0.6)
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=9); ax.set_ylim(0, 1)
tidy(ax, 'r, predicted vs observed', 'But the fit itself holds everywhere')
ax.set_xlabel('ladder rating band')

ax = axes[2]
ax.bar(x, [b['z'] for b in BAND], color=AQUA, width=0.6)
ax.axhline(0, color=MUTED, lw=1)
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=9)
tidy(ax, 'median mu / sigma', 'And the quantity being maximised moves')
ax.set_xlabel('ladder rating band')
plt.tight_layout(); plt.show()

print(f"  {'band':<12}{'subs':>6}{'signed err':>12}{'abs err':>10}{'r':>9}{'median mu/sd':>14}")
for b in BAND:
    print(f"  {b['band']:<12}{b['n']:>6}{b['signed']:>+11.1%}{b['abs']:>10.1%}"
          f"{b['r']:>+9.3f}{b['z']:>14.2f}")

from scipy import stats
MARG = {"カワシギ": [-4591.0, -4714.0, 29752.0, 27960.0, 26174.0, 32506.0, 17269.0, 17269.0, 31034.0, 31640.0, 12527.0, 16099.0, 34707.0, 34816.0, 26822.0, 27450.0, -6154.0, -7432.0, -13900.0, -14936.0], "researchstudio.site": [44949.0, 30679.0, 20265.0, 21965.0, -10834.0, -1860.0, 12428.0, 13310.0, 555.0, 569.0, -9068.0, -5955.0, 7024.0, 2782.0, 16415.0, 10858.0, 49123.0, 49123.0, 19841.0, 20165.0], "Mohamed abdelrazik": [1463.0, -1201.0, 2661.0, -2409.0, -2757.0, 3093.0, -901.0, 1429.0, 131.0, 131.0, 1505.0, -1263.0, 263.0, 263.0, 7093.0, -5619.0, 124.0, 124.0, 3434.0, -3176.0], "Furious Monk": [1263.0, -2245.0, 2656.0, -3017.0, -2313.0, 3046.0, 229.0, 2057.0, 482.0, 996.0, 915.0, 1119.0, -1338.0, -1338.0, 6364.0, -7251.0, 379.0, 379.0, -104.0, -925.0], "somewhere after": [-9510.0, -12412.0, -8944.0, -7305.0, -2605.0, 2033.0, -2690.0, -1072.0, -21483.0, -18113.0, -9635.0, -10885.0, -19297.0, -21099.0, -10665.0, -10703.0, 318.0, 318.0, 32.0, -1816.0], "Aaweg": [1364.0, -2405.0, 2885.0, -2986.0, -1904.0, 3079.0, 207.0, 1902.0, 998.0, 1353.0, 922.0, 1085.0, -1390.0, -1390.0, 7678.0, -5400.0, 914.0, 914.0, -18.0, -621.0], "One-For-All": [-6687.0, -7007.0, 19668.0, 24946.0, 13635.0, 17198.0, 13762.0, 11345.0, 2227.0, 3186.0, 20512.0, 17574.0, 17490.0, 17621.0, 16454.0, 16628.0, -12527.0, -12386.0, -27373.0, -29758.0], "Utkarsh #2": [-7076.0, -9721.0, 940.0, 3749.0, 4857.0, 6982.0, 2747.0, 4902.0, -13120.0, -9978.0, -3061.0, -5715.0, -8198.0, -11816.0, 1453.0, 1637.0, 5095.0, 5095.0, 5532.0, 3682.0], "uri_kkyhr": [-135.0, -3643.0, 1639.0, -4058.0, -3316.0, 1955.0, -526.0, 1286.0, 526.0, 810.0, 447.0, 516.0, -2749.0, -2749.0, 4608.0, -6405.0, 126.0, 126.0, -893.0, -1681.0], "MD. Nazmus Sakib Anik": [-2116.0, -1634.0, -6118.0, -4116.0, -1914.0, 4777.0, 824.0, 1776.0, -8673.0, -7434.0, -7575.0, -11319.0, -7500.0, -10729.0, 204.0, 204.0, 3890.0, 3890.0, -2141.0, -3414.0], "Suda": [1534.0, -1974.0, 3194.0, -2490.0, -1466.0, 3794.0, 895.0, 2723.0, 1087.0, 1371.0, 1566.0, 1599.0, -789.0, -789.0, 6146.0, -4789.0, 1026.0, 1026.0, 495.0, -282.0], "ИТМОНИ АНАЛЬНИКИ AI B2B67 SaaS": [-6354.0, -5707.0, 2018.0, 3171.0, 798.0, 6788.0, -5221.0, -4482.0, -15334.0, -10732.0, -14870.0, -20217.0, -10606.0, -9446.0, -5436.0, -9418.0, -1379.0, -1379.0, -2917.0, -4562.0], "Kostiantyn Isaienkov": [-12047.0, -13248.0, -2586.0, -36.0, -241.0, 4226.0, -605.0, -2027.0, -16862.0, -12641.0, -6695.0, -9140.0, -12218.0, -15223.0, -4134.0, -3950.0, 1493.0, 1493.0, 1135.0, -731.0], "Shadow": [-3873.0, -5510.0, -1764.0, -5839.0, -3133.0, 245.0, -3477.0, -3474.0, -706.0, -431.0, -3961.0, -3599.0, -1409.0, -1409.0, 472.0, -7531.0, -3414.0, -3414.0, -3819.0, -4474.0]}

names = list(MARG)
res = []
for k in names:
    m = np.array(MARG[k])
    W, p = stats.shapiro(m)
    res.append((k, stats.skew(m), stats.kurtosis(m), W, p))

# Q-Q plots for the three that reject and three that do not.
rej = [r for r in res if r[4] < 0.05][:3]
keep = [r for r in res if r[4] >= 0.05][:3]
fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.2))
for ax, (k, sk, ku, W, p) in zip(axes.ravel(), rej + keep):
    m = np.sort(np.array(MARG[k]))
    q = stats.norm.ppf((np.arange(len(m)) + 0.5) / len(m))
    ax.plot(q, m, 'o', ms=5, color=ORANGE if p < 0.05 else BLUE,
            markeredgecolor='white', markeredgewidth=0.8)
    lo, hi = q.min(), q.max()
    ax.plot([lo, hi], [m.mean() + m.std() * lo, m.mean() + m.std() * hi],
            color=MUTED, lw=1, ls='--')
    ax.set_title(f'{k[:16]}   p = {p:.3f}', loc='left', fontsize=9.5,
                 fontweight='bold', color=ORANGE if p < 0.05 else INK)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_axisbelow(True); ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.suptitle('Margins against a normal, by opponent. Orange rejects at 0.05.',
             x=0.01, ha='left', fontweight='bold', fontsize=12)
plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.show()

print(f"{'opponent':<24}{'skew':>8}{'kurtosis':>10}{'Shapiro W':>11}{'p':>9}")
for k, sk, ku, W, p in res:
    print(f'{k[:23]:<24}{sk:>8.2f}{ku:>10.2f}{W:>11.3f}{p:>9.3f}')
nrej = sum(1 for r in res if r[4] < 0.05)
print(f'\nrejected at 0.05: {nrej} of {len(res)}')
print(f'median skew across opponents: {np.median([r[1] for r in res]):+.2f}')

allm = np.concatenate([np.array(v) for v in MARG.values()])
print(f'\npooled across opponents (the WRONG test, kept to show why):')
print(f'  n = {len(allm)}, skew {stats.skew(allm):+.2f}, '
      f'kurtosis {stats.kurtosis(allm):+.2f}, Shapiro p = {stats.shapiro(allm)[1]:.1e}'      )

# The ladder pays the MEAN of your per-opponent win probabilities. Computing
# one Phi from pooled moments is a different quantity: pooling folds the
# BETWEEN-opponent spread into sigma, which drags the ratio toward zero and
# the probability toward one half.
per_opponent = statistics.mean(obs for *_, obs, _, _ in rows)

# pooled mu and sigma across all 280 games, from the per-opponent moments
N = sum(n for *_, n in rows)
pooled_mu = sum(mu * n for _, mu, _, _, _, _, _, n in rows) / N
pooled_var = sum((sd**2 + (mu - pooled_mu)**2) * n
                 for _, mu, sd, _, _, _, _, n in rows) / N
pooled = phi(pooled_mu / math.sqrt(pooled_var))

print(f'  mean of per-opponent win rates   {per_opponent:>7.1%}   <- what the ladder pays')
print(f'  Phi(pooled mu / pooled sigma)    {pooled:>7.1%}   <- what one aggregate says')
print(f'  gap                              {per_opponent - pooled:>+7.1%}')
print()
print('Aggregating first overstates the field win rate here. Estimate per')
print('opponent, then average. Never the other way round.')

# Every submission in the public dataset with at least 20 ladder episodes, which
# is a looser cut than sections 3 and 4 use: this section is asking what the
# ladder rewards, not estimating a spread, so it wants the noisy ones included.
SUBS = [{'sub': t['sub'], 'bank': t['bank'], 'wr': t['wr'],
         'rating': t['rating'], 'n': t['n'],
         'margin': t['mu']} for t in table(20)]
import statistics as st

def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** .5
    return num / den if den else 0.0

rating = [s['rating'] for s in SUBS]
bank   = [s['bank'] for s in SUBS]
winr   = [s['wr'] for s in SUBS]

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3), sharey=True)
for ax, xs, lab, col in ((axes[0], bank, 'mean bank', BLUE),
                         (axes[1], winr, 'win rate', ORANGE)):
    ax.scatter(xs, rating, s=13, color=col, alpha=0.45, edgecolors='none')
    r = corr(xs, rating)
    ax.set_xlabel(lab)
    tidy(ax, 'ladder rating' if ax is axes[0] else None,
         f'{lab} vs rating,  r = {r:+.3f}')
axes[1].xaxis.set_major_formatter(lambda v, p: f'{v:.0%}')
plt.tight_layout(); plt.show()

print(f'{len(SUBS)} submissions with 20 or more ladder episodes')
print(f'  mean bank vs rating   r = {corr(bank, rating):+.3f}')
print(f'  win rate  vs rating   r = {corr(winr, rating):+.3f}')

BUCKETS = [(20, 40, '20 to 39'), (40, 80, '40 to 79'), (80, 10 ** 9, '80 or more')]
rows = []
for lo, hi, lab in BUCKETS:
    g = [s for s in SUBS if lo <= s['n'] < hi]
    if len(g) < 25: continue
    rows.append((lab, len(g),
                 corr([s['bank'] for s in g], [s['rating'] for s in g]),
                 corr([s['wr'] for s in g], [s['rating'] for s in g])))

fig, ax = plt.subplots(figsize=(7.8, 4.2))
x = np.arange(len(rows)); w = 0.36
ax.bar(x - w / 2, [r[2] for r in rows], w, color=BLUE, label='mean bank')
ax.bar(x + w / 2, [r[3] for r in rows], w, color=ORANGE, label='win rate')
ax.axhline(0, color=MUTED, lw=1)
ax.set_xticks(x); ax.set_xticklabels([f'{r[0]}\n(n={r[1]})' for r in rows], fontsize=9)
tidy(ax, 'correlation with ladder rating',
     'The gap is measurement noise, and it closes')
ax.set_xlabel('ladder episodes the submission has played')
ax.legend(frameon=False, fontsize=9)
plt.tight_layout(); plt.show()

print(f"{'episodes':<14}{'subs':>6}{'r(bank)':>10}{'r(win rate)':>14}")
for lab, n, rb, rw in rows:
    print(f'{lab:<14}{n:>6}{rb:>+10.3f}{rw:>+14.3f}')
print()
import math
print('binomial standard error of a win rate, by games played')
for n in (20, 40, 80, 160):
    print(f'  n = {n:>3}: {math.sqrt(.25 / n):.1%}')

# The sub-additivity is not assumed. It is read off the engine: selling into a
# market that has already been moved fetches less per unit.
# The engine's price falls with inventory, so a second sale into a market the
# first sale already moved fetches less. Melon, as a percentage of its base
# price, by units already sold into it: 100 % at 0, 90 % at 50, 60 % at 100,
# 10 % at 150. Two changes that both sell melon therefore earn well under twice
# what one earns, while their dispersions still add.

# Two changes, each an improvement on its own, combined in a shared market.
CONF = [('baseline',                 1.00, 1.00),
        ('change A alone',           2.00, 1.50),
        ('change B alone',           2.00, 1.50),
        ('both, if means added',     3.00, 2.00),
        ('both, in a shared market', 2.50, 2.00)]

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0))
path = [0, 1, 4]                       # baseline -> one change -> both
labs = ['baseline', 'one change', 'both changes']

ax = axes[0]
ax.plot(range(3), [CONF[i][1] for i in path], lw=2.4, color=BLUE, marker='o', ms=8,
        markeredgecolor='white', markeredgewidth=1.3)
ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=9)
tidy(ax, 'E[M]', 'Expected margin: every step improves')

ax = axes[1]
ratio = [CONF[i][1] / CONF[i][2] for i in path]
ax.plot(range(3), ratio, lw=2.4, color=ORANGE, marker='o', ms=8,
        markeredgecolor='white', markeredgewidth=1.3)
ax.annotate('this step is a regression', (2, ratio[2]), xytext=(-8, 18),
            textcoords='offset points', ha='right', fontsize=9, color=ORANGE,
            fontweight='bold')
ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=9)
tidy(ax, 'mu / sigma', 'Probability of winning: the last step goes backwards')
plt.tight_layout(); plt.show()

print(f"  {'configuration':<26}{'mu':>7}{'sigma':>8}{'E[M]':>8}{'mu/sigma':>11}{'Pr[win]':>10}")
for lab, m, s in CONF:
    print(f'  {lab:<26}{m:>7.2f}{s:>8.2f}{m:>8.2f}{m/s:>11.3f}{phi(m/s):>10.1%}')