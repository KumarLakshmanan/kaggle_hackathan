"""Original engine execution parity and all 50 saved target regressions."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.animal_liquidity_20260928.screen import read, write, sha, validate_bindings, MANIFEST
from diagnostics.opening_probe_v2_20260928.qualify import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

FULL = ROOT / 'diagnostics/observed_hire_recovery_20260928/native_full.json'
FULL_SHA = '1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545'


def key(row):
    return row['rival'], row['candidate_seat']


def run(phase):
    pool = validate_bindings()
    screen = read(HERE / 'screen.json')
    assert screen['passed'] and screen['complete'] and screen['pool_sha256'] == sha(HERE / 'pool.json')
    assert sha(FULL) == FULL_SHA
    source = read(FULL)
    assert source['passed'] and source['complete']
    controls = {key(r):r for r in source['games'] if r['version'] == 'integrated'}
    assert len(controls) == 100
    manifest = read(MANIFEST)
    fixtures = pool['fixtures'] if phase == 'parity' else manifest['live_losses'] + manifest['current_top20']
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), screen_sha256=sha(HERE / 'screen.json'),
                    helper_sha256=sha(__file__), source_full_sha256=sha(FULL))
    jobs = []
    for fixture in fixtures:
        for seat in (0, 1):
            parent = controls[(fixture['fixture_id'], seat)]
            jobs.append(dict(version='animal_liquidity', rival=fixture['fixture_id'], team=fixture['team'],
                             panel='loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                             candidate_seat=seat, seed=int(fixture['seed']), path=pool['candidate'],
                             candidate_sha256=pool['candidate_sha256'], opponent='rawroute:' + fixture['source_action_tape_path'],
                             opponent_action_sha256=fixture['source_opponent_action_sha256'],
                             parent_result=parent['result'], parent_margin=parent['margin'], **bindings))
    expected = {key(j):j for j in jobs}
    destination = HERE / ('native_' + phase + '.json')
    assert not destination.exists()
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    if checkpoint.exists():
        rows = [json.loads(line) for line in checkpoint.read_text().splitlines()]
    elif phase == 'full':
        parity = read(HERE / 'native_parity.json')
        assert parity['passed'] and parity['complete'] and all(parity[k] == v for k,v in bindings.items())
        rows = parity['games']
        checkpoint.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    else:
        rows = []
    done = {key(r) for r in rows}
    assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k,v in expected[key(row)].items())
    pending = [j for j in jobs if key(j) not in done]
    print('Animal native', phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as stream:
        for start in range(0, len(pending), 12):
            with ProcessPoolExecutor(max_workers=1) as executor:
                for row in executor.map(play, pending[start:start+12]):
                    rows.append(row); stream.write(json.dumps(row) + '\n'); stream.flush()
                    print('Animal native', phase, len(rows), '/', len(jobs), row['team'], row['candidate_seat'], row['result'], row['margin'], flush=True)
    fast = {(r['fixture_id'], r['candidate_seat']):r for r in screen['games']}
    fields = ('candidate_reward', 'opponent_reward', 'frames', 'candidate_status', 'opponent_status', 'candidate_telemetry')
    mismatches = [dict(key=key(r), fields=[f for f in fields if r[f] != fast[key(r)][f]]) for r in rows
                  if key(r) in fast and any(r[f] != fast[key(r)][f] for f in fields)]
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE'
                and not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    regressions = [key(r) for r in rows if r['parent_result'] == 'win' and r['result'] != 'win']
    panels = []
    for panel in ('loss30', 'top20'):
        games = [r for r in rows if r['panel'] == panel]
        ids = sorted({r['rival'] for r in games})
        pairs = {fid:[r for r in games if r['rival'] == fid] for fid in ids}
        assert all(len(pair) == 2 for pair in pairs.values())
        rescues = [fid for fid,pair in pairs.items() if all(r['result'] == 'win' for r in pair) and any(r['parent_result'] != 'win' for r in pair)]
        panels.append(dict(panel=panel, fixtures=len(ids), both_seat_wins=sum(all(r['result'] == 'win' for r in pair) for pair in pairs.values()),
                           WDL=[sum(r['result'] == label for r in games) for label in ('win', 'draw', 'loss')], rescued=rescues))
    complete = len(rows) == len(jobs)
    result = dict(complete=complete, clean=clean, passed=complete and clean and not mismatches and not regressions and any(p['rescued'] for p in panels),
                  fast_native_mismatches=mismatches, regressions=regressions, panels=panels, games=sorted(rows,key=key),
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(destination, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('parity', 'full'))
    args = parser.parse_args()
    with exclusive_run(HERE / 'qualify.lock'):
        run(args.phase)
