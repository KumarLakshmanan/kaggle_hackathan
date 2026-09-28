"""Run the two frozen agents against every saved live-loss tape in both seats."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def key(row):
    return (row['episode_id'], row['version'], row['tested_seat'])


def play(job):
    source, version, tested_seat, agent_path, agent_sha = job
    assert sha(Path(agent_path).read_bytes()) == agent_sha
    route_path = Path(source['route_path'])
    route_raw = gzip.decompress(route_path.read_bytes())
    assert sha(route_raw) == source['route_sha256']
    route = json.loads(route_raw)
    assert len(route['actions']) == source['opponent_action_count'] == 719
    assert route['metadata']['episode_id'] == source['episode_id']
    raw = json.dumps(route['actions'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    assert sha(raw) == source['opponent_action_sha256']
    result = run_game(candidate=agent_path, opponent='rawroute:' + str(route_path),
                      seed=source['seed'], candidate_seat=tested_seat, debug=False,
                      capture_step=None, candidate_overrides={})
    return dict(episode_id=source['episode_id'], opponent=source['opponent'], seed=source['seed'],
                version=version, tested_seat=tested_seat,
                live_candidate_seat=source['live_candidate_seat'],
                original_seat=(tested_seat == source['live_candidate_seat']),
                live_own_cash=source['live_own_cash'], live_opponent_cash=source['live_opponent_cash'],
                live_margin=source['live_margin'], source_replay_sha256=source['source_replay_sha256'],
                route_sha256=source['route_sha256'], opponent_action_sha256=source['opponent_action_sha256'],
                agent_sha256=agent_sha, candidate_reward=result['candidate_reward'],
                opponent_reward=result['opponent_reward'], margin=result['margin'],
                result=result['result'], candidate_status=result['candidate_status'],
                opponent_status=result['opponent_status'], frames=result['frames'],
                wall_seconds=result['wall_seconds'], candidate_timing=result['candidate_timing'])


def main():
    manifest_path = HERE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    assert sha((HERE / 'PLAN.md').read_bytes()) == manifest['plan_sha256']
    assert sha(Path(__file__).read_bytes()) == manifest['runner_sha256']
    assert sha((ROOT / 'paired_benchmark.py').read_bytes()) == manifest['paired_benchmark_sha256']
    assert sha((ROOT / 'raw_route_agent.py').read_bytes()) == manifest['raw_route_agent_sha256']
    jobs = [(source, version, seat, manifest['agent_paths'][version], manifest['agent_sha256'][version])
            for source in manifest['rows'] for version in ('4ee', 'c68') for seat in (0, 1)]
    assert len(jobs) == manifest['expected_games'] == 72
    target = HERE / 'results.json'
    assert not target.exists()
    out = dict(started_at_utc=now(), manifest_path=str(manifest_path.resolve()),
               manifest_sha256=sha(manifest_path.read_bytes()), expected_games=len(jobs),
               workers=4, complete=False, games=[], errors=[])
    def save():
        target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=out['workers']) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            source, version, seat, _, _ = futures[future]
            try:
                row = future.result()
                out['games'].append(row)
                out['games'].sort(key=key)
                if len(out['games']) % 4 == 0 or len(out['games']) == len(jobs):
                    print(json.dumps(dict(done=len(out['games']), total=len(jobs),
                                          episode_id=row['episode_id'], version=row['version'],
                                          tested_seat=row['tested_seat'], result=row['result'],
                                          margin=row['margin'])), flush=True)
            except Exception as exc:
                out['errors'].append(dict(episode_id=source['episode_id'], version=version,
                                          tested_seat=seat, error=repr(exc), failed_at_utc=now()))
                print(json.dumps(out['errors'][-1], ensure_ascii=True), flush=True)
            save()
    out['completed_at_utc'] = now()
    out['complete'] = len(out['games']) == len(jobs) and not out['errors']
    out['all_done_720'] = all(g['candidate_status'] == g['opponent_status'] == 'DONE'
                              and g['frames'] == 720 for g in out['games'])
    original_new = [g for g in out['games'] if g['version'] == '4ee' and g['original_seat']]
    out['original_seat_cash_parity'] = (
        len(original_new) == 18
        and all(g['candidate_reward'] == g['live_own_cash']
                and g['opponent_reward'] == g['live_opponent_cash']
                and g['margin'] == g['live_margin'] for g in original_new))
    out['original_seat_cash_parity_failures'] = [g['episode_id'] for g in original_new
                                                if g['candidate_reward'] != g['live_own_cash']
                                                or g['opponent_reward'] != g['live_opponent_cash']
                                                or g['margin'] != g['live_margin']]
    save()
    print(json.dumps(dict(complete=out['complete'], games=len(out['games']),
                          errors=len(out['errors']), all_done_720=out['all_done_720'],
                          original_seat_cash_parity=out['original_seat_cash_parity'],
                          original_seat_cash_parity_failures=out['original_seat_cash_parity_failures'])), flush=True)


if __name__ == '__main__':
    main()
