"""Actual local Kaggle file-loader parity after all independent/preservation gates."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.native_preservation_20260928.public_wins import setup, read, write, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run


def play(job, path, mode):
    from paired_benchmark import _load_agent, _load_module, TimedAgent, _timing_dict, make
    from diagnostics.opening_probe_v2_20260928.qualify import errors
    seat = job['candidate_seat']; module = None
    opponent, opponent_timed = _load_agent(job['opponent'], 'preservation_loader_rival')
    try:
        if mode == 'file':
            candidate = str(path)
        else:
            module = _load_module(path, 'preservation_loader_direct')
            def call(obs, cfg):
                public = dict(cfg); public['seed'] = None
                return module.agent(obs, public)
            candidate = TimedAgent(call)
        env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': job['seed']}, debug=False)
        env.run([candidate, opponent] if seat == 0 else [opponent, candidate])
        final = env.steps[-1]
        result = dict(mode=mode, seat=seat, seed=job['seed'], rewards=[float(s.reward) for s in final],
                      statuses=[s.status for s in final], frames=len(env.steps),
                      actions=[[frame[p].action for p in (0, 1)] for frame in env.steps[1:]],
                      minimum_remaining_overage_seconds=min(float(frame[seat].observation.remainingOverageTime) for frame in env.steps))
        result['passed'] = result['frames'] == 720 and result['statuses'] == ['DONE', 'DONE'] and result['minimum_remaining_overage_seconds'] >= 0
        result['passed'] = result['passed'] and result['rewards'][seat] == job['candidate_reward'] and result['rewards'][1-seat] == job['opponent_reward']
        if module is not None:
            result.update(timing=_timing_dict(candidate), telemetry=dict(module.agent.telemetry), policy_errors=errors(module))
            peak = int(result['timing']['max_step'])
            budget = float(env.configuration.actTimeout) + float(env.steps[peak][seat].observation.remainingOverageTime)
            result['native_budget_at_peak_seconds'] = budget
            result['passed'] = result['passed'] and not result['policy_errors'] and result['telemetry'] == job['candidate_telemetry'] and result['timing']['max_ms'] < budget * 1000
        return result
    finally:
        if module is not None:
            sys.modules.pop(module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)
        gc.collect()


def run(profile):
    from paired_benchmark import engine_version
    from kaggle_environments.agent import get_last_callable
    assert engine_version == '1.32.7'
    folder, arms, comparisons, entrypoints, bindings, _ = setup(profile)
    preservation = read(folder / 'public_wins_native.json')
    assert preservation['complete'] and preservation['preservation_helper_sha256'] == sha(HERE / 'public_wins.py')
    assert all(preservation[k] == v for k, v in bindings.items())
    passed = [r['candidate'] for r in preservation['candidate_results'] if r['passed']]
    assert passed and set(passed) <= set(comparisons)
    full = read(folder / 'native_full.json'); assert full['complete'] and full['passed']
    destination = folder / 'loader_parity.json'; assert not destination.exists()
    bindings = dict(profile=profile, loader_helper_sha256=sha(__file__), public_preservation_sha256=sha(folder / 'public_wins_native.json'),
                    native_full_sha256=sha(folder / 'native_full.json'), confirmation_sha256=sha(folder / 'native_confirmation.json'))
    rows = []
    for candidate in passed:
        if profile == 'public-loss':
            selected = read(folder / 'selection.json')
            path = Path(selected['backup']); cohort = full['games']
            extra = min(r['rival'] for r in cohort if r['candidate_telemetry'].get('loss_pool_turns', 0))
            fixtures = {'top20-03-Boey-114266440', extra}
        else:
            version = 'main' if candidate == 'repair_main' else 'integrated'
            path = Path(read(folder / 'pool.json')['arms'][version]['backup'])
            cohort = [r for r in full['games'] if r['version'] == version]
            fixtures = {'live-114254310', 'top20-03-Boey-114266440'}
        assert sha(path) == arms[candidate][1]
        entry = get_last_callable(path.read_text(encoding='utf-8'), path=str(path)).__name__
        assert entry == entrypoints[candidate]
        jobs = sorted([r for r in cohort if r['rival'] in fixtures], key=lambda r: (r['rival'], r['candidate_seat']))
        assert len(jobs) == 4
        for job in jobs:
            item_path = folder / ('loader_' + candidate + '_' + job['rival'] + '_seat' + str(job['candidate_seat']) + '.json')
            if item_path.exists():
                item = read(item_path)
                assert all(item[k] == v for k, v in bindings.items())
                assert item['candidate_sha256'] == sha(path) and item['loaded_name'] == entry
            else:
                direct = play(job, path, 'direct'); loaded = play(job, path, 'file')
                equal = direct['actions'] == loaded['actions'] and direct['rewards'] == loaded['rewards']
                action_sha = hashlib.sha256(json.dumps(loaded['actions'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                if equal:
                    del direct['actions'], loaded['actions']
                item = dict(candidate=candidate, candidate_path=str(path), candidate_sha256=sha(path), fixture_id=job['rival'],
                            candidate_seat=job['candidate_seat'], seed=job['seed'], loaded_name=entry,
                            all_719_actions_both_players_equal=equal, actions_sha256=action_sha,
                            passed=equal and direct['passed'] and loaded['passed'], direct=direct, file=loaded, **bindings)
                write(item_path, item)
            rows.append(item)
            print('Loader', candidate, job['rival'], job['candidate_seat'], item['passed'], flush=True)
            if not item['passed']:
                break
    results = [dict(candidate=c, passed=sum(r['candidate'] == c for r in rows) == 4 and all(r['passed'] for r in rows if r['candidate'] == c)) for c in passed]
    report = dict(complete=len(rows) == 4 * len(passed), passed=all(r['passed'] for r in results), candidate_results=results,
                  game_count=len(rows) * 2, rows=rows, completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Operational direct/file parity on two fixtures per policy, not additional independent strength.', **bindings)
    write(destination, report)
    print(json.dumps({k:v for k,v in report.items() if k != 'rows'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('profile', choices=('public-loss', 'observed-hire'))
    args = parser.parse_args()
    folder = ROOT / ('diagnostics/public_loss_route_pool_20260928' if args.profile == 'public-loss' else 'diagnostics/observed_hire_recovery_20260928')
    with exclusive_run(folder / 'loader.lock'):
        run(args.profile)
