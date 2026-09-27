from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.disjoint_live_cash_0929_20260927 import audit as helper


def play(job):
    live,rank,helper_hash=job
    assert hashlib.sha256(Path(helper.__file__).read_bytes()).hexdigest()==helper_hash
    helper.HERE=HERE
    row=helper.audit(live)
    row['snapshot_opponent_rank']=rank
    return row


if __name__=='__main__':
    cohort_path=ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1005.json'
    context_path=ROOT/'diagnostics/disjoint_live_audit_20260927/opponent_context_1005.json'
    cohort=json.loads(cohort_path.read_text());assert cohort['complete'] and len(cohort['games'])==46
    context={r['episode_id']:r for r in json.loads(context_path.read_text())}
    helper_hash=hashlib.sha256(Path(helper.__file__).read_bytes()).hexdigest()
    jobs=[]
    for g in cohort['games']:
        teams=context[g['episode_id']]['matches']
        if len(teams)==1 and int(teams[0]['Rank'])<=100:
            jobs.append((g,int(teams[0]['Rank']),helper_hash))
    assert len(jobs)==4
    target=HERE/'ledger.json';assert not target.exists()
    for name in ('routes','traces'):(HERE/name).mkdir(exist_ok=True)
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,
             selection='All four episodes against teams ranked <=100 in the frozen 10:05 snapshot',
             source_cohort_sha256=hashlib.sha256(cohort_path.read_bytes()).hexdigest(),
             opponent_context_sha256=hashlib.sha256(context_path.read_bytes()).hexdigest(),
             helper_sha256=helper_hash,independent_strength_evidence=False,games=[])
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play,j) for j in jobs]):
            row=future.result();out['games'].append(row);save()
            print(f"{len(out['games'])}/4 {row['opponent']} rank={row['snapshot_opponent_rank']} margin={row['margin']:+} cash/action parity passed",flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat());save()
    for g in out['games']:
        print(g['opponent'],g['margin'],'net-item differences',g['net_item_differences'],
              'atomic',g['atomic_cash_difference'],'unexplained',g['other_cash_difference'],flush=True)
