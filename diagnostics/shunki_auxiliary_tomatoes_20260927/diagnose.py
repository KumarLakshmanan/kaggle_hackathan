from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from trace_paired_game_events import run
from diagnostics.live_refresh_56530281_20260926.cash_ledger_close import ledger


def diagnose(job):
    candidate,digest,record,expected,oldrow=job
    assert hashlib.sha256(Path(candidate).read_bytes()).hexdigest()==digest
    seat=record['original_seat']
    t=run(candidate,'rawroute:'+record['route'],record['seed'],seat)
    assert (t['candidate_reward'],t['opponent_reward'])==(expected['candidate_reward'],expected['opponent_reward'])
    raw=json.dumps(t,separators=(',',':'),ensure_ascii=False).encode()
    path=HERE/'diagnosis_traces'/f"{record['episode_id']}.json.gz";path.write_bytes(gzip.compress(raw))
    oldraw=gzip.decompress(Path(oldrow['trace_path']).read_bytes())
    assert hashlib.sha256(oldraw).hexdigest()==oldrow['trace_sha256']
    oldtrace=json.loads(oldraw)
    comparisons={}
    for p,label in ((seat,'ours'),(1-seat,'rival')):
        before=ledger(oldtrace,p);after=ledger(t,p)
        assert before['other_cash']==after['other_cash']==0
        items=set(before['net_market_by_item'])|set(after['net_market_by_item'])
        comparisons[label]=dict(before=before,after=after,cash_delta=after['final']-before['final'],
                                 net_item_deltas={i:after['net_market_by_item'].get(i,0)-before['net_market_by_item'].get(i,0) for i in sorted(items)},
                                 atomic_delta=sum(after['atomic_cash'].values())-sum(before['atomic_cash'].values()))
    relative=comparisons['ours']['cash_delta']-comparisons['rival']['cash_delta']
    assert relative==expected['margin']-oldrow['margin']
    return dict(episode_id=record['episode_id'],opponent=record['opponent'],seat=seat,
                old_margin=oldrow['margin'],new_margin=expected['margin'],paired_margin_delta=relative,
                both_cash_parity=True,ledgers=comparisons,
                old_final_shops=oldtrace['traces'][seat][-1]['observation']['town']['unlocked_shops'],
                new_final_shops=t['traces'][seat][-1]['observation']['town']['unlocked_shops'],
                trace_path=str(path),trace_sha256=hashlib.sha256(raw).hexdigest())


if __name__=='__main__':
    m=json.loads((HERE/'build_manifest.json').read_text())
    d=json.loads((HERE/'development.json').read_text());assert d['complete'] and not d['passed']
    olds={g['episode_id']:g for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927')
          for g in json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text())['games']}
    jobs=[]
    for record in d['records']:
        if record['episode_id'] not in d['activated_pairs']:continue
        expected=next(g for g in d['games'] if g['version']=='new' and g['episode_id']==record['episode_id'] and g['candidate_seat']==record['original_seat'])
        jobs.append((m['candidate'],m['candidate_sha256'],record,expected,olds[record['episode_id']]))
    assert len(jobs)==3
    (HERE/'diagnosis_traces').mkdir(exist_ok=True)
    target=HERE/'diagnosis.json';assert not target.exists()
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,candidate_sha256=m['candidate_sha256'],
             plan_sha256=hashlib.sha256((HERE/'DIAGNOSIS_PLAN.md').read_bytes()).hexdigest(),games=[])
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(diagnose,j) for j in jobs]):
            g=future.result();out['games'].append(g);save()
            print(g['opponent'],'paired change',g['paired_margin_delta'],'own',g['ledgers']['ours']['cash_delta'],'rival',g['ledgers']['rival']['cash_delta'],flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat());save()
