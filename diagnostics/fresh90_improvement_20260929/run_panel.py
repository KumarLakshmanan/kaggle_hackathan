"""Resume only unchanged, source-bound fixed-replay diagnostic jobs."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostics/submission_top100_compare_20260929_1104'
sys.path[:0] = [str(ROOT), str(PRIOR)]
from fast_game_current import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def execute(job):
    entry = job['entry']
    fixture = dict(fixture_id=job['fixture_id'], seed=int(entry['seed']),
                   source_replay_path=entry['replay_path'],
                   source_replay_sha256=entry['replay_sha256'],
                   source_action_tape_path=entry['path'],
                   source_opponent_action_sha256=entry['action_sha256'])
    try:
        result = play(fixture, job['path'], job['candidate_sha256'],
                      job['candidate_seat'], trace_path=job.get('trace_path'))
    except Exception as error:
        result = dict(error_type=type(error).__name__, error=str(error))
    return {key: value for key, value in job.items() if key != 'entry'} | result


def assess(rows):
    def clean(row):
        return (not row.get('error') and not row.get('candidate_errors') and
                row.get('candidate_status') == row.get('opponent_status') == 'DONE'
                and row.get('frames') == 720)
    def score(selected):
        groups = {}
        for r in selected:
            groups.setdefault(r['fixture_id'], []).append(r)
        return dict(games=len(selected), wins=sum(r.get('result') == 'win' for r in selected),
                    draws=sum(r.get('result') == 'draw' for r in selected),
                    losses=sum(r.get('result') == 'loss' for r in selected),
                    all_clean=all(clean(r) for r in selected),
                    distinct_episodes=len({r['episode_id'] for r in selected}),
                    both_seat_wins=sum(len(g) == 2 and {r['candidate_seat'] for r in g} == {0, 1}
                                       and all(r.get('result') == 'win' for r in g) for g in groups.values()),
                    fixtures=len(groups), mean_margin=(sum(r.get('margin', 0) for r in selected) / len(selected)
                                                       if selected else None))
    return {label: dict(all=score([r for r in rows if r['label'] == label]),
                        top20=score([r for r in rows if r['label'] == label and r['rank'] <= 20]))
            for label in sorted({r['label'] for r in rows})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('jobs', type=Path)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    assert 1 <= args.workers <= 6
    jobs = json.loads(args.jobs.read_text(encoding='utf-8'))
    byid = {j['job_id']: j for j in jobs}
    assert len(jobs) == len(byid) and jobs
    for j in jobs:
        assert sha(j['path']) == j['candidate_sha256']
    ledger = args.jobs.with_name(args.jobs.stem + '_results.jsonl')
    receipt_path = args.jobs.with_name(args.jobs.stem + '_receipt.json')
    source_hashes = {str(p): sha(p) for p in (Path(__file__), PRIOR / 'fast_game_current.py',
                    PRIOR / 'current_input.py', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py')}
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        previous = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
        done = {r['job_id'] for r in previous}
        assert len(previous) == len(done)
        for r in previous:
            j = byid[r['job_id']]
            assert all(r[k] == j[k] for k in ('candidate_sha256', 'action_sha256', 'replay_sha256',
                                             'fixture_id', 'candidate_seat', 'episode_id'))
        if receipt_path.exists():
            original = json.loads(receipt_path.read_text())
            assert original['jobs_sha256'] == sha(args.jobs)
            assert original['source_hashes'] == source_hashes
        receipt = dict(started_at_utc=now(), complete=False, jobs_sha256=sha(args.jobs),
                       source_hashes=source_hashes, planned_games=len(jobs), completed_games=len(previous),
                       workers=args.workers, fixed_replay_diagnostic_only=True)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        rows = list(previous)
        with ledger.open('a', encoding='utf-8', newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                pending = {pool.submit(execute, j): j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row = future.result()
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True) + '\n')
                    stream.flush()
                    if len(rows) % 10 == 0 or len(rows) == len(jobs):
                        print(f"{len(rows)}/{len(jobs)} {row['job_id']} {row.get('result', row.get('error_type'))}", flush=True)
        assert len(rows) == len(jobs)
        receipt.update(complete=True, completed_at_utc=now(), completed_games=len(rows),
                       results_sha256=sha(ledger), assessment=assess(rows))
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt['assessment'], indent=2), flush=True)


if __name__ == '__main__':
    main()
