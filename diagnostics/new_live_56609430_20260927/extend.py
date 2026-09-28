"""Append newly completed games from a later official listing, without changing the first cohort."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

from collect import collect_one, save

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def main(previous_path, snapshot):
    previous = json.loads(previous_path.read_text(encoding='utf8'))
    assert previous['complete'] and not previous['failures']
    listing_path = snapshot / 'episodes.json'
    raw = listing_path.read_bytes()
    episodes = json.loads(raw)
    public = sorted((e for e in episodes if 'PUBLIC' in str(e['type'])
                     and str(e['state']).endswith('COMPLETED')),
                    key=lambda e: (e['createTime'], e['id']))
    public_ids = {int(e['id']) for e in public}
    old_ids = {g['episode_id'] for g in previous['games']}
    assert old_ids <= public_ids, sorted(old_ids - public_ids)
    for row in previous['games'] + previous['validation']:
        archive = Path(row['replay_path'])
        assert hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == row['replay_sha256'], row['episode_id']
    with (snapshot / 'leaderboard.csv').open(encoding='utf-8-sig', newline='') as stream:
        board = list(csv.DictReader(stream))
    rank_by_name = {}
    for team in board:
        rank_by_name.setdefault(team['TeamName'], []).append(dict(rank=team['Rank'], team_id=team['TeamId'],
                                                                  score=team['Score']))
    new = [e for e in public if int(e['id']) not in old_ids]
    label = snapshot.name.replace('snapshot_', '')
    delta_path = HERE / f'delta_{label}.json'
    cohort_path = HERE / f'cohort_{label}.json'
    assert not delta_path.exists() and not cohort_path.exists()
    out = dict(started_at_utc=now(), submission_id=56609430, previous_cohort_path=str(previous_path),
               snapshot_path=str(snapshot.resolve()), listing_path=str(listing_path.resolve()),
               listing_sha256=hashlib.sha256(raw).hexdigest(), previous_public_count=len(old_ids),
               expected_new_ids=[int(e['id']) for e in new], complete=False, games=[], failures=[])
    save(delta_path, out)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(collect_one, e, HERE / 'raw', rank_by_name): e for e in new}
        for future in as_completed(futures):
            episode = futures[future]
            try:
                row = future.result()
                out['games'].append(row)
                out['games'].sort(key=lambda r: (r['listing']['createTime'], r['episode_id']))
                print(json.dumps(dict(episode_id=row['episode_id'], result=row['result'],
                                      margin=row['margin'], opponent=row['opponent']), ensure_ascii=True), flush=True)
            except Exception as exc:
                out['failures'].append(dict(episode_id=int(episode['id']), error=repr(exc), failed_at_utc=now(),
                                            expected_replay_path=str((HERE / 'raw' / f"episode-{episode['id']}-replay.json.gz").resolve())))
            save(delta_path, out)
    out.update(completed_at_utc=now(), complete=(len(out['games']) == len(new) and not out['failures']))
    save(delta_path, out)
    combined = dict(previous)
    combined.update(snapshot_path=str(snapshot.resolve()), listing_path=str(listing_path.resolve()),
                    listing_sha256=hashlib.sha256(raw).hexdigest(),
                    selection=f'All {len(public)} completed public episodes in saved official listing; no outcome filter',
                    expected_public_ids=[int(e['id']) for e in public],
                    extended_from=str(previous_path.resolve()), delta_path=str(delta_path.resolve()),
                    completed_at_utc=now(), complete=out['complete'], failures=out['failures'])
    combined['games'] = sorted(previous['games'] + out['games'], key=lambda r: (r['listing']['createTime'], r['episode_id']))
    combined['wins'] = sum(g['result'] == 'win' for g in combined['games'])
    combined['losses'] = sum(g['result'] == 'loss' for g in combined['games'])
    combined['draws'] = sum(g['result'] == 'draw' for g in combined['games'])
    combined['all_done_720_719'] = all(g['statuses'] == ['DONE', 'DONE'] and g['frames'] == 720
                                       and g['action_counts'] == [719, 719] for g in combined['games'] + combined['validation'])
    assert set(g['episode_id'] for g in combined['games']) == public_ids
    save(cohort_path, combined)
    print(json.dumps(dict(snapshot=snapshot.name, new=len(new), total=len(combined['games']),
                          wins=combined['wins'], losses=combined['losses'], draws=combined['draws'],
                          failures=out['failures']), ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
