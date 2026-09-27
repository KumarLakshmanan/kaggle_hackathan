from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from paired_benchmark import run_game

FILES={
    'c68':('main_uploaded_disjoint_integrated_20260927_c68fa46f.py','c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'),
    'purchase':('main_candidate_purchase_queue_20260927_43d6f448.py','43d6f44806f7ce7204aa92180584f96c894653d6cb36bb9442a0425e8fbef176'),
    'funding':('main_candidate_planned_funding_20260927_31ce35e9.py','31ce35e99548b6214cae174463f510a187bb2ca73f6b77da736d660eac753a25'),
}


def play(job):
    name,seat,seed=job
    path,digest=FILES[name];p=ROOT/path
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    g=run_game(str(p),'rawroute:'+str(HERE/'opponent.json.gz'),seed,seat,False,144,{})
    return dict(version=name,**g)


if __name__=='__main__':
    assert not (HERE/'results.json').exists()
    raw=gzip.decompress((ROOT/'diagnostics/disjoint_live_audit_20260927/raw/episode-114082874-replay.json.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest()=='22f1fbf49cf350ca95d48c471d55a15c65109785447e5098a4f012da2a2bbc2d'
    replay=json.loads(raw);assert replay['info']['TeamNames']==['Paarthpowa','Lakshmanan R']
    actions=[f[0]['action'] for f in replay['steps'][1:]];assert len(actions)==719
    (HERE/'opponent.json.gz').write_bytes(gzip.compress(json.dumps({'actions':actions},separators=(',',':')).encode()))
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),source_episode=114082874,
             seed=replay['info']['seed'],source_seat=1,candidate_hashes={k:v[1] for k,v in FILES.items()},
             independent_strength_evidence=False,complete=False,games=[])
    def save():(HERE/'results.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs=[(name,seat,out['seed']) for name in FILES for seat in (0,1)]
        for f in as_completed([pool.submit(play,j) for j in jobs]):
            g=f.result();out['games'].append(g);save()
            print(f"{g['version']} seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f}",flush=True)
    control=next(g for g in out['games'] if g['version']=='c68' and g['candidate_seat']==1)
    exact=(control['candidate_reward']==replay['rewards'][1] and control['opponent_reward']==replay['rewards'][0])
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),source_seat_cash_parity=exact,
               all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in out['games']))
    save();assert exact,'Investigate runtime/source mismatch before using counterfactual results'
