"""Save a read-only Kaggle snapshot for submission 56609430."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
SUBMISSION = 56609430
TEAM_ID = '16674353'


def now():
    return datetime.now(timezone.utc).isoformat()


def run_json(args):
    process = subprocess.run([KAGGLE, *args, '--format', 'json', '-q'],
                             capture_output=True, text=True, encoding='utf8', errors='replace')
    if process.returncode:
        if args[:2] == ['competitions', 'episodes'] and process.stderr.strip().endswith('No episodes found'):
            return []
        raise RuntimeError(f'{args}: {process.stderr[:1000]}')
    output = process.stdout
    starts = [i for i in (output.find('['), output.find('{')) if i >= 0]
    if not starts:
        raise RuntimeError(f'No JSON body: {args}: {output[:500]}')
    return json.loads(output[min(starts):])


def capture():
    target = HERE / ('snapshot_' + datetime.now(timezone.utc).strftime('%H%M%S'))
    target.mkdir(parents=True, exist_ok=False)
    requests = {
        'submissions': ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'],
        'team_submissions': ['competitions', 'team-submissions', TEAM_ID],
        'episodes': ['competitions', 'episodes', str(SUBMISSION)],
    }
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(run_json, args) for name, args in requests.items()}
        process = subprocess.run([KAGGLE, 'competitions', 'leaderboard', 'kaggriculture',
                                  '-d', '-p', str(target), '-q'],
                                 capture_output=True, text=True, encoding='utf8', errors='replace')
        if process.returncode:
            raise RuntimeError(f'Leaderboard: {process.stderr[:1000]}')
        documents = {name: future.result() for name, future in futures.items()}
    for name, document in documents.items():
        (target / (name + '.json')).write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding='utf8')
    archives = list(target.glob('*.zip'))
    assert len(archives) == 1, archives
    with zipfile.ZipFile(archives[0]) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith('.csv')]
        assert len(names) == 1, names
        raw = archive.read(names[0])
    (target / 'leaderboard.csv').write_bytes(raw)
    board = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    submissions = [row for row in documents['submissions'] if int(row['ref']) == SUBMISSION]
    assert len(submissions) == 1, submissions
    public = [e for e in documents['episodes'] if 'PUBLIC' in str(e.get('type'))]
    validation = [e for e in documents['episodes'] if 'VALIDATION' in str(e.get('type'))]
    summary = dict(checked_at_utc=now(), submission_id=SUBMISSION,
                   submission=submissions[0], our_team=next(r for r in board if r['TeamId'] == TEAM_ID),
                   rank10=next(r for r in board if r['Rank'] == '10'),
                   public_episodes=len(public),
                   completed_public_episodes=sum(str(e['state']).endswith('COMPLETED') for e in public),
                   validation=validation, snapshot_path=str(target.resolve()))
    (target / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    capture()
