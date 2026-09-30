"""Operational verification for the user's experimental a44c8c2c upload."""
from datetime import datetime, timezone
from pathlib import Path
import gc
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, _load_module, TimedAgent, _timing_dict, make, engine_version
from kaggle_environments.agent import get_last_callable
from diagnostics.opening_probe_v2_20260928.qualify import errors
from diagnostics.local_target_20260928.run_lock import exclusive_run

CANDIDATE = HERE / 'main.py'
BACKUP = ROOT / 'main_candidate_adaptive_donor_pair_repair_20260928_a44c8c2c.py'
DIGEST = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
ENTRYPOINT = 'kaggle_donor_pair_repair_entrypoint'
PARITY = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_results.json'
PARITY_DIGEST = 'ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(job, mode):
    seat = job['candidate_seat']
    actions = json.loads(gzip.decompress(Path(job['opponent'].split(':', 1)[1]).read_bytes()))['actions']
    assert job['opponent_action_sha256'] in {
        hashlib.sha256(json.dumps(actions, sort_keys=sort, separators=(',', ':')).encode()).hexdigest()
        for sort in (False, True)
    }
    opponent, opponent_timed = _load_agent(job['opponent'], 'donor_upload_loader_rival')
    module = None
    try:
        if mode == 'file':
            candidate = str(CANDIDATE)
        else:
            module = _load_module(CANDIDATE, 'donor_upload_loader_candidate')
            def call(obs, cfg):
                visible = dict(cfg)
                visible['seed'] = None
                return module.agent(obs, visible)
            candidate = TimedAgent(call)
        env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': job['seed']}, debug=False)
        env.run([candidate, opponent] if seat == 0 else [opponent, candidate])
        final = env.steps[-1]
        result = dict(mode=mode, seat=seat, seed=job['seed'], fixture_id=job['rival'],
                      rewards=[float(state.reward) for state in final],
                      statuses=[state.status for state in final], frames=len(env.steps),
                      actions=[[frame[p].action for p in (0, 1)] for frame in env.steps[1:]],
                      minimum_remaining_overage_seconds=min(float(frame[seat].observation.remainingOverageTime)
                                                           for frame in env.steps))
        assert result['statuses'] == ['DONE', 'DONE'] and result['frames'] == 720
        assert result['minimum_remaining_overage_seconds'] >= 0
        assert result['rewards'][seat] == job['candidate_reward']
        assert result['rewards'][1-seat] == job['opponent_reward']
        if module is not None:
            result['timing'] = _timing_dict(candidate)
            result['telemetry'] = dict(module.agent.telemetry)
            result['policy_errors'] = errors(module)
            peak = int(result['timing']['max_step'])
            result['native_budget_at_peak_seconds'] = float(env.configuration.actTimeout) + float(
                env.steps[peak][seat].observation.remainingOverageTime)
            assert result['timing']['max_ms'] < result['native_budget_at_peak_seconds'] * 1000
            assert not result['policy_errors']
            assert result['telemetry'] == job['candidate_telemetry']
            assert all(result['telemetry'].get(k, 0) == 0 for k in ('bridge_common_failed', 'bridge_guard_refusals', 'bridge_source_guard_failed', 'bridge_errors'))
            if job['team'] == 'Boey':
                assert result['telemetry']['bridge_selected'] == 'shared151'
                assert result['telemetry']['donor_selected'] == 'route2'
            if job['team'] == 'Yaroslav':
                assert result['telemetry']['bridge_selected'] == 'source'
                assert result['telemetry']['animal_cash_turns'] == 1
        print(json.dumps({k: v for k, v in result.items() if k not in ('actions', 'telemetry')}), flush=True)
        return result
    finally:
        if module is not None:
            sys.modules.pop(module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)
        gc.collect()


def main():
    assert not (HERE / 'loader_parity.json').exists(), 'Verification already recorded.'
    assert engine_version == '1.32.7'
    assert sha(CANDIDATE) == sha(BACKUP) == DIGEST and sha(ROOT / 'main.py') == MAIN_DIGEST
    assert sha(PARITY) == PARITY_DIGEST
    raw = CANDIDATE.read_bytes()
    compile(raw, str(CANDIDATE), 'exec')
    loaded = get_last_callable(raw.decode('utf-8'), path=str(CANDIDATE)).__name__
    assert loaded == ENTRYPOINT
    parity = json.loads(PARITY.read_text(encoding='utf-8'))
    assert parity['complete'] and parity['passed'] and parity['clean'] and len(parity['games']) == 100
    pool_path = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_pool.json'
    assert sha(pool_path) == parity['pool_sha256']
    pool = json.loads(pool_path.read_text(encoding='utf-8'))
    fixtures = {f['fixture_id']: f for f in pool['fixtures']}
    jobs = []
    for row in parity['games']:
        if row['fixture_id'] not in ('top20-03-Boey-114266440', 'live-114283577'):
            continue
        f = fixtures[row['fixture_id']]
        jobs.append(dict(row, rival=f['fixture_id'], seed=f['seed'], opponent='rawroute:' + f['source_action_tape_path'], opponent_action_sha256=f['source_opponent_action_sha256']))
    jobs.sort(key=lambda r: (r['rival'], r['candidate_seat']))
    assert {(j['team'], j['candidate_seat']) for j in jobs} == {
        (team, seat) for team in ('Yaroslav', 'Boey') for seat in (0, 1)}
    assert len(jobs) == 4 and all(j['candidate_sha256'] == DIGEST for j in jobs)
    rows = []
    for job in jobs:
        direct = run(job, 'direct')
        file = run(job, 'file')
        if direct['rewards'] != file['rewards'] or direct['actions'] != file['actions']:
            (HERE / 'loader_failure.json').write_text(json.dumps(dict(direct=direct, file=file)), encoding='utf-8')
            raise AssertionError('Direct and file-loaded policy differ; do not upload.')
        action_sha = hashlib.sha256(json.dumps(file['actions'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        del direct['actions'], file['actions']
        rows.append(dict(seat=job['candidate_seat'], team=job['team'], fixture_id=job['rival'], seed=job['seed'],
                         all_719_actions_both_players_equal=True, actions_sha256=action_sha,
                         direct=direct, file=file))
        gc.collect()
    assert sha(CANDIDATE) == sha(BACKUP) == DIGEST and sha(ROOT / 'main.py') == MAIN_DIGEST
    report = dict(passed=True, candidate=str(CANDIDATE), candidate_sha256=DIGEST,
                  loaded_name=loaded, engine_version=engine_version, game_count=8,
                  saved_panel_sha256=sha(PARITY), main_sha256=MAIN_DIGEST,
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
                  scope='Operational file-loader parity for explicitly requested experimental upload; independent qualification remains pending.')
    with (HERE / 'loader_parity.json').open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2), flush=True)


if __name__ == '__main__':
    with exclusive_run(HERE / 'loader.lock'):
        main()
