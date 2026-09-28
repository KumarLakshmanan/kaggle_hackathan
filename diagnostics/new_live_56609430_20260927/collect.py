"""Download every completed public replay from an immutable saved listing."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
SUBMISSION = 56609430
TEAM = 'Lakshmanan R'


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, document):
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding='utf8')


def collect_one(episode, raw_dir, rank_by_name):
    eid = int(episode['id'])
    path = raw_dir / f'episode-{eid}-replay.json'
    archive = raw_dir / f'episode-{eid}-replay.json.gz'
    receipt = raw_dir / f'episode-{eid}-receipt.json'
    assert not path.exists() and not archive.exists() and not receipt.exists(), eid
    for attempt in range(3):
        process = subprocess.run([KAGGLE, 'competitions', 'replay', str(eid), '-p', str(raw_dir), '-q'],
                                 capture_output=True, text=True, encoding='utf8', errors='replace')
        if process.returncode == 0 and path.exists():
            break
        if attempt == 2:
            raise RuntimeError(f'{eid}: download failed after 3 attempts: {process.stderr[:500]}')
        time.sleep(2 * (attempt + 1))
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    replay = json.loads(raw)
    archive.write_bytes(gzip.compress(raw, compresslevel=6))
    assert hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest
    path.unlink()
    info = replay['info']
    names = info['TeamNames']
    assert len(names) == 2 and names.count(TEAM) == 1, (eid, names)
    seat = names.index(TEAM)
    opponent = names[1 - seat]
    frames = replay['steps']
    last = frames[-1]
    statuses = [player['status'] for player in last]
    rewards = [player['reward'] for player in last]
    action_counts = [sum(frame[player].get('action') is not None for frame in frames[1:]) for player in (0, 1)]
    nonpass = sum(((frame[seat].get('action') or {}).get('farmer') or ['PASS'])[0] != 'PASS'
                  for frame in frames[1:])
    margin = rewards[seat] - rewards[1 - seat]
    ranks = rank_by_name.get(opponent, [])
    row = dict(episode_id=eid, listing=episode, downloaded_at_utc=now(),
               replay_path=str(archive.resolve()), replay_sha256=digest, source_bytes=len(raw),
               candidate_seat=seat, opponent=opponent, opponent_snapshot_ranks=ranks,
               team_names=names, rewards=rewards, own_cash=rewards[seat], opponent_cash=rewards[1-seat],
               margin=margin, statuses=statuses, frames=len(frames), action_counts=action_counts,
               candidate_nonpass=nonpass, seed=info.get('seed'),
               module_version=replay.get('module_version'), result='win' if margin > 0 else 'loss' if margin < 0 else 'draw')
    assert len(frames) == 720 and statuses == ['DONE', 'DONE'] and action_counts == [719, 719], (eid, statuses, action_counts)
    save(receipt, row)
    return row


def main(snapshot):
    listing_path = snapshot / 'episodes.json'
    listing_bytes = listing_path.read_bytes()
    episodes = json.loads(listing_bytes)
    chosen = sorted((e for e in episodes if 'PUBLIC' in str(e['type'])
                     and str(e['state']).endswith('COMPLETED')),
                    key=lambda e: (e['createTime'], e['id']))
    validations = sorted((e for e in episodes if 'VALIDATION' in str(e['type'])
                          and str(e['state']).endswith('COMPLETED')),
                         key=lambda e: (e['createTime'], e['id']))
    with (snapshot / 'leaderboard.csv').open(encoding='utf-8-sig', newline='') as stream:
        board = list(csv.DictReader(stream))
    rank_by_name = {}
    for team in board:
        rank_by_name.setdefault(team['TeamName'], []).append(dict(rank=team['Rank'], team_id=team['TeamId'],
                                                                  score=team['Score']))
    raw_dir = HERE / 'raw'
    raw_dir.mkdir(exist_ok=True)
    target = HERE / ('cohort_' + snapshot.name.replace('snapshot_', '') + '.json')
    assert not target.exists()
    out = dict(started_at_utc=now(), submission_id=SUBMISSION, snapshot_path=str(snapshot.resolve()),
               listing_path=str(listing_path.resolve()), listing_sha256=hashlib.sha256(listing_bytes).hexdigest(),
               selection=f'All {len(chosen)} completed public episodes in saved official listing; no outcome filter',
               expected_public_ids=[int(e['id']) for e in chosen], expected_validation_ids=[int(e['id']) for e in validations],
               complete=False, games=[], validation=[], failures=[])
    save(target, out)
    work = [('public', e) for e in chosen] + [('validation', e) for e in validations]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(collect_one, e, raw_dir, rank_by_name): (kind, e) for kind, e in work}
        for future in as_completed(futures):
            kind, episode = futures[future]
            try:
                row = future.result()
                out['games' if kind == 'public' else 'validation'].append(row)
                out['games' if kind == 'public' else 'validation'].sort(key=lambda r: (r['listing']['createTime'], r['episode_id']))
                print(f"{kind} {len(out['games'])}/{len(chosen)} {row['episode_id']} {row['result']} {row['margin']:+} vs {row['opponent']}", flush=True)
            except Exception as exc:
                failure = dict(kind=kind, episode_id=int(episode['id']), error=repr(exc), failed_at_utc=now(),
                               expected_replay_path=str((raw_dir / f"episode-{episode['id']}-replay.json.gz").resolve()))
                out['failures'].append(failure)
                print(f"FAILED {kind} {episode['id']}: {exc}", flush=True)
            save(target, out)
    out.update(completed_at_utc=now(),
               complete=(len(out['games']) == len(chosen) and len(out['validation']) == len(validations)
                         and not out['failures']),
               wins=sum(g['result'] == 'win' for g in out['games']),
               losses=sum(g['result'] == 'loss' for g in out['games']),
               draws=sum(g['result'] == 'draw' for g in out['games']),
               all_done_720_719=all(g['statuses'] == ['DONE', 'DONE'] and g['frames'] == 720
                                    and g['action_counts'] == [719, 719] for g in out['games'] + out['validation']))
    save(target, out)
    print(json.dumps({k: v for k, v in out.items() if k not in ('games', 'validation')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
