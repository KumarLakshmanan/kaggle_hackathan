"""Direct complete-tape development for the existing observable Farm/Ice gate."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_loss_route_pool_20260928.search import (
    SOURCE, SOURCE_SHA, MAIN_SHA, FULL, context as broad_context, control_maps,
    read, write, sha, now, action_hash, points, play)
from diagnostics.local_target_20260928.run_lock import exclusive_run

INVENTORY_SHA = '2d1417543f6918ff3d48a837229f16160569a9cde5650adf86c69ab0f82c6b94'
BROAD = ROOT / 'diagnostics/public_loss_route_pool_20260928'


def candidate(route, path):
    source = SOURCE.read_bytes(); assert sha(SOURCE) == SOURCE_SHA and b'_FARMICE_POOL_PARENT' not in source
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('ROUTE_VALUE', str(int(route)))
    blob = source + b'\n' + layer.encode('utf-8'); compile(blob, str(path), 'exec')
    with path.open('xb') as output:
        output.write(blob)
    return sha(path)


def prepare():
    broad = broad_context(); assert sha(HERE / 'inventory.json') == INVENTORY_SHA
    inventory = read(HERE / 'inventory.json')
    assert inventory['source_sha256'] == SOURCE_SHA and inventory['source_full_sha256'] == sha(FULL)
    assert inventory['broad_pool_sha256'] == sha(BROAD / 'pool.json')
    assert inventory['broad_control_sha256'] == sha(BROAD / 'controls.json')
    controls = read(BROAD / 'controls.json'); assert controls['complete'] and controls['clean']
    source, original = control_maps(broad)
    fixtures = inventory['fixtures']; assert len(fixtures) == 6
    frozen_controls = []
    for fixture in fixtures:
        for seat in (0, 1):
            idx = (fixture['fixture_id'], seat)
            own, old = source[idx], original[idx]
            assert own['candidate_status'] == own['opponent_status'] == 'DONE' and own['frames'] == 720
            assert own['candidate_telemetry']['farmice_turns'] > 0
            frozen_controls.append(dict(fixture_id=idx[0], candidate_seat=seat, source=own, main=old))
    spec = importlib.util.spec_from_file_location('farmice_pool_source', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert action_hash(module._FARMICE_TAPE) == inventory['source_controller_action_sha256']
    folder = HERE / 'candidates'; folder.mkdir(exist_ok=True); variants = []
    for row in inventory['compatible_routes']:
        route = row['route']; actions = module._DATA['routes'][route]
        assert len(actions) == 719 and actions[:144] == module._FARMICE_TAPE[:144]
        assert action_hash(actions) == row['action_sha256']
        path = folder / (route + '.py')
        variants.append(dict(version=route, route=route, candidate=str(path), candidate_sha256=candidate(route, path),
                             route_sha256=row['action_sha256']))
    assert len(variants) == 15 and len({v['route_sha256'] for v in variants}) == 15
    write(HERE / 'pool.json', dict(created_at_utc=now(), source_sha256=SOURCE_SHA, main_sha256=MAIN_SHA,
          inventory_sha256=INVENTORY_SHA, broad_pool_sha256=sha(BROAD / 'pool.json'),
          controls_sha256=sha(BROAD / 'controls.json'), source_full_sha256=sha(FULL),
          plan_sha256=sha(HERE / 'PLAN.md'), layer_sha256=sha(HERE / 'layer.py'), helper_sha256=sha(__file__),
          fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
          fixtures=fixtures, variants=variants, controls=frozen_controls))
    print('Prepared 15 direct controller variants, 180 games; pool SHA', sha(HERE / 'pool.json'), flush=True)


def context():
    broad_context(); pool = read(HERE / 'pool.json')
    assert sha(HERE / 'inventory.json') == pool['inventory_sha256'] == INVENTORY_SHA
    for field, path in (('plan_sha256', HERE / 'PLAN.md'), ('layer_sha256', HERE / 'layer.py'),
                        ('helper_sha256', Path(__file__)), ('broad_pool_sha256', BROAD / 'pool.json'),
                        ('controls_sha256', BROAD / 'controls.json'), ('source_full_sha256', FULL),
                        ('fast_helper_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py')):
        assert pool[field] == sha(path)
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    return pool


def key(row):
    return row['version'], row['fixture_id'], row['candidate_seat']


def jobs_for(pool):
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), plan_sha256=pool['plan_sha256'], helper_sha256=sha(__file__))
    return [(v, f, seat, bindings) for v in pool['variants'] for f in pool['fixtures'] for seat in (0, 1)]


def run_game(job):
    variant, fixture, seat, bindings = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], team=fixture['team'], seed=fixture['seed'], **bindings)
    return row


def validate(row, job):
    variant, fixture, seat, bindings = job
    assert key(row) == (variant['version'], fixture['fixture_id'], seat)
    assert row['candidate_sha256'] == variant['candidate_sha256'] and all(row[k] == v for k, v in bindings.items())
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors'] and not row.get('opponent_errors')
    telemetry = row['candidate_telemetry']
    assert telemetry['farmice_turns'] > 0 and telemetry['farmice_pool_turns'] == 575
    assert telemetry['farmice_pool_route'] == variant['route']


def run(workers):
    pool = context(); assert not (HERE / 'screen.json').exists()
    jobs = jobs_for(pool); assert len(jobs) == 180
    expected = {(v['version'], f['fixture_id'], s): (v, f, s, b) for v, f, s, b in jobs}
    checkpoint = HERE / 'screen.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        validate(row, expected[key(row)])
    pending = [j for j in jobs if (j[0]['version'], j[1]['fixture_id'], j[2]) not in done]
    print('Controller screen', len(rows), '/180', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(run_game, job) for job in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    validate(row, expected[key(row)]); done.add(key(row)); rows.append(row)
                    if len(rows) % 4 == 0:
                        print('Controller', len(rows), '/180', row['version'], row['team'], row['result'], row['margin'], flush=True)
    report = dict(complete=len(rows)==180, clean=True, pool_sha256=sha(HERE / 'pool.json'),
                  helper_sha256=sha(__file__), completed_at_utc=now(), games=sorted(rows, key=key))
    write(HERE / 'screen.json', report); print('Controller screen complete', flush=True)


def select():
    pool = context(); screen = read(HERE / 'screen.json')
    assert screen['complete'] and screen['clean'] and len(screen['games']) == 180
    assert screen['pool_sha256'] == sha(HERE / 'pool.json')
    controls = {(r['fixture_id'], r['candidate_seat']): r for r in pool['controls']}
    summaries = []
    for variant in pool['variants']:
        rows = [r for r in screen['games'] if r['version'] == variant['version']]; assert len(rows) == 12
        pairs = {f['fixture_id']: [r for r in rows if r['fixture_id']==f['fixture_id']] for f in pool['fixtures']}
        losses = [r for r in rows if r['fixture_id'].startswith('live-')]
        regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in rows if r['result'] != 'win'
                       and any(controls[(r['fixture_id'], r['candidate_seat'])][c]['result']=='win' for c in ('main','source'))]
        sweeps = sum(all(r['result']=='win' for r in rs) for fid,rs in pairs.items() if fid.startswith('live-'))
        summaries.append(dict(version=variant['version'], eligible=not regressions and sweeps>0, regressions=regressions,
            target_sweeps=sweeps, target_points=sum(map(points,losses)),
            all_sweeps=sum(all(r['result']=='win' for r in rs) for rs in pairs.values()), all_points=sum(map(points,rows)),
            target_margin_delta=sum(r['margin']-controls[(r['fixture_id'],r['candidate_seat'])]['source']['margin'] for r in losses)))
    eligible=[r for r in summaries if r['eligible']]
    result=dict(complete=True,passed=bool(eligible),summaries=summaries,pool_sha256=sha(HERE/'pool.json'),
                screen_sha256=sha(HERE/'screen.json'),source_sha256=SOURCE_SHA,completed_at_utc=now())
    if eligible:
        best=min(eligible,key=lambda r:(-r['target_sweeps'],-r['target_points'],-r['all_sweeps'],-r['all_points'],-r['target_margin_delta'],int(r['version'])))
        variant=next(v for v in pool['variants'] if v['version']==best['version'])
        path=HERE/'candidate_selected.py';backup=ROOT/('main_candidate_farmice_tape_20260928_'+variant['candidate_sha256'][:8]+'.py')
        for target in (path,backup):
            with target.open('xb') as output:output.write(Path(variant['candidate']).read_bytes())
            assert sha(target)==variant['candidate_sha256']
        result.update(selected=best,candidate=str(path),candidate_sha256=variant['candidate_sha256'],backup=str(backup))
    write(HERE/'selection.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('prepare','run','select'))
    parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    with exclusive_run(HERE/'search.lock'):
        {'prepare':prepare,'run':lambda:run(args.workers),'select':select}[args.phase]()
