"""Finite six-game timing diagnostic, never an independent qualification."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, data):
    with Path(p).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def prepare():
    prior = ROOT / 'diagnostics/public_90_research_20260928'
    pool = read(prior / 'pool.json')
    assert sha(prior / 'target.json') == 'a588a300e8354b59f7edebbbdf74aee937efb3e7bd3c23736f11e1ec4317a7bb'
    source = next(v for v in pool['variants'] if v['version'] == 'ICE_CREAM_SHOP_113332529')
    assert sha(source['candidate']) == source['candidate_sha256']
    fixture = next(f for f in pool['fixtures']['ICE_CREAM_SHOP'] if f['fixture_id'] == 'live-114288168')
    controls = [r for r in read(prior / 'target.json')['games'] if r['version'] == source['version'] and r['fixture_id'] == fixture['fixture_id']]
    assert len(controls) == 2 and all(r['margin'] == -21 for r in controls)
    variants = []
    for horizon in (18, 12, 6):
        path = HERE / ('candidate_' + str(horizon) + '.py')
        layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('HORIZON_VALUE', str(horizon))
        blob = Path(source['candidate']).read_bytes() + b'\n' + layer.encode('utf-8')
        compile(blob, str(path), 'exec')
        with path.open('xb') as stream: stream.write(blob)
        variants.append(dict(horizon=horizon, candidate=str(path), candidate_sha256=sha(path)))
    cached = ROOT / 'diagnostics/stream_replay_io_20260928'
    paths = [Path(__file__), HERE / 'PLAN.md', HERE / 'layer.py', Path(source['candidate']),
             prior / 'target.json', prior / 'pool.json', cached / 'fast_game_cached.py',
             cached / 'cached_input.py', cached / 'initial_states.json', cached / 'cached_helper_parity.json',
             ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py']
    write(HERE / 'pool.json', dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
          fixture=fixture, controls=controls, variants=variants,
          bindings={str(p): sha(p) for p in paths}, planned_games=6))
    print('Frozen three horizons, six games.', flush=True)


def run():
    pool = read(HERE / 'pool.json')
    assert all(sha(p) == h for p, h in pool['bindings'].items())
    rows = []
    for variant in pool['variants']:
        for seat in (0, 1):
            trace = HERE / ('h' + str(variant['horizon']) + '_seat' + str(seat) + '.jsonl.gz')
            assert not trace.exists()
            row = play(pool['fixture'], variant['candidate'], variant['candidate_sha256'], seat, trace)
            row.update(horizon=variant['horizon'], trace_sha256=sha(trace), pool_sha256=sha(HERE / 'pool.json'))
            assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
            assert not row['candidate_errors'] and row['candidate_telemetry']['terminal_sale_turns'] > 0
            control = next(c for c in pool['controls'] if c['candidate_seat'] == seat)
            row['delta_own'] = row['candidate_reward'] - control['candidate_reward']
            row['delta_rival'] = row['opponent_reward'] - control['opponent_reward']
            row['delta_margin'] = row['margin'] - control['margin']
            rows.append(row)
            print('Timing', len(rows), '/6', variant['horizon'], seat, row['margin'], flush=True)
    eligible = []
    for variant in pool['variants']:
        pair = [r for r in rows if r['horizon'] == variant['horizon']]
        if all(r['result'] == 'win' for r in pair):
            eligible.append((min(r['margin'] for r in pair), sum(r['margin'] for r in pair), -variant['horizon'], variant))
    selected = max(eligible, key=lambda x: x[:3])[-1] if eligible else None
    write(HERE / 'screen.json', dict(complete=True, clean=True, games=rows, game_count=6,
          selected=selected, passed=bool(selected), pool_sha256=sha(HERE / 'pool.json'),
          completed_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Advance to affected controls:', bool(selected), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare', 'run'))
    args = parser.parse_args()
    if args.phase == 'prepare': prepare()
    else:
        with exclusive_run(HERE / 'screen.lock'): run()
