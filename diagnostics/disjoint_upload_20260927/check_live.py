"""Save an official read-only leaderboard/submission/episode snapshot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json

KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'


if __name__ == '__main__':
    started = datetime.now(timezone.utc)
    target = HERE / ('live_' + started.strftime('%H%M%S'))
    target.mkdir(exist_ok=False)
    requests = {
        'submissions': ['competitions', 'submissions', 'kaggriculture', '--page-size', '3'],
        'team_submissions': ['competitions', 'team-submissions', '16674353'],
        'episodes': ['competitions', 'episodes', '56602057'],
    }
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(_run_json, KAGGLE, args) for name, args in requests.items()}
        response = subprocess.run(
            [KAGGLE, 'competitions', 'leaderboard', 'kaggriculture', '-d', '-p', str(target), '-q'],
            capture_output=True, text=True, encoding='utf8', check=True,
        )
        documents = {name: future.result() for name, future in futures.items()}
    for name, document in documents.items():
        (target / (name + '.json')).write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding='utf8')
    archives = list(target.glob('*.zip'))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        assert len(names) == 1
        csv_bytes = archive.read(names[0])
    (target / 'leaderboard.csv').write_bytes(csv_bytes)
    board = list(csv.DictReader(io.StringIO(csv_bytes.decode('utf-8-sig'))))
    team = next(r for r in board if str(r['TeamId']) == '16674353')
    rank10 = next(r for r in board if str(r['Rank']) == '10')
    submission = next(s for s in documents['submissions'] if int(s['ref']) == 56602057)
    episodes = documents['episodes']
    public = [e for e in episodes if 'PUBLIC' in str(e['type'])]
    summary = dict(
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        our_team=team, rank10=rank10, new_submission=submission,
        public_episodes=len(public),
        completed_public_episodes=sum(str(e['state']).endswith('COMPLETED') for e in public),
        directory=str(target),
    )
    (target / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
