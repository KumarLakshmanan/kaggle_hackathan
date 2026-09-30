"""Native execution parity and the complete saved target gate for each arm."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.observed_hire_recovery_20260928.screen import read, write, sha, PARENTS, MANIFEST, FULL
from diagnostics.opening_probe_v2_20260928.qualify import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):
    return row['version'], row['rival'], row['candidate_seat']


def run(phase, workers):
    pool = read(HERE / 'pool.json'); screen = read(HERE / 'screen.json')
    assert screen['complete'] and screen['clean'] and all(r['passed'] for r in screen['summaries'])
    assert screen['pool_sha256'] == sha(HERE / 'pool.json') and screen['helper_sha256'] == pool['helper_sha256']
    assert pool['plan_sha256'] == sha(HERE / 'PLAN.md') and pool['layer_sha256'] == sha(HERE / 'layer.py')
    assert sha(MANIFEST) == pool['target_manifest_sha256'] and sha(FULL) == pool['native_source_full_sha256']
    assert all(sha(p) == digest for p, digest in PARENTS.values())
    assert all(sha(a['candidate']) == a['candidate_sha256'] == sha(a['backup']) for a in pool['arms'].values())
    destination = HERE / ('native_' + phase + '.json'); assert not destination.exists()
    manifest, parent_full = read(MANIFEST), read(FULL)
    fixtures = pool['fixtures'] if phase == 'parity' else manifest['live_losses'] + manifest['current_top20']
    parent_rows = {(r['rival'], r['candidate_seat']): r for r in parent_full['games']}
    fast = {(r['version'], r['fixture_id'], r['candidate_seat']): r for r in screen['games']}
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), screen_sha256=sha(HERE / 'screen.json'),
                    qualify_helper_sha256=sha(__file__), plan_sha256=pool['plan_sha256'])
    jobs = []
    for version, arm in pool['arms'].items():
        for fixture in fixtures:
            for seat in (0, 1):
                prior = (parent_rows[(fixture['fixture_id'], seat)] if version == 'integrated' else
                         next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat'] == seat))
                jobs.append(dict(version=version, rival=fixture['fixture_id'], team=fixture['team'],
                                 panel='loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                                 seed=int(fixture['seed']), candidate_seat=seat, path=arm['candidate'],
                                 candidate_sha256=arm['candidate_sha256'], opponent='rawroute:' + fixture['source_action_tape_path'],
                                 opponent_action_sha256=fixture['source_opponent_action_sha256'], parent_sha256=arm['parent_sha256'],
                                 parent_result=prior['result'], parent_margin=prior['margin'], **bindings))
    expected = {key(j): j for j in jobs}; assert len(expected) == len(jobs)
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    if checkpoint.exists():
        rows = [json.loads(line) for line in checkpoint.read_text().splitlines()]
    elif phase == 'full':
        parity = read(HERE / 'native_parity.json'); assert parity['complete'] and parity['passed']
        assert all(parity[k] == v for k, v in bindings.items())
        rows = parity['games']
        checkpoint.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    else:
        rows = []
    for row in rows:
        assert all(row[k] == v for k, v in expected[key(row)].items())
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    pending = [j for j in jobs if key(j) not in done]
    print('Native hire', phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as out:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play, j) for j in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row); out.write(json.dumps(row) + '\n'); out.flush()
                    if len(rows) % 2 == 0:
                        print('Native hire', phase, len(rows), '/', len(jobs), row['version'], row['team'], row['result'], row['margin'], flush=True)
    fields = ('candidate_reward', 'opponent_reward', 'frames', 'candidate_status', 'opponent_status', 'candidate_telemetry')
    mismatches = [dict(key=key(r), fields=[f for f in fields if r[f] != fast[key(r)][f]]) for r in rows
                  if key(r) in fast and any(r[f] != fast[key(r)][f] for f in fields)]
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE'
                and not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    summaries = []
    for version in pool['arms']:
        arm = [r for r in rows if r['version'] == version]
        regressions = [key(r) for r in arm if r['parent_result'] == 'win' and r['result'] != 'win']
        panels = []
        for panel in ('loss30', 'top20'):
            games = [r for r in arm if r['panel'] == panel]
            ids = sorted({r['rival'] for r in games})
            pairs = {fid: [r for r in games if r['rival'] == fid] for fid in ids}
            assert all(len(pair) == 2 for pair in pairs.values())
            rescues = [fid for fid, pair in pairs.items() if all(r['result'] == 'win' for r in pair)
                       and any(r['parent_result'] != 'win' for r in pair)]
            panels.append(dict(panel=panel, fixtures=len(ids), both_seat_wins=sum(all(r['result'] == 'win' for r in pair) for pair in pairs.values()),
                               WDL=[sum(r['result'] == s for r in games) for s in ('win', 'draw', 'loss')], rescued=rescues))
        summaries.append(dict(version=version, passed=clean and not mismatches and not regressions and any(p['rescued'] for p in panels),
                              regressions=regressions, panels=panels))
    result = dict(complete=len(rows) == len(jobs), passed=clean and not mismatches and all(s['passed'] for s in summaries),
                  clean=clean, fast_native_mismatches=mismatches, summaries=summaries, games=sorted(rows, key=key),
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(destination, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('parity', 'full'))
    parser.add_argument('--workers', type=int, default=2); args = parser.parse_args()
    with exclusive_run(HERE / 'qualify.lock'):
        run(args.phase, args.workers)
