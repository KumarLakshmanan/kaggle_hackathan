from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.disjoint_live_cash_0929_20260927 import audit as helper


def play(job):
    live,digest=job
    assert hashlib.sha256(Path(helper.__file__).read_bytes()).hexdigest()==digest
    helper.HERE=HERE
    return helper.audit(live)


if __name__=='__main__':
    old_path=ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1005.json'
    new_path=ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1022.json'
    old=json.loads(old_path.read_text());new=json.loads(new_path.read_text())
    assert old['complete'] and new['complete']
    old_ids={g['episode_id'] for g in old['games']}
    chosen=[g for g in new['games'] if g['episode_id'] not in old_ids]
    assert len(chosen)==5
    target=HERE/'ledger.json';assert not target.exists()
    for name in ('routes','traces'):(HERE/name).mkdir(exist_ok=True)
    digest=hashlib.sha256(Path(helper.__file__).read_bytes()).hexdigest()
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,
             source_cohort_sha256=hashlib.sha256(new_path.read_bytes()).hexdigest(),
             previous_cohort_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),
             helper_sha256=digest,plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             independent_strength_evidence=False,selection='Every five newly listed game from 10:05 to10:22, without outcome filtering',games=[])
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play,(g,digest)) for g in chosen]):
            g=future.result();out['games'].append(g);save()
            print(f"{len(out['games'])}/5 {g['opponent']} {g['margin']:+} exact parity",flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat());save()
    for g in out['games']:
        print(g['opponent'],g['margin'],'net',g['net_item_differences'],'atomic',g['atomic_cash_difference'],
              'own failures',g['failed_purchases']['ours']['counts'],flush=True)
