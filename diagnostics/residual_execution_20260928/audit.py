"""Capture both-seat residual mechanisms, without modifying any policy."""
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
from diagnostics.bakery_pizza_pool_20260928.analyze_mhw import analyze
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'diagnostics/public_loss_route_pool_20260928/candidate_selected.py'
SOURCE_SHA = '8dde995de6430dcdb7c3dae57bc7a42885ea1b230583c9b0eaf062d1361d3432'
FULL = SOURCE.parent / 'native_full.json'
FULL_SHA = 'a01df893b3e032aa9aa017360fecc2039308bc58e7dd12595852e6bcfc21de89'
MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
MANIFEST_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'


def run(job):
    fixture, seat, native, bindings = job
    path = HERE / (fixture['fixture_id'] + '_seat' + str(seat) + '.jsonl.gz')
    assert not path.exists()
    row = play(fixture, SOURCE, SOURCE_SHA, seat, path)
    fields = ('candidate_reward', 'opponent_reward', 'frames', 'candidate_status', 'opponent_status', 'candidate_telemetry')
    assert all(row[k] == native[k] for k in fields), (fixture['fixture_id'], seat)
    assert not row['candidate_errors']
    row.update(version='8dde995d', team=fixture['team'], trace_path=str(path), trace_sha256=sha(path),
               native_terminal_parity=True, **bindings)
    result = dict(game=row, analysis=analyze(row))
    path.with_name(path.name + '.receipt.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main(workers):
    assert sha(SOURCE) == SOURCE_SHA and sha(FULL) == FULL_SHA and sha(MANIFEST) == MANIFEST_SHA
    full = json.loads(FULL.read_text(encoding='utf-8'))
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    fixtures = manifest['live_losses'] + manifest['current_top20']
    assert full['complete'] and full['passed']
    failed = {r['rival'] for r in full['games'] if r['result'] != 'win'}
    assert len(failed) == 19
    chosen = [f for f in fixtures if f['fixture_id'] in failed or f['team'] in ('Boey', 'Majkel1337')]
    assert len(chosen) == 21
    bindings = dict(source_sha256=SOURCE_SHA, native_full_sha256=FULL_SHA, manifest_sha256=MANIFEST_SHA,
                    plan_sha256=sha(HERE / 'PLAN.md'), helper_sha256=sha(__file__),
                    fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                    analyzer_sha256=sha(ROOT / 'diagnostics/bakery_pizza_pool_20260928/analyze_mhw.py'))
    expected = {(r['rival'], r['candidate_seat']): r for r in full['games']}
    jobs = [(f, seat, expected[(f['fixture_id'], seat)], bindings) for f in chosen for seat in (0, 1)]
    output = HERE / 'audit.json'; assert not output.exists()
    checkpoint = HERE / 'audit.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done = {(r['game']['fixture_id'], r['game']['candidate_seat']) for r in rows}
    assert len(done) == len(rows)
    for row in rows:
        assert all(row['game'][k] == v for k, v in bindings.items())
        assert sha(row['game']['trace_path']) == row['game']['trace_sha256']
    pending = [j for j in jobs if (j[0]['fixture_id'], j[1]) not in done]
    with checkpoint.open('a', encoding='utf-8') as out:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(run, job) for job in pending[start:start+16]]
                for future in as_completed(futures):
                    row = future.result(); rows.append(row)
                    out.write(json.dumps(row) + '\n'); out.flush()
                    print('Residual audit', len(rows), '/', len(jobs), row['game']['team'], row['game']['candidate_seat'],
                          row['game']['margin'], row['analysis']['nochange_counts'], flush=True)
    assert len(rows) == 42
    payload = dict(complete=True, diagnostic_only=True, native_parity=True, rows=rows,
                   completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print('Residual audit complete', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    with exclusive_run(HERE / 'audit.lock'):
        main(args.workers)
