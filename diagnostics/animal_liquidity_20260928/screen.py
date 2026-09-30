"""One frozen candidate, pre-outcome transition parity, then 12 diagnostic games."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import gzip
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.physical_route_rollout_20260928.check import Box, extract
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
SOURCE_SHA = '367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0'
MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
CONTROLS = ROOT / 'diagnostics/observed_hire_recovery_20260928/native_parity.json'
IDS = ['live-114283577', 'live-114254310', 'live-114227779',
       'top20-01-DECEM-114267880', 'top20-03-Boey-114266440',
       'top20-06-Majkel1337-114263239']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def load(path):
    spec = importlib.util.spec_from_file_location('animal_liquidity_validation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(MANIFEST) == '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    assert sha(CONTROLS) == '190e408a0537811d349c5bdcf3e92e39ead130c6f4609122faf619275f888a3a'
    manifest = read(MANIFEST)
    fixtures = [next(f for f in manifest['live_losses'] + manifest['current_top20'] if f['fixture_id'] == fid) for fid in IDS]
    prior = read(CONTROLS)
    assert prior['complete'] and prior['passed']
    controls = [r for r in prior['games'] if r['version'] == 'integrated']
    assert len(controls) == 12 and all(r['candidate_sha256'] == SOURCE_SHA for r in controls)
    candidate = HERE / 'candidate.py'
    data = SOURCE.read_bytes() + b'\n' + (HERE / 'layer.py').read_bytes()
    compile(data, str(candidate), 'exec')
    with candidate.open('xb') as stream:
        stream.write(data)
    pool = dict(candidate=str(candidate), candidate_sha256=sha(candidate), source_sha256=SOURCE_SHA,
                fixtures=fixtures, controls=controls, plan_sha256=sha(HERE / 'PLAN.md'),
                layer_sha256=sha(HERE / 'layer.py'), helper_sha256=sha(__file__),
                source_controls_sha256=sha(CONTROLS), manifest_sha256=sha(MANIFEST),
                fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                created_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE / 'pool.json', pool)
    print(json.dumps({k:v for k,v in pool.items() if k not in ('fixtures', 'controls')}, indent=2), flush=True)


def validate_bindings():
    pool = read(HERE / 'pool.json')
    for key, path in [('candidate_sha256', pool['candidate']), ('source_sha256', SOURCE),
                      ('plan_sha256', HERE / 'PLAN.md'), ('layer_sha256', HERE / 'layer.py'),
                      ('helper_sha256', __file__), ('source_controls_sha256', CONTROLS),
                      ('manifest_sha256', MANIFEST), ('fast_helper_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py')]:
        assert pool[key] == sha(path), (key, path)
    return pool


def transition_check():
    pool = validate_bindings()
    core, provenance = extract()
    # The frozen forecast deliberately ends before midnight transitions.
    # Using the separately extracted native interpreter with only midnight
    # disabled checks execution order, atomic planting and all other mechanics.
    core['_end_of_day'] = lambda *args: None
    module = load(pool['candidate'])
    fixture = pool['fixtures'][0]
    replay = json.loads(gzip.decompress(Path(fixture['source_replay_path']).read_bytes()))
    cfg = dict(replay['configuration'], seed=None)
    del replay
    rows = []
    trace_bindings = {}
    for seat in (0, 1):
        path = ROOT / 'diagnostics/residual_execution_20260928' / ('live-114283577_seat' + str(seat) + '.jsonl.gz')
        trace_bindings[str(path)] = sha(path)
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            frame = next(json.loads(line) for line in stream if json.loads(line)['step'] == 195)
        obs, action = frame['observation'], frame['action']
        schedule = module._hire_recovery_schedule(obs)
        orders = action['market']
        index = next(i for i, order in enumerate(orders) if order[:2] == ['BUY_ANIMAL', 'SHEEP'])
        proposals = [orders] + [orders[:index] + [['SELL', 'WOOL', n]] + orders[index:] for n in (1, 2)]
        for mirror in (False, True):
            for quantity, proposal in enumerate(proposals):
                actual = module._animal_cash_simulate(obs, action, proposal, cfg, mirror, 'SHEEP')
                farms = [copy.deepcopy(obs['farms'][seat]) for _ in (0, 1)]
                farms[1-seat]['money'] = obs['farms'][1-seat]['money']
                market, town = copy.deepcopy(obs['market']), copy.deepcopy(obs['town'])
                state = [Box(status='ACTIVE', reward=0, action={}, observation=Box(farms=farms, market=market, town=town,
                         private=copy.deepcopy(obs['private']), player=i, step=195, day=8, hour=3)) for i in (0, 1)]
                env = Box(configuration=Box(**cfg), done=False, info={})
                snapshots = []
                before = module._animal_cash_owned(farms[seat], state[seat].observation.private, 'SHEEP')
                for turn in range(195, 216):
                    own_action = copy.deepcopy(action if turn == 195 else schedule[turn])
                    other_action = copy.deepcopy(own_action) if mirror else {'farmer':['PASS'], 'hands':[], 'market':[]}
                    if turn == 195:
                        own_action['market'] = copy.deepcopy(proposal)
                    state[seat].action, state[1-seat].action = own_action, other_action
                    for item in state:
                        item.observation.step = turn
                    core['interpreter'](state, env)
                    if turn == 195:
                        acquired = module._animal_cash_owned(farms[seat], state[seat].observation.private, 'SHEEP') - before
                    snapshots.append(module._animal_cash_snapshot(farms[seat], state[seat].observation.private))
                private = state[seat].observation.private
                animals = sum(isinstance(t, dict) and bool(t.get('animal')) for row in farms[seat]['tiles'] for t in row)
                wheat = private['shed'].get('WHEAT', 0) + sum(inv.get('WHEAT', 0) for inv in private['inventories'])
                expected = dict(snapshots=snapshots, acquired=acquired, farm=farms[seat], private=private,
                                own=farms[seat]['money'], rival=farms[1-seat]['money'],
                                feed_reserve=max(0, animals-wheat)*market['prices']['WHEAT'])
                mismatches = [key for key in expected if expected[key] != actual[key]]
                rows.append(dict(seat=seat, mirror=mirror, sold_units=quantity, transitions=len(snapshots), mismatches=mismatches))
    result = dict(passed=all(not r['mismatches'] for r in rows), checks=rows, provenance=provenance,
                  trace_sha256=trace_bindings, pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__),
                  completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE / 'transition_check.json', result)
    print(json.dumps(result, indent=2), flush=True)
    assert result['passed']


def job_run(job):
    fixture, seat, pool, bindings = job
    trace = HERE / (fixture['fixture_id'] + '_seat' + str(seat) + '.jsonl.gz')
    assert not trace.exists()
    row = play(fixture, pool['candidate'], pool['candidate_sha256'], seat, trace)
    row.update(team=fixture['team'], trace_path=str(trace), trace_sha256=sha(trace), **bindings)
    return row


def screen():
    pool = validate_bindings()
    parity = read(HERE / 'transition_check.json')
    assert parity['passed'] and parity['pool_sha256'] == sha(HERE / 'pool.json') and parity['helper_sha256'] == sha(__file__)
    assert not (HERE / 'screen.json').exists()
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__), transition_check_sha256=sha(HERE / 'transition_check.json'))
    jobs = [(fixture, seat, pool, bindings) for fixture in pool['fixtures'] for seat in (0, 1)]
    checkpoint = HERE / 'screen.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}
    assert len(done) == len(rows)
    assert all(all(row[k] == v for k, v in bindings.items()) for row in rows)
    pending = [job for job in jobs if (job[0]['fixture_id'], job[1]) not in done]
    with checkpoint.open('a', encoding='utf-8') as stream, ProcessPoolExecutor(max_workers=1) as executor:
        for row in executor.map(job_run, pending):
            rows.append(row)
            stream.write(json.dumps(row) + '\n'); stream.flush()
            print('Animal liquidity', len(rows), '/12', row['team'], row['candidate_seat'], row['result'], row['margin'],
                  row['candidate_telemetry'].get('animal_cash_turns'), flush=True)
    controls = {(r['rival'], r['candidate_seat']):r for r in pool['controls']}
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' and not r['candidate_errors'] for r in rows)
    regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in rows
                   if controls[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' and r['result'] != 'win']
    rescues = [fid for fid in IDS if all(r['result'] == 'win' for r in rows if r['fixture_id'] == fid)
               and any(controls[(fid, seat)]['result'] != 'win' for seat in (0, 1))]
    for row in rows:
        prior = controls[(row['fixture_id'], row['candidate_seat'])]
        row['parent_result'] = prior['result']
        row['delta_own'] = row['candidate_reward'] - prior['candidate_reward']
        row['delta_rival'] = row['opponent_reward'] - prior['opponent_reward']
        row['delta_margin'] = row['margin'] - prior['margin']
    result = dict(complete=len(rows) == len(jobs), clean=clean, passed=clean and len(rows) == len(jobs) and not regressions and bool(rescues),
                  regressions=regressions, rescues=rescues, games=rows,
                  WDL=[sum(r['result'] == label for r in rows) for label in ('win', 'draw', 'loss')],
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(HERE / 'screen.json', result)
    if result['passed']:
        backup = ROOT / ('main_candidate_animal_liquidity_20260928_' + pool['candidate_sha256'][:8] + '.py')
        with backup.open('xb') as stream:
            stream.write(Path(pool['candidate']).read_bytes())
        assert sha(backup) == pool['candidate_sha256']
    print(json.dumps({k:v for k,v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'transition-check', 'screen'))
    args = parser.parse_args()
    with exclusive_run(HERE / 'screen.lock'):
        {'prepare':prepare, 'transition-check':transition_check, 'screen':screen}[args.phase]()
