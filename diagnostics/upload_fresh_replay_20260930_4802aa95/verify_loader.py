"""Bounded operational checks for the explicitly requested experimental upload.

These checks do not reverse the failed research promotion decision. They use
one prior loader control and one already-exposed reacting regression seed.
The untouched research confirmation seeds remain reserved.
"""
from datetime import datetime, timezone
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.fresh90_loss_audit_20260929.verify_combined_v2_operational import run_loader_one

SOURCE = ROOT / 'main_candidate_fresh_replay_20260930_4802aa95.py'
CANDIDATE = HERE / 'main.py'
BASELINE = ROOT / 'diagnostics/fresh90_improvement_20260929/baseline_cb76fbc4.py'
DIGEST = '4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4'
BASE_DIGEST = 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
ENTRYPOINT = 'kaggle_fresh_execution_schedule_entrypoint'
SEEDS = (12929001, 22929006)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(path, data): Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')

def main():
    assert not (HERE / 'loader_parity.json').exists(), 'Inspect existing verification before rerunning.'
    assert sha(SOURCE) == DIGEST and sha(BASELINE) == BASE_DIGEST
    assert sha(ROOT / 'main.py') == MAIN_DIGEST
    if not CANDIDATE.exists():
        with CANDIDATE.open('xb') as stream:
            stream.write(SOURCE.read_bytes())
    assert sha(CANDIDATE) == DIGEST
    source = CANDIDATE.read_text(encoding='utf-8')
    compile(source, str(CANDIDATE), 'exec')
    assert [n.name for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)][-1] == ENTRYPOINT
    from kaggle_environments.agent import get_last_callable
    loaded_name = get_last_callable(source, path=str(CANDIDATE)).__name__
    assert loaded_name == ENTRYPOINT
    write(HERE / 'package_provenance.json', dict(
        source=str(SOURCE), source_sha256=DIGEST, submission_file=str(CANDIDATE),
        submission_sha256=sha(CANDIDATE), entrypoint=loaded_name, created_at_utc=now(),
        experimental=True, research_promotion=False, root_main_replaced=False,
        operational_seeds=SEEDS, planned_games=8))
    rows, parity = [], []
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        for seed in SEEDS:
            for seat in (0, 1):
                pair = []
                for mode in ('direct', 'file'):
                    row = run_loader_one(CANDIDATE, BASELINE, seed, seat, mode)
                    rows.append(row)
                    pair.append(row)
                    write(HERE / 'loader_progress.json', dict(rows=rows, updated_at_utc=now()))
                    print(json.dumps(dict(seed=seed, seat=seat, mode=mode, passed=row['passed'],
                                          rewards=row['rewards'], frames=row['frames'])), flush=True)
                match = all(pair[0][field] == pair[1][field] for field in (
                    'rewards', 'statuses', 'candidate_action_sha256', 'joint_action_sha256'))
                parity.append(dict(seed=seed, seat=seat, direct_vs_file_match=match))
        assert sha(SOURCE) == sha(CANDIDATE) == DIGEST
        assert sha(BASELINE) == BASE_DIGEST and sha(ROOT / 'main.py') == MAIN_DIGEST
        result = dict(candidate_sha256=DIGEST, baseline_sha256=BASE_DIGEST, loaded_name=loaded_name,
                      rows=rows, parity=parity, action_reward_parity=all(p['direct_vs_file_match'] for p in parity),
                      passed=all(r['passed'] for r in rows) and all(p['direct_vs_file_match'] for p in parity),
                      completed_at_utc=now(), research_promotion=False,
                      scope='Native runtime and file-loader verification only; prior reacting performance gate failed.')
        write(HERE / 'loader_parity.json', result)
    assert result['passed'], 'Operational verification failed; do not upload.'
    print(json.dumps(dict(passed=True, games=len(rows), candidate_sha256=DIGEST, entrypoint=loaded_name)), flush=True)

if __name__ == '__main__': main()
