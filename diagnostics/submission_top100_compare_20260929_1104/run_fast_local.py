"""Complete frozen top-100 comparison with parity-checked native transitions."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run
from fast_game_current import play

SOURCES = {
    'ae349d83': (HERE / 'downloaded/main_ae349d83.py',
                 'ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb'),
    '257f941d': (HERE / 'downloaded/main_257f941d.py',
                 '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'),
    '4eeac9c3': (HERE / 'downloaded/main_4eeac9c3.py',
                 '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def run_one(job):
    label, entry, seat = job
    path, digest = SOURCES[label]
    assert sha(path) == digest
    fixture = {
        'fixture_id': str(entry['team_id']),
        'seed': int(entry['seed']),
        'source_replay_path': entry['replay_path'],
        'source_replay_sha256': entry['replay_sha256'],
        'source_action_tape_path': entry['path'],
        'source_opponent_action_sha256': entry['action_sha256'],
    }
    try:
        result = play(fixture, str(path), digest, seat)
        return {key: result.get(key) for key in (
            'result', 'margin', 'candidate_reward', 'opponent_reward',
            'candidate_status', 'opponent_status', 'frames', 'wall_seconds',
            'candidate_telemetry', 'candidate_errors')}
    except Exception as error:
        return {'error_type': type(error).__name__, 'error': str(error)[:400]}


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        native = json.loads((HERE / 'fast_native_parity.json').read_text(encoding='utf-8'))
        assert native['passed'] and len(native['rows']) == 18
        manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
        entries = json.loads((HERE / 'routes/summary.json').read_text(encoding='utf-8'))
        assert manifest['complete'] and manifest['eligible'] == len(entries) == 100
        assert len({int(e['team_id']) for e in entries}) == 100
        for path, digest in SOURCES.values():
            assert sha(path) == digest
        assert not (HERE / 'fast_results.jsonl').exists()
        assert not (HERE / 'fast_run_receipt.json').exists()
        jobs = [(label, entry, seat) for entry in entries
                for seat in (0, 1) for label in SOURCES]
        receipt = {
            'started_at_utc': now(), 'complete': False, 'method': 'pure native transitions from verified public replay initial frame',
            'leaderboard_snapshot_utc': manifest['leaderboard_snapshot_utc'],
            'manifest_sha256': sha(HERE / 'manifest.json'),
            'download_receipt_sha256': sha(HERE / 'downloaded/download_receipt.json'),
            'parity_receipt_sha256': sha(HERE / 'fast_native_parity.json'),
            'source_sha256': {label: digest for label, (_, digest) in SOURCES.items()},
            'planned_games': 600, 'completed_games': 0,
            'native_framework_validation': False, 'frozen_fixed_tapes_only': True,
        }
        receipt_path = HERE / 'fast_run_receipt.json'
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        with (HERE / 'fast_results.jsonl').open('x', encoding='utf-8') as stream:
            with ProcessPoolExecutor(max_workers=6) as pool:
                futures = {pool.submit(run_one, job): job for job in jobs}
                for future in as_completed(futures):
                    label, entry, seat = futures[future]
                    try:
                        result = future.result()
                    except Exception as error:
                        result = {'error_type': type(error).__name__,
                                  'error': str(error)[:400]}
                    row = {
                        'label': label, 'rank': int(entry['rank']),
                        'team_id': int(entry['team_id']), 'team': entry['team'],
                        'episode_id': int(entry['episode_id']),
                        'submission_id': int(entry['submission_id']),
                        'seed': int(entry['seed']), 'candidate_seat': seat,
                        'opponent_action_sha256': entry['action_sha256'],
                        **result,
                    }
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    receipt['completed_games'] += 1
                    if receipt['completed_games'] % 30 == 0:
                        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
                        print(f"{receipt['completed_games']}/600 ",
                              f"rank={entry['rank']} {label} seat={seat} ",
                              row.get('result', row.get('error_type')), flush=True)
        receipt.update(complete=True, completed_at_utc=now(),
                       results_sha256=sha(HERE / 'fast_results.jsonl'))
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(f"COMPLETE 600/600 results_sha256={receipt['results_sha256']}", flush=True)


if __name__ == '__main__':
    main()
