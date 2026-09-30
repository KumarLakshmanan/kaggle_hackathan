from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.stream_replay_io_20260928.fast_game_cached import play


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    prior = ROOT / 'diagnostics/public_90_research_20260928'
    target_path = prior / 'target.json'
    assert sha(target_path) == 'a588a300e8354b59f7edebbbdf74aee937efb3e7bd3c23736f11e1ec4317a7bb'
    pool = json.loads((prior / 'pool.json').read_text(encoding='utf-8'))
    target = json.loads(target_path.read_text(encoding='utf-8'))
    variant = next(v for v in pool['variants'] if v['version'] == 'ICE_CREAM_SHOP_113332529')
    fixture = next(f for f in pool['fixtures']['ICE_CREAM_SHOP'] if f['fixture_id'] == 'live-114288168')
    assert sha(variant['candidate']) == variant['candidate_sha256']
    rows = []
    for seat in (0, 1):
        trace = HERE / ('seat' + str(seat) + '.jsonl.gz')
        assert not trace.exists()
        row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat, trace)
        expected = next(r for r in target['games'] if r['version'] == variant['version'] and r['fixture_id'] == fixture['fixture_id'] and r['candidate_seat'] == seat)
        fields = ('candidate_reward', 'opponent_reward', 'result', 'candidate_telemetry', 'candidate_status', 'opponent_status', 'frames')
        assert all(row[k] == expected[k] for k in fields)
        assert row['margin'] == -21 and not row['candidate_errors']
        last_day = []
        with gzip.open(trace, 'rt', encoding='utf-8') as stream:
            for line in stream:
                state = json.loads(line)
                if state['step'] >= 696:
                    obs = state['observation']
                    farm = obs['farms'][seat]
                    last_day.append(dict(step=state['step'], own_cash=farm['money'],
                        opponent_cash=obs['farms'][1-seat]['money'], farmer=farm['farmer'], hands=farm['hands'],
                        private=obs['private'], action=state['action']))
        rows.append(dict(result=row, trace_sha256=sha(trace), last_day=last_day))
        print('Near-loss diagnostic seat', seat, 'matches -21.', flush=True)
    report = dict(complete=True, exact_reproduction=True, independent_games=0,
                  candidate_sha256=variant['candidate_sha256'], prior_receipt_sha256=sha(target_path),
                  helper_sha256=sha(__file__), plan_sha256=sha(HERE / 'PLAN.md'),
                  cache_helper_sha256=sha(ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py'),
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), seats=rows)
    with (HERE / 'audit.json').open('x', encoding='utf-8') as out:
        json.dump(report, out, indent=2)


if __name__ == '__main__': main()
