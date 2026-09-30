from collections import defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STEPS=(72,144,216,288,360,432,504,576)
EXPECTED='c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def normalized(action):
    orders=action.get('market',[]) or [];kept=[];i=0
    while i<len(orders):
        if (i+1<len(orders) and len(orders[i])>=3 and len(orders[i+1])>=3
                and orders[i][0]=='BUY_PRODUCT' and orders[i+1][0]=='SELL'
                and orders[i][1:]==orders[i+1][1:]):
            i+=2;continue
        kept.append(orders[i]);i+=1
    hands=[a or ['PASS'] for a in action.get('hands',[]) or []]
    while hands and hands[-1]==['PASS']:hands.pop()
    return dict(farmer=action.get('farmer') or ['PASS'],hands=hands,market=kept)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    source=ROOT/'main.py';assert hashlib.sha256(source.read_bytes()).hexdigest()==EXPECTED
    spec=importlib.util.spec_from_file_location('fresh_compat_c68',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    baseline=module._DATA['routes']
    normbase={k:[normalized(a) for a in tape] for k,tape in baseline.items()}
    index={mode:{step:defaultdict(list) for step in STEPS} for mode in ('exact','normalized')}
    for mode,tapes in (('exact',baseline),('normalized',normbase)):
        for rid,tape in tapes.items():
            for step in STEPS:index[mode][step][sha(tape[:step])].append(rid)
    manifest_path=ROOT/'diagnostics/current_top100_20260927_1137/manifest.json'
    manifest=json.loads(manifest_path.read_text());assert manifest['complete']
    sources=[r for r in manifest['rows'] if not r.get('self_control')]
    assert len(sources)==99
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),main_sha256=EXPECTED,
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
             baseline_routes=len(baseline),external_sources=len(sources),complete=False,rows=[])
    raw_cache={}
    for row in sources:
        payload=json.loads(gzip.decompress(Path(row['path']).read_bytes()));tape=payload['actions']
        assert sha(tape)==row['action_sha256'] and len(tape)==719
        norms=[normalized(a) for a in tape]
        matches=[]
        for step in STEPS:
            exact=index['exact'][step].get(sha(tape[:step]),[])
            near=index['normalized'][step].get(sha(norms[:step]),[])
            if not exact and not near:continue
            if row['episode_id'] not in raw_cache:
                raw=gzip.decompress(Path(row['replay_path']).read_bytes())
                assert hashlib.sha256(raw).hexdigest()==row['replay_sha256']
                replay=json.loads(raw)
                raw_cache[row['episode_id']]={s:replay['steps'][s][0]['observation']['town']['unlocked_shops'] for s in STEPS}
            differing=[r for r in near if norms[step:]!=normbase[r][step:]]
            matches.append(dict(step=step,exact_routes=exact,normalized_routes=near,
                                routes_with_distinct_future=differing,source_shops=raw_cache[row['episode_id']][step],
                                future_normalized_sha256=sha(norms[step:])))
        out['rows'].append(dict(rank=row['rank'],team=row['team'],team_id=row['team_id'],
                               episode_id=row['episode_id'],action_sha256=row['action_sha256'],matches=matches))
    out['summary']={str(step):dict(
        exact_sources=sum(any(m['step']==step and m['exact_routes'] for m in row['matches']) for row in out['rows']),
        normalized_sources=sum(any(m['step']==step and m['normalized_routes'] for m in row['matches']) for row in out['rows']),
        sources_with_distinct_future=sum(any(m['step']==step and m['routes_with_distinct_future'] for m in row['matches']) for row in out['rows']),
        distinct_future_schedules=len({m['future_normalized_sha256'] for row in out['rows'] for m in row['matches']
                                      if m['step']==step and m['routes_with_distinct_future']})) for step in STEPS}
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps(out['summary'],indent=2),flush=True)
