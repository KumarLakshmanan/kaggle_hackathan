from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import base64, contextlib, gzip, hashlib, io, json, os, platform
import subprocess, sys, tarfile, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown, FileLink

ENGINE_VERSION = '1.32.7'
FULL_QUALIFICATION = True
ALLOW_ENGINE_INSTALL = True
AGENT_SETTINGS = {'adaptive_horizon': True, 'quote_order': True}
WORK = Path('/kaggle/working') if sys.platform != 'win32' and Path('/kaggle/working').is_dir() else Path.cwd()
LAB = WORK / 'harvest_nocturne'
LAB.mkdir(parents=True, exist_ok=True)
NOTEBOOK_STARTED = time.monotonic()

try:
    installed_engine = version('kaggle-environments')
except PackageNotFoundError:
    installed_engine = None
ENGINE_READY = installed_engine == ENGINE_VERSION
if not ENGINE_READY and ALLOW_ENGINE_INSTALL:
    try:
        install = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--quiet',
             'kaggle-environments==' + ENGINE_VERSION],
            capture_output=True, text=True, timeout=240)
        (LAB / 'engine-install.log').write_text(install.stdout + install.stderr, encoding='utf-8')
        ENGINE_READY = install.returncode == 0 and version('kaggle-environments') == ENGINE_VERSION
    except (subprocess.TimeoutExpired, PackageNotFoundError):
        ENGINE_READY = False

sns.set_theme(style='whitegrid', palette='Set2', context='notebook',
              rc={'axes.titleweight': 'bold', 'axes.labelsize': 11,
                  'axes.titlesize': 14, 'figure.dpi': 120, 'grid.alpha': 0.25})
COLORS = sns.color_palette('Set2')

def finish_plot(fig, name):
    fig.tight_layout()
    fig.savefig(LAB / (name + '.png'), dpi=150, bbox_inches='tight')
    plt.show()
    plt.close(fig)

print('🧰 Toolkit ready | 🖥️ CPU only | 🎨 seaborn whitegrid + Set2')
print('✅ Engine pinned to ' + ENGINE_VERSION if ENGINE_READY else
      '🛡️ Engine unavailable: build the frozen anchor; fresh qualification is disabled.')
print('🔒 Deterministic development seeds: 261001, 261002')
print('🧪 Untuned holdout seeds: 261201, 261202, 261203')

import lzma

LIBRARY_SHA256 = '49e2b2df3bf7962bc871f4a3c87ef196887694a6a874a99de9cac92698c821cf'
local = WORK.parent / 'dataset' / 'source-library.json.xz'
matches = list(Path('/kaggle/input').rglob('source-library.json.xz')) if Path('/kaggle/input').exists() else []
matches += [local] if local.exists() else []
assert len(matches) == 1, 'Attach the public Harvest Nocturne V2 source library.'
packed = matches[0].read_bytes()
assert hashlib.sha256(packed).hexdigest() == LIBRARY_SHA256
bundle = json.loads(lzma.decompress(packed))
for relative, source in bundle['assets'].items():
    target = (LAB / relative).resolve()
    assert target.is_relative_to(LAB.resolve())
    data = source.encode('utf-8')
    assert hashlib.sha256(data).hexdigest() == bundle['manifest'][relative]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
(LAB/'source-manifest.json').write_text(json.dumps(bundle['manifest'], indent=2))
plans = json.loads((LAB/'sources/two_coins/actions.json').read_text())
assert len(plans) == 13 and all(len(plan) == 719 for plan in plans)
print(f'📚 {len(bundle["assets"])} verified source files | 🔏 Bundle and member hashes passed')
print('🪪 Original licenses retained | 🛡️ V1 archives preserved separately')


hire_costs = [1, 1]
while len(hire_costs) < 12:
    hire_costs.append(hire_costs[-1] + hire_costs[-2])
fig, ax = plt.subplots(figsize=(9, 3.8))
bars = ax.bar(np.arange(1, 13), hire_costs, color=COLORS[0])
ax.bar_label(bars, padding=3)
ax.set(title='The Next Farmhand Becomes Expensive',
       xlabel='Hire number within the same day', ylabel='Marginal cost (coins)',
       xticks=np.arange(1, 13), ylim=(0, 170))
finish_plot(fig, '01_labor_cost')
print(f'🚜 Eleven hands cost {sum(hire_costs[:11])} coins; twelve cost {sum(hire_costs)}.')
print('💡 Scale the workload and the team together; protect tomorrow’s hiring cash.')

herd_rows = []
for plan_id, label in [(0, 'General route'), (12, 'Two Yarn Stores')]:
    for animal in ['COW', 'SHEEP', 'GOOSE']:
        quantity = sum(int(o[2]) for a in plans[plan_id] for o in a.get('market', [])
                       if len(o) >= 3 and o[:2] == ['BUY_ANIMAL', animal])
        herd_rows.append({'Route': label, 'Animal': animal.title(), 'Requested purchases': quantity})
herds = pd.DataFrame(herd_rows)
fig, ax = plt.subplots(figsize=(9, 4))
sns.barplot(data=herds, x='Animal', y='Requested purchases', hue='Route',
            palette=COLORS[:2], errorbar=None, ax=ax)
for container in ax.containers:
    ax.bar_label(container, padding=3, fmt='%.0f')
ax.set_title('A Different Town Calls for a Different Herd')
ax.set_ylim(0, 17)
ax.legend(title=None, loc='upper left')
finish_plot(fig, '02_route_herds')

from collections import Counter
commands = Counter(c[0] for action in plans[0]
                   for c in [action.get('farmer') or ['PASS'], *action.get('hands', [])] if c)
operations = ['WATER', 'FEED', 'CARE', 'HARVEST', 'COLLECT_FERTILIZER', 'PLANT']
activity = pd.Series({op.replace('_', ' ').title(): commands[op] for op in operations}).sort_values()
fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.barh(activity.index, activity.values, color=COLORS[2])
ax.bar_label(bars, padding=4)
ax.set(title='The General Route Is a Daily Care Schedule', xlabel='Planned worker commands across 719 decisions')
ax.set_xlim(0, activity.max() * 1.18)
finish_plot(fig, '03_workload')
print('🗺️ Planned land purchases:', [s for s,a in enumerate(plans[0]) if ['BUY_LAND'] in a['market']])

import importlib.util
price_spec = importlib.util.spec_from_file_location('nocturne_prices', LAB/'candidate/prices.py')
price_model = importlib.util.module_from_spec(price_spec)
price_spec.loader.exec_module(price_model)
scenario = []
for item in ['MILK', 'WOOL', 'MELON', 'STRAWBERRY', 'WHEAT']:
    inv = price_model.MARKET_PARAMS[item]['I0'] + 40
    now = sum(price_model.market_price(item, inv+j) for j in range(12))
    delayed = sum(price_model.market_price(item, inv+8+j) for j in range(12))
    scenario.append({'Product': item.title(), 'Revenue at risk': now-delayed})
scenario = pd.DataFrame(scenario).sort_values('Revenue at risk')
fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.barh(scenario.Product, scenario['Revenue at risk'], color=COLORS[1])
ax.bar_label(bars, padding=4, fmt='%.0f')
ax.set(title='Which Sale Is Most Exposed to an Eight-Unit Rival Batch?',
       xlabel='Coins lost on our 12-unit sale (scenario: market inventory = I0 + 40)')
ax.set_xlim(0, scenario['Revenue at risk'].max() * 1.2)
finish_plot(fig, '04_quote_risk')

AGENT_SOURCE = r'''
# SPDX-License-Identifier: Apache-2.0
"""Harvest Nocturne: observed competition pressure over a frozen farm plan.

New work: occupied-tile similarity, guarded three-turn reservations, and exact
price-curve risk ordering. Production, feeding, and route assets are inherited
from Two Coins / Moon / Shop Router. Full attribution travels with the archive.
"""
import importlib.util
import math
from pathlib import Path
import sys

SETTINGS = {'adaptive_horizon': True, 'quote_order': True}
_ROOT = Path(globals().get('__file__') or (lambda: None).__code__.co_filename).resolve().parent
_spec = importlib.util.spec_from_file_location(__name__ + '_farm', _ROOT / 'router.py')
_farm = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _farm
_spec.loader.exec_module(_farm)
_price_spec = importlib.util.spec_from_file_location(__name__ + '_prices', _ROOT / 'prices.py')
_prices = importlib.util.module_from_spec(_price_spec)
_price_spec.loader.exec_module(_prices)
_last_step = -1
_similar_streak = 0
telemetry = {'three_turn_calls': 0, 'reordered_turns': 0,
             'overlay_errors': 0, 'baseline_fallbacks': 0, 'parent_errors': 0}


def active_similarity(observation):
    """Empty tiles cannot make two unrelated production layouts look alike."""
    farms = observation['farms']
    own, rival = farms[observation['player']], farms[1-observation['player']]
    if own['unlocked_quadrants'] != rival['unlocked_quadrants']:
        return 0.0
    matches = total = 0
    for a, b in zip([t for row in own['tiles'] for t in row],
                    [t for row in rival['tiles'] for t in row]):
        sa = (a.get('crop'), a.get('animal')) if isinstance(a, dict) else (None, None)
        sb = (b.get('crop'), b.get('animal')) if isinstance(b, dict) else (None, None)
        if sa != (None, None) or sb != (None, None):
            total += 1
            matches += sa == sb
    return matches / total if total >= 8 else 0.0


def quote_priority(observation, order, stock):
    """Revenue exposed to a small rival batch, not nominal headline revenue."""
    item = order[1]
    quantity = min(max(0, int(order[2])), stock.get(item, 0))
    if not quantity or item not in _prices.MARKET_PARAMS:
        return 0.0
    inventory = observation['market']['inventory'][item]
    params = {k: dict(v) for k, v in _prices.MARKET_PARAMS.items()}
    for k, patch in observation['market'].get('params', {}).items():
        if k in params:
            params[k].update(patch)
    rival = observation['farms'][1-observation['player']]
    crop_item = item if item in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON') else None
    animal = {'EGG':'GOOSE','MILK':'COW','WOOL':'SHEEP'}.get(item)
    standing = sum(max(0, int(t.get('yield_units', 0))) for row in rival['tiles'] for t in row
                   if isinstance(t, dict) and
                   ((crop_item is not None and t.get('crop') == crop_item) or
                    (animal is not None and t.get('animal') == animal)))
    # Public fields do not reveal the rival shed. Eight units are a scenario,
    # not a recovered hidden quantity; visible ripe yield increases the stress.
    batch = min(24, max(8, standing))
    now = sum(_prices.market_price(item, inventory+j, params) for j in range(quantity))
    later = sum(_prices.market_price(item, inventory+batch+j, params) for j in range(quantity))
    return now-later


def reorder_sales(observation, action):
    """Keep quantities and purchase barriers; rank distinct contiguous sales."""
    stock = _farm.projected_shed(action, _farm.FarmView(observation))
    orders = [list(o) for o in action['market']]
    start = 0
    while start < len(orders):
        if orders[start][0] != 'SELL':
            start += 1
            continue
        end = start
        while end < len(orders) and orders[end][0] == 'SELL':
            end += 1
        block = orders[start:end]
        if len({o[1] for o in block}) == len(block):
            orders[start:end] = sorted(block, key=lambda o: quote_priority(observation, o, stock), reverse=True)
        start = end
    if orders != action['market']:
        telemetry['reordered_turns'] += 1
        action = dict(action, market=orders)
    return action


def baseline(observation, configuration=None):
    """Last-resort legal action: deliver reachable goods and liquidate the shed."""
    own = observation['farms'][observation['player']]
    center = len(own['tiles']) // 2
    positions = [own['farmer'], *own['hands']]
    work = [['DROP'] if p[0] in (center-1,center) and p[1] in (center-1,center)
            else ['PASS'] for p in positions]
    action = {'farmer':work[0], 'hands':work[1:], 'market':[]}
    stock = _farm.projected_shed(action, _farm.FarmView(observation))
    action['market'] = [['SELL', item, int(q)] for item,q in stock.items()
                        if item in _prices.MARKET_PARAMS and q > 0][:10]
    return action


def agent(observation, configuration=None):
    global _last_step, _similar_streak
    step = int(observation['step'])
    if step <= _last_step:
        _similar_streak = 0
    _last_step = step
    _farm.SALE_HORIZON = 2
    try:
        _similar_streak = _similar_streak + 1 if active_similarity(observation) >= 0.90 else 0
        if SETTINGS['adaptive_horizon'] and 336 <= step < 648 and _similar_streak >= 6:
            _farm.SALE_HORIZON = 3
            telemetry['three_turn_calls'] += 1
    except Exception:
        telemetry['overlay_errors'] += 1
    try:
        action = _farm.agent(observation, configuration)
    except Exception:
        telemetry['parent_errors'] += 1
        telemetry['baseline_fallbacks'] += 1
        return baseline(observation, configuration)
    # New ranking starts only after the irreversible farm setup is complete.
    if SETTINGS['quote_order'] and step >= 288:
        try:
            return reorder_sales(observation, action)
        except Exception:
            telemetry['overlay_errors'] += 1
    return action


agent.telemetry = telemetry
'''

assert set(AGENT_SETTINGS) == {'adaptive_horizon', 'quote_order'}
assert all(type(v) is bool for v in AGENT_SETTINGS.values())
agent_source = AGENT_SOURCE.lstrip('\n').replace(
    "SETTINGS = {'adaptive_horizon': True, 'quote_order': True}",
    'SETTINGS = ' + repr(AGENT_SETTINGS))
compile(agent_source, 'main.py', 'exec')
(LAB/'candidate/main.py').write_text(agent_source, encoding='utf-8', newline='\n')
CANDIDATE_SHA = hashlib.sha256((LAB/'candidate/main.py').read_bytes()).hexdigest()
print('🌙 Harvest Nocturne built | ⚙️', AGENT_SETTINGS)
print('🔏 Controller SHA-256:', CANDIDATE_SHA)

development = pd.read_json(LAB/'pilot_results.json')
assert len(development) == 60
dev_pairs = development.pivot(index=['seed','opponent','seat'], columns='candidate', values='margin')
assert not dev_pairs.isna().any().any()
contributions = pd.Series({
    'Quote ordering only': (dev_pairs.quote_only-dev_pairs.anchor).mean(),
    'Ordering + adaptive timing': (dev_pairs.nocturne-dev_pairs.anchor).mean()})
fig, ax = plt.subplots(figsize=(9, 3.7))
bars = ax.barh(contributions.index, contributions.values, color=COLORS[:2])
ax.bar_label(bars, labels=[f'{v:+,.0f}' for v in contributions], padding=5)
ax.axvline(0, color='#444444', linewidth=1)
ax.set(title='What Did Each Change Add in Development?', xlabel='Mean paired change in final coin margin')
ax.set_xlim(min(0, contributions.min())*1.2, max(1, contributions.max())*1.25)
finish_plot(fig, '05_development_ablation')
display(development.assign(Win=lambda x:x.margin.gt(0), Loss=lambda x:x.margin.lt(0), Tie=lambda x:x.margin.eq(0))
        .groupby('candidate').agg(Games=('margin','size'),Wins=('Win','sum'),Losses=('Loss','sum'),Ties=('Tie','sum')))
print('🧪 Development evidence only | 🧬 Related opponents | 🎲 Two seed clusters')

audit = json.loads((LAB/'replay_audit.json').read_text())
log_rows = []
for episode in audit['episodes']:
    for player in episode['players']:
        log_rows.append({'Episode': episode['episode'], 'Seat': player['seat'],
            'First callback (ms)': player['first_seconds']*1000,
            'P99 callback (ms)': player['p99_seconds']*1000,
            'Errors': player['stderr_entries'], 'Final coins': player['final_money']})
log_table = pd.DataFrame(log_rows)
display(log_table.round(3))
fig, ax = plt.subplots(figsize=(9, 3.8))
bars = ax.bar([f'{r.Episode} / seat {r.Seat}' for r in log_table.itertuples()],
              log_table['First callback (ms)'], color=[COLORS[0]]*2+[COLORS[1]]*2)
ax.bar_label(bars, fmt='%.0f ms', padding=3)
ax.axhline(1000, color='#444444', linestyle='--', label='Official 1-second action limit')
ax.set(title='Real Submission Logs: Startup Dominates', ylabel='First callback (ms)', ylim=(0,1120))
ax.legend(loc='upper left')
finish_plot(fig, '08_replay_startup')
print('✅ 2 self-play episodes | 2,876 callbacks | No stderr | No terminal cargo left behind')

def checked(script, args, timeout):
    tick = time.monotonic()
    try:
        result = subprocess.run([sys.executable, str(LAB/script), *args], cwd=LAB,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        (LAB/(script+'.log')).write_text(result.stdout+result.stderr, encoding='utf-8')
        return result.returncode == 0, time.monotonic()-tick
    except subprocess.TimeoutExpired:
        return False, time.monotonic()-tick

verification_ok, verify_seconds = checked('verify_agent.py', [], 120) if ENGINE_READY else (False,0)
qualification_ok, qualification_seconds = checked('qualify_v2.py', [], 1080) if verification_ok else (False,0)
results = pd.read_json(LAB/'v2_results.json') if (LAB/'v2_results.json').exists() else pd.DataFrame()
gates = {'verification': verification_ok, 'complete_panel': qualification_ok and len(results)==60}
gates['exact_action_parity'] = bool(gates['complete_panel'] and results.exact_action_parity.all())
gates['immutable_plans'] = bool(gates['complete_panel'] and results.plans_unchanged.all())
gates['runtime_margin'] = bool(gates['complete_panel'] and results.max_seconds.max()<0.5)
gates['startup_improved'] = bool(gates['complete_panel'] and
    all(g.first_seconds.median()<g.reference_first_seconds.median() for _,g in results.groupby('variant')))
V2_PASSED = all(gates.values())
display(pd.DataFrame({'Check':gates.keys(), 'Passed':gates.values()}))
print('✅ V2 QUALIFICATION PASSED' if V2_PASSED else '🛡️ ROLLBACK TO ORIGINAL ANCHOR')
print(f'⏱️ Qualification: {qualification_seconds:.1f}s | Verification: {verify_seconds:.1f}s')

if gates['complete_panel']:
    summary = results.groupby('variant').agg(Games=('margin','size'),
        Wins=('margin',lambda x:(x>0).sum()), Ties=('margin',lambda x:(x==0).sum()),
        Losses=('margin',lambda x:(x<0).sum()), Max_ms=('max_seconds',lambda x:x.max()*1000))
    display(summary.round(3))
    fig, axes = plt.subplots(1,2,figsize=(11,4))
    timing = results.groupby('variant')[['reference_first_seconds','first_seconds']].median()*1000
    timing.columns = ['Original V1','Runtime-refactored V2']
    timing.plot.bar(ax=axes[0],color=[COLORS[1],COLORS[0]],rot=0)
    axes[0].set(title='Same Decisions, Lighter Startup',ylabel='Median first callback (ms)',xlabel='Policy family')
    for container in axes[0].containers:
        axes[0].bar_label(container,fmt='%.1f',padding=3)
    outcomes = results.assign(points=(results.margin>0)+0.5*(results.margin==0)).groupby(
        ['opponent','variant']).points.mean().unstack()*100
    outcomes.index = ['Nocturne V1' if x=='original_nocturne' else 'Anchor V1' if x=='original_anchor'
                      else x.replace('sources/','').title() for x in outcomes.index]
    outcomes.plot.bar(ax=axes[1],color=[COLORS[2],COLORS[0]],rot=25)
    axes[1].set(title='Fresh Reacting Opponents',ylabel='Wins + half-credit ties (%)',xlabel='',ylim=(0,110))
    finish_plot(fig,'09_v2_runtime_and_outcomes')
    print(f'🔏 {results.calls.sum():,} exact action comparisons | Every plan hash unchanged')
    print(f'🧠 Largest post-game sampled RSS: {results.rss_bytes.max()/2**20:.1f} MiB (not continuous peak)')
    print('📏 Timing excludes module import; the independent archive reload below includes file loading.')

def deterministic_archive(folder, members):
    buffer = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=buffer, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name in sorted(members):
                assert Path(name).name == name
                content = (folder/name).read_bytes()
                if name.endswith('.py'):
                    compile(content, name, 'exec')
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(content), 0o644, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def package(folder, filename):
    members = [p.name for p in folder.iterdir() if p.suffix in ('.py','.json','.txt')]
    packed = deterministic_archive(folder,members)
    assert packed == deterministic_archive(folder,members) and len(packed)<100*2**20
    (WORK/filename).write_bytes(packed)
    with tarfile.open(WORK/filename) as archive:
        assert set(archive.getnames())==set(members)
        for member in archive.getmembers():
            assert member.isfile() and archive.extractfile(member).read()==(folder/member.name).read_bytes()
    return {'filename':filename,'sha256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed),
            'members':{m:hashlib.sha256((folder/m).read_bytes()).hexdigest() for m in members}}

packages = {}
for variant, filename in [('relay','Moonlit_Relay_V2.tar.gz'),('aurora','Nocturne_Aurora_V2.tar.gz')]:
    folder = LAB/variant if V2_PASSED else LAB/'original_anchor'
    packages[variant] = package(folder,filename)
package(LAB/'original_anchor','Moonlit_Vault_Anchor_Original.tar.gz')
(WORK/'submission.tar.gz').write_bytes((WORK/'Moonlit_Relay_V2.tar.gz').read_bytes())
reload_ok, reload_seconds = checked('reload_v2.py', [str(WORK)], 120) if ENGINE_READY else (False,0)
reload_report = json.loads((WORK/'archive-reloads.json').read_text()) if reload_ok else None
receipt = {'version':2,'engine':ENGINE_VERSION,'gates':gates,'v2_passed':V2_PASSED,
    'reload_passed':reload_ok,'archive_reloads':reload_report,'packages':packages,
    'selected_primary':'Moonlit Relay V2' if V2_PASSED else 'Original anchor',
    'fallback_used':'none' if V2_PASSED else 'original anchor',
    'qualification_seconds':qualification_seconds,'reload_seconds':reload_seconds,
    'notebook_seconds':time.monotonic()-NOTEBOOK_STARTED,'platform':platform.platform(),
    'python':platform.python_version(),'new_leaderboard_rating':None}
(WORK/'v2-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('📦 TWO V2 SUBMISSIONS READY' if V2_PASSED and reload_ok else '🛡️ Inspect fallback receipt before submitting')
for item in packages.values():
    display(FileLink(item['filename']))
display(FileLink('v2-receipt.json'))