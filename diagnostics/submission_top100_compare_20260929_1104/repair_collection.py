"""Retry only the five failed frozen top-100 rows; keep all initial evidence."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

from collect import collect

HERE = Path(__file__).resolve().parent


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def retry(team):
    attempts = []
    for index in range(3):
        row = collect(team)
        attempts.append({'attempt': index + 1,
                         'error': row.get('error'),
                         'unavailable': row.get('unavailable'),
                         'episode_id': row.get('episode_id')})
        if 'action_sha256' in row:
            return row, attempts
        if index < 2:
            time.sleep(2 * (index + 1))
    return row, attempts


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    manifest_path = HERE / 'manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert old['complete'] and len(old['rows']) == 100 and old['eligible'] == 95
    failing = {r['rank']: r for r in old['rows'] if 'action_sha256' not in r}
    assert len(failing) == 5
    shutil.copyfile(manifest_path, HERE / 'manifest_initial.json')
    shutil.copyfile(HERE / 'routes/summary.json', HERE / 'routes/summary_initial.json')
    teams = json.loads((HERE / 'top100_teams.json').read_text(encoding='utf-8'))
    selected = [team for team in teams if team['rank'] in failing]
    repair = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'frozen_ranks': sorted(failing), 'attempts': []}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(retry, team): team for team in selected}
        for future in as_completed(futures):
            team = futures[future]
            row, attempts = future.result()
            assert row['rank'] == team['rank']
            old['rows'] = [r for r in old['rows'] if r['rank'] != row['rank']] + [row]
            old['rows'].sort(key=lambda r: r['rank'])
            repair['attempts'].append({'rank': row['rank'], 'team': row['team'],
                                       'attempts': attempts,
                                       'eligible': 'action_sha256' in row})
            print(f"rank={row['rank']} {row['team']} " +
                  ('recovered' if 'action_sha256' in row else 'unavailable'),
                  flush=True)
    eligible = [r for r in old['rows'] if 'action_sha256' in r]
    old.update(eligible=len(eligible), unique_episodes=len({r['episode_id'] for r in eligible}),
               repaired_at_utc=datetime.now(timezone.utc).isoformat(),
               initial_manifest='manifest_initial.json')
    write(manifest_path, old)
    write(HERE / 'routes/summary.json', eligible)
    repair.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  eligible=len(eligible), missing_ranks=sorted({r['rank'] for r in old['rows']
                                                                if 'action_sha256' not in r}))
    write(HERE / 'repair_receipt.json', repair)
    print(f"COMPLETE eligible={len(eligible)}/100 missing={repair['missing_ranks']}", flush=True)
