from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.opening_probe_v2_20260928.qualify import play, sha, MANIFEST, MANIFEST_SHA

SOURCE_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
GROUPS = {
    'A': {'pair': 'BRUNCH_SPOT|BRUNCH_SPOT', 'original': '113371344', 'teams': ['DECEM', 'Yizhou'], 'live': ['live-114289228']},
    'B': {'pair': 'YARN_STORE|FARMERS_MARKET', 'original': '113661901', 'teams': ['Boey'], 'live': []},
    'C': {'pair': 'SMOOTHIE_SHOP|ICE_CREAM_SHOP', 'original': '113441389', 'teams': ['Vadim Vasilenko', 'Kaggledew Valley'], 'live': []},
}

LAYER = '''

# Commit to a whole schedule after two public shop revelations.
_POOL_REPLACEMENTS = REPLACEMENTS_VALUE
for _pool_key in list(_DATA["route_map"]):
    for _pool_pair, _pool_route in _POOL_REPLACEMENTS.items():
        if _pool_key == _pool_pair or _pool_key.startswith(_pool_pair + "|"):
            _DATA["route_map"][_pool_key] = _pool_route

_POOL_PARENT = agent
_POOL_STATS = {"compatible_pool_turns": 0, "compatible_pool_route": ""}

def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _POOL_STATS.update(compatible_pool_turns=0, compatible_pool_route="")
    result = _POOL_PARENT(observation, configuration)
    pair = "|".join(observation["town"]["unlocked_shops"][:2])
    if step >= 144 and pair in _POOL_REPLACEMENTS:
        _POOL_STATS["compatible_pool_turns"] += 1
        _POOL_STATS["compatible_pool_route"] = str(_POOL_REPLACEMENTS[pair])
    agent.telemetry.update(_POOL_STATS)
    return result

agent.telemetry = {}

def kaggle_compatible_route_pool_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def write_candidate(source, replacements, target):
    blob = source + LAYER.replace('REPLACEMENTS_VALUE', repr(replacements)).encode()
    compile(blob, str(target), 'exec')
    target.write_bytes(blob)
    return sha(target)


def prepare():
    assert not (HERE / 'pool.json').exists()
    source = (ROOT / 'main.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA
    assert sha(MANIFEST) == MANIFEST_SHA
    spec = importlib.util.spec_from_file_location('compatible_pool_source', ROOT / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    folder = HERE / 'candidates'
    folder.mkdir(exist_ok=True)
    records = []
    for group, info in GROUPS.items():
        prefix = module._DATA['routes'][info['original']][:144]
        seen = set()
        for route, actions in sorted(module._DATA['routes'].items()):
            if actions[:144] != prefix:
                continue
            digest = hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            assert len(actions) == 719
            target = folder / (group + '_' + route + '.py')
            candidate_sha = write_candidate(source, {info['pair']: int(route)}, target)
            records.append(dict(group=group, route=route, route_sha256=digest, candidate=str(target), candidate_sha256=candidate_sha))
        assert len(seen) == {'A': 10, 'B': 10, 'C': 12}[group]
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    grouped = {}
    for group, info in GROUPS.items():
        grouped[group] = [f for f in manifest['live_losses'] + manifest['current_top20']
                          if f['fixture_id'] in info['live'] or (f['fixture_id'].startswith('top20-')
                          and any(f['team'] == name or f['team'].startswith(name+' ') for name in info['teams']))]
        assert len(grouped[group]) == {'A': 3, 'B': 1, 'C': 2}[group]
    pool = dict(source_sha256=SOURCE_SHA, manifest_sha256=MANIFEST_SHA, groups=GROUPS, fixtures=grouped,
                plan_sha256=sha(HERE/'PLAN.md'), variants=records)
    (HERE/'pool.json').write_text(json.dumps(pool, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'variants':len(records),'games':sum(2*len(grouped[r['group']]) for r in records),
                      'pool_sha256':sha(HERE/'pool.json')},indent=2))


def run(workers):
    pool = json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    assert sha(ROOT/'main.py') == pool['source_sha256'] == SOURCE_SHA
    assert sha(MANIFEST) == pool['manifest_sha256'] == MANIFEST_SHA
    assert sha(HERE/'PLAN.md') == pool['plan_sha256']
    jobs = []
    for variant in pool['variants']:
        assert sha(variant['candidate']) == variant['candidate_sha256']
        for fixture in pool['fixtures'][variant['group']]:
            for seat in (0, 1):
                baseline = next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat'] == seat)
                jobs.append(dict(version=variant['route'], group=variant['group'], rival=fixture['fixture_id'], team=fixture['team'],
                    seed=int(fixture['seed']), candidate_seat=seat, path=variant['candidate'], candidate_sha256=variant['candidate_sha256'],
                    opponent='rawroute:' + fixture['source_action_tape_path'], opponent_action_sha256=fixture['source_opponent_action_sha256'],
                    baseline_result=baseline['result'], baseline_margin=baseline['margin'], plan_sha256=pool['plan_sha256']))
    def key(row):
        return row['group'], row['version'], row['rival'], row['candidate_seat']
    expected = {key(j):j for j in jobs}
    checkpoint = HERE/'screen.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    for row in rows:
        assert all(row[k] == v for k,v in expected[key(row)].items())
    completed = {key(r) for r in rows}
    assert len(completed) == len(rows)
    pending = [j for j in jobs if key(j) not in completed]
    print(f'{len(rows)}/{len(jobs)} complete; {len(pending)} pending', flush=True)
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play,j) for j in pending[start:start+16]]):
                    row = future.result()
                    rows.append(row)
                    output.write(json.dumps(row,ensure_ascii=False)+'\n')
                    output.flush()
                    if len(rows)%4 == 0:
                        print(f'{len(rows)}/{len(jobs)} {row["group"]}/{row["version"]} {row["team"]} '
                              f'seat{row["candidate_seat"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
    all_done = all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows)
    no_errors = all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    payload = dict(complete=True, game_count=len(rows), all_done=all_done, no_errors=no_errors,
                   pool_sha256=sha(HERE/'pool.json'), plan_sha256=pool['plan_sha256'],games=sorted(rows,key=key))
    (HERE/'screen.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k!='games'},indent=2))


def select():
    assert not (HERE/'CONTROL_FIX.md').exists(), 'Control coverage correction required; use complete_controls.py select'
    pool = json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    screen = json.loads((HERE/'screen.json').read_text(encoding='utf-8'))
    assert screen['complete'] and screen['all_done'] and screen['no_errors']
    assert screen['pool_sha256'] == sha(HERE/'pool.json')
    selections, summaries = {}, []
    for group, info in GROUPS.items():
        fixtures = pool['fixtures'][group]
        incumbent_sweeps = sum(all(r['result']=='win' for r in f['baseline_frozen_tape_both_seat_outcomes']) for f in fixtures)
        incumbent_points = sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0
                               for f in fixtures for r in f['baseline_frozen_tape_both_seat_outcomes'])
        eligible = []
        for variant in [v for v in pool['variants'] if v['group']==group]:
            rows = [r for r in screen['games'] if r['group']==group and r['version']==variant['route']]
            pairs = {r['rival']:[] for r in rows}
            for r in rows: pairs[r['rival']].append(r)
            sweeps = sum(all(r['result']=='win' for r in pair) for pair in pairs.values())
            points = sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in rows)
            regressions = sum(r['baseline_result']=='win' and r['result']!='win' for r in rows)
            delta = sum(r['margin']-r['baseline_margin'] for r in rows)
            item = dict(group=group,route=variant['route'],sweeps=sweeps,win_points=points,regressions=regressions,
                        margin_delta=delta,fixtures=[dict(team=pair[0]['team'],margins=[r['margin'] for r in pair]) for pair in pairs.values()])
            summaries.append(item)
            if regressions==0 and (sweeps,points)>(incumbent_sweeps,incumbent_points): eligible.append(item)
        if eligible:
            best = sorted(eligible,key=lambda r:(-r['sweeps'],-r['win_points'],-r['margin_delta'],r['route']))[0]
            selections[info['pair']] = int(best['route'])
    target_teams = {'DECEM','Boey','Vadim Vasilenko'}
    rescued=[]
    for group,info in GROUPS.items():
        route=selections.get(info['pair'])
        if route is None: continue
        chosen=[r for r in screen['games'] if r['group']==group and r['version']==str(route)]
        for team in target_teams:
            pair=[r for r in chosen if r['team']==team]
            if len(pair)==2 and all(r['result']=='win' for r in pair):rescued.append(team)
    result=dict(complete=True,passed=bool(rescued),selected_replacements=selections,rescued_top20=rescued,
                summaries=summaries,pool_sha256=sha(HERE/'pool.json'),screen_sha256=sha(HERE/'screen.json'))
    if result['passed']:
        source=(ROOT/'main.py').read_bytes()
        assert hashlib.sha256(source).hexdigest()==SOURCE_SHA
        target=HERE/'candidate_selected.py'
        result['candidate']=str(target)
        result['candidate_sha256']=write_candidate(source,selections,target)
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='summaries'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','run','select'))
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    with exclusive_run(HERE / 'search.lock'):
        {'prepare':prepare,'run':lambda:run(args.workers),'select':select}[args.phase]()
