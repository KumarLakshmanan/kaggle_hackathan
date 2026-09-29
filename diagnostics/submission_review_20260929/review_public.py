"""Read the uploaded a44 public games for the user-requested upload review."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
CLI = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
TEAM = 'Lakshmanan R'


def inspect(episode):
    folder = HERE / ('episode_' + str(episode['id']))
    folder.mkdir(exist_ok=True)
    paths = list(folder.glob('*.json'))
    if not paths:
        run = subprocess.run([CLI, 'competitions', 'replay', str(episode['id']),
                              '-p', str(folder), '-q'], capture_output=True,
                             text=True, encoding='utf-8', errors='replace', timeout=120)
        if run.returncode:
            raise RuntimeError(f"Replay {episode['id']} download failed: {run.stderr[-500:]}")
        paths = list(folder.glob('*.json'))
    assert len(paths) == 1
    path = paths[0]
    replay = json.loads(path.read_text(encoding='utf-8'))
    names = replay['info']['TeamNames']
    assert names.count(TEAM) == 1, names
    seat = names.index(TEAM)
    steps = replay['steps']
    own, other = steps[-1][seat], steps[-1][1-seat]
    cash, rival = float(own.get('reward') or 0), float(other.get('reward') or 0)
    bad = [(i, state[seat].get('status')) for i, state in enumerate(steps)
           if state[seat].get('status') in ('ERROR', 'TIMEOUT', 'INVALID')]
    budgets = [state[seat].get('observation', {}).get('remainingOverageTime')
               for state in steps]
    budgets = [float(x) for x in budgets if x is not None]
    return {'episode_id': episode['id'], 'created_at': episode['createTime'],
            'replay': str(path), 'replay_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'seat': seat, 'opponent': names[1-seat], 'frames': len(steps),
            'own_status': own.get('status'), 'rival_status': other.get('status'),
            'own_reward': cash, 'rival_reward': rival, 'margin': cash-rival,
            'result': 'win' if cash > rival else 'loss' if cash < rival else 'draw',
            'first_bad_status': bad[0] if bad else None,
            'minimum_remaining_overage': min(budgets) if budgets else None,
            'engine_version': replay.get('module_version')}


if __name__ == '__main__':
    listing = json.loads((HERE / 'a44_episodes_20260929.json').read_text())
    episodes = [x for x in listing['episodes'] if str(x['type']).endswith('PUBLIC')]
    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(inspect, episode) for episode in episodes]
        for future in as_completed(pending):
            rows.append(future.result())
            print(f'Public replay review {len(rows)}/{len(episodes)}', flush=True)
    rows.sort(key=lambda r: (r['created_at'], r['episode_id']))
    receipt = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
               'submission_id': 56649310, 'candidate_sha256':
               'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f',
               'all_listed_public_episodes_included': len(rows) == len(episodes),
               'game_count': len(rows), 'wdl': dict(Counter(r['result'] for r in rows)),
               'bad_status_game_count': sum(bool(r['first_bad_status']) for r in rows),
               'games': rows}
    with (HERE / 'public_cohort_review.json').open('x', encoding='utf-8') as out:
        json.dump(receipt, out, ensure_ascii=True, indent=2)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'games'}, indent=2))
    print('Worst margins:', json.dumps(sorted(rows, key=lambda r: r['margin'])[:5], ensure_ascii=True))
