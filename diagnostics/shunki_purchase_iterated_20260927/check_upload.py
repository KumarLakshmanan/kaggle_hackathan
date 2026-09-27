"""Read-only official status and leaderboard snapshot for the new upload."""
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
from diagnostics.shunki_purchase_iterated_20260927.promote_upload import KAGGLE

def request(args):
    try:
        return _run_json(KAGGLE,args)
    except RuntimeError as exc:
        if args[:2] == ['competitions','episodes'] and str(exc).strip().endswith('No episodes found'):
            return []
        raise

if __name__ == '__main__':
    receipt_path = HERE / 'promotion_receipt.json'
    receipt = json.loads(receipt_path.read_text())
    submission = int(receipt['submission_id'])
    target = HERE / ('live_' + datetime.now(timezone.utc).strftime('%H%M%S'))
    target.mkdir(exist_ok=False)
    requests = {'submissions':['competitions','submissions','kaggriculture','--page-size','5'],
                'team_submissions':['competitions','team-submissions','16674353'],
                'episodes':['competitions','episodes',str(submission)]}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name:pool.submit(request,args) for name,args in requests.items()}
        subprocess.run([KAGGLE,'competitions','leaderboard','kaggriculture','-d','-p',str(target),'-q'],
                       capture_output=True,text=True,encoding='utf8',check=True)
        data = {name:future.result() for name,future in futures.items()}
    for name, document in data.items():
        (target/(name+'.json')).write_text(json.dumps(document,indent=2,ensure_ascii=False),encoding='utf8')
    archives = list(target.glob('*.zip'))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith('.csv')]
        assert len(names) == 1
        raw = archive.read(names[0])
    (target/'leaderboard.csv').write_bytes(raw)
    board = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    current = next(row for row in data['submissions'] if int(row['ref']) == submission)
    validation = [e for e in data['episodes'] if 'VALIDATION' in str(e['type'])]
    out = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), directory=str(target),
               submission=current, validation=validation,
               our_team=next(row for row in board if str(row['TeamId']) == '16674353'),
               rank10=next(row for row in board if str(row['Rank']) == '10'),
               completed_public_episodes=sum('PUBLIC' in str(e['type']) and str(e['state']).endswith('COMPLETED') for e in data['episodes']))
    (target/'summary.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    receipt.update(kaggle_submission=current, latest_status_snapshot=str(target/'summary.json'))
    if len(validation) == 1:
        receipt['validation_episode_id'] = int(validation[0]['id'])
    receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(json.dumps(out,indent=2,ensure_ascii=False),flush=True)
