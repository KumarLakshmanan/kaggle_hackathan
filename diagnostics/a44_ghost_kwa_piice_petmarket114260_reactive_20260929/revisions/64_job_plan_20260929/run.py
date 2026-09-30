from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import sys

from build_preflight import HERE, ROOT, verify

RESULTS = HERE / 'outcomes.jsonl'
RECEIPT = HERE / 'outcome_receipt.json'
RUN_MANIFEST = HERE / 'run_manifest.json'
OWN_LOCK = HERE / 'qualification.lock'
SHARED_LOCK = ROOT / 'diagnostics/.shared_game_run.lock'
PET_KEYS = (
    'a44_pet_market_gate_key72',
    'a44_pet_market_gate_rival_melon72',
    'a44_pet_market_gate_wheat_stock72',
    'a44_pet_market_gate_active72',
    'a44_pet_market_gate_route72',
    'a44_pet_market_gate_turns',
    'a44_pet_market_gate_errors',
)
VERSIONS = ('parent_6a', 'pet_candidate')
POINTS = {'win': 1.0, 'draw': 0.5, 'loss': 0.0}


def gate_telemetry(row):
    telemetry = row.get('candidate_telemetry') or {}
    gate = {key: telemetry.get(key) for key in PET_KEYS}
    active = telemetry.get('a44_pet_market_gate_active72')
    route = telemetry.get('a44_pet_market_gate_route72')
    calls = telemetry.get('a44_pet_market_gate_turns')
    expected_route = '113517834' if active is True else ''
    expected_calls = 647 if active is True else 0
    checks = {
        'all_gate_fields_present': all(telemetry.get(key) is not None for key in PET_KEYS),
        'gate_errors_zero': telemetry.get('a44_pet_market_gate_errors') == 0,
        'active_route_consistent': route == expected_route,
        'active_call_count_consistent': calls == expected_calls,
    }
    return {'observed': gate, 'checks': checks, 'passed': all(checks.values())}


def point_total(rows):
    return sum(POINTS[row['result']] for row in rows)


def wdl(rows):
    return {result: sum(row['result'] == result for row in rows)
            for result in ('win', 'draw', 'loss')}


def summarize(rows, manifest):
    by_key = {(row['version'], row['opponent_id'], int(row['seed']),
               int(row['candidate_seat'])): row for row in rows}
    assert len(by_key) == len(rows) == manifest['planned_game_count']
    per_opponent = {}
    for opponent_id in manifest['opponents']:
        block = {}
        for version in VERSIONS:
            selected = [row for row in rows
                        if row['opponent_id'] == opponent_id and row['version'] == version]
            block[version] = {
                'games': len(selected),
                'points': point_total(selected),
                'wdl': wdl(selected),
                'mean_margin_diagnostic': sum(row['margin'] for row in selected) / len(selected),
            }
        block['paired_point_delta_candidate_minus_6a'] = (
            block['pet_candidate']['points'] - block['parent_6a']['points'])
        per_opponent[opponent_id] = block

    seed_blocks = []
    for seed in manifest['seed_block']:
        delta = 0.0
        scores = {}
        for version in VERSIONS:
            selected = [row for row in rows
                        if row['version'] == version and int(row['seed']) == int(seed)]
            scores[version] = point_total(selected)
        delta = scores['pet_candidate'] - scores['parent_6a']
        seed_blocks.append({'seed': int(seed), 'points_by_version': scores,
                            'paired_delta_candidate_minus_6a': delta})

    candidate_rows = [row for row in rows if row['version'] == 'pet_candidate']
    all_clean = (len(rows) == 64 and all(
        row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
        for row in rows))
    no_errors = all(not row.get('candidate_errors') and not row.get('opponent_errors')
                    for row in rows)
    telemetry_rows = [row['pet_gate_telemetry'] for row in candidate_rows]
    telemetry_consistent = (len(telemetry_rows) == 32 and
                            all(item['passed'] for item in telemetry_rows))
    max_candidate_ms = max((float((row.get('candidate_timing') or {}).get('max_ms', 0.0))
                            for row in candidate_rows), default=float('inf'))
    per_opponent_nonregression = all(
        block['paired_point_delta_candidate_minus_6a'] >= 0
        for block in per_opponent.values())
    candidate_total = sum(block['pet_candidate']['points'] for block in per_opponent.values())
    parent_total = sum(block['parent_6a']['points'] for block in per_opponent.values())
    seed_nonnegative_count = sum(item['paired_delta_candidate_minus_6a'] >= 0
                                 for item in seed_blocks)
    checks = {
        '64_unique_done_done_720_games': all_clean,
        'zero_candidate_and_opponent_errors': no_errors,
        'candidate_pet_telemetry_consistent': telemetry_consistent,
        'max_candidate_call_under_1000ms': max_candidate_ms < 1000.0,
        'no_per_opponent_point_regression': per_opponent_nonregression,
        'pooled_candidate_points_exceed_6a': candidate_total > parent_total,
        'at_least_3_of_4_nonnegative_seed_blocks': seed_nonnegative_count >= 3,
    }
    return {
        'per_opponent': per_opponent,
        'pooled_points': {'pet_candidate': candidate_total, 'parent_6a': parent_total,
                          'delta_candidate_minus_6a': candidate_total - parent_total},
        'seed_blocks': seed_blocks,
        'nonnegative_seed_block_count': seed_nonnegative_count,
        'candidate_pet_gate_active_game_count': sum(
            item['observed'].get('a44_pet_market_gate_active72') is True
            for item in telemetry_rows),
        'candidate_pet_gate_telemetry': [
            {'job_id': row['job_id'], 'observed': row['pet_gate_telemetry']['observed']}
            for row in candidate_rows],
        'max_candidate_call_ms': max_candidate_ms,
        'checks': checks,
        'passed': all(checks.values()),
    }


def run():
    manifest, jobs = verify()
    from paired_benchmark import engine_version
    assert engine_version == manifest['engine_version'] == '1.32.7'
    from diagnostics.opening_probe_v2_20260928.qualify import play
    from diagnostics.local_target_20260928.run_lock import exclusive_run

    started = datetime.now(timezone.utc).isoformat()
    output_paths = manifest['output_paths']
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            assert not any(Path(output_paths[name]).exists()
                           for name in ('outcomes', 'receipt', 'run_manifest'))
            with RUN_MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump({
                    'started_at_utc': started,
                    'frozen_manifest_sha256': hashlib.sha256(
                        (HERE / 'frozen_manifest.json').read_bytes()).hexdigest(),
                    'candidate_sha256': manifest['candidate_sha256'],
                    'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                    'opponent_hashes': manifest['opponents'],
                    'engine_version': engine_version,
                    'seed_block': manifest['seed_block'],
                    'planned_games': len(jobs),
                    'fixed_tape': False,
                    'one_shot': True,
                    'worker_count': 1,
                }, stream, indent=2)
                stream.write('\n')

            rows = []
            with RESULTS.open('x', encoding='utf-8', newline='\n') as stream:
                for index, job in enumerate(jobs, start=1):
                    actual = play(job)
                    result = dict(actual)
                    result['game_points'] = POINTS[result['result']]
                    result['clean_done_done_720'] = (
                        result['frames'] == 720 and result['candidate_status'] ==
                        result['opponent_status'] == 'DONE')
                    result['zero_policy_errors'] = (
                        not result.get('candidate_errors') and not result.get('opponent_errors'))
                    result['pet_gate_telemetry'] = (
                        gate_telemetry(result) if result['version'] == 'pet_candidate' else None)
                    rows.append(result)
                    stream.write(json.dumps(result, ensure_ascii=True, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({
                        'completed': index,
                        'planned': len(jobs),
                        'job_id': result['job_id'],
                        'version': result['version'],
                        'opponent': result['opponent_id'],
                        'seed': result['seed'],
                        'seat': result['candidate_seat'],
                        'result': result['result'],
                        'margin': result['margin'],
                        'clean': result['clean_done_done_720'],
                        'errors': result['zero_policy_errors'],
                    }, ensure_ascii=True), flush=True)

            summary = summarize(rows, manifest)
            receipt = {
                'schema': 'pet-6a-reactive-original-shop-pilot-outcome-v1',
                'complete': len(rows) == 64,
                'diagnostic_only': True,
                'reactive_original_shop_episodes': True,
                'fixed_tape_only': False,
                'promotion': False,
                'candidate_sha256': manifest['candidate_sha256'],
                'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                'frozen_manifest_sha256': hashlib.sha256(
                    (HERE / 'frozen_manifest.json').read_bytes()).hexdigest(),
                'seed_block': manifest['seed_block'],
                'opponents': manifest['opponents'],
                'games': rows,
                **summary,
                'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            }
            with RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(receipt, stream, ensure_ascii=True, indent=2)
                stream.write('\n')
            print(json.dumps({key: value for key, value in receipt.items()
                              if key not in ('games', 'candidate_pet_gate_telemetry')},
                             ensure_ascii=True, indent=2), flush=True)
            return receipt


if __name__ == '__main__':
    if '--root-release' not in sys.argv:
        manifest, jobs = verify()
        print(json.dumps({'verified': True, 'planned_games': len(jobs),
                          'native_game_runs_now': 0,
                          'note': 'Pass --root-release only after the root task coordinates the simulator.'},
                         indent=2))
    else:
        result = run()
        if not result['passed']:
            raise SystemExit(1)
