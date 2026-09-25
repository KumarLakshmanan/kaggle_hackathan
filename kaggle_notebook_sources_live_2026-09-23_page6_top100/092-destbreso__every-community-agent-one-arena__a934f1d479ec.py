import subprocess, sys, shutil, os, json, tarfile, tempfile, time, pathlib

# FIND the dataset instead of assuming where it is mounted. On this image /kaggle/input
# is not a flat directory of datasets: it holds competitions/ and datasets/<owner>/<slug>/,
# so the files sit three levels down and a hard-coded path misses them.
IN = pathlib.Path('/kaggle/input')
found = None
for root in (IN, pathlib.Path('.')):
    if root.exists():
        found = next(iter(sorted(root.rglob('donors.csv'))), None)
    if found:
        break
if found is None:
    raise SystemExit('attach destbreso/kaggriculture-donor-agents-20260902')
DATA = found.parent
WORK = pathlib.Path('/kaggle/working' if pathlib.Path('/kaggle/working').exists() else 'work')
WORK.mkdir(exist_ok=True)
BUILD = pathlib.Path(tempfile.mkdtemp(prefix='kagsim_'))   # not under WORK: a notebook
# saves everything in its working directory as output, and a compiler leaves a lot there


def unpack(src, into):
    """Kaggle extracts archives on upload, so what was pushed as a tarball arrives as a
    directory carrying its own top-level folder. Take either form, and return a WRITABLE
    copy, because the dataset mount is read only and a compiler writes beside its sources."""
    if src.is_dir():
        dst = into / src.name
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        return dst
    with tarfile.open(src) as t:
        t.extractall(into)
        top = sorted({m.name.split('/')[0] for m in t.getmembers()})[0]
    return into / top


def build_engine(data, work):
    """Compile the engine here rather than `pip install` it.

    This notebook has no network, so pip's isolated build cannot fetch its build
    dependencies and fails before a compiler is ever called. The extension is one
    translation unit over header-only pybind11, which setuptools compiles directly,
    and the dataset carries those headers for an image that has none of its own."""
    cpp = next(iter(sorted(data.rglob('python/kagsim.cpp'))), None)
    if cpp is not None:
        src = unpack(cpp.parent.parent, work)
    else:
        tgz = next(iter(sorted(data.rglob('kagsim-*.tar.gz'))), None)
        src = unpack(tgz, work) if tgz else None
    if src is None:
        return None, 'no engine source in the dataset'

    try:
        import pybind11                             # the image's own copy, if it has one
        inc = pybind11.get_include()
    except ImportError:
        h = next(iter(sorted(data.rglob('pybind11/pybind11.h'))), None)
        if h is None:
            tgz = next(iter(sorted(data.rglob('pybind11*.tar.gz'))), None)
            if tgz:
                unpack(tgz, work)
                h = next(iter(sorted(work.rglob('pybind11/pybind11.h'))), None)
        inc = str(h.parent.parent) if h else None
    if inc is None:
        return None, 'no pybind11 headers, in this image or in the dataset'

    (src / '_build.py').write_text(
        "from setuptools import setup, Extension\n"
        "setup(name='kagsim', version='0.5.0', ext_modules=[Extension(\n"
        "    'kagsim', ['python/kagsim.cpp'], language='c++',\n"
        f"    include_dirs=[{inc!r}],\n"
        "    extra_compile_args=['-O3', '-std=c++17', '-fvisibility=hidden'])])\n")
    t0 = time.time()
    r = subprocess.run([sys.executable, '_build.py', 'build_ext', '--inplace'],
                       cwd=src, capture_output=True, text=True)
    so = next(iter(sorted(src.glob('kagsim*.so'))), None)
    if so is None:
        return None, (r.stderr or r.stdout)[-1200:]
    return src, f'{time.time() - t0:.0f}s'


print('engine source:', DATA)
ENGINE_SRC, note = build_engine(DATA, BUILD)
if ENGINE_SRC:
    sys.path.insert(0, str(ENGINE_SRC))
try:
    import kagsim
    ENGINE_OK = True
    print(f'engine: {kagsim.ENGINE_VERSION} compiled in {note}, about 50 microseconds a game')
except ImportError:
    ENGINE_OK = False
    print('ENGINE NOT BUILT. Everything below falls back to kaggle_environments, which',
          'is correct but roughly 5,000 times slower AND enforces a per-turn time limit',
          'that a large agent on a shared worker can miss. A timed-out agent plays a',
          'legal, empty game, so treat any small table below as suspect; arena.py says',
          'so itself when it sees one. The build said:')
    print(note)

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd, numpy as np, csv
if 'inline' not in matplotlib.get_backend():
    # every figure below is drawn with plt.show(), which draws nothing at all under a
    # non-interactive backend. Silence there would look exactly like a page with no figures.
    print('WARNING: the matplotlib backend is', matplotlib.get_backend(),
          'so the figures below may not render.')
csv.field_size_limit(1 << 31)
plt.rcParams.update({'figure.dpi': 120, 'font.size': 9, 'axes.grid': True,
                     'grid.alpha': .25, 'axes.spines.top': False, 'axes.spines.right': False})
INK, WARM, COOL = '#1b1b1b', '#c2410c', '#0f766e'

import collections
rows = list(csv.DictReader(open(DATA / 'donors.csv', newline='')))
fam = collections.Counter(r['behaviour_family'] or r['donor_id'] for r in rows)
dupes = {k: v for k, v in fam.items() if v > 1}
print(f'{len(rows)} files, {len(fam)} distinct measured behaviours, '
      f'{sum(v - 1 for v in dupes.values())} of those files are a repeat of another')
for f, n in sorted(dupes.items(), key=lambda kv: -kv[1]):
    members = [r['donor_id'] for r in rows if (r['behaviour_family'] or r['donor_id']) == f]
    print(f'  {n}x identical conduct: ' + ', '.join(sorted(members)))

import importlib.util, base64, tempfile
def last_callable(m):
    name = None
    for k, v in vars(m).items():
        if callable(v) and not k.startswith('_') and getattr(v, '__module__', None) == m.__name__:
            name = k
    return name
tmp = pathlib.Path(tempfile.mkdtemp()); odd, read, failed = [], 0, []
for r in rows:
    if r['payload_included'] != 'True' or r['payload_format'] != 'py':
        continue                      # packaged agents are loaded from their tar by arena.py
    p = tmp / (r['donor_id'] + '.py'); p.write_bytes(base64.b64decode(r['payload_b64']))
    spec = importlib.util.spec_from_file_location('m' + str(abs(hash(p)) % 9999), str(p))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception as exc:          # counted and named, never passed over in silence
        failed.append((r['donor_id'], f'{type(exc).__name__}: {exc}'[:70]))
        continue
    read += 1
    s = last_callable(m)
    if s and s != 'agent' and 'agent' in vars(m):
        odd.append((r['donor_id'], s))
print(f'{len(odd)} of the {read} single-file agents that import here would lose layers '
      f'if loaded by the name `agent`:')
for n, s in odd:
    print(f'  {n:<48} runner takes `{s}`')
if failed:
    print(f'\n{len(failed)} did not import at all, which is a property of the file and not '
          f'of the loader:')
    for n, why in failed:
        print(f'  {n:<48} {why}')

# The output STREAMS, line by line, as the games are played. A run that prints only
# when it finishes looks identical to one that has hung, and this one reports its rate
# and what it has left, so a slower machine is visible rather than a mystery.
cmd = [sys.executable, '-u', str((DATA / 'arena.py').resolve()), '--data', str(DATA.resolve()),
       '--diverse', '12', '--worlds', '6', '--procs', '4',
       # one agent in this field runs a neural policy in pure Python and costs 225
       # SECONDS a game. A panel of twelve that happens to draw it is eight hours.
       '--exclude', 'hesoponyo-pure-rl-agent-bc-ppo',
       '--matrix', str((WORK / 'lite_matrix.csv').resolve()),
       '--games', str((WORK / 'lite_games.csv').resolve())]
env = dict(os.environ)
if ENGINE_SRC:                      # the engine was built here, not installed
    env['PYTHONPATH'] = str(ENGINE_SRC) + os.pathsep + env.get('PYTHONPATH', '')
run = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, bufsize=1, env=env)
for line in run.stdout:
    print(line, end='')
if run.wait():
    raise SystemExit(f'arena.py exited with {run.returncode}: the table above is incomplete')

games = pd.read_csv(DATA / 'examples' / 'full_games_20260919.csv')
print(f'the finished run: {len(games):,} game-sides, {games.opponent.nunique()} opponents, '
      f'{games.seed.nunique()} worlds, seats {sorted(games.seat.unique())}')
summary = (games.assign(win=games.margin > 0)
                .groupby('agent')
                .agg(games=('margin', 'size'), win_rate=('win', 'mean'),
                     median_margin=('margin', 'median'), mean_margin=('margin', 'mean')))
summary.round(3)

per = (games.assign(win=games.margin > 0)
            .groupby(['agent', 'opponent'])
            .agg(win_rate=('win', 'mean'), median=('margin', 'median'), n=('margin', 'size'))
            .reset_index())
fig, ax = plt.subplots(figsize=(7.4, 4.4))
for name, colour, mark in (('CAND', COOL, 'o'), ('INC', WARM, '^')):
    d = per[per.agent == name]
    ax.scatter(d.win_rate, d['median'], s=26, c=colour, marker=mark, alpha=.75,
               edgecolor='none', label=name)
ax.set_yscale('symlog', linthresh=100)
ax.axhline(0, color=INK, lw=.8)
ax.axvline(.5, color=INK, lw=.8, ls=':')
near = per[per['median'].abs() < 60].sort_values('win_rate')
far = per[per['median'] < -1500].sort_values('win_rate')
if len(near):
    ax.annotate(f'{len(near)} pairings inside 60 dollars', (near.win_rate.mean(), 0),
                textcoords='offset points', xytext=(18, 26), fontsize=8, color=COOL,
                arrowprops=dict(arrowstyle='-', color=COOL, lw=.7))
if len(far):
    ax.annotate(f'{len(far)} pairings past 1,500 dollars', (far.win_rate.mean(), far['median'].median()),
                textcoords='offset points', xytext=(26, -8), fontsize=8, color=WARM,
                arrowprops=dict(arrowstyle='-', color=WARM, lw=.7))
ax.set_xlabel('share of games won against that opponent')
ax.set_ylabel('median margin, dollars (symlog)')
ax.set_title('Win rate against median margin, one point per opponent')
ax.legend(frameon=False, loc='lower right')
fig.tight_layout(); plt.show()
print('pairings within 60 dollars of a tie:')
print(near[['agent', 'opponent', 'win_rate', 'median']].to_string(index=False))

cand = games[games.agent == 'CAND'].copy()
cand['win'] = cand.margin > 0
grid = cand.pivot_table(index='world', columns='opponent', values='win', aggfunc='mean')
# Almost every column is a clean sweep, so a 0-to-1 scale over all 62 shows one shade.
# Keep the opponents that vary at all: those are where a world changes the answer.
varying = grid.columns[(grid.min() < 1.0)]
grid = grid[sorted(varying, key=lambda c: grid[c].mean())]
fig, ax = plt.subplots(figsize=(8.4, 6.4))
im = ax.imshow(grid.values, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(range(grid.shape[1]))
ax.set_xticklabels([c[:26] for c in grid.columns], rotation=45, ha='right', fontsize=7)
ax.set_yticks(range(0, len(grid), 2))
ax.set_yticklabels([w[:30] for w in grid.index[::2]], fontsize=6)
ax.set_title(f'Win rate by world for the {grid.shape[1]} opponents that are not a clean sweep\n'
             f'(the other {len(varying.symmetric_difference(cand.opponent.unique()))} are won in every world)',
             fontsize=10)
ax.grid(False)
fig.colorbar(im, ax=ax, shrink=.6, label='share of games won in that world')
fig.tight_layout(); plt.show()
spread = (grid.max() - grid.min()).sort_values(ascending=False)
print('largest swing across worlds, per opponent:')
for k, v in spread.head(5).items():
    print(f'   {k:<46}{v:.0%} between its best and worst world')

lite = pd.read_csv(WORK / 'lite_matrix.csv')
pair = lite.groupby(['agent', 'opponent'])[['games', 'wins']].sum()
pair['rate'] = pair.wins / pair.games
M = pair['rate'].unstack()
order = M.mean(axis=1).sort_values(ascending=False).index
M = M.loc[order, order]
short = lambda n: n if len(n) <= 26 else n[:25] + '\u2026'

size = max(6.6, 0.62 * len(M))
fig, ax = plt.subplots(figsize=(size, size * .84))
im = ax.imshow(M.values, cmap='RdYlGn', vmin=0, vmax=1)
for i in range(len(M)):
    for j in range(len(M)):
        v = M.values[i, j]
        if v == v:
            ax.text(j, i, f'{v:.0%}', ha='center', va='center', fontsize=7 if len(M) > 8 else 8,
                    color=INK if .25 < v < .75 else 'white')
ax.set_xticks(range(len(M)), [short(n) for n in M.columns], rotation=35, ha='right', fontsize=7)
ax.set_yticks(range(len(M)), [short(n) for n in M.index], fontsize=7)
per_cell = int(lite.groupby(['agent', 'opponent']).games.sum().median())
ax.set_title(f'Sampled run: share of games the row agent won, {per_cell} games a cell')
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=.035, pad=.02).set_label('win rate', fontsize=8)
fig.tight_layout(); plt.show()

from matplotlib.colors import ListedColormap, BoundaryNorm, SymLogNorm

games['win'] = games.margin > 0
strength = games.groupby('opponent').opponent_bank.median().sort_values(ascending=False)
bands = pd.qcut(strength, 4, labels=['bottom quarter', 'lower middle',
                                     'upper middle', 'top quarter'])
rows = list(strength.index)                          # strongest opponent at the top
hardest = (games[games.agent == 'CAND'].pivot_table(index='world', values='win', aggfunc='mean')
           .sort_values('win').index)                # hardest world on the left
ORDER = ['top quarter', 'upper middle', 'lower middle', 'bottom quarter']

cmap = ListedColormap(['#7f1d1d', '#f59e0b', '#dfe7e1'])
norm = BoundaryNorm([-.5, .5, 1.5, 2.5], cmap.N)
grids = {}
fig, axes = plt.subplots(1, 2, figsize=(11.6, 6.2), sharey=True)
for ax, name in zip(axes, ('CAND', 'INC')):
    d = games[games.agent == name]
    W = d.pivot_table(index='opponent', columns='world', values='win',
                      aggfunc='sum').reindex(index=rows, columns=hardest)
    grids[name] = W
    ax.imshow(W.values, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
    lost = int((W.values == 0).sum()); split = int((W.values == 1).sum())
    ax.set_title(f'{name}: {lost} cells lost, {split} split, {W.size - lost - split} swept',
                 fontsize=9)
    ax.set_xlabel('64 shop worlds, hardest on the left')
    ax.set_xticks([]); ax.grid(False)
    for edge in np.flatnonzero(np.diff(bands.reindex(rows).cat.codes.values)) + .5:
        ax.axhline(edge, color=INK, lw=.7, ls=':')

# the bands become the y axis, and the rows that are not a clean sweep are named on the
# right, stacked so that a cluster of them stays readable
centre = [np.mean([i for i, n in enumerate(rows) if bands[n] == lab]) for lab in ORDER]
axes[0].set_yticks(centre, ORDER, fontsize=8)
axes[0].set_ylabel('62 opponents, ordered by the money they bank')
worst = (2 - grids['INC']).sum(axis=1).sort_values(ascending=False).head(8)
place, used = {}, []
for n in sorted(worst.index, key=rows.index):
    y = rows.index(n)
    while any(abs(y - u) < 2.6 for u in used):
        y += 1.0
    used.append(y); place[n] = y
for n, y in place.items():
    axes[1].annotate(f'{n[:32]}  ({int(worst[n])})', xy=(63.5, rows.index(n)),
                     xytext=(67, y), fontsize=6.5, va='center', color=INK,
                     annotation_clip=False,
                     arrowprops=dict(arrowstyle='-', lw=.5, color='#999999'))
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cmap.colors]
axes[0].legend(handles, ['lost both seats', 'split', 'won both seats'], frameon=False,
               fontsize=8, loc='upper left', bbox_to_anchor=(0, -.06), ncol=3)
fig.suptitle('The complete matrix: 62 opponents by 64 worlds, two seats a cell', y=.99)
fig.tight_layout(rect=(0, 0, .86, 1)); plt.show()
print('cells that are not a clean sweep, with the count of seats lost out of 128:')
seats_lost = (2 - grids['CAND']).sum(axis=1).sort_values(ascending=False)
print(seats_lost[seats_lost > 0].to_string())

band_of = bands.to_dict()
games['band'] = games.opponent.map(band_of)
ORDER = ['top quarter', 'upper middle', 'lower middle', 'bottom quarter']
full_band = (games.groupby(['band', 'agent'], observed=True)
                  .agg(opponents=('opponent', 'nunique'), games=('margin', 'size'),
                       win_rate=('win', 'mean'), median_margin=('margin', 'median'))
                  .reset_index().pivot(index='band', columns='agent').reindex(ORDER))
print('THE FULL RUN, 15,872 games\n')
print(full_band.round(3).to_string())

lite_games = pd.read_csv(WORK / 'lite_games.csv')
lite_games['win'] = lite_games.margin > 0
lstr = lite_games.groupby('opponent').opponent_bank.median().sort_values()
lbands = pd.qcut(lstr, 4, labels=ORDER[::-1])
lite_games['band'] = lite_games.opponent.map(lbands.to_dict())
lite_band = (lite_games.groupby('band', observed=True)
                       .agg(opponents=('opponent', 'nunique'), games=('margin', 'size'),
                            win_rate=('win', 'mean'), median_margin=('margin', 'median'))
                       .reindex(ORDER))
print('\n\nTHE SAMPLED RUN, the same cut, 240 game sides\n')
print(lite_band.round(3).to_string())
print('\nEach band of the sample holds one or two agents, so the column is a label and not a'
      '\nmeasurement: at this size the quartiles are four names, not four populations.')

lim = 64000
fig, axes = plt.subplots(2, 1, figsize=(11.2, 4.8), sharex=True)
for ax, name in zip(axes, ('CAND', 'INC')):
    d = games[games.agent == name]
    G = d.pivot_table(index='band', columns='world', values='margin', aggfunc='median',
                      observed=True).reindex(index=ORDER, columns=hardest)
    im = ax.imshow(G.values, cmap='RdYlGn', aspect='auto', interpolation='nearest',
                   norm=SymLogNorm(linthresh=2000, vmin=-lim, vmax=lim))
    ax.set_yticks(range(len(ORDER)), ORDER, fontsize=8)
    ax.set_title(f'{name}: median margin in dollars, 28 to 34 games a cell',
                 fontsize=9, loc='left')
    ax.set_xticks([]); ax.grid(False)
    worst = np.unravel_index(np.argmin(G.values), G.shape)
    ax.annotate(f'{G.values[worst]:,.0f} in {G.columns[worst[1]]}',
                xy=(worst[1], worst[0]), xytext=(worst[1] + 3, worst[0] + .85),
                fontsize=7, color=INK,
                arrowprops=dict(arrowstyle='-', lw=.6, color=INK))
axes[1].set_xlabel('64 shop worlds, hardest on the left, in the order of the figure above')
cb = fig.colorbar(im, ax=axes, fraction=.02, pad=.01)
cb.set_label('median margin, dollars (symmetric log)', fontsize=8)
plt.show()
floor = (games.groupby(['agent', 'band', 'world'], observed=True).margin.median()
              .groupby(['agent', 'band'], observed=True).min().unstack(0).reindex(ORDER))
print('the worst world of each band, in median margin:')
print(floor.round(0).to_string())

FIELD_GAMES = 'window_games_20260921.csv'
FIELD = DATA / 'examples' / FIELD_GAMES
fg = pd.read_csv(FIELD)
fg['win'] = fg.margin > 0
rank = (fg.groupby('agent')
          .agg(games=('margin', 'size'), win_rate=('win', 'mean'),
               median_margin=('margin', 'median'), median_bank=('bank', 'median'))
          .sort_values('win_rate', ascending=False))
print(f'{fg.agent.nunique()} agents, {len(fg) // 2:,} games, {fg.world.nunique()} worlds, both seats\n')
print('THE TEN THAT WIN MOST')
print(rank.head(10).to_string(float_format=lambda v: f'{v:,.3f}'))
print('\nTHE FIVE THAT WIN LEAST')

W = (fg.pivot_table(index='agent', columns='opponent', values='win', aggfunc='mean'))
order = rank.index
W = W.reindex(index=order, columns=order)
fig, ax = plt.subplots(figsize=(9.6, 8.6))
im = ax.imshow(W.values, cmap='RdYlGn', vmin=0, vmax=1, interpolation='nearest')
ax.set_xticks([]); ax.grid(False)
ax.set_yticks(range(len(order)), [n[:34] for n in order], fontsize=5)
ax.set_xlabel(f'{len(order)} agents, the same order left to right')
ax.set_ylabel('strongest at the top')
ax.set_title('Share of games the row agent took from the column agent')
fig.colorbar(im, ax=ax, fraction=.03, pad=.02).set_label('win rate', fontsize=8)
fig.tight_layout(); plt.show()

ref = list(rank.index[len(rank) // 3: len(rank) // 3 + 12])   # a fixed reference panel
key = (fg[fg.opponent.isin(ref)]
       .pivot_table(index='agent', columns=['opponent', 'seed', 'seat'], values='bank'))
# an agent has no games against itself, so its own columns are empty. Fill before the
# join: a missing value is a float and str.join refuses one, which is the whole bug.
sig = key.round(0).fillna(-1).astype('int64').astype(str).agg('|'.join, axis=1)
fam = collections.Counter(sig)
sizes = collections.Counter(fam.values())
dup = sorted([sorted(sig[sig == s].index) for s, n in fam.items() if n > 1], key=len, reverse=True)
print(f'{len(rank)} files, {len(fam)} distinct behaviours measured against a fixed panel of '
      f'{len(ref)} opponents\n')
for group in dup:
    print(f'  {len(group)} files, one behaviour: ' + ', '.join(g[:30] for g in group))

fig, ax = plt.subplots(figsize=(6.8, 3.2))
ks = sorted(sizes)
ax.bar([str(k) for k in ks], [sizes[k] for k in ks], color=COOL, width=.6)
for k in ks:
    ax.text(str(k), sizes[k], f' {sizes[k]}', ha='center', va='bottom', fontsize=8, color=INK)
ax.set_xlabel('files that behave identically'); ax.set_ylabel('classes')
ax.set_title('The field is fewer opponents than it is files')
fig.tight_layout(); plt.show()

pairs = (fg.groupby(['agent', 'opponent']).win.mean().rename('direct').reset_index())
pairs['gap'] = pairs.agent.map(rank.win_rate) - pairs.opponent.map(rank.win_rate)
pairs = pairs[pairs.gap > 0]                       # one row per unordered pair
ups = pairs[pairs.direct < .5]
fig, ax = plt.subplots(figsize=(7.4, 4.2))
ax.scatter(pairs.gap, pairs.direct, s=8, c=COOL, alpha=.35, edgecolor='none', label='pairing')
ax.scatter(ups.gap, ups.direct, s=16, c=WARM, edgecolor='none', label='upset')
ax.axhline(.5, color=INK, lw=.8, ls=':')
ax.set_xlabel('gap in win rate over the whole field')
ax.set_ylabel('share of the direct games the stronger agent took')
ax.set_title('Upsets against the strength gap')
ax.legend(frameon=False, loc='lower right')
fig.tight_layout(); plt.show()
print(f'{len(ups):,} upsets in {len(pairs):,} pairings, {len(ups) / len(pairs):.1%}')
big = ups.sort_values('gap', ascending=False).head(6)
print('\nthe upsets across the widest strength gap:')
for _, r in big.iterrows():
    print(f'  {r.opponent[:34]:36} beats {r.agent[:34]:36} '
          f'{1 - r.direct:.0%} of the time, {r.gap:.0%} below it overall')

seat = (games.assign(win=games.margin > 0)
             .pivot_table(index=['agent', 'opponent'], columns='seat', values='win', aggfunc='mean')
             .reset_index())
seat.columns = ['agent', 'opponent', 's0', 's1']
fig, ax = plt.subplots(figsize=(5.4, 5.2))
for name, colour, mark in (('CAND', COOL, 'o'), ('INC', WARM, '^')):
    d = seat[seat.agent == name]
    ax.scatter(d.s0, d.s1, s=28, c=colour, marker=mark, alpha=.7, edgecolor='none', label=name)
ax.plot([0, 1], [0, 1], color=INK, lw=.9, ls='--')
ax.set_xlabel('win rate in seat 0'); ax.set_ylabel('win rate in seat 1')
ax.set_title('Win rate in seat 0 against seat 1, one point per opponent')
ax.legend(frameon=False, loc='lower right')
gap = (seat.s1 - seat.s0).abs()
ax.text(.03, .92, f'median seat gap {gap.median():.1%}\nlargest {gap.max():.0%}',
        transform=ax.transAxes, fontsize=8, color=INK)
fig.tight_layout(); plt.show()

rng = np.random.default_rng(7)
truth = {}
draws = {}
for name in ('CAND', 'INC'):
    d = games[games.agent == name]
    truth[name] = (d.margin > 0).mean()
    seeds = d.seed.unique()
    got = []
    for _ in range(2000):
        pick = rng.choice(seeds, size=4, replace=False)
        got.append((d[d.seed.isin(pick)].margin > 0).mean())
    draws[name] = np.array(got)
fig, ax = plt.subplots(figsize=(7.2, 3.6))
for name, colour in (('CAND', COOL), ('INC', WARM)):
    ax.hist(draws[name], bins=40, alpha=.55, color=colour, label=f'{name}, four worlds')
    ax.axvline(truth[name], color=colour, lw=1.6)
ax.set_xlabel('win rate a four-world sample would have reported')
ax.set_ylabel('draws out of 2,000')
ax.set_title('Vertical lines are the true value over all 64 worlds')
ax.legend(frameon=False)
fig.tight_layout(); plt.show()
for name in ('CAND', 'INC'):
    lo, hi = np.percentile(draws[name], [2.5, 97.5])
    print(f'{name}: true {truth[name]:.1%}, four-world 95% range {lo:.1%} to {hi:.1%} '
          f'(width {hi-lo:.1%})')

w = json.loads((DATA / 'examples' / 'weights_one_per_behaviour.json').read_text())
ease = per.groupby('opponent').win_rate.mean()
schemes = {'every opponent equal': lambda o: 1.0,
           'one vote per behaviour': lambda o: w.get(o, 1.0),
           'skewed to the easy half': lambda o: 1.0 / (2.0 - ease.get(o, 1.0))}
tab = []
for label, fn in schemes.items():
    row = {'weighting': label}
    for ag, d in per.groupby('agent'):
        num = sum(fn(o) * r for o, r in zip(d.opponent, d.win_rate))
        row[ag] = round(num / sum(fn(o) for o in d.opponent), 4)
    row['gap'] = round(row['CAND'] - row['INC'], 4)
    tab.append(row)
weighted = pd.DataFrame(tab).set_index('weighting')
fig, ax = plt.subplots(figsize=(6.6, 3.0))
x = np.arange(len(weighted))
ax.bar(x - .18, weighted.CAND, .34, color=COOL, label='CAND')
ax.bar(x + .18, weighted.INC, .34, color=WARM, label='INC')
ax.set_xticks(x); ax.set_xticklabels(weighted.index, fontsize=8)
ax.set_ylim(.9, 1.0); ax.set_ylabel('weighted win rate')
ax.set_title('Weighted win rate under three populations', loc='right', fontsize=9)
ax.legend(frameon=False, loc='lower left', bbox_to_anchor=(0, 1.0), ncol=2, fontsize=8)
fig.tight_layout(); plt.show()
weighted

tel = json.loads((DATA / 'examples' / 'telemetry_one_game.json').read_text())
live = {k: v for k, v in sorted(tel.items()) if v}
show = ['sell_zero_fill', 'shed_discarded_units', 'hand_pass_turns', 'farmer_pass_turns',
        'fertilizer_forgone', 'dead_actions', 'silent_loss_units', 'silent_loss_coins',
        'sold_units', 'sell_revenue', 'plant_unwatered_days', 'idle_tile_days']
print(f'{len(tel)} counters, {len(live)} non-zero in this game. The ones worth a look first:')
for k in show:
    if k in tel:
        print(f'   {k:<26}{tel[k]:>12,.0f}')

try:
    import kagsim, time
    P = {'farmer': ['PASS'], 'hands': [], 'market': []}

    def bench(mode, n, reps=3):
        # best of three: a shared worker's noise is one-sided, so the minimum is the
        # honest estimate of the cost and the mean is an estimate of the neighbours
        best = float('inf')
        for _ in range(reps):
            t0 = time.perf_counter()
            for s in range(n):
                g = kagsim.Game(s)
                while not g.done:
                    g.step(P, P)
                    if mode == 'step':
                        dict(g.telemetry(0))
                if mode == 'game':
                    dict(g.telemetry(0)); dict(g.telemetry(1))
            best = min(best, (time.perf_counter() - t0) / n * 1e3)
        return best

    base, once, every = bench('never', 60), bench('game', 60), bench('step', 8)
    print(f'never read          {base:5.2f} ms a game')
    print(f'once per game       {once:5.2f} ms a game   ({once / base:.2f}x)')
    print(f'after every step    {every:5.2f} ms a game   ({every / base:.2f}x)')
except ImportError:
    print('the C++ engine is not installed here, so this benchmark is skipped;',
          'the table above was measured at 0.61, 0.64 and 3.22 ms a game')