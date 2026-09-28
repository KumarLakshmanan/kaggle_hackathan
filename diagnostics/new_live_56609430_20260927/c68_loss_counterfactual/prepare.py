"""Freeze exact live-loss replays and 719-action opponent routes."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments import __version__ as engine_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COHORT = HERE.parent / 'cohort_164140.json'
AGENTS = {
    'c68': ROOT / 'main_before_purchase_iterated_20260927_c68fa46f.py',
    '4ee': ROOT / 'main_uploaded_purchase_iterated_20260927_4eeac9c3.py',
}
EXPECTED = {
    'c68': 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad',
    '4ee': '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    cohort_raw = COHORT.read_bytes()
    cohort = json.loads(cohort_raw)
    assert cohort['complete'] and cohort['submission_id'] == 56609430 and not cohort['failures']
    losses = [g for g in cohort['games'] if g['result'] == 'loss']
    assert len(losses) == 18
    assert all(sha(path.read_bytes()) == EXPECTED[name] for name, path in AGENTS.items())
    routes_dir = HERE / 'routes'
    routes_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for game in losses:
        eid = game['episode_id']
        raw = gzip.decompress(Path(game['replay_path']).read_bytes())
        assert sha(raw) == game['replay_sha256'], eid
        replay = json.loads(raw)
        seat = game['candidate_seat']
        rival_seat = 1 - seat
        assert int(replay['info']['EpisodeId']) == eid
        assert replay['info']['TeamNames'][seat] == 'Lakshmanan R'
        assert replay['info']['TeamNames'][rival_seat] == game['opponent']
        assert int(replay['info']['seed']) == int(game['seed'])
        assert len(replay['steps']) == 720 and replay['statuses'] == ['DONE', 'DONE']
        actions = [frame[rival_seat]['action'] for frame in replay['steps'][1:]]
        assert len(actions) == 719 and all(action is not None for action in actions)
        actions_raw = json.dumps(actions, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8')
        route = dict(actions=actions, metadata=dict(episode_id=eid, source_replay_sha256=game['replay_sha256'],
                                                   source_seat=rival_seat, source_candidate_seat=seat,
                                                   seed=game['seed'], opponent=game['opponent'],
                                                   action_sha256=sha(actions_raw)))
        route_raw = json.dumps(route, separators=(',', ':'), ensure_ascii=False).encode('utf8')
        route_path = routes_dir / f'opponent-{eid}.json.gz'
        assert not route_path.exists(), route_path
        route_path.write_bytes(gzip.compress(route_raw, compresslevel=9))
        assert json.loads(gzip.decompress(route_path.read_bytes())) == route
        rows.append(dict(episode_id=eid, opponent=game['opponent'], live_candidate_seat=seat,
                         seed=int(game['seed']), live_margin=game['margin'],
                         live_own_cash=game['own_cash'], live_opponent_cash=game['opponent_cash'],
                         live_result=game['result'], source_replay_path=game['replay_path'],
                         source_replay_sha256=game['replay_sha256'],
                         route_path=str(route_path.resolve()), route_sha256=sha(route_raw),
                         opponent_action_sha256=sha(actions_raw), opponent_action_count=len(actions)))
    manifest = dict(prepared_at_utc=datetime.now(timezone.utc).isoformat(),
                    selection='All 18 losses from complete 16:41 UTC submission 56609430 live cohort',
                    cohort_path=str(COHORT.resolve()), cohort_sha256=sha(cohort_raw),
                    plan_sha256=sha((HERE / 'PLAN.md').read_bytes()),
                    runner_sha256=sha((HERE / 'run.py').read_bytes()),
                    paired_benchmark_sha256=sha((ROOT / 'paired_benchmark.py').read_bytes()),
                    raw_route_agent_sha256=sha((ROOT / 'raw_route_agent.py').read_bytes()),
                    agent_paths={name: str(path.resolve()) for name, path in AGENTS.items()},
                    agent_sha256=EXPECTED, engine_version=engine_version,
                    expected_episodes=len(rows), expected_games=len(rows) * 4, rows=rows)
    target = HERE / 'manifest.json'
    assert not target.exists()
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(dict(manifest=str(target), losses=len(rows), games=manifest['expected_games'],
                          agent_sha256=EXPECTED), ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
