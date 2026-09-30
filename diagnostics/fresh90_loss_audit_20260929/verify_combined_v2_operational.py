"""Gated native-framework/action and file-loader verifier for fresh combined V2.

This is an operational runner, not a game launcher for ordinary audit turns.
Use --preflight to inspect inputs without games. Actual games require both
--run and --confirm-gates-passed after the frozen reserved/reacting gates pass.
The fixed receipt is consumed by run_reacting.py's confirm phase.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import argparse
import copy
import gc
import gzip
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
WORK = ROOT / 'diagnostics' / 'fresh90_improvement_20260929'
PHYSICAL = ROOT / 'diagnostics' / 'physical_route_rollout_20260928'
PRIOR = ROOT / 'diagnostics' / 'submission_top100_compare_20260929_1104'
LOCK = ROOT / 'diagnostics' / '.shared_game_run.lock'

CANDIDATE = WORK / 'candidate_fresh_combined_v2.py'
BASELINE = WORK / 'baseline_cb76fbc4.py'
MANIFEST = WORK / 'combined_v2_manifest.json'
TOP_JOBS = WORK / 'combined_v2_top100_jobs.json'
TOP_RESULTS = WORK / 'combined_v2_top100_jobs_results.jsonl'
TOP_RECEIPT = WORK / 'combined_v2_top100_jobs_receipt.json'
SCREEN_JOBS = WORK / 'combined_v2_screen_jobs.json'
SCREEN_RESULTS = WORK / 'combined_v2_screen_results.jsonl'
SCREEN_RECEIPT = WORK / 'combined_v2_screen_receipt.json'
OPERATIONAL_RECEIPT = WORK / 'combined_v2_operational_receipt.json'
RESULTS = OWN / 'combined_v2_operational_results.json'

EXPECTED_CANDIDATE_SHA = '4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4'
EXPECTED_BASELINE_SHA = 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
EXPECTED_ENTRYPOINT = 'kaggle_fresh_execution_schedule_entrypoint'
DEFAULT_LOADER_SEED = 12929001
TARGET_RANKS = (1, 8, 10)
BAD_STATUSES = {'ERROR', 'INVALID', 'TIMEOUT'}

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PRIOR))


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def read_gzip_json(path: Path | str) -> Any:
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def nonzero_error_counters(telemetry: Any) -> dict[str, Any]:
    if not isinstance(telemetry, dict):
        return {'telemetry': 'not a dict'}
    out = {}
    for key, value in telemetry.items():
        if ('error' in str(key).lower() or 'collision' in str(key).lower()) and value:
            out[str(key)] = value
    return out


def result_value_matches(actual: dict[str, Any], expected: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [key for key in fields if actual.get(key) != expected.get(key)]


def route_action_hashes(actions: list[Any]) -> set[str]:
    # Match the exact route collection verifier's supported canonical forms.
    return {hashlib.sha256(json.dumps(actions, sort_keys=sort_keys, separators=(',', ':'),
                                      ensure_ascii=False).encode('utf-8')).hexdigest()
            for sort_keys in (False, True)}


def check_route_source(entry: dict[str, Any]) -> None:
    route = read_gzip_json(entry['path'])
    actions = route.get('actions', [])
    assert len(actions) == 719, (entry.get('episode_id'), 'route action count')
    assert entry['action_sha256'] in route_action_hashes(actions), (entry.get('episode_id'), 'route action hash')
    raw = gzip.decompress(Path(entry['replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == entry['replay_sha256'], (entry.get('episode_id'), 'raw replay hash')
    replay = json.loads(raw.decode('utf-8-sig'))
    assert len(replay.get('steps', [])) == 720, (entry.get('episode_id'), 'raw replay frames')
    assert replay.get('statuses') == ['DONE', 'DONE'], (entry.get('episode_id'), 'source statuses')
    assert replay.get('module_version') == '1.32.7', (entry.get('episode_id'), 'engine version')


def _assert_saved_case_identity(job: dict[str, Any], saved: dict[str, Any], rank: int, seat: int) -> None:
    for field in ('job_id', 'candidate_sha256', 'fixture_id', 'rank', 'episode_id', 'seed',
                  'candidate_seat', 'action_sha256', 'replay_sha256'):
        assert job.get(field) == saved.get(field), (rank, seat, field, job.get(field), saved.get(field))
    assert job['candidate_sha256'] == EXPECTED_CANDIDATE_SHA
    assert Path(job['path']).resolve() == CANDIDATE.resolve()
    assert Path(saved['path']).resolve() == CANDIDATE.resolve()
    assert job.get('label') == saved.get('label') == 'combined_v2'
    assert int(job['candidate_seat']) == seat and int(job['rank']) == rank
    assert int(job['entry']['seed']) == int(job['seed'])
    assert job['entry']['replay_sha256'] == job['replay_sha256']
    assert job['entry']['action_sha256'] == job['action_sha256']
    check_route_source(job['entry'])
    assert saved.get('frames') == 720 and saved.get('candidate_status') == saved.get('opponent_status') == 'DONE'
    assert saved.get('candidate_errors') == {}
    assert not nonzero_error_counters(saved.get('candidate_telemetry', {}))


def _selected_screen_cases(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [r for r in rows if r.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
                  and r.get('version', 'candidate') in ('candidate', 'combined_v2')
                  and r.get('candidate_seat') in (0, 1)
                  and r.get('method', 'fast_native_transitions') in ('fast_native_transitions', 'native')
                  and r.get('rival') != 'cb76']
    candidates.sort(key=lambda r: (int(r.get('seed', 0)), str(r.get('rival', '')), int(r.get('candidate_seat', -1))))
    chosen: list[dict[str, Any]] = []
    used_rivals: set[str] = set()
    for seat in (0, 1):
        match = next((r for r in candidates if int(r['candidate_seat']) == seat
                      and str(r.get('rival')) not in used_rivals), None)
        if match is not None:
            chosen.append(match)
            used_rivals.add(str(match.get('rival')))
    assert len(chosen) >= 2, 'Need candidate reacting rows in both seats against two distinct non-cb76 opponents.'
    for row in chosen:
        assert row.get('path') and Path(row['path']).is_file()
        assert sha(row['path']) == EXPECTED_CANDIDATE_SHA
        assert row.get('opponent') and Path(row['opponent']).is_file()
        assert sha(row['opponent']) == row.get('opponent_sha256')
        assert row.get('frames') == 720 and row.get('candidate_status') == row.get('opponent_status') == 'DONE'
        assert row.get('candidate_errors') == {} and row.get('opponent_errors') == {}
        assert not nonzero_error_counters(row.get('candidate_telemetry', {}))
        assert not nonzero_error_counters(row.get('opponent_telemetry', {}))
    assert len({str(r.get('rival')) for r in chosen}) == 2
    assert {int(r['candidate_seat']) for r in chosen} == {0, 1}
    return chosen


def build_plan(require_screen: bool) -> dict[str, Any]:
    blockers: list[str] = []
    if not CANDIDATE.is_file() or sha(CANDIDATE) != EXPECTED_CANDIDATE_SHA:
        blockers.append('candidate source missing or SHA differs from frozen 4802aa95')
    if not BASELINE.is_file() or sha(BASELINE) != EXPECTED_BASELINE_SHA:
        blockers.append('baseline source missing or SHA differs from uploaded cb76')
    if not MANIFEST.is_file():
        blockers.append('combined V2 manifest missing')
        manifest = {}
    else:
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if manifest.get('candidate_sha256') != EXPECTED_CANDIDATE_SHA or manifest.get('expected_entrypoint') != EXPECTED_ENTRYPOINT:
            blockers.append('combined V2 manifest candidate or entrypoint mismatch')
        if manifest.get('candidate') and Path(manifest['candidate']).resolve() != CANDIDATE.resolve():
            blockers.append('combined V2 manifest points to a different candidate path')
    entrypoint = None
    if CANDIDATE.is_file() and sha(CANDIDATE) == EXPECTED_CANDIDATE_SHA:
        try:
            from kaggle_environments.agent import get_last_callable
            entrypoint = get_last_callable(CANDIDATE.read_text(encoding='utf-8'), path=str(CANDIDATE)).__name__
            if entrypoint != EXPECTED_ENTRYPOINT:
                blockers.append(f'candidate last callable is {entrypoint!r}, expected {EXPECTED_ENTRYPOINT!r}')
        except Exception as ex:
            blockers.append(f'cannot resolve candidate last callable: {type(ex).__name__}: {ex}')
    engine_version = None
    try:
        from paired_benchmark import engine_version as installed_engine_version
        engine_version = str(installed_engine_version)
        if engine_version != '1.32.7':
            blockers.append(f'local Kaggle engine is {engine_version}, expected 1.32.7')
    except Exception as ex:
        blockers.append(f'cannot read local Kaggle engine version: {type(ex).__name__}: {ex}')
    if not all(p.is_file() for p in (TOP_JOBS, TOP_RESULTS, TOP_RECEIPT)):
        blockers.append('top100 jobs, results, or receipt missing')
        top_jobs, top_results, top_receipt = [], [], {}
    else:
        top_jobs = json.loads(TOP_JOBS.read_text(encoding='utf-8'))
        top_results = jsonl(TOP_RESULTS)
        top_receipt = json.loads(TOP_RECEIPT.read_text(encoding='utf-8'))
        if not top_receipt.get('complete') or top_receipt.get('jobs_sha256') != sha(TOP_JOBS) or top_receipt.get('results_sha256') != sha(TOP_RESULTS):
            blockers.append('top100 completion receipt is incomplete or hash-mismatched')
        if len(top_jobs) != 200 or len(top_results) != 200:
            blockers.append('top100 ledger does not contain exactly 200 jobs and results')
    jobs_by_key = {(int(r.get('rank', -1)), int(r.get('candidate_seat', -1))): r for r in top_jobs}
    if len(jobs_by_key) != len(top_jobs):
        blockers.append('duplicate top100 rank/seat job identity')
    results_by_id = {r.get('job_id'): r for r in top_results}
    if len(results_by_id) != len(top_results):
        blockers.append('duplicate top100 result job IDs')
    saved_cases = []
    if top_jobs and top_results:
        for rank in TARGET_RANKS:
            for seat in (0, 1):
                job = jobs_by_key.get((rank, seat))
                if not job:
                    blockers.append(f'missing saved top100 job r{rank}/s{seat}')
                    continue
                saved = results_by_id.get(job.get('job_id'))
                if not saved:
                    blockers.append(f'missing saved top100 result {job.get("job_id")}')
                    continue
                try:
                    _assert_saved_case_identity(job, saved, rank, seat)
                    telemetry = saved['candidate_telemetry']
                    if rank == 8 and not telemetry.get('fresh_complete_route'):
                        blockers.append('rank 8 did not activate its recorded complete route')
                    if rank == 10 and int(telemetry.get('funded_land_turns', 0)) <= 0:
                        blockers.append('rank 10 did not activate funded land')
                    if rank == 1 and (telemetry.get('fresh_complete_route') or int(telemetry.get('funded_land_turns', 0)) != 0):
                        blockers.append('rank 1 is no longer an inactive control')
                    saved_cases.append({'job': job, 'saved': saved, 'rank_case': rank, 'seat': seat})
                except Exception as ex:
                    blockers.append(f'invalid saved r{rank}/s{seat}: {type(ex).__name__}: {ex}')

    screen_receipt: dict[str, Any] = {}
    screen_rows: list[dict[str, Any]] = []
    screen_cases: list[dict[str, Any]] = []
    if not all(p.is_file() for p in (SCREEN_JOBS, SCREEN_RESULTS, SCREEN_RECEIPT)):
        if require_screen:
            blockers.append('combined_v2 screen jobs/results/receipt missing; wait for reacting screen completion')
    else:
        screen_jobs = json.loads(SCREEN_JOBS.read_text(encoding='utf-8'))
        screen_rows = jsonl(SCREEN_RESULTS)
        screen_receipt = json.loads(SCREEN_RECEIPT.read_text(encoding='utf-8'))
        if not screen_receipt.get('complete') or screen_receipt.get('phase') != 'screen':
            blockers.append('combined_v2 reacting screen receipt is incomplete or not the screen phase')
        if screen_receipt.get('candidate_sha256') != EXPECTED_CANDIDATE_SHA:
            blockers.append('reacting screen receipt candidate SHA mismatch')
        if screen_receipt.get('jobs_sha256') != sha(SCREEN_JOBS) or screen_receipt.get('results_sha256') != sha(SCREEN_RESULTS):
            blockers.append('reacting screen receipt job/results hash mismatch')
        if not (screen_receipt.get('assessment', {}).get('screen_passed') is True):
            blockers.append('reacting screen did not pass its frozen screen gate')
        screen_jobs_by_id = {r.get('job_id'): r for r in screen_jobs}
        screen_rows_by_id = {r.get('job_id'): r for r in screen_rows}
        if len(screen_rows_by_id) != len(screen_rows):
            blockers.append('duplicate reacting screen result job IDs')
        if set(screen_jobs_by_id) != set(screen_rows_by_id):
            blockers.append('reacting screen results do not cover exactly the frozen jobs')
        for row in screen_rows:
            job = screen_jobs_by_id.get(row.get('job_id'), {})
            for key in ('version', 'rival', 'seed', 'candidate_seat', 'path', 'candidate_sha256', 'opponent', 'opponent_sha256', 'method'):
                if key in job and row.get(key) != job[key]:
                    blockers.append(f'reacting result identity mismatch for {row.get("job_id")} field {key}')
        try:
            screen_cases = _selected_screen_cases(screen_rows)
        except Exception as ex:
            blockers.append(f'cannot select reacting parity cases: {type(ex).__name__}: {ex}')
    if require_screen and not screen_cases:
        blockers.append('no reacting parity cases available')

    source_paths = [Path(__file__), MANIFEST, CANDIDATE, BASELINE, TOP_JOBS, TOP_RESULTS, TOP_RECEIPT,
                    SCREEN_JOBS, SCREEN_RESULTS, SCREEN_RECEIPT,
                    ROOT / 'diagnostics' / 'top100_regression_repair_20260929' / 'verify_native.py',
                    ROOT / 'diagnostics' / 'top100_regression_repair_20260929' / 'verify_loader.py',
                    ROOT / 'diagnostics' / 'opening_probe_v2_20260928' / 'qualify.py',
                    ROOT / 'diagnostics' / 'physical_route_rollout_20260928' / 'fast_reactive.py',
                    ROOT / 'diagnostics' / 'physical_route_rollout_20260928' / 'native_core.py',
                    PRIOR / 'fast_game_current.py', PRIOR / 'current_input.py',
                    ROOT / 'raw_route_agent.py', ROOT / 'paired_benchmark.py',
                    ROOT / 'diagnostics' / 'local_target_20260928' / 'run_lock.py']
    data_paths = list(source_paths)
    for case in saved_cases:
        entry = case['job']['entry']
        data_paths.extend((Path(entry['path']), Path(entry['replay_path'])))
    for row in screen_cases:
        data_paths.append(Path(row['opponent']))
    source_hashes = {str(p.resolve()): sha(p) for p in data_paths if p.is_file()}
    return {'ready': not blockers, 'blockers': blockers, 'manifest': manifest,
            'entrypoint': entrypoint, 'engine_version': engine_version,
            'saved_cases': saved_cases, 'screen_cases': screen_cases,
            'source_hashes': source_hashes,
            'top_jobs_sha256': sha(TOP_JOBS) if TOP_JOBS.is_file() else None,
            'top_results_sha256': sha(TOP_RESULTS) if TOP_RESULTS.is_file() else None,
            'screen_jobs_sha256': sha(SCREEN_JOBS) if SCREEN_JOBS.is_file() else None,
            'screen_results_sha256': sha(SCREEN_RESULTS) if SCREEN_RESULTS.is_file() else None,
            'screen_receipt_sha256': sha(SCREEN_RECEIPT) if SCREEN_RECEIPT.is_file() else None}


@contextmanager
def capture_core_actions():
    """Capture both players' 719 actions from the exact pure-native transition path."""
    core = importlib.import_module('diagnostics.physical_route_rollout_20260928.native_core')
    original = core.interpreter
    frames: list[list[Any]] = []

    def recording_interpreter(state: Any, env: Any) -> Any:
        frames.append([copy.deepcopy(getattr(player, 'action', None)) for player in state])
        return original(state, env)

    core.interpreter = recording_interpreter
    try:
        yield frames
    finally:
        core.interpreter = original


def _route_fixture(job: dict[str, Any]) -> dict[str, Any]:
    entry = job['entry']
    return {'fixture_id': job['fixture_id'], 'seed': int(job['seed']),
            'source_replay_path': entry['replay_path'], 'source_replay_sha256': entry['replay_sha256'],
            'source_action_tape_path': entry['path'], 'source_opponent_action_sha256': entry['action_sha256']}


def _load_fast_game_module():
    module = importlib.import_module('fast_game_current')
    return module


def _load_fast_reactive_module():
    return importlib.import_module('diagnostics.physical_route_rollout_20260928.fast_reactive')


def _action_views(joint: list[list[Any]], seat: int) -> dict[str, Any]:
    assert len(joint) == 719, f'expected 719 transitions, got {len(joint)}'
    return {'candidate_actions': [frame[seat] for frame in joint],
            'joint_actions': joint,
            'candidate_action_sha256': canonical_sha([frame[seat] for frame in joint]),
            'joint_action_sha256': canonical_sha(joint)}


def run_fast_route(case: dict[str, Any]) -> dict[str, Any]:
    job, saved, seat = case['job'], case['saved'], int(case['seat'])
    runner = _load_fast_game_module()
    fixture = _route_fixture(job)
    with capture_core_actions() as joint:
        actual = runner.play(fixture, CANDIDATE, EXPECTED_CANDIDATE_SHA, seat)
    assert len(joint) == 719, (job['job_id'], 'fast-native action count')
    expected_fields = ('candidate_reward', 'opponent_reward', 'result', 'frames', 'candidate_status',
                       'opponent_status', 'candidate_telemetry', 'candidate_errors')
    mismatches = result_value_matches(actual, saved, expected_fields)
    actual = dict(actual)
    actual['reproduced_saved_mismatches'] = mismatches
    actual.update(_action_views(joint, seat))
    actual['job_id'] = job['job_id']
    actual['passed'] = (not mismatches and actual['frames'] == 720 and
                        actual['candidate_status'] == actual['opponent_status'] == 'DONE' and
                        not actual.get('candidate_errors') and not nonzero_error_counters(actual.get('candidate_telemetry')))
    return actual


def _framework_call(module: Any) -> Callable[[Any, Any], Any]:
    def call(obs: Any, cfg: Any) -> Any:
        visible = dict(cfg)
        visible['seed'] = None
        return module.agent(obs, visible)
    return call


def _module_errors(module: Any) -> dict[str, Any]:
    qualify = importlib.import_module('diagnostics.opening_probe_v2_20260928.qualify')
    return qualify.errors(module)


def _framework_result(env: Any, modules_by_seat: list[Any | None], seat: int,
                      job_id: str, expected_fast: dict[str, Any] | None = None) -> dict[str, Any]:
    final = env.steps[-1]
    bad = [(step, player, state.status) for step, frame in enumerate(env.steps) for player, state in enumerate(frame)
           if state.status in BAD_STATUSES]
    stderr = [(step, player, str(log.get('stderr', ''))) for step, logs in enumerate(env.logs)
              for player, log in enumerate(logs) if str(log.get('stderr', '')).strip()]
    calls = [sum(len(logs) > player and 'duration' in logs[player] for logs in env.logs) for player in (0, 1)]
    joint = [[copy.deepcopy(frame[player].action) for player in (0, 1)] for frame in env.steps[1:]]
    view = _action_views(joint, seat)
    own = float(final[seat].reward or 0)
    rival = float(final[1-seat].reward or 0)
    telemetry = dict(getattr(modules_by_seat[seat].agent, 'telemetry', {}) or {}) if modules_by_seat[seat] else {}
    errors = _module_errors(modules_by_seat[seat]) if modules_by_seat[seat] else {}
    opponent_telemetry = dict(getattr(modules_by_seat[1-seat].agent, 'telemetry', {}) or {}) if modules_by_seat[1-seat] else {}
    opponent_errors = _module_errors(modules_by_seat[1-seat]) if modules_by_seat[1-seat] else {}
    minimum_overage = min(float(frame[seat].observation.remainingOverageTime) for frame in env.steps)
    row = {'job_id': job_id, 'candidate_reward': own, 'opponent_reward': rival,
           'result': 'win' if own > rival else 'loss' if own < rival else 'draw',
           'frames': len(env.steps), 'candidate_status': final[seat].status,
           'opponent_status': final[1-seat].status, 'native_calls': calls,
           'bad_statuses': bad, 'stderr': stderr, 'minimum_remaining_overage': minimum_overage,
           'candidate_telemetry': telemetry, 'opponent_telemetry': opponent_telemetry,
           'candidate_policy_errors': errors, 'opponent_policy_errors': opponent_errors,
           'candidate_error_counters': nonzero_error_counters(telemetry),
           'opponent_error_counters': nonzero_error_counters(opponent_telemetry)}
    row.update(view)
    row['passed'] = (row['frames'] == 720 and row['native_calls'] == [719, 719]
                     and row['candidate_status'] == row['opponent_status'] == 'DONE'
                     and not bad and not stderr and minimum_overage >= 0
                     and not errors and not opponent_errors
                     and not row['candidate_error_counters'] and not row['opponent_error_counters'])
    if expected_fast is not None:
        row['fast_action_match'] = joint == expected_fast['joint_actions']
        row['fast_candidate_telemetry_match'] = telemetry == expected_fast['candidate_telemetry']
        row['fast_opponent_telemetry_match'] = opponent_telemetry == expected_fast.get('opponent_telemetry', {})
        row['passed'] = bool(row['passed'] and row['fast_action_match'] and
                             row['fast_candidate_telemetry_match'] and row['fast_opponent_telemetry_match'] and
                             own == expected_fast['candidate_reward'] and rival == expected_fast['opponent_reward'] and
                             row['candidate_status'] == expected_fast['candidate_status'] and
                             row['opponent_status'] == expected_fast['opponent_status'])
    return row


def _framework_env(config: dict[str, Any], seed: int, agents: list[Any]) -> Any:
    from paired_benchmark import make
    config = dict(config)
    config['episodeSteps'] = 720
    config['seed'] = int(seed)
    env = make('kaggriculture', configuration=config, debug=False)
    env.run(agents)
    return env


def run_framework_route(case: dict[str, Any], fast: dict[str, Any]) -> dict[str, Any]:
    from paired_benchmark import _load_agent, _load_module, TimedAgent
    job, seat = case['job'], int(case['seat'])
    entry = job['entry']
    raw = read_gzip_json(entry['replay_path'])
    config = dict(raw.get('configuration', {}))
    config['seed'] = int(job['seed'])
    modules: list[Any | None] = [None, None]
    timed_agents: list[Any] = [None, None]
    candidate_module = _load_module(CANDIDATE, f'operational_candidate_route_{job["rank"]}_{seat}')
    modules[seat] = candidate_module
    timed_agents[seat] = TimedAgent(_framework_call(candidate_module), module_name=candidate_module.__name__)
    opponent, opponent_timed = _load_agent('rawroute:' + entry['path'], f'operational_route_{job["rank"]}_{seat}')
    timed_agents[1-seat] = opponent
    if opponent_timed is not None and opponent_timed.module_name:
        modules[1-seat] = sys.modules.get(opponent_timed.module_name)
    # timed_agents is already stored by absolute player seat.
    agents = timed_agents
    try:
        env = _framework_env(config, int(job['seed']), agents)
        return _framework_result(env, modules, seat, job['job_id'], fast)
    finally:
        for module in modules:
            if module is not None:
                sys.modules.pop(module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)
        sys.modules.pop(candidate_module.__name__, None)
        del agents, timed_agents
        gc.collect()


def run_fast_reacting(row: dict[str, Any]) -> dict[str, Any]:
    runner = _load_fast_reactive_module()
    with capture_core_actions() as joint:
        actual = runner.play(row)
    assert len(joint) == 719, (row.get('job_id'), 'fast-reactive action count')
    fields = ('candidate_reward', 'opponent_reward', 'result', 'frames', 'candidate_status',
              'opponent_status', 'candidate_telemetry', 'opponent_telemetry', 'candidate_errors', 'opponent_errors')
    mismatches = result_value_matches(actual, row, fields)
    actual = dict(actual)
    actual['job_id'] = row['job_id']
    actual['reproduced_screen_mismatches'] = mismatches
    actual.update(_action_views(joint, int(row['candidate_seat'])))
    actual['passed'] = (not mismatches and actual['frames'] == 720 and
                        actual['candidate_status'] == actual['opponent_status'] == 'DONE' and
                        not actual.get('candidate_errors') and not actual.get('opponent_errors') and
                        not nonzero_error_counters(actual.get('candidate_telemetry')) and
                        not nonzero_error_counters(actual.get('opponent_telemetry')))
    return actual


def run_framework_reacting(row: dict[str, Any], fast: dict[str, Any]) -> dict[str, Any]:
    from paired_benchmark import _load_module, TimedAgent
    seat = int(row['candidate_seat'])
    modules: list[Any | None] = [None, None]
    timed_agents: list[Any] = [None, None]
    paths = [None, None]
    paths[seat] = row['path']
    paths[1-seat] = row['opponent']
    for player in (0, 1):
        module = _load_module(Path(paths[player]), f'operational_reacting_{row["job_id"]}_{player}')
        modules[player] = module
        timed_agents[player] = TimedAgent(_framework_call(module), module_name=module.__name__)
    template = json.loads((PHYSICAL / 'initial_template.json').read_text(encoding='utf-8'))
    config = dict(template['configuration'])
    try:
        env = _framework_env(config, int(row['seed']), timed_agents)
        return _framework_result(env, modules, seat, row['job_id'], fast)
    finally:
        for module in modules:
            if module is not None:
                sys.modules.pop(module.__name__, None)
        del timed_agents, modules
        gc.collect()


def run_loader_one(path: Path, baseline: Path, seed: int, seat: int, mode: str) -> dict[str, Any]:
    from paired_benchmark import _load_module, TimedAgent
    modules: list[Any | None] = [None, None]
    paths = [path, baseline] if seat == 0 else [baseline, path]
    try:
        if mode == 'direct':
            agents = []
            for player, module_path in enumerate(paths):
                module = _load_module(Path(module_path), f'operational_loader_{seed}_{seat}_{player}')
                modules[player] = module
                agents.append(TimedAgent(_framework_call(module), module_name=module.__name__))
        elif mode == 'file':
            agents = [str(Path(p)) for p in paths]
        else:
            raise ValueError(mode)
        config = {'episodeSteps': 720, 'seed': int(seed)}
        env = _framework_env(config, seed, agents)
        final = env.steps[-1]
        bad = [(step, player, state.status) for step, frame in enumerate(env.steps) for player, state in enumerate(frame)
               if state.status in BAD_STATUSES]
        stderr = [(step, player, str(log.get('stderr', ''))) for step, logs in enumerate(env.logs)
                  for player, log in enumerate(logs) if str(log.get('stderr', '')).strip()]
        calls = [sum(len(logs) > player and 'duration' in logs[player] for logs in env.logs) for player in (0, 1)]
        joint = [[copy.deepcopy(frame[player].action) for player in (0, 1)] for frame in env.steps[1:]]
        own = float(final[seat].reward or 0)
        rival = float(final[1-seat].reward or 0)
        min_overage = min(float(frame[seat].observation.remainingOverageTime) for frame in env.steps)
        candidate_module = modules[seat]
        policy_errors = _module_errors(candidate_module) if candidate_module is not None else {}
        row = {'mode': mode, 'seed': int(seed), 'candidate_seat': seat,
               'statuses': [s.status for s in final], 'frames': len(env.steps),
               'rewards': [float(s.reward or 0) for s in final],
               'candidate_action_sha256': canonical_sha([a[seat] for a in joint]),
               'joint_action_sha256': canonical_sha(joint), 'native_calls': calls,
               'bad_statuses': bad, 'stderr': stderr, 'minimum_remaining_overage': min_overage,
               'candidate_policy_errors': policy_errors,
               'candidate_error_counters': nonzero_error_counters(
                   dict(getattr(candidate_module.agent, 'telemetry', {}) or {}) if candidate_module else {})}
        row['passed'] = (row['statuses'] == ['DONE', 'DONE'] and row['frames'] == 720 and calls == [719, 719]
                         and not bad and not stderr and not policy_errors and min_overage >= 0
                         and not row['candidate_error_counters'])
        return row
    finally:
        for module in modules:
            if module is not None:
                sys.modules.pop(module.__name__, None)
        gc.collect()


def run_loader_suite(plan: dict[str, Any]) -> dict[str, Any]:
    from kaggle_environments.agent import get_last_callable
    entrypoint = get_last_callable(CANDIDATE.read_text(encoding='utf-8'), path=str(CANDIDATE)).__name__
    assert entrypoint == EXPECTED_ENTRYPOINT, (entrypoint, EXPECTED_ENTRYPOINT)
    saved_seed_by_rank = {int(c['rank_case']): int(c['job']['seed']) for c in plan['saved_cases']}
    seeds = list(dict.fromkeys([DEFAULT_LOADER_SEED, saved_seed_by_rank[8], saved_seed_by_rank[10]]))
    rows = []
    parity = []
    for seed in seeds:
        for seat in (0, 1):
            direct = run_loader_one(CANDIDATE, BASELINE, seed, seat, 'direct')
            file_loaded = run_loader_one(CANDIDATE, BASELINE, seed, seat, 'file')
            pair_match = (direct['rewards'] == file_loaded['rewards']
                          and direct['statuses'] == file_loaded['statuses']
                          and direct['candidate_action_sha256'] == file_loaded['candidate_action_sha256']
                          and direct['joint_action_sha256'] == file_loaded['joint_action_sha256'])
            parity.append({'seed': seed, 'candidate_seat': seat, 'direct_vs_file_match': pair_match})
            direct['direct_file_match'] = pair_match
            file_loaded['direct_file_match'] = pair_match
            rows.extend((direct, file_loaded))
    return {'entrypoint': entrypoint, 'seeds': seeds, 'rows': rows, 'parity': parity,
            'passed': all(r['passed'] for r in rows) and all(p['direct_vs_file_match'] for p in parity)}


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def _case_basics_pass(row: dict[str, Any]) -> bool:
    return bool(row.get('passed'))


def _compact_result(row: dict[str, Any]) -> dict[str, Any]:
    """Persist hashes and parity verdicts, not duplicated 719-action arrays."""
    return {key: value for key, value in row.items() if key not in ('candidate_actions', 'joint_actions')}


def run_all(plan: dict[str, Any]) -> dict[str, Any]:
    fast_route_rows = []
    framework_route_rows = []
    fast_reacting_rows = []
    framework_reacting_rows = []
    failure = None
    try:
        for case in plan['saved_cases']:
            fast = run_fast_route(case)
            fast_route_rows.append(_compact_result(fast))
            framework = run_framework_route(case, fast)
            framework_route_rows.append(_compact_result(framework))
        for case in plan['screen_cases']:
            fast = run_fast_reacting(case)
            fast_reacting_rows.append(_compact_result(fast))
            framework = run_framework_reacting(case, fast)
            framework_reacting_rows.append(_compact_result(framework))
        loader = run_loader_suite(plan)
    except Exception as ex:
        failure = {'type': type(ex).__name__, 'message': str(ex)}
        loader = {'passed': False, 'error': failure, 'rows': [], 'parity': []}

    candidate_stable = CANDIDATE.is_file() and sha(CANDIDATE) == EXPECTED_CANDIDATE_SHA
    baseline_stable = BASELINE.is_file() and sha(BASELINE) == EXPECTED_BASELINE_SHA
    current_hashes = {str(p): sha(p) for p in (CANDIDATE, BASELINE) if p.is_file()}
    inputs_stable = all(Path(path).is_file() and sha(path) == digest
                        for path, digest in plan['source_hashes'].items())
    route_passed = (len(fast_route_rows) == 6 and len(framework_route_rows) == 6
                    and all(_case_basics_pass(r) for r in fast_route_rows)
                    and all(_case_basics_pass(r) for r in framework_route_rows))
    reacting_passed = (len(fast_reacting_rows) >= 2 and len(framework_reacting_rows) >= 2
                       and all(_case_basics_pass(r) for r in fast_reacting_rows)
                       and all(_case_basics_pass(r) for r in framework_reacting_rows))
    passed = bool(failure is None and candidate_stable and baseline_stable and inputs_stable
                  and route_passed and reacting_passed and loader.get('passed'))
    return {'complete': failure is None, 'passed': passed, 'candidate_sha256': EXPECTED_CANDIDATE_SHA,
            'baseline_sha256': EXPECTED_BASELINE_SHA, 'expected_entrypoint': EXPECTED_ENTRYPOINT,
            'native_engine_version': plan['engine_version'],
            'gates_declared_passed_by_operator': True,
            'cases': {'saved_fast_native_vs_framework': framework_route_rows,
                      'saved_fast_native_reproduction': fast_route_rows,
                      'reacting_fast_native_vs_framework': framework_reacting_rows,
                      'reacting_fast_native_reproduction': fast_reacting_rows,
                      'file_loader': loader},
            'checks': {'candidate_sha_stable': candidate_stable, 'baseline_sha_stable': baseline_stable,
                       'input_hashes_stable': inputs_stable, 'saved_native_cases_passed': route_passed,
                       'reacting_cases_passed': reacting_passed, 'loader_direct_file_passed': bool(loader.get('passed'))},
            'input_hashes': plan['source_hashes'], 'post_run_source_hashes': current_hashes,
            'screen_receipt_sha256': plan['screen_receipt_sha256'],
            'selected_saved_cases': [{'job_id': c['job']['job_id'], 'rank': c['rank_case'], 'seat': c['seat'],
                                      'episode_id': c['job']['episode_id'], 'seed': c['job']['seed']}
                                     for c in plan['saved_cases']],
            'selected_reacting_cases': [{'job_id': r['job_id'], 'rival': r['rival'], 'seed': r['seed'],
                                         'candidate_seat': r['candidate_seat']} for r in plan['screen_cases']],
            'failure': failure, 'completed_at_utc': datetime.now(timezone.utc).isoformat()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--preflight', action='store_true', help='Check source, frozen jobs, and screen gates; run no games.')
    modes.add_argument('--run', action='store_true', help='Run the operational checks under the shared game lock.')
    parser.add_argument('--confirm-gates-passed', action='store_true',
                        help='Required with --run: operator confirms reserved and reacting gates have passed.')
    args = parser.parse_args()
    if args.run and not args.confirm_gates_passed:
        parser.error('--run requires --confirm-gates-passed after the frozen reserved/reacting gates pass')
    plan = build_plan(require_screen=True)
    if args.preflight:
        summary = {'ready': plan['ready'], 'blockers': plan['blockers'],
                   'saved_cases': [{'job_id': c['job']['job_id'], 'rank': c['rank_case'], 'seat': c['seat']}
                                   for c in plan['saved_cases']],
                   'reacting_cases': [{'job_id': r.get('job_id'), 'rival': r.get('rival'), 'seed': r.get('seed'),
                                       'candidate_seat': r.get('candidate_seat')} for r in plan['screen_cases']]}
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0 if plan['ready'] else 2

    # Fail closed for future confirmation even if a previous run left a true receipt.
    provisional = {'complete': False, 'passed': False, 'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                   'baseline_sha256': EXPECTED_BASELINE_SHA, 'started_at_utc': datetime.now(timezone.utc).isoformat(),
                   'reason': 'operational checks have not completed'}
    _atomic_json(OPERATIONAL_RECEIPT, provisional)
    try:
        if not plan['ready']:
            raise RuntimeError('Preflight failed: ' + '; '.join(plan['blockers']))
        with importlib.import_module('diagnostics.local_target_20260928.run_lock').exclusive_run(LOCK):
            # Recheck that no source/ledger changed while waiting for the lock.
            locked_plan = build_plan(require_screen=True)
            if not locked_plan['ready']:
                raise RuntimeError('Locked preflight failed: ' + '; '.join(locked_plan['blockers']))
            if locked_plan['source_hashes'] != plan['source_hashes']:
                raise RuntimeError('Source/input hashes changed while acquiring shared game lock')
            result = run_all(locked_plan)
        result['runner_sha256'] = sha(Path(__file__))
        result['run_lock_path'] = str(LOCK)
        result['run_lock_used'] = True
        _atomic_json(RESULTS, result)
        _atomic_json(OPERATIONAL_RECEIPT, result)
        print(json.dumps({'passed': result['passed'], 'receipt': str(OPERATIONAL_RECEIPT),
                          'results': str(RESULTS), 'checks': result['checks']}, indent=2))
        return 0 if result['passed'] else 1
    except Exception as ex:
        failed = dict(provisional, complete=False, passed=False,
                      failure={'type': type(ex).__name__, 'message': str(ex)},
                      failed_at_utc=datetime.now(timezone.utc).isoformat())
        _atomic_json(OPERATIONAL_RECEIPT, failed)
        _atomic_json(RESULTS, failed)
        print(json.dumps(failed, indent=2, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
