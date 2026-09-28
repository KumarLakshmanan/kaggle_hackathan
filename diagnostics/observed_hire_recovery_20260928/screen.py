from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

PARENTS = {'main': (ROOT / 'main.py', '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
           'integrated': (ROOT / 'main_candidate_public_loss_routes_20260928_8dde995d.py',
                          '8dde995de6430dcdb7c3dae57bc7a42885ea1b230583c9b0eaf062d1361d3432')}
MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
FULL = ROOT / 'diagnostics/public_loss_route_pool_20260928/native_full.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def prepare():
    assert sha(MANIFEST) == '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    assert sha(FULL) == 'a01df893b3e032aa9aa017360fecc2039308bc58e7dd12595852e6bcfc21de89'
    assert all(sha(p) == digest for p, digest in PARENTS.values())
    manifest = read(MANIFEST); full = read(FULL); all_fixtures = manifest['live_losses'] + manifest['current_top20']
    ids = ['live-114254310', 'live-114283577', 'live-114227779', 'top20-01-DECEM-114267880',
           'top20-03-Boey-114266440', 'top20-06-Majkel1337-114263239']
    fixtures = [next(f for f in all_fixtures if f['fixture_id'] == fid) for fid in ids]
    arms = {}
    for version, (path, digest) in PARENTS.items():
        blob = path.read_bytes() + b'\n' + (HERE / 'layer.py').read_bytes()
        candidate = HERE / ('candidate_' + version + '.py')
        compile(blob, str(candidate), 'exec')
        with candidate.open('xb') as f:
            f.write(blob)
        candidate_sha = sha(candidate)
        backup = ROOT / ('main_candidate_hire_recovery_' + version + '_20260928_' + candidate_sha[:8] + '.py')
        with backup.open('xb') as f:
            f.write(blob)
        arms[version] = dict(candidate=str(candidate), candidate_sha256=candidate_sha, backup=str(backup), parent_sha256=digest)
    controls = {'main': [], 'integrated': []}
    for fixture in fixtures:
        for seat in (0, 1):
            native = next(r for r in full['games'] if r['rival'] == fixture['fixture_id'] and r['candidate_seat'] == seat)
            old = next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat'] == seat)
            controls['integrated'].append(dict(fixture_id=fixture['fixture_id'], candidate_seat=seat,
                                               result=native['result'], margin=native['margin'], candidate_reward=native['candidate_reward'],
                                               opponent_reward=native['opponent_reward']))
            controls['main'].append(dict(fixture_id=fixture['fixture_id'], candidate_seat=seat, **old))
    pool = dict(arms=arms, fixtures=fixtures, controls=controls, plan_sha256=sha(HERE / 'PLAN.md'),
                helper_sha256=sha(__file__), layer_sha256=sha(HERE / 'layer.py'), native_source_full_sha256=sha(FULL),
                target_manifest_sha256=sha(MANIFEST), fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                created_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE / 'pool.json', pool)
    print(json.dumps(arms, indent=2), flush=True)


def job_run(job):
    version, fixture, seat, arm, bindings = job
    trace = HERE / (version + '_' + fixture['fixture_id'] + '_seat' + str(seat) + '.jsonl.gz')
    assert not trace.exists()
    row = play(fixture, arm['candidate'], arm['candidate_sha256'], seat, trace)
    row.update(version=version, team=fixture['team'], trace_path=str(trace), trace_sha256=sha(trace), **bindings)
    return row


def screen(workers):
    pool = read(HERE / 'pool.json')
    assert pool['helper_sha256'] == sha(__file__) and pool['layer_sha256'] == sha(HERE / 'layer.py')
    assert pool['plan_sha256'] == sha(HERE / 'PLAN.md')
    assert all(sha(p) == digest for p, digest in PARENTS.values())
    assert all(sha(arm['candidate']) == arm['candidate_sha256'] == sha(arm['backup']) for arm in pool['arms'].values())
    assert not (HERE / 'screen.json').exists()
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__))
    jobs = [(version, fixture, seat, arm, bindings) for version, arm in pool['arms'].items()
            for fixture in pool['fixtures'] for seat in (0, 1)]
    checkpoint = HERE / 'screen.jsonl'; rows = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done = {(r['version'], r['fixture_id'], r['candidate_seat']) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k, v in bindings.items())
    pending = [j for j in jobs if (j[0], j[1]['fixture_id'], j[2]) not in done]
    with checkpoint.open('a', encoding='utf-8') as out:
        for start in range(0, len(pending), 12):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(job_run, j) for j in pending[start:start+12]]):
                    row = future.result(); rows.append(row); out.write(json.dumps(row) + '\n'); out.flush()
                    print('Observed hire recovery', len(rows), '/24', row['version'], row['team'], row['candidate_seat'],
                          row['result'], row['margin'], row['candidate_telemetry']['hire_recovery_turns'], flush=True)
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' and not r['candidate_errors'] for r in rows)
    summaries = []
    for version in pool['arms']:
        arm = [r for r in rows if r['version'] == version]
        prior = {(r['fixture_id'], r['candidate_seat']): r for r in pool['controls'][version]}
        regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in arm
                       if prior[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' and r['result'] != 'win']
        rescued = [f['fixture_id'] for f in pool['fixtures']
                   if all(r['result'] == 'win' for r in arm if r['fixture_id'] == f['fixture_id'])
                   and any(prior[(f['fixture_id'], seat)]['result'] != 'win' for seat in (0, 1))]
        summaries.append(dict(version=version, passed=clean and not regressions and bool(rescued),
                              rescued=rescued, regressions=regressions,
                              WDL=[sum(r['result'] == s for r in arm) for s in ('win', 'draw', 'loss')]))
    result = dict(complete=len(rows) == len(jobs), clean=clean, summaries=summaries, games=rows,
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(HERE / 'screen.json', result)
    print(json.dumps({k:v for k,v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare', 'screen'))
    parser.add_argument('--workers', type=int, default=2); args = parser.parse_args()
    with exclusive_run(HERE / 'screen.lock'):
        prepare() if args.phase == 'prepare' else screen(args.workers)
