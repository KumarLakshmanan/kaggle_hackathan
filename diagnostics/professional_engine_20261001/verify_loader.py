"""Both-seat real framework direct/file-loader parity for the frozen survivor."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.fresh90_loss_audit_20260929.verify_combined_v2_operational import run_loader_one


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--candidate', type=Path, required=True); args = parser.parse_args()
    candidate = args.candidate.resolve(); baseline = HERE/'baseline_main_bbffbe65.py'
    manifest = json.loads(candidate.with_suffix('.manifest.json').read_text()); assert manifest['candidate_sha256'] == sha(candidate)
    from kaggle_environments.agent import get_last_callable
    entrypoint = get_last_callable(candidate.read_text(), path=str(candidate)).__name__
    assert entrypoint == manifest['expected_entrypoint']
    screen = [json.loads(s) for s in (HERE/'screen_results.jsonl').read_text().splitlines()]
    selected = {r['candidate_seat']: r for r in screen if r['candidate_sha256'] == sha(candidate) and r['seed'] == 34010001 and r['rival'] == 'bbff'}
    assert set(selected) == {0, 1}
    rows = []; parity = []
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        for seat in (0, 1):
            pair = []
            for mode in ('direct', 'file'):
                row = run_loader_one(candidate, baseline, 34010001, seat, mode)
                expected = [selected[seat]['candidate_reward'], selected[seat]['opponent_reward']]
                if seat == 1: expected.reverse()
                row['fast_native_reward_match'] = row['rewards'] == expected
                row['passed'] = row['passed'] and row['fast_native_reward_match']
                rows.append(row); pair.append(row)
                (HERE/'loader_progress.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
                print(json.dumps({'seat': seat, 'mode': mode, 'passed': row['passed'], 'rewards': row['rewards'], 'remaining': row['minimum_remaining_overage']}), flush=True)
            match = all(pair[0][k] == pair[1][k] for k in ('rewards', 'statuses', 'candidate_action_sha256', 'joint_action_sha256'))
            parity.append({'seat': seat, 'match': match})
        receipt = {'candidate_sha256': sha(candidate), 'entrypoint': entrypoint, 'rows': rows, 'parity': parity,
            'passed': all(r['passed'] for r in rows) and all(p['match'] for p in parity), 'completed_at_utc': datetime.now(timezone.utc).isoformat()}
        (HERE/'loader_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        assert receipt['passed']


if __name__ == '__main__': main()
