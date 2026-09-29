"""Read-only public production inventory and exact source predecision prefixes."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
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
from diagnostics.public_90_research_20260928.research import SOURCE, SOURCE_SHA, TARGETS, TARGETS_SHA, sha, read, write, action_hash
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames
from diagnostics.physical_route_rollout_20260928.fast_reactive import load_policy, errors
from diagnostics.local_target_20260928.run_lock import exclusive_run

WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
WINS_SHA = 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'


def summary(farm):
    crops, animals = Counter(), Counter()
    for row in farm['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get('crop'): crops[tile['crop']] += 1
                if tile.get('animal'): animals[tile['animal']] += 1
    return dict(crop_counts=dict(crops), animal_counts=dict(animals), hand_count=len(farm['hands']),
                cash=farm['money'], quadrants=farm['unlocked_quadrants'])


def fixtures():
    assert sha(SOURCE) == SOURCE_SHA and sha(TARGETS) == TARGETS_SHA and sha(WINS) == WINS_SHA
    targets = read(TARGETS)
    result = targets['live_losses'] + targets['current_top20'] + read(WINS)['fixtures']
    assert len(result) == 104 and len({f['fixture_id'] for f in result}) == 104
    return result


def replay(fixture):
    raw = gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == fixture['source_replay_sha256']
    return json.loads(raw)


def recorded():
    rows = []
    for fixture in fixtures():
        data = replay(fixture)
        opponent_seat = fixture.get('source_seat') if fixture['fixture_id'].startswith('top20-') else 1 - fixture['source_candidate_seat']
        assert opponent_seat in (0, 1)
        farms = data['steps'][72][0]['observation']['farms']
        obs = data['steps'][72][1-opponent_seat]['observation']
        rows.append(dict(fixture_id=fixture['fixture_id'], team=fixture['team'], observed_step=72,
                         provenance='Original recorded episode; not a367 matched decision state.',
                         recorded_peer_is_our_baseline=not fixture['fixture_id'].startswith('top20-'),
                         opponent_recorded_seat=opponent_seat,
                         rival_public=summary(farms[opponent_seat]), recorded_peer_public=summary(farms[1-opponent_seat]),
                         rival_farm=farms[opponent_seat], recorded_peer_farm=farms[1-opponent_seat],
                         recorded_peer_private=obs['private'], market=obs['market'], revealed_shops=obs['town']['unlocked_shops'],
                         source_replay_path=fixture['source_replay_path'], source_replay_sha256=fixture['source_replay_sha256']))
    write(HERE / 'recorded_features72.json', dict(complete=True, fixture_count=104, helper_sha256=sha(__file__),
          plan_sha256=sha(HERE / 'FEATURE_PLAN.md'), created_at_utc=datetime.now(timezone.utc).isoformat(), rows=rows))
    print('Recorded-public inventory:104 fixtures; explicitly not matched367 states.', flush=True)


def prefix(fixture, seat):
    data = replay(fixture); state = state_from_frames(data['steps'][0]); cfg = dict(data['configuration']); cfg['seed'] = None
    env = Box(configuration=Box(**cfg), info={'seed': int(fixture['seed'])}, done=False)
    del data; gc.collect()
    tape = json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    assert len(tape) == 719 and fixture['source_opponent_action_sha256'] in {
        hashlib.sha256(json.dumps(tape, sort_keys=order, separators=(',', ':')).encode()).hexdigest() for order in (False, True)}
    module = load_policy(SOURCE, 'early_public_feature_source'); actions = []
    for step in range(72):
        obs = copy.deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))
        action = module.agent(obs, cfg); actions.append(copy.deepcopy(action))
        state[seat].action = action; state[1-seat].action = copy.deepcopy(tape[step])
        core.interpreter(state, env)
        for item in state: item.observation.step = step + 1
    obs = copy.deepcopy(state[seat].observation)
    row = dict(fixture_id=fixture['fixture_id'], team=fixture['team'], candidate_seat=seat,
               observed_step=72, frames=73, candidate_sha256=SOURCE_SHA,
               own_public=summary(obs['farms'][seat]), rival_public=summary(obs['farms'][1-seat]),
               own_farm=obs['farms'][seat], rival_farm=obs['farms'][1-seat], own_private=obs['private'],
               market=obs['market'], revealed_shops=obs['town']['unlocked_shops'], statuses=[s.status for s in state],
               candidate_errors=errors(module), candidate_telemetry=dict(module.agent.telemetry),
               prefix_actions_sha256=action_hash(actions), source_replay_sha256=fixture['source_replay_sha256'],
               source_opponent_action_sha256=fixture['source_opponent_action_sha256'], seed_visible_to_policy=None,
               helper_sha256=sha(__file__), plan_sha256=sha(HERE / 'FEATURE_PLAN.md'))
    assert row['statuses'] == ['ACTIVE', 'ACTIVE'] and not row['candidate_errors']
    assert sha(SOURCE) == SOURCE_SHA
    del module, state; gc.collect()
    return row


def matched():
    fs = fixtures(); expected = {(f['fixture_id'], seat): f for f in fs for seat in (0, 1)}
    ledger = HERE / 'matched_features72.jsonl'; destination = HERE / 'matched_features72.json'; assert not destination.exists()
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        assert (row['fixture_id'], row['candidate_seat']) in expected
        assert row['helper_sha256'] == sha(__file__) and row['candidate_sha256'] == SOURCE_SHA
        assert row['plan_sha256'] == sha(HERE / 'FEATURE_PLAN.md')
    with ledger.open('a', encoding='utf-8') as output:
        for (fid, seat), fixture in expected.items():
            if (fid, seat) in done: continue
            row = prefix(fixture, seat); rows.append(row)
            output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
            if len(rows) % 8 == 0: print(f'Matched feature prefixes {len(rows)}/208', flush=True)
    assert len(rows) == 208
    write(destination, dict(complete=True, source_sha256=SOURCE_SHA, prefix_count=208,
          helper_sha256=sha(__file__), plan_sha256=sha(HERE / 'FEATURE_PLAN.md'),
          target_manifest_sha256=TARGETS_SHA, public_win_manifest_sha256=WINS_SHA,
          core_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'),
          created_at_utc=datetime.now(timezone.utc).isoformat(), rows=rows))
    print('Matched feature inventory:208 complete prefixes; no terminal outcomes.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['recorded', 'matched']); mode = parser.parse_args().mode
    with exclusive_run(HERE / ('features_' + mode + '.lock')):
        recorded() if mode == 'recorded' else matched()
