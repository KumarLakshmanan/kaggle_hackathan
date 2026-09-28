"""Outcome-blind source prefixes for all saved fixture/seat combinations."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import gc
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames, sha
from diagnostics.physical_route_rollout_20260928.fast_reactive import load_policy, errors
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.guarded_route_pool_20260928.search import SOURCE, SOURCE_SHA, TARGETS, TARGETS_SHA, WINS, WINS_SHA


def prefix(job):
    fixture, seat, correction_sha, helper_sha = job
    raw = gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == fixture['source_replay_sha256']
    replay = json.loads(raw)
    state = state_from_frames(replay['steps'][0])
    recorded_pair = list(replay['steps'][144][0]['observation']['town']['unlocked_shops'][:2])
    cfg = dict(replay['configuration']); cfg['seed'] = None
    env = Box(configuration=Box(**cfg), info={'seed': int(fixture['seed'])}, done=False)
    del raw, replay; gc.collect()
    tape = json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    assert fixture['source_opponent_action_sha256'] in {
        hashlib.sha256(json.dumps(tape, sort_keys=order, separators=(',', ':')).encode()).hexdigest()
        for order in (False, True)
    }
    assert sha(SOURCE) == SOURCE_SHA
    module = load_policy(SOURCE, 'guarded_route_coverage_source')
    own_actions = []
    for step in range(144):
        obs = copy.deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))
        action = module.agent(obs, cfg)
        own_actions.append(copy.deepcopy(action))
        state[seat].action = action
        state[1-seat].action = copy.deepcopy(tape[step])
        core.interpreter(state, env)
        for item in state:
            item.observation.step = step + 1
    result = dict(fixture_id=fixture['fixture_id'], team=fixture['team'], candidate_seat=seat,
                  candidate_sha256=SOURCE_SHA, source_replay_sha256=fixture['source_replay_sha256'],
                  source_opponent_action_sha256=fixture['source_opponent_action_sha256'],
                  correction_sha256=correction_sha, helper_sha256=helper_sha,
                  recorded_shops144=recorded_pair, shops144=list(state[seat].observation.town['unlocked_shops'][:2]),
                  statuses=[s.status for s in state], frames=145, observed_step=144,
                  candidate_telemetry=dict(module.agent.telemetry), candidate_errors=errors(module),
                  prefix_actions_sha256=hashlib.sha256(json.dumps(own_actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
    assert result['statuses'] == ['ACTIVE', 'ACTIVE'] and not result['candidate_errors']
    assert sha(SOURCE) == SOURCE_SHA
    del module, state; gc.collect()
    return result


def key(row):
    return row['fixture_id'], row['candidate_seat']


def main(workers):
    assert sha(TARGETS) == TARGETS_SHA and sha(WINS) == WINS_SHA
    assert sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py') == '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'
    target = json.loads(TARGETS.read_text(encoding='utf-8'))
    wins = json.loads(WINS.read_text(encoding='utf-8'))
    fixtures = target['live_losses'] + target['current_top20'] + wins['fixtures']
    assert len(fixtures) == 104
    correction_sha, helper_sha = sha(HERE / 'COVERAGE_CORRECTION.md'), sha(__file__)
    jobs = [(fixture, seat, correction_sha, helper_sha) for fixture in fixtures for seat in (0, 1)]
    checkpoint = HERE / 'coverage.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    expected = {(f['fixture_id'], seat): f for f, seat, _, _ in jobs}
    done = {key(row) for row in rows}; assert len(done) == len(rows)
    for row in rows:
        fixture = expected[key(row)]
        assert row['candidate_sha256'] == SOURCE_SHA and row['helper_sha256'] == helper_sha and row['correction_sha256'] == correction_sha
        assert row['source_replay_sha256'] == fixture['source_replay_sha256']
        assert row['source_opponent_action_sha256'] == fixture['source_opponent_action_sha256']
    pending = [job for job in jobs if (job[0]['fixture_id'], job[1]) not in done]
    print(f'Coverage prefixes {len(rows)}/208; workers={workers}', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(prefix, job) for job in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    if len(rows) % 8 == 0:
                        print(f'Coverage prefixes {len(rows)}/208', flush=True)
    result = dict(complete=len(rows) == 208, passed=all(r['statuses'] == ['ACTIVE', 'ACTIVE'] and not r['candidate_errors'] for r in rows),
                  source_sha256=SOURCE_SHA, correction_sha256=correction_sha, helper_sha256=helper_sha,
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), prefixes=sorted(rows, key=key))
    with (HERE / 'coverage.json').open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'prefixes'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    with exclusive_run(HERE / 'coverage.lock'):
        main(args.workers)
