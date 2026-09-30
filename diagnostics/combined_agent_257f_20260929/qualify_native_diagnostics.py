"""Checkpointed integration and untouched reacting qualification, offline only."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import gzip
import hashlib
import json
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, _load_module, TimedAgent, _timing_dict, make, engine_version

MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
MANIFEST_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
REFS = {
    '4ee': (ROOT / 'main.py', '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
    'v43': (ROOT / 'main_v43_current.py', '69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3'),
    'market': (ROOT / 'public_market_smart_f6a756cf_20260927.py', 'f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2'),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def errors(module):
    found = {}
    reports = {name: value for name, value in vars(module).items()
               if isinstance(value, dict) and ('STATS' in name or 'REPORT' in name)}
    reports['agent.telemetry'] = getattr(module.agent, 'telemetry', {})
    for name, report in reports.items():
        for key, value in report.items():
            if ('error' in str(key).lower() or 'collision' in str(key).lower()) and isinstance(value, (int, float)) and value:
                found[name + '.' + str(key)] = value
    return found


def play(job):
    assert sha(job['path']) == job['candidate_sha256']
    candidate = _load_module(Path(job['path']), 'opening_qualification_candidate')
    opponent_module = None
    opponent_timed = None
    reference_fallback_errors = 0
    try:
        if job['opponent'].startswith('rawroute:'):
            tape_path = Path(job['opponent'].split(':', 1)[1])
            actions = json.loads(gzip.decompress(tape_path.read_bytes()))['actions']
            action_hashes = [hashlib.sha256(json.dumps(actions, sort_keys=s, separators=(',', ':')).encode()).hexdigest()
                             for s in (False, True)]
            assert job['opponent_action_sha256'] in action_hashes
            opponent, opponent_timed = _load_agent(job['opponent'], 'opening_qualification_tape')
        else:
            assert sha(job['opponent']) == job['opponent_sha256']
            opponent_module = _load_module(Path(job['opponent']), 'opening_qualification_reference')
            if hasattr(opponent_module, '_V43_POLICY'):
                original_v43 = opponent_module._V43_POLICY
                def instrumented_v43(obs, cfg=None):
                    nonlocal reference_fallback_errors
                    try:
                        return original_v43(obs, cfg)
                    except Exception:
                        reference_fallback_errors += 1
                        raise
                opponent_module._V43_POLICY = instrumented_v43
            def reference_call(obs, cfg):
                visible = dict(cfg)
                visible['seed'] = None
                return opponent_module.agent(obs, visible)
            opponent = TimedAgent(reference_call)
        def candidate_call(obs, cfg):
            visible = dict(cfg)
            visible['seed'] = None
            return candidate.agent(obs, visible)
        timed = TimedAgent(candidate_call, capture_step=1)
        started = time.perf_counter()
        env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': job['seed']}, debug=False)
        seat = job['candidate_seat']
        env.run([timed, opponent] if seat == 0 else [opponent, timed])
        final = env.steps[-1]
        own, rival = float(final[seat].reward or 0), float(final[1-seat].reward or 0)
        margin = own - rival
        telemetry = dict(getattr(candidate.agent, 'telemetry', {}) or {})
        opponent_telemetry = (dict(getattr(opponent_module.agent, 'telemetry', {}) or {})
                              if opponent_module is not None else {})
        native_status_errors = [
            {'step': step, 'player': player, 'status': state.status}
            for step, frame in enumerate(env.steps)
            for player, state in enumerate(frame)
            if state.status in {'ERROR', 'INVALID', 'TIMEOUT'}
        ]
        native_stderr_events = [
            {'step': step, 'player': player, 'stderr': str(log.get('stderr', ''))}
            for step, frame_logs in enumerate(env.logs)
            for player, log in enumerate(frame_logs)
            if str(log.get('stderr', '')).strip()
        ]
        remaining_overage = []
        for frame in env.steps:
            observation = frame[seat].observation
            value = (observation.get('remainingOverageTime')
                     if hasattr(observation, 'get')
                     else getattr(observation, 'remainingOverageTime', None))
            if value is not None:
                remaining_overage.append(float(value))
        row = dict(job, candidate_reward=own, opponent_reward=rival, margin=margin,
                   result='win' if margin > 0 else 'loss' if margin < 0 else 'draw',
                   frames=len(env.steps), candidate_status=final[seat].status, opponent_status=final[1-seat].status,
                   wall_seconds=time.perf_counter()-started, candidate_timing=_timing_dict(timed),
                   opponent_timing=_timing_dict(opponent) if isinstance(opponent, TimedAgent) else None,
                   candidate_capture=timed.capture, candidate_telemetry=telemetry,
                   opponent_telemetry=opponent_telemetry,
                   native_status_errors=native_status_errors,
                   native_stderr_events=native_stderr_events,
                   minimum_remaining_overage_seconds=(min(remaining_overage)
                                                       if remaining_overage else None),
                   candidate_errors=errors(candidate), opponent_errors=errors(opponent_module) if opponent_module else {},
                   configuration_seed_visible=None)
        if reference_fallback_errors:
            row['opponent_errors']['v43_fallback'] = reference_fallback_errors
        assert sha(job['path']) == job['candidate_sha256']
        if job.get('expected'):
            expected = job['expected']
            row['integration_match'] = (telemetry['selected_arm'] == expected['arm']
                and own == expected['candidate_reward'] and rival == expected['opponent_reward']
                and row['result'] == expected['result'])
        return row
    finally:
        sys.modules.pop(candidate.__name__, None)
        if opponent_module is not None:
            sys.modules.pop(opponent_module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)
        gc.collect()


def points(row):
    return 1.0 if row['result'] == 'win' else .5 if row['result'] == 'draw' else 0.0


def key(row):
    return (row['version'], row['rival'], row['seed'], row['candidate_seat'])


def unique_checkpoint_rows(rows):
    """Keep duplicate executions as audit evidence, never as extra games.

    A review chat briefly launched the same pilot as an existing research
    chat. Concurrent appends are retained in the raw checkpoint. Resume
    accepts a duplicate only when every field except runtime measurements
    agrees; conflicting outcomes or candidate hashes remain hard errors.
    """
    unique = {}
    for row in rows:
        identity = key(row)
        if identity in unique:
            comparable = lambda r: {k: v for k, v in r.items() if k not in ('wall_seconds', 'candidate_timing')}
            assert comparable(row) == comparable(unique[identity]), f'Conflicting duplicate checkpoint {identity}'
        else:
            unique[identity] = row
    return list(unique.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('integration', 'pilot', 'confirmation'))
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    assert engine_version == '1.32.7'
    selector = json.loads((HERE / 'selector_manifest.json').read_text())
    assert sha(selector['candidate']) == selector['candidate_sha256']
    assert all(sha(path) == digest for path, digest in REFS.values())
    assert sha(MANIFEST) == MANIFEST_SHA
    plan_sha = sha(HERE / 'NATIVE_PLAN.md')
    if args.phase != 'integration':
        gate = json.loads((HERE / ('integration.json' if args.phase == 'pilot' else 'pilot.json')).read_text())
        assert gate['complete'] and gate['passed'] and gate['candidate_sha256'] == selector['candidate_sha256']
        assert gate['plan_sha256'] == plan_sha
    jobs = []
    if args.phase == 'integration':
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        fitted = json.loads((HERE / 'selection.json').read_text(encoding='utf-8'))['best_preserving_incumbent_wins']
        choices = {(c['fixture_id'], c['seat']): c['arm'] for c in fitted['choices']}
        arms = json.loads((HERE / 'arms.json').read_text(encoding='utf-8'))['games']
        previous = {(r['fixture_id'], r['candidate_seat'], r['arm']): r for r in arms}
        for fixture in manifest['live_losses'] + manifest['current_top20']:
            for seat in (0, 1):
                arm = choices[(fixture['fixture_id'], seat)]
                prior = previous[(fixture['fixture_id'], seat, arm)]
                jobs.append(dict(version='new', rival=fixture['fixture_id'], team=fixture['team'],
                    seed=int(fixture['seed']), candidate_seat=seat, path=selector['candidate'],
                    candidate_sha256=selector['candidate_sha256'],
                    opponent='rawroute:' + fixture['source_action_tape_path'],
                    opponent_action_sha256=fixture['source_opponent_action_sha256'],
                    expected={k: prior[k] for k in ('arm', 'candidate_reward', 'opponent_reward', 'result')},
                    baseline_result=prior['baseline_result'], plan_sha256=plan_sha))
        seeds = sorted({job['seed'] for job in jobs})
    else:
        seeds = list(range(2908000, 2908008) if args.phase == 'pilot' else range(2908100, 2908116))
        versions = {'new': (selector['candidate'], selector['candidate_sha256']), 'old': REFS['4ee']}
        jobs = [dict(version=version, rival=reference, seed=seed, candidate_seat=seat,
                     path=str(path), candidate_sha256=digest, opponent=str(opponent), opponent_sha256=opponent_digest,
                     plan_sha256=plan_sha)
                for seed in seeds for reference, (opponent, opponent_digest) in REFS.items()
                for version, (path, digest) in versions.items() for seat in (0, 1)]
    expected = {key(job): job for job in jobs}
    assert len(expected) == len(jobs)
    checkpoint = HERE / (args.phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    rows = unique_checkpoint_rows(rows)
    for row in rows:
        assert all(row[k] == v for k, v in expected[key(row)].items())
    keys = {key(row) for row in rows}
    assert len(keys) == len(rows)
    pending = [job for job in jobs if key(job) not in keys]
    print(f'{args.phase}: {len(rows)}/{len(jobs)} already complete; {len(pending)} pending', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 32):
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(play, job) for job in pending[start:start+32]]
                for future in as_completed(futures):
                    row = future.result()
                    rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + '\n')
                    output.flush()
                    if len(rows) % 8 == 0:
                        print(f'{args.phase}: {len(rows)}/{len(jobs)} {row["version"]} vs {row["rival"]} '
                              f'{row["result"]} {row["margin"]:+.0f}', flush=True)
    all_done = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' for r in rows)
    assert len(rows) == len(expected) and len({key(row) for row in rows}) == len(rows)
    no_errors = all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    result = dict(complete=True, phase=args.phase, candidate_sha256=selector['candidate_sha256'],
                  plan_sha256=plan_sha, script_sha256=sha(__file__), manifest_sha256=MANIFEST_SHA,
                  reference_hashes={r: d for r, (p, d) in REFS.items()}, engine_version=engine_version,
                  configuration_seed_masked=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  intended_games=len(jobs), game_count=len(rows), all_done=all_done, no_errors=no_errors,
                  seeds=seeds, games=sorted(rows, key=key))
    if args.phase == 'integration':
        matches = all(r['integration_match'] for r in rows)
        nonregression = all(r['result'] == 'win' for r in rows if r['baseline_result'] == 'win')
        result.update(integration_match=matches, incumbent_win_preservation=nonregression,
                      passed=all_done and no_errors and matches and nonregression)
    else:
        scores = {ref: {version: sum(points(r) for r in rows if r['rival'] == ref and r['version'] == version)
                        for version in ('old', 'new')} for ref in REFS}
        active = [(seed, ref) for seed in seeds for ref in REFS if all(
            r['candidate_telemetry'].get('selected_arm') == 'v43' for r in rows
            if r['seed'] == seed and r['rival'] == ref and r['version'] == 'new')]
        deltas = [sum(points(r) * (1 if r['version'] == 'new' else -1) for r in rows if r['seed'] == seed)
                  / (2 * len(REFS)) for seed in seeds]
        nonregression = all(s['new'] >= s['old'] for s in scores.values())
        passed = all_done and no_errors and nonregression and sum(deltas) > 0
        passed = passed and len(active) >= (4 if args.phase == 'pilot' else 8)
        result.update(scores=scores, activated_pairs=active, seed_win_point_deltas=deltas,
                      reference_nonregression=nonregression)
        if args.phase == 'confirmation':
            rng = random.Random(2908199)
            bootstrap = sorted(statistics.fmean(rng.choices(deltas, k=len(deltas))) for _ in range(10000))
            interval = [bootstrap[250], bootstrap[9749]]
            result['paired_seed_bootstrap_95'] = interval
            passed = passed and interval[0] > 0
        result['passed'] = bool(passed)
    (HERE / (args.phase + '.json')).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    with exclusive_run(HERE / 'qualification.lock'):
        main()
