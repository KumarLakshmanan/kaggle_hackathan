from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'diagnostics/disjoint_upload_20260927/live_0822/episodes.json'
KAGGLE = r'C:/Users/Veeramani Selvaraj/AppData/Roaming/Python/Python314/Scripts/kaggle.exe'
TEAM = 'Lakshmanan R'


def now():
    return datetime.now(timezone.utc).isoformat()


def collect(episode):
    eid = int(episode['id'])
    path = HERE / 'raw' / f'episode-{eid}-replay.json'
    archive = path.with_suffix('.json.gz')
    assert not path.exists() and not archive.exists()
    result = subprocess.run([KAGGLE, 'competitions', 'replay', str(eid), '-p', str(path.parent), '-q'],
                            capture_output=True, text=True, encoding='utf8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'Replay {eid}: {result.stderr[:300]}')
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    replay = json.loads(raw)
    archive.write_bytes(gzip.compress(raw, compresslevel=6))
    assert hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest
    assert path.resolve().parent == (HERE / 'raw').resolve()
    path.unlink()
    info = replay.get('info', {})
    names = info['TeamNames']
    seat = names.index(TEAM)
    last = replay['steps'][-1]
    cash = [x['reward'] for x in last]
    statuses = [x['status'] for x in last]
    active = sum(1 for frame in replay['steps'][1:]
                 if ((frame[seat].get('action') or {}).get('farmer') or ['PASS'])[0] != 'PASS')
    row = dict(episode_id=eid, listing=episode, downloaded_at_utc=now(),
               replay_path=str(archive.resolve()), replay_sha256=digest, source_bytes=len(raw),
               candidate_seat=seat, opponent=names[1-seat], team_names=names,
               rewards=cash, own_cash=cash[seat], opponent_cash=cash[1-seat],
               margin=cash[seat]-cash[1-seat], statuses=statuses, frames=len(replay['steps']),
               candidate_nonpass=active, seed=info.get('seed'),
               module_version=replay.get('module_version'), info=info)
    row['result'] = 'win' if row['margin'] > 0 else 'loss' if row['margin'] < 0 else 'draw'
    (HERE / 'raw' / f'episode-{eid}-receipt.json').write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding='utf8')
    return row


if __name__ == '__main__':
    episodes = json.loads(SOURCE.read_text())
    chosen = sorted([e for e in episodes if 'PUBLIC' in str(e['type']) and str(e['state']).endswith('COMPLETED')],
                    key=lambda e: (e['createTime'], e['id']))
    assert len(chosen) == 13
    assert not (HERE / 'cohort.json').exists()
    (HERE / 'raw').mkdir(exist_ok=True)
    output = dict(started_at_utc=now(), listing=str(SOURCE.resolve()),
                  listing_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  submission_id=56602057, selection='All 13 completed public episodes at 08:22 UTC, no outcome filter',
                  complete=False, games=[])
    def save():
        (HERE / 'cohort.json').write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf8')
    save()
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(collect, e) for e in chosen]):
            row = future.result()
            output['games'].append(row)
            output['games'].sort(key=lambda r: r['listing']['createTime'])
            save()
            print(f"{len(output['games'])}/13 {row['episode_id']} {row['result']} {row['margin']:+} versus {row['opponent']}", flush=True)
    output.update(complete=True, completed_at_utc=now(),
                  wins=sum(g['result']=='win' for g in output['games']),
                  losses=sum(g['result']=='loss' for g in output['games']),
                  draws=sum(g['result']=='draw' for g in output['games']))
    save()
    print(json.dumps({k:v for k,v in output.items() if k != 'games'}), flush=True)
