"""Mandatory saved-public-win preservation after independent confirmation only."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.check import sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

MANIFEST = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
MANIFEST_SHA = 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def setup(profile):
    if profile == 'public-loss':
        from diagnostics.public_loss_route_pool_20260928 import native as protocol
        selected, bindings, _ = protocol.setup('confirmation')
        folder = ROOT / 'diagnostics/public_loss_route_pool_20260928'
        confirmation = read(folder / 'native_confirmation.json')
        assert confirmation['complete'] and confirmation['passed']
        assert all(confirmation[k] == v for k, v in bindings.items())
        arms = {'main': (ROOT / 'main.py', protocol.MAIN_SHA), 'source': (protocol.SOURCE, protocol.SOURCE_SHA),
                'new': (Path(selected['candidate']), selected['candidate_sha256'])}
        comparisons = {'new': ('main', 'source')}
        entrypoints = {'new': 'kaggle_public_loss_pool_entrypoint'}
    else:
        from diagnostics.observed_hire_recovery_20260928 import native as protocol
        candidates, bindings, _ = protocol.setup('confirmation')
        folder = ROOT / 'diagnostics/observed_hire_recovery_20260928'
        confirmation = read(folder / 'native_confirmation.json')
        assert confirmation['terminal'] and all(confirmation[k] == v for k, v in bindings.items())
        passed = [r['candidate'] for r in confirmation['candidate_results'] if r['passed']]
        assert passed and set(passed) <= set(candidates)
        pool = read(folder / 'pool.json')
        arms = {'main': protocol.PARENTS['main']}
        if 'repair_integrated' in passed:
            arms['source'] = protocol.PARENTS['integrated']
        for name in passed:
            arm = pool['arms']['main' if name == 'repair_main' else 'integrated']
            arms[name] = (Path(arm['candidate']), arm['candidate_sha256'])
        comparisons = {name: protocol.COMPARISONS[name] for name in passed}
        entrypoints = {name: 'kaggle_observed_hire_recovery_entrypoint' for name in passed}
    assert sha(MANIFEST) == MANIFEST_SHA and all(sha(path) == digest for path, digest in arms.values())
    fixtures = read(MANIFEST)['fixtures']; assert len(fixtures) == 54
    assert len({f['fixture_id'] for f in fixtures}) == 54
    bindings = dict(profile=profile, confirmation_sha256=sha(folder / 'native_confirmation.json'),
                    preservation_helper_sha256=sha(__file__), public_win_manifest_sha256=MANIFEST_SHA,
                    native_game_helper_sha256=sha(ROOT / 'diagnostics/opening_probe_v2_20260928/qualify.py'))
    jobs = []
    for fixture in fixtures:
        raw = gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == fixture['source_replay_sha256']
        episode = json.loads(raw)
        assert float(episode['rewards'][fixture['source_candidate_seat']]) == fixture['source_candidate_reward']
        assert float(episode['rewards'][1-fixture['source_candidate_seat']]) == fixture['source_opponent_reward']
        for version, (path, digest) in arms.items():
            for seat in (0, 1):
                jobs.append(dict(version=version, rival=fixture['fixture_id'], team=fixture['team'], seed=int(fixture['seed']),
                                 candidate_seat=seat, path=str(path), candidate_sha256=digest,
                                 opponent='rawroute:' + fixture['source_action_tape_path'],
                                 opponent_action_sha256=fixture['source_opponent_action_sha256'],
                                 source_candidate_seat=fixture['source_candidate_seat'],
                                 public_candidate_reward=fixture['source_candidate_reward'],
                                 public_opponent_reward=fixture['source_opponent_reward'], **bindings))
    return folder, arms, comparisons, entrypoints, bindings, jobs


def key(row):
    return row['version'], row['rival'], row['candidate_seat']


def clean(row):
    return row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE' and not row['candidate_errors'] and not row['opponent_errors']


def run(profile, workers):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    folder, arms, comparisons, entrypoints, bindings, jobs = setup(profile)
    destination = folder / 'public_wins_native.json'; assert not destination.exists()
    expected = {key(j): j for j in jobs}; assert len(expected) == len(jobs)
    checkpoint = folder / 'public_wins_native.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    for row in rows:
        assert all(row[k] == v for k, v in expected[key(row)].items())
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    # Reuse only exact policy/seed/seat/tape identities from the broad native parity ledger.
    # Metadata labels may differ; retain immutable source provenance explicitly.
    reuse = ROOT / 'diagnostics/public_loss_route_pool_20260928/native_parity.json'
    imported = []
    if not rows and reuse.exists():
        ledger = read(reuse)
        if ledger.get('complete') and ledger.get('passed'):
            for job in jobs:
                matches = [r for r in ledger['games'] if all(r[k] == job[k] for k in
                           ('rival', 'seed', 'candidate_seat', 'candidate_sha256', 'opponent', 'opponent_action_sha256'))]
                if matches:
                    assert len(matches) == 1 and clean(matches[0])
                    row = dict(matches[0]); row.update(job)
                    row.update(reused_from=str(reuse), reused_ledger_sha256=sha(reuse))
                    rows.append(row); done.add(key(row)); imported.append(key(row))
            if rows:
                checkpoint.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    pending = [j for j in jobs if key(j) not in done]
    print('Public wins', profile, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as out:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play, j) for j in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row); out.write(json.dumps(row) + '\n'); out.flush()
                    if len(rows) % 4 == 0:
                        print('Public wins', profile, len(rows), '/', len(jobs), row['version'], row['team'], row['result'], flush=True)
    assert len(rows) == len(jobs)
    parity = [key(r) for r in rows if r['version'] == 'main' and r['candidate_seat'] == r['source_candidate_seat'] and
              (r['candidate_reward'] != r['public_candidate_reward'] or r['opponent_reward'] != r['public_opponent_reward'])]
    indexed = {key(r): r for r in rows}; results = []
    for candidate, controls in comparisons.items():
        regressions = [dict(fixture_id=r['rival'], seat=r['candidate_seat'], control=control)
                       for r in rows if r['version'] == candidate for control in controls
                       if indexed[(control, r['rival'], r['candidate_seat'])]['result'] == 'win' and r['result'] != 'win']
        required_roles = {candidate, *controls}
        result = dict(candidate=candidate, regressions=regressions,
                      passed=not parity and not regressions and all(clean(r) for r in rows if r['version'] in required_roles))
        results.append(result)
    summaries = {}
    for version in arms:
        arm = [r for r in rows if r['version'] == version]
        summaries[version] = dict(WDL=[sum(r['result'] == s for r in arm) for s in ('win', 'draw', 'loss')],
            both_seat_wins=sum(all(indexed[(version, fid, seat)]['result'] == 'win' for seat in (0, 1)) for fid in {r['rival'] for r in arm}))
    report = dict(complete=True, game_count=len(rows), reused_games=sum('reused_from' in r for r in rows),
                  clean=all(clean(r) for r in rows), public_original_seat_cash_mismatches=parity,
                  candidate_results=results, summaries=summaries, entrypoints=entrypoints,
                  arms={name: dict(path=str(path), sha256=digest) for name, (path, digest) in arms.items()},
                  games=sorted(rows, key=key), completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(destination, report)
    print(json.dumps({k:v for k,v in report.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('profile', choices=('public-loss', 'observed-hire'))
    parser.add_argument('--workers', type=int, default=3); args = parser.parse_args()
    folder = ROOT / ('diagnostics/public_loss_route_pool_20260928' if args.profile == 'public-loss' else 'diagnostics/observed_hire_recovery_20260928')
    with exclusive_run(folder / 'public_wins.lock'):
        run(args.profile, args.workers)
